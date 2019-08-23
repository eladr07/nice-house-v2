import itertools
from datetime import date

from django.http import HttpResponseBadRequest

from Management.models import Demand, EmployeeBase, Employee, EmployeeSalary, SalaryExpenses, DivisionType
from Management.models import NHEmployee, NHEmployeeSalary, NHBranch, NHBranchEmployee
from Management.forms import ProjectSeasonForm
from Management.enrichers.demand import set_demand_sale_fields, set_demand_diff_fields, set_demand_invoice_payment_fields
from Management.enrichers.salary import enrich_employee_salaries, enrich_nh_employee_salaries, set_loan_fields, set_salary_base_fields

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

    title = u'ריכוז שכר עובדים לחודש {month}/{year}'.format(
        month=month, year=year)

    return _generate_salary_export(title, salaries)

def employee_salary_season_export(request):
    employee_id = int(request.GET['employee_id'])
    from_year = int(request.GET['from_year'])
    from_month = int(request.GET['from_month'])
    to_year = int(request.GET['to_year'])
    to_month = int(request.GET['to_month'])

    employee_base = EmployeeBase.objects.get(pk=employee_id)

    # set to Employee or NHEmployee
    employee = employee_base.derived

    set_loan_fields([employee])

    if isinstance(employee, Employee):
        salaries = EmployeeSalary.objects.nondeleted() \
            .range(from_year, from_month, to_year, to_month) \
            .filter(employee_id = employee_base.id)
        
        # set the same employee instance for all salaries
        for s in salaries:
            s.employee = employee

        enrich_employee_salaries(
            salaries, 
            {employee_base.id: employee},
            from_year, from_month, to_year, to_month)

    elif isinstance(employee, NHEmployee):
        salaries = NHEmployeeSalary.objects \
            .nondeleted() \
            .range(from_year, from_month, to_year, to_month) \
            .filter(nhemployee__id = employee_base.id)
        
        # set the same employee instance for all salaries
        for s in salaries:
            s.nhemployee = employee

        enrich_nh_employee_salaries(
            salaries, 
            {employee_base.id: employee},
            from_year, from_month, to_year, to_month)
    
    title = u'ריכוז שכ"ע לפי תקופה - ' + str(employee_base)

    return _generate_salary_export(title, salaries)


