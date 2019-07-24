from django.db import models

from django.utils.translation import gettext

from Management.models import Sale, NHSale, Signup, House, Building, Project, Employee, NHEmployee, NHBranch

# Create your models here.
class Media(models.Model):
    name = models.CharField(gettext('name'), max_length=20, unique=True)
        
class City(models.Model):
    name = models.CharField(gettext('name'), max_length=20, unique=True)
        
class CityCallers(models.Model):
    activity_base = models.ForeignKey('ActivityBase', on_delete=models.PROTECT, editable=False)
    
    city = models.ForeignKey('City', on_delete=models.PROTECT, verbose_name = gettext('city'), blank=True)
    callers_num = models.PositiveSmallIntegerField(gettext('callers_num'))

class MediaReferrals(models.Model):
    activity_base = models.ForeignKey('ActivityBase', on_delete=models.PROTECT, editable=False)
    
    media = models.ForeignKey('Media', on_delete=models.PROTECT, verbose_name = gettext('media'), blank=True)
    referrals_num = models.PositiveSmallIntegerField(gettext('referrals_num'))

class PriceOffer(models.Model):
    nhactivity = models.ForeignKey('NHActivity', on_delete=models.PROTECT, editable=False)
    
    nhemployee = models.ForeignKey(NHEmployee, on_delete=models.PROTECT, verbose_name = gettext('nhemployee'))
    
    address = models.CharField(gettext('address'), max_length=50)
    rooms = models.FloatField(gettext('rooms'))
    
    clients = models.CharField(gettext('clients'), max_length=50)
    
    price_wanted = models.IntegerField(gettext('price_wanted'))
    price_offered = models.IntegerField(gettext('price_offered'))
    
    commission_seller = models.FloatField(gettext('commission_seller'))
    commission_buyer = models.FloatField(gettext('commission_buyer'))
    
    remarks = models.TextField(gettext('remarks'), max_length=200, null=True, blank=True)

class SaleProcess(models.Model):
    activity_base = models.ForeignKey('ActivityBase', on_delete=models.PROTECT, editable=False)
    
    project = models.ForeignKey(Project, on_delete=models.PROTECT, verbose_name=gettext('project'))
    building = models.ForeignKey(Building, on_delete=models.PROTECT, verbose_name=gettext('building'))
    house = models.ForeignKey(House, on_delete=models.PROTECT, verbose_name=gettext('house'))
    
    price = models.IntegerField(gettext('price'))
    objection = models.TextField(gettext('objection'), max_length=200, null=True, blank=True)
    remarks = models.TextField(gettext('remarks'), max_length=200, null=True, blank=True)

class Event(models.Model):
    activity_base = models.ForeignKey('ActivityBase', on_delete=models.PROTECT, editable=False)
    
    date = models.DateTimeField(gettext('date'))
    initiator = models.CharField(gettext('event_initiator'), max_length=50)
    subject = models.CharField(gettext('event_subject'), max_length=50)
    attendees = models.TextField(gettext('event_attendees'), max_length=200, null=True, blank=True)
    summary = models.TextField(gettext('event_summary'), max_length=200, null=True, blank=True)
    issues = models.TextField(gettext('issues'), max_length=200, null=True, blank=True)
    remarks = models.TextField(gettext('remarks'), max_length=200, null=True, blank=True)
    
    class Meta:
        ordering = ['date']
    
class ActivityBase(models.Model):
    from_date = models.DateField(gettext('from_date'))
    to_date = models.DateField(gettext('to_date'))
    office_meetings_num = models.PositiveSmallIntegerField(gettext('office_meetings_num'))
    recurring_meetings_num = models.PositiveSmallIntegerField(gettext('recurring_meetings_num'))
    new_meetings_from_phone_num = models.PositiveSmallIntegerField(gettext('new_meetings_from_phone_num'))
    
class Activity(ActivityBase):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, verbose_name=gettext('project'))
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, verbose_name = gettext('employee'))
    
    @property
    def sales(self):
        return Sale.objects.filter(house__building__project = self.project, employee = self.employee,
                                   sale_date__range = (self.from_date, self.to_date))
    @property
    def signups(self):
        return Signup.objects.filter(house__building__project = self.project, employee = self.employee,
                                     date__range = (self.from_date, self.to_date))
    @property
    def canceled_signups(self):
        return self.signups.filter(cancel__isnull = False)
    @property
    def active_signups(self):
        return self.signups.filter(cancel__isnull = True)
    
    class Meta:
        db_table = 'Activity'
        
class NHActivity(ActivityBase):
    nhbranch = models.ForeignKey(NHBranch, on_delete=models.PROTECT, verbose_name=gettext('nhbranch'))
    nhemployee = models.ForeignKey(NHEmployee, on_delete=models.PROTECT, verbose_name = gettext('nhemployee'))
    
    @property
    def nhsales(self):
        return NHSale.objects.filter(nhsaleside_set__signing_advisor = self.nhemploee)