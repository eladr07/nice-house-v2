from django.http import HttpResponse, HttpResponseBadRequest

from Management.models import Demand, Employee, EmployeeSalary
from Management.forms import ProjectSeasonForm
from Management.enrichers.demand import set_demand_sale_fields, set_demand_diff_fields, set_demand_invoice_payment_fields
from Management.enrichers.salary import enrich_employee_salaries, set_loan_fields

from Management.export.generator import ExcelColumn, ExcelGenerator

from Management.templatetags.management_extras import commaise

def demand_sales_export(request, id):
    demand = Demand.objects \
        .prefetch_related('diffs','invoices','payments') \
        .select_related('project') \
        .get(pk=id)

    year, month = demand.year, demand.month

    set_demand_sale_fields([demand], year, month, year, month)

    sales = demand.sales_list
    commissions = demand.project.commissions.get()

    discount_cols = sales[0].discount != None
    bonus_cols = commissions.b_discount_save_precentage != None
    zilber_cols = commissions.c_zilber != None

    columns = [
        ExcelColumn('מזהה מכירה'),
        ExcelColumn('שם הרוכשים', width=20),
        ExcelColumn('בניין'),
        ExcelColumn('דירה'),
        ExcelColumn('ת. הרשמה', width=15),
        ExcelColumn('ת. מכירה', width=15),
        ExcelColumn('מחיר חוזה', 'currency', showSum=True, width=20),
        ExcelColumn('מחיר חוזה לעמלה', 'currency', showSum=True, width=20),
    ]

    if discount_cols:
        columns += [
            ExcelColumn('מחיר כולל מע"מ', 'currency', showSum=True),
            ExcelColumn('% הנחה ניתן', 'percent'),
            ExcelColumn('% הנחה מותר', 'percent'),
        ]
        
    columns += [
        ExcelColumn('% עמלת בסיס', 'percent', width=15),
        ExcelColumn('שווי עמלת בסיס', 'currency', showSum=True, width=20),
    ]
    
    if bonus_cols or zilber_cols:
        columns += [
            ExcelColumn('% בונוס חיסכון', 'percent'),
            ExcelColumn('שווי בונוס חיסכון', 'currency', showSum=True),
        ]

    columns += [
        ExcelColumn('% עמלה סופי', 'percent', width=15),
        ExcelColumn('שווי עמלה סופי', 'currency', showSum=True, width=20),
    ]

    rows = []

    for counter, sale in enumerate(sales, 1):
        signup = sale.house.get_signup()

        row = [
            '{demand_id}-{counter}'.format(demand_id=id, counter=counter),
            sale.clients,
            sale.house.building.num,
            sale.house.num,
            signup.date if signup != None else '',
            sale.sale_date,
            sale.price,
            sale.price_final
        ]

        if discount_cols:
            row += [
                sale.price_taxed,
                sale.discount,
                sale.allowed_discount
            ]
        
        row += [
            sale.pc_base,
            sale.pc_base_worth
        ]

        if bonus_cols:
            row += [
                sale.pb_dsp,
                sale.pb_dsp_worth
            ]
        elif zilber_cols:
            row += [
                '',
                sale.zdb
            ]

        row += [
            sale.c_final,
            sale.c_final_worth
        ]

        rows.append(row)
    
    title = u'פירוט מכירות - {project} לחודש {month}/{year}'.format(
        project=demand.project.name, month=month, year=year)

    return ExcelGenerator().generate(title, columns, rows)


