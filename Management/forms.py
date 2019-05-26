﻿import django.forms as forms
from django.forms.models import modelform_factory
import sys
import common
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext
from models import *
from datetime import datetime, date
import reversion

class SeasonForm(forms.Form):
    from_year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                             label = ugettext('from_year'), initial = common.current_month().year)
    from_month = forms.ChoiceField(choices=((i,i) for i in range(1,13)), label = ugettext('from_month'),
                              initial = common.current_month().month)
    to_year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                             label = ugettext('to_year'), initial = common.current_month().year)
    to_month = forms.ChoiceField(choices=((i,i) for i in range(1,13)), label = ugettext('to_month'),
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
                             label = ugettext('year'), initial = datetime.now().year)
    month = forms.ChoiceField(choices=((i,i) for i in range(1,13)), label = ugettext('month'),
                              initial = common.current_month().month)  
    def clean_year(self):
        return int(self.cleaned_data['year'])
    def clean_month(self):
        return int(self.cleaned_data['month'])

class RevisionExtForm(forms.ModelForm):
    date = forms.DateTimeField(label = ugettext('modification_date'), help_text = ugettext('modification_date_help'))
    
    def __init__(self, *args, **kw):
        super(RevisionExtForm, self).__init__(*args,**kw)
        self.fields['date'].widget.attrs = {'class':'vDateField'}   
    def save(self, *args, **kw):
        reversion.revision.add_meta(RevisionExt, date = self.cleaned_data['date'])
        return super(RevisionExtForm, self).save(*args, **kw)
    
    class Meta:
        pass
        
CVarForm = modelform_factory(CVar, RevisionExtForm)

CVarPrecentageForm = modelform_factory(CVarPrecentage, RevisionExtForm)

CByPriceForm = modelform_factory(CByPrice, RevisionExtForm)

CZilberForm = modelform_factory(CZilber, RevisionExtForm)

CVarPrecentageFixedForm = modelform_factory(CVarPrecentageFixed, RevisionExtForm)

BDiscountSaveForm = modelform_factory(BDiscountSave, RevisionExtForm)

BDiscountSavePrecentageForm = modelform_factory(BDiscountSavePrecentage, RevisionExtForm)

BHouseTypeForm = modelform_factory(BHouseType, RevisionExtForm)

BSaleRateForm = modelform_factory(BSaleRate, RevisionExtForm)

AdvancePaymentForm = modelform_factory(AdvancePayment)

LoanPayForm = modelform_factory(LoanPay)
        
SalaryExpensesForm = modelform_factory(SalaryExpenses)
        
TaskForm = modelform_factory(Task)

AccountForm = modelform_factory(Account)

DemandRemarksForm = modelform_factory(Demand, fields = ('remarks',))

DemandSaleCountForm = modelform_factory(Demand, fields = ('sale_count',))

EmployeeSalaryRemarksForm = modelform_factory(EmployeeSalary, fields = ('employee', 'remarks'))

EmployeeSalaryRefundForm = modelform_factory(EmployeeSalary, fields = ('employee', 'refund','refund_type'))

NHEmployeeSalaryRemarksForm = modelform_factory(NHEmployeeSalary, fields = ('nhemployee', 'remarks'))

NHEmployeeSalaryRefundForm = modelform_factory(NHEmployeeSalary, fields = ('nhemployee', 'refund','refund_type'))

NHCommissionForm = modelform_factory(NHCommission, RevisionExtForm)

SalePriceModForm = modelform_factory(SalePriceMod)

SaleHouseModForm = modelform_factory(SaleHouseMod)

SalePreForm = modelform_factory(SalePre)

SaleRejectForm = modelform_factory(SaleReject)

class ContactForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'3'})
    class Meta:
        model = Contact

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

class ProjectDetailsForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'3'})
    class Meta:
        model = ProjectDetails

class BuildingForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'3'})
    class Meta:
        model = Building

class PricelistForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self, *args, **kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'5'})
        self.fields['settle_date'].widget = forms.TextInput({'class':'vDateField'})
    class Meta:
        model = Pricelist

