
from sys import maxsize
from datetime import datetime, date

from django.core.exceptions import ValidationError
from django.utils.translation import gettext
import django.forms as forms
from django.forms.models import modelform_factory

import reversion

import Management.common as common
from Management.models import *

class SeasonForm(forms.Form):
    from_year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                             label = gettext('from_year'), initial = common.current_month().year)
    from_month = forms.ChoiceField(choices=((i,i) for i in range(1,13)), label = gettext('from_month'),
                              initial = common.current_month().month)
    to_year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                             label = gettext('to_year'), initial = common.current_month().year)
    to_month = forms.ChoiceField(choices=((i,i) for i in range(1,13)), label = gettext('to_month'),
                              initial = common.current_month().month)
    def clean_from_year(self):
        return int(self.cleaned_data['from_year'])
    def clean_from_month(self):
        return int(self.cleaned_data['from_month'])
    def clean_to_year(self):
        return int(self.cleaned_data['to_year'])
    def clean_to_month(self):
        return int(self.cleaned_data['to_month'])

class MonthForm(forms.Form):
    year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                             label = gettext('year'), initial = datetime.now().year)
    month = forms.ChoiceField(choices=((i,i) for i in range(1,13)), label = gettext('month'),
                              initial = common.current_month().month)  
    def clean_year(self):
        return int(self.cleaned_data['year'])
    def clean_month(self):
        return int(self.cleaned_data['month'])

class RevisionExtForm(forms.ModelForm):
    date = forms.DateTimeField(label = gettext('modification_date'), help_text = gettext('modification_date_help'))
    
    def __init__(self, *args, **kw):
        super(RevisionExtForm, self).__init__(*args,**kw)
        self.fields['date'].widget.attrs = {'class':'vDateField'}   
    def save(self, *args, **kw):
        reversion.add_meta(RevisionExt, date = self.cleaned_data['date'])
        return super(RevisionExtForm, self).save(*args, **kw)
    
    class Meta:
        pass
        
CVarForm = modelform_factory(CVar, RevisionExtForm, fields=('date','is_retro'))

CVarPrecentageForm = modelform_factory(CVarPrecentage, RevisionExtForm, fields=('date','is_retro','start_retro'))

CByPriceForm = modelform_factory(CByPrice, RevisionExtForm, fields=('date',))

CZilberForm = modelform_factory(CZilber, RevisionExtForm, fields=('date','base','b_discount','b_sale_rate','b_sale_rate_max','base_madad','third_start'))

CVarPrecentageFixedForm = modelform_factory(CVarPrecentageFixed, RevisionExtForm, fields=('date','is_retro','first_count','first_precentage','step','last_count','last_precentage'))

BDiscountSaveForm = modelform_factory(BDiscountSave, RevisionExtForm, fields=('date','precentage_bonus','max_for_bonus'))

BDiscountSavePrecentageForm = modelform_factory(BDiscountSavePrecentage, RevisionExtForm, fields=('date','precentage_bonus','max_for_bonus'))

BHouseTypeForm = modelform_factory(BHouseType, RevisionExtForm, fields=('date',))

BSaleRateForm = modelform_factory(BSaleRate, RevisionExtForm, fields=('date',))

LoanPayForm = modelform_factory(LoanPay, fields=('employee','month','year','amount','deduct_from_salary','remarks'))
        
SalaryExpensesForm = modelform_factory(SalaryExpenses, exclude=('approved_date',))

AccountForm = modelform_factory(Account, fields=('num','bank','branch','branch_num','payee'))

DemandRemarksForm = modelform_factory(Demand, fields = ('remarks',))

DemandSaleCountForm = modelform_factory(Demand, fields = ('sale_count',))

EmployeeSalaryRemarksForm = modelform_factory(EmployeeSalary, fields = ('employee', 'remarks'))

EmployeeSalaryRefundForm = modelform_factory(EmployeeSalary, fields = ('employee', 'refund','refund_type'))

NHEmployeeSalaryRemarksForm = modelform_factory(NHEmployeeSalary, fields = ('nhemployee', 'remarks'))

NHEmployeeSalaryRefundForm = modelform_factory(NHEmployeeSalary, fields = ('nhemployee', 'refund','refund_type'))

NHCommissionForm = modelform_factory(NHCommission, RevisionExtForm, 
    fields=('date',
            'nhbranch','nhemployee','name',
            'left_filter','left_income_type','operator','left_amount',
            'right_filter','right_income_type','right_amount','right_amount_type'))

SalePriceModForm = modelform_factory(SalePriceMod, exclude=('sale','date'))

