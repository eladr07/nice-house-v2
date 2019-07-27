from django.forms import ModelForm, ModelChoiceField, CharField, ChoiceField, IntegerField, ValidationError
from django.forms import TextInput, Textarea

from django.utils.translation import gettext

from .models import ExpenseType, SupplierType, EmployeeCheck, PaymentCheck

from Management.models import DivisionType, EmployeeBase, Invoice
from Management.forms import SeasonForm

class CheckFilterForm(SeasonForm):
    division_type = ModelChoiceField(queryset = DivisionType.objects.all(), label=gettext('division_type'), 
                                           required=False)
    expense_type = ModelChoiceField(queryset = ExpenseType.objects.all(), label=gettext('expense_type'), 
                                          required=False)
    supplier_type = ModelChoiceField(queryset = SupplierType.objects.all(), label=gettext('supplier_type'), 
                                           required=False)

class EmployeeCheckFilterForm(SeasonForm):
    employee = ModelChoiceField(queryset = EmployeeBase.objects.all(), label=gettext('employee'), required=False)
    division_type = ModelChoiceField(queryset = DivisionType.objects.all(), label=gettext('division_type'), 
                                           required=False)
    expense_type = ModelChoiceField(queryset = ExpenseType.objects.all(), label=gettext('expense_type'), 
                                          required=False)

class CheckForm(ModelForm):
    invoice_num = IntegerField(label = gettext('invoice_num'), help_text=u'החשבונית חייבת להיות מוזנת במערכת',
                                     required=False)
    new_division_type = CharField(label = gettext('new_division_type'), max_length = 20, required=False)
    new_expense_type = CharField(label = gettext('new_expense_type'), max_length = 20, required=False)
    new_supplier_type = CharField(label = gettext('new_supplier_type'), max_length = 20, required=False)

    def clean_invoice_num(self):
        invoice_num = self.cleaned_data['invoice_num']
        query = Invoice.objects.filter(num = invoice_num)
        if query.count()==0:
            raise ValidationError(u"אין חשבונית עם מס' זה")
        return invoice_num
    def save(self, *args, **kw):
        invoice_num = self.cleaned_data['invoice_num']
        invoice = Invoice.objects.get(num = invoice_num)
        self.instance.invoice = invoice
        return ModelForm.save(self,*args,**kw)
    def __init__(self, *args, **kw):
        ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['issue_date'].widget.attrs = {'class':'vDateField'}
        self.fields['pay_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = PaymentCheck
        fields = ['division_type','new_division_type','expense_type','new_expense_type',
                  'supplier_type', 'new_supplier_type','invoice_num','type','issue_date','pay_date','num','amount',
                  'tax_deduction_source','order_verifier','payment_verifier','remarks']

class EmployeeCheckForm(ModelForm):
    invoice_num = IntegerField(label = gettext('invoice_num'), help_text=u'החשבונית חייבת להיות מוזנת במערכת',
                                     required=False)
    new_division_type = CharField(label = gettext('new_division_type'), max_length = 20, required=False)
    new_expense_type = CharField(label = gettext('new_expense_type'), max_length = 20, required=False)
    
    def clean_invoice_num(self):
        invoice_num = self.cleaned_data['invoice_num']
        query = Invoice.objects.filter(num = invoice_num)
        if query.count()==0:
            raise ValidationError(u"אין חשבונית עם מס' זה")
        return invoice_num
    def save(self, *args, **kw):
        invoice_num = self.cleaned_data['invoice_num']
        invoice = Invoice.objects.get(num = invoice_num)
        self.instance.invoice = invoice
        return ModelForm.save(self,*args,**kw)
    def __init__(self, *args, **kw):
        ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['issue_date'].widget.attrs = {'class':'vDateField'}
        self.fields['pay_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = EmployeeCheck
        fields = ['division_type','new_division_type','employee','year','month','expense_type','new_expense_type','purpose_type',
                  'invoice_num','type','amount','num','issue_date','pay_date','remarks']
