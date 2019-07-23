import itertools
from datetime import date

from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.urls import reverse

from Indices.models import Tax

from Management.models import HireType, Sale, DivisionType, Demand, EmployeeSalary, PaymentCheck
from Management.models import NHMonth, NHBranch, NHEmployeeSalary
from Management.views import build_and_return_pdf
from Management.forms import SeasonForm, NHBranchSeasonForm
from Management.pdf.writers import SaleAnalysisWriter
from Management.enrichers.demand import set_demand_diff_fields, set_demand_sale_fields
from Management.enrichers.salary import set_salary_base_fields
from Management.common import current_month

from .forms import SaleAnalysisForm, GloablProfitLossForm

# Create your views here.

@permission_required('Management.sale_analysis')
def sale_analysis(request):
    data = []
    include_clients = None
    total_sale_count = 0

    if len(request.GET):
        form = SaleAnalysisForm(request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            project, include_clients = cleaned_data['project'], int(cleaned_data['include_clients'])
            building_num, rooms_num, house_type = cleaned_data['building_num'], cleaned_data['rooms_num'], cleaned_data['house_type']
            from_year, from_month, to_year, to_month = (cleaned_data['from_year'], cleaned_data['from_month'],
                                                        cleaned_data['to_year'], cleaned_data['to_month'])
            
            # query all the sales needed
            all_sales = Sale.objects.contractor_pay_range(from_year, from_month, to_year, to_month)
            all_sales = all_sales.filter(house__building__project = project).order_by('contractor_pay_year', 'contractor_pay_month').select_related('house')
            if rooms_num:
                all_sales = all_sales.filter(house__rooms = rooms_num)
            if house_type:
                all_sales = all_sales.filter(house__type = house_type)
            if building_num:
                all_sales = all_sales.filter(house__building__num = building_num)
            
            if 'html' in request.GET:    
                house_attrs = ('net_size', 'garden_size', 'rooms', 'floor', 'perfect_size')
                sale_attrs = ('price_taxed', 'price_taxed_for_perfect_size')
                
                for (month, year), sales in itertools.groupby(all_sales, lambda sale: (sale.contractor_pay_month, sale.contractor_pay_year)):
                    sales_list = list(sales)
                    houses = [sale.house for sale in sales_list]
                    item_count = len(sales_list)
                    row = {'sales':sales_list,'houses':houses,'year':year,'month':month}
                    for attr in house_attrs:
                        sum = 0
                        for house in houses:
                            attr_value = getattr(house, attr)
                            sum += (attr_value or 0)
                        row['avg_' + attr] = item_count and (sum / item_count) or 0
                    for attr in sale_attrs:
                        sum = 0
                        for sale in sales_list:
                            attr_value = getattr(sale, attr)
                            sum += (attr_value or 0)
                        row['avg_' + attr] = item_count and (sum / item_count) or 0
                    data.append(row)
    
                for i in range(1,len(data)):
                    curr_row = data[i]
                    prev_row = data[i-1]
                    if not len(curr_row['sales']) or not len(prev_row['sales']):
                        continue
                    curr_row['diff_avg_price_taxed_for_perfect_size'] = curr_row['avg_price_taxed_for_perfect_size'] - \
                        prev_row['avg_price_taxed_for_perfect_size']
                    
            elif 'pdf' in request.GET:
                writer = SaleAnalysisWriter(project, from_month, from_year, to_month, to_year, all_sales, include_clients)
                return build_and_return_pdf(writer)
    else:
        form = SaleAnalysisForm()
        
    context = { 
        'filterForm':form, 
        'sale_months':data, 
        'include_clients':include_clients,
        'total_sale_count':total_sale_count 
    }

    return render(request, 'Analytics/sale_analysis.html', context)
    
@permission_required('Management.global_profit_lost')
def global_profit_lost(request):
    data = []
    global_income, global_loss = 0,0
    if len(request.GET):
        form = GloablProfitLossForm(request.GET)
        if form.is_valid():
            # extract form data
            divisions = form.cleaned_data['divisions']
            from_year, from_month = form.cleaned_data['from_year'], form.cleaned_data['from_month']
            to_year, to_month = form.cleaned_data['to_year'], form.cleaned_data['to_month']

            from_date = date(from_year, from_month, 1)
            to_date = date(to_year, to_month, 1)

            for division in divisions:
                total_income, total_loss = 0,0
                income_rows, loss_rows = [], []
                
                if division.id == DivisionType.Marketing:
                    # load and enrich demands
                    demands = Demand.objects \
                        .range(from_year, from_month, to_year, to_month)

                    set_demand_diff_fields(demands)

                    # load and enrich salaries
                    salaries = EmployeeSalary.objects \
                        .select_related('employee__employment_terms') \
                        .nondeleted() \
                        .range(from_year, from_month, to_year, to_month)

                    set_salary_base_fields(
                        salaries,
                        {s.employee_id:s.employee for s in salaries},
                        from_year, from_month, to_year, to_month)

                    # load all Tax objects, order by 'date' descending
                    taxes = list(Tax.objects.all())

                    # sum up demands total_amount
                    demands_amount = 0

                    for demand in demands:
                        # find the first tax object with date earlier then demand's date
                        demand_date = date(demand.year, demand.month, 1)
                        tax = next((t for t in taxes if t.date <= demand_date))  

                        tax_val = tax.value / 100 + 1

                        demands_amount += demand.total_amount / tax_val

                    # sum up salaries amount
                    salaries_amount = sum([salary.bruto or salary.check_amount or 0 for salary in salaries])

                    income_rows.append({
                        'name':division,
                        'amount':demands_amount,
                        'details_link':'/seasonincome/?from_year=%s;from_month=%s;to_year=%s;to_month=%s' 
                                        % (from_date.year, from_date.month, to_date.year, to_date.month)
                    })
                    loss_rows.append({
                        'name':u'הוצאות שכר', 
                        'amount':salaries_amount,
                        'details_link': reverse('salary-season-total-expenses') + 'division_type=%s;from_year=%s;from_month=%s;to_year=%s;to_month=%s'
                            % (division.id, from_date.year, from_date.month, to_date.year, to_date.month)})
                        
                    total_income += demands_amount
                    total_loss += salaries_amount
                    
                elif division.is_nicehouse:
                    # get nhbranch object from the division type
                    if division.id == DivisionType.NHShoham:
                        nhbranch = NHBranch.objects.get(pk = NHBranch.Shoham)
                    elif division.id == DivisionType.NHModiin:
                        nhbranch = NHBranch.objects.get(pk = NHBranch.Modiin)
                    elif division.id == DivisionType.NHNesZiona:
                        nhbranch = NHBranch.objects.get(pk = NHBranch.NesZiona)
                    
                    # load and enrich salaries
                    salaries = NHEmployeeSalary.objects \
                        .select_related('nhemployee') \
                        .nondeleted() \
                        .range(from_year, from_month, to_year, to_month) \
                        .filter(nhbranch = nhbranch)

                    set_salary_base_fields(
                        salaries,
                        {s.nhemployee_id: s.nhemployee for s in salaries},
                        from_year, from_month, to_year, to_month)

                    nhmonths = NHMonth.objects.range(from_year, from_month, to_year, to_month) \
                        .filter(nhbranch = nhbranch)
                    
                    nhmonths_amount, salary_amount = 0,0
                    for nhmonth in nhmonths:
                        nhmonth.include_tax = False
                        nhmonths_amount += nhmonth.total_net_income
                    for salary in salaries:
                        salary_amount += salary.bruto or salary.check_amount or 0
                        
                    income_rows.append({
                        'name':nhbranch, 
                        'amount':nhmonths_amount,
                        'details_link':'/nhseasonincome/?nhbranch=%s;from_year=%s;from_month=%s;to_year=%s;to_month=%s' 
                                        % (nhbranch.id, from_date.year, from_date.month, to_date.year, to_date.month)})
                    loss_rows.append({
                        'name':u'הוצאות שכר', 
                        'amount':salary_amount,
                        'details_link': reverse('salary-season-total-expenses') + '?division_type=%s;from_year=%s;from_month=%s;to_year=%s;to_month=%s' 
                                    % (division.id, from_date.year, from_date.month, to_date.year, to_date.month)})
                    
                    total_income += nhmonths_amount
                    total_loss += salary_amount
                    
                #general information required by all divisions    
                checks = PaymentCheck.objects \
                    .filter(issue_date__range=(from_date,to_date), division_type=division)
                
                incomes_amount = 0 # Income model was removed
                total_income += incomes_amount
                
                income_rows.extend([{'name':u'הכנסות אחרות','amount':incomes_amount,
                                     'details_link':'/incomes/?division_type=%s;from_year=%s;from_month=%s;to_year=%s;to_month=%s' 
                                     % (division.id, from_date.year, from_date.month, to_date.year, to_date.month)},
                                     {'name':u'סה"כ','amount':total_income}])
                
                global_income += total_income
                
                expenses_amount = sum([check.amount for check in checks])
                total_loss += expenses_amount
                
                loss_rows.extend([{'name':u'הוצאות אחרות', 'amount':expenses_amount,
                                   'details_link':'/checks/?division_type=%s;from_year=%s;from_month=%s;to_year=%s;to_month=%s' 
                                   % (division.id, from_date.year, from_date.month, to_date.year, to_date.month)},
                                   {'name':u'סה"כ', 'amount':total_loss}])
                global_loss += total_loss
                    
                data.append({'division':division, 'incomes':income_rows,'losses':loss_rows,'profit':total_income-total_loss})
                #calculate relative profits and losses for all divisions items (i.e. projects/nhbranches)
                for row in data:
                    division, incomes, losses = row['division'] ,row['incomes'], row['losses']
                    for incomeRow in incomes:
                        amount = incomeRow['amount']
                        incomeRow['relative'] = global_income and (amount / global_income * 100) or 0
                    for lossRow in losses:
                        amount = lossRow['amount']
                        lossRow['relative'] = global_loss and (amount / global_loss * 100) or 0
    else:
        form = GloablProfitLossForm()
        from_date, to_date = None, None
        
    context = {
        'filterForm':form, 
        'data':data,
        'global_income':global_income, 
        'global_loss':global_loss,
        'global_profit':global_income - global_loss, 
        'start':from_date, 
        'end':to_date
    }

    return render(request, 'Analytics/global_profit_loss.html', context)
    
@permission_required('Management.projects_profit')
def projects_profit(request):
        
    # load all Tax objects, order by 'date' descending
    taxes = list(Tax.objects.all())

    def _process_demands(demands):
        projects = []

        for p, demand_iter in itertools.groupby(demands, lambda demand: demand.project):
            p.sale_count, p.total_income, p.total_expense, p.profit, p.total_sales_amount = 0,0,0,0,0
            p.employee_expense = {}
            
            for demand in demand_iter:
                # find the first tax object with date earlier then demand's date
                demand_date = date(demand.year, demand.month, 1)
                tax = next((t for t in taxes if t.date <= demand_date))  

                tax_val = tax.value / 100 + 1
    
                total_amount = demand.total_amount / tax_val
                sales = demand.sales_list
                sale_count = demand.sales_count
                
                p.total_income += total_amount
                p.sale_count += sale_count
                p.total_sales_amount += sum(map(lambda sale: sale.price if sale.include_tax else sale.price / tax_val ,sales))
            
            projects.append(p)
            
        return projects

    def _process_salaries(salaries, projects):
        for s in salaries:
            # find the first tax object with date earlier then salary's date
            salary_date = date(s.year, s.month, 1)
            tax = next((t for t in taxes if t.date <= salary_date))  
            
            tax_val = tax.value / 100 + 1
            terms = s.employee.employment_terms
            if not terms: continue
            s.calculate()
            for project, salary in s.project_salary().items():
                fixed_salary = salary
                if terms.hire_type.id == HireType.SelfEmployed:
                    fixed_salary = salary / tax_val
                p = projects[projects.index(project)]
                p.employee_expense.setdefault(s.employee, 0)
                p.employee_expense[s.employee] += fixed_salary
                p.total_expense += fixed_salary
    
    if len(request.GET):
        form = SeasonForm(request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            from_year, from_month, to_year, to_month = cleaned_data['from_year'], cleaned_data['from_month'], cleaned_data['to_year'], cleaned_data['to_month']
            
            demands = Demand.objects \
                .range(from_year, from_month, to_year, to_month) \
                .order_by('project')

            set_demand_sale_fields(demands, from_year, from_month, to_year, to_month)
            set_demand_diff_fields(demands)
                
            salaries = EmployeeSalary.objects.nondeleted().range(from_year, from_month, to_year, to_month)
            
            projects = _process_demands(demands)
            _process_salaries(salaries, projects)
            
            total_income = sum([project.total_income for project in projects])
            avg_relative_expense_income, avg_relative_sales_expense = 0,0
        
            project_count = 0
            for p in projects:
                if p.sale_count > 0:
                    project_count += 1
                p.relative_income = total_income and (p.total_income / total_income * 100) or 100
                if p.total_expense and p.total_sales_amount:
                    p.relative_sales_expense = float(p.total_expense) / p.total_sales_amount * 100
                    avg_relative_sales_expense += p.relative_sales_expense
                else:
                    if p.total_expense == 0 and p.total_sales_amount == 0: p.relative_sales_expense_str = 'אפס'
                    elif p.total_sales_amount == 0: p.relative_sales_expense_str = u'גרעון'
                    elif p.total_expense == 0: p.relative_sales_expense_str = u'עודף'
                if p.total_income and p.total_expense:
                    p.relative_expense_income = p.total_expense / p.total_income * 100
                    avg_relative_expense_income += p.relative_expense_income
                else:
                    if p.total_income == 0 and p.total_expense == 0: p.relative_expense_income_str = u'אפס'
                    elif p.total_income == 0: p.relative_expense_income_str = u'גרעון'
                    elif p.total_expense == 0: p.relative_expense_income_str = u'עודף'
                p.profit = p.total_income - p.total_expense
                
            total_sale_count = sum([project.sale_count for project in projects])
            total_expense = sum([project.total_expense for project in projects])
            total_profit = sum([project.profit for project in projects])
        
            if project_count:
                avg_relative_expense_income = avg_relative_expense_income / project_count
                avg_relative_sales_expense = avg_relative_sales_expense / project_count
    else:
        month = current_month()
        form = SeasonForm(initial = {'from_year': month.year, 'from_month': month.month, 'to_year': month.year, 'to_month': month.month})
        from_year, from_month, to_year, to_month = month.year, month.month, month.year, month.month
        total_income, total_expense, total_profit, avg_relative_expense_income, total_sale_count, avg_relative_sales_expense = 0,0,0,0,0,0
        projects = []

    context = { 
        'projects':projects,
        'from_year':from_year,
        'from_month':from_month, 
        'to_year':to_year,
        'to_month':to_month, 
        'filterForm':form,
        'total_income':total_income,
        'total_expense':total_expense, 
        'total_profit':total_profit,
        'avg_relative_expense_income':avg_relative_expense_income,
        'total_sale_count':total_sale_count,
        'avg_relative_sales_expense':avg_relative_sales_expense
        }

    return render(request, 'Analytics/projects_profit.html', context)

@permission_required('Management.nh_season_profit')
def nh_season_profit(request):
    months = []
    totals = {}
    
    if len(request.GET):
        form = NHBranchSeasonForm(request.GET)
        if form.is_valid():
            nhbranch = form.cleaned_data['nhbranch']
            cleaned_data = form.cleaned_data
            from_year, from_month, to_year, to_month = cleaned_data['from_year'], cleaned_data['from_month'], \
                cleaned_data['to_year'], cleaned_data['to_month']
            total_profit, total_net_income = 0,0
            nhmonths = NHMonth.objects.range(from_year, from_month, to_year, to_month).filter(nhbranch = nhbranch)
            for nhm in nhmonths:
                nhm.include_tax = False
                salary_expenses = 0
                #collect all employee expenses for this month
                for salary in NHEmployeeSalary.objects.nondeleted().filter(nhbranch = nhm.nhbranch, year = nhm.year, month = nhm.month):
                    salary_expenses += salary.check_amount or 0
                #calculate commulative sales prices for this month
                sales_worth = 0
                for nhsale in nhm.nhsales.all():
                    sales_worth += nhsale.price
                profit = nhm.total_net_income - salary_expenses
                month_total = {'nhmonth':nhm, 'sales_count':nhm.nhsales.count(),'sales_worth_no_tax':sales_worth,
                               'income_no_tax':nhm.total_income, 'lawyers_pay':nhm.total_lawyer_pay,
                               'net_income_no_tax':nhm.total_net_income, 'salary_expenses':salary_expenses,
                               'profit':profit}
                months.append(month_total)
                total_profit += profit
                total_net_income += nhm.total_net_income
            totals = {}
            #calculate relative fields, and totals
            for month in months:
                month['relative_profit'] = month['profit'] / total_profit * 100
                month['relative_net_income'] = month['net_income_no_tax'] / total_net_income * 100
                for key in ['sales_worth_no_tax','income_no_tax','lawyers_pay','net_income_no_tax','salary_expenses','profit']:
                    totals.setdefault(key, 0)
                    totals[key] += month[key]
    else:
        form = NHBranchSeasonForm()
        month = current_month()
        from_year, from_month, to_year, to_month = month.year, month.month, month.year, month.month
        
    context = { 
        'months':months,
        'totals':totals, 
        'filterForm':form, 
        'from_year':from_year, 
        'from_month': from_month,
        'to_year': to_year, 
        'to_month': to_month 
    }

    return render(request, 'Analytics/nh_season_profit.html', context)

@permission_required('Management.season_income')
def season_income(request):
    total_sale_count, total_amount, total_amount_notax = 0,0,0
    from_date, to_date = None, None
    month_count = 1
    projects = []
    if len(request.GET):
        form = SeasonForm(request.GET)
        if form.is_valid():
            # extract form data
            from_year, from_month = form.cleaned_data['from_year'], form.cleaned_data['from_month']
            to_year, to_month = form.cleaned_data['to_year'], form.cleaned_data['to_month']

            from_date = date(from_year, from_month, 1)
            to_date = date(to_year, to_month, 1)
            
            # load Demand objects
            demands = Demand.objects \
                .select_related('project') \
                .range(from_year, from_month, to_year, to_month)

            set_demand_sale_fields(demands, from_year, from_month, to_year, to_month)
            set_demand_diff_fields(demands)
                
            # load all Tax objects, order by 'date' descending
            taxes = list(Tax.objects.all())

            for demand in demands:
                if demand.project in projects:
                    project = projects[projects.index(demand.project)]
                else:
                    project = demand.project
                    projects.append(project)
                    for attr in ['total_amount', 'total_amount_notax', 'total_sale_count']:
                        setattr(project, attr, 0)

                # find the first tax object with date earlier then demand's date
                demand_date = date(demand.year, demand.month, 1)
                tax = next((t for t in taxes if t.date <= demand_date))       
                tax_val = tax.value / 100 + 1
                
                # sum amount
                amount = demand.total_amount
                project.total_amount += amount
                project.total_amount_notax += amount / tax_val

                # sum sale count
                sales_count = demand.sales_count
                project.total_sale_count += sales_count
                total_sale_count += sales_count

                # sum totals
                total_amount += amount
                total_amount_notax += amount / tax_val

            # set avg_sale_count
            for p in projects:
                start_date = max(p.start_date, from_date)
                active_months = round((to_date - start_date).days/30) + 1
                p.avg_sale_count = p.total_sale_count / active_months if active_months > 0 else 0

            month_count = round((to_date-from_date).days/30) + 1
    else:
        form = SeasonForm()

    context = { 
        'start':from_date, 'end':to_date,
        'projects':projects, 'filterForm':form,
        'total_amount':total_amount,'total_sale_count':total_sale_count,
        'total_amount_notax':total_amount_notax,'avg_amount':total_amount/month_count,
        'avg_amount_notax':total_amount_notax/month_count,'avg_sale_count':total_sale_count/month_count
    }

    return render(request, 'Analytics/season_income.html', context)