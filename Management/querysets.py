from django.db.models import Avg, Max, Min, Count, Sum
from django.db import models

class SeasonQuerySet(models.QuerySet):
    def range(self, from_year, from_month, to_year, to_month):
        q = models.Q(year = from_year, month__gte = from_month)
        if from_year == to_year:
            q = q & models.Q(month__lte = to_month)
        else:
            q = q | models.Q(year__gt = from_year, year__lt = to_year) | models.Q(year = to_year, month__lte = to_month)
        return self.filter(q)

class EmployeeSalaryBaseQuerySet(SeasonQuerySet):
    def nondeleted(self):
        return self.filter(is_deleted=False)
    
class DemandQuerySet(SeasonQuerySet):
    def total_sales_commission(self):
        return self.aggregate(Sum('sales_commission'))['sales_commission__sum'] or 0
    def total_sale_count(self):
        return self.aggregate(Sum('sale_count'))['sale_count__sum'] or 0

class SaleQuerySet(models.QuerySet):
    def contractor_pay_range(self, from_year, from_month, to_year, to_month):
        q = models.Q(contractor_pay_year = from_year, contractor_pay_month__gte = from_month)
        if from_year == to_year:
            q = q & models.Q(contractor_pay_month__lte = to_month)
        else:
            q = q | models.Q(contractor_pay_year__gt = from_year, contractor_pay_year__lt = to_year) 
            q = q | models.Q(contractor_pay_year = to_year, contractor_pay_month__lte = to_month)
        return self.filter(q)
    def employee_pay_range(self, from_year, from_month, to_year, to_month):
        q = models.Q(employee_pay_year = from_year, employee_pay_month__gte = from_month)
        if from_year == to_year:
            q = q & models.Q(employee_pay_month__lte = to_month)
        else:
            q = q | models.Q(employee_pay_year__gt = from_year, employee_pay_year__lt = to_year) 
            q = q | models.Q(employee_pay_year = to_year, employee_pay_month__lte = to_month)
        return self.filter(q)
    def total_price(self):
        return self.aggregate(Sum('price'))['price__sum'] or 0
    def total_price_final(self):
        return self.aggregate(Sum('price_final'))['price_final__sum'] or 0
    
class HouseQuerySet(models.QuerySet):
    def sold(self):
        q = models.Q(is_sold = True) | models.Q(sales__salecancel__isnull = True)
        return self.filter(q).annotate(sales_num = Count('sales')).filter(sales_num = 1)
    def signed(self):
        return self.filter(signups__cancel__isnull = False).annotate(signups_num = Count('signups')).filter(signups_num = 1)
    def avalible(self):
        q = models.Q(is_sold = False) & models.Q(sales__salecancel__isnull = True) & models.Q(signups__cancel__isnull = True)
        return self.filter(q).annotate(sales_num = Count('sales'), signups_num = Count('signups')).filter(sales_num = 0, signups_num = 0)

class HouseVersionQuerySet(models.QuerySet):
    def company(self):
        return self.filter(type__id = 1)
    def doh0(self):
        return self.filter(type__id = 2)

class CityCallersQuerySet(models.QuerySet):
    def total_callers_num(self):
        return self.aggregate(Sum('callers_num'))['callers_num__sum'] or 0        

class MediaReferralsQuerySet(models.QuerySet):
    def total_referrals_num(self):
        return self.aggregate(Sum('referrals_num'))['referrals_num__sum'] or 0
