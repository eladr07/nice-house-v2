﻿# coding: utf-8

import itertools
import logging
import Management.common as common

from datetime import datetime, date
from decimal import InvalidOperation

from django.db import models
from django.db import IntegrityError
from django.utils.translation import gettext
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from Indices.models import Tax

from .templatetags.management_extras import commaise
from .decorators import cache_method
from .managers import *

Salary_Types = (
                (None, u'לא ידוע'),
                (False, u'ברוטו'),
                (True, u'נטו')
                )
TaxDeductionTypes = (
                (None, u'לא ידוע'),
                (False, u'פטור'),
                (True, u'יש')
                )
Family_State_Types = (
                      (1, u'רווק'),
                      (2, u'נשוי'),
                      (3, u'גרוש'),
                      (4, u'אלמן')
                      )
Boolean = (
           (False, u'לא'),
           (True, u'כן')
           )

Attachment_types = (
                    (1, gettext('sent')),
                    (2, gettext('received')),
                    )
    
class Tag(models.Model):
    name = models.CharField(unique = True, max_length=20)
    is_deleted = models.BooleanField(editable=False, default=False)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table = 'Tag'
        ordering = ['name']
        
class Attachment(models.Model):
    object_id = models.TextField(null = True, editable = False)
    
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, null = True, editable = False)
     
    add_time = models.DateTimeField(auto_now_add=True, editable=False)
    user_added = models.ForeignKey(User, on_delete=models.PROTECT, related_name = 'attachments', editable=False, verbose_name=gettext('user'))
    tags = models.ManyToManyField('Tag', related_name = 'attachments', blank=True, verbose_name = gettext('tags'))
    file = models.FileField(gettext('filename'), upload_to='files')

    type = models.SmallIntegerField(gettext('attachment_type'), choices = Attachment_types)
    sr_name = models.CharField(gettext('sr_name'), max_length=20)
    is_private = models.BooleanField(gettext('is_private'), blank=True)
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)
    
    def get_related_object(self):
        obj = self.content_type.get_object_for_this_type(pk = self.object_id)
        return obj

    def get_absolute_url(self):
        return '/attachment/%s' % self.id

    class Meta:
        db_table = 'Attachment'
        permissions = (('list_attachment', 'Can list attachments'),)
        
class ReminderStatusType(models.Model):
    Added, Done, Deleted = 1,2,3
    name = models.CharField(max_length=20, unique=True)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table='ReminderStatusType'
        
class ReminderStatus(models.Model):
    reminder = models.ForeignKey('Reminder', on_delete=models.PROTECT, related_name='statuses')
    type = models.ForeignKey('ReminderStatusType', on_delete=models.PROTECT)
    time = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.type) + ' - ' + str(self.time)
    class Meta:
        db_table='ReminderStatus'
        ordering = ['-time']
        get_latest_by = 'time'
        
class Reminder(models.Model):
    content = models.TextField(gettext('content'))
    def do(self):
        self.statuses.create(type = ReminderStatusType.objects.get(pk = ReminderStatusType.Done)).save()
    def delete(self):
        self.statuses.create(type = ReminderStatusType.objects.get(pk = ReminderStatusType.Deleted)).save()
    def get_absolute_url(self):
        return '/reminder/%s' % self.id
    class Meta:
        db_table = 'Reminder'

class ProjectDetails(models.Model):
    architect = models.CharField(gettext('architect'), max_length=30)
    houses_num = models.PositiveSmallIntegerField(gettext('houses_num'))
    buildings_num = models.PositiveSmallIntegerField(gettext('buildings_num'))
    bank = models.CharField(gettext('accompanied_bank'), max_length=20)
    url = models.URLField(gettext('url'), null=True, blank=True)
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)  
    building_types = models.ManyToManyField('BuildingType', verbose_name=gettext('building_types'))
    class Meta:
        db_table = 'ProjectDetails'

class Project(models.Model):
    details = models.ForeignKey('ProjectDetails', on_delete=models.PROTECT, editable=False, null=True)
    initiator = models.CharField(gettext('initiator'), max_length=30)
    name = models.CharField(gettext('project name'), max_length=30)
    city = models.CharField(gettext('city'), max_length=30)
    hood = models.CharField(gettext('hood'), max_length=30)
    office_address = models.CharField(gettext('office address'), max_length=30)
    phone = models.CharField(gettext('project phone'), max_length=15)
    cell_phone = models.CharField(gettext('project cell phone'), max_length=15)
    fax = models.CharField(gettext('project fax'), max_length=15)
    mail = models.EmailField(gettext('mail'), null=True, blank=True)
    is_marketing = models.BooleanField(gettext('is_marketing'), choices=Boolean)
    start_date = models.DateField(gettext('startdate'))
    end_date = models.DateField(gettext('enddate'), null=True, blank=True)
    remarks = models.TextField(gettext('special_data'), null=True, blank=True)
    demand_contact = models.ForeignKey('Contact', on_delete=models.PROTECT, editable=False, related_name='projects_demand', blank=True, null=True)
    payment_contact = models.ForeignKey('Contact', on_delete=models.PROTECT, editable=False, related_name='projects_payment', blank=True, null=True)
    contacts = models.ManyToManyField('Contact', related_name='projects', editable=False)
    reminders = models.ManyToManyField('Reminder', editable=False)

    objects = ProjectManager()
    
    def get_open_reminders(self):
        return [r for r in self.reminders.all() if r.statuses.latest().type.id 
                not in (ReminderStatusType.Deleted,ReminderStatusType.Done)]
    def sales(self):
        current = common.current_month()
        return Sale.objects.filter(house__building__project = self,
                                   contractor_pay_month = current.month,
                                   contractor_pay_year = current.year)
    def signups(self):
        current = common.current_month()
        return Signup.objects.filter(house__building__project = self, date__year = current.year, date__month= current.month)
    def end(self):
        self.end_date = datetime.now()
    def __str__(self):
        return u"%s - %s" % (self.initiator, self.name)
    def houses(self):
        return House.objects.filter(building__project = self, building__is_deleted = False)
    def non_deleted_buildings(self):
        return self.buildings.filter(is_deleted= False)
    def save(self, *args, **kw):
        models.Model.save(self, *args, **kw)
        if ProjectCommission.objects.filter(project = self).count()==0 :
            ProjectCommission(project = self, include_tax = True).save()
    @property
    def is_active(self):
        return self.is_marketing and not self.end_date
    @property
    def name_and_city(self):
        """
        Returns the name of the project including the name of the city.
        """
        return self.city.strip() in self.name and self.name or self.name + ' ' + self.city
    def get_absolute_url(self):
        return '/projects/%s' % self.id
    class Meta:
        verbose_name = gettext('project')
        verbose_name_plural = gettext('projects')
        db_table = 'Project'
        ordering = ['initiator','name']
        permissions = (('projects_profit','Projects profit'),('project_list_pdf','Projects list PDF'))

class ParkingType(models.Model):
    name = models.CharField(gettext('name'), max_length=20, unique=True)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table='ParkingType'
      
class PricelistType(models.Model):
    Company, Doh0 = 1, 2
    name = models.CharField(gettext('name'), max_length=20, unique=True)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table='PricelistType'

class Parking(models.Model):
    building = models.ForeignKey('Building', on_delete=models.PROTECT, verbose_name=gettext('building'), related_name='parkings')
    house = models.ForeignKey('House', on_delete=models.PROTECT, null=True, blank=True, related_name='parkings', verbose_name=gettext('house'))
    num = models.PositiveSmallIntegerField(gettext('parking_num'))
    type = models.ForeignKey('ParkingType', on_delete=models.PROTECT, verbose_name=gettext('parking_type'))
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)
    def get_absolute_url(self):
        return '/parkings/%s' % self.id
    def __str__(self):
        return u'מס\' %s - %s' % (self.num, self.type)
    class Meta:
        db_table='Parking'
        unique_together = ('building', 'num')
        ordering = ['num']
        
class Storage(models.Model):
    building = models.ForeignKey('Building', on_delete=models.PROTECT, verbose_name=gettext('building'), related_name='storages')
    house = models.ForeignKey('House', on_delete=models.PROTECT, null=True, blank=True, related_name='storages', verbose_name=gettext('house'))
    num = models.PositiveSmallIntegerField(gettext('storage_num'))
    size = models.FloatField(gettext('size'), null=True, blank=True)
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)
    
    def get_absolute_url(self):
        return '/storages/%s' % self.id
    def __str__(self):
        return self.size and u'מס\' %s - %s מ"ר' % (self.num, self.size) or u'מס\' %s' % self.num 
    class Meta:
        db_table='Storage'
        unique_together = ('building', 'num')
        ordering = ['num']

class House(models.Model):
    building = models.ForeignKey('Building', on_delete=models.PROTECT, related_name='houses',verbose_name = gettext('building'), editable=False)
    type = models.ForeignKey('HouseType', on_delete=models.PROTECT, verbose_name=gettext('asset_type'))
    num = models.CharField(gettext('house_num'), max_length=5)
    floor = models.PositiveSmallIntegerField(gettext('floor'))
    rooms = models.FloatField(gettext('rooms'))
    net_size = models.FloatField(gettext('net_size'))
    garden_size = models.FloatField(gettext('garden_size'), null=True, blank=True)
    remarks = models.CharField(gettext('remarks'), max_length = 200, null=True, blank=True)
    
    bruto_size = models.FloatField(gettext('bruto_size'), null=True, blank=True)
    load_precentage = models.FloatField(gettext('load_precentage'), null=True, blank=True)
    parking_size = models.FloatField(gettext('parking_size'), null=True, blank=True)
    
    is_sold = models.BooleanField(gettext('is_sold'), default= False)
    
    objects = HouseManager()
    
    @property
    def settle_date(self):
        return self.building.pricelist.settle_date
    @property
    def perfect_size(self):
        balcony_size = self.garden_size or 0
        return self.net_size + balcony_size * 0.3
    def pricelist_types(self):
        versions = self.versions.select_related('type')
        return set([version.type for version in versions])
    def get_cottage_num(self):
        return self.num[:-1]
    @cache_method
    def get_signup(self):
        s = self.signups.filter(cancel=None)
        if s.count() > 1:
            raise IntegrityError('More than 1 active signup for house %s' % self.id)
        return s.count() > 0 and s[0] or None
    @cache_method 
    def get_sale(self):
        s = self.sales.filter(salecancel=None)
        if s.count() > 1:
            return s
        elif s.count() == 1:
            return s[0]
        return None
    def save(self, *args, **kw):
        if len(self.num) < 5:#patch to make house ordering work. because it is char field, '2' > '19'
            self.num = self.num.ljust(5, ' ')
        models.Model.save(self, *args, **kw)
    def __str__(self):
        return str(self.num).strip()
    def get_absolute_url(self):
        return self.building.get_absolute_url() + '/house/%s' % self.id
    class Meta:
        unique_together = ('building', 'num')
        ordering = ['num']
        db_table = 'House'

class BuildingType(models.Model):
    Cottage = 3
    name = models.CharField(max_length=20, unique=True)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table = 'BuildingType'

class HouseType(models.Model):
    Cottage = 2
    name = models.CharField(max_length=20, unique=True)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table = 'HouseType'

class HireType(models.Model):
    SelfEmployed, Salaried, DailySalaried, SmallEmployed, ExemptEmployed = 1,2,3,4,5
    name = models.CharField(max_length=20, unique=True)
    salary_net = models.NullBooleanField()
    include_tax = models.BooleanField()
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table = 'HireType'
        
class HouseVersion(models.Model):
    house = models.ForeignKey('House', on_delete=models.PROTECT, related_name = 'versions', editable=False)
    type = models.ForeignKey('PricelistType', on_delete=models.PROTECT, verbose_name = gettext('pricelist_type'), editable=False)
    date = models.DateTimeField()
    insert_date = models.DateTimeField(auto_now_add = True)
    price = models.IntegerField(gettext('price'))
    
    objects = HouseVersionManager()
    
    class Meta:
        get_latest_by = 'insert_date'
        ordering = ['date']
        db_table = 'HouseVersion'

class RankType(models.Model):
    RegionalSaleManager = 8
    name = models.CharField(gettext('rank'), max_length=20, unique=True)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table = 'RankType'
        ordering = ['name']
        
class ParkingCost(models.Model):
    pricelist = models.ForeignKey('Pricelist', on_delete=models.PROTECT, related_name='parking_costs')
    type = models.ForeignKey('ParkingType', on_delete=models.PROTECT, verbose_name = gettext('parking_type'))
    cost = models.FloatField(gettext('cost'))
    class Meta:
        db_table='ParkingCost'
        unique_together = ('pricelist','type')

class Pricelist(models.Model):
    include_tax = models.NullBooleanField(gettext('include_tax'))
    include_lawyer = models.NullBooleanField(gettext('include_lawyer'))
    include_parking = models.NullBooleanField(gettext('include_parking'))
    include_storage = models.NullBooleanField(gettext('include_storage'))
    include_registration = models.NullBooleanField(gettext('include_registration'))
    include_guarantee = models.NullBooleanField(gettext('include_guarantee'))
    settle_date = models.DateField(gettext('settle_date'), null=True, blank=True)
    allowed_discount = models.FloatField(gettext('allowed_discount'), default=0)
    is_permit = models.NullBooleanField(gettext('is_permit'))
    permit_date = models.DateField(gettext('permit_date'), null=True, blank=True)
    lawyer_fee = models.FloatField(gettext('lawyer_fee'), default=0)
    register_amount = models.FloatField(gettext('register_amount'), default=0)
    guarantee_amount = models.FloatField(gettext('guarantee_amount'), default=0)
    storage_cost = models.FloatField(gettext('storage_cost'), null=True, blank=True)
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)
    class Meta:
        db_table = 'Pricelist'

