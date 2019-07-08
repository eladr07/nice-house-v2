import itertools
from datetime import date

from django.db.models import Sum

from Management.models import Demand, SalaryExpenses, EmployeeSalaryBaseStatus, Sale, Loan, LoanPay
from Management.models import RankType, EmployeeSalaryBaseStatusType

def enrich_employee_salaries(salaries, employee_by_id, from_year, from_month, to_year, to_month):
    set_salary_base_fields(salaries, employee_by_id, from_year, from_month, to_year, to_month)
    
    # construct a map between employee id and project list
    employee_projects_map = {employee_id: list(employee.projects.all()) for (employee_id, employee) in employee_by_id.items()}

    set_demands(salaries, employee_projects_map, from_year, from_month, to_year, to_month)

    set_employee_sales(salaries, employee_by_id, employee_projects_map, from_year, from_month, to_year, to_month)

    set_salary_status_date(salaries)

def enrich_nh_employee_salaries(salaries, employee_by_id, from_year, from_month, to_year, to_month):
    set_salary_base_fields(salaries, employee_by_id, from_year, from_month, to_year, to_month)
    
    set_salary_status_date(salaries)

def set_salary_base_fields(salaries, employee_by_id, from_year, from_month, to_year, to_month):
    employee_ids = employee_by_id.keys()

    # construct a map between (employee id, year, month) and SalaryExpense object
    salary_expenses = SalaryExpenses.objects \
        .range(from_year, from_month, to_year, to_month) \
        .filter(employee_id__in = employee_ids)

    expenses_map = {(e.employee_id, e.year, e.month): e for e in salary_expenses}
    
    # construct a map between (employee id, year, month) and Total Amount of Loan Pay objects
    loan_pays = LoanPay.objects \
        .range(from_year, from_month, to_year, to_month) \
        .filter(employee_id__in = employee_ids, deduct_from_salary = True) \
        .values('employee_id','year','month') \
        .annotate(total_amount = Sum('amount'))

    loan_pay_map = {(row['employee_id'], row['year'], row['month']): row['total_amount'] \
        for row in loan_pays}

    for salary in salaries:
        # create the key for the maps constructed above
        map_key = (salary.get_employee().id, salary.year, salary.month)
        (employee_id, year, month) = map_key

        employee = employee_by_id[employee_id]
        terms = employee.employment_terms
        
        # load mapped objects
        exp = expenses_map.get(map_key)
        loan_pay = loan_pay_map.get(map_key, 0)

        bruto, neto, check_amount, invoice_amount = None, None, None, None

        if terms:
            total_amount = salary.total_amount

            if terms.salary_net == None:
                check_amount = total_amount - loan_pay
                invoice_amount = total_amount - loan_pay
            else:
                if terms.salary_net == False:
                    bruto = total_amount - loan_pay
                    if exp != None:
                        neto = total_amount - exp.income_tax - exp.national_insurance - exp.health - exp.pension_insurance
                elif terms.salary_net == True:
                    neto = total_amount
                    if exp != None:
                        bruto = total_amount + exp.income_tax + exp.national_insurance + exp.health + exp.pension_insurance \
                            + exp.vacation + exp.convalescence_pay
                
                if neto:
                    check_amount = neto - loan_pay
        
        salary.expenses = exp

        salary.bruto = bruto
        salary.neto = neto
        salary.check_amount = check_amount
        salary.invoice_amount = invoice_amount

        salary.loan_pay = loan_pay

        # set 'bruto_employer_expense' field
        if exp:
            salary.bruto_employer_expense = sum([
                bruto,exp.employer_benefit,exp.employer_national_insurance,exp.compensation_allocation])
        else:
            salary.bruto_employer_expense = None

def set_demands(salaries, employee_projects_map, from_year, from_month, to_year, to_month):
    # construct a map between (project id, year, month) and Demand object
    demands = Demand.objects.select_related('project').range(from_year, from_month, to_year, to_month)

    demand_map = {(d.project_id, d.year, d.month): d for d in demands}

    for salary in salaries:
        # create the key for the maps constructed above
        map_key = (salary.employee_id, salary.year, salary.month)
        (employee_id, year, month) = map_key
        
        # set 'demands' property
        project_ids = [project.id for project in employee_projects_map[employee_id]]

        salary.demands = [demand_map.get((project_id, year, month)) for project_id in project_ids if (project_id, year, month) in demand_map]

