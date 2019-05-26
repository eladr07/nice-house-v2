from reportlab.platypus import Paragraph
from pyfribidi import log2vis
from django.utils.translation import ugettext

import Management.models as models
from Management.templatetags.management_extras import commaise
from Management.pdf.styles import *

class TableField(object):
    def __init__(self, title='', width= -1, is_summarized=False, is_commaised=False, is_averaged = False):
        self.name = self.__class__.__name__
        self.title = title
        self.width = width
        self.is_summarized = is_summarized
        self.is_commaised = is_commaised
        self.is_averaged = is_averaged
    
    def _format_title(self):
        parts = [log2vis(part) for part in self._title.split()]
        self._title = '\n'.join(parts)
    
    def get_title(self):
        return self._title
    def set_title(self, value):
        self._title = value
        self._format_title()
    title = property(get_title, set_title)
    
    def format(self, item):
        raise NotImplementedError
    def get_height(self, item):
        return None
        
class ProjectNameAndCityField(TableField):
    def __init__(self):
        return super(ProjectNameAndCityField, self).__init__(ugettext('project_name'),135)
    def format(self, item):
        return log2vis(item.project.name_and_city)
    
    class Meta:
        models = (models.Demand, models.Sale)

class ProjectInitiatorField(TableField):
    def __init__(self):
        return super(ProjectInitiatorField, self).__init__(ugettext('initiator'),150)
    def format(self, item):
        return log2vis(item.project.initiator)
    
    class Meta:
        models = (models.Demand, models.Sale)

class MonthField(TableField):
    def __init__(self):
        return super(MonthField, self).__init__(ugettext('pdf_month'), 45)
    def format(self, item):
        return '%s/%s' % (item.month, item.year)
    
    class Meta:
        models = (models.Demand,)

class DemandSalesCountField(TableField):
    def __init__(self):
        return super(DemandSalesCountField, self).__init__(ugettext('demand_sales_count'),50, is_summarized=True)
    def format(self, item):
        return len(item.get_sales())
    
    class Meta:
        models = (models.Demand,)

class DemandSalesTotalPriceField(TableField):
    def __init__(self):
        return super(DemandSalesTotalPriceField, self).__init__(ugettext('demand_total_sales_price'),50, 
                                                                is_commaised=True, is_summarized=True)
    def format(self, item):
        return item.get_sales().total_price()
    
    class Meta:
        models = (models.Demand,)

class DemandTotalAmountField(TableField):
    def __init__(self):
        return super(DemandTotalAmountField, self).__init__(ugettext('demand_total_amount'),50, is_commaised=True, 
                                                            is_summarized=True)
    def format(self, item):
        return item.get_total_amount()
    
    class Meta:
        models = (models.Demand,)

class DemandDiffInvoiceField(TableField):
    def __init__(self):
        return super(DemandDiffInvoiceField, self).__init__(ugettext('demand_diff_invoice'),50, is_commaised=True, 
                                                            is_summarized=True)
    def format(self, item):
        return item.diff_invoice
    
    class Meta:
        models = (models.Demand,)

class DemandDiffInvoicePaymentField(TableField):
    def __init__(self):
        return super(DemandDiffInvoicePaymentField, self).__init__(ugettext('demand_diff_invoice_payment'),50, is_commaised=True, 
                                                                   is_summarized=True)
    def format(self, item):
        return item.diff_invoice_payment
    
    class Meta:
        models = (models.Demand,)
        
class InvoicesNumField(TableField):
    def __init__(self):
        return super(InvoicesNumField, self).__init__(ugettext('invoices_num'),50)
    def format(self, item):
        return '\n'.join([str(i.num) for i in item.invoices.all()])
    
    def get_height(self, item):
        invoices_count = item.invoices.count()
        return invoices_count * 14 or None
    
    class Meta:
        models = (models.Demand,)
        
class InvoicesAmountField(TableField):
    def __init__(self):
        return super(InvoicesAmountField, self).__init__(ugettext('invoices_amount'), 50)
    def format(self, item):
        return '\n'.join([commaise(i.amount) for i in item.invoices.all()])
    
    def get_height(self, item):
        invoices_count = item.invoices.count()
        return invoices_count * 14 or None
    
    class Meta:
        models = (models.Demand,)
        
class InvoicesDateField(TableField):
    def __init__(self):
        return super(InvoicesDateField, self).__init__(ugettext('invoices_date'), 50)
    def format(self, item):
        return '\n'.join([i.date.strftime('%d/%m/%y') for i in item.invoices.all()])
    
    def get_height(self, item):
        invoices_count = item.invoices.count()
        return invoices_count * 14 or None
    
    class Meta:
        models = (models.Demand,)
        
class PaymentsNumField(TableField):
    def __init__(self):
        return super(PaymentsNumField, self).__init__(ugettext('payments_num'),50)
    def format(self, item):
        return '\n'.join([str(p.num) for p in item.payments.all()])
    
    def get_height(self, item):
        payments_count = item.payments.count()
        return payments_count * 14 or None
    
    class Meta:
        models = (models.Demand,)
        