class Building(models.Model):
    pricelist = models.OneToOneField('Pricelist', on_delete=models.PROTECT, editable=False, related_name='building')
    project = models.ForeignKey('Project', on_delete=models.PROTECT, related_name = 'buildings', verbose_name=gettext('project'))
    num = models.CharField(gettext('building_num'), max_length = 4)
    name = models.CharField(gettext('name'), max_length=10, null=True, blank=True)
    type = models.ForeignKey('BuildingType', on_delete=models.PROTECT, verbose_name=gettext('building_types'))
    floors = models.PositiveSmallIntegerField(gettext('floors'))
    house_count = models.PositiveSmallIntegerField(gettext('houses_num'))
    stage = models.CharField(gettext('stage'), max_length = 1, null=True, blank=True)
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)
    is_deleted = models.BooleanField(default= False, editable= False)

    def is_cottage(self):
        return self.type.id == BuildingType.Cottage
    def pricelist_types(self):
        types = set()
        for house in self.houses.all():
            types.update(house.pricelist_types())
        return types
    def save(self, *args, **kw):
        try:
            pl = self.pricelist
        except Pricelist.DoesNotExist:
            pl = Pricelist()
            pl.save()
            self.pricelist = pl
        models.Model.save(self, *args, **kw)
    def __str__(self):
        return str(self.num)
    def get_absolute_url(self):
        return '/buildings/%s' % self.id
    class Meta:
        unique_together = ('project', 'num')
        db_table = 'Building'
        permissions = (('building_clients', 'Building Clients'), ('building_clients_pdf', 'Building Clients PDF'),
                       ('copy_building', 'Can copy building'),)
        
class Person(models.Model):
    first_name = models.CharField(gettext('first_name'), max_length=20)
    last_name = models.CharField(gettext('last_name'), max_length=20)
    cell_phone = models.CharField(gettext('cell_phone'), max_length=10, null=True, blank=True)
    mail = models.EmailField(gettext('mail'), null=True, blank=True)
    address = models.CharField(gettext('address'), max_length=40, null=True, blank=True)
    role = models.CharField(gettext('role'), max_length= 20, null=True, blank=True)
    def __str__(self):
        return u'%s %s' % (self.first_name, self.last_name)
    class Meta:
        abstract = True
        verbose_name = gettext('person')
        verbose_name_plural = gettext('persons')
        
class Contact(Person):
    phone = models.CharField(gettext('phone'), max_length=10, null=True, blank=True)
    fax = models.CharField(gettext('fax'), max_length=10, null=True, blank=True)
    company = models.CharField(gettext('company'), max_length=20, null=True, blank=True)
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)
    def get_absolute_url(self):
        return '/contact/%s' % self.id
    class Meta:
        db_table = 'Contact'
        unique_together = ('first_name','last_name')

class EmploymentTerms(models.Model):
    salary_base = models.PositiveIntegerField(gettext('salary base'))
    salary_net = models.NullBooleanField(gettext('salary net'), choices= Salary_Types)
    safety = models.PositiveIntegerField(gettext('safety'))
    hire_type = models.ForeignKey('HireType', on_delete=models.PROTECT, verbose_name=gettext('hire_type'), help_text = gettext('hire_type_help'))
    include_tax = models.BooleanField(gettext('commission_include_tax'), blank=True)
    include_lawyer = models.BooleanField(gettext('commission_include_lawyer'), blank=True)
    tax_deduction_source = models.NullBooleanField(gettext('tax_deduction_source'), choices = TaxDeductionTypes)
    tax_deduction_source_precentage = models.FloatField(gettext('tax_deduction_source_precentage'), null=True, blank=True)
    tax_deduction_date = models.DateField(gettext('tax_deduction_date'), null=True, blank=True)
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)
    class Meta:
        db_table='EmploymentTerms'
    
class TransactionUpdateHistory(models.Model):
    tid              = models.AutoField(primary_key=True)
    transaction_type = models.PositiveIntegerField(gettext('transaction_type'))
    transaction_id   = models.PositiveIntegerField(gettext('transaction_id'))
    field_name       = models.TextField(gettext('field_name'))
    field_value      = models.TextField(gettext('field_value'))
    timestamp        = models.DateTimeField(gettext('timestamp'))

    class Meta:
        db_table='TransactionUpdateHistory'

class EmployeeBase(Person):
    pid = models.PositiveIntegerField(gettext('pid'), unique=True)
    birth_date = models.DateField(gettext('birth_date'))
    work_phone = models.CharField(gettext('work_phone'), max_length=10, null=True, blank=True)
    work_fax = models.CharField(gettext('work_fax'), max_length=10, null=True, blank=True)
    home_phone = models.CharField(gettext('home_phone'), max_length=10)
    mate_phone = models.CharField(gettext('mate_phone'), max_length=10, null=True, blank=True)
    family_state = models.PositiveIntegerField(gettext('family state'), choices = Family_State_Types)
    child_num = models.PositiveIntegerField(gettext('child num'), null=True, blank=True)
    work_start = models.DateField(gettext('work start'))
    work_end = models.DateField(gettext('work end'), null=True, blank=True)
    
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)    
    reminders = models.ManyToManyField('Reminder', editable=False)
    account = models.ForeignKey('Account', on_delete=models.PROTECT, related_name='%(class)s',editable=False, null=True, blank=True)
    employment_terms = models.ForeignKey('EmploymentTerms', on_delete=models.PROTECT,editable=False, related_name='%(class)s', null=True, blank=True)
        
    objects = EmployeeManager()
    
    @property
    def derived(self):
        if hasattr(self, 'employee'):
            return self.employee
        elif hasattr(self, 'nhemployee'):
            return self.nhemployee
        return self    
    
    @property
    def payee(self):
        return self.account and self.account.payee or str(self)
    
    class Meta:
        db_table='EmployeeBase'

class Employee(EmployeeBase):
    rank = models.ForeignKey('RankType', on_delete=models.PROTECT, verbose_name=gettext('rank'))
    projects = models.ManyToManyField('Project', verbose_name=gettext('projects'), related_name='employees', 
                                      blank=True, editable=False)
    main_project = models.ForeignKey('Project', on_delete=models.PROTECT, verbose_name=gettext('main_project'), null=True, blank=True)
    objects = EmployeeManager()
    
    def get_open_reminders(self):
        return [r for r in self.reminders.all() if r.statuses.latest().type.id 
                not in (ReminderStatusType.Deleted,ReminderStatusType.Done)]
    def end(self):
        self.work_end = datetime.now()
    def save(self, *args, **kw):
        models.Model.save(self, *args, **kw)
        for p in self.projects.all():
            if self.commissions.filter(project = p).count() == 0:
                EPCommission(employee = self, project = p).save()
    def get_absolute_url(self):
        return '/employees/%s' % self.id
    class Meta:
        verbose_name = gettext('employee')
        verbose_name_plural = gettext('employees')
        db_table = 'Employee'
        ordering = ['rank','-work_start']

class NHSaleFilter(models.Model):
    His, NotHis, All = 1,2,3
    name = models.CharField(max_length = 20, unique=True)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table = 'NHSaleFilter'

class NHIncomeType(models.Model):
    Relative, Total = 1,2
    name = models.CharField(max_length = 20, unique=True)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table = 'NHIncomeType'

class Operator(models.Model):
    gt, lt, eq, neq = 1,2,3,4
    name = models.CharField(max_length = 20, unique=True)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table = 'Operator'

class AmountType(models.Model):
    Amount, Precentage = 1,2
    name = models.CharField(max_length = 20, unique=True)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table = 'AmountType'

class CommissionException(Exception):
    pass

class NHCommission(models.Model):
    nhbranch = models.ForeignKey('NHBranch', on_delete=models.PROTECT, verbose_name = gettext('nhbranch'))
    nhemployee = models.ForeignKey('NHEmployee', on_delete=models.PROTECT, verbose_name = gettext('nhemployee'))
    name = models.CharField(gettext('name'), max_length=30)
    
    left_filter = models.ForeignKey('NHSaleFilter', on_delete=models.PROTECT, verbose_name=gettext('filter'), related_name='left_nhcommission_set', 
                                    null=True, blank=True)
    left_income_type = models.ForeignKey('NHIncomeType', on_delete=models.PROTECT, verbose_name=gettext('income_type') , null=True, blank=True, 
                                         related_name='left_nhcommission_set')
    operator = models.ForeignKey('Operator', on_delete=models.PROTECT, verbose_name=gettext('operator'), null=True, blank=True)
    left_amount = models.FloatField(gettext('value'), null=True, blank=True)
    
    right_filter = models.ForeignKey('NHSaleFilter', on_delete=models.PROTECT, verbose_name=gettext('filter'), related_name='right_nhcommission_set', null=True, blank=True)
    right_income_type = models.ForeignKey('NHIncomeType', on_delete=models.PROTECT, verbose_name=gettext('income_type'), 
                                          related_name='right_nhcommission_set', null=True, blank=True)
    right_amount = models.FloatField(gettext('value'))
    right_amount_type = models.ForeignKey('AmountType', on_delete=models.PROTECT, verbose_name=gettext('value_type'))
    
    def calc(self, year, month, ratio = 1):
        scds = []
        income = 0
        # get all branch sales for this month        
        branch_sales_query = NHSaleSide.objects.filter(nhsale__nhmonth__year__exact = year, 
                                                       nhsale__nhmonth__month__exact = month,
                                                       nhsale__nhmonth__nhbranch = self.nhbranch)
        # filter : either employee1, employee2, employee3 is self.nhemployee
        q = models.Q(employee1 = self.nhemployee) | models.Q(employee2 = self.nhemployee) | models.Q(employee3 = self.nhemployee)
        
        def get_income(nhss, income_type_id, filter_id):
            if income_type_id == NHIncomeType.Total:
                income = nhss.net_income
            elif income_type_id == NHIncomeType.Relative:
                self_pay = nhss.get_employee_pay(self.nhemployee)
                all_pay = nhss.all_employee_commission
                if all_pay == 0:
                    return 0
                if filter_id == NHSaleFilter.His:
                    income = self_pay / all_pay * nhss.net_income
                elif filter_id == NHSaleFilter.NotHis:
                    income = (all_pay-self_pay) / all_pay * nhss.net_income
                elif filter_id == NHSaleFilter.All:
                    income = nhss.net_income
            return income
        
        if self.left_filter:
            if self.left_filter_id == NHSaleFilter.His:
                sales_query = branch_sales_query.filter(q)
            elif self.left_filter_id == NHSaleFilter.NotHis:
                sales_query = branch_sales_query.filter(~q)
            elif self.left_filter_id == NHSaleFilter.All:
                sales_query = branch_sales_query
            
            if self.left_amount and self.left_income_type:
                sales_income = 0
                for nhss in sales_query:
                    income = get_income(nhss, self.left_income_type_id, self.left_filter_id)
                    sales_income += income * ratio
                if self.operator_id == Operator.gt and sales_income < self.left_amount:
                    return scds
                if self.operator_id == Operator.lt and sales_income > self.left_amount:
                    return scds
            else:
                raise CommissionException('missing one of (left_amount, left_income_type)')
        
        if self.right_amount_type_id == AmountType.Amount:
            scds.append(NHSaleCommissionDetail(commission = self.name, amount = self.right_amount))
        else:        
            if self.right_filter_id == NHSaleFilter.His:
                sales_query = branch_sales_query.filter(q)
            elif self.right_filter_id == NHSaleFilter.NotHis:
                sales_query = branch_sales_query.filter(~q)
            elif self.right_filter_id == NHSaleFilter.All:
                sales_query = branch_sales_query
    
            for nhss in sales_query:
                income = get_income(nhss, self.right_income_type_id, self.right_filter_id)
                income *= ratio
                scds.append(NHSaleCommissionDetail(nhsaleside = nhss, commission = self.name,
                                                   amount = income * self.right_amount / 100,
                                                   precentage = self.right_amount, income = income))
        return scds
    def get_absolute_url(self):
        return '/nhcbi/%s' % self.id
    class Meta:
        db_table = 'NHCommission'

class NHBranchEmployee(models.Model):
    nhbranch = models.ForeignKey('NHBranch', on_delete=models.PROTECT, verbose_name = gettext('nhbranch'))
    nhemployee = models.ForeignKey('NHEmployee', on_delete=models.PROTECT, verbose_name = gettext('nhemployee'))
    is_manager = models.BooleanField(gettext('is_manager'))
    start_date = models.DateField(gettext('start_date'))
    end_date = models.DateField(gettext('end_date'), null = True, blank = True)

    objects = NHBranchEmployeeManager()

    def get_absolute_url(self):
        return '/nhbranchemployee/%s' % self.id
    class Meta:
        db_table = 'NHBranchEmployee'
        get_latest_by = 'start_date'
        ordering = ['nhbranch','start_date']

class NHBranch(models.Model):
    Shoham, Modiin, NesZiona = 1, 2, 3
    name = models.CharField(gettext('name'), max_length=30, unique=True)
    address = models.CharField(gettext('address'), max_length=40, null=True, blank=True)
    phone = models.CharField(gettext('phone'), max_length=15, null=True, blank=True)
    mail = models.EmailField(gettext('mail'), null=True, blank=True)
    fax = models.CharField(gettext('fax'), max_length=15, null=True, blank=True)
    url = models.URLField(gettext('url'), null=True, blank=True)
    @property
    @cache_method
    def active_nhbranchemployees(self):
        return NHBranchEmployee.objects.filter(nhbranch= self, end_date = None)
    @property
    @cache_method
    def nhemployees_archive(self):
        query = NHBranchEmployee.objects.filter(nhbranch= self).exclude(end_date = None)
        return [nhbe.nhemployee for nhbe in query]
    @property
    @cache_method
    def nhemployees(self):
        query = NHBranchEmployee.objects.filter(nhbranch = self, end_date = None)
        return [nhbe.nhemployee for nhbe in query]
    @property
    @cache_method
    def all_nhemployees(self):
        query = NHBranchEmployee.objects.filter(nhbranch = self)
        return [nhbe.nhemployee for nhbe in query]
    @property
    def prefix(self):
        return self.name.replace(u'נייס האוס ','') \
               [0]
    def get_absolute_url(self):
        return '/nhbranch/%s' % self.id
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table='NHBranch'
        permissions = (('nhbranch_1', 'NHBranch Shoham'),('nhbranch_2', 'NHBranch Modiin'),('nhbranch_3', 'NHBranch Nes Ziona'))
        
