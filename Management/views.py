import reversion, itertools, time, threading, io
from datetime import datetime, date

import django.core.paginator
from django.db import models, transaction
from django.db.models import Count, Sum
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, FileResponse
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory
from django.core import serializers
from django.urls import reverse

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType

import Management.common as common
from Management.forms import *
from Management.models import *
from Management.pdf.writers import MonthDemandWriter, MultipleDemandWriter, EmployeeListWriter, EmployeeSalariesWriter, ProjectListWriter, EmployeesLoans
from Management.pdf.writers import PricelistWriter, BuildingClientsWriter, EmployeeSalariesBookKeepingWriter, SalariesBankWriter, DemandFollowupWriter
from Management.pdf.writers import EmployeeSalesWriter, SaleAnalysisWriter, DemandPayBalanceWriter

from Management.mail import mail
from pprint import pprint


def build_and_return_pdf(writer):
    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    writer.build(buffer)

    buffer.seek(io.SEEK_SET)

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    return FileResponse(buffer, as_attachment=True, filename='hello.pdf')  
    
def revision_list(request):
    if len(request.GET):
        filterForm = RevisionFilterForm(request.GET)
    else:
        filterForm = RevisionFilterForm(request.GET)
        
    return render(request, 'revision_list.html', {'filterForm':filterForm })

def calc_salaries(salaries):
    def calc_salaries_core(salaries):
        with reversion.create_revision():
            for salary in salaries:
                try:
                    salary.calculate()
                    salary.save()
                except:
                    continue
    
    thread = threading.Thread(target = lambda: calc_salaries_core(salaries))
    thread.setDaemon(True)
    thread.start()

def calc_demands(demands):
    def calc_demands_core(demands):
        with reversion.create_revision():
            for demand in demands:
                try:
                    demand.calc_sales_commission()
                except:
                    continue
    
    thread = threading.Thread(target = lambda: calc_demands_core(demands))
    thread.setDaemon(True)
    thread.start()

@login_required
def index(request):
    context = {
        'locateHouseForm':LocateHouseForm(), 
        'locateDemandForm': LocateDemandForm(),
        'employeeSalesForm': ProjectSeasonForm(), 
        'employeeSalarySeasonForm': EmployeeSeasonForm(),
        'nhbranches':NHBranch.objects.all()
        }
    return render(request, 'Management/index.html', context)
  
@login_required  
def locate_house(request):
    from django.core.exceptions import ObjectDoesNotExist

    if request.method == 'GET':
        form = LocateHouseForm(request.GET)
        if form.is_valid():
            project = form.cleaned_data['project']
            try:
                building = project.buildings.get(num=form.cleaned_data['building_num'])
                house = building.houses.get(num=form.cleaned_data['house_num'])
                return HttpResponseRedirect('/buildings/%s/house/%s/type1' % (building.id, house.id))
            except ObjectDoesNotExist:
                error = u'לא נמצאה דירה מס %s בבניין מס %s בפרוייקט %s' % (form.cleaned_data['house_num'],
                                                                           form.cleaned_data['building_num'],
                                                                           project)
                return render(request, 'Management/error.html', {'error': error})

    return HttpResponseRedirect('/')
    