SaleHouseModForm = modelform_factory(SaleHouseMod, exclude=('sale','date'))

SalePreForm = modelform_factory(SalePre, exclude=('sale','date'))

SaleRejectForm = modelform_factory(SaleReject, exclude=('sale','date'))

class ContactForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'3'})
    class Meta:
        model = Contact
        fields=('first_name','last_name','cell_phone','mail','address','role',
                'phone','fax','company','remarks')

class ExistContactForm(forms.Form):
    contact = forms.ModelChoiceField(queryset=Contact.objects.all())

class ProjectForm(forms.ModelForm):    
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'5'})
        self.fields['start_date'].widget = forms.TextInput({'class':'vDateField'})
        self.fields['end_date'].widget = forms.TextInput({'class':'vDateField'})

    class Meta:
        model = Project
        exclude=('details','demand_contact','payment_contact','contacts','reminders')
    
    field_order = ['initiator','name','city','hood','office_address','phone','cell_phone',
        'fax','mail','start_date']

class ProjectDetailsForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'3'})
    class Meta:
        model = ProjectDetails
        fields=('architect','houses_num','buildings_num','bank','url','remarks','building_types')

class BuildingForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'3'})
    class Meta:
        model = Building
        exclude=('pricelist','is_deleted')

class PricelistForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self, *args, **kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'5'})
        self.fields['settle_date'].widget = forms.TextInput({'class':'vDateField'})
    class Meta:
        model = Pricelist
        fields=('include_tax','include_lawyer','include_parking','include_storage','include_registration','include_guarantee',
                'settle_date','allowed_discount','is_permit','permit_date','lawyer_fee',
                'register_amount','guarantee_amount','storage_cost','remarks')

class PricelistUpdateForm(forms.Form):
    Add, Multiply, Precentage = 1,2,3
    
    pricelisttype = forms.ModelChoiceField(queryset = PricelistType.objects.all(), 
                                           required=False, label = gettext('pricelisttype'))
    all_pricelists = forms.BooleanField(required=False, label=gettext('all_pricelists'))
    date = forms.DateField(label=gettext('date'))
    action = forms.ChoiceField(label=gettext('action'), choices = (
                                                                    (Add, gettext('add')),
                                                                    (Multiply, gettext('multiply')),
                                                                    (Precentage, gettext('precentage'))
                                                                    ))
    value = forms.FloatField(label=gettext('value'), required=False)
    def clean_action(self):
        return int(self.cleaned_data['action'])
    def __init__(self, *args, **kw):
        forms.Form.__init__(self, *args, **kw)
        self.fields['date'].widget = forms.TextInput({'class':'vDateField'})

class ParkingForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'3'})
        if self.instance.id > 0:
            self.fields['house'].queryset = self.instance.building.houses.all()
    class Meta:
        model = Parking
        fields=('building','house','num','type','remarks')
        
class StorageForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'3'})
        if self.instance.id > 0:
            self.fields['house'].queryset = self.instance.building.houses.all()
    class Meta:
        model = Storage
        fields=('building','house','num','size','remarks')

