from django.db import models

from django.utils.translation import gettext

from Management.models import DivisionType, Account, Invoice, EmployeeBase, Employee, NHEmployee, EmployeeSalary, NHEmployeeSalary
from Management.common import get_month_choices, get_year_choices

# Create your models here.

class CheckBaseType(models.Model):
    WithInvoice, NoInvoice = 1, 2
    
    name = models.CharField(gettext('name'), max_length=20, unique=True)

    def __str__(self):
        return str(self.name) 

class CheckBase(models.Model):
    num = models.IntegerField(gettext('check_num'), unique=True)
    issue_date = models.DateField(gettext('issue_date'))
    pay_date = models.DateField(gettext('payment_date'))
    division_type = models.ForeignKey(DivisionType, on_delete=models.PROTECT, verbose_name=gettext('division_type'), blank=True)
    expense_type = models.ForeignKey('ExpenseType', on_delete=models.PROTECT, verbose_name=gettext('expense_type'), blank=True)
    type = models.ForeignKey('CheckBaseType', on_delete=models.PROTECT, verbose_name=gettext('invoice'))
    amount = models.IntegerField(gettext('amount'))
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, editable=False, null=True)
    remarks = models.TextField(gettext('remarks'), blank=True)

    def diff_amount_invoice(self):
        if self.invoice == None: return None
        return self.amount - self.invoice.amount

    class Meta:
        ordering = ['division_type','expense_type']

class EmployeeCheck(CheckBase):
    employee = models.ForeignKey(EmployeeBase, on_delete=models.PROTECT, related_name='checks', verbose_name=gettext('employee'))
    purpose_type = models.ForeignKey('PurposeType', on_delete=models.PROTECT, verbose_name=gettext('purpose_type'))
    month = models.PositiveSmallIntegerField(gettext('month'), choices=get_month_choices())
    year = models.PositiveSmallIntegerField(gettext('year'), choices=get_year_choices())

    def salary(self):
        if isinstance(self.employee.derived, Employee):
            query = EmployeeSalary.objects.filter(year = self.year, month = self.month, employee = self.employee.derived)
        elif isinstance(self.employee.derived, NHEmployee):
            query = NHEmployeeSalary.objects.filter(year = self.year, month = self.month, nhemployee = self.employee.derived)
        
        if query.count() == 0: 
            return None
        if query.count() > 1: 
            raise InvalidOperation % 'more than 1 salary for employee for the month'
        
        return query[0]
    def diff_amount_salary(self):
        salary = self.salary()
        if salary:
            return self.amount - salary
        return None
    def get_absolute_url(self):
        return '/employeechecks/%s' % self.id 

class PaymentCheck(CheckBase):
    supplier_type = models.ForeignKey('SupplierType', on_delete=models.PROTECT, verbose_name=gettext('supplier_type'))
    account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, editable=False)
    tax_deduction_source = models.IntegerField(gettext('tax_deduction_source'),null=True, blank=True)
    order_verifier = models.CharField(gettext('order_verifier'),max_length=30)
    payment_verifier = models.CharField(gettext('payment_verifier'),max_length=30)
    def get_absolute_url(self):
        return '/checks/%s' % self.id 

class SupplierType(models.Model):
    name = models.CharField(gettext('name'), max_length=20, unique=True)
    def __str__(self):
        return str(self.name)

class ExpenseType(models.Model):
    name = models.CharField(gettext('name'), max_length=20, unique=True)
    def __str__(self):
        return str(self.name)

class PurposeType(models.Model):
    Salary, AdvancePayment, Loan = 1,2,3
    name = models.CharField(gettext('name'), max_length=20, unique=True)
    def __str__(self):
        return str(self.name)