@login_required  
def locate_demand(request):
    if request.method == 'GET':
        form = LocateDemandForm(request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            try:
                demand = Demand.objects.get(**cleaned_data)
                
                if 'find' in request.GET:
                    return HttpResponseRedirect(demand.get_absolute_url())
                elif 'pdf' in request.GET:
                    return report_project_month(request, demand = demand)
                
            except Demand.DoesNotExist:
                error = u'לא נמצאה דרישה מתאימה'
                return render(request, 'Management/error.html', {'error': error})

    return HttpResponseRedirect('/')
    
@login_required
def employee_loans(request, object_id):

    employee_base = EmployeeBase.objects.get(pk=object_id)

    # set to Employee or NHEmployee
    employee = employee_base.derived

    set_loan_fields([employee])

    if request.GET.get('t') == 'pdf' :
        writer = EmployeesLoans(employee)
        return build_and_return_pdf(writer)
    else:
        return render(request, 'Management/employee_loans.html', {'employee':employee})

@login_required
def limited_update_object(request, permission=None, *args, **kwargs):
    if 'model' in kwargs:
        model = kwargs['model']
    elif 'form_class' in kwargs:
        model = kwargs['form_class']._meta.model

    model_name = model.__name__.lower()

    if request.method == "POST" :
        if model_name == 'projectcommission':
            allow_history = [ 'add_amount', 'add_type', 'registration_amount', 'max' ]
            form_old      = ProjectCommission()
            form_old_dict = form_old.__dict__.copy()
            form          = ProjectCommissionForm(request.POST, instance=form_old)

            if form.is_valid():
                form_dict = form.instance.__dict__

                for item in form_old._meta.fields :
                    name = item.name

                    if name in form_dict and name in allow_history :
                        value     = form_dict.get(name)
                        value_len = value != None and len(str(value)) or 0

                        if value_len > 0 and ( form_old_dict.get(name) != value ):
                            TransactionUpdateHistory( transaction_type='1', transaction_id=kwargs.get('object_id'), field_name=name, field_value=(value and value or ''), timestamp=datetime.now() ).save()

    if not permission:
        permission = 'Management.change_' + model_name
    if request.user.has_perm(permission):
        return UpdateView.as_view(*args, **kwargs)
    else:
        return HttpResponse('No permission. contact Elad.')

class HouseDetailView(LoginRequiredMixin, DetailView):
    model = House
    context_object_name = 'house'
    template_name = 'Management/house_details.html'
    
class SignupDetailView(LoginRequiredMixin, DetailView):
    model = Signup
    context_object_name = 'signup'
    template_name = 'Management/signup_details.html'

@login_required
def employeecheck_list(request):
    month = date.today()
    sum_check_amount, sum_invoice_amount, sum_diff_check_invoice, sum_salary_amount, sum_diff_check_salary = 0,0,0,0,0
    from_date, to_date = None,None
    checks = EmployeeCheck.objects.none()
    if len(request.GET):
        form = EmployeeCheckFilterForm(request.GET)
        if form.is_valid():
            from_year = form.cleaned_data['from_year']
            from_month = form.cleaned_data['from_month']
            to_year = form.cleaned_data['to_year']
            to_month = form.cleaned_data['to_month']
            division_type, expense_type, employee = form.cleaned_data['division_type'],form.cleaned_data['expense_type'],form.cleaned_data['employee']
            
            from_date = date(from_year, from_month, 1)
            to_date = date(to_month == 12 and to_year + 1 or to_year, to_month == 12 and 1 or to_month + 1, 1)
            checks = EmployeeCheck.objects.filter(issue_date__range = (from_date, to_date))
        
            if division_type:
                checks = checks.filter(division_type = division_type)
            if expense_type:
                checks = checks.filter(expense_type = expense_type)
            if employee:
                checks = checks.filter(employee = employee)
                
            for check in checks:
                sum_check_amount += check.amount
                if check.invoice:
                    sum_invoice_amount += check.invoice.amount
                    sum_diff_check_invoice += check.diff_amount_invoice
                salary = check.salary
                if salary:
                    sum_salary_amount += salary.amount
                    sum_diff_check_salary += check.diff_amount_salary
    else:
        form = EmployeeCheckFilterForm()
    
    context = {
        'checks':checks, 
        'from_date':from_date, 
        'to_date':to_date, 
        'filterForm':form,
        'sum_check_amount':sum_check_amount, 
        'sum_invoice_amount':sum_invoice_amount, 
        'sum_diff_check_invoice':sum_diff_check_invoice, 
        'sum_salary_amount':sum_salary_amount, 
        'sum_diff_check_salary':sum_diff_check_salary
    }

    return render(request, 'Management/employeecheck_list.html', context)

### Advance Payment Views ###

class AdvancePaymentListView(LoginRequiredMixin, ListView):
    model = AdvancePayment

    def get_queryset(self):
        return AdvancePayment.objects.filter(is_paid=None)

class AdvancePaymentCreate(PermissionRequiredMixin, CreateView):
    model = AdvancePayment
    form_class = AdvancePaymentForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_advancepayments'

class AdvancePaymentUpdate(PermissionRequiredMixin, UpdateView):
    model = AdvancePayment
    form_class = AdvancePaymentForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_advancepayments'

class AdvancePaymentDelete(PermissionRequiredMixin, DeleteView):
    model = AdvancePayment
    success_url = '/advancepayments'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_advancepayments'

@permission_required('Management.delete_advancepayment')
def advance_payment_toloan(request, id):
    ap = AdvancePayment.objects.get(pk=id)
    if request.method == 'POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            form.save()
            ap.to_loan()
    else:
        form = LoanForm(initial={'employee':ap.employee.id, 'amount':ap.amount, 'year':ap.date.year, 'month':ap.date.month})
   
    return render(request, 'Management/object_edit.html', {'form':form})

### Loan Views ###

class LoanListView(PermissionRequiredMixin, ListView):
    model = Loan
    permission_required = 'Management.list_loan'

    def get_queryset(self):
        return Loan.objects.all()

class LoanCreate(PermissionRequiredMixin, CreateView):
    model = Loan
    form_class = LoanForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_loan'

class LoanUpdate(PermissionRequiredMixin, UpdateView):
    model = Loan
    form_class = LoanForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_loan'

class LoanDelete(PermissionRequiredMixin, DeleteView):
    model = Loan
    success_url = '/loans'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_loan'

### Lawer Views ###

class LawyerListView(LoginRequiredMixin, ListView):
    model = Lawyer

    def get_queryset(self):
        return Lawyer.objects.all()

class LawyerCreate(PermissionRequiredMixin, CreateView):
    model = Lawyer
    fields = ('first_name','last_name','cell_phone','mail','address','role','phone')
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_lawyer'

class LawyerUpdate(PermissionRequiredMixin, UpdateView):
    model = Lawyer
    fields = ('first_name','last_name','cell_phone','mail','address','role','phone')
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_lawyer'

class LawyerDelete(PermissionRequiredMixin, DeleteView):
    model = Lawyer
    success_url = '/lawyers'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_lawyer'

### Madad BI Views ###

class MadadBIListView(LoginRequiredMixin, ListView):
    model = MadadBI

    def get_queryset(self):
        return MadadBI.objects.all()

class MadadBICreate(PermissionRequiredMixin, CreateView):
    model = MadadBI
    form_class = MadadBIForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_madadbi'

class MadadBIUpdate(PermissionRequiredMixin, UpdateView):
    model = MadadBI
    form_class = MadadBIForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_madadbi'

class MadadBIDelete(PermissionRequiredMixin, DeleteView):
    model = MadadBI
    success_url = '/madadbi'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_madadbi'

### Madad CP Views ###

class MadadCPListView(LoginRequiredMixin, ListView):
    model = MadadCP

    def get_queryset(self):
        return MadadCP.objects.all()

class MadadCPCreate(PermissionRequiredMixin, CreateView):
    model = MadadCP
    form_class = MadadCPForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_madadcp'

class MadadCPUpdate(PermissionRequiredMixin, UpdateView):
    model = MadadCP
    form_class = MadadCPForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_madadcp'

class MadadCPDelete(PermissionRequiredMixin, DeleteView):
    model = MadadCP
    success_url = '/madadcp'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_madadcp'

### Tax Views ###

class TaxListView(LoginRequiredMixin, ListView):
    model = Tax

    def get_queryset(self):
        return Tax.objects.all()

class TaxCreate(PermissionRequiredMixin, CreateView):
    model = Tax
    form_class = TaxForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_tax'

class TaxUpdate(PermissionRequiredMixin, UpdateView):
    model = Tax
    form_class = TaxForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_tax'

class TaxDelete(PermissionRequiredMixin, DeleteView):
    model = Tax
    success_url = '/tax'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_tax'

### Link Views ###

class LinkListView(LoginRequiredMixin, ListView):
    model = Link

    def get_queryset(self):
        return Link.objects.all()

class LinkCreate(PermissionRequiredMixin, CreateView):
    model = Link
    fields = ('name','url')
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_link'

class LinkUpdate(PermissionRequiredMixin, UpdateView):
    model = Link
    fields = ('name','url')
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_link'

class LinkDelete(PermissionRequiredMixin, DeleteView):
    model = Link
    success_url = '/links'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_link'

### Car Views ###

class CarListView(LoginRequiredMixin, ListView):
    model = Car

    def get_queryset(self):
        return Car.objects.all()

class CarCreate(PermissionRequiredMixin, CreateView):
    model = Car
    fields = ('number','owner','insurance_expire_date','insurance_man','insurance_phone',
        'tow_company','tow_phone','compulsory_insurance_cost','comprehensive_insurance_cost')
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_car'

class CarUpdate(PermissionRequiredMixin, UpdateView):
    model = Car
    fields = ('number','owner','insurance_expire_date','insurance_man','insurance_phone',
        'tow_company','tow_phone','compulsory_insurance_cost','comprehensive_insurance_cost')
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_car'

class CarDelete(PermissionRequiredMixin, DeleteView):
    model = Car
    success_url = '/cars'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_car'

### NHCommission Views ###

class NHCommissionCreate(PermissionRequiredMixin, CreateView):
    model = NHCommission
    form_class = NHCommissionForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_nhcommission'

class NHCommissionUpdate(PermissionRequiredMixin, UpdateView):
    model = NHCommission
    form_class = NHCommissionForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_nhcommission'

class NHCommissionDelete(PermissionRequiredMixin, DeleteView):
    model = NHCommission
    success_url = '/nhcommissions'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_nhcommission'

### Demand Views ###

class DemandRemarksUpdate(PermissionRequiredMixin, UpdateView):
    model = Demand
    form_class = DemandRemarksForm
    template_name = 'Management/object_edit.html'
    success_url = 'remarks'
    permission_required = 'Management.demand_remarks'
    
class DemandSaleCountUpdate(PermissionRequiredMixin, UpdateView):
    model = Demand
    form_class = DemandSaleCountForm
    template_name = 'Management/object_edit.html'
    success_url = 'salecount'
    permission_required = 'Management.demand_sale_count'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        
        context['title'] = u"עדכון מס' מכירות צפוי"
        return context

### Account ###

class AccountUpdate(PermissionRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_account'

### EPCommission ###

class EPCommissionUpdate(PermissionRequiredMixin, UpdateView):
    model = EPCommission
    fields = ('start_date','end_date','max')
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_epcommission'

### NHEmployee ###

class NHEmployeeUpdate(PermissionRequiredMixin, UpdateView):
    model = NHEmployee
    form_class = NHEmployeeForm
    permission_required = 'Management.change_nhemployee'

class NHEmployeeEndUpdate(PermissionRequiredMixin, UpdateView):
    model = NHEmployee
    form_class = EmployeeEndForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_nhemployee'

@permission_required('Management.list_check')
def check_list(request):
    month = date.today()
    checks = PaymentCheck.objects.none()
    from_date, to_date = None, None
    sum_check_amount, sum_invoice_amount, sum_diff_check_invoice = 0,0,0
    if len(request.GET):
        form = CheckFilterForm(request.GET)
        if form.is_valid():
            from_year = form.cleaned_data['from_year']
            from_month = form.cleaned_data['from_month']
            to_year = form.cleaned_data['to_year']
            to_month = form.cleaned_data['to_month']
            division_type, expense_type = form.cleaned_data['division_type'], form.cleaned_data['expense_type']
            
            from_date = date(from_year, from_month, 1)
            to_date = date(to_month == 12 and to_year + 1 or to_year, to_month == 12 and 1 or to_month + 1, 1)
            checks = PaymentCheck.objects.filter(issue_date__range = (from_date, to_date))
            if division_type:
                checks = checks.filter(division_type = division_type)
            if expense_type:
                checks = checks.filter(expense_type = expense_type)
                
            for check in checks:
                sum_check_amount += check.amount
                if check.invoice:
                    sum_invoice_amount += check.invoice.amount
                    sum_diff_check_invoice += check.diff_amount_invoice
    else:
        form = CheckFilterForm()

    context = {
        'checks':checks, 
        'from_date':from_date, 
        'to_date':to_date, 
        'filterForm':form,
        'sum_check_amount':sum_check_amount,
        'sum_invoice_amount':sum_invoice_amount,
        'sum_diff_check_invoice':sum_diff_check_invoice
        }

    return render(request, 'Management/check_list.html', context)

def process_check_base_form(form):
    division_type, expense_type = form.cleaned_data['new_division_type'], form.cleaned_data['new_expense_type']
    supplier_type = 'new_supplier_type' in form.cleaned_data and form.cleaned_data['new_supplier_type'] 
    if division_type:
        dt, new = DivisionType.objects.get_or_create(name=division_type)
        form.cleaned_data['division_type'] = dt
    if expense_type:
        et, new = ExpenseType.objects.get_or_create(name=expense_type)
        form.cleaned_data['expense_type'] = et
    if supplier_type:
        et, new = SupplierType.objects.get_or_create(name=supplier_type)
        form.cleaned_data['supplier_type'] = et        

@permission_required('Management.add_check')
def check_add(request):
    if request.method == 'POST':
        accountForm = AccountForm(request.POST)
        form = CheckForm(request.POST)
        if accountForm.has_changed() and accountForm.is_valid():
            form.instance.account = accountForm.save()
        else:
            form.instance.account = None
        if form.is_valid():
            process_check_base_form(form)
            form.save()
            accountForm = AccountForm()
            form = CheckForm()
            if 'addanother' in request.POST:
                accountForm = AccountForm()
                form = CheckForm()
    else:
        accountForm = AccountForm()
        form = CheckForm()
        
    return render(request, 'Management/check_edit.html', 
                              { 'accountForm':accountForm, 'form':form,'title':u"הזנת צ'ק אחר" },
                              )
    
@permission_required('Management.edit_check')
def check_edit(request, id):
    c = PaymentCheck.objects.get(pk=id)
    if request.method == 'POST':
        accountForm = AccountForm(request.POST, instance = c.account)
        form = CheckForm(request.POST, instance = c)
        if accountForm.has_changed() and accountForm.is_valid():
            form.instance.account = accountForm.save()
        if form.is_valid():
            process_check_base_form(form)
            form.save()
            if 'addanother' in request.POST:
                accountForm = AccountForm()
                form = CheckForm()
    else:
        accountForm = AccountForm()
        form = CheckForm()
        
    return render(request, 'Management/check_edit.html', 
                              { 'accountForm':accountForm, 'form':form,'title':u"הזנת צ'ק אחר" },
                              )

class PaymentCheckDelete(PermissionRequiredMixin, DeleteView):
    model = PaymentCheck
    success_url = '/checks'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_paymentcheck'

def apply_employee_check(ec):
    if ec.purpose_type.id == PurposeType.AdvancePayment:
        query = AdvancePayment.objects.filter(employee = ec.employee, year = ec.year, month=ec.month)
        if query.count > 0:
            ap = AdvancePayment(employee = ec.employee, year = ec.year, month=ec.month)
        else:
            ap = query[0]
        ap.amount = ec.amount
        ap.save()
    elif ec.purpose_type.id == PurposeType.Loan:
        query = Loan.objects.filter(employee = ec.employee, year = ec.year, month = ec.month)
        if query.count > 0:
            loan = Loan(employee = ec.employee, year = ec.year, month = ec.month)
        else:
            loan = query[0]
        loan.amount = ec.amount
        loan.save()
        
@permission_required('Management.add_employeecheck')
def employeecheck_add(request):
    if request.method == 'POST':
        form = EmployeeCheckForm(request.POST)
        if form.is_valid():
            process_check_base_form(form)
            ec = form.save()
            apply_employee_check(ec)
            if 'addanother' in request.POST:
                form = EmployeeCheckForm()
    else:
        form = EmployeeCheckForm()
        
    return render(request, 'Management/object_edit.html', 
                              { 'form':form,'title':u"הזנת צ'ק לעובד" },
                              )
        
@permission_required('Management.edit_employeecheck')
def employeecheck_edit(request, id):
    ec = EmployeeCheck.objects.get(pk=id)
    if request.method == 'POST':
        form = EmployeeCheckForm(request.POST, instance = ec)
        if form.is_valid():
            process_check_base_form(form)
            ec = form.save()
            apply_employee_check(ec)
            if 'addanother' in request.POST:
                form = EmployeeCheckForm()
    else:
        form = EmployeeCheckForm()
        
    return render(request, 'Management/object_edit.html', 
                              { 'form':form,'title':u"הזנת צ'ק לעובד" },
                              )

class EmployeeCheckDelete(PermissionRequiredMixin, DeleteView):
    model = EmployeeCheck
    success_url = '/employeechecks'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_employeecheck'

def signup_list(request, project_id):
    month = date.today()
    y = int(request.GET.get('year', month.year))
    m = int(request.GET.get('month', month.month))
    month = datetime(y,m,1)
    form = MonthForm(initial={'year':y,'month':m})
    p = Project.objects.get(pk = project_id)
    signups = p.signups(y, m)
    return render(request, 'Management/signup_list.html', 
                          { 'project':p, 'signups':signups, 'month':month, 'filterForm':form },
                          )

@permission_required('Management.add_signup')
def signup_edit(request, id=None, house_id=None, project_id=None): 
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('add')
    else:
        if id:
            signup = Signup.objects.get(pk=id)
            h = signup.house
            form = SignupForm(instance=signup)
        elif house_id:
            h = House.objects.get(pk= house_id)  
            signup = h.get_signup()
            form = signup and SignupForm(instance = signup) or SignupForm()
        if house_id or id:
            form.fields['house'].initial = h.id
            form.fields['building'].initial = h.building.id
            form.fields['project'].initial = h.building.project.id
            form.fields['house'].queryset = h.building.houses.all()
            form.fields['building'].queryset = h.building.project.non_deleted_buildings()
        elif project_id:
            form = SignupForm(initial = {'project':project_id})
            form.fields['building'].queryset = Building.objects.filter(project__id = project_id, is_deleted=False)
        else:
            form = SignupForm()
            
    return render(request, 'Management/signup_edit.html', 
                              { 'form':form },
                              )

@permission_required('Management.change_signup')
def signup_cancel(request, id):
    s = Signup.objects.get(pk=id)
    cancel = s.cancel or SignupCancel()
    if request.method=='POST':
        form = SignupCancelForm(request.POST)
        if form.is_valid():
            s.cancel = form.save()
            s.save()
    else:
        form = SignupCancelForm(instance=cancel)
    return render(request, 'Management/object_edit.html', 
                              { 'form':form },
                              )

@permission_required('Management.add_account')
def employee_account(request, id, model):
    employee = model.objects.get(pk=id)
    try:
        acc = employee.account
    except Account.DoesNotExist:
        acc = Account()
    if request.method == 'POST':
        form = AccountForm(data=request.POST, instance=acc) 
        if form.is_valid(): 
            employee.account = form.save()
            employee.save()
    else:
        form = AccountForm(instance=acc)
        
    return render(request, 'Management/object_edit.html', 
                              { 'form':form },
                              )

@permission_required('Management.list_demand')
def demand_function(request,id , function):
    d = Demand.objects.get(pk=id)
    function(d)
    return HttpResponse('ok')

@permission_required('Management.list_demand')
def demand_return_to_calc(request, id):
    demand = Demand.objects.get(pk = id)
    demand.close()
    return HttpResponseRedirect('/demandsold/?year=%s&month=%s' % (demand.year,demand.month))

@permission_required('Management.list_demand')
def demand_calc(request, id):
    # end the revision created by the middleware - i want manual control of the revision
    #reversion.revision.end()
        
    d = Demand.objects.get(pk=id)
    c = d.project.commissions.get()
    if c.commission_by_signups or c.c_zilber:
        if c.commission_by_signups:
            demands = list(Demand.objects.filter(project = d.project))
        elif c.c_zilber:
            demand = d
            demands = []
            while demand.zilber_cycle_index() > 1:
                demands.insert(0, demand)
                demand = demand.get_previous_demand()
            demands.insert(0, demand)
        
        # exclude all demands that were already sent! to include them you must manually change their status!!!!!
        demands = [demand for demand in demands if demand.statuses.count() == 0 or (demand.statuses.count() > 0 and
                    demand.statuses.latest().type.id not in (DemandStatusType.Sent, DemandStatusType.Finished))]
            
        #delete all commissions and sale commission details before re-calculating
        for demand in demands:
            for s in demand.statuses.all():
                s.delete()
            for s in demand.get_sales():
                for scd in s.project_commission_details.all():
                    scd.delete()
        for d2 in demands:
            d2.calc_sales_commission()
            demand = Demand.objects.get(pk=d2.id)
            if demand.get_next_demand() != None:
                demand.finish()
                time.sleep(1)
    else:
        for s in d.get_sales():
            for scd in s.project_commission_details.all():
                scd.delete()
        d.calc_sales_commission()
        
    return HttpResponseRedirect('/demandsold/?year=%s&month=%s' % (d.year,d.month))

@permission_required('Management.projects_profit')
def projects_profit(request):
    def _process_demands(demands):
        projects = []
        for p, demand_iter in itertools.groupby(demands, lambda demand: demand.project):
            p.sale_count, p.total_income, p.total_expense, p.profit, p.total_sales_amount = 0,0,0,0,0
            p.employee_expense = {}
            
            for d in demand_iter:
                tax_val = Tax.objects.filter(date__lte=date(d.year, d.month,1)).latest().value / 100 + 1
    
                total_amount = d.get_total_amount() / tax_val
                sales = d.get_sales()
                sale_count = len(sales)
                p.total_income += total_amount
                p.sale_count += sale_count
                for s in sales:
                    p.total_sales_amount += s.include_tax and s.price or (s.price / tax_val)
            
            projects.append(p)
            
        return projects
    def _process_salaries(salaries, projects):
        for s in salaries:
            tax_val = Tax.objects.filter(date__lte=date(s.year, s.month,1)).latest().value / 100 + 1
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
            
            demands = Demand.objects.range(from_year, from_month, to_year, to_month).order_by('project')
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
        month = common.current_month()
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

    return render(request, 'Management/projects_profit.html', context)

def set_demand_diff_fields(demands):
    # extract demand ids
    demand_ids = [d.id for d in demands]
    
    # construct a map of demand id to DemandDiff list
    diffs = DemandDiff.objects \
        .filter(demand_id__in=demand_ids) \
        .order_by('demand_id')

    diff_groups = itertools.groupby(diffs, lambda diff: diff.demand_id)

    demand_diff_map = {demand_id:list(demand_diffs) for (demand_id, demand_diffs) in diff_groups}

    diff_type_to_field = {
        u'קבועה': 'fixed_diff',
        u'משתנה': 'var_diff',
        u'בונוס': 'bonus_diff',
        u'קיזוז': 'fee_diff',
        u'התאמה': 'adjust_diff',
    }

    for demand in demands:
        total_diff_amount = 0

        if demand.id in demand_diff_map:
            demand_diffs = demand_diff_map[demand.id]
        else:
            demand_diffs = []

        for diff in demand_diffs:
            total_diff_amount += diff.amount

            if diff.type in diff_type_to_field:
                field_name = diff_type_to_field[diff.type]
                
                # set '*_diff' fields
                setattr(demand, field_name, diff)
        
        # set 'total_amount' field
        demand.total_amount = demand.sales_commission + total_diff_amount

def set_demand_is_fixed(demands):
    # extract demand ids
    demand_ids = [d.id for d in demands]

    # count modified sales for demand
    query = Sale.objects \
        .filter(demand_id__in=demand_ids) \
        .exclude(salehousemod=None, salepricemod=None, salepre=None, salereject=None) \
        .values('demand_id') \
        .annotate(cnt=Count('demand_id'))

    counts_by_demand = {row['demand_id']:row['cnt'] for row in query}

    for demand in demands:
        cnt = counts_by_demand.get(demand.id, 0)
        demand.is_fixed = cnt > 0

def set_demand_last_status(demands):
    # extract demand ids
    demand_ids = [d.id for d in demands]

    statuses = DemandStatus.objects \
        .filter(demand_id__in=demand_ids) \
        .order_by('demand_id','-date')

    statuses_by_demand = itertools.groupby(statuses, lambda status: status.demand_id)

    # construct a map of (demand_id, last_status)
    last_status_by_demand = {demand_id:next(demand_statuses, None) for (demand_id, demand_statuses) in statuses_by_demand}

    for demand in demands:
        demand.last_status = last_status_by_demand.get(demand.id, None)

def set_demand_open_reminders(demands):
    for demand in demands:
        demand.open_reminders = [r for r in demand.reminders.all()
            if r.statuses.latest().type_id not in (ReminderStatusType.Deleted,ReminderStatusType.Done)]

def set_demand_invoice_payment_fields(demands):
    for demand in demands:
        # sum invoice amounts
        invoice_amounts = [i.amount for i in demand.invoices.all()]
        demand.invoices_amount = sum(invoice_amounts) if len(invoice_amounts) > 0 else None

        # sum invoice offset amounts
        invoice_offset_amounts = [i.offset.amount for i in demand.invoices.all() if i.offset != None]
        demand.invoice_offsets_amount = sum(invoice_offset_amounts) if len(invoice_offset_amounts) > 0 else None

        demand.total_amount_offset = (demand.invoices_amount or 0) + (demand.invoice_offsets_amount or 0)

        # sum payment amounts
        payment_amounts = [p.amount for p in demand.payments.all()]
        demand.payments_amount = sum(payment_amounts) if len(payment_amounts) > 0 else None

        demand.diff_invoice = demand.total_amount_offset - demand.total_amount
        demand.diff_invoice_payment = (demand.payments_amount or 0) - demand.total_amount_offset

        demand.is_fully_paid = demand.force_fully_paid or (
            demand.total_amount == demand.total_amount_offset and demand.total_amount == demand.payments_amount)

def set_demand_total_fields(
    demands, 
    from_year, from_month, to_year, to_month):
    # extract project ids
    project_ids = [d.project_id for d in demands]

    # get sales for all projects
    all_sales = Sale.objects \
        .contractor_pay_range(from_year, from_month, to_year, to_month) \
        .filter(
            house__building__project_id__in=project_ids,
            commission_include=True, 
            salecancel__isnull=True) \
        .order_by('house__building__project_id', 'contractor_pay_year', 'contractor_pay_month') \
        .select_related('house__building')

    # group sales by (project id, year, month)
    sale_groups = itertools.groupby(
        all_sales, 
        lambda sale: (sale.house.building.project_id, sale.contractor_pay_year, sale.contractor_pay_month))

    sales_map = {map_key: list(sales) for (map_key, sales) in sale_groups}

    for demand in demands:
        map_key = (demand.project_id, demand.year, demand.month)

        sales_list = sales_map.get(map_key, [])

        demand.sales_list = sales_list
        demand.sales_count = len(sales_list)
        demand.sales_amount = sum([sale.price_final for sale in sales_list])

@permission_required('Management.list_demand')
def demand_old_list(request):
    year, month = None, None
    ds, unhandled_projects = [], []
    total_sales_count,total_sales_amount, total_amount = 0,0,0
        
    if len(request.GET):
        form = MonthForm(request.GET)
        if form.is_valid():
            year, month = form.cleaned_data['year'], form.cleaned_data['month']
    else:
        current = common.current_month()
        year, month = current.year, current.month
        form = MonthForm(initial={'year':year,'month':month})
        
    if year and month:
        ds = Demand.objects \
            .filter(year = year, month = month) \
            .annotate(Count('statuses')) \
            .prefetch_related('reminders__statuses') \
            .select_related('project')

        unhandled_projects.extend(Project.objects.active())

        set_demand_total_fields(ds, year, month, year, month)
        set_demand_diff_fields(ds)
        set_demand_is_fixed(ds)
        set_demand_last_status(ds)
        set_demand_open_reminders(ds)

        for d in ds:
            total_sales_count += d.sales_count
            total_sales_amount += d.sales_amount
            total_amount += d.total_amount

            if d.last_status and d.last_status.type_id in [DemandStatusType.Sent, DemandStatusType.Finished]:
                try:
                    unhandled_projects.remove(d.project)
                except ValueError:
                    pass
        
    context =  { 
        'demands':ds, 
        'month':date(year, month, 1),
        'filterForm':form,
        'total_sales_count':total_sales_count,
        'total_sales_amount':total_sales_amount,
        'total_amount':total_amount,
        'unhandled_projects':unhandled_projects
    }

    return render(request, 'Management/demand_old_list.html', context)

def nhemployee_salary_send(request, nhbranch_id, year, month):
    pass
    
def nhemployee_salary_pdf(request, nhbranch_id, year, month):
    nhb = NHBranch.objects.get(pk = nhbranch_id)

    salaries = NHEmployeeSalary.objects \
        .select_related('nhemployee__employment_terms__hire_type') \
        .nondeleted() \
        .filter(nhbranch = nhb, year = year, month= month) \
        .order_by('id')

    employee_by_id = {s.nhemployee.id:s.nhemployee for s in salaries}

    set_salary_base_fields(
        salaries, 
        employee_by_id, 
        year, month, year, month)

    set_salary_status_date(salaries)

    approved_salaries = [salary for salary in salaries if salary.approved_date]

    nhsales = NHSale.objects.filter(nhmonth__year__exact = year, nhmonth__month__exact = month, nhmonth__nhbranch = nhb)
    title = u'שכר עבודה לסניף %s לחודש %s\%s' % (nhb, year, month)

    writer = EmployeeSalariesBookKeepingWriter(approved_salaries, title, nhsales)
    
    return build_and_return_pdf(writer)

@permission_required('Management.change_salaryexpenses')
def employee_salary_expenses(request, salary_id):
    salary = EmployeeSalaryBase.objects.get(pk=salary_id)
    
    # set to EmployeeSalary or NHEmployeeSalary
    salary = salary.derived

    employee = salary.get_employee()
    terms = employee.employment_terms

    year, month = salary.year, salary.month

    set_salary_base_fields(
        [salary],
        {employee.id:employee},
        year, month, year, month)

    expenses = salary.expenses or SalaryExpenses(employee = employee, year = year, month = month)

    if request.method=='POST':
        form = SalaryExpensesForm(request.POST, instance= expenses)
        if form.is_valid():
            form.save()
    else:
        vacation = terms.salary_base and (terms.salary_base / 24) or (2500/12)
        form = SalaryExpensesForm(instance= expenses, initial={'vacation':vacation})

    context = {'form': form, 'neto': salary.neto or 0}
    
    return render(request, 'Management/salaryexpenses_edit.html', context)

@permission_required('Management.change_employeesalary')
def employee_salary_approve(request, id):
    es = EmployeeSalaryBase.objects.get(pk=id)
    es.approve()

    if hasattr(es,'employeesalary'):
        url = reverse('salary-list') + '?year=%s&month=%s' % (es.year, es.month)
    elif hasattr(es,'nhemployeesalary'):
        url = reverse('nh-salary-list') + '?year=%s&month=%s' % (es.year, es.month)

    return HttpResponseRedirect(url)

@permission_required('Management.change_employeesalary')
def salary_expenses_approve(request, id):
    se = SalaryExpenses.objects.get(pk=id)
    se.approve()
    se.save()
    url = reverse('salary-expenses') + '?year=%s&month=%s' % (se.year, se.month)
    return HttpResponseRedirect(url)
    
class SalaryExpensesUpdate(PermissionRequiredMixin, UpdateView):
    model = SalaryExpenses
    exclude = ('approved_date',)
    template_name = 'Management/salaryexpenses_edit.html'
    permission_required = 'Management.change_salaryexpenses'

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

@permission_required('Management.list_employeesalary')
def employee_salary_list(request):
    current = common.current_month()
    year = int(request.GET.get('year', current.year))
    month = int(request.GET.get('month', current.month))
    salaries = []
    today = date.today()
    if date(year, month, 1) <= today:
        employees = Employee.objects \
            .select_related('employment_terms__hire_type','rank') \
            .prefetch_related('projects') \
            .filter(employment_terms__isnull=False)

        for e in employees:
            # do not include employees who did not start working by the month selected
            if year < e.work_start.year or (year == e.work_start.year and month < e.work_start.month):
                continue
            # do not include employees who finished working by the month selected
            if e.work_end and (year > e.work_end.year or (year == e.work_end.year and month > e.work_end.month)):
                continue
            es, new = EmployeeSalary.objects.get_or_create(employee = e, month = month, year = year)
            if new:
                es.calculate()
                es.save()
            else:
                if es.is_deleted:
                    continue

            # set employee field with already-loaded fields
            es.employee = e

            salaries.append(es)
        
        employee_by_id = {employee.id:employee for employee in employees}

        enrich_employee_salaries(salaries, employee_by_id, year, month, year, month)

        set_loan_fields(employees)

    context = {
        'salaries':salaries, 
        'month': date(int(year), int(month), 1),
        'filterForm':MonthForm(initial={'year':year,'month':month})
        }
    
    return render(request, 'Management/employee_salaries.html', context)

class SalaryExpensesListView(PermissionRequiredMixin, ListView):
    model = EmployeeSalary
    template_name = 'Management/salaries_expenses.html'
    context_object_name = 'salaries'
    permission_required = 'Management.list_salaryexpenses'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        current = common.current_month()
        self.year = int(self.request.GET.get('year', current.year))
        self.month = int(self.request.GET.get('month', current.month))

    def get_queryset(self):
        salaries = EmployeeSalary.objects.nondeleted() \
            .select_related('employee__employment_terms__hire_type', 'employee__rank') \
            .prefetch_related('employee__projects') \
            .filter(year = self.year, month = self.month)

        employee_by_id = {s.employee.id:s.employee for s in salaries}

        enrich_employee_salaries(salaries, employee_by_id, self.year, self.month, self.year, self.month)

        return salaries

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        
        context['month'] = date(int(self.year), int(self.month), 1)
        context['filterForm'] = MonthForm(initial={'year':self.year,'month':self.month})

        return context

class NHSalaryExpensesListView(PermissionRequiredMixin, ListView):
    model = EmployeeSalary
    template_name = 'Management/salaries_expenses.html'
    context_object_name = 'salaries'
    permission_required = 'Management.nh_salaries_expenses'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        current = common.current_month()
        self.year = int(self.request.GET.get('year', current.year))
        self.month = int(self.request.GET.get('month', current.month))

    def get_queryset(self):
        salaries = NHEmployeeSalary.objects.nondeleted() \
            .select_related('nhemployee__employment_terms__hire_type') \
            .filter(year = self.year, month = self.month)

        employee_by_id = {s.nhemployee.id:s.nhemployee for s in salaries}

        enrich_nh_employee_salaries(salaries, employee_by_id, self.year, self.month, self.year, self.month)

        return salaries

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        
        context['month'] = date(int(self.year), int(self.month), 1)
        context['filterForm'] = MonthForm(initial={'year':self.year,'month':self.month})

        return context

@permission_required('Management.list_nhemployeesalary')
def nhemployee_salary_list(request):
    current = common.current_month()
    year = int(request.GET.get('year', current.year))
    month = int(request.GET.get('month', current.month))
    
    salaries = []

    # key is NHBranch, value is a list of NHEmployeeSalary objects
    branch_list = {}

    for nhbe in NHBranchEmployee.objects.month(year, month):
        es, new = NHEmployeeSalary.objects.get_or_create(nhemployee = nhbe.nhemployee, nhbranch = nhbe.nhbranch,
                                                         month = month, year = year)
        if not new and es.is_deleted:
            continue
        #if (new or not es.commissions or not es.base or not es.admin_commission) and es.approved_date == None: 
        if new:
            es.calculate()
            es.save()
        
        salaries.append(es)

        branch_sales = branch_list.setdefault(nhbe.nhbranch, [])
        branch_sales.append(es)

    employee_by_id = {s.nhemployee.id:s.nhemployee for s in salaries}

    enrich_nh_employee_salaries(salaries, employee_by_id, year, month, year, month)

    set_loan_fields(employee_by_id.values())

    return render(request, 'Management/nhemployee_salaries.html', 
                              {'branch_list':branch_list, 'month': date(int(year), int(month), 1),
                               'filterForm':MonthForm(initial={'year':year,'month':month})},
                               )

@permission_required('Management.salaries_bank')
def salaries_bank(request):
    if request.method == 'POST':
        form = MonthForm(request.POST)
        if form.is_valid():
            month, year = form.cleaned_data['month'], form.cleaned_data['year']

            query = EmployeeSalaryBase.objects.select_related(
                'employeesalary__employee__employment_terms',
                'employeesalary__employee__account',
                'nhemployeesalary__nhemployee__employment_terms',
                'nhemployeesalary__nhemployee__account')

            if 'pdf' in request.POST:
                salary_ids = [key.replace('salary-','') for key in request.POST if key.startswith('salary-')]
                salaries = query.filter(pk__in = salary_ids)
            elif 'filter' in request.POST:
                salaries = query.filter(month=month, year=year)
                
            salaries.select_related(
                'employeesalary__employee__employment_terms',
                'employeesalary__employee__account',
                'nhemployeesalary__nhemployee__employment_terms',
                'nhemployeesalary__nhemployee__account')

            # replace base objects with derived
            salaries = [s.derived for s in salaries]

            # extract employees from salaries
            employees = [salary.get_employee() for salary in salaries]

            # create map
            employee_by_id = {e.id:e for e in employees}

            set_salary_base_fields(
                salaries, 
                employee_by_id,
                year, month, year, month)

            if 'pdf' in request.POST:
                writer = SalariesBankWriter(salaries, month, year)
                return build_and_return_pdf(writer)
        else:
            raise ValidationError
    else:
        now = datetime.now()
        month, year = now.month, now.year
        args = {'month':month, 'year':year}
        form = MonthForm(initial = args)
        salaries = EmployeeSalaryBase.objects.filter(**args)
    
    for salary in salaries:
        employee = salary.get_employee()
        if isinstance(employee, Employee):
            salary.division = u'נווה העיר'
        elif isinstance(employee, NHEmployee):
            salary.division = str(salary.nhemployeesalary.nhbranch)
    
    salaries = list(salaries)
    salaries.sort(key = lambda salary: salary.division)

    return render(request, 'Management/salaries_bank.html', 
                              {'salaries':salaries,'filterForm':form, 'month':datetime(year, month, 1)},
                               )  

class EmployeeSalaryUpdate(PermissionRequiredMixin, UpdateView):
    model = EmployeeSalary
    form_class = EmployeeSalaryForm
    template_name = 'Management/employee_salary_edit.html'
    permission_required = 'Management.change_employeesalary'

class NHEmployeeSalaryUpdate(PermissionRequiredMixin, UpdateView):
    model = NHEmployeeSalary
    form_class = NHEmployeeSalaryForm
    template_name = 'Management/nhemployee_salary_edit.html'
    permission_required = 'Management.change_nhemployeesalary'

def employee_salary_pdf(request, year, month):

    salaries = EmployeeSalary.objects \
        .select_related('employee__employment_terms__hire_type') \
        .nondeleted() \
        .filter(year = year, month= month) \
        .order_by('id')

    employee_by_id = {s.employee.id:s.employee for s in salaries}

    set_salary_base_fields(
        salaries, 
        employee_by_id, 
        year, month, year, month)

    set_salary_status_date(salaries)

    approved_salaries = [salary for salary in salaries if salary.approved_date]

    title = u'שכר עבודה למנהלי פרויקטים לחודש %s\%s' % (year, month)

    writer = EmployeeSalariesBookKeepingWriter(approved_salaries, title)

    return build_and_return_pdf(writer)

def employee_salary_calc(request, model, id):
    es = model.objects.get(pk=id)
    es.calculate()
    es.save()
    
    if model == EmployeeSalary:
        url = reverse('salary-list') + '?year=%s&month=%s' % (es.year, es.month)
    elif model == NHEmployeeSalary:
        url = reverse('nh-salary-list') + '?year=%s&month=%s' % (es.year, es.month)

    return HttpResponseRedirect(url)

@permission_required('Management.employee_salary_delete')
def employee_salary_delete(request, model, id):
    es = model.objects.get(pk = id)
    es.mark_deleted()
    es.save()
    
    if model == EmployeeSalary:
        url = reverse('salary-list') + '?year=%s&month=%s' % (es.year, es.month)
    elif model == NHEmployeeSalary:
        url = reverse('nh-salary-list') + '?year=%s&month=%s' % (es.year, es.month)

    return HttpResponseRedirect(url)

class EmployeeSalaryCommissionDetailView(LoginRequiredMixin, DetailView):
    model = EmployeeSalary
    context_object_name = 'salary'
    template_name = 'Management/employee_commission_details.html'

class EmployeeSalaryCheckDetailView(LoginRequiredMixin, DetailView):
    model = EmployeeSalary
    context_object_name = 'salary'
    template_name = 'Management/employee_salary_check_details.html'

class EmployeeSalaryTotalDetailView(LoginRequiredMixin, DetailView):
    model = EmployeeSalary
    context_object_name = 'salary'
    template_name = 'Management/employee_salary_total_details.html'
    

class NHEmployeeSalaryCommissionDetailView(LoginRequiredMixin, DetailView):
    model = NHEmployeeSalary
    context_object_name = 'salary'
    template_name = 'Management/nhemployee_commission_details.html'

class NHEmployeeSalaryCheckDetailView(LoginRequiredMixin, DetailView):
    model = NHEmployeeSalary
    context_object_name = 'salary'
    template_name = 'Management/employee_salary_check_details.html'

class NHEmployeeSalaryTotalDetailView(LoginRequiredMixin, DetailView):
    model = NHEmployeeSalary
    context_object_name = 'salary'
    template_name = 'Management/employee_salary_total_details.html'


@permission_required('Management.list_demand')
def demands_all(request):
    error = None
    if request.method == 'POST':
        houseForm = LocateHouseForm(request.POST)
        demandForm = LocateDemandForm(request.POST)
        if houseForm.is_valid():
            houses = House.objects.filter(building__project = houseForm.cleaned_data['project'], 
                                          building__num = houseForm.cleaned_data['building_num'],
                                          num = houseForm.cleaned_data['house_num'])
            if houses.count() > 0:
                return HttpResponseRedirect('/buildings/%s/house/%s/type1' % (houses[0].building.id, houses[0].id))
            else:
                error = u'לא נמצאה דירה מס %s בבניין מס %s בפרוייקט %s' % (houseForm.cleaned_data['house_num'],
                                                                           houseForm.cleaned_data['building_num'],
                                                                           houseForm.cleaned_data['project'])
        if demandForm.is_valid():
            demands = Demand.objects.filter(project = demandForm.cleaned_data['project'], 
                                            month = demandForm.cleaned_data['month'],
                                            year = demandForm.cleaned_data['year'])
            if demands.count()>0:
                return HttpResponseRedirect('/reports/project_month/%s/%s/%s' % (demands[0].project.id,
                                                                         demands[0].year, demands[0].month))
    
    total_mispaid, total_unpaid, total_nopayment, total_noinvoice, total_notyetpaid = 0,0,0,0,0
    amount_mispaid, amount_unpaid, amount_nopayment, amount_noinvoice, amount_notyetpaid = 0,0,0,0,0
    projects = Project.objects.all()
    for p in projects:
        for d in p.demands_mispaid():
            amount_mispaid += d.get_total_amount()
            total_mispaid += 1
        for d in p.demands_unpaid():
            amount_unpaid += d.get_total_amount()
            total_unpaid += 1
        for d in p.demands.nopayment():
            amount_nopayment += d.get_total_amount()
            total_nopayment += 1
        for d in p.demands.noinvoice():
            amount_noinvoice += d.get_total_amount()
            total_noinvoice += 1
        for d in p.demands_not_yet_paid():
            amount_notyetpaid += d.get_total_amount()
            total_notyetpaid += 1

    return render(request, 'Management/demands_all.html', 
                              { 'projects':projects, 'total_mispaid':total_mispaid, 'total_unpaid':total_unpaid,
                               'total_nopayment':total_nopayment, 'total_noinvoice':total_noinvoice,'total_notyetpaid':total_notyetpaid,
                               'amount_mispaid':amount_mispaid, 'amount_unpaid':amount_unpaid, 'amount_notyetpaid':amount_notyetpaid,
                               'amount_nopayment':amount_nopayment, 'amount_noinvoice':amount_noinvoice,
                               'houseForm':LocateHouseForm(), 
                               'demandForm':LocateDemandForm(),
                               'error':error },
                              )

def employee_list_pdf(request):
    writer = EmployeeListWriter(
        employees = Employee.objects.active(),
        nhemployees = NHEmployee.objects.active())
    return build_and_return_pdf(writer)

class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'Management/employee_list.html'
    context_object_name = 'employee_list'

    def get_queryset(self):
        return Employee.objects.active().select_related('employment_terms__hire_type')
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        
        context['nhbranch_list'] = NHBranch.objects.all()
        return context

class EmployeeArchiveListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'Management/employee_archive.html'
    context_object_name = 'employee'

    def get_queryset(self):
        return Employee.objects.archive()
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        
        context['nhbranch_list'] = NHBranch.objects.all()
        return context

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
        month = common.current_month()
        from_year, from_month, to_year, to_month = month.year, month.month, month.year, month.month
        
    return render(request, 'Management/nh_season_profit.html', 
                              { 'months':months,'totals':totals, 'filterForm':form, 'from_year':from_year, 'from_month': from_month,
                               'to_year': to_year, 'to_month': to_month },
                              )

@permission_required('Management.nhmonth_season')
def nh_season_income(request):
    nhmonth_set, employees = NHMonth.objects.none(), []
    totals_notax = {'income':0, 'net_income':0, 'net_income_no_commission':0}
    totals = {'income':0, 'net_income':0, 'net_income_no_commission':0, 'sale_count':0}
    avg = {'signed_commission':0, 'actual_commission':0}
    avg_notax = {'income':0, 'net_income':0, 'net_income_no_commission':0}
    nhbranch = None
    
    if len(request.GET):
        form = NHBranchSeasonForm(request.GET)
        if form.is_valid():
            nhbranch = form.cleaned_data['nhbranch']
            if not request.user.has_perm('Management.nhbranch_' + str(nhbranch.id)):
                return HttpResponse('No Permission. Contact Elad.') 
            from_date = date(form.cleaned_data['from_year'], form.cleaned_data['from_month'], 1)
            to_year, to_month = form.cleaned_data['to_year'], form.cleaned_data['to_month']
            to_date = date(to_month == 12 and to_year + 1 or to_year, to_month == 12 and 1 or to_month + 1, 1)
        
            nhmonth_set = NHMonth.objects.range(from_date.year, from_date.month, to_date.year, to_date.month) \
                                         .filter(nhbranch = nhbranch).annotate(Count('nhsales'))
                
            query = NHBranchEmployee.objects.filter(start_date__lt = to_date, nhbranch = nhbranch) \
                                            .exclude(end_date__isnull=False, end_date__lt = from_date)
            employees = [x.nhemployee for x in query]
            
            for e in employees:
                e.season_total, e.season_total_notax, e.season_branch_income_notax = 0, 0, 0
                e.season_branch_income_buyers_notax, e.season_branch_income_sellers_notax = 0, 0
            for nhm in nhmonth_set:
                query = NHBranchEmployee.objects.filter(start_date__lt = to_date, nhbranch = nhbranch) \
                                                .exclude(end_date__isnull=False, end_date__lt = from_date)
                nhm.employees = [x.nhemployee for x in query]
                tax = Tax.objects.filter(date__lte=date(nhm.year, nhm.month,1)).latest().value / 100 + 1
                for e in nhm.employees:
                    e.month_total = 0
                for nhs in nhm.nhsales.all():
                    for nhss in nhs.nhsaleside_set.all():
                        for e in employees:
                            nhss.include_tax = True
                            e.season_total += nhss.get_employee_pay(e)
                            nhss.include_tax = False
                            e.season_total_notax += nhss.get_employee_pay(e)
                            if nhss.signing_advisor == e:
                                income_notax = nhss.income / tax
                                e.season_branch_income_notax += income_notax
                                if nhss.sale_type.id in [SaleType.SaleSeller, SaleType.RentRenter]:
                                    e.season_branch_income_sellers_notax += income_notax
                                elif nhss.sale_type.id in [SaleType.SaleBuyer, SaleType.RentRentee]:
                                    e.season_branch_income_buyers_notax += income_notax
                        for e in nhm.employees:
                            nhss.include_tax = True
                            e.month_total += nhss.get_employee_pay(e)
                nhm.include_tax = False
                totals_notax['income'] += nhm.total_income
                totals_notax['net_income'] += nhm.total_net_income
                totals_notax['net_income_no_commission'] += nhm.net_income_no_commission
                nhm.include_tax = True
                totals['income'] += nhm.total_income
                totals['net_income'] += nhm.total_net_income
                totals['net_income_no_commission'] += nhm.net_income_no_commission
                totals['sale_count'] += nhm.nhsales__count
                avg['signed_commission'] += nhm.avg_signed_commission
                avg['actual_commission'] += nhm.avg_actual_commission
            month_count = len(nhmonth_set)
            month_with_sales_count = len([nhm for nhm in nhmonth_set if nhm.nhsales__count > 0])
            if month_count > 0:
                avg['signed_commission'] /= month_with_sales_count
                avg['actual_commission'] /= month_with_sales_count
                avg_notax['income'] = totals_notax['income'] / month_count
                avg_notax['net_income'] = totals_notax['net_income'] / month_count
                avg_notax['net_income_no_commission'] = totals_notax['net_income_no_commission'] / month_count
               
            for e in employees:
                e.season_avg_notax = month_count and e.season_total_notax / month_count or 0
                total_net_income_notax = totals_notax['net_income']
                if total_net_income_notax:
                    e.season_branch_income_ratio_notax = e.season_branch_income_notax / total_net_income_notax * 100
                    e.season_branch_income_buyers_ratio_notax = e.season_branch_income_buyers_notax / total_net_income_notax * 100
                    e.season_branch_income_sellers_ratio_notax = e.season_branch_income_sellers_notax / total_net_income_notax * 100
    else:
        form = NHBranchSeasonForm()
    return render(request, 'Management/nh_season_income.html', 
                              { 'nhmonths':nhmonth_set, 'filterForm':form, 'employees':employees,
                               'totals':totals,'totals_notax':totals_notax,
                               'nhbranch':nhbranch, 'avg':avg, 'avg_notax':avg_notax },
                              )
    
class NHBranchCreate(PermissionRequiredMixin, CreateView):
    model = NHBranch
    fields = ('name','address','phone','mail','fax','url')
    template_name = 'Management/nhbranch_edit.html'
    permission_required = 'Management.add_nhbranch'

class NHBranchUpdate(PermissionRequiredMixin, UpdateView):
    model = NHBranch
    fields = ('name','address','phone','mail','fax','url')
    template_name = 'Management/nhbranch_edit.html'
    permission_required = 'Management.change_nhbranch'

def nhmonth_sales(request, nhbranch_id):
    if not request.user.has_perm('Management.nhbranch_' + str(nhbranch_id)):
        return HttpResponse('No Permission. Contact Elad.') 
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    d = date(year, month, 1)
    if year and month:
        q = NHMonth.objects.filter(nhbranch__id = nhbranch_id, year=year, month=month)
    nhb = NHBranch.objects.get(pk=nhbranch_id)
    nhm = q.count() > 0 and q[0] or NHMonth(nhbranch = nhb, year = year, month = month)
    query = NHBranchEmployee.objects.filter(nhbranch = nhb).exclude(end_date__isnull=False, end_date__lt = d)
    employees = [x.nhemployee for x in query]
    for e in employees:
        e.month_total = 0
    for sale in nhm.nhsales.all():
        for nhss in sale.nhsaleside_set.all():
            for e in employees:
                e.month_total += nhss.get_employee_pay(e)
    form = MonthForm(initial={'year':nhm.year,'month':nhm.month})
    return render(request, 'Management/nhmonth_sales.html', 
                              { 'nhmonth':nhm, 'filterForm':form, 'employees':employees },
                              )

@permission_required('Management.change_nhmonth')
def nhmonth_close(request):
    today = date.today()
    nhbranch_id = int(request.GET.get('nhbranch'))
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    if not request.user.has_perm('Management.nhbranch_' + str(nhbranch_id)):
        return HttpResponse('No Permission. Contact Elad.')
    query = NHMonth.objects.filter(nhbranch__id = nhbranch_id, year = year, month = month)
    if query.count() == 1:
        nhm = query[0]
    elif query.count() == 0:
        nhbranch = NHBranch.objects.get(pk=nhbranch_id)
        nhm = NHMonth(nhbranch = nhbranch, year = year, month = month)
    nhm.close()
    return HttpResponseRedirect('/nhbranch/%s/sales?year=%s&month=%s' % (nhbranch_id, nhm.year, nhm.month))

@permission_required('Management.add_demand')
def demand_list(request):
    ds, unhandled_projects = [], []
    
    current = common.current_month()
    year, month = current.year, current.month
    
    if len(request.GET):
        form = MonthForm(request.GET)
        if form.is_valid():
            year, month = form.cleaned_data['year'], form.cleaned_data['month']
    else:
        form = MonthForm(initial={'year':year,'month':month})
        
    '''loop through all active projects and create demands for them if havent
    alredy created. if project has status other than Feed, it is handled''' 
    for project in Project.objects.active():
        demand, new = Demand.objects.get_or_create(project = project, year = year, month = month)
        ds.append(demand)

    set_demand_total_fields(ds, year, month, year, month)
    set_demand_last_status(ds)
    set_demand_open_reminders(ds)

    # add un-handled projects
    for demand in ds:
        last_status = demand.last_status

        if last_status and last_status.type_id == DemandStatusType.Feed:
            unhandled_projects.append(demand.project)

    sales_count, expected_sales_count, sales_amount = 0,0,0

    for d in ds:
        sales_count += d.sales_count
        sales_amount += d.sales_amount
        expected_sales_count += d.sale_count
        
    context = { 
        'demands':ds, 
        'unhandled_projects':unhandled_projects, 
        'month':date(year, month, 1), 'filterForm':form, 'sales_count':sales_count ,
        'sales_amount':sales_amount, 'expected_sales_count':expected_sales_count }

    return render(request, 'Management/demand_list.html', context)

def employee_sales(request, id, year, month):
    salary = EmployeeSalary.objects.get(employee__id = id, year = year, month = month)

    employee = salary.employee

    set_employee_sales(
        [salary], 
        {id:employee}, 
        {id:list(employee.projects.all())},
        year, month, year, month)

    return render(request, 'Management/employee_sales.html', { 'es':salary })

@permission_required('Management.add_employeesalary')
def employee_refund(request, year, month):
    if request.method == 'POST':
        form = EmployeeSalaryRefundForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            es = EmployeeSalary.objects.get_or_create(employee = cleaned_data['employee'], year = year, month = month)[0]
            es.refund = cleaned_data['refund']
            es.refund_type = cleaned_data['refund_type']
            es.save()
    else:
        form = EmployeeSalaryRefundForm()

    return render(request, 'Management/employee_salary_edit.html', 
                              { 'form':form, 'month':month, 'year':year },
                              )

@permission_required('Management.add_employeesalary')
def employee_remarks(request, year, month):
    if request.method == 'POST':
        form = EmployeeSalaryRemarksForm(request.POST)
        if form.is_valid():  
            cleaned_data = form.cleaned_data
            es = EmployeeSalary.objects.get_or_create(employee = cleaned_data['employee'], year = year, month = month)[0]
            es.remarks = cleaned_data['remarks']
            es.save()
    else:
        form = EmployeeSalaryRemarksForm()

    return render(request, 'Management/employee_salary_edit.html', 
                              { 'form':form, 'month':month, 'year':year },
                              )
    
def nhemployee_add(request):
    if request.method == 'POST':
        form = NHEmployeeForm(request.POST)
        if form.is_valid():
            nhemployee = form.save()
            nhbranch = form.cleaned_data['nhbranch']
            NHBranchEmployee.objects.create(nhemployee = nhemployee, nhbranch = nhbranch, start_date = nhemployee.work_start, 
                                            is_manager = False)
            return HttpResponseRedirect(nhemployee.get_absolute_url())
    else:
        form = NHEmployeeForm()
        
    return render(request, 'Management/nhemployee_form.html', {'form':form}, )

def nhemployee_sales(request, id, year, month):
    es = NHEmployeeSalary.objects.get(nhemployee__id = id, year = year, month = month)
    return render(request, 'Management/nhemployee_sales.html', 
                              { 'es':es },
                              )
    
@permission_required('Management.add_nhemployeesalary')
def nhemployee_refund(request, year, month):
    if request.method == 'POST':
        form = NHEmployeeSalaryRefundForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            es = NHEmployeeSalary.objects.get_or_create(nhemployee = cleaned_data['nhemployee'], year = year, month = month)[0]
            es.refund = cleaned_data['refund']
            es.refund_type = cleaned_data['refund_type']
            es.save()
    else:
        form = NHEmployeeSalaryRefundForm()

    return render(request, 'Management/nhemployee_salary_edit.html', 
                              { 'form':form, 'month':month, 'year':year },
                              )

@permission_required('Management.add_nhemployeesalary')
def nhemployee_remarks(request, year, month):
    if request.method == 'POST':
        form = EmployeeSalaryRemarksForm(request.POST)
        if form.is_valid():            
            cleaned_data = form.cleaned_data
            es = NHEmployeeSalary.objects.get_or_create(nhemployee = cleaned_data['nhemployee'], year = year, month = month)[0]
            es.remarks = cleaned_data['remarks']
            es.save()
    else:
        form = NHEmployeeSalaryRemarksForm()

    return render(request, 'Management/nhemployee_salary_edit.html', 
                              { 'form':form, 'month':month, 'year':year },
                              )

@permission_required('Management.change_demand')
def demand_edit(request, object_id):
    demand = Demand.objects.select_related('project').get(pk = object_id)
    sales = demand.get_sales().select_related('house__building')
    months = None

    if request.method == 'POST':
        form = DemandForm(request.POST, instance = demand)
        if form.is_valid():
            form.save()
    else:
        form = DemandForm(instance = demand)
        months = MonthForm()
        
    return render(request, 'Management/demand_edit.html', { 'form':form, 'demand':demand, 'sales':sales, 'months':months }, )
    
@permission_required('Management.change_demand')
def demand_close(request, id):
    d = Demand.objects.get(pk=id)
    if request.method == 'POST':
        d.close()
        d.save()
    return render(request, 'Management/demand_close.html', 
                              { 'demand':d },
                              )

@permission_required('Management.change_demand')
def demand_zero(request, id):
    d = Demand.objects.get(pk=id)
    d.close()
    return HttpResponseRedirect('/demands')

@permission_required('Management.send_mail')
def send_mail(request):
    if request.method == 'POST':
        form = MailForm(request.POST, request.FILES)
        if form.is_valid():
            field_names = ['attachment1','attachment2','attachment3','attachment4','attachment5']
            attachments = [request.FILES[field_name] for field_name in field_names if form.cleaned_data[field_name]]
            
            mail(to = form.cleaned_data['to'], cc = form.cleaned_data['Cc'], bcc = form.cleaned_data['Bcc'],
                 subject = form.cleaned_data['subject'], contents = form.cleaned_data['contents'], attachments = attachments)
    else:
        form = MailForm()
        
    return render(request, 'Management/send_mail.html',  { 'form':form }, )

def demand_send_mail(demand, addr):
    filename = common.generate_unique_media_filename('pdf')
    MonthDemandWriter(demand, to_mail=True).build(filename)
    mail(to = addr, subject = u'עמלה לפרויקט %s לחודש %s/%s' % (demand.project, demand.month, demand.year), attachments = [filename])
    demand.send()

@permission_required('Management.change_demand')
def demands_send(request):
    current = common.current_month()
    y = int(request.GET.get('year', current.year))
    m = int(request.GET.get('month', current.month))
    form = MonthForm(initial={'year':y,'month':m})
    month = datetime(y,m,1)
    ds = Demand.objects.filter(year = y, month = m)
    forms=[]
    if request.method == 'POST':
        error = False
        for d in ds:
            f = DemandSendForm(request.POST, instance=d, prefix = str(d.id))
            if f.is_valid():
                is_finished, by_mail, by_fax, mail = f.cleaned_data['is_finished'], f.cleaned_data['by_mail'], f.cleaned_data['by_fax'], f.cleaned_data['mail']
                if is_finished:
                    d.finish()
                if by_mail and d.get_sales().count() > 0:
                    if mail:
                        demand_send_mail(d, mail)
                    else:
                        error = u'לפרויקט %s לא הוגדר מייל לשליחת דרישות' % d.project
                if by_fax:
                    pass
            forms.append(f)
        if error:
            return render(request, 'Management/error.html', {'error': error}, )
        else:
            return HttpResponseRedirect('/demandsold')
    else:
        for d in ds:
            if d.project.demand_contact:
                initial = {'mail':d.project.demand_contact.mail,
                           'fax':d.project.demand_contact.fax}
            else:
                initial = {}
            f = DemandSendForm(instance=d, prefix=str(d.id), initial = initial)
            forms.append(f)
            
    return render(request, 'Management/demands_send.html', 
                              { 'forms':forms,'filterForm':form, 'month':month },
                              )

@permission_required('Management.change_demand')
def demand_closeall(request):
    for d in Demand.objects.current():
        if d.statuses.latest().type.id == DemandStatusType.Feed:
            d.close()
    return HttpResponseRedirect('/demands')
        
@permission_required('Management.delete_sale')
def demand_sale_del(request, demand_id, id):
    sale = Sale.objects.get(pk=id)
    if sale.demand.statuses.latest().type.id != DemandStatusType.Sent:
        sale.delete()
        return HttpResponseRedirect('../../../')
    else:
        sc = SaleCancel(sale = sale, date = date.today(), deduct_from_demand=True)
        sc.save()
        return HttpResponseRedirect('/salecancel/%s' % sc.id)

class SalePriceModUpdate(PermissionRequiredMixin, UpdateView):
    model = SalePriceMod
    form_class = SalePriceModForm
    template_name = 'Management/sale_mod_edit.html'
    permission_required = 'Management.change_salepricemod'
    
class SaleHouseModUpdate(PermissionRequiredMixin, UpdateView):
    model = SaleHouseMod
    form_class = SaleHouseModForm
    template_name = 'Management/sale_mod_edit.html'
    permission_required = 'Management.change_salehousemod'

class SaleCancelUpdate(PermissionRequiredMixin, UpdateView):
    model = SaleCancel
    fields = ('deduct_from_demand','remarks')
    template_name = 'Management/sale_mod_edit.html'
    permission_required = 'Management.change_salecancel'

def salepaymod_edit(request, model, object_id):
    from django.forms.models import modelform_factory

    object = model.objects.select_related('sale__demand__project', 'sale__house').get(pk = object_id)
    form_class = modelform_factory(model, fields=('to_month','to_year','employee_pay_month','employee_pay_year','remarks'))
    
    if request.method == 'POST':
        form = form_class(request.POST, instance = object)
        if form.is_valid():
            demands_to_calc = []
            salaries_to_calc = []
            to_year, to_month = form.cleaned_data['to_year'], form.cleaned_data['to_month']
            employee_pay_year, employee_pay_month = form.cleaned_data['employee_pay_year'], form.cleaned_data['employee_pay_month']
            project = object.sale.demand.project
            
            # need to re-calc both origin and destination demand (if changed)
            if object.to_year != to_year or object.to_month != to_month:
                q = models.Q(year = object.to_year, month = object.to_month) | models.Q(year = to_year, month = to_month)
                demands_to_calc.extend(project.demands.filter(q))
                
            # need to calc origin and destination salaries for all project employees
            if object.employee_pay_year != employee_pay_year or object.employee_pay_month != employee_pay_month:
                q = models.Q(year = object.employee_pay_year, month = object.employee_pay_month) | models.Q(year = employee_pay_year, month = employee_pay_month)
                salaries = EmployeeSalary.objects.nondeleted().filter(q, employee__in = project.employees.all())
                salaries_to_calc.extend(salaries)
            
            for demand in demands_to_calc:
                demand.calc_sales_commission()
            
            for salary in salaries_to_calc:
                salary.calculate()
                salary.save()
    else:
        form = form_class(instance = object)
        
    return render(request, 'Management/sale_mod_edit.html', {'form':form}, )
        

@permission_required('Management.reject_sale')
def demand_sale_reject(request, demand_id, id):
    sale = Sale.objects.get(pk=id)
    y,m = sale.contractor_pay_year, sale.contractor_pay_month
    demands_to_calc = []
    
    try:
        sr = sale.salereject
    except SaleReject.DoesNotExist:
        sr = SaleReject(sale = sale, employee_pay_month = sale.employee_pay_month, employee_pay_year = sale.employee_pay_year)
    
    to_year, to_month = m==12 and y+1 or y, m==12 and 1 or m+1
    
    if to_year != sr.to_year or to_month != sr.to_month:
        project = sale.demand.project
        # need to recalc both origin and destination demands
        q = models.Q(year = y, month = m) | models.Q(year = to_year, month = to_month)
        demands_to_calc.extend(project.demands.filter(q))
        
    sr.to_year, sr.to_month = to_year, to_month
    sr.save()
    
    calc_demands(demands_to_calc)
    
    return HttpResponseRedirect('/salereject/%s' % sr.id)

@permission_required('Management.pre_sale')
def demand_sale_pre(request, demand_id, id):
    sale = Sale.objects.get(pk=id)
    y,m = request.GET.get('year'), request.GET.get('month')
    demands_to_calc = []
    
    try:
        sr = sale.salepre
    except SalePre.DoesNotExist:
        sr = SalePre(sale = sale, employee_pay_month = sale.employee_pay_month, employee_pay_year = sale.employee_pay_year)
    
    to_year, to_month = y is None and sale.contractor_pay_year or y, m is None and sale.contractor_pay_month or m
    
    if to_year != sr.to_year or to_month != sr.to_month:
        project = sale.demand.project
        # need to recalc both origin and destination demands
        q = models.Q(year = y, month = m) | models.Q(year = to_year, month = to_month)
        demands_to_calc.extend(project.demands.filter(q))
        
    sr.to_year, sr.to_month = to_year, to_month
    sr.save()
    
    calc_demands(demands_to_calc)
    
    return HttpResponseRedirect('/salepre/%s' % sr.id)

@permission_required('Management.cancel_sale')
def demand_sale_cancel(request, demand_id, id):
    sale = Sale.objects.get(pk=id)
    try:
        sc = sale.salecancel
    except SaleCancel.DoesNotExist:
        sc = SaleCancel(sale = sale)
    sc.save()
    
    sale.commission_include = False
    sale.save()
    
    #re-calculate the entire demand
    calc_demands([sale.demand])
    
    return HttpResponseRedirect('/salecancel/%s' % sc.id)

@permission_required('Management.add_invoice')
def invoice_add(request, initial=None):
    
    sales = initial.get('demand').get_sales().select_related('house__building')

    if request.method == 'POST':
        form = DemandInvoiceForm(request.POST)
        if form.is_valid():
            form.save()
            if 'addanother' in request.POST:
                form = DemandInvoiceForm(initial=initial)
            if 'addpayment' in request.POST:
                return HttpResponseRedirect('/payments/add')
    else:
        form = DemandInvoiceForm(initial=initial)
    return render(request, 'Management/invoice_edit.html', {'form':form, 'sales':sales, 'demand': initial.get('demand')}, )

class InvoiceUpdate(PermissionRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'Management/invoice_edit.html'
    permission_required = 'Management.change_invoice'

@permission_required('Management.add_invoice')
def demand_invoice_add(request, id):
    demand = Demand.objects.select_related('project').get(pk=id)
    return invoice_add(request, {'project':demand.project.id, 'month':demand.month, 'year':demand.year, 'demand': demand})

@permission_required('Management.demand_invoices')
def demand_invoice_list(request):
    invoices = None
    if len(request.GET):
        form = ProjectSeasonForm(request.GET)
        if form.is_valid():
            project = form.cleaned_data['project']
            from_date = date(form.cleaned_data['from_year'], form.cleaned_data['from_month'], 1)
            to_date = date(form.cleaned_data['to_year'], form.cleaned_data['to_month'], 1)
            to_date = date(to_date.month == 12 and to_date.year + 1 or to_date.year, to_date.month == 12 and 1 or to_date.month + 1, 1)

            query = Invoice.objects.reverse().select_related()

            invoices = []
            for invoice in query:
                if project:
                    invoice_demands = invoice.demands.filter(project = project)
                else:
                    invoice_demands = invoice.demands.all()
                    
                if not invoice_demands.count():
                    continue
                
                for demand in invoice_demands:
                    demand_date = date(demand.year, demand.month, 1)
                    if demand_date >= from_date and demand_date < to_date:
                        invoices.append(invoice)
                        break

            paginator = django.core.paginator.Paginator(invoices, 25) 
        
            try:
                page = int(request.GET.get('page', '1'))
            except ValueError:
                page = 1
        
            try:
                invoices = paginator.page(page)
            except (paginator.EmptyPage, paginator.InvalidPage):
                invoices = paginator.page(paginator.num_pages)
    else:
        form = ProjectSeasonForm()

    return render(request, 'Management/demand_invoice_list.html', {'page': invoices,'filterForm':form})    
 
 
@permission_required('Management.demand_payments')
def demand_payment_list(request):
    payments = None
    if len(request.GET):
        form = ProjectSeasonForm(request.GET)
        if form.is_valid():
            project = form.cleaned_data['project']
            from_date = date(form.cleaned_data['from_year'], form.cleaned_data['from_month'], 1)
            to_date = date(form.cleaned_data['to_year'], form.cleaned_data['to_month'], 1)
            to_date = date(to_date.month == 12 and to_date.year + 1 or to_date.year, to_date.month == 12 and 1 or to_date.month + 1, 1)

            query = Payment.objects.reverse().select_related()
            
            payments = []
            for payment in query:
                if project:
                    payment_demands = payment.demands.filter(project = project)
                else:
                    payment_demands = payment.demands.all()
                    
                if not payment_demands.count():
                    continue
                
                for demand in payment_demands:
                    demand_date = date(demand.year, demand.month, 1)
                    if demand_date >= from_date and demand_date < to_date:
                        payments.append(payment)
                        break
            
            paginator = django.core.paginator.Paginator(payments, 25) 
        
            try:
                page = int(request.GET.get('page', '1'))
            except ValueError:
                page = 1
        
            try:
                payments = paginator.page(page)
            except (paginator.EmptyPage, paginator.InvalidPage):
                payments = paginator.page(paginator.num_pages)
    else:
        form = ProjectSeasonForm()

    return render(request, 'Management/demand_payment_list.html', {'page': payments,'filterForm':form})    
   
@permission_required('Management.add_invoice')
def project_invoice_add(request, id):
    return invoice_add(request, {'project':id})

@permission_required('Management.delete_invoice')
def invoice_del(request, id):
    i = Invoice.objects.get(pk=id)
    demand_id = i.demands.all()[0].id
    i.delete()
    return HttpResponseRedirect('/demands/%s' % demand_id)

@permission_required('Management.add_invoiceoffset')
def invoice_offset(request, id=None):
    if request.method == 'POST':
        form = InvoiceOffsetForm(request.POST)
        if form.is_valid():
            invoice_num = form.cleaned_data['invoice_num']
            invoice = Invoice.objects.get(num = invoice_num) 
            invoice.offset = form.save()
            invoice.save()
    else:
        if id:
            i = Invoice.objects.get(pk=id)
            invoice_num = i.num
            offset = i.offset or InvoiceOffset()
        else:
            offset = InvoiceOffset()
            invoice_num = 0
        form = InvoiceOffsetForm(instance = offset, initial={'invoice_num':invoice_num})
    
    return render(request, 'Management/object_edit.html', {'form': form, 'title':u'זיכוי חשבונית'})    

class InvoiceOffsetUpdate(PermissionRequiredMixin, UpdateView):
    model = InvoiceOffset
    fields = ('date','amount','reason','remarks')
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_invoiceoffset'

class LoanPayUpdate(PermissionRequiredMixin, UpdateView):
    model = LoanPay
    form_class = LoanPayForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_loanpay'

@permission_required('Management.delete_invoiceoffset')
def invoice_offset_del(request, id):
    io = InvoiceOffset.objects.get(pk=id)
    demand_id = io.invoice.demands.all()[0].id
    #unlink invoice from the offset
    invoice = io.invoice
    invoice.offset = None
    invoice.save()
    InvoiceOffset.objects.get(pk=id).delete()
    return HttpResponseRedirect('/demands/%s' % demand_id)

def process_deal_form(form):
    pass

def process_income_form(form):
    new_division_type, new_income_type, new_income_producer_type, new_client_type = (form.cleaned_data['new_client_status_type'],
                                                                                     form.cleaned_data['new_income_type'],
                                                                                     form.cleaned_data['new_income_producer_type'],
                                                                                     form.cleaned_data['new_client_type'])
    if new_division_type:
        division_type, new = DivisionType.objects.get_or_create(name=new_division_type)
        form.cleaned_data['division_type'] = division_type
    if new_income_type:
        income_type, new = DivisionType.objects.get_or_create(name=new_income_type)
        form.cleaned_data['income_type'] = income_type
    if new_income_producer_type:
        income_producer_type, new = DivisionType.objects.get_or_create(name=new_income_producer_type)
        form.cleaned_data['income_producer_type'] = income_producer_type
    if new_client_type:
        client_type, new = DivisionType.objects.get_or_create(name=new_client_type)
        form.cleaned_data['client_type'] = client_type

@permission_required('Management.add_income')
def income_add(request):
    return income_core(request, Income(deal = Deal(), invoice = Invoice(), payment = Payment()))

@permission_required('Management.edit_income')
def income_edit(request, id):
    income = Income.objects.get(pk=id)
    return income_core(request, income)

def income_core(request, instance):
    if request.method=='POST':
        incomeForm, dealForm, invoiceForm, paymentForm = (IncomeForm(request.POST, instance = instance), 
                                                          DealForm(request.POST, instance = instance.deal), 
                                                          InvoiceForm(request.POST, instance = instance.invoice), 
                                                          PaymentForm(request.POST, instance = instance.payment))
        if (incomeForm.is_valid() and dealForm.is_valid() 
            and (invoiceForm.has_changed() == False or invoiceForm.is_valid())
            and (paymentForm.has_changed() == False or paymentForm.is_valid())):
            process_deal_form(dealForm)
            process_income_form(incomeForm)
            instance.deal, instance.invoice, instance.payment = dealForm.save(), invoiceForm.save(), paymentForm.save()
            incomeForm.save()
    else:
        incomeForm = IncomeForm(instance = instance)
        dealForm = DealForm(instance = instance.deal)
        invoiceForm = InvoiceForm(instance = instance.invoice)
        paymentForm = PaymentForm(instance = instance.payment)
    
    context = {
        'incomeForm':incomeForm, 
        'dealForm':dealForm, 
        'invoiceForm':invoiceForm,
        'paymentForm':paymentForm 
        }

    return render(request, 'Management/income_edit.html', context) 

@permission_required('Management.list_income')
def income_list(request):
    incomes, from_date, to_date = [], date.today(), date.today()
    if len(request.GET):
        form = IncomeFilterForm(request.GET)
        incomes = Income.objects.all()
        if form.is_valid():
            if form.cleaned_data['division_type']:
                incomes = incomes.filter(division_type = form.cleaned_data['division_type'])
            if form.cleaned_data['income_type']:
                incomes = incomes.filter(income_type = form.cleaned_data['income_type'])
            if form.cleaned_data['income_producer_type']:
                incomes = incomes.filter(income_producer_type = form.cleaned_data['income_producer_type'])
            if form.cleaned_data['client_type']:
                incomes = incomes.filter(client_type = form.cleaned_data['client_type'])
            from_date = date(form.cleaned_data['from_year'], form.cleaned_data['from_month'], 1)
            to_date = date(form.cleaned_data['to_year'], form.cleaned_data['to_month'], 1)
            incomes = incomes.range(from_date.year, from_date.month, to_date.year, to_date.month)
    else:
        form = IncomeFilterForm()
    
    context = { 'filterForm':form, 'incomes':incomes, 'from_date':from_date, 'to_date':to_date }

    return render(request, 'Management/income_list.html', context) 

class IncomeDelete(PermissionRequiredMixin, DeleteView):
    model = Income
    success_url = '/incomes'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_income'

@permission_required('Management.add_payment')
def split_payment_add(request):
    DemandFormset = formset_factory(SplitPaymentDemandForm, extra=5)
    error = ''
    if request.method == 'POST':
        spf = SplitPaymentForm(request.POST)
        spdForms = DemandFormset(request.POST)
        if spf.is_valid() and spdForms.is_valid():
            for form in spdForms.forms:
                if not form.is_valid() or not 'amount' in form.cleaned_data:
                    continue
                p = Payment()
                for attr, value in spf.cleaned_data.items():
                    setattr(p, attr, value)
                p.amount = form.cleaned_data['amount']
                p.save()
                project, year, month = form.cleaned_data['project'], form.cleaned_data['year'], form.cleaned_data['month']
                q = Demand.objects.filter(project = project, year = year, month = month)
                if q.count() == 1:
                    q[0].payments.add(p)
                else:
                    error += '\r\n' + u'לא קיימת דרישה לפרוייקט %s לחודש %s\%s' % (project, year, month)
            if error == '':
                return HttpResponseRedirect('/demandpayments')
    else:
        spf = SplitPaymentForm()
        spdForms = DemandFormset()
        
    return render(request, 'Management/split_payment_add.html', 
                              { 'spf':spf, 'spdForms':spdForms, 'error':error }, )

@permission_required('Management.add_payment')
def payment_add(request, initial=None):
    if request.method == 'POST':
        form = DemandPaymentForm(request.POST)
        if form.is_valid():
            form.save()
            if 'addanother' in request.POST:
                form = DemandPaymentForm(initial=initial)
            if 'addinvoice' in request.POST:
                return HttpResponseRedirect('/invoices/add')
    else:
        form = DemandPaymentForm(initial=initial)
    return render(request, 'Management/payment_edit.html', 
                              { 'form':form }, )

class PaymentUpdate(PermissionRequiredMixin, UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'Management/payment_edit.html'
    permission_required = 'Management.change_payment'

@permission_required('Management.change_payment')
def demand_payment_edit(request, id):
    payment = Payment.objects.get(pk = id)
    if request.method == 'POST':
        form = DemandPaymentForm(request.POST, instance = payment)
        if form.is_valid():
            form.save()
            if 'addanother' in request.POST:
                try:
                    demand = payment.demands.all()[0]
                    return HttpResponseRedirect('/demands/%s/payment/add' % demand.id)
                except KeyError:
                    return HttpResponseRedirect(reverse(payment_add))
            if 'addinvoice' in request.POST:
                return HttpResponseRedirect('/invoices/add')
    else:
        form = DemandPaymentForm(instance = payment)
    return render(request, 'Management/payment_edit.html', 
                              { 'form':form }, )

@permission_required('Management.change_invoice')
def demand_invoice_edit(request, id):
    invoice = Invoice.objects.get(pk = id)
    if request.method == 'POST':
        form = DemandInvoiceForm(request.POST, instance = invoice)
        if form.is_valid():
            form.save()
            if 'addanother' in request.POST:
                try:
                    demand = invoice.demands.all()[0]
                    return HttpResponseRedirect('/demands/%s/invoice/add' % demand.id)
                except KeyError:
                    return HttpResponseRedirect(reverse(invoice_add))
            if 'addpayment' in request.POST:
                return HttpResponseRedirect('/payments/add')
    else:
        form = DemandInvoiceForm(instance = invoice)
    return render(request, 'Management/invoice_edit.html', 
                              { 'form':form }, )

def payment_details(request, project, year, month):
    try:
        d = Demand.objects.get(project = project, year = year, month = month)
        return render(request, 'Management/demand_payment_details.html', 
                                  { 'payments':d.payments.all()}, )
    except Demand.DoesNotExist:
        return HttpResponse('')
    
def invoice_details(request, project, year, month):
    try:
        d = Demand.objects.get(project = project, year = year, month = month)
        return render(request, 'Management/demand_invoice_details.html', 
                                  { 'invoices':d.invoices.all()}, )
    except Demand.DoesNotExist:
        return HttpResponse('')
    
def demand_details(request, project, year, month):
    try:
        d = Demand.objects.get(project = project, year = year, month = month)
        return render(request, 'Management/demand_details.html', 
                                  { 'demand':d}, )
    except Demand.DoesNotExist:
        return HttpResponse('')

@permission_required('Management.add_demanddiff')
def demand_adddiff(request, object_id, type = None):
    demand = Demand.objects.get(pk=object_id)
    if request.method == 'POST':
        form = DemandDiffForm(request.POST)
        if form.is_valid():
            form.instance.demand = demand
            diff = form.save()
            if 'addanother' in request.POST:
                return HttpResponseRedirect(reverse(demand_adddiff, args=[object_id]))
            return HttpResponseRedirect(diff.get_absolute_url())
    else:
        form = DemandDiffForm(initial={'type':type})
    return render(request, 'Management/object_edit.html', 
                              { 'form':form }, )

@permission_required('Management.demand_force_fully_paid')
def demand_force_fully_paid(request, id):
    demand = Demand.objects.get(pk=id)
    demand.force_fully_paid = True
    demand.save()
    return HttpResponse('ok')

@permission_required('Management.demand_not_yet_paid')
def demand_not_yet_paid(request, id):
    demand = Demand.objects.get(pk=id)
    demand.not_yet_paid = demand.not_yet_paid == 0 and True or False
    demand.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@permission_required('Management.add_demanddiff')
def demand_adddiff_adjust(request, object_id):
    return demand_adddiff(request, object_id, u'התאמה')

class DemandDiffUpdate(PermissionRequiredMixin, UpdateView):
    model = DemandDiff
    form_class = DemandDiffForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_demanddiff'

@permission_required('Management.delete_demanddiff')
def demanddiff_del(request, pk):
    diff = DemandDiff.objects.get(pk=pk)
    url = diff.demand.get_absolute_url()
    diff.delete()
    return HttpResponseRedirect(url)

@permission_required('Management.add_payment')
def demand_payment_add(request, id):
    demand = Demand.objects.get(pk=id)
    return payment_add(request, {'project':demand.project.id, 'month':demand.month, 'year':demand.year})
    
@permission_required('Management.add_payment')
def project_payment_add(request, id):    
    demand = Demand.objects.get(pk=id)
    return payment_add(request, {'project':id})

@permission_required('Management.add_payment')
def nhsaleside_payment_add(request, object_id):
    nhs = NHSaleSide.objects.get(pk=object_id)
    if not request.user.has_perm('Management.nhbranch_' + str(nhs.nhsale.nhmonth.nhbranch.id)):
        return HttpResponse('No Permission. Contact Elad.') 
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            p = form.save()
            nhs.payments.add(p)
            if 'addanother' in request.POST:
                form = PaymentForm()
    else:
        form = PaymentForm()
    return render(request, 'Management/object_edit.html', 
                              { 'form':form }, )
    
@permission_required('Management.add_invoice')
def nhsaleside_invoice_add(request, object_id):
    nhs = NHSaleSide.objects.get(pk=object_id)
    if not request.user.has_perm('Management.nhbranch_' + str(nhs.nhsale.nhmonth.nhbranch.id)):
        return HttpResponse('No Permission. Contact Elad.') 
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            i = form.save()
            nhs.invoices.add(i)
    else:
        form = InvoiceForm()
    return render(request, 'Management/object_edit.html', 
                              { 'form':form }, )

 
@permission_required('Management.delete_payment')
def payment_del(request, id):
    p = Payment.objects.get(pk=id)
    if p.demands.count() == 1:
        next = '/demands/%s' % p.demands.all()[0].id
    elif i.nhsaleside_set.count() == 1:
        next = '/nhsale/%s' % p.nhsaleside_set.all()[0].nhsale.id
    p.delete()
    return HttpResponseRedirect(next)

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project

    def get_queryset(self):
        return Project.objects.filter(end_date = None).select_related('demand_contact','payment_contact')

@permission_required('Management.project_list_pdf')
def project_list_pdf(request):
    writer = ProjectListWriter(projects = Project.objects.active())
    return build_and_return_pdf(writer)

class ProjectArchiveListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'Management/project_archive.html'

    def get_queryset(self):
        return Project.objects.archive()

class NHSaleDetailView(LoginRequiredMixin, DetailView):
    model = NHSale
    context_object_name = 'nhs'
    template_name = 'Management/nhsale_edit.html'

class NHSaleUpdate(PermissionRequiredMixin, UpdateView):
    model = NHSale
    form_class = NHSaleForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_nhsale'

    
class NHSaleSideUpdate(PermissionRequiredMixin, UpdateView):
    model = NHSaleSide
    form_class = NHSaleSideForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_nhsaleside'

@permission_required('Management.change_nhsale')
def nhsale_edit(request, object_id):
    nhs = NHSale.objects.get(pk=object_id)
    if not request.user.has_perm('Management.nhbranch_' + str(nhs.nhmonth.nhbranch.id)):
        return HttpResponse('No Permission. Contact Elad.') 
    return render(request, 'Management/nhsale_edit.html',
                              {'nhs': nhs}, 
                              )

@permission_required('Management.nhsale_move_nhmonth')
def nhsale_move_nhmonth(request, object_id):
    nhsale = NHSale.objects.get(pk=object_id)
    if request.method == 'POST':
        form = NHMonthForm(request.POST)
        if form.is_valid():
            kwargs = form.cleaned_data
            nhmonth, new = NHMonth.objects.get_or_create(**kwargs)
            nhsale.nhmonth = nhmonth
            nhsale.save()
    else:
        nhmonth = nhsale.nhmonth
        form = NHMonthForm(initial = {'year':nhmonth.year, 'month':nhmonth.month, 'nhbranch':nhmonth.nhbranch.id})
        
    return render(request, 'Management/object_edit.html',
                              {'form': form, 'title':u'העברת עסקה מס ' + str(nhsale.num)}, 
                              )

@permission_required('Management.add_nhsale')
def nhsale_add(request, branch_id):
    from django.forms.models import modelformset_factory

    if not request.user.has_perm('Management.nhbranch_' + str(branch_id)):
        return HttpResponse('No Permission. Contact Elad.') 
    
    PaymentFormset = modelformset_factory(Payment, PaymentForm, extra=5)

    if request.method=='POST':
        monthForm = NHMonthForm(request.POST, prefix='month')
        saleForm = NHSaleForm(request.POST, prefix='sale')
        side1Form = NHSaleSideForm(request.POST, prefix='side1')
        side2Form = NHSaleSideForm(request.POST, prefix='side2')
        invoice1Form = InvoiceForm(request.POST, prefix='invoice1')
        payment1Forms = PaymentFormset(request.POST, prefix='payments1')
        invoice2Form = InvoiceForm(request.POST, prefix='invoice2')
        payment2Forms = PaymentFormset(request.POST, prefix='payments2')
        
        if monthForm.is_valid() and saleForm.is_valid() and side1Form.is_valid() and side2Form.is_valid():
            kwargs = monthForm.cleaned_data
            nhmonth, new = NHMonth.objects.get_or_create(**kwargs)
            saleForm.instance.nhmonth = nhmonth
            nhsale = saleForm.save()
            side1Form.instance.nhsale = side2Form.instance.nhsale = nhsale
            side1, side2 = side1Form.save(), side2Form.save()
            error = False
            if invoice1Form.has_changed() and invoice1Form.is_valid():
                side1.invoices.add(invoice1Form.save())
            else:
                error = invoice1Form.has_changed()
            if payment1Forms.is_valid():
                for p in payment1Forms.save():
                    side1.payments.add(p)
            else:
                error = True
            if invoice2Form.has_changed() and invoice2Form.is_valid():
                side2.invoices.add(invoice2Form.save())
            else:
                error = invoice2Form.has_changed()
            if payment2Forms.is_valid():
                for p in payment2Forms.save():
                    side2.payments.add(p)
            else:
                error = True
            if not error:
                if 'addanother' in request.POST:
                    return HttpResponseRedirect('add')
                elif 'tomonth' in request.POST:
                    return HttpResponseRedirect('/nhbranch/%s/sales' % nhsale.nhmonth.nhbranch.id)
    else:
        branch = NHBranch.objects.get(pk=branch_id)
        employee_base_query = EmployeeBase.objects.active()
        nhemployees_query = NHEmployee.objects.filter(nhbranchemployee__nhbranch = branch, work_end = None)
        
        saleForm = NHSaleForm(prefix='sale')
        monthForm = NHMonthForm(prefix='month')
        monthForm.fields['nhbranch'].initial = branch_id
        side1Form = NHSaleSideForm(prefix='side1')
        side1Form.fields['employee1'].queryset = nhemployees_query
        side1Form.fields['employee2'].queryset = nhemployees_query
        side1Form.fields['signing_advisor'].queryset = nhemployees_query
        side1Form.fields['director'].queryset = employee_base_query
        side2Form = NHSaleSideForm(prefix='side2')
        side2Form.fields['employee1'].queryset = nhemployees_query
        side2Form.fields['employee2'].queryset = nhemployees_query
        side2Form.fields['signing_advisor'].queryset = nhemployees_query
        side2Form.fields['director'].queryset = employee_base_query
        invoice1Form = InvoiceForm(prefix='invoice1')
        payment1Forms = PaymentFormset(prefix='payments1', queryset=Payment.objects.none())
        invoice2Form = InvoiceForm(prefix='invoice2')
        payment2Forms = PaymentFormset(prefix='payments2', queryset=Payment.objects.none())
        
    return render(request, 'Management/nhsale_add.html',
                              {'monthForm':monthForm, 'saleForm':saleForm, 
                               'side1form':side1Form, 'side2form':side2Form, 
                               'invoice1Form':invoice1Form, 'payment1Forms':payment1Forms, 
                               'invoice2Form':invoice2Form, 'payment2Forms':payment2Forms}, 
                              )

@permission_required('Management.change_pricelist')
def building_pricelist(request, object_id, type_id):
    b = Building.objects.get(pk = object_id)
    InlineFormSet = inlineformset_factory(Pricelist, ParkingCost, fields=('type','cost'), can_delete=False, extra=5, max_num=5)
    if request.method == 'POST':
        form = PricelistForm(request.POST, instance=b.pricelist)
        formset = InlineFormSet(request.POST, instance = b.pricelist)
        updateForm = PricelistUpdateForm(request.POST, prefix='upd')
        if form.is_valid():
            form.save()
            if formset.is_valid():
                formset.save()
        if updateForm.is_valid():
            action, value, date = (updateForm.cleaned_data['action'], updateForm.cleaned_data['value'],
                                   updateForm.cleaned_data['date'])
            pricelist_types = updateForm.cleaned_data['all_pricelists'] and Pricelist.objects.all() or [updateForm.cleaned_data['pricelisttype']]
            houses = [k.replace('house-','') for k in request.POST if k.startswith('house-')]
            for id in houses:
                h = House.objects.get(pk=id)
                for type in pricelist_types:
                    f = h.versions.filter(type=type)
                    if f.count() == 0: continue
                    price = f.latest().price
                    new = HouseVersion(house=h, type=type, date = date)
                    if action == PricelistUpdateForm.Add:
                        new.price = price + value
                    elif action == PricelistUpdateForm.Precentage:
                        new.price = price * (100 + value) / 100
                    elif action == PricelistUpdateForm.Multiply:
                        new.price = price * value
                    new.save()
    else:
        form = PricelistForm(instance = b.pricelist)
        formset = InlineFormSet(instance = b.pricelist)
        updateForm = PricelistUpdateForm(prefix='upd')
    
    houses = b.houses.all()
    for house in houses:
        versions = house.versions.filter(type__id = type_id)
        house.price = versions.count() > 0 and versions.latest().price or None
        
    return render(request, 'Management/building_pricelist.html',
                              {'form': form, 'formset': formset, 'updateForm':updateForm, 
                               'houses' : houses,
                               'type':PricelistType.objects.get(pk=type_id), 
                               'types':PricelistType.objects.all()}, 
                              )

@permission_required('Management.change_pricelist')
def building_pricelist_pdf(request, object_id, type_id):
    type = request.GET.get('type', '')
    b = Building.objects.get(pk = object_id)
    pricelist_type = PricelistType.objects.get(pk = type_id)
    houses = b.houses.all()
    if type == 'avaliable':
        houses = b.houses.avalible()
    for h in houses:
        try:
            h.price = h.versions.filter(type__id = type_id).latest().price
        except HouseVersion.DoesNotExist:
            h.price = None
    
    title = u'מחירון לפרוייקט %s' % str(b.project)
    subtitle = u'בניין %s - %s' % (b.num, str(pricelist_type))
    
    q = HouseVersion.objects.filter(house__building = b, type=pricelist_type)
    
    if q.count() > 0:
        subtitle += u' לתאריך ' + q.latest().date.strftime('%d/%m/%Y')

    writer = PricelistWriter(b.pricelist, houses, title, subtitle)
    
    return build_and_return_pdf(writer)

class BuildingUpdate(PermissionRequiredMixin, UpdateView):
    model = Building
    form_class = BuildingForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_building'

@permission_required('Management.building_clients')
def building_clients(request, object_id):
    b = Building.objects.get(pk = object_id)
    total_sale_price = 0
    for h in b.houses.sold():
        sale = h.get_sale()
        if sale:
            total_sale_price += sale.price
        try:
            h.price = h.versions.company().latest().price
        except HouseVersion.DoesNotExist:
            h.price = None
    return render(request, 'Management/building_clients.html',
                              { 'object':b, 'total_sale_price':total_sale_price},
                              )

@permission_required('Management.building_clients_pdf')
def building_clients_pdf(request, object_id):
    b = Building.objects.get(pk = object_id)
    houses = b.houses.sold()
    for h in houses:
        try:
            h.price = h.versions.company().latest().price
        except HouseVersion.DoesNotExist:
            h.price = None
    
    title = u'מצבת רוכשים לפרוייקט %s' % str(b.project)
    subtitle = u'בניין %s' % b.num
    
    writer = BuildingClientsWriter(houses, title, subtitle)

    return build_and_return_pdf(writer)

@permission_required('Management.add_project')
def project_add(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        ecForm = ExistContactForm(request.POST)
        contactForm = ContactForm(request.POST, prefix='contact')
        if form.is_valid():
            project = form.save()
            if contactForm.is_valid():
                project.demand_contact = contactForm.save()
            elif ecForm.is_valid():
                project.demand_contact = ecForm.cleaned_data['contact']
            project.save()
            return HttpResponseRedirect('../%s/' % project.id)
        else:
            ecForm = ExistContactForm()
    else:
        form = ProjectForm()
        ecForm = ExistContactForm()
        contactForm = ContactForm(prefix='contact')
    return render(request, 'Management/project_add.html',
                              { 'form':form,'ecForm':ecForm, 'contactForm':contactForm },
                              )

@permission_required('Management.change_salecommissiondetail')
def salecommissiondetail_edit(request, sale_id):
    sale = Sale.objects.get(pk=sale_id)
    InlineFormSet = inlineformset_factory(Sale, SaleCommissionDetail, fields=('commission','value','sale'), can_delete=False)
    if request.method == 'POST':
        formset = InlineFormSet(request.POST, instance=sale)
        if formset.is_valid():
            formset.save()
    else:
        formset = InlineFormSet(instance=sale)
        
    return render(request, 'Management/objectset_edit.html', 
                              { 'formset':formset },
                              )
    
@permission_required('Management.change_project')
def project_edit(request, id):
    project = Project.objects.select_related('demand_contact','payment_contact').get(pk=id)
    details = project.details or ProjectDetails()
    transactions = []
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        detailsForm = ProjectDetailsForm(request.POST, instance=details, prefix='det')
        if form.is_valid():
            form.save()
        if detailsForm.is_valid():
            project.details = detailsForm.save()
            project.save()
    else:
        form = ProjectForm(instance=project)
        detailsForm = ProjectDetailsForm(instance=details, prefix='det')
        commission = project.commissions.get()
        transactionsForm = TransactionUpdateHistory.objects.filter(transaction_id = commission.id, transaction_type = 1)

        for value in transactionsForm :
            field_value = value.field_value
            field_name  = value.field_name

            try :
                if field_name == 'max' :
                    field_name  = u'מקסימום עמלה'
                    field_value = field_value + ' %'
                else :
                    field_value = commaise( int( field_value ) ) + ' ש"ח'
            except :
                pass

            transactions.append( [ gettext( field_name ), field_value, str( value.timestamp ).split(' ')[0] ] )

    context = {
        'form':form, 
        'detailsForm':detailsForm, 
        'project':project, 
        'history':transactions
    }

    return render(request, 'Management/project_edit.html', context)
  
class ProjectCommissionUpdate(PermissionRequiredMixin, UpdateView):
    model = ProjectCommission
    form_class = ProjectCommissionForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_projectcommission'

class ProjectEndUpdate(PermissionRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectEndForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_project'

@login_required  
def project_commission_del(request, project_id, commission):
    project = Project.objects.get(pk = project_id)
    c = project.commissions.get()
    for field in c._meta.fields:
        if abbrevate(field.name) == commission:
            obj = getattr(c, field.name)
            break
    #unlink commission from project
    setattr(c, commission, None)
    project.commissions.save()
    #delete commission
    obj.delete()
    return HttpResponseRedirect('/projects/%s' % project.id)

@login_required
def project_commission_add(request, project_id, commission):
    import inspect
    module = inspect.getmodule(project_commission_add)
    view_func = getattr(module, 'project_' + commission)
    return view_func(request, project_id)

@login_required
def employee_commission_del(request, employee_id, project_id, commission):
    employee = Employee.objects.get(pk = employee_id)
    c = employee.commissions.filter(project__id = project_id)[0]
    for field in c._meta.fields:
        if abbrevate(field.name) == commission:
            obj = getattr(c, field.name)
            #unlink commission from employee
            setattr(c, field.name, None)
            c.save()
            break

    #delete commission
    obj.delete()
    return HttpResponseRedirect('/employees/%s' % employee.id)

def abbrevate(s):
    s2 = ''
    for part in s.split('_'):
        s2 += part[0]
    return s2

@login_required
def employee_commission_add(request, employee_id, project_id, commission):
    import inspect
    module = inspect.getmodule(employee_commission_add)
    view_func = getattr(module, 'employee_' + commission)
    return view_func(request, employee_id, project_id)
        
@permission_required('Management.add_cvarprecentage')
def project_cvp(request, project_id):
    c = ProjectCommission.objects.get(project__id = project_id)
    cvp = c.c_var_precentage or CVarPrecentage()
    InlineFormSet = inlineformset_factory(CVarPrecentage, CPrecentage, fields=('precentage',), extra = 10, max_num = 10)

    if request.method == "POST":
        formset = InlineFormSet(request.POST, instance=cvp)
        form = CVarPrecentageForm(request.POST, instance=cvp)
        if formset.is_valid() and form.is_valid():
            c.c_var_precentage = form.save()
            c.save()
            formset.save()
    else:
        formset = InlineFormSet(instance=cvp)
        form = CVarPrecentageForm(instance=cvp)
    return render(request, 'Management/commission_inline.html', 
                              { 'formset':formset,'form':form, 'show_house_num':True },
                              )

@permission_required('Management.add_cvarprecentagefixed')
def project_cvpf(request, project_id):
    c = ProjectCommission.objects.get(project__id = project_id)
    cvpf = c.c_var_precentage_fixed or CVarPrecentageFixed()
    
    if request.method == 'POST':
        form = CVarPrecentageFixedForm(request.POST, instance = cvpf)
        if form.is_valid():
            c.c_var_precentage_fixed = form.save()
            c.save()
    else:
        form = CVarPrecentageFixedForm(instance= cvpf)
            
    return render(request, 'Management/object_edit.html', 
                              { 'form':form },
                              )
    
@permission_required('Management.add_czilber')
def project_cz(request, project_id):
    c = ProjectCommission.objects.get(project__id = project_id)
    cz = c.c_zilber or CZilber()
    
    if request.method == 'POST':
        form = CZilberForm(request.POST, instance= cz)
        if form.is_valid():
            c.c_zilber = form.save()
            c.save()
    else:
        form = CZilberForm(instance= cz)
            
    return render(request, 'Management/object_edit.html', 
                              { 'form':form },
                              )

@permission_required('Management.add_bdiscountsaveprecentage')
def project_bdsp(request, project_id):
    c = ProjectCommission.objects.get(project__id = project_id)
    bdsp = c.b_discount_save_precentage or BDiscountSavePrecentage()
    
    if request.method == 'POST':
        form = BDiscountSavePrecentageForm(request.POST, instance = bdsp)
        if form.is_valid():
            c.b_discount_save_precentage = form.save()
            c.save()
    else:
        form = BDiscountSavePrecentageForm(instance=bdsp)
            
    return render(request, 'Management/object_edit.html', 
                              { 'form':form },
                              )
    
@permission_required('Management.add_contact')
def project_contact(request, project_id, demand=False, payment=False):
    project = Project.objects.get(pk=project_id)
    if request.method == 'POST':
        form = ContactForm(request.POST)
        existForm = ExistContactForm(request.POST)
        if existForm.is_valid():
            c = existForm.cleaned_data['contact']
            form = ContactForm()
        elif form.is_valid():
            existForm = ExistContactForm(initial={'contact':(demand and project.demand_contact and project.demand_contact.id) or (payment and project.payment_contact and project.payment_contact.id)})
            c = form.save()
        else:
            c=None
        if c:
            if demand:
                project.demand_contact = c
            elif payment:
                project.payment_contact = c
            else:
                project.contacts.add(c)
            project.save()
    else:
        form = ContactForm()
        existForm = ExistContactForm(initial={'contact':(demand and project.demand_contact and project.demand_contact.id) or (payment and project.payment_contact and project.payment_contact.id)})
        
    return render(request, 'Management/project_contact_edit.html', 
                              { 'form':form, 'existForm':existForm },
                              )

@permission_required('Management.change_employee')
def employee_project_add(request, employee_id):
    if request.method == 'POST':
        form = EmployeeAddProjectForm(request.POST)
        if form.is_valid():
            project, employee, start_date = form.cleaned_data['project'], form.cleaned_data['employee'], form.cleaned_data['start_date']
            # check if the employee already has an open commission for this project
            open_commissions = employee.commissions.filter(project = project, end_date = None)
            if len(open_commissions) == 0:
                employee.projects.add(project)

                # create EPCommission
                commission = EPCommission(employee=employee, project=project, start_date=start_date)
                commission.save()

                # add commission to employee
                employee.commissions.add(commission)
            else:
                # TODO: something
                pass
    else:
        form = EmployeeAddProjectForm(initial={'employee':employee_id})
    return render(request, 'Management/object_edit.html', 
                              { 'form':form, 'title':u'העסקה בפרוייקט חדש' },
                              )

@permission_required('Management.change_employee')
def employee_project_remove(request, employee_id, project_id):
    project = Project.objects.get(pk = project_id)
    employee = Employee.objects.get(pk = employee_id)
    if request.method == 'POST':
        form = EmployeeRemoveProjectForm(request.POST)
        if form.is_valid():
            project, employee, end_date = form.cleaned_data['project'], form.cleaned_data['employee'], form.cleaned_data['end_date']
            for epc in employee.commissions.filter(project=project):
                epc.end_date = end_date
                epc.save()
            employee.projects.remove(project)
    else:
        form = EmployeeRemoveProjectForm(initial={'employee':employee_id, 'project':project.id})
    return render(request, 'Management/object_edit.html', 
                              { 'form':form, 'title':u'סיום העסקה בפרוייקט' },
                              )

class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = 'Management/contact_list.html'

class ContactCreate(PermissionRequiredMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_contact'

class ContactUpdate(PermissionRequiredMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_contact'

@permission_required('Management.change_contact')
def project_removecontact(request, id, project_id):
    p = Project.objects.get(pk=project_id)
    contact = Contact.objects.get(pk=id)
    
    for attr in ['projects','projects_demand','projects_payment']:
        attr_value = getattr(contact, attr)
        try:
            attr_value.remove(p)
        except:
            pass

    return HttpResponseRedirect('/projects/%s' % p.id)

@permission_required('Management.delete_contact')
def project_deletecontact(request, id, project_id):
    p = Project.objects.get(pk=project_id)
    contact = Contact.objects.get(pk=id)
    contact.projects.clear()
    contact.projects_demand.clear()
    contact.projects_payment.clear()
    contact.delete()
    return HttpResponseRedirect('/projects/%s' % p.id)
    
@permission_required('Management.delete_contact')
def contact_delete(request, project_id, id):
    contact = Contact.objects.get(pk=id)
    contact.projects.clear()
    contact.projects_demand.clear()
    contact.projects_payment.clear()
    contact.delete()
    return HttpResponseRedirect('/contacts')

@permission_required('Management.add_attachment')
def obj_add_attachment(request, obj_id, model):
    content_type = ContentType.objects.get_for_model(model)
    obj = content_type.get_object_for_this_type(pk = obj_id)
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES, initial={'is_private':False})
        attachment = form.instance
        attachment.user_added = request.user
        attachment.file = request.FILES['file']
        attachment.content_type = content_type
        attachment.object_id = obj_id
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('../attachments')
    else:
        form = AttachmentForm()
    
    return render(request, 'Management/attachment_add.html',
                              {'form': form, 'obj':obj}, )

@login_required
def obj_attachments(request, obj_id, model):
    content_type = ContentType.objects.get_for_model(model)
    obj = content_type.get_object_for_this_type(pk = obj_id)
    attachments = Attachment.objects.filter(content_type = content_type, object_id = obj_id)

    if not request.user.is_staff:
        attachments = attachments.filter(is_private=False)
        
    return render(request, 'Management/object_attachment_list.html', 
                              {'attachments': attachments, 'obj':obj}, 
                              )

@permission_required('Management.add_reminder')
def obj_add_reminder(request, obj_id, model):
    obj = model.objects.get(pk= obj_id)
    if request.method == 'POST':
        form = ReminderForm(data= request.POST)
        if form.is_valid():
            r = form.save()
            obj.reminders.add(r)
            return HttpResponseRedirect('reminders')
    else:
        form = ReminderForm(initial={'status':ReminderStatusType.Added})
    
    return render(request, 'Management/object_edit.html',
                              {'form': form}, )

@login_required
def obj_reminders(request, obj_id, model):
    obj = model.objects.get(pk = obj_id)
    return render(request, 'Management/reminder_list.html',
                              {'reminders': obj.reminders}, )

class ReminderUpdate(PermissionRequiredMixin, UpdateView):
    model = Reminder
    form_class = ReminderForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_reminder'

@permission_required('Management.delete_reminder')
def reminder_del(request, id):
    r = Reminder.objects.get(pk= id)
    if r.statuses.latest().type.id == ReminderStatusType.Deleted:
        return HttpResponse('reminder is already deleted')
    else:
        r.delete()
        return HttpResponse('ok')
    
@permission_required('Management.change_reminder')
def reminder_do(request, id):
    r = Reminder.objects.get(pk= id)
    if r.statuses.latest().type.id == ReminderStatusType.Done:
        return HttpResponse('reminder is already done')
    else:
        r.do()
        return HttpResponse('ok')

@login_required
def project_buildings(request, project_id):
    p = Project.objects.get(pk = project_id)
    buildings = p.buildings.filter(is_deleted=False)
    total_signed_houses, total_houses, total_avalible_houses, total_sold_houses = 0,0,0,0
    for b in buildings:
        total_houses = total_houses + b.house_count
        total_signed_houses += len(b.houses.signed())
        total_sold_houses += len(b.houses.sold())
        total_avalible_houses += len(b.houses.avalible())

    return render(request, 'Management/building_list.html', 
                              { 'buildings' : buildings,'total_houses':total_houses,'project':p,
                               'total_signed_houses':total_signed_houses, 'total_avalible_houses':total_avalible_houses, 'total_sold_houses':total_sold_houses},
                              )

@permission_required('Management.add_building')
def building_add(request, project_id=None):
    if request.method == 'POST':
        form = BuildingForm(request.POST)
        if form.is_valid():
            building = form.save()
            return HttpResponseRedirect('../buildings')
    else:
        form = BuildingForm()
        if project_id:
            project = Project.objects.get(pk=project_id)
            form.initial = {'project':project.id}
            
    return render(request, 'Management/object_edit.html', 
                              {'form' : form})

@permission_required('Management.add_parking')
def building_addparking(request, building_id = None):
    if request.method == 'POST':
        form = ParkingForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = ParkingForm()
        if building_id:
            b = Building.objects.get(pk=building_id)
            form.initial = {'building':b.id}
            form.fields['house'].queryset = b.houses.all()
    return render(request, 'Management/object_edit.html', 
                              {'form' : form},
                              )

class ParkingUpdate(PermissionRequiredMixin, UpdateView):
    model = Parking
    form_class = ParkingForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_parking'

@permission_required('Management.add_storage')
def building_addstorage(request, building_id = None):
    if request.method == 'POST':
        form = StorageForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = StorageForm()
        if building_id:
            b = Building.objects.get(pk=building_id)
            form.initial = {'building':b.id}
            form.fields['house'].queryset = b.houses.all()
    return render(request, 'Management/object_edit.html', {'form' : form}, )
        
class StorageUpdate(PermissionRequiredMixin, UpdateView):
    model = Storage
    form_class = StorageForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_storage'

@permission_required('Management.delete_building')
def building_delete(request, building_id):
    building = Building.objects.get(pk = building_id)
    building.is_deleted = True
    building.save()
    return HttpResponse('ok')
        
@permission_required('Management.copy_building')
def building_copy(request, building_id):
    building = Building.objects.get(pk = building_id)
    if request.method == 'POST':
        form = CopyBuildingForm(request.POST)
        if form.is_valid():
            include_houses, include_house_prices, include_parkings, include_storages = (form.cleaned_data['include_houses'],
                                                                                        form.cleaned_data['include_house_prices'],
                                                                                        form.cleaned_data['include_parkings'],
                                                                                        form.cleaned_data['include_storages'])
            
            if building.pricelist:
                new_pricelist = common.clone(building.pricelist, False)
                new_pricelist.save()
            else:
                new_pricelist = None
            
            new_building = common.clone(building, False)
            new_building.num = form.cleaned_data['new_building_num']
            new_building.pricelist = new_pricelist
            new_building.save()
            
            if include_parkings:
                for parking in building.parkings.filter(house__isnull=True):
                    new_parking = common.clone(parking, False)
                    new_parking.building = new_building
                    new_parking.save()
                    
            if include_storages:
                for storage in building.storages.filter(house__isnull=True):
                    new_storage = common.clone(storage, False)
                    new_storage.building = new_building
                    new_storage.save()
                                
            if include_houses:
                for house in building.houses.all():
                    new_house = common.clone(house, False)
                    new_house.building = new_building
                    new_house.save()
                    
                    if include_house_prices:
                        for house_version in house.versions.all():
                            new_house_version = common.clone(house_version, False)
                            new_house_version.house = new_house
                            new_house_version.save()
                            
                    if include_parkings:
                        for parking in house.parkings.all():
                            new_parking = common.clone(parking, False)
                            new_parking.house = new_house
                            new_parking.building = new_building
                            new_parking.save()
                            
                    if include_storages:
                        for storage in house.storages.all():
                            new_storage = common.clone(storage, False)
                            new_storage.house = new_house
                            new_storage.building = new_building
                            new_storage.save()
                    
            return HttpResponseRedirect(reverse(project_buildings, args=[building.project_id]))
    else:
        form = CopyBuildingForm()
        form.fields['building'].queryset = building.project.buildings.filter(is_deleted=False)
        form.fields['building'].initial = building.id
        
    return render(request, 'Management/object_edit.html',
                              {'form' : form, 'title':gettext('copy_building')}, 
                              )
    
@permission_required('Management.add_house')
def building_addhouse(request, type_id, building_id):
    b = Building.objects.get(pk=building_id)
    if request.method == 'POST':
        form = HouseForm(type_id, data = request.POST)
        form.instance.building = b
        if form.is_valid():
            form.save(type_id)
            if 'addanother' in request.POST:
                next_url = reverse(building_addhouse, args=[building_id, type_id])
            elif 'finish' in request.POST:
                next_url = reverse(building_pricelist, args=[building_id, type_id])
            else:
                next_url = reverse(house_edit, args=[form.instance.id, type_id])
            return HttpResponseRedirect(next_url)
    else:
        form = HouseForm(type_id)
        form.instance.building = b
        if b.is_cottage():
            form.initial['type'] = HouseType.Cottage

    ps = Parking.objects.filter(building = b)
    ss = Storage.objects.filter(building = b)
    for f in ['parking1','parking2','parking3']:
        form.fields[f].queryset = ps
    for f in ['storage1','storage2']:
        form.fields[f].queryset = ss
    return render(request, 'Management/house_edit.html', 
                              {'form' : form, 'type':PricelistType.objects.get(pk = type_id) },
                              )

@permission_required('Management.house_versionlog')
def house_version_log(request, building_id, id ,type_id):
    house = House.objects.get(pk=id)
    pricelist_type = PricelistType.objects.get(pk=type_id)
    query = HouseVersion.objects.filter(house__id = id, type__id = type_id)
    versions = list(query)
    previous_version = None
    for version in versions:
        if previous_version:
            version.diff_amount = version.price - previous_version.price
            version.diff_precentage = float(version.price) / previous_version.price * 100 - 100
        previous_version = version
    
    return render(request, 'Management/house_version_log.html', 
                              {'title':u'מחירי %s עבור דירה %s' % (pricelist_type, house.num),
                               'versions':versions })
    
@permission_required('Management.change_house')
def house_edit(request, building_id, id ,type_id):
    h = House.objects.get(pk=id)
    b = h.building
    if request.method == 'POST':
        form = HouseForm(type_id, data = request.POST, instance = h)
        if form.is_valid():
            form.save(type_id)
            if 'addanother' in request.POST:
                return HttpResponseRedirect('../../addhouse/type%s' % type_id)
            elif 'finish' in request.POST:
                return HttpResponseRedirect('../../pricelist/type%s' % type_id)
    else:
        form = HouseForm(type_id, instance = h)
        if b.is_cottage():
            form.initial['type'] = HouseType.Cottage

    ps = Parking.objects.filter(building = b)
    ss = Storage.objects.filter(building = b)
    for f in ['parking1','parking2','parking3']:
        form.fields[f].queryset = ps
    for f in ['storage1','storage2']:
        form.fields[f].queryset = ss
    return render(request, 'Management/house_edit.html', 
                              {'form' : form, 'type':PricelistType.objects.get(pk = type_id) },
                              )

@permission_required('Management.delete_house')
def house_delete(request, building_id, type_id, house_id):
    house = House.objects.get(pk = house_id)
    house.delete()
    return HttpResponseRedirect("../../../type%s" % type_id)
        
@permission_required('Management.add_loan')
def employee_addloan(request, employee_id):
    employee = Employee.objects.get(pk = employee_id)
    if request.method=='POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            form.save() 
    else:
        form = LoanForm(initial={'employee':employee.id})
    
    return render(request, 'Management/object_edit.html',
                              {'form' : form}, )
    
@permission_required('Management.add_loanpay')
def employee_loanpay(request, employee_id):
    e = Employee.objects.get(pk=employee_id)
    if request.method == 'POST':
        form = LoanPayForm(request.POST)
        if form.is_valid():
            form.instance.employee = e
            form.save()
    else:
        form = LoanPayForm(initial={'employee':e.id})
    return render(request, 'Management/object_edit.html',
                              {'form' : form}, )

class EmployeeCreate(PermissionRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    permission_required = 'Management.change_employee'

class EmployeeUpdate(PermissionRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    permission_required = 'Management.change_employee'

@permission_required('Management.change_employee')
def employee_end(request, object_id):
    employee = EmployeeBase.objects.get(pk=object_id)
    if request.method == 'POST':
        form = EmployeeEndForm(request.POST, instance = employee)
        if form.is_valid():
            form.save()

            employee_derived = employee.derived

            if isinstance(employee_derived, Employee):
                for epcommission in employee_derived.commissions.all():
                    if not epcommission.end_date:
                        epcommission.end_date = employee.work_end
                        epcommission.save()
            elif isinstance(employee_derived, NHEmployee):
                for nhbranchemployee in employee_derived.nhbranchemployee_set.all():
                    if not nhbranchemployee.end_date:
                        nhbranchemployee.end_date = employee.work_end
                        nhbranchemployee.save()
    else:
        form = EmployeeEndForm(instance = employee)
        
    return render(request, 'Management/object_edit.html',
                              {'form' : form}, )

@permission_required('Management.add_loan')
def nhemployee_addloan(request, employee_id):
    employee = NHEmployee.objects.get(pk = employee_id)
    if request.method=='POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            form.save() 
    else:
        form = LoanForm(initial={'employee':employee.id})
    
    return render(request, 'Management/object_edit.html',
                              {'form' : form}, )
    
@permission_required('Management.add_loanpay')
def nhemployee_loanpay(request, employee_id):
    e = NHEmployee.objects.get(pk=employee_id)
    if request.method == 'POST':
        form = LoanPayForm(request.POST)
        if form.is_valid():
            form.instance.nhemployee = e
            form.save()
    else:
        form = LoanPayForm(initial={'employee':e.id})
    return render(request, 'Management/object_edit.html',
                              {'form' : form}, )

@permission_required('Management.add_employmentterms')
def employee_employmentterms(request, id, model):
    employee = model.objects.get(pk = id)
    terms = employee.employment_terms or EmploymentTerms()
    terms_dict = terms.__dict__.copy()

    allow_history = [ 'salary_base', 'safety', 'tax_deduction_source_precentage' ]

    if request.method == "POST":
        form = EmploymentTermsForm(request.POST, instance=terms)
        if form.is_valid():
            form_dict = form.instance.__dict__

            for item in terms._meta.fields :
                name = item.name

                if name in form_dict and name in allow_history :
                    value     = form_dict.get(name)
                    value_len = value != None and len(str(value)) or 0

                    if value_len > 0 and ( terms_dict.get(name) != value ):
                        TransactionUpdateHistory( transaction_type='0', transaction_id=id, field_name=name, field_value=(value and value or ''), timestamp=datetime.now() ).save()

            employee.employment_terms = form.save()
            employee.save()
    else:
        form = EmploymentTermsForm(instance=terms)
    return render(request, 'Management/object_edit.html', 
                              { 'form':form },
                              )
    
@permission_required('Management.add_cvar')
def employee_cv(request, employee_id, project_id):
    pc = EPCommission.objects.get(employee__id = employee_id, project__id = project_id, end_date__isnull = True)
    cv = pc.c_var or CVar()
    InlineFormSet = inlineformset_factory(CVar, CAmount, fields=('amount',), extra = 10, max_num = 10)
    
    if request.method == "POST":
        formset = InlineFormSet(request.POST, instance=cv)
        form = CVarForm(request.POST, instance=cv)
        if formset.is_valid() and form.is_valid():
            pc.c_var = form.save()
            pc.save()
            formset.save()
    else:
        formset = InlineFormSet(instance=cv)
        form = CVarForm(instance=cv)
    return render(request, 'Management/commission_inline.html', 
                              { 'formset':formset,'form':form, 'show_house_num':True },
                              )
    
@permission_required('Management.add_cvarprecentage')
def employee_cvp(request, employee_id, project_id):
    pc = EPCommission.objects.get(employee__id = employee_id, project__id = project_id, end_date__isnull = True)
    cvp = pc.c_var_precentage or CVarPrecentage()
    InlineFormSet = inlineformset_factory(CVarPrecentage, CPrecentage, fields=('precentage',), extra = 10, max_num = 10)
    
    if request.method == "POST":
        formset = InlineFormSet(request.POST, instance=cvp)
        form = CVarPrecentageForm(request.POST, instance=cvp)
        if formset.is_valid() and form.is_valid():
            pc.c_var_precentage = form.save()
            pc.save()
            formset.save()
    else:
        formset = InlineFormSet(instance=cvp)
        form = CVarPrecentageForm(instance=cvp)
    return render(request, 'Management/commission_inline.html', 
                              { 'formset':formset,'form':form, 'show_house_num':True },
                              )
    
@permission_required('Management.add_cbyprice')
def employee_cbp(request, employee_id, project_id):
    pc = EPCommission.objects.get(employee__id = employee_id, project__id = project_id, end_date__isnull = True)
    cbp = pc.c_by_price or CByPrice()
    InlineFormSet = inlineformset_factory(CByPrice, CPriceAmount,CPriceAmountForm, extra = 10, max_num = 10)
    if request.method == "POST":
        formset = InlineFormSet(request.POST, instance=cbp)
        form = CByPriceForm(request.POST, instance=cbp)
        if formset.is_valid() and form.is_valid():
            pc.c_by_price = form.save()
            pc.save()
            formset.save()
    else:
        formset = InlineFormSet(instance = cbp)
        form = CByPriceForm(instance = cbp)
        
    return render(request, 'Management/commission_inline.html', 
                              { 'form':form, 'formset':formset, 'show_house_num':False },
                              )

@permission_required('Management.add_bsalerate')
def employee_bsr(request, employee_id, project_id):
    pc = EPCommission.objects.get(employee__id = employee_id, project__id = project_id, end_date__isnull = True)
    bsr = pc.b_sale_rate or BSaleRate()
    InlineFormSet = inlineformset_factory(BSaleRate, SaleRateBonus, fields=('house_count','amount'), extra = 10, max_num = 10)
    if request.method == "POST":
        formset = InlineFormSet(request.POST, instance=bsr)
        form = BSaleRateForm(request.POST, instance=bsr)
        if formset.is_valid() and form.is_valid():
            pc.b_sale_rate = form.save()
            pc.save()
            formset.save()
    else:
        formset = InlineFormSet(instance = bsr)
        form = BSaleRateForm(instance = bsr)
        
    return render(request, 'Management/commission_inline.html', 
                              { 'form':form, 'formset':formset, 'show_house_num':False},
                              )
    
@permission_required('Management.add_bhousetype')
def employee_bht(request, employee_id, project_id):
    pc = EPCommission.objects.get(employee__id = employee_id, project__id = project_id, end_date__isnull = True)
    htb = pc.b_house_type or BHouseType()
    InlineFormSet = inlineformset_factory(BHouseType, HouseTypeBonus, fields=('type','amount'), extra = 10, max_num = 10)
    if request.method == "POST":
        formset = InlineFormSet(request.POST, instance=htb)
        form = BHouseTypeForm(request.POST, instance=htb)
        if formset.is_valid() and form.is_valid():
            pc.b_house_type = form.save()
            pc.save()
            formset.save()
    else:
        formset = InlineFormSet(instance=htb)
        form = BHouseTypeForm(instance = htb)
        
    return render(request, 'Management/commission_inline.html', 
                              { 'form':form, 'formset':formset, 'show_house_num':False},
                              )
    
@permission_required('Management.add_bdiscountsave')
def employee_bds(request, employee_id, project_id):
    pc = EPCommission.objects.get(employee__id = employee_id, project__id = project_id, end_date__isnull = True)
    bds = pc.b_discount_save or BDiscountSave()
    
    if request.method == 'POST':
        form = BDiscountSaveForm(request.POST, instance = bds)
        if form.is_valid():
            pc.b_discount_save = form.save()
            pc.save()
    else:
        form = BDiscountSaveForm(instance=bds)
            
    return render(request, 'Management/object_edit.html', 
                              { 'form':form },
                              )

@permission_required('Management.add_bdiscountsaveprecentage')
def employee_bdsp(request, employee_id, project_id):
    pc = EPCommission.objects.get(employee__id = employee_id, project__id = project_id, end_date__isnull = True)
    bdsp = pc.b_discount_save_precentage or BDiscountSavePrecentage()
    
    if request.method == 'POST':
        form = BDiscountSavePrecentageForm(request.POST, instance = bdsp)
        if form.is_valid():
            pc.b_discount_save_precentage = form.save()
            pc.save()
    else:
        form = BDiscountSavePrecentageForm(instance=bdsp)
            
    return render(request, 'Management/object_edit.html', 
                              { 'form':form },
                              )

class NHBranchEmployeeCreate(PermissionRequiredMixin, CreateView):
    model = NHBranchEmployee
    form_class = NHBranchEmployeeForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.add_nhbranchemployee'

    def get_initial(self):
        initial = super().get_initial()
        branch_id = self.kwargs.get('nhbranch_id')
        initial['nhbranch'] = branch_id
        return initial

class NHBranchEmployeeUpdate(PermissionRequiredMixin, UpdateView):
    model = NHBranchEmployee
    form_class = NHBranchEmployeeForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_nhbranchemployee'

@login_required
def json_buildings(request, project_id):
    data = serializers.serialize('json', Project.objects.get(pk= project_id).non_deleted_buildings(), 
                                 fields=('id','name','num'))
    return HttpResponse(data)

@login_required
def json_employees(request, project_id):
    l = [EmployeeBase.objects.get(pk=e.id) for e in Project.objects.get(pk=project_id).employees.active()]
    data = serializers.serialize('json', l, 
                                 fields=('id','pid','first_name','last_name'))
    return HttpResponse(data)

@login_required
def json_houses(request, building_id):
    houses = House.objects.filter(building__id = building_id)
    data = serializers.serialize('json', houses, fields=('id','num'))
    return HttpResponse(data)

@login_required
def json_house(request, house_id):
    data = serializers.serialize('json', [House.objects.get(pk= house_id),])
    return HttpResponse(data)
    house = House.objects.get(pk= house_id)
    fields = {}
    for field in ['id', 'num', 'floor', 'rooms', 'allowed_discount', 'parking', 'warehouse', 'remarks']:
        fields[field] = 1 and getattr(house, field) or ''
    fields['price'] = house.prices.latest().price
    a = '[' + str({'pk':house.id, 'model':'Management.house', 'fields':fields}) + ']'
    return HttpResponse(a)
  
@login_required
def json_links(request):
    data = serializers.serialize('json', Link.objects.all())
    return HttpResponse(data)

@login_required
def task_list(request):
    sender = request.GET.get('sender', 'others')
    status = request.GET.get('status', 'undone')
    filterForm = TaskFilterForm(initial={'sender':sender, 'status':status})
    tasks = request.user.tasks.filter(is_deleted = False)
    if sender == 'me':
        tasks = tasks.filter(sender = request.user)
    if sender == 'others':
        tasks = tasks.filter(user = request.user)
    if status == 'done':
        tasks = tasks.filter(is_done = True)
    if status == 'undone':
        tasks = tasks.filter(is_done = False)
    
    return render(request, 'Management/task_list.html',
                              {'tasks': tasks, 'filterForm' : filterForm}, )

@permission_required('Management.add_task')
def task_add(request):
    if request.method=='POST':
        form = TaskForm(data = request.POST)
        if form.is_valid():
            t = form.instance
            t.sender = request.user
            form.save()
    else:
        form = TaskForm()
    
    return render(request, 'Management/object_edit.html',
                              {'form' : form}, )
    

class TaskDelete(PermissionRequiredMixin, DeleteView):
    model = Task
    success_url = '/tasks'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_task'

@permission_required('Management.change_task')
def task_do(request, id):
    t = Task.objects.get(pk = id)
    if t.is_done:
        return HttpResponse('task is already done')
    else:
        t.do()
        return HttpResponseRedirect('/tasks')    

@permission_required('Management.delete_task')
def task_del(request, id):
    t = Task.objects.get(pk = id)
    if t.is_deleted:
        return HttpResponse('task is already deleted')
    else:
        t.delete()
        return HttpResponseRedirect('/tasks')

class AttachmentUpdate(PermissionRequiredMixin, UpdateView):
    model = Attachment
    form_class = AttachmentForm
    template_name = 'Management/object_edit.html'
    permission_required = 'Management.change_attachment'

class AttachmentDelete(PermissionRequiredMixin, DeleteView):
    model = Attachment
    success_url = '/attachments'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_attachment'

@permission_required('Management.list_attachment')
def attachment_list(request):
    attachments = Attachment.objects.all()
    
    if len(request.GET):
        project_select_form = ProjectSelectForm(request.GET, prefix = 'project')
        employee_select_form = EmployeeSelectForm(request.GET, prefix = 'employee')
        demand_select_form = DemandSelectForm(request.GET, prefix = 'demand')
        
        object_id, content_type = None, None
        
        if 'project' in request.GET:
            if project_select_form.is_valid():
                project = project_select_form.cleaned_data['project']
                model = project.__class__
                content_type = ContentType.objects.get_for_model(model)
                object_id = project.id
        elif 'employee' in request.GET:
            if employee_select_form.is_valid():
                employee = employee_select_form.cleaned_data['employee']
                model = employee.__class__
                content_type = ContentType.objects.get_for_model(model)
                object_id = employee.id
        elif 'demand' in request.GET:
            if demand_select_form.is_valid():
                kwargs = demand_select_form.cleaned_data
                demand = Demand.objects.get(**kwargs)
                model = demand.__class__
                content_type = ContentType.objects.get_for_model(model)
                object_id = demand.id
        
        attachments = attachments.filter(content_type = content_type, object_id = object_id)
    else:
        project_select_form = ProjectSelectForm(prefix = 'project')
        employee_select_form = EmployeeSelectForm(prefix = 'employee')
        demand_select_form = DemandSelectForm(prefix = 'demand')
          
    return render(request, 'Management/attachment_list.html', 
                              {'project_select_form':project_select_form, 'employee_select_form':employee_select_form,
                               'demand_select_form':demand_select_form, 'attachments':attachments },
                              )

@permission_required('Management.add_attachment')
def attachment_add(request):
    if request.method == "POST":
        form = AttachmentForm(request.POST, request.FILES)
        project_select_form = ProjectSelectForm(request.POST, prefix = 'project')
        employee_select_form = EmployeeSelectForm(request.POST, prefix = 'employee')
        demand_select_form = DemandSelectForm(request.POST, prefix = 'demand')
        
        attachment = form.instance
        attachment.user_added = request.user
        attachment.file = request.FILES['file']
        
        if 'project' in request.POST:
            if project_select_form.is_valid():
                attachment.content_type = ContentType.objects.get_for_model(Project)
                attachment.object_id = project_select_form.cleaned_data['project'].id
        elif 'employee' in request.POST:
            if employee_select_form.is_valid():
                attachment.content_type = ContentType.objects.get_for_model(EmployeeBase)
                attachment.object_id = employee_select_form.cleaned_data['employee'].id
        elif 'demand' in request.POST:
            if demand_select_form.is_valid():
                attachment.content_type = ContentType.objects.get_for_model(Demand)
                kwargs = demand_select_form.cleaned_data
                demand = Demand.objects.get(**kwargs)
                attachment.object_id = demand.id
        
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/attachments')
    else:
        form = AttachmentForm()
        project_select_form = ProjectSelectForm(prefix = 'project')
        employee_select_form = EmployeeSelectForm(prefix = 'employee')
        demand_select_form = DemandSelectForm(prefix = 'demand')
        
    return render(request, 'Management/attachment_add.html', 
                              {'form':form, 'project_select_form':project_select_form, 'employee_select_form':employee_select_form,
                               'demand_select_form':demand_select_form },
                              )

@permission_required('Management.change_sale')
#@transaction.autocommit
def sale_edit(request, id):
    sale = Sale.objects.get(pk=id)
    if request.POST:
        form = SaleForm(request.POST, instance = sale)
        #handles the case when the building changes, and the house is not in the queryset of the house field
        form.fields['house'].queryset = House.objects.all()
        form.fields['building'].queryset = Building.objects.all()
        if form.is_valid():
            project = form.cleaned_data['project']
            next = None
            #temp fix. should remove
            demand = sale.demand
            if demand.statuses.count() == 0:
                demand.feed()
            if demand.was_sent:
                #check for mods:
                if form.changed_data.count('price'):
                    try:
                        spm = sale.salepricemod
                    except SalePriceMod.DoesNotExist:
                        spm = SalePriceMod(sale = sale, old_price = sale.price) 
                    spm.save()
                    next = '/salepricemod/%s' % spm.id
                if form.changed_data.count('house'):
                    try:
                        shm = sale.salehousemod
                    except SaleHouseMod.DoesNotExist:
                        shm = SaleHouseMod(sale = sale, old_house = sale.house)
                    shm.save()
                    next = '/salehousemod/%s' % shm.id
            form.save()

            calc_demands([demand])

            year, month = sale.demand.year, sale.demand.month
            employees = demand.project.employees.exclude(work_end__isnull = False, work_end__lt = date(year, month, 1))
            
            salaries_to_calc = list(EmployeeSalary.objects.nondeleted().filter(employee__in = employees, year = year, month = month))
            calc_salaries(salaries_to_calc)

            if 'addanother' in request.POST:
                return HttpResponseRedirect(next or '/demands/%s/sale/add' % sale.demand.id)
            elif 'todemand' in request.POST:
                return HttpResponseRedirect(next or '/demands/%s' % sale.demand.id)
    else:
        form = SaleForm(instance= sale)
    return render(request, 'Management/sale_edit.html', 
                              {'form':form, 'year':sale.actual_demand.year, 'month':sale.actual_demand.month},
                              )    

@permission_required('Management.add_sale')
#@transaction.autocommit
def sale_add(request, demand_id=None):
    if demand_id:
        demand = Demand.objects.get(pk = demand_id)
        year, month = demand.year, demand.month
    else:
        year, month = common.current_month().year, common.current_month().month
    if request.POST:
        form = SaleForm(request.POST)
        if form.is_valid():
            if not demand_id:
                demand, new = Demand.objects.get_or_create(year = year, month = month, project = form.cleaned_data['project'])
            form.instance.demand = demand
            form.save()
            next = None
            if demand.statuses.count() == 0:
                demand.feed()
            if demand.was_sent:
                sp = SalePre(sale = form.instance,
                             to_month = month, to_year = year,
							 employee_pay_year = month == 12 and year + 1 or year,
							 employee_pay_month = month == 12 and 1 or month)
                sp.save()
                next = '/salepre/%s' % sp.id 
            
            calc_demands([demand])
            
            employees = demand.project.employees.exclude(work_end__isnull = False, work_end__lt = date(year, month, 1))
            
            salaries_to_calc = list(EmployeeSalary.objects.nondeleted().filter(employee__in = employees, year = year, month = month))
            calc_salaries(salaries_to_calc)
                
            if 'addanother' in request.POST:
                return HttpResponseRedirect(next or reverse(sale_add, args=[demand_id]))
            elif 'todemand' in request.POST:
                return HttpResponseRedirect(next or '/demands/%s' % demand.id)
    else:
        form = SaleForm()
        if demand_id:
            p = demand.project
            form.fields['project'].initial = p.id
            form.fields['employee'].queryset = p.employees.all()
            form.fields['building'].queryset = p.buildings.all()
            form.fields['commission_madad_bi'].initial = demand.get_madad()
    return render(request, 'Management/sale_edit.html', 
                              {'form':form, 'year':year, 'month':month},
                              )

def demand_sale_list(request):
    demand_id = int(request.GET.get('demand_id', 0))
    project_id = int(request.GET.get('project_id', 0))
    from_year = int(request.GET.get('from_year', 0))
    from_month = int(request.GET.get('from_month', 0))
    to_year = int(request.GET.get('to_year', 0))
    to_month = int(request.GET.get('to_month', 0))

    if demand_id:
        demand = Demand.objects.get(pk=demand_id)
        project, year, month = demand.project, demand.year, demand.month

        demands = [demand]

        set_demand_total_fields(demands, year, month, year, month)

        title = u'ריכוז מכירות לפרוייקט %s לחודש %s/%s' % (str(project), month, year)
    elif project_id:
        project = Project.objects.get(pk=project_id)
        
        demands = Demand.objects \
            .range(from_year, from_month, to_year, to_month) \
            .filter(project = project)

        set_demand_total_fields(demands, from_year, from_month, to_year, to_month)

        title = u'ריכוז מכירות לפרוייקט %s מחודש %s/%s עד חודש %s/%s' % (str(project), from_month, from_year,
                                                                         to_month, to_year)
    else:
        raise ValueError

    sales = []
    sales_amount = 0

    for demand in demands:
        sales.extend(demand.sales_list)
        sales_amount += demand.sales_amount

    return render(request, 'Management/sale_list.html', 
        {'sales':sales, 'sales_amount':sales_amount,'title':title})

@login_required
def project_demands(request, project_id, func, template_name):
    p = Project.objects.get(pk = project_id)
    demands = getattr(p, func)
    return render(request, template_name,
                               {'demands':demands(), 'project':p},
                               )

@login_required
def demand_sales(request, project_id, year, month):
    try:
        demand = Demand.objects.get(project__id = project_id, year = year, month = month)
        sales = demand.get_sales()
    except Demand.DoesNotExist:
        sales = Demand.objects.none()
        
    return render(request, 'Management/sale_table.html',
							  {'sales':sales},
							  )

@permission_required('Management.report_employee_sales')
def report_employee_sales(request):
    if len(request.GET):
        form = ProjectSeasonForm(request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            project, from_month, from_year, to_month, to_year = cleaned_data['project'], cleaned_data['from_month'], \
                cleaned_data['from_year'], cleaned_data['to_month'], cleaned_data['to_year']
                
            demands = Demand.objects.range(from_year, from_month, to_year, to_month).filter(project = project)
            
            writer = EmployeeSalesWriter(project, from_month, from_year, to_month, to_year, demands)
            
            return build_and_return_pdf(writer)

    error = u'לא ניתן להפיק את הדו"ח. אנא ודא שכל הנתונים הוזנו כראוי.'
    return render(request, 'Management/error.html', {'error': error}, )
        
    

@permission_required('Management.demand_pdf')
def report_project_month(request, project_id = 0, year = 0, month = 0, demand = None):
    if not (demand or (project_id and year and month)):
        raise ValueError % 'must supply either demand or project_id, year and month'
    
    if not demand:
        demand = Demand.objects.get(project__id = project_id, year = year, month = month)
    
    if demand.get_sales().count() == 0:
        return render(request, 'Management/error.html', {'error':u'לדרישה שנבחרה אין מכירות'}, )
    
    writer = MonthDemandWriter(demand, to_mail=False)
    
    return build_and_return_pdf(writer)

@permission_required('Management.report_projects_month')
def report_projects_month(request, year, month):

    demands = Demand.objects.filter(year = year, month=month).all()

    title = u'ריכוז דרישות לפרוייקטים לחודש %s\%s' % (year, month)

    writer = MultipleDemandWriter(demands, title, show_month=False, show_project=True)

    return build_and_return_pdf(writer)

@permission_required('demand_season_pdf')
def report_project_season(request, project_id=None, from_year=common.current_month().year, from_month=common.current_month().month, 
                          to_year=common.current_month().year, to_month=common.current_month().month):
    from_date = date(int(from_year), int(from_month), 1)
    to_date = date(int(to_year), int(to_month), 1)
    
    demands = Demand.objects.range(from_date.year, from_date.month, to_date.year, to_date.month).filter(project__id = project_id)
    
    project = Project.objects.get(pk=project_id)

    title = u'ריכוז דרישות תקופתי לפרוייקט %s' % project

    writer = MultipleDemandWriter(demands, title, show_month=True, show_project=False)

    return build_and_return_pdf(writer)

@permission_required('demand_followup_pdf')
def report_project_followup(request, project_id=None, from_year=common.current_month().year, from_month=common.current_month().month, 
                            to_year=common.current_month().year, to_month=common.current_month().month):
    from_date = date(int(from_year), int(from_month), 1)
    to_date = date(int(to_year), int(to_month), 1)
    
    project = Project.objects.get(pk = project_id)
    demands = Demand.objects.range(from_date.year, from_date.month, to_date.year, to_date.month).filter(project__id = project_id)

    writer = DemandFollowupWriter(project, from_month, from_year, to_month, to_year, demands)
    
    return build_and_return_pdf(writer)

@permission_required('Management.demand_season')
def demand_season_list(request):
    ds = Demand.objects.none()
    total_sales_count,total_sales_amount, total_amount = 0,0,0
    from_date, to_date, project = None, None, None
    
    if len(request.GET):
        form = ProjectSeasonForm(request.GET)
        if form.is_valid():
            project = form.cleaned_data['project']

            from_year, from_month = form.cleaned_data['from_year'], form.cleaned_data['from_month']
            to_year, to_month = form.cleaned_data['to_year'], form.cleaned_data['to_month']

            from_date = date(from_year, from_month, 1)
            to_date = date(to_year, to_month, 1)
            
            ds = Demand.objects \
                .range(from_year, from_month, to_year, to_month) \
                .filter(project = project) \
                .prefetch_related('reminders__statuses') \
                .select_related('project')

            set_demand_total_fields(ds, from_year, from_month, to_year, to_month)
            set_demand_diff_fields(ds)
            set_demand_last_status(ds)
            set_demand_is_fixed(ds)
            set_demand_open_reminders(ds)

            for d in ds:
                total_sales_count += d.sales_count
                total_sales_amount += d.sales_amount
                total_amount += d.total_amount
    else:
        form = ProjectSeasonForm()
        
    context = { 
        'demands':ds, 
        'start':from_date, 'end':to_date,
        'project':project, 'filterForm':form,
        'total_sales_count':total_sales_count,
        'total_sales_amount':total_sales_amount,
        'total_amount':total_amount
    }

    return render(request, 'Management/demand_season_list.html', context)

@permission_required('Management.demand_pay_balance')
def demand_pay_balance_list(request):
    if len(request.GET):
        form = DemandPayBalanceForm(request.GET)
        if form.is_valid():
            # gather form data
            cleaned_data = form.cleaned_data
            demand_pay_balance = cleaned_data['demand_pay_balance']
            project, from_year, from_month, to_year, to_month, all_times = \
                cleaned_data['project'], \
                cleaned_data['from_year'], \
                cleaned_data['from_month'], \
                cleaned_data['to_year'], \
                cleaned_data['to_month'], \
                cleaned_data['all_times']
            
            if project:
                query = Demand.objects.filter(project = project)
            else:
                query = Demand.objects.all()
            if from_year and from_month and to_year and to_month and not all_times:
                query = query.range(from_year, from_month, to_year, to_month)

            all_demands = query \
                .prefetch_related('reminders__statuses', 'invoices__offset','payments') \
                .select_related('project__demand_contact', 'project__payment_contact') \
                .order_by('project_id', 'year', 'month')

            set_demand_total_fields(all_demands, from_year, from_month, to_year, to_month)
            set_demand_diff_fields(all_demands)
            set_demand_invoice_payment_fields(all_demands)
            set_demand_open_reminders(all_demands)

            filters = {
                'un-paid': lambda demand: not demand.payments_amount,
                'mis-paid': lambda demand: demand.diff_invoice and demand.invoices_amount != None,
                'partially-paid': lambda demand: demand.diff_invoice_payment and demand.payments_amount != None,
                'fully-paid': lambda demand: demand.is_fully_paid,
                'all': lambda demand: True,
            }

            filter_func = filters[demand_pay_balance.id]

            # apply a filter to the list of demands
            all_demands = filter(filter_func, all_demands)
            
            # group the demands by project
            project_demands = {}
            
            for project, demand_iter in itertools.groupby(all_demands, lambda demand: demand.project):
                demands = list(demand_iter)
                project_demands[project] = demands

                project.total_amount = sum(map(lambda d: d.total_amount, demands))
                project.total_payments = sum(map(lambda d: d.payments_amount or 0, demands))
                project.total_invoices = sum(map(lambda d: (d.invoices_amount or 0) + (d.invoice_offsets_amount or 0), demands))
                project.total_diff_invoice = sum(map(lambda d: d.diff_invoice, demands))
                project.total_diff_invoice_payment = sum(map(lambda d: d.diff_invoice_payment, demands))
                
            if 'html' in request.GET:
                return render(request, 'Management/demand_pay_balance_list.html', 
                    { 'filterForm': form, 'project_demands': project_demands})
            elif 'pdf' in request.GET:
                # build arguments to the writer
                kwargs = {}
                for key in 'all_times', 'from_month', 'from_year', 'to_month', 'to_year', 'demand_pay_balance':
                    kwargs[key] = cleaned_data[key]
                kwargs['project_demands'] = project_demands
                
                writer = DemandPayBalanceWriter(**kwargs)
                
                return build_and_return_pdf(writer)
    else:
        return render(request, 'Management/demand_pay_balance_list.html', 
                                  { 'filterForm': DemandPayBalanceForm(), 'project_demands': {}},
                                  )

@permission_required('Management.season_income')
def season_income(request):
    total_sale_count, total_amount, total_amount_notax = 0,0,0
    from_date, to_date = None, None
    month_count = 1
    projects = []
    if len(request.GET):
        form = SeasonForm(request.GET)
        if form.is_valid():
            from_date = date(form.cleaned_data['from_year'], form.cleaned_data['from_month'], 1)
            to_date = date(form.cleaned_data['to_year'], form.cleaned_data['to_month'], 1)
                        
            ds = Demand.objects.range(from_date.year, from_date.month, to_date.year, to_date.month)
                
            for d in ds:
                if d.project in projects:
                    project = projects[projects.index(d.project)]
                else:
                    project = d.project
                    projects.append(project)
                    for attr in ['total_amount', 'total_amount_notax', 'total_sale_count']:
                        setattr(project, attr, 0)
                        
                tax = Tax.objects.filter(date__lte=date(d.year, d.month,1)).latest().value / 100 + 1
                
                # sum amount
                amount = d.get_total_amount()
                project.total_amount += amount
                project.total_amount_notax += amount / tax

                # sum sale count
                sales_count = d.get_sales().count()
                project.total_sale_count += sales_count
                total_sale_count += sales_count

                # sum totals
                total_amount += amount
                total_amount_notax += amount / tax

            # set avg_sale_count
            for p in projects:
                start_date = max(p.start_date, from_date)
                active_months = round((to_date - start_date).days/30) + 1
                p.avg_sale_count = p.total_sale_count / active_months if active_months > 0 else 0

            month_count = round((to_date-from_date).days/30) + 1
    else:
        form = SeasonForm()

    return render(request, 'Management/season_income.html', 
                              { 'start':from_date, 'end':to_date,
                                'projects':projects, 'filterForm':form,'total_amount':total_amount,'total_sale_count':total_sale_count,
                                'total_amount_notax':total_amount_notax,'avg_amount':total_amount/month_count,
                                'avg_amount_notax':total_amount_notax/month_count,'avg_sale_count':total_sale_count/month_count},
                              )

@permission_required('Management.demand_followup')
def demand_followup_list(request):
    ds = Demand.objects.none()
    total_amount, total_invoices, total_payments, total_diff_invoice, total_diff_invoice_payment = 0,0,0,0,0
    from_date, to_date, project = None, None, None
    
    if len(request.GET):
        form = ProjectSeasonForm(request.GET)
        if form.is_valid():
            project = form.cleaned_data['project']

            from_year, from_month = form.cleaned_data['from_year'], form.cleaned_data['from_month']
            to_year, to_month = form.cleaned_data['to_year'], form.cleaned_data['to_month']

            from_date = date(from_year, from_month, 1)
            to_date = date(to_year, to_month, 1)
            
            ds = Demand.objects \
                .range(from_year, from_month, to_year, to_month) \
                .filter(project = project) \
                .select_related('project') \
                .prefetch_related('reminders__statuses', 'invoices__offset','payments')

            set_demand_total_fields(ds, from_year, from_month, to_year, to_month)
            set_demand_diff_fields(ds)
            set_demand_is_fixed(ds)
            set_demand_invoice_payment_fields(ds)
            set_demand_open_reminders(ds)

            for d in ds:
                total_amount += d.total_amount
                total_invoices += d.total_amount_offset
                total_payments += d.payments_amount
                total_diff_invoice += d.diff_invoice
                total_diff_invoice_payment += d.diff_invoice_payment
    else:
        form = ProjectSeasonForm()
            
    context = { 
        'demands':ds, 
        'start':from_date, 'end':to_date,
        'project':project, 'filterForm':form,
        'total_amount':total_amount, 
        'total_invoices':total_invoices, 
        'total_payments':total_payments,
        'total_diff_invoice':total_diff_invoice, 
        'total_diff_invoice_payment':total_diff_invoice_payment}

    return render(request, 'Management/demand_followup_list.html', context)

@permission_required('Management.season_employeesalary')
def employeesalary_season_list(request):
    salaries = []
    from_date, to_date, employee_base = None,None,None
    
    total_attrs = ['neto', 'check_amount', 'loan_pay', 'bruto', 'refund']
    totals = dict([('total_' + attr, 0) for attr in total_attrs])
    
    if len(request.GET):
        form = EmployeeSeasonForm(request.GET)
        if form.is_valid():
            employee_base = form.cleaned_data['employee']

            from_year, from_month = form.cleaned_data['from_year'], form.cleaned_data['from_month']
            to_year, to_month = form.cleaned_data['to_year'], form.cleaned_data['to_month']

            from_date = date(from_year, from_month, 1)
            to_date = date(to_year, to_month, 1)

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
                salaries = NHEmployeeSalary.objects.nondeleted().range(from_year, from_month, to_year, to_month).filter(nhemployee__id = employee_base.id)
                
                # set the same employee instance for all salaries
                for s in salaries:
                    s.nhemployee = employee

                enrich_nh_employee_salaries(
                    salaries, 
                    {employee_base.id: employee},
                    from_year, from_month, to_year, to_month)
            
            if 'list' in request.GET:    
                # aggregate to get total values
                for salary in salaries:
                    for attr in total_attrs:
                        attr_value = getattr(salary, attr)
                        totals['total_' + attr] += attr_value or 0
            elif 'pdf' in request.GET:
                title = u'ריכוז שכר תקופתי לעובד - %s' % employee_base
                writer = EmployeeSalariesWriter(salaries, title, show_month=True, show_employee=False)
                return build_and_return_pdf(writer)
    else:
        form = EmployeeSeasonForm()
    
    context = { 'salaries':salaries, 'start':from_date, 'end':to_date, 'employee':employee_base, 'filterForm':form }
    context.update(totals)
    
    return render(request, 'Management/employeesalary_season_list.html', context, )

@permission_required('Management.season_salaryexpenses')
def employeesalary_season_expenses(request):
    salaries = []
    total_neto, total_check_amount, total_loan_pay, total_bruto, total_bruto_employer, total_refund = 0,0,0,0,0,0
    total_sale_count = 0
    from_date, to_date, employee_base = None,None,None
    
    if len(request.GET):
        form = EmployeeSeasonForm(request.GET)
        if form.is_valid():
            employee_base = form.cleaned_data['employee']
            from_date = date(form.cleaned_data['from_year'], form.cleaned_data['from_month'], 1)
            to_date = date(form.cleaned_data['to_year'], form.cleaned_data['to_month'], 1)

            employee = employee_base.derived

            if isinstance(employee, Employee):
                salaries = EmployeeSalary.objects.nondeleted() \
                    .range(from_date.year, from_date.month, to_date.year, to_date.month) \
                    .select_related('employee__employment_terms__hire_type') \
                    .filter(employee_id = employee_base.id)
                
                enrich_employee_salaries(
                    salaries, 
                    {employee_base.id: employee},
                    from_date.year, from_date.month, to_date.year, to_date.month)
                
                template = 'Management/employeesalary_season_expenses.html'
            elif isinstance(employee, NHEmployee):
                salaries = NHEmployeeSalary.objects.nondeleted().range(from_date.year, from_date.month, to_date.year, to_date.month).filter(nhemployee__id = employee_base.id)

                enrich_nh_employee_salaries(
                    salaries, 
                    {employee_base.id: employee},
                    from_date.year, from_date.month, to_date.year, to_date.month)

                template = 'Management/nhemployeesalary_season_expenses.html'

            for salary in salaries:
                total_neto += salary.neto or 0
                total_check_amount += salary.check_amount or 0
                total_loan_pay += salary.loan_pay or 0
                total_bruto += salary.bruto or 0
                total_bruto_employer += salary.bruto_employer_expense or 0
    else:
        template = 'Management/employeesalary_season_expenses.html'
        form = EmployeeSeasonForm()
        
    return render(request, template, 
                              { 'salaries':salaries, 'start':from_date, 'end':to_date,
                                'employee': employee_base, 'filterForm':form,
                                'total_neto':total_neto,'total_check_amount':total_check_amount,
                                'total_loan_pay':total_loan_pay,'total_bruto':total_bruto,'total_bruto_employer':total_bruto_employer},
                              )

@permission_required('Management.season_total_salaryexpenses')
def employeesalary_season_total_expenses(request):
    employees = []
    to_date, from_date = None, None
    
    if len(request.GET):
        form = DivisionTypeSeasonForm(request.GET)
        if form.is_valid():
            # extract form values
            division_type = form.cleaned_data['division_type']

            from_year, from_month = form.cleaned_data['from_year'], form.cleaned_data['from_month']
            to_year, to_month = form.cleaned_data['to_year'], form.cleaned_data['to_month']

            from_date = date(from_year, from_month, 1)
            to_date = date(to_year, to_month, 1)

            if division_type.id == DivisionType.Marketing:
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

                branch_id = division_to_branch[division_type.id]
                
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
            
            for employee_id, employee_salaries in itertools.groupby(salaries, lambda salary: salary.get_employee().id):
                # get the employee object
                employee = employee_by_id[employee_id]
                
                # evaluate and store the iterator
                employee_salaries_list = list(employee_salaries)

                for attr in attrs:
                    # extract 'attr' from each salary
                    attr_list = [getattr(salary, attr, 0) or 0 for salary in employee_salaries_list]
                    # sum 'attr' over employee_salaries
                    attr_sum = sum(attr_list)
                    # set 'total_' attribute on employee object
                    setattr(employee, 'total_' + attr, attr_sum)

    else:
        form = DivisionTypeSeasonForm()
            
    context = { 
        'employees':employees, 
        'start':from_date, 
        'end':to_date, 
        'filterForm':form 
    }

    return render(request, 'Management/employeesalary_season_total_expenses.html', context)

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
        
    return render(request, 'Management/sale_analysis.html', 
                              { 'filterForm':form, 'sale_months':data, 'include_clients':include_clients,
                               'total_sale_count':total_sale_count },
                              )
    
@permission_required('Management.global_profit_lost')
def global_profit_lost(request):
    data = []
    global_income, global_loss = 0,0
    if len(request.GET):
        form = GloablProfitLossForm(request.GET)
        if form.is_valid():
            divisions = form.cleaned_data['divisions']
            from_date = date(form.cleaned_data['from_year'], form.cleaned_data['from_month'], 1)
            to_date = date(form.cleaned_data['to_year'], form.cleaned_data['to_month'], 1)
            for division in divisions:
                total_income, total_loss = 0,0
                income_rows, loss_rows = [], []
                
                if division.id == DivisionType.Marketing:
                    demands = Demand.objects.range(from_date.year, from_date.month, to_date.year, to_date.month)
                    salaries = EmployeeSalary.objects.nondeleted().range(from_date.year, from_date.month, to_date.year, to_date.month)
                    
                    demands_amount, salaries_amount = 0,0
                    for demand in demands:
                        tax_val = Tax.objects.filter(date__lte=date(demand.year, demand.month,1)).latest().value / 100 + 1
                        demands_amount += demand.get_total_amount() / tax_val
                    for salary in salaries:
                        salaries_amount += salary.bruto or salary.check_amount or 0

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
                    
                    salaries = NHEmployeeSalary.objects.nondeleted().range(from_date.year, from_date.month, to_date.year, to_date.month).filter(nhbranch = nhbranch)
                    nhmonths = NHMonth.objects.range(from_date.year, from_date.month, to_date.year, to_date.month).filter(nhbranch = nhbranch)
                    
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
                incomes = Income.objects.range(from_date.year, from_date.month, to_date.year, to_date.month).filter(division_type = division)
                checks = PaymentCheck.objects.filter(issue_date__range = (from_date,to_date), division_type = division)
                
                incomes_amount = 0
                for income in incomes:
                    incomes_amount += income.invoice and income.invoice.amount or 0
                    
                total_income += incomes_amount
                
                income_rows.extend([{'name':u'הכנסות אחרות','amount':incomes_amount,
                                     'details_link':'/incomes/?division_type=%s;from_year=%s;from_month=%s;to_year=%s;to_month=%s' 
                                     % (division.id, from_date.year, from_date.month, to_date.year, to_date.month)},
                                     {'name':u'סה"כ','amount':total_income}])
                
                global_income += total_income
                
                expenses_amount = 0
                for check in checks:
                    expenses_amount += check.amount
                    
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

    return render(request, 'Management/global_profit_loss.html', context)
    
#################################################### ACTIVITY VIEWS ##########################################

def object_edit_core(request, form_class, instance,
                     template_name = 'Management/object_edit.html', 
                     before_save = None, 
                     after_save = None):
    
    if request.method == 'POST':
        form = form_class(request.POST, instance = instance)
        if form.is_valid():
            if before_save:
                before_save(form, instance)
            form.save()
            if after_save:
                after_save(form, instance)
    else:
        form = form_class(instance = instance)
        
    return render(request, template_name, {'form':form })


@permission_required('Management.add_activity')
def activity_add(request):
    activity = Activity()
    return object_edit_core(request, ActivityForm, activity, 'Management/activity_edit.html')
    
class ActivityDetailView(LoginRequiredMixin, DetailView):
    model = Activity
    template_name = 'Management/activity_detail.html'

class ActivityUpdate(PermissionRequiredMixin, UpdateView):
    model = Activity
    form_class = 'ActivityForm'
    success_url = 'edit'
    template_name = 'Management/activity_edit.html'
    permission_required = 'Management.change_activity'

@permission_required('Management.add_citycallers')
def activitybase_citycallers_add(request, activitybase_id):
    activity_base = ActivityBase.objects.get(pk = activitybase_id)
    return citycallers_core(request, CityCallers(activity_base = activity_base))

@permission_required('Management.change_citycallers')
def citycallers_edit(request, object_id):
    obj = CityCallers.objects.get(pk = object_id)
    return citycallers_core(request, obj)

def citycallers_core(request, instance):
    if request.method == 'POST':
        form = CityCallersForm(request.POST, instance = instance)
        if form.is_valid():
            new_city_name = form.cleaned_data['new_city']
            if new_city_name:
                new_city = City(name = new_city_name)
                new_city.save()
                form.cleaned_data['city'] = new_city
            form.save()
            if 'addanother' in request.POST:
                return HttpResponseRedirect(reverse(citycallers_add))
    else:
        form = CityCallersForm(instance = instance)
    
    return render(request, 'Management/object_edit.html', {'form':form })
    
@permission_required('Management.add_mediareferrals')
def activitybase_mediareferrals_add(request, activitybase_id):
    activity_base = ActivityBase.objects.get(pk = activitybase_id)
    return mediareferrals_core(request, MediaReferrals(activity_base = activity_base))

@permission_required('Management.change_mediareferrals')
def mediareferrals_edit(request, object_id):
    obj = MediaReferrals.objects.get(pk = object_id)
    return mediareferrals_core(request, obj)

def mediareferrals_core(request, instance):
    if request.method == 'POST':
        form = MediaReferralsForm(request.POST, instance = instance)
        if form.is_valid():
            new_media_name = form.cleaned_data['new_media']
            if new_media_name:
                new_media = Media(name = new_media_name)
                new_media.save()
                form.cleaned_data['media'] = new_media
            form.save()
            if 'addanother' in request.POST:
                return HttpResponseRedirect(reverse(mediareferrals_add))
    else:
        form = MediaReferralsForm(instance = instance)
    
    return render(request, 'Management/object_edit.html', {'form':form })
    
@permission_required('Management.add_event')
def activitybase_event_add(request, activitybase_id):
    activity_base = ActivityBase.objects.get(pk = activitybase_id)
    return event_core(request, Event(activity_base = activity_base))
    
@permission_required('Management.change_event')
def event_edit(request, object_id):
    obj = Event.objects.get(pk = object_id)
    return event_core(request, obj)

@permission_required('Management.add_saleprocess')
def activitybase_saleprocess_add(request, activitybase_id):
    activity_base = ActivityBase.objects.get(pk = activitybase_id)
    return saleprocess_core(request, SaleProcess(activity_base = activity_base))
    
@permission_required('Management.change_saleprocess')
def saleprocess_edit(request, object_id):
    obj = SaleProcess.objects.get(pk = object_id)
    return saleprocess_core(request, obj)

@permission_required('Management.add_priceoffer')
def activitybase_priceoffer_add(request, activitybase_id):
    activity_base = ActivityBase.objects.get(pk = activitybase_id)
    return priceoffer_core(request, PriceOffer(activity_base = activity_base))

@permission_required('Management.change_priceoffer')
def priceoffer_edit(request, object_id):
    obj = PriceOffer.objects.get(pk = object_id)
    return priceoffer_core(request, obj)

def event_core(request, instance):
    return object_edit_core(request, EventForm, instance)
    
def saleprocess_core(request, instance):
    return object_edit_core(request, SaleProcessForm, instance)
    
def priceoffer_core(request, instance):
    return object_edit_core(request, PriceOfferForm, instance)
