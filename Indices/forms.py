from django.forms import ModelForm

from .models import MadadCP, MadadBI, Tax

class MadadBIForm(ModelForm):
    def __init__(self, *args, **kw):
        ModelForm.__init__(self, *args, **kw)
        self.fields['publish_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = MadadBI
        fields=('year','month','publish_date','value')

class MadadCPForm(ModelForm):
    def __init__(self, *args, **kw):
        ModelForm.__init__(self, *args, **kw)
        self.fields['publish_date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = MadadCP
        fields=('year','month','publish_date','value')

class TaxForm(ModelForm):
    def __init__(self, *args, **kw):
        super(TaxForm, self).__init__(*args, **kw)
        self.fields['date'].widget.attrs = {'class':'vDateField'}
    class Meta:
        model = Tax
        fields=('date','value')
