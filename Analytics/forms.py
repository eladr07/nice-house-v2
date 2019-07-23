     
from django.utils.translation import gettext
from django.forms import ModelChoiceField, CharField, ChoiceField, TextInput

from Management.models import Project, HouseType, DivisionType
from Management.forms import SeasonForm

RoomsChoices = [(float(i)/2,float(i)/2) for i in range(2, 21)]
RoomsChoices.insert(0, ('',u'----'))

class SaleAnalysisForm(SeasonForm):
    project = ModelChoiceField(queryset = Project.objects.all(), label=gettext('project'))
    building_num = CharField(max_length=4, min_length=1, required = False, label = gettext('building_num'),
                                   widget = TextInput(attrs = {'size':'3'}))
    include_clients = ChoiceField(label = gettext('include_clients'), required = False, choices = ((0,u'לא'),
                                                                                                          (1,u'כן')))
    house_type = ModelChoiceField(queryset=HouseType.objects.all(), required = False, label = gettext('house_type'))
    rooms_num = ChoiceField(label = gettext('rooms'), required = False, choices = RoomsChoices)
  
class GloablProfitLossForm(SeasonForm):
    division_choices = []
    division_choices.extend([(-1, gettext('all_divisions')),
                             (-2, gettext('all_nh'))])
    divisions = ChoiceField(label = gettext('division_type'), choices = division_choices)
        
    def clean_divisions(self):
        division = self.cleaned_data['divisions']
        if division == '-1':
            return DivisionType.objects.all()
        elif division == '-2':
            return DivisionType.objects.nh_divisions()
        return [DivisionType.objects.get(pk = int(division))]