class HouseForm(forms.ModelForm):
    parking1 = forms.ModelChoiceField(queryset=Parking.objects.all(), required=False, label = gettext('parking') + ' 1')
    parking2 = forms.ModelChoiceField(queryset=Parking.objects.all(), required=False, label = gettext('parking') + ' 2')
    parking3 = forms.ModelChoiceField(queryset=Parking.objects.all(), required=False, label = gettext('parking') + ' 3')
    storage1 = forms.ModelChoiceField(queryset=Storage.objects.all(), required=False, label = gettext('storage') + ' 1')
    storage2 = forms.ModelChoiceField(queryset=Storage.objects.all(), required=False, label = gettext('storage') + ' 2')
    price = forms.IntegerField(label=gettext('price'), required=False)
    price_date = forms.DateField(label = gettext('price_date'), required = False)
    
    def save(self, price_type_id, *args, **kw):
        h = forms.ModelForm.save(self, *args, **kw)
        
        for f in ['parking1','parking2','parking3']:
            if self.cleaned_data[f]:
                h.parkings.add(self.cleaned_data[f])
        for f in ['storage1','storage2']:
            if self.cleaned_data[f]:
                h.storages.add(self.cleaned_data[f])

        price, price_date = self.cleaned_data['price'], self.cleaned_data['price_date']
        
        versions = self.instance.versions.filter(type__id = price_type_id)
        
        if price and (versions.count() == 0 or versions.latest().price != price):
            pricelist_type = PricelistType.objects.get(pk=price_type_id)
            house_version = HouseVersion(type = pricelist_type, price = price, date = price_date)
            # save the object first
            house_version.save()
            # and add it to the House versions
            self.instance.versions.add(house_version)

        return h
    
    def clean(self):
        cleaned_data = self.cleaned_data
        price, price_date = cleaned_data.get('price'), cleaned_data.get('price_date')
        if price and not price_date:
            self._errors['price_date'] = gettext('mandatory_field')
            del cleaned_data['price_date']
        if price_date and not price:
            self._errors['price'] = gettext('mandatory_field')
            del cleaned_data['price']
        return cleaned_data
    
    def __init__(self, price_type_id, *args, **kw):
        super(HouseForm, self).__init__(*args, **kw)
        self.fields['price_date'].widget.attrs = {'class':'vDateField'}
        
        if not self.instance.id:
            return
        i=1
        for p in self.instance.parkings.all():
            self.initial['parking%s' % i] = p.id
            i=i+1
        i=1
        for s in self.instance.storages.all():
            self.initial['storage%s' % i] = s.id
            i=i+1
        vs = self.instance.versions.filter(type__id = price_type_id)
        if vs.count() > 0:
            latest_version = vs.latest()
            self.initial['price'] = latest_version.price
            self.initial['price_date'] = latest_version.date
    class Meta:
        model = House
        exclude=('building',)

class EmployeeForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)

        self.history_trans_update = []
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['birth_date'].widget.attrs = {'class':'vDateField'}
        self.fields['work_start'].widget.attrs = {'class':'vDateField'}
        self.fields['work_end'].widget.attrs = {'class':'vDateField'}

        if self.instance.id:
            self.fields['main_project'].queryset = self.instance.projects

        transactions = TransactionUpdateHistory.objects.filter(transaction_id = self.instance.id, transaction_type = 0)

        for value in transactions :
            field_value = value.field_value
            field_name  = value.field_name

            try :
                field_value = commaise( int( field_value ) ) + ' ש"ח'
            except :
                if field_name == 'tax_deduction_source_precentage' :
                    field_value = field_value + ' %'

            self.history_trans_update.append( [ gettext( field_name ), field_value, str( value.timestamp ).split(' ')[0] ] )
    class Meta:
        model = Employee
        exclude=('reminders','account','employment_terms','projects')

class NHEmployeeForm(forms.ModelForm):
    nhbranch = forms.ModelChoiceField(NHBranch.objects.all(), empty_label=gettext('choose_branch'), label = gettext('nhbranch'))
    
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['birth_date'].widget.attrs = {'class':'vDateField'}
        self.fields['work_start'].widget.attrs = {'class':'vDateField'}
        self.fields['work_end'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = NHEmployee
        exclude=('reminders','account','employment_terms')
      
class ProjectCommissionForm(RevisionExtForm):
    def __init__(self, *args, **kw):
        super(ProjectCommissionForm, self).__init__(*args,**kw)
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'5'}
    class Meta:
        model = ProjectCommission
        exclude=('project','c_var_precentage','c_var_precentage_fixed','c_zilber','b_discount_save_precentage')

class EmployeeAddProjectForm(forms.Form):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), label=gettext('employee'))
    project = forms.ModelChoiceField(queryset=Project.objects.active(), label=gettext('project'))
    start_date = forms.DateField(label=gettext('start date'), input_formats=['%d-%m-%Y'])
    def __init__(self, *args, **kw):
        super(EmployeeAddProjectForm, self).__init__(*args, **kw)
        self.fields['start_date'].widget.attrs = {'class':'vDateFormatField'}

class EmployeeRemoveProjectForm(forms.Form):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), label=gettext('employee'))
    project = forms.ModelChoiceField(queryset=Project.objects.all(), label=gettext('project'))
    end_date = forms.DateField(label=gettext('end_date'), input_formats=['%d-%m-%Y'])
    def __init__(self, *args, **kw):
        super(EmployeeRemoveProjectForm, self).__init__(*args, **kw)
        self.fields['end_date'].widget.attrs = {'class':'vDateFormatField'}

class CPriceAmountForm(forms.ModelForm):
    def clean_price(self):
        price = self.cleaned_data['price']
        if not price:
            price = maxsize
        return price
    class Meta:
        model = CPriceAmount
        exclude=('c_by_price',)
 
class SignupForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset = Project.objects.all(), label=gettext('project'))
    building = forms.ModelChoiceField(queryset = Building.objects.all(), label=gettext('building'))
    
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['clients'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['clients_phone'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['clients_address'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['date'].widget.attrs = {'class':'vDateField'}
        self.fields['sale_date'].widget.attrs = {'class':'vDateField'}
    
    class Meta:
        model = Signup 
        exclude=('cancel',)
    
    field_order=['id','project','building','house','clients','clients_phone','clients_address',
        'date','sale_date','price','include_lawyer','remarks']

class SignupCancelForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['reason'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model =SignupCancel
        fields=('date','was_signed','was_fee','reason')

class DemandDiffForm(forms.ModelForm):
    add_type = forms.ChoiceField(choices=((1,u'תוספת'),
                                          (2,'קיזוז')), 
                                          label=gettext('add_type'))
    def clean(self):
        add_type, amount = self.cleaned_data['add_type'], self.cleaned_data['amount']
        self.cleaned_data['amount'] = int(add_type) == 2 and (amount * -1) or amount 
        return self.cleaned_data
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self, *args, **kw)
        if self.instance.id:
            self.fields['add_type'].initial = self.instance.amount >= 0 and 1 or 2
    class Meta:
        model = DemandDiff
        exclude=('demand',)
                 
class SaleForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset = Project.objects.all(), label=gettext('project'))
    building = forms.ModelChoiceField(queryset = Building.objects.all(), label=gettext('building'))
    joined_sale = forms.BooleanField(label = gettext('joined sale'), required = False)
    signup_date = forms.DateField(label=gettext('signup_date'), required=False)
    
    def clean_house(self):
        house = self.cleaned_data['house']
        if self.instance.id:
            s = house.get_sale()
            if s and s != self.instance:
                raise forms.ValidationError(u"כבר קיימת מכירה לדירה זו")
        else:
            if house.get_sale():
                raise forms.ValidationError(u"כבר קיימת מכירה לדירה זו")
        return house
    def clean(self):
        cleaned_data = self.cleaned_data
        if cleaned_data['joined_sale']: 
            cleaned_data['employee'] = None
        return cleaned_data
    def save(self, *args, **kw):
        cleaned_data = self.cleaned_data
        house, discount, allowed_discount, price, signup_date = \
            (cleaned_data['house'], cleaned_data['discount'], cleaned_data['allowed_discount'], cleaned_data['price'], 
             cleaned_data['signup_date'])
        
        # checks if entered a allowed discount but not discount -> will fill discount automatically
        if allowed_discount and not discount:
            max_p = house.versions.company().latest().price
            cleaned_data['discount'] = 100 - (100 / float(max_p) * price)
            cleaned_data['contract_num'] = 0
        
        # fill Signup automatically. it is temp fix until signup_date field will be removed.
        if signup_date != None:
            signup = house.get_signup() or Signup()
            signup.date = signup_date
            for attr in ['house','employee','clients','clients_phone','sale_date','price','price_include_lawyer']:
                setattr(signup, attr, cleaned_data[attr])
            signup.save()
        
        return forms.ModelForm.save(self, *args, **kw)
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'3'})
        self.fields['clients'].widget = forms.Textarea({'cols':'20', 'rows':'3'})
        self.fields['sale_date'].widget = forms.TextInput({'class':'vDateField'})
        self.fields['signup_date'].widget = forms.TextInput({'class':'vDateField'})
        if self.instance.id:
            self.fields['project'].initial = self.instance.house.building.project_id
            self.fields['building'].initial = self.instance.house.building_id
            self.fields['house'].initial = self.instance.house_id
            self.fields['building'].queryset = self.instance.house.building.project.buildings.all()
            self.fields['house'].queryset = self.instance.house.building.houses.all()
            # fill signup_date field.
            signup= self.instance.house.get_signup()
            if signup:
                self.fields['signup_date'].initial = signup.date
            if not self.instance.employee:
                self.fields['joined_sale'].initial = True
    class Meta:
        model = Sale
        exclude=('demand','employee_pay_month','employee_pay_year','contractor_pay_month','contractor_pay_year')

class EmployeeEndForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['work_end'].widget = forms.TextInput({'class':'vDateField'})
    class Meta:
        model = EmployeeBase
        fields = ('work_end',)
        
class ProjectEndForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['end_date'].widget = forms.TextInput({'class':'vDateField'})
    class Meta:
        model = Project
        fields = ('end_date',)
        