def demand_season_list_export(request):

    if not len(request.GET):
        return HttpResponseBadRequest()

    form = ProjectSeasonForm(request.GET)

    if not form.is_valid():
        return HttpResponseBadRequest()

    project = form.cleaned_data['project']

    from_year, from_month = form.cleaned_data['from_year'], form.cleaned_data['from_month']
    to_year, to_month = form.cleaned_data['to_year'], form.cleaned_data['to_month']
    
    ds = Demand.objects \
        .range(from_year, from_month, to_year, to_month) \
        .filter(project = project) \
        .prefetch_related('reminders__statuses') \
        .select_related('project')

    set_demand_sale_fields(ds, from_year, from_month, to_year, to_month)
    set_demand_diff_fields(ds)
    # set_demand_last_status(ds)
    # set_demand_is_fixed(ds)

    columns = [
        ExcelColumn("מס'"), 
        ExcelColumn('חודש'), 
        ExcelColumn("מס' מכירות", showSum=True), 
        ExcelColumn('סה"כ מכירות כולל מע"מ', 'currency', showSum=True, width=20),
        ExcelColumn('עמלה מחושב בגין שיווק', 'currency', width=20),
        ExcelColumn('תוספת קבועה', 'currency', width=15),
        ExcelColumn('תוספת משתנה', 'currency', width=15),
        ExcelColumn('בונוס', 'currency', width=15),
        ExcelColumn('קיזוז', 'currency', width=15),
        ExcelColumn('סה"כ תשלום לחברה', 'currency', showSum=True, width=20),
    ]

    rows = []

    # Iterate through all demands
    for demand in ds:
        # Define the data for each cell in the row 
        row = [
            demand.id,
            '{month}/{year}'.format(month=demand.month, year=demand.year),
            demand.sale_count,
            demand.sales_amount,
            demand.sales_commission,
            hasattr(demand, 'fixed_diff') and demand.fixed_diff.amount or None,
            hasattr(demand, 'var_diff') and demand.var_diff.amount or None,
            hasattr(demand, 'bonus_diff') and demand.bonus_diff.amount or None,
            hasattr(demand, 'fee_diff') and demand.fee_diff.amount or None,
            demand.total_amount
        ]
        
        rows.append(row)

    title = 'ריכוז דרישות - {project_name}'.format(project_name=project.name)

    return ExcelGenerator().generate(title, columns, rows)

def demand_followup_export(request):
    if not len(request.GET):
        return HttpResponseBadRequest()

    form = ProjectSeasonForm(request.GET)

    if not form.is_valid():
        return HttpResponseBadRequest()

    project = form.cleaned_data['project']

    from_year, from_month = form.cleaned_data['from_year'], form.cleaned_data['from_month']
    to_year, to_month = form.cleaned_data['to_year'], form.cleaned_data['to_month']

    columns = [
        ExcelColumn('פרטי דרישה', columns=[
            ExcelColumn("מס'"),
            ExcelColumn('חודש'),
            #ExcelColumn('סטטוס'),
            ExcelColumn("מס' מכירות"),
            ExcelColumn('סכום דרישה', 'currency', showSum=True, width=20)
        ]),
        ExcelColumn('פרטי חשבונית', columns=[
            ExcelColumn("מס' חשבונית"),
            ExcelColumn('סכום'),
            ExcelColumn('תאריך')
        ]),
        ExcelColumn('פרטי שיקים', columns=[
            ExcelColumn('סכום'),
            ExcelColumn('תאריך')
        ]),
        ExcelColumn('הפרשי דרישה', columns=[
            ExcelColumn('דרישה לחשבונית', 'currency', showSum=True, width=20),
            ExcelColumn('שיק לחשבונית', 'currency', showSum=True),
            ExcelColumn('זיכוי חשבונית')
        ])
    ]

    demands = Demand.objects \
        .prefetch_related('invoices','payments') \
        .select_related('project') \
        .range(from_year, from_month, to_year, to_month) \
        .filter(project__id = project.id)

    set_demand_sale_fields(demands, from_year, from_month, to_year, to_month)
    set_demand_diff_fields(demands)
    set_demand_invoice_payment_fields(demands)

    # build data rows (copied from DemandFollowupWriter)
    rows = []

    for demand in demands:

        invoice_nums = []
        invoice_amounts = []
        invoice_dates = []
        offset_amounts = []

        for invoice in demand.invoices.all():
            invoice_nums.append(str(invoice.num))
            invoice_amounts.append(commaise(invoice.amount))
            invoice_dates.append(invoice.date.strftime('%d/%m/%Y'))

            offset = invoice.offset
            if offset:
                offset_amounts.append(offset.amount)

        invoice_num_str = '<br/>'.join(invoice_nums)
        invoice_amount_str = '<br/>'.join(invoice_amounts)
        invoice_date_str = '<br/>'.join(invoice_dates)

        payments = demand.payments.all()
        payment_amount_str = '<br/>'.join([commaise(payment.amount) for payment in payments])
        payment_date_str = '<br/>'.join([payment.payment_date.strftime('%d/%m/%Y') for payment in payments])
        
        offset_amount_str = '<br/>'.join(offset_amounts)
        
        row = [
            demand.id, '%s/%s' % (demand.month, demand.year), demand.sales_count, demand.total_amount,
            invoice_num_str, invoice_amount_str, invoice_date_str,
            payment_amount_str, payment_date_str, 
            demand.diff_invoice, demand.diff_invoice_payment, offset_amount_str
        ]
        
        rows.append(row)

    title = 'מעקב דרישות - {project_name}'.format(project_name=project.name)

    return ExcelGenerator().generate(title, columns, rows)