def set_employee_sales(
    salaries, 
    employee_by_id, employee_projects_map, 
    from_year, from_month, to_year, to_month):
    """
    Set 'sales' and 'sales_count' fields for every EmployeeSalary object in 'salaries'
    """
    # construct a map between Porject and Sale list
    sales = Sale.objects.select_related('house__building') \
        .employee_pay_range(from_year, from_month, to_year, to_month) \
        .order_by('house__building__project_id','sale_date')

    # group sales by (project_id, year, month)
    sale_groups = itertools.groupby(sales,
        lambda sale: (sale.house.building.project_id, sale.employee_pay_year, sale.employee_pay_month))

    # create map
    sales_map = {map_key:list(project_sales) for (map_key, project_sales) in sale_groups}

    for salary in salaries:
        year, month = salary.year, salary.month

        employee = employee_by_id[salary.employee_id]
        employee_projects = employee_projects_map[salary.employee_id]

        # construct sales list for salary
        employee_sales = {}

        if employee.rank_id == RankType.RegionalSaleManager:
            employee_sales = {
                project: sales_map[(project.id, year, month)] \
                    for project in employee_projects if (project.id, year, month) in sales_map}
        else:
            employee_sales = {
                project: [sale for sale in sales_map[(project.id, year, month)] if sale.employee_id in (employee.id, None)] \
                    for project in employee_projects if (project.id, year, month) in sales_map}

        salary.sales = employee_sales
        salary.sales_count = sum(len(project_sales) for (project, project_sales) in employee_sales.items())

def set_salary_status_date(salaries):
    """
    Set 'approved_date', 'sent_to_bookkeeping_date', 'sent_to_checks_date' fields 
    for every EmployeeSalary object in 'salaries'
    """
    salary_ids = [salary.id for salary in salaries]

    # construct a map between Salary object and its latest status
    all_statuses = EmployeeSalaryBaseStatus.objects \
        .filter(employeesalarybase_id__in=salary_ids) \
        .order_by('employeesalarybase_id','-date')

    statuses_by_salary_id = {esb_id: list(statuses) for (esb_id, statuses) in itertools.groupby(all_statuses, lambda status: status.employeesalarybase_id)}

    for salary in salaries:
        # set status properties
        salary_statuses = statuses_by_salary_id.get(salary.id)

        if salary_statuses != None:
            salary.approved_date = next((status.date for status in salary_statuses if status.type_id == EmployeeSalaryBaseStatusType.Approved), None)
            salary.sent_to_bookkeeping_date = next((status.date for status in salary_statuses if status.type_id == EmployeeSalaryBaseStatusType.SentBookkeeping), None)
            salary.sent_to_checks_date = next((status.date for status in salary_statuses if status.type_id == EmployeeSalaryBaseStatusType.SentChecks), None)
        else:
            salary.approved_date = None
            salary.sent_to_bookkeeping_date = None
            salary.sent_to_checks_date = None

def set_loan_fields(employees):
    """
    Set 'loan_left' and 'loans_and_pays' fields for every Employee in 'employees'
    """
    loans = Loan.objects.filter(employee__in=employees).order_by('employee_id')
    loan_pays = LoanPay.objects.filter(employee__in=employees).order_by('employee_id')

    loans_by_employee_id = {employee_id:list(loans) for (employee_id, loans) in itertools.groupby(loans, lambda loan: loan.employee_id)}
    loan_pays_by_employee_id = {employee_id:list(loan_pays) for (employee_id, loan_pays) in itertools.groupby(loan_pays, lambda loan_pay: loan_pay.employee_id)}

    for employee in employees:
        employee_id = employee.id
        # merge loans and loan-pays to a single list
        loans_and_pays = []

        if employee_id in loans_by_employee_id:
            loans_and_pays += list(loans_by_employee_id[employee_id])
        if employee_id in loan_pays_by_employee_id:
            loans_and_pays += list(loan_pays_by_employee_id[employee_id])

        # sort list by (year, month)
        loans_and_pays.sort(key=lambda x: date(x.year, x.month, 1))

        left = 0

        for item in loans_and_pays:
            if isinstance(item, Loan):
                left += item.amount
            elif isinstance(item, LoanPay):
                left -= item.amount
            item.left = left

        # set fields on employee
        employee.loan_left = left
        employee.loans_and_pays = loans_and_pays