class NHEmployee(EmployeeBase):
    objects = NHEmployeeManager()

    @property
    def current_nhbranches(self):
        return self.nhbranchemployee_set.filter(end_date__isnull = True)
        
    def get_open_reminders(self):
        return [r for r in self.reminders.all() if r.statuses.latest().type.id 
                not in (ReminderStatusType.Deleted,ReminderStatusType.Done)]
    def end(self):
        self.work_end = datetime.now()
    def get_absolute_url(self):
        return '/nhemployees/%s' % self.id
    class Meta:
        db_table = 'NHEmployee'
        ordering = ['-work_start']

class NHSaleCommissionDetail(models.Model):
    nhemployeesalary = models.ForeignKey('NHEmployeeSalary', on_delete=models.PROTECT)
    nhsaleside = models.ForeignKey('NHSaleSide', on_delete=models.PROTECT, null=True)
    commission = models.CharField(max_length=30)
    income = models.IntegerField(null=True)
    precentage = models.FloatField(null=True)
    amount = models.IntegerField()
    class Meta:
        db_table = 'NHSaleCommissionDetail'
        
class Loan(models.Model):
    employee = models.ForeignKey('EmployeeBase', on_delete=models.PROTECT, related_name = 'loans', verbose_name=gettext('employee'))
    amount = models.IntegerField(gettext('amount'))
    month = models.PositiveSmallIntegerField(gettext('month'), choices=common.get_month_choices())
    year = models.PositiveSmallIntegerField(gettext('year'), choices=common.get_year_choices())
    date = models.DateField(gettext('date'), help_text = gettext('loan_date_help'), null=True)
    pay_num = models.PositiveSmallIntegerField(gettext('pay_num'))
    remarks = models.TextField(gettext('remarks'), blank=True, null=True)

    def get_absolute_url(self):
        return '/loans/%s' % self.id

    class Meta:
        db_table = 'Loan'
        permissions = (('list_loan', 'Loans list'), )

class LoanPay(models.Model):
    employee = models.ForeignKey('EmployeeBase', on_delete=models.PROTECT, related_name='loan_pays', verbose_name=gettext('employee'))
    month = models.PositiveSmallIntegerField(gettext('month'), choices=common.get_month_choices())
    year = models.PositiveSmallIntegerField(gettext('year'), choices=common.get_year_choices())
    amount = models.FloatField(gettext('amount'))
    deduct_from_salary = models.BooleanField(gettext('deduct_from_salary'), choices = Boolean, blank = True,
                                             help_text = gettext('deduct_from_salary_help'))
    remarks = models.TextField(gettext('remarks'), blank=True, null=True)

    objects = SeasonManager()

    def get_absolute_url(self):
        return '/loanpays/%s' % self.id
    class Meta:
        db_table = 'LoanPay'
    
class SaleCommissionDetail(models.Model):
    employee_salary = models.ForeignKey('EmployeeSalary', on_delete=models.PROTECT, related_name='commission_details', null=True)
    commission = models.CharField(max_length=30)
    value = models.FloatField(null=True)
    sale = models.ForeignKey('Sale', on_delete=models.PROTECT, null=True, related_name='commission_details')
    
    def __str__(self):
        return u'%s - %s' % (self.commission, self.value)
    
    class Meta:
        db_table = 'SaleCommissionDetail'
        ordering=['commission','value']

class EmployeeSalaryBaseStatusType(models.Model):
    Approved, SentBookkeeping, SentChecks = 1, 2, 3
    name = models.CharField(max_length=20)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table='EmployeeSalaryBaseStatusType'
        
class EmployeeSalaryBaseStatus(models.Model):
    employeesalarybase = models.ForeignKey('EmployeeSalaryBase', on_delete=models.PROTECT, related_name='statuses')
    type = models.ForeignKey('EmployeeSalaryBaseStatusType', on_delete=models.PROTECT)
    date = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table='EmployeeSalaryBaseStatus'
        ordering = ['date']
        get_latest_by = 'date'

class SalaryExpenses(models.Model):
    employee = models.ForeignKey('EmployeeBase', on_delete=models.PROTECT, verbose_name=gettext('employee'))
    month = models.PositiveSmallIntegerField(gettext('month'), choices=common.get_month_choices())
    year = models.PositiveSmallIntegerField(gettext('year'), choices=common.get_year_choices())
    income_tax = models.FloatField(gettext('income_tax'))
    national_insurance = models.FloatField(gettext('national_insurance'))
    health = models.FloatField(gettext('health'))
    pension_insurance = models.FloatField(gettext('pension_insurance'))
    vacation = models.FloatField(gettext('vacation'))
    convalescence_pay = models.FloatField(gettext('convalescence_pay'))
    employer_national_insurance = models.FloatField(gettext('employer_national_insurance'))
    employer_benefit = models.FloatField(gettext('employer_benefit'))
    compensation_allocation = models.FloatField(gettext('compensation_allocation'))
    approved_date = models.DateTimeField(editable=False, null=True)

    objects = SeasonManager()

    @property
    def salary(self):
        if isinstance(self.employee, Employee):
            return EmployeeSalary.objects.get(year = self.year, month = self.month, employee = self.employee.employee)
        elif isinstance(self.employee, NHEmployee):
            return NHEmployeeSalary.objects.get(year = self.year, month = self.month, nhemployee = self.employee.nhemployee)
    def approve(self):
        self.approved_date = datetime.now()
    def get_absolute_url(self):
        return '/salaries/expenses/%s' % self.id
    class Meta:
        db_table = 'SalaryExpenses'
        unique_together = ('employee','year','month')
        permissions = (('list_salaryexpenses', 'Can list salary expenses'),('season_salaryexpenses','Season salary expenses'),
                       ('season_total_salaryexpenses', 'Season total salary expenses'))
        
class EmployeeSalaryBase(models.Model):
    month = models.PositiveSmallIntegerField(gettext('month'), editable=False, choices=common.get_month_choices())
    year = models.PositiveSmallIntegerField(gettext('year'), editable=False, choices=common.get_year_choices())
    base = models.FloatField(gettext('salary_base'), null=True)
    commissions = models.FloatField(gettext('commissions'), editable=False, null=True)
    safety_net = models.FloatField(gettext('safety_net'), null=True, blank=True)
    var_pay = models.FloatField(gettext('var_pay'), null=True, blank=True)
    var_pay_type = models.CharField(gettext('var_pay_type'), max_length=20, null=True, blank=True)
    refund = models.FloatField(gettext('refund'), null=True, blank=True)
    refund_type = models.CharField(gettext('refund_type'), max_length=20, null=True, blank=True)
    deduction = models.FloatField(gettext('deduction'), null=True, blank=True)
    deduction_type = models.CharField(gettext('deduction_type'), max_length=20, null=True, blank=True)
    remarks = models.TextField(gettext('remarks'),null=True, blank=True)
    pdf_remarks = models.TextField(gettext('pdf_remarks'),null=True, blank=True)
    is_deleted = models.BooleanField(default = False, editable = False)
       
    @property
    def derived(self):
        if hasattr(self, 'employeesalary'):
            return self.employeesalary
        if hasattr(self, 'nhemployeesalary'):
            return self.nhemployeesalary
    def approve(self):
        self.statuses.create(type = EmployeeSalaryBaseStatusType.objects.get(pk = EmployeeSalaryBaseStatusType.Approved)).save()
    def send_to_checks(self):
        self.statuses.create(type = EmployeeSalaryBaseStatusType.objects.get(pk = EmployeeSalaryBaseStatusType.SentChecks)).save()
    def send_to_bookkeeping(self):
        self.statuses.create(type = EmployeeSalaryBaseStatusType.objects.get(pk = EmployeeSalaryBaseStatusType.SentBookkeeping)).save()
    def mark_deleted(self):
        self.is_deleted = True
    def get_employee(self):
        if hasattr(self, 'employeesalary'):
            return self.employeesalary.employee
        elif hasattr(self, 'nhemployeesalary'):
            return self.nhemployeesalary.nhemployee
    class Meta:
        db_table = 'EmployeeSalaryBase'
        ordering = ['year','month']
        permissions = (('salaries_bank', 'Salaries for bank'), ('employee_salary_delete', 'Delete salary'))

class NHEmployeeSalary(EmployeeSalaryBase):
    nhemployee = models.ForeignKey('NHEmployee', on_delete=models.PROTECT, verbose_name=gettext('nhemployee'), related_name='salaries')
    nhbranch = models.ForeignKey('NHBranch', on_delete=models.PROTECT, verbose_name=gettext('nhbranch'), null=True)
    admin_commission = models.IntegerField(editable=False, null=True)
    
    objects = EmployeeSalaryBaseManager()
        
    def get_employee(self):
        return self.nhemployee

    @property
    @cache_method
    def total_amount(self):
        return (self.base or 0) + (self.commissions or 0) + (self.admin_commission or 0) + (self.var_pay or 0) + (self.safety_net or 0) - (self.deduction or 0)
    def calculate(self):
        terms = self.nhemployee.employment_terms
        if not terms:
            self.remarks = u'לעובד לא הוגדרו תנאי העסקה!'
            return
                    
        if terms.salary_net == False:
            self.pdf_remarks = u'ברוטו, כמה נטו בעדכון הוצאות'
        if not terms.include_tax:
            d = date(self.month == 12 and self.year + 1 or self.year, self.month == 12 and 1 or self.month + 1, 1)
            tax = Tax.objects.filter(date__lt = d).latest().value
            self.ratio = 1 / ((tax + 100)/100)

        for scd in NHSaleCommissionDetail.objects.filter(nhemployeesalary = self):
            scd.delete()
        self.admin_commission, self.commissions, self.base = 0, 0, 0
        
        # calculate base salary. if the employee only worked for part of the month, get that relative amount
        if self.year == self.nhemployee.work_start.year and self.month == self.nhemployee.work_start.month:
            self.base = float(30 - self.nhemployee.work_start.day) / 30 * terms.salary_base 
        else:
            self.base = terms.salary_base
            
        # get all sales where either employee1, employee2, employee3, director is self.nhemployee
        q = models.Q(employee1 = self.nhemployee) | models.Q(employee2 = self.nhemployee) | models.Q(employee3 = self.nhemployee) | models.Q(director = self.nhemployee)
        
        sales_query = NHSaleSide.objects.filter(q, nhsale__nhmonth__year__exact = self.year,
                                                nhsale__nhmonth__month__exact = self.month,
                                                nhsale__nhmonth__nhbranch = self.nhbranch)
        
        for nhss in sales_query:
            pay = nhss.get_employee_pay(self.nhemployee) * self.ratio
            commission = nhss.get_employee_commission(self.nhemployee) * self.ratio
            self.commissions += pay
            NHSaleCommissionDetail.objects.create(nhemployeesalary=self, nhsaleside=nhss, commission='base', amount = pay,
                                                  precentage = commission, income = nhss.net_income)

        scds = []
        restore_date = date(self.year, self.month, 1)
        for nhcbi in self.nhemployee.nhcommission_set.filter(nhbranch = self.nhbranch):
            commission = common.restore_object(nhcbi, restore_date)
            commission_res = commission.calc(self.year, self.month, self.ratio)
            if commission_res:
                scds.extend(commission_res)
        
        total_scds_amount = 0
        for scd in scds:
            total_scds_amount += scd.amount
        
        if total_scds_amount < terms.safety:
            self.safety_net = terms.safety
        else:
            for scd in scds:
                scd.nhemployeesalary = self
                scd.save()
            self.admin_commission = total_scds_amount

    def __init__(self, *args, **kw):
        super(NHEmployeeSalary, self).__init__(*args, **kw)
        '''
        defines a multiplier for all commissions. used to reduce tax for employees that get the commission w/o tax
        '''
        self.ratio = 1
    def get_absolute_url(self):
        return '/nh-salaries/%s' % self.id
    class Meta:
        db_table='NHEmployeeSalary'
        
