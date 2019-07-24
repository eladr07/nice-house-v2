from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from django.views.generic.edit import UpdateView
from django.views.generic.detail import DetailView

from .models import ActivityBase, Activity, City, CityCallers, Media, MediaReferrals, Event, SaleProcess, PriceOffer
from .forms import ActivityForm, CityCallersForm, MediaReferralsForm, EventForm, SaleProcessForm

# Create your views here.

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
    return object_edit_core(request, ActivityForm, activity, 'Activity/activity_edit.html')
    
class ActivityDetailView(LoginRequiredMixin, DetailView):
    model = Activity
    template_name = 'Activity/activity_detail.html'

class ActivityUpdate(PermissionRequiredMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    success_url = 'edit'
    template_name = 'Activity/activity_edit.html'
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
