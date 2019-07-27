from datetime import date

from django.shortcuts import render

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin

from django.views.generic.edit import DeleteView

from .models import PaymentCheck, EmployeeCheck, ExpenseType, SupplierType
from .forms import CheckForm, CheckFilterForm, EmployeeCheckForm, EmployeeCheckFilterForm

from Management.models import DivisionType, Loan
from Management.forms import AccountForm

# Create your views here.

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

    return render(request, 'Checks/check_list.html', context)

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
        
    return render(request, 'Checks/check_edit.html', 
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
        
    return render(request, 'Checks/check_edit.html', 
                              { 'accountForm':accountForm, 'form':form,'title':u"הזנת צ'ק אחר" },
                              )

class PaymentCheckDelete(PermissionRequiredMixin, DeleteView):
    model = PaymentCheck
    success_url = '/checks'
    template_name = 'Management/object_confirm_delete.html'
    permission_required = 'Management.delete_paymentcheck'

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

    return render(request, 'Checks/employeecheck_list.html', context)

def apply_employee_check(ec):
    if ec.purpose_type.id == PurposeType.AdvancePayment:
        # TODO FIX - AdvancePayment models was probably deleted ...
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