def _generate_salary_export(title, salaries):
    columns = [
        ExcelColumn('כללי', columns=[
            ExcelColumn('חודש'),
            ExcelColumn('שם העובד', width=15),
            ExcelColumn('פרוייקט', width=15),
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
            '%d/%d' % (salary.month, salary.year),
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

    return ExcelGenerator().generate(title, columns, rows)

def employeesalary_season_expenses_export(request):
    salaries = []
    
    employee_id = int(request.GET['employee_id'])
    from_year = int(request.GET['from_year'])
    from_month = int(request.GET['from_month'])
    to_year = int(request.GET['to_year'])
    to_month = int(request.GET['to_month'])

    employee_base = EmployeeBase.objects.get(pk=employee_id)
    employee = employee_base.derived

    if isinstance(employee, Employee):
        salaries = EmployeeSalary.objects.nondeleted() \
            .range(from_year, from_month, to_year, to_month) \
            .select_related('employee__employment_terms__hire_type') \
            .filter(employee_id = employee_base.id)
        
        enrich_employee_salaries(
            salaries, 
            {employee_base.id: employee},
            from_year, from_month, to_year, to_month)
    else:
        # TODO
        pass

    # create a map of salary expenses
    expenses = SalaryExpenses.objects \
        .range(from_year, from_month, to_year, to_month) \
        .filter(employee_id=employee_id)

    expenses_map = {(e.employee_id, e.year, e.month):e for e in expenses}

    columns = [
        ExcelColumn('כללי', columns=[
            ExcelColumn('חודש'),
            ExcelColumn('שם העובד', width=15),
            ExcelColumn('פרוייקט', width=15),
            ExcelColumn('חטיבה'),
            ExcelColumn('סוג העסקה'),
            ExcelColumn("מס' עסקאות", showSum=True)
        ]),
        ExcelColumn('חישוב שכר נטו', columns=[
            ExcelColumn('סה"כ שווי תלוש', 'currency', showSum=True, width=15),
            ExcelColumn('החזר הלוואה', 'currency', showSum=True, width=15),
            ExcelColumn('שווי שיק', 'currency', showSum=True, width=15)
        ]),
        ExcelColumn('מיסי עובד לתשלום והפרשות', columns=[
            ExcelColumn('מס הכנסה', 'currency'), 
            ExcelColumn('ביטוח לאומי', 'currency'), 
            ExcelColumn('בריאות', 'currency'), 
            ExcelColumn('ביטוח פנסיה', 'currency'), 
            ExcelColumn('חופשה'), 
            ExcelColumn('דמי הבראה', 'currency'), 
            ExcelColumn('סה"כ ברוטו לעובד', 'currency')
        ]),
         ExcelColumn('הוצאות מעביד', columns=[
            ExcelColumn('ביטוח לאומי', 'currency'),  
            ExcelColumn('גמל', 'currency'),  
            ExcelColumn('הפרשה לפיצויים', 'currency'),  
            ExcelColumn('ברוטו כולל מעביד', 'currency')
        ]),
        ExcelColumn('אסמכתאות', columns=[
            ExcelColumn('שווי חשבונית', 'currency', showSum=True, width=15)
        ])
    ]

    rows = []

    for salary in salaries:
        key = (salary.employee_id, salary.year, salary.month)
        salary_expenses = expenses_map.get(key)
        employee = salary.employee
        terms = employee.employment_terms

        row = [
            '%d/%d' % (salary.month, salary.year),
            str(employee),
            ', '.join([demand.project.name for demand in salary.demands]),
            employee.rank.name,
            terms.hire_type.name,
            salary.sales_count,

            salary.neto,
            salary.loan_pay,
            salary.check_amount if terms.salary_net != None else None,

            salary_expenses and salary_expenses.income_tax,
            salary_expenses and salary_expenses.national_insurance,
            salary_expenses and salary_expenses.health,
            salary_expenses and salary_expenses.pension_insurance,
            salary_expenses and salary_expenses.vacation,
            salary_expenses and salary_expenses.convalescence_pay,
            salary_expenses and salary_expenses.bruto,

            salary_expenses and salary_expenses.employer_national_insurance,
            salary_expenses and salary_expenses.employer_benefit,
            salary_expenses and salary_expenses.compensation_allocation,
            salary_expenses and salary_expenses.bruto_with_employer,

            salary.invoice_amount
        ]

        rows.append(row)

    title = 'ריכוז שכר לעובד כולל הוצאות מעביד תקופתי - ' + str(employee)

    return ExcelGenerator().generate(title, columns, rows)

def employeesalary_season_total_expenses_export(request):
    salaries = []
    
    division_type = int(request.GET['division_type'])
    from_year = int(request.GET['from_year'])
    from_month = int(request.GET['from_month'])
    to_year = int(request.GET['to_year'])
    to_month = int(request.GET['to_month'])

    from_date = date(from_year, from_month, 1)
    to_date = date(to_year, to_month, 1)

    if division_type == DivisionType.Marketing:
        employees = list(Employee.objects \
            .select_related('employment_terms') \
            .exclude(work_end__isnull = False, work_end__lt = from_date))

        employee_by_id = {e.id:e for e in employees}
        
        salaries = EmployeeSalary.objects \
            .select_related('employee__employment_terms') \
            .range(from_year, from_month, to_year, to_month) \
            .order_by('employee_id')
    else:
        # NiceHouse division

        # map DivisionType to NHBranch
        division_to_branch = {
            DivisionType.NHShoham: NHBranch.Shoham,
            DivisionType.NHModiin: NHBranch.Modiin,
            DivisionType.NHNesZiona: NHBranch.NesZiona,
        }

        branch_id = division_to_branch[division_type]
        
        query = NHBranchEmployee.objects \
            .select_related('nhemployee__employment_terms') \
            .filter(nhbranch__id = branch_id) \
            .exclude(end_date__isnull=False, end_date__lt = from_date)

        employees = [x.nhemployee for x in query]
        employee_by_id = {e.id:e for e in employees}

        salaries = NHEmployeeSalary.objects \
            .range(from_year, from_month, to_year, to_month) \
            .order_by('nhemployee_id')

    set_salary_base_fields(
        salaries,
        employee_by_id,
        from_year, from_month, to_year, to_month)

    attrs = ['neto', 'loan_pay', 'check_amount', 'income_tax', 'national_insurance', 'health', 'pension_insurance', 
            'vacation', 'convalescence_pay', 'bruto', 'employer_national_insurance', 'employer_benefit',
            'compensation_allocation', 'bruto_with_employer']
            
    salaries_by_employee_id = {employee_id:list(salaries) for employee_id, salaries in itertools.groupby(salaries, lambda salary: salary.get_employee().id)}

    for employee in employees:
        # get the salary list, or empty list if no salaries exist for employee
        employee_salaries_list = salaries_by_employee_id.get(employee.id, [])
        
        for attr in attrs:
            # extract 'attr' from each salary
            attr_list = [getattr(salary, attr, 0) or 0 for salary in employee_salaries_list]
            # sum 'attr' over employee_salaries
            attr_sum = sum(attr_list)
            # set 'total_' attribute on employee object
            setattr(employee, 'total_' + attr, attr_sum)

    columns = [
        ExcelColumn('כללי', columns=[
            ExcelColumn('שם העובד', width=15)            
        ]),
        ExcelColumn('תשלום נטו', columns=[
            ExcelColumn('תלוש נטו', 'currency', showSum=True, width=15),
            ExcelColumn('החזר הלוואה', 'currency', showSum=True, width=15),
            ExcelColumn('שווי שיק', 'currency', showSum=True, width=15)
        ]),
        ExcelColumn('מיסי עובד לתשלום והפרשות', columns=[
            ExcelColumn('מס הכנסה', 'currency'), 
            ExcelColumn('ביטוח לאומי', 'currency'), 
            ExcelColumn('בריאות', 'currency'), 
            ExcelColumn('ביטוח פנסיה', 'currency'), 
            ExcelColumn('חופשה'), 
            ExcelColumn('דמי הבראה', 'currency'), 
            ExcelColumn('סה"כ ברוטו לעובד', 'currency', width=15)
        ]),
         ExcelColumn('הוצאות מעביד', columns=[
            ExcelColumn('ביטוח לאומי', 'currency'),  
            ExcelColumn('גמל', 'currency'),  
            ExcelColumn('הפרשה לפיצויים', 'currency'),  
            ExcelColumn('ברוטו כולל מעביד', 'currency')
        ])
    ]

    rows = []

    for employee in employees:
        row = [
            str(employee),

            employee.total_neto,
            employee.total_loan_pay,
            employee.total_check_amount,

            employee.total_income_tax,
            employee.total_national_insurance,
            employee.total_health,
            employee.total_pension_insurance,
            employee.total_vacation,
            employee.total_convalescence_pay,
            employee.total_bruto,

            employee.total_employer_national_insurance,
            employee.total_employer_benefit,
            employee.total_compensation_allocation,
            employee.total_bruto_with_employer
        ]

        rows.append(row)

    title = 'ריכוז שכר לעובדים כולל הוצאות מעביד תקופתי - %d/%d-%d/%d' % (from_month, from_year, to_month, to_year)

    return ExcelGenerator().generate(title, columns, rows)
