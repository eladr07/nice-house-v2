# coding: utf-8

from datetime import date

from django.db import models

from .common import current_month
from .querysets import *

class SeasonManager(models.Manager):
    def range(self, from_year, from_month, to_year, to_month):
        return self.get_queryset().range(from_year, from_month, to_year, to_month)
    def get_queryset(self):
        return SeasonQuerySet(self.model)

class EmployeeSalaryBaseManager(SeasonManager):
    def nondeleted(self):
        return self.get_queryset().nondeleted()
    def get_queryset(self):
        return EmployeeSalaryBaseQuerySet(self.model)
    
class DemandManager(SeasonManager):
    use_for_related_fields = True
    
    def get_or_create(self, **kwargs):
        demand, created = super(DemandManager, self).get_or_create(**kwargs)
        commissions = demand.project.commissions.get()
        if created and commissions.add_amount:
            demand.diffs.create(type=u'קבועה', amount = commissions.add_amount, reason = commissions.add_type)
        return demand, created
            
    def current(self):
        now = current_month()
        return self.filter(year = now.year, month = now.month)
    
    def get_queryset(self):
        return DemandQuerySet(self.model, using=self._db)

class SaleManager(models.Manager):
    use_for_related_fields = True
    
    def contractor_pay_range(self, from_year, from_month, to_year, to_month):
        return self.get_queryset().contractor_pay_range(from_year, from_month, to_year, to_month)
    def employee_pay_range(self, from_year, from_month, to_year, to_month):
        return self.get_queryset().employee_pay_range(from_year, from_month, to_year, to_month)
    def get_queryset(self):
        return SaleQuerySet(self.model, using=self._db)
    
class HouseManager(models.Manager):
    use_for_related_fields = True
    
    def sold(self):
        return self.get_queryset().sold()
    def signed(self):
        return self.get_queryset().signed()
    def avalible(self):
        return self.get_queryset().avalible()
    def get_queryset(self):
        return HouseQuerySet(self.model)

class HouseVersionManager(models.Manager):
    use_for_related_fields = True
    
    def company(self):
        return self.get_queryset().company()
    def doh0(self):
        return self.get_queryset().doh0()
    def get_queryset(self):
        return HouseVersionQuerySet(self.model)

class DivisionTypeManager(models.Manager):
    def nh_divisions(self):
        return self.filter(pk__in = (2,3,4))
    
class ProjectManager(models.Manager):
    def active(self):
        return self.filter(end_date=None, is_marketing=True)
    def archive(self):
        return self.exclude(end_date=None)

class EmployeeManager(models.Manager):
    def active(self):
        return self.filter(work_end = None)
    def archive(self):
        return self.exclude(work_end = None)
    
class NHBranchEmployeeManager(models.Manager):
    def month(self, year, month):
        start_date = date(year, month, 1)
        end_date = date(month == 12 and year + 1 or year, month == 12 and 1 or month + 1, 1)
        q = models.Q(start_date__lt = start_date) & (models.Q(end_date__isnull = True) | models.Q(end_date__gte = end_date))
        return self.filter(q)

class NHEmployeeManager(models.Manager):
    def _get_key(self, nhemployee):
        query = nhemployee.nhbranchemployee_set.all()
        if query.count() == 0:
            return 0
        else:
            return query.latest().nhbranch_id
    def active(self):
        query = self.filter(work_end = None)
        nhemployees = list(query)
        nhemployees.sort(self._get_key)
        return nhemployees
    def archive(self):
        query = self.exclude(work_end = None)
        nhemployees = list(query)
        nhemployees.sort(self._get_key)
        return nhemployees