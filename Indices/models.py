from django.db import models

from django.utils.translation import gettext

# Create your models here.

class Tax(models.Model):
    date = models.DateField(gettext('date'))
    value = models.FloatField(gettext('value'))

    def get_absolute_url(self):
        return '/tax/%s' % self.id
    
    class Meta:
        db_table = 'Tax'
        get_latest_by = 'date'
        ordering = ['-date']
        verbose_name = gettext('tax')
                
#Building Input
class MadadBI(models.Model):
    year = models.PositiveSmallIntegerField(gettext('year'))
    month = models.PositiveSmallIntegerField(gettext('month'))
    publish_date = models.DateField(gettext('publish_date'))
    value = models.FloatField(gettext('value'))

    def diff(self):
        q = MadadBI.objects.filter(year = self.month == 1 and self.year - 1 or self.year,
                                   month = self.month == 1 and 12 or self.month - 1)
        if q.count() == 0:
            return 0
        prev_madad = q[0]
        return (self.value - prev_madad.value) / (prev_madad.value / 100)
    
    def get_absolute_url(self):
        return '/madadbi/%s' % self.id

    class Meta:
        db_table = 'MadadBI'
        get_latest_by = 'publish_date'
        ordering = ['-publish_date']
        unique_together = ('year', 'month')

#Consumer Prices
class MadadCP(models.Model):
    year = models.PositiveSmallIntegerField(gettext('year'))
    month = models.PositiveSmallIntegerField(gettext('month'))
    publish_date = models.DateField(gettext('publish_date'))
    value = models.FloatField(gettext('value'))

    def diff(self):
        q = MadadCP.objects.filter(year = self.month == 1 and self.year - 1 or self.year,
                                   month = self.month == 1 and 12 or self.month - 1)
        if q.count() == 0:
            return 0
        prev_madad = q[0]
        return (self.value - prev_madad.value) / (prev_madad.value / 100)
    
    def get_absolute_url(self):
        return '/madadcp/%s' % self.id
    
    class Meta:
        db_table = 'MadadCP'
        get_latest_by = 'publish_date'
        ordering = ['-publish_date']
        unique_together = ('year', 'month')