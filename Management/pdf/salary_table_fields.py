

from reportlab.platypus import Paragraph
from pyfribidi import log2vis

import Management.models as models
from Management.templatetags.management_extras import commaise
from Management.pdf.styles import *
from Management.pdf.table_fields import TableField

from django.utils.translation import ugettext

class EmployeeHireTypeField(TableField):
    def __init__(self):
        return super(EmployeeHireTypeField, self).__init__(ugettext('hire_type'),35)
    def format(self, item):
        '''
        item is of type EmployeeBase
        '''
        terms = item.employment_terms
        return unicode(terms.hire_type)
    class Meta:
        models = (models.EmployeeBase,)
        
class EmployeeSalarySalesField(TableField):
    def __init__(self):
        return super(EmployeeSalarySalesField, self).__init__(ugettext('sale_count'),35)
    def format(self, item):
        '''
        item is of type EmployeeSalary
        '''
        val = ''
        sales = item.sales
        for project, sales in sales:
            val += log2vis("%s - %s" % (project, len(sales))) + '<br/>'
        return val
    class Meta:
        models = (models.EmployeeSalary,)
        
class EmployeeSalaryNetoField(TableField):
    def __init__(self):
        return super(EmployeeSalaryNetoField, self).__init__(ugettext('neto_amount'),35, is_commaised = True)
    def format(self, item):
        return item.neto
    class Meta:
        models = (models.EmployeeSalaryBase)
    
class EmployeeSalaryLoanPayField(TableField):
    def __init__(self):
        return super(EmployeeSalaryLoanPayField, self).__init__(ugettext('loan_pay'),35, is_commaised = True)
    def format(self, item):
        return item.loan_pay
    class Meta:
        models = (models.EmployeeSalaryBase)
    
class EmployeeSalaryCheckAmountField(TableField):
    def __init__(self):
        return super(EmployeeSalaryLoanPayField, self).__init__(ugettext('check_amount'),35, is_commaised = True)
    def format(self, item):
        return item.check_amount
    class Meta:
        models = (models.EmployeeSalaryBase)

class EmployeeSalaryBrutoWithEmployerField(TableField):
    def __init__(self):
        return super(EmployeeSalaryBrutoWithEmployerField, self).__init__(ugettext('bruto_with_employer'),35, is_commaised = True)
    def format(self, item):
        return ''
    class Meta:
        models = (models.EmployeeSalaryBase)

class EmployeeSalaryBrutoField(TableField):
    def __init__(self):
        return super(EmployeeSalaryBrutoField, self).__init__(ugettext('bruto'),35, is_commaised = True)
    def format(self, item):
        return item.bruto
    class Meta:
        models = (models.EmployeeSalaryBase)

class SalaryExpensesIncomeTaxField(TableField):
    def __init__(self):
        return super(SalaryExpensesIncomeTaxField, self).__init__(ugettext('income_tax'),35, is_commaised = True)    
    def format(self, item):
        return item.income_tax
    class Meta:
        models = (models.SalaryExpenses)

class SalaryExpensesNationalInsuranceField(TableField):
    def __init__(self):
        return super(SalaryExpensesNationalInsuranceField, self).__init__(ugettext('national_insurance'),35, is_commaised = True)
    def format(self, item):
        return item.national_insurance
    class Meta:
        models = (models.SalaryExpenses)

class SalaryExpensesHealthField(TableField):
    def __init__(self):
        return super(SalaryExpensesHealthField, self).__init__(ugettext('health'),35, is_commaised = True)
    def format(self, item):
        return item.health
    class Meta:
        models = (models.SalaryExpenses)

class SalaryExpensesPensionInsuranceField(TableField):
    def __init__(self):
        return super(SalaryExpensesPensionInsuranceField, self).__init__(ugettext('pension_insurance'),35, is_commaised = True)
    def format(self, item):
        return item.pension_insurance
    class Meta:
        models = (models.SalaryExpenses)

class SalaryExpensesVacationField(TableField):
    def __init__(self):
        return super(SalaryExpensesVacationField, self).__init__(ugettext('vacation'),35, is_commaised = True)
    def format(self, item):
        return item.vacation
    class Meta:
        models = (models.SalaryExpenses)

class SalaryExpensesConvalescencePayField(TableField):
    def __init__(self):
        return super(SalaryExpensesConvalescencePayField, self).__init__(ugettext('convalescence_pay'),35, is_commaised = True)
    def format(self, item):
        return item.convalescence_pay
    class Meta:
        models = (models.SalaryExpenses)

class SalaryExpensesEmployerNationalInsuranceField(TableField):
    def __init__(self):
        return super(SalaryExpensesEmployerNationalInsuranceField, self).__init__(ugettext('employer_national_insurance'),35, is_commaised = True)
    def format(self, item):
        return item.employer_national_insurance
    class Meta:
        models = (models.SalaryExpenses)

class SalaryExpensesEmployerBenefitField(TableField):
    def __init__(self):
        return super(SalaryExpensesEmployerBenefitField, self).__init__(ugettext('employer_benefit'),35, is_commaised = True)
    def format(self, item):
        return item.employer_benefit
    class Meta:
        models = (models.SalaryExpenses)

class SalaryExpensesCompensationAllocationField(TableField):
    def __init__(self):
        return super(SalaryExpensesCompensationAllocationField, self).__init__(ugettext('compensation_allocation'),35, is_commaised = True)
    def format(self, item):
        return item.compensation_allocation
    class Meta:
        models = (models.SalaryExpenses)