class EmployeeSalary(EmployeeSalaryBase):
    employee = models.ForeignKey('Employee', on_delete=models.PROTECT, verbose_name=gettext('employee'), related_name='salaries')
    
    objects = EmployeeSalaryBaseManager()
    
    def __init__(self, *args, **kw):
        super(EmployeeSalary, self).__init__(*args, **kw)
        self.project_commission = {}
        
    def get_employee(self):
        return self.employee
    @property
    @cache_method
    def total_amount(self):
        return (self.base or 0) + (self.commissions or 0) + (self.var_pay or 0) + (self.safety_net or 0) - (self.deduction or 0)
    @cache_method
    def project_salary(self):
        res = {}
        if not len(self.project_commission): return res
        ''' TODO: FIX AFTER SALARY EXPENSES ARE FEED '''
        bruto_amount = self.total_amount
        if self.employee.main_project:
            for project, commission in self.project_commission.items():
                res[project] = commission + (self.employee.main_project.id == project.id and bruto_amount-self.commissions or 0)
        else:
            if self.employee.projects.count():
                base = (bruto_amount-self.commissions) / self.employee.projects.count()
                for project, commission in self.project_commission.items():
                    res[project] = commission + base
        return res 
    def calculate(self):
        logger = logging.getLogger('salary')
        
        try:
            logger.info('starting to calculate salary for employee #%(employee)d, year %(year)d, month %(month)d',
                        {'employee':self.employee_id, 'year':self.year, 'month':self.month})
            
            terms = self.employee.employment_terms

            if not terms:
                self.remarks = u'לעובד לא הוגדרו תנאי העסקה!'
                logger.warn('could not load employment terms.')
                return

            self.commissions = 0
            self.safety_net = self.sales_count == 0 and terms.safety or None

            if self.year == self.employee.work_start.year and self.month == self.employee.work_start.month:
                self.base = float(30 - self.employee.work_start.day) / 30 * terms.salary_base 
            else:
                self.base = terms.salary_base
    
            logger.debug('salary base : %s', self.base)
    
            for project, sales in self.sales.items():
                project_id = project.id

                # load commission for project
                q = self.employee.commissions.filter(project__id=project_id)

                if q.count() == 0: 
                    logger.warning('no employee commission is defined for project #%d, continuing', project_id)
                    continue

                epc = q[0]

                # validate commission is active
                if not epc.is_active(date(self.year, self.month,1)) or not sales or len(sales) == 0:
                    self.project_commission[epc.project] = 0
                    logger.warning('no employee commission for project #%(project)d is not active - start: %(start)s end: %(end)s, continuing',
                        {'project':project_id, 'start':epc.start_date, 'end':epc.end_date})
                    continue
                
                # calculate commission for project
                amount = epc.calc(sales, self)

                logger.info('employee commission for project #%(project)d is %(amount)d', 
                    {'project':project_id, 'amount':amount})
                
                self.project_commission[epc.project] = amount
                self.commissions += amount

                if terms.salary_net == False:
                    self.pdf_remarks = u'ברוטו, כמה נטו בעדכון הוצאות'

                for sale in sales:
                    sale.employee_paid = True
                    sale.save() 
        except:
            logger.exception('exception while trying to calculate salary for employee #%(employee)d, year %(year)d, month %(month)d',
                             {'employee':self.employee_id, 'year':self.year, 'month':self.month})
        else:
            logger.info('succeeded to calculate salary for employee #%(employee)d, year %(year)d, month %(month)d',
                {'employee':self.employee_id, 'year':self.year, 'month':self.month})
            
    def get_absolute_url(self):
        return '/salaries/%s' % self.id
    class Meta:
        db_table = 'EmployeeSalary'
        permissions = (('season_employeesalary','Season employee salary'),)

class EPCommission(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.PROTECT, related_name='commissions', editable=False)
    project = models.ForeignKey('Project', on_delete=models.PROTECT, related_name= 'epcommission', editable=False)
    start_date = models.DateField(gettext('start_date'))
    end_date = models.DateField(gettext('end_date'), null=True, blank=True)
    max = models.FloatField(gettext('max_commission'), null=True, blank=True)
    c_var = models.ForeignKey('CVar', on_delete=models.PROTECT, null=True, editable=False)
    c_var_precentage = models.ForeignKey('CVarPrecentage', on_delete=models.PROTECT, null=True, editable=False)
    c_by_price = models.ForeignKey('CByPrice', on_delete=models.PROTECT, null= True, editable=False)
    b_house_type = models.ForeignKey('BHouseType', on_delete=models.PROTECT, null=True, editable=False)
    b_discount_save = models.ForeignKey('BDiscountSave', on_delete=models.PROTECT, null=True, editable=False)
    b_discount_save_precentage = models.ForeignKey('BDiscountSavePrecentage', on_delete=models.PROTECT, null=True, editable=False)
    b_sale_rate = models.ForeignKey('BSaleRate', on_delete=models.PROTECT, null=True, editable=False)
    def is_active(self, date=date.today()):
        if not self.end_date:
            return True
        if date > self.start_date and date < self.end_date:
            return True
        return False 
    def calc(self, sales, salary):
        try:
            logger = logging.getLogger('salary')
            logger.info('starting to calculate commission for employee #%(employee)d project #%(project)d. %(sale_count)d sales.', 
                        {'employee':self.employee_id, 'project':self.project_id,'sale_count':len(sales)})
            
            restore_date = date(salary.year, salary.month , 1)
            logger.debug('restore_date: %s' % restore_date)
            
            # commission amount for each sale
            dic = {}
            
            for c in ['c_var', 'c_by_price', 'b_house_type', 'b_discount_save']:
                commission = getattr(self,c)

                if not commission: 
                    # delete and previous commission detail
                    for sale in sales:
                        sale.commission_details \
                            .filter(employee_salary=salary, commission=c) \
                            .delete()
                    continue

                commission = common.restore_object(commission, restore_date)
                
                logger.info('calculating commission : %s' % c)
                
                amounts = commission.calc(sales)

                for sale in amounts:
                    amount = amounts[sale]

                    if amount == 0: 
                        logger.warning('sale #%s has 0 commission!' % sale.id)

                    # update commission detail
                    scd, new = sale.commission_details.get_or_create(employee_salary=salary, commission=c)

                    scd.value = amount
                    scd.save()

                    # update dic
                    dic[sale] = dic[sale] + amount if sale in dic else amount

            for c in ['c_var_precentage', 'b_discount_save_precentage']:
                commission = getattr(self,c)

                if not commission: 
                    # delete and previous commission detail
                    for sale in sales:
                        sale.commission_details \
                            .filter(employee_salary=salary, commission=c) \
                            .delete()
                    continue

                commission = common.restore_object(commission, restore_date)
                
                logger.info('calculating commission : %s' % c)
                
                precentages = commission.calc(sales)

                for sale in precentages:
                    if precentages[sale] == 0: 
                        logger.warning('sale #%d has 0 commission!' % sale.id)

                    if self.max and precentages[sale] > self.max:
                        logger.warning('sale #%(id)d commission %(commission)s is higher than max commission %(max_commission).2f',
                                       {'id':sale.id, 'commission':precentages[sale], 'max_commission':self.max})
                        precentages[sale] = self.max

                    amount = precentages[sale] * sale.employee_price(self.employee) / 100
                    
                    # update commission detail
                    scd, new = sale.commission_details.get_or_create(employee_salary=salary, commission=c)
                    scd.value = amount
                    scd.save()

                    # update dic
                    dic[sale] = dic[sale] + amount if sale in dic else amount

            # sum up amounts from all sales
            total_amount = sum(dic[sale] for sale in dic)

            for c in ['b_sale_rate']:
                commission = getattr(self,c)
                if not commission: 
                    continue
                
                logger.info('calculating commission : %s' % c)
                
                commission = common.restore_object(commission, restore_date)
                amount = commission.calc(sales)
                if amount == 0: 
                    logger.warning('sales has 0 commission!')
                    continue
                total_amount = total_amount + amount
                scd = SaleCommissionDetail(employee_salary = salary, value = amount, commission = c)
                scd.save()
            return total_amount
        except:
            logger.exception('exception during calculate commission for employee #%(employee)d project #%(project)d.', 
                             {'employee':self.employee_id, 'project':self.project_id})
            return 0
        else:
            logger.info('finished to calculate commission for employee #%(employee)d project #%(project)d. %(sale_count)d sales.', 
                        {'employee':self.employee_id, 'project':self.project_id,'sale_count':len(sales)})
        
    def get_absolute_url(self):
        return '/epcommission/%s' % self.id
    class Meta:
        db_table = 'EPCommission'

class CAmount(models.Model):
    c_var = models.ForeignKey('CVar', on_delete=models.PROTECT, related_name='amounts', editable=False)
    amount = models.PositiveIntegerField(gettext('commission amount'))
    index = models.PositiveSmallIntegerField(editable=False)

    def save(self, *args, **kw):
        if not self.id:
            if self.c_var.amounts.count() > 0:
                latest = self.c_var.amounts.latest()
                self.index = latest.index + 1
            else:
                self.index = 1
        super(CAmount, self).save(*args, **kw)

    class Meta:
        ordering = ['index']
        get_latest_by = 'index'
        unique_together = ('index','c_var')
        db_table = 'ECAmount'
        
class CPrecentage(models.Model):
    c_var_precentage = models.ForeignKey('CVarPrecentage', on_delete=models.PROTECT, related_name='precentages', editable=False)
    precentage = models.FloatField(gettext('commission precentage'))
    index = models.PositiveSmallIntegerField(editable=False)
    
    def save(self, *args, **kw):
        if not self.id:
            if self.c_var_precentage.precentages.count() > 0:
                latest = self.c_var_precentage.precentages.latest()
                self.index = latest.index + 1
            else:
                self.index = 1
        super(CPrecentage, self).save(*args, **kw)
    
    class Meta:
        ordering = ['index']
        get_latest_by = 'index'
        unique_together = ('index','c_var_precentage')
        db_table = 'CPrecentage'

class CPriceAmount(models.Model):
    c_by_price = models.ForeignKey('CByPrice', on_delete=models.PROTECT, related_name='price_amounts', editable=False)
    price = models.PositiveIntegerField(gettext('price'))
    amount = models.PositiveIntegerField(gettext('commission amount'))
    
    class Meta:
        ordering = ['price']
        get_latest_by = 'price'
        unique_together = ('price','c_by_price')
        db_table = 'CPriceAmount'
    
class HouseTypeBonus(models.Model):
    bonus = models.ForeignKey('BHouseType', on_delete=models.PROTECT, related_name ='bonuses')
    type = models.ForeignKey('HouseType', on_delete=models.PROTECT, verbose_name=gettext('house_type'))
    amount = models.PositiveIntegerField(gettext('amount'))
    class Meta:
        db_table = 'HouseTypeBonus'
        unique_together = ('bonus','type')
        
class SaleRateBonus(models.Model):
    b_sale_rate = models.ForeignKey('BSaleRate', on_delete=models.PROTECT, related_name='bonuses')
    house_count = models.PositiveSmallIntegerField(gettext('house count'))
    amount = models.PositiveIntegerField(gettext('commission amount'))
    class Meta:
        ordering = ['house_count']
        db_table = 'SaleRateBonus'
    
class CVar(models.Model):
    is_retro = models.BooleanField(gettext('retroactive'))
    def calc(self,sales):
        dic = {}
        amounts = dict(self.amounts.values_list('index','amount'))
        last_index = self.amounts.latest().index
        
        if self.is_retro:
            index = min((len(sales), last_index))
            amount = amounts[index]

            for s in sales:
                dic[s] = amount
        else:
            i = 1
            for s in sales:
                index = min((i, last_index))
                dic[s] = amounts[index]
                i += 1
        return dic

    class Meta:
        db_table = 'CVar'
        
class CVarPrecentage(models.Model):
    is_retro = models.BooleanField(gettext('retroactive'))
    start_retro = models.PositiveSmallIntegerField(gettext('retroactive_start'),null=True, blank=True, default=1)
    def calc(self, sales):        
        dic = {}
        precentages = dict(self.precentages.values_list('index','precentage'))
        last_index = self.precentages.latest().index
        
        if self.is_retro and len(sales) >= self.start_retro:
            index = min((len(sales), last_index))
            precentage = precentages[index]

            for s in sales:
                dic[s] = precentage
        else:
            i = 1
            for s in sales:
                index = min((i, last_index))
                dic[s] = precentages[index]
                i += 1
        return dic
    
    class Meta:
        db_table = 'CVarPrecentage'
 
class CVarPrecentageFixed(models.Model):
    is_retro = models.BooleanField(gettext('retroactive'))
    first_count = models.PositiveSmallIntegerField(gettext('cvf first count'))
    first_precentage = models.FloatField(gettext('commission precentage'))
    step = models.FloatField(gettext('cvf step'))
    last_count = models.PositiveSmallIntegerField(gettext('cvf last count'), null=True, blank=True)
    last_precentage = models.FloatField(gettext('commission precentage'), null=True, blank=True)
    def calc(self, sales):
        if len(sales) == 0: return {}
        houses_remaning = len(sales)
        for h in sales[0].house.building.project.houses():
            if h.get_sale() == None and not h.is_sold:
                houses_remaning += 1
        dic = {}
        if self.is_retro and len(sales) > self.first_count:
            precentage = self.first_precentage + self.step * (len(sales) - self.first_count)
            for s in sales:
                if self.last_count and houses_remaning <= self.last_count:
                    dic[s] = self.last_precentage
                else:
                    dic[s] = precentage
                houses_remaning -= 1
        else:
            for s in sales[:self.first_count]:
                dic[s] = self.first_precentage
            if len(sales) <= self.first_count:
                return dic
            i = self.first_count + 1
            for s in sales[self.first_count+1:]:
                if self.last_count and houses_remaning <= self.last_count:
                    dic[s] = self.last_precentage
                else:
                    dic[s] = self.first_precentage + self.step * (i - self.first_count)
                houses_remaning -= 1
                i += 1
        return dic
    class Meta:
        db_table = 'CVarPrecentageFixed'

class CByPrice(models.Model):
    def calc(self, sales):
        dic = {}
        for s in sales:
            dic[s] = self.get_amount(s.price_taxed)
        return dic
    
    def get_amount(self, price):
        query = self.price_amounts.filter(price__gte = price)
        if query.count() == 0:
            raise CommissionException
        return query[0].amount

    class Meta:
        db_table = 'CByPrice'