class PricelistUpdateForm(forms.Form):
    Add, Multiply, Precentage = 1,2,3
    
    pricelisttype = forms.ModelChoiceField(queryset = PricelistType.objects.all(), 
                                           required=False, label = ugettext('pricelisttype'))
    all_pricelists = forms.BooleanField(required=False, label=ugettext('all_pricelists'))
    date = forms.DateField(label=ugettext('date'))
    action = forms.ChoiceField(label=ugettext('action'), choices = (
                                                                    (Add, ugettext('add')),
                                                                    (Multiply, ugettext('multiply')),
                                                                    (Precentage, ugettext('precentage'))
                                                                    ))
    value = forms.FloatField(label=ugettext('value'), required=False)
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
        
class StorageForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea({'cols':'20', 'rows':'3'})
        if self.instance.id > 0:
            self.fields['house'].queryset = self.instance.building.houses.all()
    class Meta:
        model = Storage

class HouseForm(forms.ModelForm):
    parking1 = forms.ModelChoiceField(queryset=Parking.objects.all(), required=False, label = ugettext('parking') + ' 1')
    parking2 = forms.ModelChoiceField(queryset=Parking.objects.all(), required=False, label = ugettext('parking') + ' 2')
    parking3 = forms.ModelChoiceField(queryset=Parking.objects.all(), required=False, label = ugettext('parking') + ' 3')
    storage1 = forms.ModelChoiceField(queryset=Storage.objects.all(), required=False, label = ugettext('storage') + ' 1')
    storage2 = forms.ModelChoiceField(queryset=Storage.objects.all(), required=False, label = ugettext('storage') + ' 2')
    price = forms.IntegerField(label=ugettext('price'), required=False)
    price_date = forms.DateField(label = ugettext('price_date'), required = False)
    
    def save(self, price_type_id, *args, **kw):
        h = forms.ModelForm.save(self, *args, **kw)
        for f in ['parking1','parking2','parking3']:
            if self.cleaned_data[f]:
                h.parkings.add(self.cleaned_data[f])
        for f in ['storage1','storage2']:
            if self.cleaned_data[f]:
                h.storages.add(self.cleaned_data[f])
        price, price_date = self.cleaned_data['price'], self.cleaned_data['price_date']
        q = self.instance.versions.filter(type__id = price_type_id)
        if price and (q.count() == 0 or q.latest().price != price):
            house_version = HouseVersion(type = PricelistType.objects.get(pk=price_type_id), price = price, date = price_date)
            self.instance.versions.add(house_version)
        return h
    
    def clean(self):
        cleaned_data = self.cleaned_data
        price, price_date = cleaned_data.get('price'), cleaned_data.get('price_date')
        if price and not price_date:
            self._errors['price_date'] = ugettext('mandatory_field')
            del cleaned_data['price_date']
        if price_date and not price:
            self._errors['price'] = ugettext('mandatory_field')
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

class EmployeeForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['birth_date'].widget.attrs = {'class':'vDateField'}
        self.fields['work_start'].widget.attrs = {'class':'vDateField'}
        self.fields['work_end'].widget.attrs = {'class':'vDateField'}
        if self.instance.id:
            self.fields['main_project'].queryset = self.instance.projects
    class Meta:
        model = Employee

class NHEmployeeForm(forms.ModelForm):
    nhbranch = forms.ModelChoiceField(NHBranch.objects.all(), ugettext('choose_branch'), label = ugettext('nhbranch'))
    
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['birth_date'].widget.attrs = {'class':'vDateField'}
        self.fields['work_start'].widget.attrs = {'class':'vDateField'}
        self.fields['work_end'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = NHEmployee
      
class ProjectCommissionForm(RevisionExtForm):
    def __init__(self, *args, **kw):
        super(ProjectCommissionForm, self).__init__(*args,**kw)
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'5'}
    class Meta:
        model = ProjectCommission

class EmployeeAddProjectForm(forms.Form):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), label=ugettext('employee'))
    project = forms.ModelChoiceField(queryset=Project.objects.active(), label=ugettext('project'))
    start_date = forms.DateField(label=ugettext('start date'))
    def __init__(self, *args, **kw):
        super(EmployeeAddProjectForm, self).__init__(*args, **kw)
        self.fields['start_date'].widget.attrs = {'class':'vDateField'}