class DemandForm(forms.ModelForm):    
    remarks = forms.CharField(widget=forms.Textarea(attrs={'cols':'20', 'rows':'3'}), required = False ,
                              label=gettext('remarks'))
    def save(self, *args, **kw):
        if self.instance.id:
            i=forms.ModelForm.save(self, *args, **kw)
        else:
            i=forms.ModelForm.save(self, *args, **kw)
            self.instance.feed()
        return i
    class Meta:
        model = Demand
        fields=('project','month','year','sale_count','remarks')

class DemandInvoiceForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset = Project.objects.all(), label = gettext('project'))
    year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                             label = gettext('year'), initial = datetime.now().year)
    month = forms.ChoiceField(choices=((i+1,i+1) for i in range(12)), label = gettext('month'),
                              initial = datetime.now().month)
    
    def save(self, *args, **kw):
        d = Demand.objects.get(project = self.cleaned_data['project'], year = self.cleaned_data['year'],
                               month = self.cleaned_data['month'])
        if self.instance.id:
            self.instance.demands.clear()
        i = forms.ModelForm.save(self, *args, **kw)
        d.invoices.add(i)
        return i
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['date'].widget.attrs = {'class':'vDateField'}
        if self.instance.id and self.instance.demands.count() == 1:
            demand = self.instance.demands.all()[0]
            self.fields['project'].initial = demand.project_id
            self.fields['year'].initial = demand.year
            self.fields['month'].initial = demand.month
    class Meta:
        model = Invoice
        exclude=('creation_date','offset')

    field_order = ['project', 'year', 'month', 'num', 'date', 'amount', 'remarks']

class InvoiceForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = Invoice
        exclude=('creation_date','offset')
        
class InvoiceOffsetForm(forms.ModelForm):
    invoice_num = forms.IntegerField(label=gettext('invoice_num'))       
    add_type = forms.ChoiceField(choices=((1,u'תוספת'),
                                          (2,'קיזוז')), 
                                          label=gettext('add_type'))
    def clean(self):
        add_type, amount = self.cleaned_data['add_type'], self.cleaned_data['amount']
        self.cleaned_data['amount'] = int(add_type) == 2 and (amount * -1) or amount 
        return self.cleaned_data
    def clean_invoice_num(self):
        invoice_num = self.cleaned_data['invoice_num']
        invoices = Invoice.objects.filter(num = invoice_num)
        if invoices.count() == 0:
            raise forms.ValidationError(u"לא קיימת חשבונית שזה מספרה.")
        elif invoices.count() > 1:
            raise forms.ValidationError(u"קיימת יותר מחשבונית אחת עם מספר זה.")
        return invoice_num
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['date'].widget.attrs = {'class':'vDateField'}
        if self.instance.id:
            self.fields['add_type'].initial = self.instance.amount >= 0 and 1 or 2 
    class Meta:
        model = InvoiceOffset
        fields = ['invoice_num','date','add_type','amount','reason','remarks']

class PaymentBaseForm(forms.ModelForm):
    def clean(self):
        cleaned_data = self.cleaned_data
        payment_type = cleaned_data.get('payment_type')
        if payment_type and payment_type.id != PaymentType.Cash:
            if not cleaned_data.get('bank'):
                self._errors['bank'] = gettext('mandatory_field')
            if not cleaned_data.get('branch_num'):
                self._errors['branch_num'] = gettext('mandatory_field')
        return cleaned_data
    class Meta:
        model = Payment
        exclude=('creation_date',)
        
class PaymentForm(PaymentBaseForm):
    def __init__(self, *args, **kw):
        super(PaymentForm, self).__init__(*args, **kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'1'})
        self.fields['payment_date'].widget.attrs = {'class':'vDateField', 'size':10}
        for field in ['num','support_num','bank','branch_num','amount']:
            self.fields[field].widget.attrs = {'size':10}
    class Meta:
        model = Payment
        exclude=('creation_date',)

class SplitPaymentForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'1'})
        self.fields['payment_date'].widget.attrs = {'class':'vDateField', 'size':10}
    class Meta:
        model = Payment
        exclude = ('creation_date','amount')

    field_order = ['num','support_num','bank','branch_num','payment_type','payment_date','remarks']

class SplitPaymentDemandForm(MonthForm):
    project = forms.ModelChoiceField(queryset = Project.objects.all(), label = gettext('project'))
    amount = forms.IntegerField(label=gettext('amount'))
    