class CZilber(models.Model):
    Cycle = 4
    base = models.FloatField(gettext('commission_base'))
    b_discount = models.FloatField(gettext('b_discount'))
    b_sale_rate = models.FloatField(gettext('b_sale_rate'))
    b_sale_rate_max = models.FloatField(gettext('max_commission'))
    base_madad = models.FloatField(gettext('madad_base'))
    third_start = models.DateField(gettext('third_start'))
    
    def calc_bonus(self, month, sales, d):
        logger = logging.getLogger('commission.czilber')
            
        prices_date = date(month.month == 12 and month.year+1 or month.year, month.month % 12 + 1, 1)
        logger.debug('%(vals)s', {'vals': {'prices_date':prices_date}})
        
        total_zdb = 0
            
        for s in sales:
            if not self.base_madad:
                continue
            
            doh0prices = s.house.versions.doh0().filter(date__lte = prices_date)
            if doh0prices.count() == 0: 
                logger.warning('skipping c_zilber_discount calc for sale #%(id)s. no doh0 prices', {'id':s.id})
                continue
            latest_doh0price = doh0prices.latest().price
            
            # calc the memudad price
            current_madad = max(s.commission_madad_bi or d.get_madad(), self.base_madad)
            memudad_multiplier = ((current_madad / self.base_madad) - 1) * 0.6 + 1
            memudad = latest_doh0price * memudad_multiplier
            
            zdb = (s.price_final - memudad) * self.b_discount

            commissions = {
                'c_zilber_discount': zdb,
                'latest_doh0price': latest_doh0price,
                'memudad': memudad,
                'current_madad': current_madad,
            }

            # overwrite project commission details (not attached to a salary)
            for scd in s.commission_details.filter(employee_salary=None):
                commission = scd.commission
                
                if commission in commissions:
                    # update commission
                    scd.value = commissions[commission]
                    scd.save()
                else:
                    # delete any extra commission
                    scd.delete()
            
            total_zdb += zdb
              
            logger.debug('sale #%(id)s c_zilber_discount calc values: %(vals)s',
                         {'id':s.id, 'vals':{'latest_doh0price':latest_doh0price, 'current_madad':current_madad, 
                                             'memudad_multiplier':memudad_multiplier, 'memudad':memudad,'zdb':zdb}})
        return total_zdb

    def calc_adds(self, base, cycle_sales):
        logger = logging.getLogger('commission.czilber')
        prev_adds = 0
        
        for sale in cycle_sales:
            if base == sale.pc_base:
                logger.debug('sale #%(id)d skipping zilber add', sale.id)
                continue
                
            # store the new base commission value in the sale commission details.
            # also updates the commissions for sales from previous month in the cycle. old values will be avaliable
            # using the reversion framework
            for commission in ['c_zilber_base','final']:
                scd, new = sale.commission_details.get_or_create(commission = commission, employee_salary = None)
                scd.value = base
                scd.save()
            
            # get the sale_add ammount      
            sale_add = (base - sale.pc_base) * sale.price_final / 100
            prev_adds += sale_add
        
            logger.debug('sale #%(id)d adds calc values: %(vals)s', 
                {'id':sale.id, 'vals': {'base':base,'sale_add':sale_add}})

        return prev_adds

    def calc(self, month):
        '''
        month is datetime
        '''
        try:
            from Management.enrichers.demand import set_demand_sale_fields, set_demand_diff_fields

            logger = logging.getLogger('commission.czilber')
            
            projectcommission = self.projectcommission.get()
            project = projectcommission.project

            d = Demand.objects.get(project = project, year = month.year, month = month.month)
            
            # enrich demand object
            set_demand_sale_fields([d], month.year, month.month, month.year, month.month)
            set_demand_diff_fields([d])

            if getattr(d, 'var_diff', None) != None: 
                d.var_diff.delete()
            if getattr(d, 'bonus_diff', None) != None: 
                d.bonus_diff.delete()
            
            sales = d.sales_list
    
            logger.info('sales count: %d', len(sales))
            
            for sale in sales:
                sale.price_final = sale.project_price()
                sale.save()
                
                logger.debug('sale #%(id)s price_final = %(value)s', {'id':sale.id, 'value':sale.price_final})
            
            # split 'sales' to 'sales' and 'excluded_sales'
            excluded_sales = [sale for sale in sales if sale.commission_include == False]
            sales = set([sale for sale in sales if sale.commission_include == True])
            
            # reset commissions for excluded sales
            for sale in excluded_sales:
                for scd in sale.commission_details:
                    if scd.commission in ['c_zilber_base', 'final']:
                        scd.value = 0
                        scd.save()
                        
                logger.warning('skipping sale #%d because commission_include=False', sale.id)
                                
            self.calc_bonus(month, sales, d)

            logger.info('starting to calculate ziber adds')
            
            demand = d
            demands = [demand]
            while demand.zilber_cycle_index() > 1:
                demand = demand.get_previous_demand()
                demands.append(demand)
            
            # enrich all demands in cycle
            set_demand_sale_fields(
                demands,
                demands[-1].year, demands[-1].month,
                demands[0].year, demands[0].month)

            cycle_sales = []
            for demand in demands:
                cycle_sales.extend(demand.sales_list)
            
            excluded_sales = [sale for sale in cycle_sales if sale.commission_include == False]
            cycle_sales = set([sale for sale in cycle_sales if sale.commission_include == True])
            
            if len(excluded_sales):
                logger.warning('excluding %d sales from zilber adds calc', len(excluded_sales))
        
            base = self.base + self.b_sale_rate * (len(cycle_sales) - 1)
            
            if base > self.b_sale_rate_max:
                logger.info('base commission %(base)s exceeded max commisison %(max)s',
                    {'base':base, 'max':self.b_sale_rate_max})
                base = self.b_sale_rate_max
            
            prev_adds = self.calc_adds(base, cycle_sales)
            
            if d.include_zilber_bonus():
                if prev_adds:
                    d.diffs.create(type=u'משתנה', reason=u'הפרשי קצב מכירות (נספח א)', amount=round(prev_adds))
                bonus = sum([sale.zdb for sale in cycle_sales])
                if bonus:
                    d.diffs.create(type=u'בונוס', reason=u'בונוס חסכון בהנחה (נספח ב)', amount=round(bonus))
                    
                logger.debug('demand #%(id)d created bonus=%(bonus)d', {'id':d.id, 'bonus':bonus})
                
            logger.info('finished calculation for month %(month)d/%(year)d', {'month':month.month, 'year':month.year})
        except:
            logger.exception('error while calculating commissions for month %(month)d/%(year)d', {'month':month.month, 'year':month.year})
        
    class Meta:
        db_table = 'CZilber'

class BDiscountSave(models.Model):
    precentage_bonus = models.PositiveIntegerField(gettext('precentage_bonus'))
    max_for_bonus = models.FloatField(gettext('max_bonus'), blank=True, null=True)
    def calc(self, sales):
        dic = {}
        for s in sales:
            saved = min(s.saved_discount, self.max_for_bonus or 0)
            dic[s] = saved * self.precentage_bonus
        return dic
    class Meta:
        db_table = 'BDiscountSave'
        
class BDiscountSavePrecentage(models.Model):
    precentage_bonus = models.FloatField(gettext('precentage_bonus'))
    max_for_bonus = models.FloatField(gettext('max_bonus'), blank=True, null=True)
    def calc(self, sales):
        dic = {}
        for s in sales:
            if self.max_for_bonus is None:
                saved = s.saved_discount
            else:
                saved = min(s.saved_discount, self.max_for_bonus)
            dic[s] = saved * self.precentage_bonus
        return dic
    class Meta:
        db_table = 'BDiscountSavePrecentage'

class BHouseType(models.Model):
    def calc(self, sales):
        dic={}
        for s in sales:
            b = self.bonuses.filter(type = s.house.type)
            dic[s] = b.count() == 1 and b[0].amount or 0
        return dic
    class Meta:
        db_table = 'BHouseType'    
        
class BSaleRate(models.Model):
    def calc(self,sales):
        c = len(sales)
        for b in self.bonuses.reverse():
            if c >= b.house_count:
                return b.amount
        return 0
    class Meta:
        db_table = 'BSaleRate'
    
class ProjectCommission(models.Model):
    project = models.ForeignKey('Project', on_delete=models.PROTECT, related_name= 'commissions', editable=False)
    c_var_precentage = models.ForeignKey('CVarPrecentage', on_delete=models.PROTECT, related_name= 'projectcommission', null=True, editable=False)
    c_var_precentage_fixed = models.ForeignKey('CVarPrecentageFixed', on_delete=models.PROTECT, related_name= 'projectcommission', null=True, editable=False)
    c_zilber = models.ForeignKey('CZilber', on_delete=models.PROTECT, related_name='projectcommission', null=True, editable=False)
    b_discount_save_precentage = models.ForeignKey('BDiscountSavePrecentage', on_delete=models.PROTECT, related_name= 'projectcommission', null=True, editable=False)
   
    add_amount = models.PositiveIntegerField(gettext('add_amount'), null=True, blank=True)
    add_type = models.CharField(gettext('add_type'), max_length = 20, null=True, blank=True)
    registration_amount = models.PositiveIntegerField(gettext('registration_amount'), null=True, blank=True)
    deduct_registration = models.NullBooleanField(gettext('deduct_registration_from_price_no_lawyer'), blank=True,
                                                  choices = ((None,'לא משנה'),
                                                             (False, 'לא'),
                                                             (True, 'כן'))
                                                  )
    include_tax = models.NullBooleanField(gettext('commission_include_tax'), blank=True, default=True)
    include_lawyer = models.NullBooleanField(gettext('commission_include_lawyer'), blank=True,
                                             choices = ((None,'לא משנה'),
                                                        (False, 'לא'),
                                                        (True, 'כן'))
                                             )
    commission_by_signups = models.BooleanField(gettext('commission_by_signups'), blank=True, default=False)
    max = models.FloatField(gettext('max_commission'), null=True, blank=True)
    agreement = models.FileField(gettext('agreement'), upload_to='files', null=True, blank=True)
    remarks = models.TextField(gettext('commission_remarks'), null=True, blank=True)
    
    def calc_by_signups(self, demand):
        logger = logging.getLogger('commission')
            
        for (m, y) in demand.get_signup_months():
            # get sales that were signed up for specific month, not including future sales.
            max_contractor_pay = date(demand.month==12 and demand.year+1 or demand.year, demand.month==12 and 1 or demand.month+1,1) 
            q = models.Q(contractor_pay_year = max_contractor_pay.year, contractor_pay_month__lt = max_contractor_pay.month) | \
                models.Q(contractor_pay_year__lt = max_contractor_pay.year)
            
            subSales = Sale.objects.filter(q, house__signups__date__year=y,
                                           house__signups__date__month=m,
                                           house__signups__cancel=None,
                                           house__building__project = demand.project,
                                           commission_include=True)
            subSales = subSales.order_by('house__signups__date')
            
            logger.info('calculating affected sales %(sale_ids)d for month %(month)d/%(year)d',
                        {'sale_ids':[sale.id for sale in subSales], 'month':m,'year':y})
                        
            # send these sales to regular processing
            self.calc(subSales)

        bonus = 0
        for subSales in demand.get_affected_sales().values():
            for s in subSales:
                if not s.commission_include: 
                    logger.info('skipping sale #%d - commission_include=False', s.id)
                    continue
                signup = s.house.get_signup()
                if not signup: 
                    logger.warning('skipping sale #%d - no signup', s.id)
                    continue
                # get the finish date when the demand for the month the signup 
                # were made we use it to find out what was the commission at
                # that time
                if not s.actual_demand or not s.actual_demand.finish_date:
                    logger.warning('skipping sale #%d - actual_demand=None or actual_demand.finish_date=None', s.id)
                    continue
                q = s.project_commission_details.filter(commission='final')
                if q.count()==0:
                    logger.warning('skipping sale #%d - no final commission', s.id)
                    continue
                s.restore_date = demand.get_previous_demand().finish_date
                diff = (q[0].value - s.c_final) * s.price_final / 100
                
                logger.debug('sale #%(id)d bonus calc values: %(vals)s',
                             {'id': s.id,
                              'vals': {'diff':diff,
                                       'q[0].value':q[0].value,
                                       's.c_final':s.c_final,
                                       's.price_final':s.price_final}
                              })
                
                bonus += int(diff)
        if bonus > 0:
            if demand.bonus_diff:
                demand.bonus_diff.amount = bonus
                demand.bonus_diff.save()
            else:
                demand.diffs.create(type=u'בונוס', reason = u'הפרשי עמלה (ניספח א)', amount = bonus)
        return
    
    def calc(self, sales = (), demand = None, restore_date = date.today()):
        try:
            logger = logging.getLogger('commission')
            
            if demand:
                sales = demand.sales_list
                logger.info('starting to calculate commission for project #%(project)d: %(month)s-%(year)d %(sale_count)d sales.', 
                            {'project':self.project_id,'sale_count':len(sales),'month':demand.month, 'year':demand.year})
            
            if len(sales) == 0: 
                return

            if self.commission_by_signups and demand:
                self.calc_by_signups(demand)
            
            if getattr(self, 'c_zilber') != None:
                month = date(demand.year, demand.month, 1)
                c_zilber = getattr(self, 'c_zilber')
                c_zilber = common.restore_object(c_zilber, restore_date) 
                c_zilber.calc(month)
                return
            
            dic={}
            details={}
            for c in ['c_var_precentage','c_var_precentage_fixed','b_discount_save_precentage']:
                if getattr(self,c) == None:
                    # delete any previous commission details
                    for sale in sales:
                        sale.commission_details \
                            .filter(employee_salary=None) \
                            .delete()
                    continue
                
                commission = getattr(self,c)
                commission = common.restore_object(commission, restore_date)
                precentages = commission.calc(sales)

                for s in precentages:
                    if c in ['c_var_precentage', 'c_var_precentage_fixed'] and self.max and precentages[s] > self.max:
                        precentages[s] = self.max
                        logger.info('sale #%(id)d - %(commission)s (%(commission_value).3f) exceeded max commission %(max).3f',
                                    {'id':s.id, 'commission':c, 'commission_value':precentages[s], 'max':self.max})
    
                    dic[s] = s in dic and dic[s] + precentages[s] or precentages[s]
                    s_details = details.setdefault(s, {})
                    s_details[c] = precentages[s]
                    
            # enforce the maximum commission for all commissions sum
            if self.max:
                for sale in dic:
                    if dic[sale] > self.max:
                        dic[sale] = self.max
                        logger.info('sale #%(id)d - final commission (%(commission_value).3f) exceeded max commission %(max).3f',
                                    {'id':sale.id, 'commission_value':dic[sale], 'max':self.max})
                        
            for sale in details:
                for c, v in details[sale].items():
                    scd, new = sale.commission_details.get_or_create(employee_salary=None, commission=c)
                    scd.value = v
                    scd.save()
                    
                scd, new = sale.commission_details.get_or_create(employee_salary=None, commission='final')
                scd.value = dic[sale]
                scd.save()
                
                # set price_final
                sale.price_final = sale.project_price()
                sale.save()
                
                logger.debug('sale #%(id)d - price_final=%(price_final)d, details:%(details)s', 
                             {'id':sale.id, 'price_final':sale.price_final, 'details':details[sale]})
        except:
            logger.exception('exception during calculate commission for project #%d.', self.project_id)
        else:
            logger.info('finished to calculate commission for project #%d.', self.project_id)
            
    def get_absolute_url(self):
        return '/projectcommission/%s' % self.id
    class Meta:
        db_table = 'ProjectCommission'