class PaymentsAmountField(TableField):
    def __init__(self):
        return super(PaymentsAmountField, self).__init__(ugettext('payments_amount'),50)
    def format(self, item):
        return '\n'.join([commaise(p.amount) for p in item.payments.all()])
    
    def get_height(self, item):
        payments_count = item.payments.count()
        return payments_count * 14 or None
        
    class Meta:
        models = (models.Demand,)

class PaymentsDateField(TableField):
    def __init__(self):
        return super(PaymentsDateField, self).__init__(ugettext('payments_date'), 50)
    def format(self, item):
        return '\n'.join([p.payment_date.strftime('%d/%m/%y') for p in item.payments.all()])
    
    def get_height(self, item):
        invoices_count = item.payments.count()
        return invoices_count * 14 or None
    
    class Meta:
        models = (models.Demand,)
        
class SaleClientsField(TableField):
    def __init__(self):
        return super(SaleClientsField, self).__init__(ugettext('clients_name'), 65)
    def format(self, item):
        clients = item.clients
        str2 = ''
        parts = clients.strip().split('\r\n')
        parts.reverse()
        for s in parts:
            str2 += log2vis(s)
        return Paragraph(str2, styleRow10)
    
    class Meta:
        models = (models.Sale,)
        
class SalePriceTaxedField(TableField):
    def __init__(self):
        return super(SalePriceTaxedField, self).__init__(ugettext('price_with_tax'), 50, is_commaised = True,
                                                           is_summarized = True, is_averaged = True)
    def format(self, item):
        return item.price_taxed
    
    class Meta:
        models = (models.Sale,)

class SalePriceTaxedForPerfectSizeField(TableField):
    def __init__(self):
        return super(SalePriceTaxedForPerfectSizeField, self).__init__(ugettext('price_for_size'), 35, is_commaised = True,
                                                                       is_summarized = True, is_averaged = True)
    def format(self, item):
        return item.price_taxed_for_perfect_size
    
    class Meta:
        models = (models.Sale,) 

class SaleIncludeLawyerTaxField(TableField):
    def __init__(self):
        return super(SaleIncludeLawyerTaxField, self).__init__(ugettext('include_lawyer_tax'), 50)
    def format(self, item):
        if item.price_include_lawyer == None:
            return '---'
        elif item.price_include_lawyer == False:
            return log2vis(ugettext('no'))
        elif item.price_include_lawyer == True:
            return log2vis(ugettext('yes'))
    
    class Meta:
        models = (models.Sale,)
        
class SaleEmployeeNameField(TableField):
    def __init__(self):
        return super(SaleEmployeeNameField, self).__init__(ugettext('employee_name'), 75)
    def format(self, item):
        return log2vis(unicode(item.employee or ''))
    
    class Meta:
        models = (models.Sale,)

class SaleDateField(TableField):
    def __init__(self):
        return super(SaleDateField, self).__init__(ugettext('sale_date'), 45)
    def format(self, item):
        return item.sale_date.strftime('%d/%m/%y')
    
    class Meta:
        models = (models.Sale,)

class HouseNumField(TableField):
    def __init__(self):
        return super(HouseNumField, self).__init__(ugettext('house_num'), 35)
    def format(self, item):
        return item.num
    
    class Meta:
        models = (models.House,)

class HouseBuildingNumField(TableField):
    def __init__(self):
        return super(HouseBuildingNumField, self).__init__(ugettext('building_num'), 35)
    def format(self, item):
        return item.building.num
    
    class Meta:
        models = (models.House,)
        
class HouseRoomsField(TableField):
    def __init__(self):
        return super(HouseRoomsField, self).__init__(ugettext('rooms_num'),35, is_averaged = True)
    def format(self, item):
        return item.rooms
    
    class Meta:
        models = (models.House,)
        
class HouseFloorField(TableField):
    def __init__(self):
        return super(HouseFloorField, self).__init__(ugettext('floor'),35, is_averaged = True)
    def format(self, item):
        return item.floor
    
    class Meta:
        models = (models.House,)
        
class HouseSizeField(TableField):
    def __init__(self):
        return super(HouseSizeField, self).__init__(ugettext('house_size'),40, is_averaged = True)
    def format(self, item):
        return item.net_size
    
    class Meta:
        models = (models.House,)
        
class HouseGardenSizeField(TableField):
    def __init__(self):
        return super(HouseGardenSizeField, self).__init__(ugettext('garden_size'),55, is_averaged = True)
    def format(self, item):
        return item.garden_size
    
    class Meta:
        models = (models.House,)
        
class HousePerfectSizeField(TableField):
    def __init__(self):
        return super(HousePerfectSizeField, self).__init__(ugettext('perfect_size'),55, is_averaged = True)
    def format(self, item):
        return item.perfect_size
    
    class Meta:
        models = (models.House,)
        
class HouseTypeField(TableField):
    def __init__(self):
        return super(HouseTypeField, self).__init__(ugettext('house_type'),55)
    def format(self, item):
        return log2vis(unicode(item.type))
    
    class Meta:
        models = (models.House,)
        
class HouseSettleDateField(TableField):
    def __init__(self):
        return super(HouseSettleDateField, self).__init__(ugettext('settle_date'),35)
    def format(self, item):
        settle_date = item.settle_date
        return settle_date and settle_date.strftime('%d/%m/%y') or ''
    
    class Meta:
        models = (models.House,)