def employee_salary_export(request):
    year = int(request.GET['year'])
    month = int(request.GET['month'])

    employees = Employee.objects \
        .select_related('employment_terms__hire_type','rank') \
        .prefetch_related('projects') \
        .filter(employment_terms__isnull=False)

    current_employee_ids = []

    for e in employees:
        # do not include employees who did not start working by the month selected
        if year < e.work_start.year or (year == e.work_start.year and month < e.work_start.month):
            continue
        # do not include employees who finished working by the month selected
        if e.work_end and (year > e.work_end.year or (year == e.work_end.year and month > e.work_end.month)):
            continue

        current_employee_ids.append(e.id)

    salaries = EmployeeSalary.objects.filter(
        year=year, month=month, employee_id__in=current_employee_ids)

    employee_by_id = {employee.id:employee for employee in employees}

    enrich_employee_salaries(salaries, employee_by_id, year, month, year, month)

    set_loan_fields(employees)

    columns = [
        ExcelColumn('כללי', columns=[
            ExcelColumn('שם העובד'),
            ExcelColumn('פרוייקט'),
            ExcelColumn('חטיבה'),
            ExcelColumn('סוג העסקה'),
            ExcelColumn("מס' עסקאות", showSum=True)
        ]),
        ExcelColumn('חישוב שכר נטו', columns=[
            ExcelColumn('שכר בסיס', 'currency', showSum=True, width=15),
            ExcelColumn('עמלות', 'currency', showSum=True, width=15),
            ExcelColumn('רשת ביטחון', 'currency', showSum=True, width=15),
            ExcelColumn('תוספת משתנה', 'currency', showSum=True, width=15),
            ExcelColumn('קיזוז שכר', 'currency', showSum=True, width=15),
            ExcelColumn('סה"כ שווי תלוש', 'currency', showSum=True, width=15),
            ExcelColumn('החזר הלוואה', 'currency', showSum=True, width=15),
            ExcelColumn('שווי שיק', 'currency', showSum=True, width=15)
        ]),
        ExcelColumn('אסמכתאות', columns=[
            ExcelColumn('ברוטו לחישוב', 'currency', showSum=True, width=15),
            #ExcelColumn('ניכוי מס במקור'),
            ExcelColumn('שווי חשבונית', 'currency', showSum=True, width=15)
        ]),
        ExcelColumn('נלווה לשכר', columns=[
            ExcelColumn('החזר הוצאות', 'currency', showSum=True, width=15),
            #ExcelColumn('חופש ומחלה')
        ]),
        ExcelColumn('הערות ושליחה', columns=[
            ExcelColumn('הערות', width=30),
            ExcelColumn('ת. אישור', width=30),
            ExcelColumn('ת. שליחה להנה"ח', width=30),
            ExcelColumn('ת. שליחה לשיקים', width=30)
        ])
    ]

    rows = []

    for salary in salaries:
        employee = salary.employee
        terms = employee.employment_terms

        row = [
            str(employee),
            ', '.join([demand.project.name for demand in salary.demands]),
            employee.rank.name,
            terms.hire_type.name,
            salary.sales_count,

            salary.base,
            salary.commissions,
            salary.safety_net,
            salary.var_pay,
            salary.deduction,
            salary.neto,
            salary.loan_pay,
            salary.check_amount if terms.salary_net != None else None,

            salary.bruto,
            salary.invoice_amount,

            salary.refund,

            salary.remarks,
            salary.approved_date,
            salary.sent_to_bookkeeping_date,
            salary.sent_to_checks_date
        ]

        rows.append(row)

    title = u'ריכוז שכר עובדים לחודש {month}/{year}'.format(
        month=month, year=year)

    return ExcelGenerator().generate(title, columns, rows)

def employeesalary_season_expenses_export(request):
    pass