class Invoice(models.Model):
    num = models.IntegerField(gettext('invoice_num'), unique=True, null=True, blank=True)
    creation_date = models.DateField(auto_now_add = True)
    date = models.DateField(gettext('invoice_date'))
    amount = models.IntegerField(gettext('amount'))
    remarks = models.TextField(gettext('remarks'), null=True,blank=True)
    offset = models.ForeignKey('InvoiceOffset', on_delete=models.PROTECT, editable=False, null=True)
    
    def get_absolute_url(self):
        return '/invoices/%s' % self.id
    def __str__(self):
        return u'חשבונית על סך %s ש"ח בתאריך %s' % (commaise(self.amount), self.date.strftime('%d/%m/%Y'))
    class Meta:
        db_table = 'Invoice'
        get_latest_by = 'creation_date'
        ordering = ['creation_date']

class InvoiceOffset(models.Model):
    date = models.DateField(gettext('date'))
    amount = models.IntegerField(gettext('amount'))
    reason = models.CharField(gettext('reason'), max_length=30)
    remarks = models.TextField(gettext('remarks'), null=True,blank=True)
    def get_absolute_url(self):
        return '/invoiceoffset/%s' % self.id
    class Meta:
        db_table = 'InvoiceOffset'
        
class PaymentType(models.Model):
    Cash, Check, BankTransfer, Other = 1,2,3,4
    name = models.CharField(max_length=20)
    def __str__(self):
        return str(self.name)  
    class Meta:
        db_table = 'PaymentType'

class Payment(models.Model):
    num = models.IntegerField(gettext('check_num'), null=True, blank=True)
    support_num = models.IntegerField(gettext('support_num'), null=True, blank=True)
    bank = models.CharField(gettext('bank'), max_length=40, null=True, blank=True)
    branch_num = models.PositiveSmallIntegerField(gettext('branch_num'), null=True, blank=True)
    payment_type = models.ForeignKey('PaymentType', on_delete=models.PROTECT, verbose_name=gettext('payment_type'))
    payment_date = models.DateField(gettext('payment_date'))
    creation_date = models.DateField(auto_now_add = True)
    amount = models.IntegerField(gettext('amount'))
    remarks = models.TextField(gettext('remarks'), null=True,blank=True)
    
    def __str__(self):
        return u'תשלום על סך %s ש"ח בתאריך %s' % (commaise(self.amount), self.payment_date.strftime('%d/%m/%Y'))
    def is_split(self):
        return self.demands.count() > 1
    def get_absolute_url(self):
        return '/payments/%s' % self.id
    class Meta:
        db_table = 'Payment'
        get_latest_by = 'creation_date'
        ordering = ['creation_date']


class DemandStatusType(models.Model):
    Feed, Closed, Sent, Finished = range(1,5)
    
    name = models.CharField(max_length=20)

    def __str__(self):
        return str(self.name)  
    
    class Meta:
        db_table = 'DemandStatusType'

class DemandStatus(models.Model):
    demand = models.ForeignKey('Demand', on_delete=models.PROTECT, related_name='statuses')
    date = models.DateTimeField(auto_now_add=True)
    type = models.ForeignKey('DemandStatusType', on_delete=models.PROTECT)
    
    def __str__(self):
        return self.type.name

    class Meta:
        db_table = 'DemandStatus'
        get_latest_by = 'date'

class DemandDiff(models.Model):
    demand = models.ForeignKey('Demand', on_delete=models.PROTECT, editable=False, related_name='diffs')
    type = models.CharField(gettext('diff_type'), max_length=30, help_text=u'קבועה, משתנה, בונוס, קיזוז או לבחירתך')
    reason = models.CharField(gettext('diff_reason'), max_length=30, null=True, blank=True)
    amount = models.FloatField(gettext('amount'))
    
    def __str__(self):
        return u'תוספת מסוג %s על סך %s ש"ח - %s' % (self.type, self.amount, self.reason)
    def get_absolute_url(self):
        return '/demanddiff/%s' % self.id
    class Meta:
        db_table = 'DemandDiff'
        unique_together = ('demand','type')
      
class Demand(models.Model):
    project = models.ForeignKey('Project', on_delete=models.PROTECT, related_name='demands', verbose_name = gettext('project'))
    month = models.PositiveSmallIntegerField(gettext('month'), choices=common.get_month_choices())
    year = models.PositiveSmallIntegerField(gettext('year'), choices=common.get_year_choices())
    sale_count = models.PositiveSmallIntegerField(gettext('sale_count'), default=0)
    remarks = models.TextField(gettext('remarks'), null=True,blank=True)
    is_finished = models.BooleanField(default=False, editable=False)
    reminders = models.ManyToManyField('Reminder', editable=False)
    force_fully_paid = models.BooleanField(editable=False, default=False)
    sales_commission = models.IntegerField(editable=False, default=0)

    invoices = models.ManyToManyField('Invoice',  related_name = 'demands', 
                                      editable=False, blank=True)
    payments = models.ManyToManyField('Payment',  related_name = 'demands', 
                                      editable=False, blank=True)
    not_yet_paid = models.IntegerField(editable=False, default=0)

    objects = DemandManager()
    
    def get_madad(self):
        from Indices.models import MadadBI
        q = MadadBI.objects.filter(year = self.year, month=self.month)
        return q.count() > 0 and q[0].value or MadadBI.objects.latest().value
    def zilber_cycle_index(self):
        commissions = self.project.commissions.get()
        start = commissions.c_zilber.third_start
        if (start.year == self.year and start.month > self.month) or self.year < start.year:
            return -1
        i = 1
        while start.year != self.year or start.month != self.month:
            start = date(start.month == 12 and start.year + 1 or start.year,
                         start.month == 12 and 1 or start.month + 1, 1)
            i += 1
        return (i % CZilber.Cycle) or CZilber.Cycle
    def get_previous_demand(self):
        try:
            return Demand.objects.get(project = self.project,
                                      year = self.month == 1 and self.year - 1 or self.year,
                                      month = self.month == 1 and 12 or self.month - 1)
        except Demand.DoesNotExist:
            return None
    def get_next_demand(self):
        try:
            return Demand.objects.get(project = self.project,
                                      year = self.month == 12 and self.year + 1 or self.year,
                                      month = self.month == 12 and 1 or self.month + 1)
        except Demand.DoesNotExist:
            return None
    def get_affected_sales(self):
        '''
        get sales from last months, affected by this month's calculation,
        excluding sales from current demand. key is (month, year) and value is the sales
        '''
        dic = {}
        commissions = self.project.commissions.get()
        if not commissions.commission_by_signups:
            return dic
        for m,y in self.get_signup_months():
            q = models.Q(contractor_pay_year = self.year, contractor_pay_month__gte = self.month) | models.Q(contractor_pay_year__gt = self.year)
            dic[(m,y)] = Sale.objects.filter(house__signups__date__year=y,
                                             house__signups__date__month=m,
                                             house__signups__cancel=None,
                                             demand__project__id = self.project.id,
                                             salecancel=None
                        ).exclude(q)
        return dic
    def get_signup_months(self):
        months = {}
        for sale in self.sales_list:
            signup = sale.house.get_signup()
            if not signup:
                continue
            key = (signup.date.month, signup.date.year)
            months.setdefault(key, 0)
            months[key] += 1
        return months
    def include_zilber_bonus(self):
        return self.zilber_cycle_index() == CZilber.Cycle
    def get_absolute_url(self):
        return '/demands/%s' % self.id
    def get_salaries(self):
        s = []
        for e in self.project.employees.all():
            s.append(e.salaries.get(year = self.year, month = self.month))
        return s
    @property
    def was_sent(self):
        return self.statuses.filter(type__id__in = [DemandStatusType.Sent, DemandStatusType.Finished]).count() > 0
    @property
    @cache_method
    def finish_date(self):
        query = self.statuses.filter(type__id = DemandStatusType.Finished)
        return query.count() > 0 and query.latest().date or None
    def _get_sales(self):
        return Sale.objects.filter(contractor_pay_year = self.year, contractor_pay_month = self.month,
                                house__building__project = self.project)
    @cache_method
    def get_pricemodsales(self):
        return self._get_sales().exclude(salepricemod=None)
    @cache_method
    def get_housemodsales(self):
        return self._get_sales().exclude(salehousemod=None)
    def get_presales(self):
        return self.sales.exclude(salepre=None)
    def get_rejectedsales(self):
        return self.sales.exclude(salereject=None)
    @cache_method
    def get_canceledsales(self):
        return self._get_sales().exclude(salecancel=None)
    @cache_method
    def get_excluded_sales(self):
        q = models.Q(commission_include=False) | models.Q(salecancel__isnull=False)
        query = self._get_sales().filter(q)
        commissions = self.project.commissions.get()
        if commissions.commission_by_signups:
            query = query.order_by('house__signups__date')
        return query
        
    def calc_sales_commission(self):
        logger = logging.getLogger('commission')
        logger.info('calculaion commissions for demand #%(demand_id)d - project_id:%(project_id)d,month:%(month)d,year:%(year)d',
                    {'demand_id':self.id,'project_id':self.project_id,'month':self.month, 'year':self.year})
        
        project_commissions = self.project.commissions.get()

        add_amount = project_commissions.add_amount
        
        # check if fixed add amount has changed
        if add_amount:
            fixed_diff = self.fixed_diff
            if fixed_diff:
                if add_amount != fixed_diff.amount:
                    logger.info('resetting fixed_diff.amount from value %(old_amount)s to %(new_amount)s',
                                {'old_amount':fixed_diff.amount, 'new_amount':add_amount})
                    fixed_diff.amount = add_amount
                    fixed_diff.save()
            else:
                # add amount was proboably added after the demand was created
                self.diffs.create(type=u'קבועה', amount = add_amount, reason = project_commissions.add_type)
        
        project_commissions.calc(demand = self, restore_date = date(self.year, self.month, 1))
        
        # sum 'c_final_worth' for each sale
        self.sales_commission = sum([sale.c_final_worth for sale in self.sales_list])
        
        self.save()

    def feed(self):
        self.statuses.create(type= DemandStatusType.objects.get(pk=DemandStatusType.Feed)).save()
    def send(self):
        self.statuses.create(type= DemandStatusType.objects.get(pk=DemandStatusType.Sent)).save()
    def close(self):
        self.statuses.create(type= DemandStatusType.objects.get(pk=DemandStatusType.Closed)).save()
    def finish(self):
        self.statuses.create(type= DemandStatusType.objects.get(pk=DemandStatusType.Finished)).save()
        self.is_finished = True
        self.save()
    def __str__(self):
        return u'דרישה לתשלום לפרוייקט %s בגיו חודש %s' % (self.project, '%s-%s' % (self.month, self.year))
    class Meta:
        db_table='Demand'
        ordering = ['year','month','project']
        get_latest_by = 'month'
        unique_together = ('project', 'month', 'year')
        permissions = (('list_demand', 'Can list demands'),('demand_pdf', 'Demand PDF'), ('demands_pdf', 'Demands PDF'),
                       ('demand_season', 'Demand Season'), ('demand_season_pdf', 'Demand Season PDF'), 
                       ('demand_remarks', 'Demand Remarks'), ('demand_sale_count', 'Demand Sale Count'),
                       ('demand_invoices', 'Demand Invoices'), ('demand_payments', 'Demand Payments'),
                       ('season_income', 'Season Income'), ('demand_force_fully_paid', 'Demand Force Fully Paid'),
                       ('demand_followup', 'Demand followup'), ('demand_pay_balance', 'Demand pay balance'), 
                       ('demand_followup_pdf', 'Demand followup PDF'))

class SignupCancel(models.Model):
    date = models.DateField(gettext('cancel_date'))
    was_signed = models.BooleanField(gettext('was_signed_cancel_form'), choices = Boolean)
    was_fee = models.BooleanField(gettext('was_fee'), choices = Boolean)
    reason = models.TextField(gettext('cancel_reason'), null=True, blank=True)
    class Meta:
        db_table='SignupCancel'
        