class EmployeeRemoveProjectForm(forms.Form):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), label=ugettext('employee'))
    project = forms.ModelChoiceField(queryset=Project.objects.all(), label=ugettext('project'))
    end_date = forms.DateField(label=ugettext('end_date'))
    def __init__(self, *args, **kw):
        super(EmployeeRemoveProjectForm, self).__init__(*args, **kw)
        self.fields['end_date'].widget.attrs = {'class':'vDateField'}

class CPriceAmountForm(forms.ModelForm):
    def clean_price(self):
        price = self.cleaned_data['price']
        if not price:
            price = sys.maxint
        return price
    class Meta:
        model = CPriceAmount
 
class SignupForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset = Project.objects.all(), label=ugettext('project'))
    building = forms.ModelChoiceField(queryset = Building.objects.all(), label=ugettext('building'))
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

class SignupCancelForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['reason'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model =SignupCancel

class DemandDiffForm(forms.ModelForm):
    add_type = forms.ChoiceField(choices=((1,u'תוספת'),
                                          (2,'קיזוז')), 
                                          label=ugettext('add_type'))
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
        
class SaleAnalysisForm(SeasonForm):
    project = forms.ModelChoiceField(queryset = Project.objects.all(), label=ugettext('project'))
    building_num = forms.CharField(4, 1, required = False, label = ugettext('building_num'),
                                   widget = forms.TextInput(attrs = {'size':'3'}))
    include_clients = forms.ChoiceField(label = ugettext('include_clients'), required = False, choices = ((0,u'לא'),
                                                                                                          (1,u'כן')))
    house_type = forms.ModelChoiceField(queryset=HouseType.objects.all(), required = False, label = ugettext('house_type'))
    rooms_num = forms.ChoiceField(label = ugettext('rooms'), required = False, choices = RoomsChoices)
                
class SaleForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset = Project.objects.all(), label=ugettext('project'))
    building = forms.ModelChoiceField(queryset = Building.objects.all(), label=ugettext('building'))
    joined_sale = forms.BooleanField(label = ugettext('joined sale'), required = False)
    signup_date = forms.DateField(label=ugettext('signup_date'), required=False)
    
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
                              label=ugettext('remarks'))
    def save(self, *args, **kw):
        if self.instance.id:
            i=forms.ModelForm.save(self, *args, **kw)
        else:
            i=forms.ModelForm.save(self, *args, **kw)
            self.instance.feed()
        return i
    class Meta:
        model = Demand

class DemandInvoiceForm(forms.ModelForm):
    project = forms.ModelChoiceField(queryset = Project.objects.all(), label = ugettext('project'))
    year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                             label = ugettext('year'), initial = datetime.now().year)
    month = forms.ChoiceField(choices=((i+1,i+1) for i in range(12)), label = ugettext('month'),
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

class InvoiceForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = Invoice
        
class InvoiceOffsetForm(forms.ModelForm):
    invoice_num = forms.IntegerField(label=ugettext('invoice_num'))       
    add_type = forms.ChoiceField(choices=((1,u'תוספת'),
                                          (2,'קיזוז')), 
                                          label=ugettext('add_type'))
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
                self._errors['bank'] = ugettext('mandatory_field')
            if not cleaned_data.get('branch_num'):
                self._errors['branch_num'] = ugettext('mandatory_field')
        return cleaned_data
    class Meta:
        model = Payment
        
class PaymentForm(PaymentBaseForm):
    def __init__(self, *args, **kw):
        super(PaymentForm, self).__init__(*args, **kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'1'})
        self.fields['payment_date'].widget.attrs = {'class':'vDateField', 'size':10}
        for field in ['num','support_num','bank','branch_num','amount']:
            self.fields[field].widget.attrs = {'size':10}
    class Meta:
        model = Payment

class SplitPaymentForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'1'})
        self.fields['payment_date'].widget.attrs = {'class':'vDateField', 'size':10}
    class Meta:
        model = Payment
        exclude = ('amount')

class SplitPaymentDemandForm(MonthForm):
    project = forms.ModelChoiceField(queryset = Project.objects.all(), label = ugettext('project'))
    amount = forms.IntegerField(label=ugettext('amount'))
    