class DemandPaymentForm(PaymentBaseForm):
    project = forms.ModelChoiceField(queryset = Project.objects.all(), label = gettext('project'))
    year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                             label = gettext('year'), initial = datetime.now().year)
    month = forms.ChoiceField(choices=((i+1,i+1) for i in range(12)), label = gettext('month'),
                              initial = datetime.now().month)
    
    def save(self, *args, **kw):
        demand, new = Demand.objects.get_or_create(project = self.cleaned_data['project'], year = self.cleaned_data['year'], month = self.cleaned_data['month'])
        if self.instance.id:
            self.instance.demands.clear()
        p = forms.ModelForm.save(self, *args, **kw)
        demand.payments.add(p)
        return p
    def __init__(self, *args, **kw):
        super(DemandPaymentForm, self).__init__(*args, **kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['payment_date'].widget.attrs = {'class':'vDateField'}
        if self.instance.id and self.instance.demands.count() == 1:
            demand = self.instance.demands.all()[0]
            self.fields['project'].initial = demand.project_id
            self.fields['year'].initial = demand.year
            self.fields['month'].initial = demand.month
    class Meta:
        model = Payment
        exclude = ('creation_date')

    field_order = ['project','year','month','num','support_num','bank','branch_num',
        'payment_type','payment_date','amount','remarks']

class NHSaleForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self, *args, **kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['sale_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = NHSale
        exclude=('nhmonth',)

class NHSaleSideForm(forms.ModelForm):
    lawyer1_pay = forms.FloatField(label=gettext('lawyer_pay'), required=False)
    lawyer2_pay = forms.FloatField(label=gettext('lawyer_pay'), required=False)
    def save(self, *args, **kw):
        nhs = forms.ModelForm.save(self, *args,**kw)
        nhsale = nhs.nhsale
        year, month = nhsale.nhmonth.year, nhsale.nhmonth.month
        income = self.cleaned_data['income']
        self.cleaned_data['actual_commission'] = income / nhsale.price * 100
        l1, l2 = self.cleaned_data['lawyer1'], self.cleaned_data['lawyer2']
        lp1, lp2 = self.cleaned_data['lawyer1_pay'], self.cleaned_data['lawyer2_pay']
        if l1 and lp1:
            q = l1.nhpays.filter(nhsaleside = nhs)
            nhp = q.count() == 1 and q[0] or NHPay(lawyer=l1, nhsaleside = nhs, year = year, month = month)
            nhp.amount = lp1
            nhp.save()
        if l2 and lp2:
            q = l2.nhpays.filter(nhsaleside = nhs)
            nhp = q.count() == 1 and q[0] or NHPay(lawyer=l2, nhsaleside = nhs, year = year, month = month)
            nhp.amount = lp2
            nhp.save()
        return nhs
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self, *args, **kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['employee_remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['voucher_date'].widget.attrs = {'class':'vDateField'}
        if self.instance.id:
            nhss = self.instance
            if self.instance.lawyer1:
                pays = self.instance.lawyer1.nhpays.filter(nhsaleside=nhss)
                if pays.count() == 1:
                    self.fields['lawyer1_pay'].initial = pays[0].amount
            if self.instance.lawyer2:
                pays = self.instance.lawyer2.nhpays.filter(nhsaleside=nhss)
                if pays.count() == 1:
                    self.fields['lawyer2_pay'].initial = pays[0].amount
    class Meta:
        model = NHSaleSide
        exclude=('nhsale','invoices','payments')

class LoanForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(LoanForm, self).__init__(*args, **kw)
        self.fields['date'].widget.attrs = {'class':'vDateField'}
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'30', 'rows':'6'})
    class Meta:
        model= Loan
        fields=('employee','amount','month','year','date','pay_num','remarks')

class DemandSendForm(forms.ModelForm):
    is_finished = forms.BooleanField(required=False)
    by_mail = forms.BooleanField(required=False)
    mail = forms.EmailField(required=False)
    by_fax = forms.BooleanField(required=False)
    fax = forms.CharField(max_length=20, required=False)
    class Meta:
        model = Demand
        exclude = ('project','year','month','sale_count')

class DivisionTypeSeasonForm(SeasonForm):
    division_type = forms.ModelChoiceField(queryset = DivisionType.objects.all(), label=gettext('division_type'))

class ReminderForm(forms.ModelForm):
    status = forms.ModelChoiceField(queryset=ReminderStatusType.objects.all(), label=gettext('status'))
    def save(self, *args, **kw):
        r = forms.ModelForm.save(self, *args, **kw)
        if not self.instance.statuses.count() or self.instance.statuses.latest().type.id != self.cleaned_data['status']:
            r.statuses.create(type=self.cleaned_data['status'])
        return r
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['content'].widget = forms.Textarea(attrs={'cols':'30', 'rows':'6'})
        if self.instance.statuses.count():
            self.fields['status'].initial = self.instance.statuses.latest().type_id
    class Meta:
        model = Reminder
        fields=('content',)

class AttachmentForm(forms.ModelForm):
    tag_new = forms.CharField(max_length=20, required=False, label=gettext('tag_new'))
    
    def save(self, *args, **kw):
        forms.ModelForm.save(self, *args, **kw)
        tag = self.cleaned_data['tag_new'].strip()
        if tag and tag != '':
            self.instance.tags.create(name=tag)
        return self.instance
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
    
    class Meta:
        model = Attachment
        fields=('tags','file','type','sr_name','is_private','remarks','tag_new')

    field_order = ['file', 'type', 'sr_name', 'is_private', 'tags', 'tag_new', 'remarks']

class NHBranchEmployeeForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(NHBranchEmployeeForm, self).__init__(*args, **kw)
        self.fields['start_date'].widget.attrs = {'class':'vDateField'}
        self.fields['end_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = NHBranchEmployee
        fields=('nhbranch','nhemployee','is_manager','start_date','end_date')

class NHMonthForm(MonthForm):
    nhbranch = forms.ModelChoiceField(queryset = NHBranch.objects.all(), label=gettext('nhbranch'))  
    
class EmploymentTermsForm(RevisionExtForm):
    def __init__(self, *args, **kw):
        super(EmploymentTermsForm, self).__init__(*args, **kw)
        self.fields['tax_deduction_date'].widget.attrs = {'class':'vDateField'}
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'3'}
    class Meta:
        model = EmploymentTerms
        fields=('salary_base','salary_net','safety','hire_type','include_tax','include_lawyer',
                'tax_deduction_source','tax_deduction_source_precentage','tax_deduction_date','remarks')

class EmployeeSalaryForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(EmployeeSalaryForm, self).__init__(*args, **kw)
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['pdf_remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
    class Meta:
        model = EmployeeSalary
        exclude=('month','year','commissions','is_deleted')
  
class NHEmployeeSalaryForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(NHEmployeeSalaryForm, self).__init__(*args, **kw)
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['pdf_remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
    class Meta:
        model = NHEmployeeSalary
        exclude=('month','year','commissions','is_deleted','admin_commission')

class TaskFilterForm(forms.Form):
    status = forms.ChoiceField(choices = [('done', 'בוצעו'), ('undone','לא בוצעו'), ('all','הכל')])
    sender = forms.ChoiceField(choices = [('me', 'אני שלחתי'), ('others','נשלחו אלי')])

class ProjectSeasonForm(SeasonForm):
    project = forms.ModelChoiceField(Project.objects.all(), empty_label=gettext('choose_project'), label=gettext('project'))

    field_order = ['project', 'from_year', 'from_month', 'to_year', 'to_month']

class NHBranchSeasonForm(SeasonForm):
    nhbranch = forms.ModelChoiceField(NHBranch.objects.all(), label=gettext('nhbranch'))

class EmployeeSeasonForm(SeasonForm):
    employee = forms.ModelChoiceField(EmployeeBase.objects.all(), label=gettext('employee'))

    field_order = ['employee', 'from_year', 'from_month', 'to_year', 'to_month']

class ContactFilterForm(forms.Form):
    first_name = forms.CharField(label=gettext('first_name'), required=False)
    last_name = forms.CharField(label=gettext('last_name'), required=False)
    role = forms.CharField(label=gettext('role'), required=False)
    company = forms.CharField(label=gettext('company'), required=False)

class LocateDemandForm(forms.Form):
    project = forms.ModelChoiceField(Project.objects.all(), empty_label=gettext('choose_project'))
    year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                             initial = datetime.now().year)
    month = forms.ChoiceField(choices=((i,i) for i in range(1,13)), initial = common.current_month().month)  
    
    def clean_year(self):
        return int(self.cleaned_data['year'])
    def clean_month(self):
        return int(self.cleaned_data['month'])
    
class LocateHouseForm(forms.Form):
    project = forms.ModelChoiceField(Project.objects.all(), empty_label=gettext('choose_project'))
    building_num = forms.CharField(widget=forms.TextInput(attrs={'size':'3'}), initial = gettext('building_num'))
    house_num = forms.CharField(widget=forms.TextInput(attrs={'size':'3'}), initial = gettext('house_num'))
    
class CopyBuildingForm(forms.Form):
    building = forms.ModelChoiceField(queryset = Building.objects.all(), label=gettext('building'))
    new_building_num = forms.CharField(label=gettext('new_building_num'))
    include_houses = forms.BooleanField(label=gettext('include_houses'), initial=True)
    include_house_prices = forms.BooleanField(label=gettext('include_house_prices'), initial=True)
    include_parkings = forms.BooleanField(label=gettext('include_parkings'), initial=True)
    include_storages = forms.BooleanField(label=gettext('include_storages'), initial=True)
    
    def clean(self):
        cleaned_data = self.cleaned_data
        building, new_building_num = cleaned_data['building'], cleaned_data['new_building_num']
        project_buildings = building.project.buildings.all()
        if project_buildings.filter(num = new_building_num).exists():
            raise forms.ValidationError(gettext('existing_building_num'))
        return cleaned_data
    
class ProjectSelectForm(forms.Form):
    project = forms.ModelChoiceField(Project.objects.all(), label = gettext('project'))
    
class EmployeeSelectForm(forms.Form):
    employee = forms.ModelChoiceField(EmployeeBase.objects.all(), label = gettext('employee'))
    
class DemandSelectForm(MonthForm):
    project = forms.ModelChoiceField(Project.objects.all(), label = gettext('project'))

class DemandPayBalanceForm(forms.Form):
    
    class DemandPayBalanceType(object):
        __slots__ = ('id', 'name')
        
        def __init__(self, id = None, name = None):
            self.id, self.name = id, name
    
    demand_pay_balance_choices = [DemandPayBalanceType('all', gettext('all')), DemandPayBalanceType('un-paid', gettext('un-paid')),
                                  DemandPayBalanceType('mis-paid', gettext('mis-paid')), DemandPayBalanceType('partially-paid', gettext('partially-paid')),
                                  DemandPayBalanceType('fully-paid', gettext('fully-paid')),]
    
    from_year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                                    label = gettext('from_year'), 
                                    initial = common.current_month().year)
    from_month = forms.ChoiceField(choices=((i,i) for i in range(1,13)), 
                                    label = gettext('from_month'),
                                    initial = common.current_month().month)
    to_year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                                label = gettext('to_year'), 
                                initial = common.current_month().year)
    to_month = forms.ChoiceField(choices=((i,i) for i in range(1,13)), 
                                label = gettext('to_month'),
                                initial = common.current_month().month)

    all_times = forms.BooleanField(required=False, label = gettext('all_times'))
    
    project = forms.ModelChoiceField(queryset=Project.objects.all(), 
                                    empty_label=gettext('all_projects'), 
                                    label = gettext('project'),
                                    required = False)
    
    demand_pay_balance = forms.ChoiceField(choices=[(x.id, x.name) for x in demand_pay_balance_choices], 
                                            label = gettext('pay_balance'))
    
    def __init__(self, *args, **kw):
        super(DemandPayBalanceForm, self).__init__(*args, **kw)
        for attr in ['from_month', 'from_year', 'to_month', 'to_year']:
            self.fields[attr].required = False
    def clean_demand_pay_balance(self):
        demand_pay_balance = self.cleaned_data['demand_pay_balance']
        return [dpb for dpb in DemandPayBalanceForm.demand_pay_balance_choices if dpb.id == demand_pay_balance][0]
    def clean_from_year(self):
        return int(self.cleaned_data['from_year'])
    def clean_from_month(self):
        return int(self.cleaned_data['from_month'])
    def clean_to_year(self):
        return int(self.cleaned_data['to_year'])
    def clean_to_month(self):
        return int(self.cleaned_data['to_month'])

class MailForm(forms.Form):
    to = forms.EmailField(label = gettext('to'))
    Cc = forms.EmailField(label = gettext('CC'), required = False)
    Bcc = forms.EmailField(label = gettext('BCC'), required = False)
    subject = forms.CharField(label = gettext('subject'), max_length = 100, required = False)
    attachment1 = forms.FileField(label = gettext('attachment') + ' 1', required = False)
    attachment2 = forms.FileField(label = gettext('attachment') + ' 2', required = False)
    attachment3 = forms.FileField(label = gettext('attachment') + ' 3', required = False)
    attachment4 = forms.FileField(label = gettext('attachment') + ' 4', required = False)
    attachment5 = forms.FileField(label = gettext('attachment') + ' 5', required = False)
    contents = forms.CharField(widget = forms.Textarea(), label = gettext('contents'), required = False)
    
class RevisionFilterForm(forms.Form):
    content_type = forms.ModelChoiceField(queryset = ContentType.objects.all())
    object_id = forms.IntegerField()