class Signup(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.PROTECT, related_name = 'signups', verbose_name=gettext('employee'),
                                 null=True, blank=True)
    house = models.ForeignKey('House', on_delete=models.PROTECT, related_name = 'signups', verbose_name=gettext('house'))
    date = models.DateField(gettext('signup_date'))
    clients = models.TextField(gettext('clients'))
    clients_address = models.TextField(gettext('clients_address'), null=True)
    clients_phone = models.TextField(gettext('phone'))
    sale_date = models.DateField(gettext('predicted_sale_date'))
    price = models.IntegerField(gettext('signup_price'))
    price_include_lawyer = models.BooleanField(gettext('include_lawyer'), choices = Boolean)
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)
    cancel = models.ForeignKey('SignupCancel', on_delete=models.PROTECT, related_name = 'signup', null=True, editable=False)
    def get_absolute_url(self):
        return '/signups/%s' % self.id
    class Meta:
        ordering = ['date']
        db_table = 'Signup'
        verbose_name = gettext('signup')
        get_latest_by = 'date'

class NHPay(models.Model):
    nhsaleside = models.ForeignKey('NHSaleSide', on_delete=models.PROTECT, editable=False, related_name='pays')
    employee = models.ForeignKey('EmployeeBase', on_delete=models.PROTECT, editable=False, related_name='nhpays', 
                                 null=True)
    lawyer = models.ForeignKey('Lawyer', on_delete=models.PROTECT, editable=False, related_name='nhpays', 
                               null=True)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    amount = models.FloatField(gettext('amount'))
    class Meta:
        db_table='NHPay'

class Lawyer(Person):
    phone = models.CharField(gettext('phone'), max_length=10, null=True, blank=True)
    def get_absolute_url(self):
        return '/lawyers/%s' % self.id
    class Meta:
        db_table='Lawyer'

class SaleType(models.Model):
    SaleSeller, SaleBuyer, RentRenter, RentRentee = range(1,5)
    name = models.CharField(max_length=20, unique=True)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table='SaleType'

class NHSaleSide(models.Model):
    nhsale = models.ForeignKey('NHSale', on_delete=models.PROTECT, editable=False)
    sale_type = models.ForeignKey('SaleType', on_delete=models.PROTECT, verbose_name=gettext('action_type'))
    name1 = models.CharField(gettext('name'), max_length=20)
    name2 = models.CharField(gettext('name'), max_length=20, null=True, blank=True)
    phone1 = models.CharField(gettext('phone'), max_length=20)
    phone2 = models.CharField(gettext('phone'), max_length=20, null=True, blank=True)
    address = models.CharField(gettext('address'), max_length=40)
    employee1 = models.ForeignKey('NHEmployee', on_delete=models.PROTECT, verbose_name=gettext('advisor'), related_name='nhsaleside1s')
    employee1_commission = models.FloatField(gettext('commission_precent'))
    employee2 = models.ForeignKey('NHEmployee', on_delete=models.PROTECT, verbose_name=gettext('advisor'), related_name='nhsaleside2s', null=True, 
                                  blank=True)
    employee2_commission = models.FloatField(gettext('commission_precent'), null=True, blank=True)
    employee3 = models.ForeignKey('NHEmployee', on_delete=models.PROTECT, verbose_name=gettext('advisor'), related_name='nhsaleside3s', null=True, 
                                  blank=True)
    employee3_commission = models.FloatField(gettext('commission_precent'), null=True, blank=True)
    director = models.ForeignKey('EmployeeBase', on_delete=models.PROTECT, verbose_name=gettext('director'), related_name='nhsaleside_director', 
                                null=True, blank=True)    
    director_commission = models.FloatField(gettext('commission_precent'), null=True, blank=True)
    signing_advisor = models.ForeignKey('NHEmployee', on_delete=models.PROTECT, verbose_name=gettext('signing_advisor'), related_name='nhsaleside_signer')
    lawyer1 = models.ForeignKey('Lawyer', on_delete=models.PROTECT, verbose_name=gettext('lawyer'), related_name='nhsaleside1s', 
                                null=True, blank=True)
    lawyer2 = models.ForeignKey('Lawyer', on_delete=models.PROTECT, verbose_name=gettext('lawyer'), related_name='nhsaleside2s', 
                                null=True, blank=True)
    signed_commission = models.FloatField(gettext('signed_commission'))
    actual_commission = models.FloatField(gettext('actual_commission'))
    income = models.IntegerField(gettext('return_worth'), blank=True)
    voucher_num = models.IntegerField(gettext('voucher_num'))
    voucher_date = models.DateField(gettext('voucher_date'))
    temp_receipt_num = models.IntegerField(gettext('temp_receipt_num'))
    employee_remarks = models.TextField(gettext('employee_remarks'), null=True, blank=True)
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)
    invoices = models.ManyToManyField('Invoice', editable=False)
    payments = models.ManyToManyField('Payment', editable=False)
    def __init__(self, *args, **kw):
        models.Model.__init__(self, *args, **kw)
        self.include_tax = True
    @property
    def employee1_pay(self):
        if self.employee1_commission == None or self.employee1 == None:
            return None
        amount = self.net_income * self.employee1_commission / 100
        terms = self.employee1.employment_terms
        if not terms: return amount
        nhmonth = self.nhsale.nhmonth
        tax = Tax.objects.filter(date__lte=date(nhmonth.year, nhmonth.month,1)).latest().value / 100 + 1
        if not self.include_tax and terms.include_tax:
            amount = amount / tax
        return amount
    @property
    def employee2_pay(self):
        if self.employee2_commission == None or self.employee2 == None:
            return None
        amount = self.net_income * self.employee2_commission / 100
        terms = self.employee2.employment_terms
        if not terms: return amount
        nhmonth = self.nhsale.nhmonth
        tax = Tax.objects.filter(date__lte=date(nhmonth.year, nhmonth.month,1)).latest().value / 100 + 1
        if not self.include_tax and terms.include_tax:
            amount = amount / tax
        return amount
    @property
    def employee3_pay(self):
        if self.employee3_commission == None or self.employee3 == None:
            return None
        amount = self.net_income * self.employee3_commission / 100
        terms = self.employee3.employment_terms
        if not terms: return amount
        nhmonth = self.nhsale.nhmonth
        tax = Tax.objects.filter(date__lte=date(nhmonth.year, nhmonth.month,1)).latest().value / 100 + 1
        if not self.include_tax and terms.include_tax:
            amount = amount / tax
        return amount
    @property
    def director_pay(self):
        if self.director_commission == None or self.director == None:
            return None
        amount =  self.net_income * self.director_commission / 100
        terms = self.director.employment_terms
        if not terms: return amount
        nhmonth = self.nhsale.nhmonth
        tax = Tax.objects.filter(date__lte=date(nhmonth.year, nhmonth.month,1)).latest().value / 100 + 1
        if not self.include_tax and terms.include_tax:
            amount = amount / tax
        return amount
    @property
    def lawyer1_pays(self):
        nhpays = self.lawyer1.nhpays if self.lawyer1 else NHPay.objects.none()
        return nhpays.filter(nhsaleside = self)
    @property
    def lawyer2_pays(self):
        nhpays = self.lawyer2.nhpays if self.lawyer2 else NHPay.objects.none()
        return nhpays.filter(nhsaleside = self)
    @property
    def lawyers_pay(self):
        amount = 0
        if self.lawyer1:
            for nhp in self.lawyer1.nhpays.filter(nhsaleside = self):
                amount += nhp.amount
        if self.lawyer2:
            for nhp in self.lawyer2.nhpays.filter(nhsaleside = self):
                amount += nhp.amount
        return amount
    @property
    def net_income(self):
        return self.income - self.lawyers_pay
    @property
    def all_employee_commission_precentage(self):
        return (self.employee1_commission or 0) + (self.employee2_commission or 0) + (self.director_commission or 0)
    @property
    def all_employee_commission(self):
        amount = 0
        for attr in ['employee1_pay','employee2_pay', 'employee3_pay', 'director_pay']:
            pay = getattr(self, attr)
            amount += (pay or 0)
        return amount
    def is_employee_related(self, employee):
        for attr in ['employee1','employee2', 'employee3', 'director']:
            if getattr(self, attr) == employee:
                return True
        return False
    def get_employee_pay(self, employee):
        pay = 0
        for attr in ['employee1','employee2', 'employee3', 'director']:
            e = getattr(self, attr)
            if e == employee:
                e_pay = getattr(self, attr + '_pay')
                if e_pay: 
                    pay += e_pay
        return pay
    def get_employee_commission(self, employee):
        commission = 0
        for attr in ['employee1','employee2', 'employee3', 'director']:
            e = getattr(self, attr)
            if e == employee:
                e_commission = getattr(self, attr + '_commission')
                if e_commission: 
                    commission += e_commission
        return commission
    def save(self,*args, **kw):
        if not self.income and self.actual_commission:
            self.income = self.nhsale.price * self.actual_commission / 100
        elif self.income and not self.actual_commission:
            self.actual_commission = self.income / self.nhsale.price * 100
        models.Model.save(self, *args, **kw)
        e1, ec1, e2, ec2, e3, ec3, d, dc = (self.employee1, self.employee1_commission,
                                   self.employee2, self.employee2_commission,
                                   self.employee3, self.employee3_commission,
                                   self.director, self.director_commission)
        y, m = self.nhsale.nhmonth.year,self.nhsale.nhmonth.month 
        if e1 and ec1:
            q = e1.nhpays.filter(nhsaleside = self)
            nhp = q.count() == 1 and q[0] or NHPay(employee=e1, nhsaleside = self, year = y, month = m)
            nhp.amount = self.employee1_pay
            nhp.save()
        if e2 and ec2:
            q = e2.nhpays.filter(nhsaleside = self)
            nhp = q.count() == 1 and q[0] or NHPay(employee=e2, nhsaleside = self, year = y, month = m)
            nhp.amount = self.employee2_pay
            nhp.save()
        if e3 and ec3:
            q = e3.nhpays.filter(nhsaleside = self)
            nhp = q.count() == 1 and q[0] or NHPay(employee=e3, nhsaleside = self, year = y, month = m)
            nhp.amount = self.employee3_pay
            nhp.save()
        if d and dc:
            q = d.nhpays.filter(nhsaleside = self)
            nhp = q.count() == 1 and q[0] or NHPay(employee=d, nhsaleside = self, year = y, month = m)
            nhp.amount = self.director_pay
            nhp.save()
    def get_absolute_url(self):
        return '/nhsaleside/%s' % self.id
    class Meta:
        db_table = 'NHSaleSide'

class NHMonth(models.Model):
    nhbranch = models.ForeignKey('NHBranch', on_delete=models.PROTECT, verbose_name=gettext('nhbranch'))
    month = models.PositiveSmallIntegerField(gettext('month'), choices=common.get_month_choices())
    year = models.PositiveSmallIntegerField(gettext('year'), choices=common.get_year_choices())
    is_closed = models.BooleanField(editable=False, default=False)
    
    objects = SeasonManager()
    
    def __init__(self, *args, **kw):
        models.Model.__init__(self, *args, **kw)
        self.include_tax = True
    @property
    def avg_signed_commission(self):
        count, total = 0, 0
        for nhs in self.nhsales.all():
            for nhss in nhs.nhsaleside_set.all():
                if nhss.sale_type.id in [SaleType.RentRentee, SaleType.RentRenter]: continue
                count += 1
                total += nhss.signed_commission
        return count > 0 and total / count or 0
    @property 
    def avg_actual_commission(self):
        count, total = 0, 0
        for nhs in self.nhsales.all():
            for nhss in nhs.nhsaleside_set.all():
                if nhss.sale_type.id in [SaleType.RentRentee, SaleType.RentRenter]: continue
                count += 1
                total += nhss.actual_commission
        return count > 0 and total / count or 0
    @property
    def total_income(self):
        amount = 0
        for nhs in self.nhsales.all():
            for nhss in nhs.nhsaleside_set.all():
                amount += nhss.income
        if not self.include_tax:
            t = Tax.objects.filter(date__lte=date(self.year, self.month,1)).latest().value / 100 + 1
            amount = amount / t
        return amount
    @property
    def total_lawyer_pay(self):
        amount = 0
        for nhs in self.nhsales.all():
            for nhss in nhs.nhsaleside_set.all():
                amount += nhss.lawyers_pay
        return amount
    @property
    def total_net_income(self):
        amount = 0
        for nhs in self.nhsales.all():
            for nhss in nhs.nhsaleside_set.all():
                amount += nhss.net_income
        if not self.include_tax:
            t = Tax.objects.filter(date__lte=date(self.year, self.month,1)).latest().value / 100 + 1
            amount = amount / t
        return amount
    @property
    def total_commission(self):
        amount = 0
        for nhs in self.nhsales.all():
            for nhss in nhs.nhsaleside_set.all():
                amount += nhss.all_employee_commission
        if not self.include_tax:
            t = Tax.objects.filter(date__lte=date(self.year, self.month,1)).latest().value / 100 + 1
            amount = amount / t
        return amount
    @property
    def net_income_no_commission(self):
        return self.total_net_income - self.total_commission
    @property
    def commission_to_net_income_precentage(self):
        if self.total_net_income == 0:
            return 0
        return self.total_commission / self.total_net_income * 100
    def close(self):
        self.is_closed = True
        self.save()
    def tax(self):
        return Tax.objects.filter(date__lte = date(self.year, self.month, 1)).latest().value
    def get_absolute_url(self):
        return '/nhmonth/' + str(self.id)
    class Meta:
        db_table = 'NHMonth'
        ordering = ['year', 'month']
        permissions = (('nhmonth_season', 'NHMonth Season'),('nh_season_profit', 'NH season profit'),)
        unique_together = ('nhbranch','year','month')