class DemandPaymentForm(PaymentBaseForm):
    project = forms.ModelChoiceField(queryset = Project.objects.all(), label = ugettext('project'))
    year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                             label = ugettext('year'), initial = datetime.now().year)
    month = forms.ChoiceField(choices=((i+1,i+1) for i in range(12)), label = ugettext('month'),
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

class NHSaleForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self, *args, **kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['sale_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = NHSale

class NHSaleSideForm(forms.ModelForm):
    lawyer1_pay = forms.FloatField(label=ugettext('lawyer_pay'), required=False)
    lawyer2_pay = forms.FloatField(label=ugettext('lawyer_pay'), required=False)
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

class LoanForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(LoanForm, self).__init__(*args, **kw)
        self.fields['date'].widget.attrs = {'class':'vDateField'}
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'30', 'rows':'6'})
    class Meta:
        model= Loan

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
    division_type = forms.ModelChoiceField(queryset = DivisionType.objects.all(), label=ugettext('division_type'))

class GloablProfitLossForm(SeasonForm):
    division_choices = [(division.id, unicode(division)) for division in DivisionType.objects.all()]
    division_choices.extend([(-1, ugettext('all_divisions')),
                             (-2, ugettext('all_nh'))])
    divisions = forms.ChoiceField(label = ugettext('division_type'), choices = division_choices)
        
    def clean_divisions(self):
        division = self.cleaned_data['divisions']
        if division == '-1':
            return DivisionType.objects.all()
        elif division == '-2':
            return DivisionType.objects.nh_divisions()
        return [DivisionType.objects.get(pk = int(division))]

class ReminderForm(forms.ModelForm):
    status = forms.ModelChoiceField(queryset=ReminderStatusType.objects.all(), label=ugettext('status'))
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

class TaxForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(TaxForm, self).__init__(*args, **kw)
        self.fields['date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = Tax

class AttachmentForm(forms.ModelForm):
    tag_new = forms.CharField(max_length=20, required=False, label=ugettext('tag_new'))
    
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

class NHBranchEmployeeForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(NHBranchEmployeeForm, self).__init__(*args, **kw)
        self.fields['start_date'].widget.attrs = {'class':'vDateField'}
        self.fields['end_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = NHBranchEmployee

class IncomeFilterForm(SeasonForm):
    division_type = forms.ModelChoiceField(queryset = DivisionType.objects.all(), label=ugettext('division_type'), 
                                           required=False)
    income_type = forms.ModelChoiceField(queryset = IncomeType.objects.all(), label=ugettext('income_type'), 
                                         required=False)
    client_type = forms.ModelChoiceField(queryset = ClientType.objects.all(), label=ugettext('client_name'), 
                                         required=False)
    income_producer_type = forms.ModelChoiceField(queryset = IncomeProducerType.objects.all(), label=ugettext('income_producer_type'), 
                                                  required=False)
    
class CheckFilterForm(SeasonForm):
    division_type = forms.ModelChoiceField(queryset = DivisionType.objects.all(), label=ugettext('division_type'), 
                                           required=False)
    expense_type = forms.ModelChoiceField(queryset = ExpenseType.objects.all(), label=ugettext('expense_type'), 
                                          required=False)
    supplier_type = forms.ModelChoiceField(queryset = SupplierType.objects.all(), label=ugettext('supplier_type'), 
                                           required=False)

class EmployeeCheckFilterForm(SeasonForm):
    employee = forms.ModelChoiceField(queryset = EmployeeBase.objects.all(), label=ugettext('employee'), required=False)
    division_type = forms.ModelChoiceField(queryset = DivisionType.objects.all(), label=ugettext('division_type'), 
                                           required=False)
    expense_type = forms.ModelChoiceField(queryset = ExpenseType.objects.all(), label=ugettext('expense_type'), 
                                          required=False)

class CheckForm(forms.ModelForm):
    invoice_num = forms.IntegerField(label = ugettext('invoice_num'), help_text=u'החשבונית חייבת להיות מוזנת במערכת',
                                     required=False)
    new_division_type = forms.CharField(label = ugettext('new_division_type'), max_length = 20, required=False)
    new_expense_type = forms.CharField(label = ugettext('new_expense_type'), max_length = 20, required=False)
    new_supplier_type = forms.CharField(label = ugettext('new_supplier_type'), max_length = 20, required=False)

    def clean_invoice_num(self):
        invoice_num = self.cleaned_data['invoice_num']
        query = Invoice.objects.filter(num = invoice_num)
        if query.count()==0:
            raise forms.ValidationError(u"אין חשבונית עם מס' זה")
        return invoice_num
    def save(self, *args, **kw):
        invoice_num = self.cleaned_data['invoice_num']
        invoice = Invoice.objects.get(num = invoice_num)
        self.instance.invoice = invoice
        return forms.ModelForm.save(self,*args,**kw)
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['issue_date'].widget.attrs = {'class':'vDateField'}
        self.fields['pay_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = Check
        fields = ['division_type','new_division_type','expense_type','new_expense_type',
                  'supplier_type', 'new_supplier_type','invoice_num','type','issue_date','pay_date','num','amount',
                  'tax_deduction_source','order_verifier','payment_verifier','remarks']

class EmployeeCheckForm(forms.ModelForm):
    invoice_num = forms.IntegerField(label = ugettext('invoice_num'), help_text=u'החשבונית חייבת להיות מוזנת במערכת',
                                     required=False)
    new_division_type = forms.CharField(label = ugettext('new_division_type'), max_length = 20, required=False)
    new_expense_type = forms.CharField(label = ugettext('new_expense_type'), max_length = 20, required=False)
    
    def clean_invoice_num(self):
        invoice_num = self.cleaned_data['invoice_num']
        query = Invoice.objects.filter(num = invoice_num)
        if query.count()==0:
            raise forms.ValidationError(u"אין חשבונית עם מס' זה")
        return invoice_num
    def save(self, *args, **kw):
        invoice_num = self.cleaned_data['invoice_num']
        invoice = Invoice.objects.get(num = invoice_num)
        self.instance.invoice = invoice
        return forms.ModelForm.save(self,*args,**kw)
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
        self.fields['issue_date'].widget.attrs = {'class':'vDateField'}
        self.fields['pay_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = EmployeeCheck
        fields = ['division_type','new_division_type','employee','year','month','expense_type','new_expense_type','purpose_type',
                  'invoice_num','type','amount','num','issue_date','pay_date','remarks']

class IncomeForm(forms.ModelForm):
    new_division_type = forms.CharField(label = ugettext('new_division_type'), max_length = 20, required=False)
    new_income_type = forms.CharField(label = ugettext('new_income_type'), max_length = 20, required=False)
    new_income_producer_type = forms.CharField(label = ugettext('new_income_producer_type'), max_length = 20, required=False)
    new_client_type = forms.CharField(label=ugettext('new_client_type'), max_length = 30, required = False)

    def clean(self):
        if not self.cleaned_data['division_type'] and not self.cleaned_data['new_division_type']:
            raise forms.ValidationError(ugettext('missing_division_type'))
        if not self.cleaned_data['income_type'] and not self.cleaned_data['new_income_type']:
            raise forms.ValidationError(ugettext('missing_income_type'))
        if not self.cleaned_data['income_producer_type'] and not self.cleaned_data['new_income_producer_type']:
            raise forms.ValidationError(ugettext('missing_income_producer_type'))
        if not self.cleaned_data['client_type'] and not self.cleaned_data['new_client_type']:
            raise forms.ValidationError(ugettext('missing_client_type'))
        return self.cleaned_data
    
    class Meta:
        model = Income
        fields = ['year','month','division_type','new_division_type','income_type','new_income_type',
                  'income_producer_type','new_income_producer_type','client_type','new_client_type']

class DealForm(forms.ModelForm):
    new_client_status_type = forms.CharField(label=ugettext('new_client_status_type'), max_length = 30, required = False)
    
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self,*args,**kw)
        self.fields['remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
        
    def clean(self):
        if not self.cleaned_data['client_status_type'] and not self.cleaned_data['new_client_status_type']:
            raise forms.ValidationError(ugettext('missing_client_status_type'))
        return self.cleaned_data
    
    class Meta:
        model = Deal
        fields = ['client_status_type','new_client_status_type','address','rooms','floor','price','commission_precentage','commission','remarks']

class NHMonthForm(MonthForm):
    nhbranch = forms.ModelChoiceField(queryset = NHBranch.objects.all(), label=ugettext('nhbranch'))  
    
class EmploymentTermsForm(RevisionExtForm):
    def __init__(self, *args, **kw):
        super(EmploymentTermsForm, self).__init__(*args, **kw)
        self.fields['tax_deduction_date'].widget.attrs = {'class':'vDateField'}
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'3'}
    class Meta:
        model = EmploymentTerms

class EmployeeSalaryForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(EmployeeSalaryForm, self).__init__(*args, **kw)
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['pdf_remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
    class Meta:
        model = EmployeeSalary
  
class NHEmployeeSalaryForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(NHEmployeeSalaryForm, self).__init__(*args, **kw)
        self.fields['remarks'].widget.attrs = {'cols':'20', 'rows':'3'}
        self.fields['pdf_remarks'].widget = forms.Textarea(attrs={'cols':'20', 'rows':'3'})
    class Meta:
        model = NHEmployeeSalary

class TaskFilterForm(forms.Form):
    status = forms.ChoiceField(choices = [('done', 'בוצעו'), ('undone','לא בוצעו'), ('all','הכל')])
    sender = forms.ChoiceField(choices = [('me', 'אני שלחתי'), ('others','נשלחו אלי')])

class ProjectSeasonForm(SeasonForm):
    project = forms.ModelChoiceField(Project.objects.all(), ugettext('choose_project'), label=ugettext('project'))

class NHBranchSeasonForm(SeasonForm):
    nhbranch = forms.ModelChoiceField(NHBranch.objects.all(), label=ugettext('nhbranch'))

class EmployeeSeasonForm(SeasonForm):
    employee = forms.ModelChoiceField(EmployeeBase.objects.all(), label=ugettext('employee'))
    
class MadadBIForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self, *args, **kw)
        self.fields['publish_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = MadadBI

class MadadCPForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        forms.ModelForm.__init__(self, *args, **kw)
        self.fields['publish_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = MadadCP

class CityCallersForm(forms.ModelForm):
    new_city = forms.CharField(label = ugettext('new_city'), max_length = 20, required=False)
    
    class Meta:
        model = CityCallers
        fields = ['city','new_city','callers_num']
        
class MediaReferralsForm(forms.ModelForm):
    new_media = forms.CharField(label = ugettext('new_media'), max_length = 20, required=False)
    
    class Meta:
        model = MediaReferrals
        fields = ['media','new_media','referrals_num']

class EventForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(EventForm, self).__init__(*args, **kw)
        self.fields['date'].widget.attrs = {'class':'vDateField'}
        self.fields['attendees'].widget.attrs = {'cols':'30', 'rows':'3'}
        self.fields['issues'].widget.attrs = {'cols':'30', 'rows':'3'}
        self.fields['summary'].widget.attrs = {'cols':'30', 'rows':'3'}
        self.fields['remarks'].widget.attrs = {'cols':'30', 'rows':'3'}
    class Meta:
        model = Event
        
class SaleProcessForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(SaleProcessForm, self).__init__(*args, **kw)
        self.fields['objection'].widget.attrs = {'cols':'30', 'rows':'3'}
        self.fields['remarks'].widget.attrs = {'cols':'30', 'rows':'3'}
    class Meta:
        model = SaleProcess
        
class PriceOfferForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(EventForm, self).__init__(*args, **kw)
        self.fields['remarks'].widget.attrs = {'cols':'30', 'rows':'3'}
    class Meta:
        model = PriceOffer

class ActivityForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(ActivityForm, self).__init__(*args, **kw)
        self.fields['to_date'].widget.attrs = {'class':'vDateField'}
        self.fields['from_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = Activity
        fields = ['project','employee','from_date','to_date','office_meetings_num','recurring_meetings_num','new_meetings_from_phone_num']

class ContactFilterForm(forms.Form):
    first_name = forms.CharField(label=ugettext('first_name'), required=False)
    last_name = forms.CharField(label=ugettext('last_name'), required=False)
    role = forms.CharField(label=ugettext('role'), required=False)
    company = forms.CharField(label=ugettext('company'), required=False)

class LocateDemandForm(forms.Form):
    project = forms.ModelChoiceField(Project.objects.all(), ugettext('choose_project'))
    year = forms.ChoiceField(choices=((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                             initial = datetime.now().year)
    month = forms.ChoiceField(choices=((i,i) for i in range(1,13)), initial = common.current_month().month)  
    
    def clean_year(self):
        return int(self.cleaned_data['year'])
    def clean_month(self):
        return int(self.cleaned_data['month'])
    
class LocateHouseForm(forms.Form):
    project = forms.ModelChoiceField(Project.objects.all(), ugettext('choose_project'))
    building_num = forms.CharField(widget=forms.TextInput(attrs={'size':'3'}), initial = ugettext('building_num'))
    house_num = forms.CharField(widget=forms.TextInput(attrs={'size':'3'}), initial = ugettext('house_num'))
    
class CopyBuildingForm(forms.Form):
    building = forms.ModelChoiceField(queryset = Building.objects.all(), label=ugettext('building'))
    new_building_num = forms.CharField(label=ugettext('new_building_num'))
    include_houses = forms.BooleanField(label=ugettext('include_houses'), initial=True)
    include_house_prices = forms.BooleanField(label=ugettext('include_house_prices'), initial=True)
    include_parkings = forms.BooleanField(label=ugettext('include_parkings'), initial=True)
    include_storages = forms.BooleanField(label=ugettext('include_storages'), initial=True)
    
    def clean(self):
        cleaned_data = self.cleaned_data
        building, new_building_num = cleaned_data['building'], cleaned_data['new_building_num']
        project_buildings = building.project.buildings.all()
        if project_buildings.filter(num = new_building_num).exists():
            raise forms.ValidationError(ugettext('existing_building_num'))
        return cleaned_data
    
class ProjectSelectForm(forms.Form):
    project = forms.ModelChoiceField(Project.objects.all(), label = ugettext('project'))
    
class EmployeeSelectForm(forms.Form):
    employee = forms.ModelChoiceField(EmployeeBase.objects.all(), label = ugettext('employee'))
    
class DemandSelectForm(MonthForm):
    project = forms.ModelChoiceField(Project.objects.all(), label = ugettext('project'))

class DemandPayBalanceForm(forms.Form):
    
    class DemandPayBalanceType(object):
        __slots__ = ('id', 'name')
        
        def __init__(self, id = None, name = None):
            self.id, self.name = id, name
    
    demand_pay_balance_choices = [DemandPayBalanceType('all', ugettext('all')), DemandPayBalanceType('un-paid', ugettext('un-paid')),
                                  DemandPayBalanceType('mis-paid', ugettext('mis-paid')), DemandPayBalanceType('partially-paid', ugettext('partially-paid')),
                                  DemandPayBalanceType('fully-paid', ugettext('fully-paid')),]
    
    from_year = forms.ChoiceField(((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                                  label = ugettext('from_year'), initial = common.current_month().year)
    from_month = forms.ChoiceField(((i,i) for i in range(1,13)), label = ugettext('from_month'),
                                   initial = common.current_month().month)
    to_year = forms.ChoiceField(((i,i) for i in range(datetime.now().year - 10, datetime.now().year+10)), 
                                label = ugettext('to_year'), initial = common.current_month().year)
    to_month = forms.ChoiceField(((i,i) for i in range(1,13)), label = ugettext('to_month'),
                                 initial = common.current_month().month)

    all_times = forms.BooleanField(False, label = ugettext('all_times'))
    
    project = forms.ModelChoiceField(Project.objects.all(), ugettext('all_projects'), label = ugettext('project'),
                                     required = False)
    
    demand_pay_balance = forms.ChoiceField([(x.id, x.name) for x in demand_pay_balance_choices], label = ugettext('pay_balance'))
    
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
    to = forms.EmailField(label = ugettext('to'))
    Cc = forms.EmailField(label = ugettext('CC'), required = False)
    Bcc = forms.EmailField(label = ugettext('BCC'), required = False)
    subject = forms.CharField(label = ugettext('subject'), max_length = 100, required = False)
    attachment1 = forms.FileField(label = ugettext('attachment') + ' 1', required = False)
    attachment2 = forms.FileField(label = ugettext('attachment') + ' 2', required = False)
    attachment3 = forms.FileField(label = ugettext('attachment') + ' 3', required = False)
    attachment4 = forms.FileField(label = ugettext('attachment') + ' 4', required = False)
    attachment5 = forms.FileField(label = ugettext('attachment') + ' 5', required = False)
    contents = forms.CharField(widget = forms.Textarea(), label = ugettext('contents'), required = False)
    
class RevisionFilterForm(forms.Form):
    content_type = forms.ModelChoiceField(queryset = ContentType.objects.all())
    object_id = forms.IntegerField()