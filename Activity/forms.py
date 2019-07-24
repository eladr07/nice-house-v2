from django.forms import ModelForm, CharField

from django.utils.translation import gettext

from .models import CityCallers, MediaReferrals, Event, Activity, SaleProcess, PriceOffer

class CityCallersForm(ModelForm):
    new_city = CharField(label = gettext('new_city'), max_length = 20, required=False)
    
    class Meta:
        model = CityCallers
        fields = ['city','new_city','callers_num']
        
class MediaReferralsForm(ModelForm):
    new_media = CharField(label = gettext('new_media'), max_length = 20, required=False)
    
    class Meta:
        model = MediaReferrals
        fields = ['media','new_media','referrals_num']

class EventForm(ModelForm):
    def __init__(self, *args, **kw):
        super(EventForm, self).__init__(*args, **kw)
        self.fields['date'].widget.attrs = {'class':'vDateField'}
        self.fields['attendees'].widget.attrs = {'cols':'30', 'rows':'3'}
        self.fields['issues'].widget.attrs = {'cols':'30', 'rows':'3'}
        self.fields['summary'].widget.attrs = {'cols':'30', 'rows':'3'}
        self.fields['remarks'].widget.attrs = {'cols':'30', 'rows':'3'}

    class Meta:
        model = Event
        exclude=('activity_base',)
        
class SaleProcessForm(ModelForm):
    def __init__(self, *args, **kw):
        super(SaleProcessForm, self).__init__(*args, **kw)
        self.fields['objection'].widget.attrs = {'cols':'30', 'rows':'3'}
        self.fields['remarks'].widget.attrs = {'cols':'30', 'rows':'3'}

    class Meta:
        model = SaleProcess
        exclude=('activity_base',)
        
class PriceOfferForm(ModelForm):
    def __init__(self, *args, **kw):
        super(PriceOfferForm, self).__init__(*args, **kw)
        self.fields['remarks'].widget.attrs = {'cols':'30', 'rows':'3'}

    class Meta:
        model = PriceOffer
        exclude=('nhactivity',)

class ActivityForm(ModelForm):
    def __init__(self, *args, **kw):
        super(ActivityForm, self).__init__(*args, **kw)
        self.fields['to_date'].widget.attrs = {'class':'vDateField'}
        self.fields['from_date'].widget.attrs = {'class':'vDateField'}

    class Meta:
        model = Activity
        fields = ['project','employee','from_date','to_date','office_meetings_num','recurring_meetings_num','new_meetings_from_phone_num']