class NHSale(models.Model):
    nhmonth = models.ForeignKey('NHMonth', on_delete=models.PROTECT, editable=False, related_name='nhsales')
    
    num = models.IntegerField(gettext('sale_num'), unique=True)
    address = models.CharField(gettext('address'), max_length=50)
    hood = models.CharField(gettext('hood'), max_length=50)
    rooms = models.FloatField(gettext('rooms'))
    floor = models.PositiveSmallIntegerField(gettext('floor'))
    type = models.ForeignKey('HouseType', on_delete=models.PROTECT, verbose_name = gettext('house_type'))
    
    sale_date = models.DateField(gettext('sale_date'))
    price = models.FloatField(gettext('price'))
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)
    def verbose_id(self):
        return self.nhmonth.nhbranch.prefix + '-' + str(self.id)
    def get_absolute_url(self):
        return '/nhsale/%s' % self.id
    class Meta:
        db_table='NHSale'
        permissions = (('nhsale_move_nhmonth', 'NHSale Move Month'),)

class SaleMod(models.Model):
    sale = models.OneToOneField('Sale', on_delete=models.PROTECT, editable=False, related_name='%(class)s')
    date = models.DateField(gettext('date'), auto_now = True)
    remarks = models.TextField(gettext('remarks'), null=True)
    def get_absolute_url(self):
        return '/%s/%s' % (self.__class__.__name__.lower(), self.id)
    class Meta:
        abstract = True

class SalePriceMod(SaleMod):
    old_price = models.IntegerField()
    @property
    def current_price(self):
        return self.sale.price
    def get_absolute_url(self):
        return '/salepricemod/%s' % self.id
    class Meta:
        db_table = 'SalePriceMod'

class SaleHouseMod(SaleMod):
    old_house = models.ForeignKey('House', on_delete=models.PROTECT)
    @property
    def old_building(self):
        return self.old_house.building
    @property
    def current_building(self):
        return self.current_house.building
    @property
    def current_house(self):
        return self.sale.house
    def get_absolute_url(self):
        return '/salehousemod/%s' % self.id
    class Meta:
        db_table = 'SaleHouseMod'

class SalePayMod(SaleMod):
    to_month = models.PositiveSmallIntegerField(gettext('reject_month'), choices = common.get_month_choices())
    to_year = models.PositiveSmallIntegerField(gettext('reject_year'), choices = common.get_year_choices())
    employee_pay_month = models.PositiveSmallIntegerField(gettext('employee_pay_month'), choices = common.get_month_choices())
    employee_pay_year = models.PositiveSmallIntegerField(gettext('employee_pay_year'), choices = common.get_year_choices())
    
    def save(self, *args, **kw):
        super(SalePayMod, self).save(*args, **kw)
        self.sale.employee_pay_year = self.employee_pay_year
        self.sale.employee_pay_month = self.employee_pay_month
        self.sale.contractor_pay_year = self.to_year
        self.sale.contractor_pay_month = self.to_month
        self.sale.save()
    
    class Meta:
        abstract = True

class SalePre(SalePayMod):
    class Meta:
        db_table = 'SalePre'

class SaleReject(SalePayMod):
    class Meta:
        db_table = 'SaleReject'
        
class SaleCancel(SaleMod):
    deduct_from_demand = models.BooleanField(gettext('deduct_from_demand'), blank=True, null=True)
    def save(self, *args, **kw):
        super(SaleCancel, self).save(*args, **kw)
        sale = self.sale
        demand = sale.demand
        sale.commission_include = not self.deduct_from_demand
        sale.save()
    def get_absolute_url(self):
        return '/salecancel/%s' % self.id
    class Meta:
        db_table = 'SaleCancel'

class Sale(models.Model):
    demand = models.ForeignKey('Demand', on_delete=models.PROTECT, related_name='sales', editable=False)
    house = models.ForeignKey('House', on_delete=models.PROTECT, related_name = 'sales', verbose_name=gettext('house'))
    employee = models.ForeignKey('Employee', on_delete=models.PROTECT, related_name = 'sales', verbose_name=gettext('employee'),
                                 null=True, blank=True)
    sale_date = models.DateField(gettext('sale_date'))
    price = models.IntegerField(gettext('sale_price'))
    company_price = models.IntegerField(gettext('company_price'), null=True, blank=True)
    commission_madad_bi = models.FloatField(gettext('commission_madad'), null = True, blank = True)
    include_registration = models.NullBooleanField(gettext('include_registration'), blank=True, default = None,
                                                   choices = (
                                                              (None,'לא משנה'),
                                                              (False, 'לא'),
                                                              (True, 'כן')
                                                              ))
    price_include_lawyer = models.BooleanField(gettext('price_include_lawyer'), choices = Boolean)
    price_no_lawyer = models.IntegerField(gettext('sale_price_no_lawyer'))
    include_tax = models.BooleanField(gettext('include_tax'), choices=Boolean, default=True)
    specification_expense = models.PositiveIntegerField(gettext('specification_expense'), default=0)
    other_expense = models.PositiveIntegerField(gettext('other_expense'), default=0)
    clients = models.TextField(gettext('clients'))
    clients_phone = models.CharField(gettext('phone'), max_length = 10)
    price_final = models.IntegerField(editable=False, null=True)
    
    employee_pay_month = models.PositiveSmallIntegerField(gettext('employee_pay_month'), editable=False)
    employee_pay_year = models.PositiveSmallIntegerField(gettext('employee_pay_year'), editable=False)
    contractor_pay_month = models.PositiveSmallIntegerField(gettext('contractor_pay_month'), editable=False)
    contractor_pay_year = models.PositiveSmallIntegerField(gettext('contractor_pay_year'), editable=False)
    
    remarks = models.TextField(gettext('remarks'), null=True, blank=True)
    contract_num = models.CharField(gettext('so_contact_num'), max_length=10, null=True, blank=True)
    discount = models.FloatField(gettext('given_discount'), null=True, blank=True)
    allowed_discount = models.FloatField(gettext('allowed_discount'), null=True, blank=True)
    commission_include = models.BooleanField(gettext('commission include'), default=True, blank=True)
    
    objects = SaleManager()
    
    def __init__(self, *args, **kw):
        models.Model.__init__(self, *args, **kw)
        self.custom_cache = {}
        self.restore = True
    def get_restore_date(self):
        restore_date = None
        
        if self.id:
            actual_demand = self.actual_demand
            if actual_demand:
                restore_date = actual_demand.finish_date
        
        return restore_date
    @property
    @cache_method
    def tax(self):
        """
        Returns the tax value at the time the sale was made
        """
        tax_date = date(self.contractor_pay_month == 12 and self.contractor_pay_year+ 1 or self.contractor_pay_year,
                        self.contractor_pay_month == 12 and 1 or self.contractor_pay_month + 1, 1)
        return Tax.objects.filter(date__lte = tax_date).latest().value / 100 + 1
    @property
    def project(self):
        """
        Returns the project this sale belongs to
        """
        return self.house.building.project
    @property
    def saved_discount(self):
        """returns the precentage of discount that was NOT given (hence the name "saved")."""
        if self.discount is not None and self.allowed_discount is not None:
            return max(self.allowed_discount - self.discount, 0)
        else:
            return None
    @property
    def actual_demand(self):
        demand, new = Demand.objects.get_or_create(month=self.contractor_pay_month, year=self.contractor_pay_year,
                                                   project=self.demand.project)
        return demand
    @property
    def project_commission_details(self):
        return self.commission_details.filter(employee_salary=None)
    @property
    def pc_base(self):
        restore_date = self.get_restore_date()
        for c in ['c_var_precentage', 'c_var_precentage_fixed', 'c_zilber_base']:
            q = self.project_commission_details.filter(commission=c)
            if q.count() == 0:
                continue
            obj = self.restore and restore_date and common.restore_object(q[0], restore_date) or q[0]
            return obj.value
        return 0
    @property
    def zdb(self):
        q = self.project_commission_details.filter(commission='c_zilber_discount')
        if q.count() == 0:
            return 0
        return q[0].value
    @property
    def pb_dsp(self):
        restore_date = self.get_restore_date()
        q = self.project_commission_details.filter(commission='b_discount_save_precentage')
        if q.count() == 0: 
            return 0
        obj = self.restore and restore_date and common.restore_object(q[0], restore_date) or q[0]
        return obj.value
    @property
    def c_final(self):
        restore_date = self.get_restore_date()
        q = self.project_commission_details.filter(commission='final')
        if q.count() == 0: 
            return 0
        obj = self.restore and restore_date and common.restore_object(q[0], restore_date) or q[0]
        return obj.value
    @property
    def pc_base_worth(self):
        return self.pc_base * self.price_final / 100
    @property
    def pb_dsp_worth(self):
        return self.pb_dsp * self.price_final / 100
    @property
    def zdb_worth(self):
        return self.zdb * self.price_final / 100
    @property
    def c_final_worth(self):
        return (self.c_final or 0) * (self.price_final or 0) / 100
    @property
    def price_taxed(self):
        return self.include_tax and self.price or (self.price * self.tax)
    @property
    def price_taxed_for_perfect_size(self):
        if not self.house.perfect_size:
            return 0
        return self.price_taxed / self.house.perfect_size
    @property
    def lawyer_tax(self):
        pricelist = self.house.building.pricelist
        if pricelist and pricelist.lawyer_fee:
            return pricelist.lawyer_fee
        return common.LAWYER_TAX
    def project_price(self):
        c = self.house.building.project.commissions.get()
        if c.include_lawyer == None:
            price = self.price
        elif c.include_lawyer == True:
            price = self.price_include_lawyer and self.price or self.price * self.lawyer_tax
        elif c.include_lawyer == False:
            price = self.price_no_lawyer

        if c.include_tax:
            price = self.include_tax and price or price * self.tax
        else:
            price = self.include_tax and price / self.tax or price
            
        if c.deduct_registration and self.include_registration:
            price -= c.registration_amount
            
        # deduct those attrs from the price if they exist
        for attr in ['other_expense', 'specification_expense']:
            attr_val = getattr(self, attr)
            if attr_val:
                price -= attr_val
            
        return price
    def employee_price(self, employee=None):
        '''
        employee is used in cases where self.employee is null -> when sale is shared for all employees in the project.
        if employee is null and self.employee is null an exception is thrown.
        '''
        if not employee: employee = self.employee
        et = employee.employment_terms
        if et.include_lawyer:
            price = self.price_include_lawyer and self.price or self.price * self.lawyer_tax
        else:
            price = self.price_no_lawyer
      
        if et.include_tax:
            price = self.include_tax and price or price * self.tax
        else:
            price = self.include_tax and price / self.tax or price
        return price
    def save(self, *args, **kw):
        if not self.employee_pay_year or not self.employee_pay_month:
            self.employee_pay_year, self.employee_pay_month = self.demand.year, self.demand.month
        if not self.contractor_pay_year or not self.contractor_pay_month:
            self.contractor_pay_year, self.contractor_pay_month = self.demand.year, self.demand.month
        if self.price_final == None:
            self.price_final = self.project_price()
        models.Model.save(self, args, kw)
    @property
    def is_fixed(self):
        for attr in ['salehousemod', 'salepricemod', 'salepre', 'salereject','salecancel']:
            if getattr(self, attr):
                return True
    @property
    def is_ep_ok(self):
        return self.employee_pay_year == self.demand.year and self.employee_pay_month == self.demand.month 
    @property
    def is_cp_ok(self):
        return self.contractor_pay_year == self.demand.year and self.contractor_pay_month == self.demand.month 
    def __str__(self):
        return u'בניין %s דירה %s ל%s' % (self.house.building.num, self.house.num, self.clients)
    def get_absolute_url(self):
        return '/sale/%s' % self.id
    class Meta:
        ordering = ['sale_date']
        db_table = 'Sale'
        permissions = (('reject_sale', 'Can reject sales'),('cancel_sale', 'Can cancel sales'),
                       ('pre_sale', 'Can pre sales'), ('sale_analysis', 'Sale analysis'))
        
class Account(models.Model):
    num = models.IntegerField(gettext('account_num'), unique=True)
    bank = models.CharField(gettext('bank'), max_length=20)
    branch = models.CharField(gettext('branch'), max_length=20)
    branch_num = models.SmallIntegerField(gettext('branch_num'))
    payee = models.CharField(gettext('payee'), max_length=20)
    def get_absolute_url(self):
        return '/accounts/%s' % self.id
    class Meta:
        db_table='Account'

class DivisionType(models.Model):
    Marketing, NHShoham, NHModiin, NHNesZiona = 1,2,3,4
    name = models.CharField(gettext('name'), max_length=20, unique=True)
    
    objects = DivisionTypeManager()
    
    @property
    def is_nicehouse(self):
        return self.id in (2,3,4)
    def __str__(self):
        return str(self.name)
    class Meta:
        db_table = 'DivisionType'
        permissions = (('global_profit_lost','Global profit & loss'),)

class RevisionExt(models.Model):
    from reversion.models import Revision
    revision = models.ForeignKey(Revision, on_delete=models.PROTECT)
    date = models.DateTimeField()
    
    class Meta:
        db_table = 'RevisionExt'

#register models with reversion

import reversion

reversion.register(HouseTypeBonus)
reversion.register(CPrecentage)
reversion.register(CPriceAmount)
reversion.register(CAmount)
reversion.register(BDiscountSave)
reversion.register(BDiscountSavePrecentage)
reversion.register(BSaleRate)
reversion.register(BHouseType, follow = ['bonuses'])
reversion.register(CByPrice, follow = ['price_amounts'])
reversion.register(CVar, follow = ['amounts'])
reversion.register(CVarPrecentage, follow = ['precentages'])
reversion.register(CVarPrecentageFixed)
reversion.register(CZilber)
reversion.register(EmploymentTerms)
reversion.register(ProjectCommission)
reversion.register(SaleCommissionDetail, ignore_duplicates=True)
reversion.register(NHCommission)
