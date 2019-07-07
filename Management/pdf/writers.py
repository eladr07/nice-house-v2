#!/usr/bin/python
# -*- coding: utf-8 -*-
import os,logging, itertools, textwrap
from datetime import datetime, date

import reportlab.rl_config
reportlab.rl_config.warnOnMissingFontGlyphs = 0

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Image, Spacer, Frame, Table, PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from pyfribidi import log2vis
from reportlab.lib.enums import *
from reportlab.lib.styles import ParagraphStyle

from django.utils.translation import gettext

import Management.models
from Management.templatetags.management_extras import commaise

from Management.pdf.helpers import Builder, MassBuilder
from Management.pdf.table_fields import *
from Management.pdf.salary_table_fields import *
from Management.pdf.styles import *

#register Hebrew fonts

from NiceHouse.settings import BASE_DIR

STATIC_URL = 'Management/pdf/'

pdfmetrics.registerFont(TTFont('David', os.path.join(BASE_DIR, STATIC_URL, 'fonts/DavidCLM-Medium.ttf')))
pdfmetrics.registerFont(TTFont('David-Bold', os.path.join(BASE_DIR, STATIC_URL, 'fonts/DavidCLM-Bold.ttf')))

pdfmetrics.registerFontFamily('David', normal='David', bold='David-Bold')

def break_to_lines(s):
    tmp = log2vis(s).split()
    tmp.reverse()
    return '<br/>'.join(tmp)

def clientsPara(str):
    str2=''
    parts = str.strip().split('\r\n')
    parts.reverse()
    for s in parts:
        str2 += log2vis(s)
    return Paragraph(str2, ParagraphStyle('clients', fontName='David', fontSize=10, alignment=TA_CENTER))
def titlePara(str):
    '''
    returns a paragraph containing str with the subject style
    '''
    return Paragraph('<b><u>%s</u></b>' % log2vis(str), styleSubj)
def datePara():
    '''
    returns a paragraph containing date with the date style
    '''
    s = log2vis(u'תאריך : %s' % date.today().strftime('%d/%m/%Y'))
    return Paragraph('%s' % s, styleDate)
def tableCaption(caption=log2vis(u'ולהלן פירוט העסקאות')):
    return Paragraph(u'<u>%s</u>' % caption, 
                     ParagraphStyle(name='tableCaption', fontName='David-Bold', fontSize=15,
                                    alignment=TA_CENTER))
def nhLogo():
    logo_path = os.path.join(BASE_DIR, STATIC_URL, 'images/nh_logo_new.png')
    return Image(logo_path, 170, 75)

def sigPara():
    s = log2vis('ברגשי כבוד,') + '<br/>'
    s += log2vis('אלי בר-און')
    return Paragraph(s, ParagraphStyle(name='sig', fontName='David-Bold', fontSize=15,
                                       alignment=TA_LEFT))
def nhAddr():
    s = log2vis('רחוב הגולן 1, בית ברקת 1, איירפורט סיטי') + '<br/>'
    s += log2vis('ת.ד 1103 איירפורט סיטי נתב"ג') + '<br /><br />'
    s += '<b>9302960</b>' + log2vis('  טלפון: ') + '<b>08-9302950</b>' + log2vis('  פקס: ') + '<br />'
    s += log2vis('nicehouse1@bezeqint.net')
 
    return Paragraph(s, ParagraphStyle(name='addr', fontName='David', fontSize=12, alignment=TA_CENTER))

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("David", 13)
        self.drawRightString(40*mm, 20*mm,
                             log2vis(u"עמוד %d מתוך %d" % (self._pageNumber, page_count)))

class DocumentBase(object):
    def __init__(self):
        super(DocumentBase, self).__init__()
    def addLater(self, canv, doc):
        frame2 = Frame(0, 680, 650, 150)
        frame2.addFromList([nhLogo()], canv)
        frame4 = Frame(50, 0, 500, 100)
        frame4.addFromList([nhAddr()], canv)
        date_str = log2vis(u'תאריך : %s' % date.today().strftime('%d/%m/%Y'))
        canv.setFont('David',14)
        canv.drawRightString(50*mm, 275*mm, date_str)
    def addFirst(self, canv, doc):
        frame2 = Frame(0, 680, 650, 150)
        frame2.addFromList([nhLogo()], canv)
        frame4 = Frame(50, 0, 500, 100)
        frame4.addFromList([nhAddr()], canv)
        date_str = log2vis(u'תאריך : %s' % date.today().strftime('%d/%m/%Y'))
        canv.setFont('David',14)
        canv.drawRightString(50*mm, 275*mm, date_str)
    def get_pagesize(self):
        return A4
    def build(self, filename):
        doc = SimpleDocTemplate(filename, pagesize = self.get_pagesize(), topMargin=100, bottomMargin=100)
        doc.build(self.get_story(), self.addFirst, self.addLater, NumberedCanvas)
    def get_story(self):
        pass

class ProjectListWriter(DocumentBase):
    def __init__(self, projects):
        self.projects = projects

    def projectFlows(self):
        flows = [Paragraph(log2vis(u'נווה העיר - %s פרוייקטים' % len(self.projects)), styleSubTitleBold), Spacer(0,10)]
        headers = [log2vis(n) for n in [u'יזם',u'פרוייקט\nשם',u'עיר',u"בניינים\nמס'",u"דירות\nמס'",u'אנשי מכירות',u'אנשי קשר']]
        colWidths = [None,70,None,None,None,150,150]
        
        colWidths.reverse()
        headers.reverse()
        rows=[]

        for project in self.projects:

            if project.details != None:
                houses_num, buildings_num = project.details.houses_num, project.details.buildings_num
            else:
                houses_num, buildings_num = '---','---'
                
            row = [log2vis(project.initiator), log2vis(project.name), log2vis(project.city), buildings_num, houses_num]

            employees = ''
            for employee in project.employees.all():
                employee_str = str(employee)
                if employee.cell_phone:
                    employee_str += ' - ' + employee.cell_phone
                employees += log2vis(employee_str) + '<br/>'
                    
            contacts = ''
            if project.demand_contact:
                contact_str = u'תשלום: ' + str(project.demand_contact)
                if project.demand_contact.phone:
                    contact_str += ' - ' + project.demand_contact.phone
                contacts += log2vis(contact_str) + '<br/>'
            if project.payment_contact:
                contact_str = u"צ'קים: " + str(project.payment_contact)
                if project.payment_contact.phone:
                    contact_str += ' - ' + project.payment_contact.phone
                contacts += log2vis(contact_str) + '<br/>'                
            for contact in project.contacts.all():
                contact_str = str(contact)
                if contact.phone:
                    contact_str += ' - ' + contact.phone
                contacts += log2vis(contact_str) + '<br/>' 
            
            row.extend([Paragraph(employees, styleRow9), Paragraph(contacts, styleRow9)])

            row.reverse()
            rows.append(row)
            
        data = [headers]
        data.extend(rows)
        t = Table(data,colWidths, style = saleTableStyle, repeatRows = 1)
        flows.append(t)

        return flows
    
    def get_story(self):
        story = [Spacer(0,40)]
        story.append(titlePara(u'מצבת פרוייקטים'))
        story.append(Spacer(0, 10))
        story.extend(self.projectFlows())
        return story

class EmployeeListWriter(DocumentBase):

    def __init__(self, employees, nhemployees):
        self.employees = employees
        self.nhemployees = nhemployees

    def employeeFlows(self):
        #generate phones string for an employee
        def get_phones(employee):
            phones = ''
            for attr in ['work_phone','work_fax','cell_phone','home_phone','mate_phone']:
                attr_value = getattr(e, attr)
                if attr_value:
                    phones += '<u>' + log2vis(gettext(attr)) + '</u><br/>'
                    phones += log2vis(attr_value) + '<br/>'
            return phones
        def get_account_str(employee):
            account = employee.account
            account_str = ''
            if account:
                account_str += '<u>' + log2vis(gettext('payee')) + '</u><br/>'
                account_str += log2vis(account.payee) + '<br/>'
                account_str += '<u>' + log2vis(gettext('bank')) + '</u><br/>'
                account_str += log2vis(account.bank) + '<br/>'
                account_str += '<u>' + log2vis(gettext('branch')) + '</u><br/>'
                account_str += log2vis(u'%s %s' % (account.branch, account.branch_num)) + '<br/>'
                account_str += '<u>' + log2vis(gettext('account_num')) + '</u><br/>'
                account_str += str(account.num) + '<br/>'
            return account_str            
            
        flows=[Paragraph(log2vis(u'נווה העיר - %s עובדים' % len(self.employees)), styleSubTitleBold),
               Spacer(0,10)]

        headers = [log2vis(name) for name in [u'מס"ד',u'פרטי\nשם',u'משפחה\nשם',u'טלפון',u'דוא"ל',u'כתובת',u'העסקה\nתחילת',u'העסקה\nסוג',u'חשבון\nפרטי',u'פרוייקטים']]
        colWidths = [None,None,None,85,90,70,None,None,60,80]
        
        headers.reverse()
        colWidths.reverse()
        
        rows = []
        rank = None
        for e in self.employees:
            if rank != e.rank:
                row = [log2vis(str(e.rank)),None,None,None,None]
                row.reverse()
                rows.append(row)
                rank = e.rank
            
            row=[e.id, log2vis(e.first_name), log2vis(e.last_name), Paragraph(get_phones(e), styleRow9), 
                 log2vis(e.mail), Paragraph(log2vis(e.address), styleRow9), log2vis(e.work_start.strftime('%d/%m/%Y')),
                 log2vis(str(e.employment_terms and e.employment_terms.hire_type or '---')),
                 Paragraph(get_account_str(e), styleRow9),
                 Paragraph('<br/>'.join([log2vis(p.name) for p in e.projects.all()]), styleRow9)]

            row.reverse()
            rows.append(row)

        data = [headers]
        data.extend(rows)
        t = Table(data, colWidths, style = saleTableStyle, repeatRows = 1)
        flows.append(t)
        flows.extend([PageBreak()])
        
        flows.extend([Paragraph(log2vis(u'נייס האוס - %s עובדים' % len(self.nhemployees)), styleSubTitleBold),
                      Spacer(0,10)])
        
        headers = [log2vis(name) for name in [u'מס"ד',u'פרטי\nשם',u'משפחה\nשם',u'טלפון',u'דוא"ל',u'כתובת',u'העסקה\nתחילת',u'העסקה\nסוג',u'חשבון\nפרטי']]
        colWidths = [None,None,None,110,90,70,None,30,60]
        
        colWidths.reverse()
        headers.reverse()
        
        rows = []
        
        nhbranch = None
        for e in self.nhemployees:
            if nhbranch in e.current_nhbranches:
                row = [log2vis(str(e.nhbranch)), None,None,None,None]
                row.reverse()
                rows.append(row)
                nhbranch = e.nhbranch

            row=[e.id, log2vis(e.first_name), log2vis(e.last_name), Paragraph(get_phones(e), styleRow9),
                 log2vis(e.mail), Paragraph(log2vis(e.address), styleRow9), log2vis(e.work_start.strftime('%d/%m/%Y')),
                 log2vis(str(e.employment_terms and e.employment_terms.hire_type or '')),
                 Paragraph(get_account_str(e), styleRow9)]
            row.reverse()
            rows.append(row)
                
        data = [headers]
        data.extend(rows)
        t = Table(data, colWidths, style = saleTableStyle, repeatRows = 1)
        flows.append(t)
               
        return flows
    
    def get_story(self):
        story = [Spacer(0,40)]
        story.append(titlePara(u'מצבת עובדים'))
        story.append(Spacer(0, 10))
        story.extend(self.employeeFlows())
        return story

class MonthDemandWriter(DocumentBase):

    def __init__(self, demand, to_mail=False):
        super(MonthDemandWriter, self).__init__()
        self.demand = demand
        self.commissions = self.demand.project.commissions.get()
        self.signup_adds = self.commissions.commission_by_signups
        self.to_mail = to_mail
    def toPara(self):
        contact = self.demand.project.demand_contact
        if contact:
            s = log2vis(u'בס"ד') + '<br/><br/>'
            s += '<u>%s</u><br/>' % log2vis(u'לכבוד')
            s += '<b>' + log2vis(u'חברת %s' % contact.company) + '<br/>'
            s += log2vis(u'לידי %s' % str(contact)) + '<br/>'
            s += log2vis(u'תפקיד : %s</b>' % contact.role) + '<br/></b>'
            s += log2vis(u'א.ג.נ')
        else:
            s = log2vis(u'--לא הוזן איש קשר') + '<br/>'
            s += log2vis(u'לדרישות לתשלום--')
        return Paragraph(s, styleN)
    def addFirst(self, canv, doc):
        super(MonthDemandWriter, self).addFirst(canv, doc)
        frame1 = Frame(300, 580, 250, 200)
        frame1.addFromList([self.toPara()], canv)
    def introPara(self):
        project_commissions = self.commissions
        if project_commissions.include_lawyer == None:
            lawyer_str = u''
        elif project_commissions.include_lawyer == False:
            lawyer_str = u', לא כולל שכ"ט עו"ד'
        else:
            lawyer_str = u', כולל שכ"ט עו"ד'
        tax_str = project_commissions.include_tax and u'כולל מע"מ' or u'לא כולל מע"מ'
        s = log2vis(u'א. רצ"ב פירוט דרישתנו לתשלום בגין %i עסקאות שנחתמו החודש.' %
                    self.demand.sales_count) + '<br/>'
        s += log2vis(u'ב. סה"כ מכירות (%s%s) - %s ש"ח.' %
                     (tax_str, lawyer_str, commaise(self.demand.sales_amount))) + '<br/>'
        s += log2vis(u'ג. עמלתנו (כולל מע"מ) - %s ש"ח (ראה פירוט רצ"ב).' % 
                    commaise(self.demand.total_amount)) + '<br/>'
        s += log2vis(u'ד. נא בדיקתכם ואישורכם לתשלום לתאריך %s אודה.' % datetime.now().strftime('31/%m/%Y')) + '<br/>'
        s += log2vis(u'ה. במידה ויש שינוי במחירי הדירות ו\או שינוי אחר') + '<br/>'
        s += log2vis(u'אנא עדכנו אותנו בפקס ו\או בטלפון הרצ"ב על גבי דרישה זו.   ') + '<br/>'
        s += log2vis(u'ו. לנוחיותכם, הדרישה מועברת אליכם גם במייל וגם בפקס.')
        return Paragraph(s, ParagraphStyle(name='into', fontName='David', fontSize=14,
                                           alignment=TA_RIGHT, leading=16))
    def zilberBonusFlows(self):
        logger = logging.getLogger('pdf')
        logger.info('starting zilberBonusFlows')
        
        commissions = self.commissions

        flows = [tableCaption(caption=log2vis(u'נספח ב - דו"ח חסכון בהנחה')), Spacer(0,20),
                 tableCaption(caption=log2vis(u'מדד בסיס - %s' % commissions.c_zilber.base_madad)),
                 Spacer(0,30)]
        
        headers = [log2vis(n) for n in [u'מס"ד',u'דרישה\nחודש', u'שם הרוכשים', u'ודירה\nבניין', u'חוזה\nתאריך', u'עמלה\nלחישוב\nמחיר', u'0 דו"ח\nמחירון', 
                                        u'חדש\nמדד', u'60%\nממודד\nמחירון', u'מחיר\nהפרש', u'בהנחה\nחסכון\nשווי']]
        
        colWidths  =[None,None,100,None,None,None,40,40,40,40,40]
        colWidths.reverse()
        headers.reverse()
        rows = []
        i = 0
        total_prices, total_adds, total_doh0price, total_memudad, total_diff = 0, 0, 0, 0, 0
        demand = self.demand
        commissions = self.commissions
        base_madad = commissions.c_zilber.base_madad
                
        logger.debug(str({'base_madad':base_madad}))
        
        while demand != None:
            logger.info('starting to write bonuses for %(demand)s', {'demand':demand})

            sales = demand.sales_list
            
            # for performance reasons we take all commission details in a single query and store them for later use
            commission_details = models.SaleCommissionDetail.objects.filter(
                employee_salary__isnull = True, sale__in = sales,
                commission__in = ('latest_doh0price', 'memudad', 'current_madad')) \
                .order_by('sale__id')
            
            # creating an easy-to-use dictionary {sale, {cd.commission, cd.value}} where cd is the commission detail
            sales_commission_details = {}
            
            for sale, group in itertools.groupby(commission_details, lambda commission_detail: commission_detail.sale):
                sales_commission_details[sale] = { cd.commission:cd.value for cd in list(group) }
                        
            for s in sales:
                logger.info('starting to write bonus for sale #%(id)s', {'id':s.id})
                
                i += 1
                actual_demand = s.actual_demand

                if actual_demand:
                    row = ['%s-%s' % (actual_demand.id, i),'%s/%s' % (actual_demand.month, actual_demand.year)]
                else:
                    row = [None, None]
                
                if sale in sales_commission_details:
                    details = sales_commission_details[sale]
                    latest_doh0price = details.get('latest_doh0price', 0)
                    memudad = details.get('memudad', 0)
                    current_madad = details.get('current_madad', 0)
                    price_memduad_diff = sale.price_final - memudad
                else:
                    logger.warning('sale #%(sale_id)s has no commission details', {'sale_id': s.id})
                    latest_doh0price, memudad, current_madad, price_memduad_diff = 0,0,0,0
                
                row.extend([log2vis(s.clients), '%s/%s' % (str(s.house.building), str(s.house)), 
                            s.sale_date.strftime('%d/%m/%y'), commaise(s.price_final), commaise(latest_doh0price), 
                            current_madad, commaise(memudad), commaise(price_memduad_diff), commaise(s.zdb)])

                row.reverse()
                rows.append(row)
                
                total_prices += s.price
                total_adds += s.zdb
                total_doh0price += latest_doh0price
                total_memudad += memudad
                total_diff += price_memduad_diff
 
            if demand.zilber_cycle_index() == 1:
                break
            
            demand = demand.get_previous_demand()
            
        sum_row = [Paragraph(log2vis(u'סה"כ'), styleSaleSumRow), None, None, None, None, 
                   Paragraph(commaise(total_prices), styleSaleSumRow), 
                   Paragraph(commaise(total_doh0price), styleSaleSumRow),
                   None,
                   Paragraph(commaise(total_memudad), styleSaleSumRow), 
                   Paragraph(commaise(total_diff), styleSaleSumRow), 
                   Paragraph(commaise(round(total_adds)), styleSaleSumRow)]
        
        sum_row.reverse()
        rows.append(sum_row)
        data = [headers]
        data.extend(rows)
        t = Table(data, colWidths, style = saleTableStyle, repeatRows = 1)
        flows.append(t)
        return flows
    
    def zilberAddsFlows(self):
        logger = logging.getLogger('pdf')
        logger.info('starting zilberAddsFlows')
        
        flows = [tableCaption(caption=log2vis(u'נספח א - הפרשי קצב מכירות לדרישה')),
                 Spacer(0,30)]
        headers = [log2vis(n) for n in [u'דרישה\nחודש', u'שם הרוכשים', u'ודירה\nבניין',u'מכירה\nתאריך', u'חוזה\nמחיר', u'עמלה\nלחישוב\nמחיר',
                                        u'בדרישה\nעמלה',u'חדשה\nעמלה', u'הפרש\nאחוז', u'בש"ח\nהפרש']]
        colWidths = [None,80,None,None,None,None,None,None,None,None]
        colWidths.reverse()
        headers.reverse()
        rows = []
        demand = self.demand
        sales = demand.sales_list
        total_prices, total_prices_finals, total_adds = 0, 0, 0
        
        while demand.zilber_cycle_index() > 1:
            demand = demand.get_previous_demand()
            # adds sales of the current demand before the sales we already have because we are iterating in reverse
            demand_sales = demand.sales_list
            demand_sales.extend(sales)
            sales = demand_sales
                
        for s in sales:
            # get the pc_base as it was in the actual demand
            orig_pc_base = s.pc_base
            
            # get the pc_base at the moment of the current demand being calculated - ignoring the future sales
            s.restore_date = self.demand.finish_date
            current_pc_base = s.pc_base
            diff_pc_base = current_pc_base - orig_pc_base
            
            # set the restore date to the default
            s.restore_date = s.actual_demand.finish_date
            
            sale_add = diff_pc_base * s.price_final / 100
            
            row = [log2vis('%s/%s' % (s.actual_demand.month, s.actual_demand.year)), clientsPara(s.clients), 
                   '%s/%s' % (str(s.house.building), str(s.house)), s.sale_date.strftime('%d/%m/%y'), 
                   commaise(s.price), commaise(s.price_final), orig_pc_base, current_pc_base, diff_pc_base, commaise(sale_add)]

            row.reverse()
            rows.append(row)
            total_prices += s.price
            total_prices_finals += s.price_final
            total_adds += round(sale_add)
             
        sum_row = [Paragraph(log2vis(u'סה"כ'), styleSaleSumRow), None, None, None, Paragraph(commaise(total_prices), styleSaleSumRow),
                   Paragraph(commaise(total_prices_finals), styleSaleSumRow), None, None, None, 
                   Paragraph(commaise(total_adds), styleSaleSumRow)]
        sum_row.reverse()
        rows.append(sum_row)
        data = [headers]
        data.extend(rows)
        t = Table(data, colWidths, style = saleTableStyle, repeatRows = 1)
        flows.append(t)
        return flows
                        
    def signupFlows(self):
        flows = [tableCaption(caption=log2vis(u'להלן תוספות להרשמות מחודשים קודמים')),
                 Spacer(0,30)]
        headers = [log2vis(n) for n in [u'הרשמה\nתאריך',u'דרישה\nחודש', u'הרוכשים\nשם', u'ודירה\nבניין', 
                                        u'חוזה\nתאריך',u'חוזה\nמחיר', u'ששולמה\nעמלה', 
                                        u'חדשה\nעמלה', u'עמלה\nהפרש', u'בש"ח\nהפרש']]
        headers.reverse()
        colWidths = [None,None,80,None,None,None,35,30,30,None]
        colWidths.reverse()
        rows = []
        total = 0

        for subSales in self.demand.get_affected_sales().values():
            for s in subSales.all():
                singup = s.house.get_signup() 
                row = [singup.date.strftime('%d/%m/%y'), '%s/%s' % (s.contractor_pay_month, s.contractor_pay_year), 
                       clientsPara(s.clients), '%s/%s' % (str(s.house.building), str(s.house)), 
                       s.sale_date.strftime('%d/%m/%y'), commaise(s.price)]
                s.restore_date = self.demand.get_previous_demand().finish_date
                c_final_old = s.c_final
                s.restore_date = self.demand.finish_date
                c_final_new = s.c_final
                diff = c_final_new - c_final_old
                total += int(diff * s.price_final / 100)
                row.extend([c_final_old, c_final_new, diff, commaise(diff * s.price_final / 100)])
                row.reverse()
                rows.append(row)

        sum_row = [Paragraph(log2vis(u'סה"כ'), styleSaleSumRow),None,None,None,None,None,None,None,None,Paragraph(commaise(total), styleSaleSumRow)]
        sum_row.reverse()
        rows.append(sum_row)      
        data = [headers]
        data.extend(rows)
        t = Table(data, colWidths, style = saleTableStyle, repeatRows = 1)
        flows.append(t)
        return flows
    def signup_counts_para(self):
        s = log2vis(u'סה"כ הרשמות מצטבר לחישוב עמלה') + '<br/>'
        s += log2vis(u', '.join(u'%s מ - %s/%s' % (count, month[0], month[1]) 
                                for month, count in self.demand.get_signup_months().items())) + '<br/>'
        count = 0
        for subSales in self.demand.get_affected_sales().values():
            count += subSales.count()
        s += log2vis(u' + %s מחודשים קודמים' % count)
        return Paragraph(s, ParagraphStyle('signup_months', fontName='David', fontSize=10, alignment=TA_CENTER))
    def saleFlows(self):
        sales = self.demand.sales_list
        names = [u'מס"ד']
        colWidths = [35]
        contract_num, discount, final = False, False, False
        zilber = self.demand.project.is_zilber()
        
        if sales[0].contract_num != None:
            names.append(u"חוזה\nמס'")
            colWidths.append(40)
            contract_num = True
        if self.signup_adds:
            names.append(u'הרשמה\nתאריך')
            colWidths.append(None)
        names.extend([u'שם הרוכשים',u'ודירה\nבניין',u'מכירה\nתאריך', u'חוזה\nמחיר'])
        colWidths.extend([65, None,None,45])
        
        if zilber:
            names.extend([u'רישום\nהוצאות',u'מזומן\nהנחת', u'מפרט\nהוצאות',u'עו"ד\nשכ"ט', u'נוספות\nהוצאות'])
            colWidths.extend([30,30,30,None,30])

        if not self.demand.project.id == 5:
            if sales[0].discount or sales[0].allowed_discount:
                names.extend([u'ניתן\nהנחה\n%',u'מותר\nהנחה\n%'])
                colWidths.extend([None,None])
                discount = True
                
        names.extend([u'עמלה\nלחישוב\nמחיר', u'בסיס\nעמלת\n%',u'בסיס\nעמלת\nשווי'])
        colWidths.extend([45,None,None])

        commissions = self.commissions

        if commissions.b_discount_save_precentage:
            names.extend([u'חסכון\nבונוס\n%',u'חסכון\nבונוס\nשווי', u'סופי\nעמלה\n%',u'סופי\nעמלה\nשווי'])
            colWidths.extend([30,30,None,None])
            final = True
        colWidths.reverse()
        names.reverse()
        headers = [log2vis(name) for name in names]
        i=1
        flows = [tableCaption(), Spacer(0,10)]
        if self.signup_adds:
            flows.extend([self.signup_counts_para(), Spacer(0,10)])
        rows = []
        total_lawyer_pay, total_pc_base_worth, total_pb_dsp_worth = 0, 0 ,0
        
        commissions = self.commissions
        
        for s in sales:
            s.restore = True
            row = ['%s-%s' % (self.demand.id, i)]
            if contract_num:
                row.append(s.contract_num)
            if self.signup_adds:
                signup = s.house.get_signup()
                row.append(signup and signup.date.strftime('%d/%m/%y') or '')
            row.extend([clientsPara(s.clients), '%s/%s' % (str(s.house.building), str(s.house)), 
                        s.sale_date.strftime('%d/%m/%y'), commaise(s.price)])
            if zilber:
                if commissions.deduct_registration and s.include_registration:
                    row.append(commaise(commissions.registration_amount))
                else:
                    row.append(None)
                lawyer_pay = s.price_include_lawyer and (s.price - s.price_no_lawyer) or s.price * 0.015
                total_lawyer_pay += lawyer_pay
                row.extend([None,commaise(s.specification_expense),commaise(lawyer_pay),commaise(s.other_expense)])

            if discount:
                row.extend([s.discount, s.allowed_discount])
                
            row.extend([commaise(s.price_final),s.pc_base, commaise(s.pc_base_worth)])
            total_pc_base_worth += s.pc_base_worth
            
            if final:
                row.extend([s.pb_dsp, commaise(s.pb_dsp_worth), s.c_final, commaise(s.c_final_worth)])
                total_pb_dsp_worth += s.pb_dsp_worth
                
            row.reverse()#reportlab prints columns ltr
            rows.append(row)
            i+=1

        row = [Paragraph(log2vis(u'סה"כ'), styleSaleSumRow)]
        if contract_num:
            row.append(None)
        if self.signup_adds:
            row.append(None)
        row.extend([None,Paragraph(log2vis('%s' % self.demand.sales_count), styleSaleSumRow),None])
        row.append(Paragraph(commaise(self.demand.sales_total_price), styleSaleSumRow))
        if zilber:
            row.extend([None,None,None,Paragraph(commaise(total_lawyer_pay), styleSaleSumRow),None])
        if discount:
            row.extend([None,None])
        if final:
            row.extend([None,Paragraph(commaise(total_pc_base_worth), styleSaleSumRow),
                        None,Paragraph(commaise(total_pb_dsp_worth), styleSaleSumRow),
                        None,Paragraph(commaise(self.demand.sales_commission), styleSaleSumRow)])
        else:
            row.extend([Paragraph(commaise(self.demand.sales_amount), styleSaleSumRow),
                        None,Paragraph(commaise(self.demand.sales_commission), styleSaleSumRow)])
        row.reverse()
        rows.append(row)
        data = [headers]
        data.extend(rows)
        t = Table(data, colWidths, style = saleTableStyle, repeatRows = 1)
        flows.append(t)
        
        return flows
    def remarkPara(self):
        s = '<b><u>%s</u></b><br/>' % log2vis(u'הערות לדרישה')
        remarks = self.demand.remarks
        if remarks != None and len(remarks.lstrip().rstrip())>0:
            s += log2vis(remarks.lstrip().rstrip())
        else:
            s += log2vis(u'אין')
        return Paragraph(s, ParagraphStyle(name='remarkPara', fontName='David', fontSize=13, 
                                           leading=16, alignment=TA_RIGHT))
    def addsPara(self):
        s = '<br/>'.join([log2vis(u'%s - %s ש"ח' % (d.reason, commaise(d.amount))) for d in self.demand.diffs.all()]) + '<br/>'
        s += '<b>%s</b>' % log2vis(u'סה"כ : %s ש"ח' % commaise(self.demand.total_amount)) + '<br/>'
        return Paragraph(s, ParagraphStyle(name='addsPara', fontName='David', fontSize=14, 
                                           leading=16, alignment=TA_LEFT))
    def get_story(self):
        story = [Spacer(0,100)]
        title = u'הנדון : עמלה לפרויקט %s לחודש %s/%s' % (self.demand.project, 
                                                          self.demand.month, 
                                                          self.demand.year)
        story.append(titlePara(title))
        story.append(Spacer(0, 10))
        subTitle = u"דרישה מס' %s" % self.demand.id
        if self.demand.project.is_zilber():
            subTitle += u' (%s מתוך %s)' % (self.demand.zilber_cycle_index(), models.CZilber.Cycle)

        story.append(Paragraph('<u>%s</u>' % log2vis(subTitle), styleSubTitleBold))
        story.extend([Spacer(0,20), self.introPara(), Spacer(0,20)])
        story.extend(self.saleFlows())
        if self.demand.diffs.count() > 0:
            story.extend([Spacer(0, 20), self.addsPara()])
        if self.demand.project.is_zilber() and (self.demand.include_zilber_bonus() or not self.to_mail):
            story.extend([PageBreak(), Spacer(0,30)])
            story.extend(self.zilberAddsFlows())
            story.extend([PageBreak(), Spacer(0,30)])
            story.extend(self.zilberBonusFlows())
        story.extend([Spacer(0, 20), self.remarkPara(), sigPara()]) 
        if self.signup_adds:
            story.extend([PageBreak(), Spacer(0,30), titlePara(u'נספח א')])
            story.extend(self.signupFlows())
        return story

class MultipleDemandWriter(DocumentBase):
    
    def __init__(self, demands, title, show_project, show_month):
        self.demands = demands
        self.title = title
        self.show_month = show_month
        self.show_project = show_project

    def projectsFlows(self):
        
        fields = []
        if self.show_project:
            fields.extend([ProjectNameAndCityField(), ProjectInitiatorField()])
        if self.show_month:
            fields.append(MonthField())
        fields.extend([DemandSalesCountField(), DemandSalesTotalPriceField(), DemandTotalAmountField(), InvoicesNumField(),
                       InvoicesAmountField(), PaymentsNumField(), PaymentsAmountField()])
        fields.reverse()
        builder = Builder(self.demands, fields)
        table = builder.build()
        tableFlow = Table(table.rows, table.col_widths(), table.row_heights(), projectTableStyle, 1)
        return [tableFlow]
    
    def get_pagesize(self):
        '''
        Override the default page size to be landscape
        '''
        return landscape(A4)
    
    def get_story(self):
        story = [titlePara(self.title), Spacer(0, 10)]
        story.extend(self.projectsFlows())
        return story

class EmployeeSalariesBookKeepingWriter(DocumentBase):
    def __init__(self, salaries, title, nhsales = None):
        self.salaries, self.title, self.nhsales = salaries, title, nhsales
    def nhsalesFlows(self):
        flows = []
        headers = [log2vis(n) for n in [u'מס"ד',u'הרוכשים\nשם',u'התשלום\nסכום',u"תיווך\nשרותי\nהזמנת\nמס'",u'חשבונית',
                                        u"זמנית\nקבלה\nמס'",u'תשלום\nסוג',u"מס' צ'ק",u'בנק',u'מטפל\nסוכן',
                                        u'תשלום\nתאריך',u"סניף\nמס'",u'הערות']]
        headers.reverse()
        colWidths = [None, 70, None, None, 40, None, None, 40, None, 70, None, None, 20]
        colWidths.reverse()
        rows = []
        remarks_str = ''

        for s in self.nhsales:
            for side in s.nhsaleside_set.all():
                clients = log2vis(side.name1) + '<br/>' + log2vis(side.name2 or '')
                invoice = side.invoices.count() > 0 and side.invoices.all()[0]
                if invoice:
                    invoice_str = '%s<br/>%s' % (invoice.date.strftime('%d/%m/%y'), invoice.num and str(invoice.num) or '')
                else:
                    invoice_str = ''
                invoice_para = Paragraph(invoice_str, styleRow9)
                payments = side.payments.all()
                row = [s.num, Paragraph(clients, styleRow9), commaise(side.net_income), side.voucher_num, 
                       invoice_para, side.temp_receipt_num, 
                       Paragraph('<br/>'.join([log2vis(str(p.payment_type)) for p in payments]), styleRow9),
                       Paragraph('<br/>'.join([str(p.num) for p in payments]), styleRow9),
                       Paragraph('<br/>'.join([log2vis(p.bank) for p in payments]), styleRow9),
                       log2vis(str(side.signing_advisor)),
                       Paragraph('<br/>'.join([p.payment_date.strftime('%d/%m/%y') for p in payments]), styleRow9),
                       Paragraph('<br/>'.join([str(p.branch_num) for p in payments]), styleRow9),
                       side.remarks and '*']
                row.reverse()
                rows.append(row)
                if side.remarks:
                    remarks_str += log2vis(side.name1 + ' ' + (side.name2 or '') + ' - ' + side.remarks) + '<br/>'
                
        data = [headers]
        data.extend(rows)
        t = Table(data, colWidths, style = nhsalariesTableStyle, repeatRows = 2)
        flows.append(t)
            
        flows.append(Spacer(0,10))
        flows.append(Paragraph(remarks_str, styleNormal13))
        flows.append(Spacer(0,10))
        flows.append(Paragraph(log2vis(u'לתשומת לבך'), styleSubTitleBold))
        flows.append(Spacer(0,10))
        flows.append(Paragraph(log2vis(u"יש להוציא את השכר לעובדים לאחר בדיקה שכל הצ'קים התקבלו והחשבוניות הוצאו."), styleNormal13))
        flows.append(Paragraph(log2vis(u"במידה ויש צ'קים דחויים\או שלא הגיעו נא לעדכן את אלי."), styleNormal13))
        return flows
    def salariesFlows(self):
        flows = []
        headers = [log2vis(n) for n in [u'מס"ד',u'העובד\nשם',u'העסקה\nסוג',u'לתשלום\nשווי צק',u'הוצאות\nהחזר',
                                        u'ברוטו\nשווי',u'חשבונית\nשווי',u'ניכוי מס\nשווי',u'הלוואה\nהחזר',u'תלוש נטו\nשווי',
                                        u'הערות']]
        groups = [log2vis(u'לשימוש הנה"ח בלבד'), None, None, None, None, None, log2vis(u'תשלום צקים לעובד')]
        headers.reverse()
        colWidths = [None, 50, None, None, None, None, None, None, None, None, None]
        colWidths.reverse()
        rows = []
        remarks_str = ''

        for es in self.salaries:
            employee = es.get_employee()
            terms = employee.employment_terms
            hire_type = terms and str(terms.hire_type) or ''
            if terms and not terms.salary_net and terms.hire_type.id == models.HireType.Salaried:
                hire_type += u' - ברוטו'
            
            check_amount = terms.salary_net == False and Paragraph(break_to_lines(u"הנהלת חשבונות"), styleRow9) or commaise(es.check_amount)
            row = [es.id, Paragraph(break_to_lines(str(employee)), styleRow9), '', check_amount, commaise(es.refund),
                   commaise(es.bruto),commaise(es.invoice_amount),None,commaise(es.loan_pay), commaise(es.neto), es.pdf_remarks and '*' or '']
            row.reverse()
            rows.append(row)
            
            if es.pdf_remarks:
                remarks_str += '<u><b>' + log2vis(str(employee)) + '</b></u>' + ' ' + log2vis(es.pdf_remarks) + '<br/>'
        
        sum_row = [None, None, None, 
                   commaise(sum([s.check_amount or 0 for s in self.salaries])),
                   commaise(sum([s.refund or 0 for s in self.salaries])),
                   commaise(sum([s.bruto or 0 for s in self.salaries])),
                   commaise(sum([s.invoice_amount or 0 for s in self.salaries])), None,
                   commaise(sum([s.loan_pay or 0 for s in self.salaries])),
                   commaise(sum([s.neto or 0 for s in self.salaries])), None]
        sum_row = [value and Paragraph(value, styleSumRow) or None for value in sum_row]
        sum_row.reverse()
        rows.append(sum_row)
        
        data = [groups, headers]
        data.extend(rows)
        t = Table(data, colWidths, style = salariesTableStyle, repeatRows = 2)
        flows.append(t)
                
        if remarks_str:
            flows.append(Spacer(0,10))
            flows.append(Paragraph(remarks_str, styleNormal13))
        
        return flows
    def get_story(self):
        story = [Spacer(0,50)]
        story.append(titlePara(self.title))
        story.append(Spacer(0, 10))
        story.extend(self.salariesFlows())
        if self.nhsales:
            story.extend([PageBreak(),titlePara(u"אישור צ'קים וחשבוניות"),Spacer(0,20)])
            story.extend(self.nhsalesFlows())
        return story

class EmployeeSalariesWriter:
    def __init__(self, salaries, title, show_employee, show_month):
        self.salaries, self.title, self.show_employee, self.show_month = salaries, title, show_employee, show_month

    def __chopLine(self, line, maxline):
        cant = len(line) / maxline
        cant += 1
        strline = ""
        index = maxline
        for i in range(1,cant):
            index = maxline * i
            strline += "%s\n" %(line[(index-maxline):index])
        strline += "%s\n" %(line[index:])
        return strline

    @property
    def pages_count(self):
        return len(self.salaries) / 28 + 1
    def addTemplate(self, canv, doc):
        frame2 = Frame(0, 680, 650, 150)
        frame2.addFromList([nhLogo(), datePara()], canv)
        frame3 = Frame(50, 20, 150, 40)
        frame3.addFromList([Paragraph(log2vis(u'עמוד %s מתוך %s' % (self.current_page, self.pages_count)), 
                            ParagraphStyle('pages', fontName='David', fontSize=13,))], canv)
        frame4 = Frame(50, 30, 500, 70)
        frame4.addFromList([nhAddr()], canv)
        self.current_page += 1
    def salariesFlows(self):
        flows = []
        headers = []
        if self.show_employee:
            headers.append(log2vis(u'העובד\nשם'))
        if self.show_month:
            headers.append(log2vis(u'חודש'))
        headers.append(log2vis(u'העסקה\nסוג'))
        headers.append(log2vis(u'מכירות\nמספר'))
        headers.append(log2vis(u'בסיס\nשכר'))
        headers.append(log2vis(u'עמלות'))
        headers.append(log2vis(u'ביטחון\nרשת'))
        headers.append(log2vis(u'משתנה\nתוספת'))
        headers.append(log2vis(u'שכר\nקיזוז'))
        headers.append(log2vis(u'הלוואה\nהחזר'))
        headers.append(log2vis(u'הערות'))
        headers.append(log2vis(u'הצק\nסכום'))
        headers.reverse()
        colWidths = [None,None,None,None,None,None,None,None,None,None,None]
        colWidths.reverse()
        rows = []
        i = 0
        for es in self.salaries:
            employee = es.get_employee()
            terms = employee.employment_terms
            row = []
            if self.show_employee:
                row.append(log2vis(str(employee)))
            if self.show_month:
                row.append('%s/%s' % (es.month, es.year))

            total_sales = 0

            for p, sales in es.sales.items() :
                total_sales += len(sales)
                
            row.extend([log2vis(u'%s - %s' % (terms.hire_type.name, terms.salary_net and u'נטו' or u'ברוטו'))])

            row.append(commaise(total_sales))
            row.append(commaise(es.base))
            row.append(commaise(es.commissions))
            row.extend([log2vis(u'%s' % ( es.safety_net and es.safety_net or '' ))])

            if es.var_pay :
                row.extend([log2vis(u'%s' % ( commaise(es.var_pay) ))])
            else :
                row.append('')

            if es.deduction :
                row.extend([log2vis(u'%s' % ( commaise(es.deduction) ))])
            else :
                row.append('')

            row.extend([log2vis(u'יתרה - %s\nהחזרה - %s' % (commaise( employee.loan_left and employee.loan_left() or 0 ), commaise(es.loan_pay) ))])
            row.extend([log2vis(u'%s' % ( es.remarks and ( '\n'.join( textwrap.fill( es.remarks, 15 ).split('\n')[::-1] ) ) or '' ))])

            row.append(commaise(es.check_amount))
            row.reverse()
            rows.append(row)
            i += 1
            if i % 27 == 0 or i == len(self.salaries):
                data = [headers]
                data.extend(rows)
                t = Table(data, colWidths)
                t.setStyle(saleTableStyle)
                flows.append(t)
                if i < len(self.salaries):
                    flows.extend([PageBreak(), Spacer(0, 50)])
                rows = []

        return flows
    def build(self, filename):
        self.current_page = 1
        doc = SimpleDocTemplate(filename)
        story = [Spacer(0,50)]
        story.append(titlePara(self.title))
        story.append(Spacer(0, 10))
        story.extend(self.salariesFlows())
        doc.build(story, self.addTemplate, self.addTemplate)
        return doc.canv
    
class EmployeeSalariesSeasonExpensesWriter:
        def __init__(self, salaries, title):
            self.salaries, self.title = salaries, title
        def flows(self):
            project_fields = [MonthField()]
            employee_fields = [EmployeeHireTypeField()]
            project_fields = [ProjectNameAndCityField()]
            employee_salary_fields = [EmployeeSalarySalesField(), EmployeeSalaryNetoField(), EmployeeSalaryLoanPayField(), 
                                      EmployeeSalaryCheckAmountField()]
            salary_expenses_fields = [SalaryExpensesIncomeTaxField(), SalaryExpensesNationalInsuranceField(),
                                      SalaryExpensesHealthField(), SalaryExpensesPensionInsuranceField(),
                                      SalaryExpensesVacationField(), SalaryExpensesConvalescencePayField()]
            employee_salary_fields2 = [EmployeeSalaryBrutoField()]
            salary_expenses_fields2 = [SalaryExpensesNationalInsuranceField, SalaryExpensesEmployerBenefitField(),
                                       SalaryExpensesCompensationAllocationField()]
            employee_salary_fields3 = [EmployeeSalaryBrutoWithEmployerField()]


class EmployeesLoans:
    def __init__(self, employee):
        self.loans = employee.loans_and_pays
        self.title = u'פירוט הלוואות לעובד - %s' % ( employee )
    @property
    def pages_count(self):
        return len(self.loans) / 28 + 1
    def addTemplate(self, canv, doc):
        frame2 = Frame(0, 680, 650, 150)
        frame2.addFromList([nhLogo(), datePara()], canv)
        frame3 = Frame(50, 20, 150, 40)
        frame3.addFromList([Paragraph(log2vis(u'עמוד %s מתוך %s' % (self.current_page, self.pages_count)),
                            ParagraphStyle('pages', fontName='David', fontSize=13,))], canv)
        frame4 = Frame(50, 30, 500, 70)
        frame4.addFromList([nhAddr()], canv)
        self.current_page += 1
    def loansFlow(self):
        flows = []
        headers = [log2vis(n) for n in [u'תאריך',
                                        u'פעולה',
                                        u'הלוואה\nסך',
                                        u'החזר\nסך',
                                        u'יתרה',
                                        u'מהשכר\nמקוזז',
                                        u'הערות' ]]
        colWidths = [None for header in headers]
        headers.reverse()
        colWidths.reverse()
        rows = []
        i = 0
        for s in self.loans:
            i+=1

            deduct_from_salary = ''

            row = []
            row.append( '%s/%s' % (s.month, s.year) )

            try :
                paynum = s.pay_num

                row.append(log2vis(u'הלוואה')),
                row.append(log2vis(commaise(s.amount))),
                row.append(log2vis(''))
            except :
                row.append(log2vis(u'קיזוז'))
                row.append(log2vis('')),
                row.append(log2vis(commaise(s.amount)))

            row.append( log2vis(commaise( s.left )) )

            try :
                deduct_from_salary = s.deduct_from_salary

                row.append(log2vis(deduct_from_salary == True and u'כן' or u'לא'))
            except :
                row.append('')

            row.append( log2vis(s.remarks and s.remarks or '') )

            row.reverse()
            rows.append(row)

            if len(rows) % 27 == 0 or i == len(self.loans):
                data = [headers]
                data.extend(rows)
                t = Table(data, colWidths)
                t.setStyle(saleTableStyle)
                flows.append(t)
                if i < len(self.loans):
                    flows.extend([PageBreak(), Spacer(0, 50)])
                rows = []

        return flows
    def build(self, filename):
        self.current_page = 1
        doc = SimpleDocTemplate(filename)
        story = [Spacer(0,50)]
        story.append(titlePara(self.title))
        story.append(Spacer(0, 10))
        story.extend(self.loansFlow())
        doc.build(story, self.addTemplate, self.addTemplate)
        return doc.canv


class SalariesBankWriter:
    def __init__(self, salaries, month, year):
        self.salaries = salaries
        self.title = u'שכר להעברה בנקאית לחודש %s/%s' % (month, year)
    @property
    def pages_count(self):
        return len(self.salaries) // 28 + 1
    def addTemplate(self, canv, doc):
        frame2 = Frame(0, 680, 650, 150)
        frame2.addFromList([nhLogo(), datePara()], canv)
        frame3 = Frame(50, 20, 150, 40)
        frame3.addFromList([Paragraph(log2vis(u'עמוד %s מתוך %s' % (self.current_page, self.pages_count)), 
                            ParagraphStyle('pages', fontName='David', fontSize=13,))], canv)
        frame4 = Frame(50, 30, 500, 70)
        frame4.addFromList([nhAddr()], canv)
        self.current_page += 1
    def salariesFlows(self):
        logger = logging.getLogger('pdf')
        logger.info('starting to write %(salary_count)s salaries for bank', {'salary_count':len(self.salaries)})
        
        flows = []
        headers = [log2vis(n) for n in [u'העובד\nמס', u'פרטי\nשם', u'משפחה\nשם', u'ת.ז', u'המוטב\nשם', u'להעברה\nסכום', u'חשבון\nמספר', u'בנק',
                                        u'סניף\nכתובת', u'סניף\nמספר', u'הערות']]
        colWidths = [None for header in headers]
        headers.reverse()
        colWidths.reverse()
        rows = []
        i = 0
        for salary in self.salaries:
            i+=1
            employee = salary.get_employee()
            if salary.neto:
                account = employee.account
                if not account:
                    account = models.Account()
                    
                row = [employee.id, log2vis(employee.first_name), log2vis(employee.last_name), employee.pid, log2vis(employee.payee),
                       commaise(salary.neto), account.num, log2vis(account.bank), log2vis(account.branch), account.branch_num, '']
                
                row.reverse()
                rows.append(row)
            else:
                logger.warn('skipping salary for employee #%(employee_id)s - %(employee_name)s because he does not have neto salary',
                            {'employee_id':employee.id, 'employee_name':employee})
                
            if (len(rows) > 0 and len(rows) % 27 == 0) or i == len(self.salaries):
                data = [headers]
                data.extend(rows)
                t = Table(data, colWidths)
                t.setStyle(saleTableStyle)
                flows.append(t)
                if i < len(self.salaries):
                    flows.extend([PageBreak(), Spacer(0, 50)])
                rows = []

        logger.info('finished writing salaries for bank')

        return flows
    def build(self, filename):
        self.current_page = 1
        doc = SimpleDocTemplate(filename)
        story = [Spacer(0,50)]
        story.append(titlePara(self.title))
        story.append(Spacer(0, 10))
        story.extend(self.salariesFlows())
        doc.build(story, self.addTemplate, self.addTemplate)
        return doc.canv

class PricelistWriter:
    def __init__(self, pricelist, houses, title, subtitle):
        self.pricelist, self.houses, self.title, self.subtitle = pricelist, houses, title, subtitle
    @property
    def pages_count(self):
        return len(self.houses) / 28 + 2
    def addTemplate(self, canv, doc):
        frame3 = Frame(50, 20, 150, 40)
        frame3.addFromList([Paragraph(log2vis(u'עמוד %s מתוך %s' % (self.current_page, self.pages_count)), 
                            ParagraphStyle('pages', fontName='David', fontSize=13,))], canv)
        frame4 = Frame(50, 670, 500, 70)
        frame4.addFromList([titlePara(self.title), Paragraph(log2vis(self.subtitle), styleSubTitle)], canv)
        self.current_page += 1
    def housesFlows(self):
        flows = []
        headers = [log2vis(n) for n in [u'מס', u'קומה', u'דירה\nסוג', u'חדרים\nמס', u'נטו\nשטח', u'גינה\nמרפסת/\nשטח', u'מחיר',
                                        u'חניה', u'מחסן', u'הערות']]
        headers.reverse()
        colWidths = [None,None,70,None,None,None,None,None,None,None]
        colWidths.reverse()
        rows = []
        i = 0
        for h in self.houses:
            parkings = '<br/>'.join([log2vis(str(p.num)) for p in h.parkings.all()])
            storages = '<br/>'.join([log2vis(str(s.num)) for s in h.storages.all()])
            row = [h.num, h.floor,  log2vis(str(h.type)), h.rooms, h.net_size, h.garden_size, 
                   h.price and commaise(h.price) or '-', Paragraph(parkings, styleRow), Paragraph(storages, styleRow), 
                   log2vis(h.remarks[:15] + (len(h.remarks)>15 and ' ...' or ''))]
            row.reverse()
            rows.append(row)
            i += 1
            if i % 27 == 0:
                data = [headers]
                data.extend(rows)
                t = Table(data, colWidths)
                t.setStyle(saleTableStyle)
                flows.append(t)
                if i < len(self.houses):
                    flows.extend([PageBreak(), Spacer(0, 80)])
                rows = []
        row = [None, None, None, None, None, None, None, None, 
               Paragraph(log2vis(u'סה"כ'), styleSumRow), Paragraph(str(len(self.houses)), styleSumRow)]
        row.reverse()
        rows.append(row)
        data = [headers]
        data.extend(rows)
        t = Table(data, colWidths)
        t.setStyle(saleTableStyle)
        flows.append(t)
        return flows
    def build(self, filename):
        self.current_page = 1
        doc = SimpleDocTemplate(filename)
        story = [Spacer(0,80)]
        story.extend(self.housesFlows())
        story.extend([PageBreak(), Spacer(0,80)])
        settle_date = self.pricelist.settle_date
        story.append(Paragraph(log2vis(u'מועד אכלוס : ' + (settle_date and settle_date.strftime('%d/%m/%Y') or '----')),
                               ParagraphStyle('1', fontName='David',fontSize=14, leading=15, alignment=TA_RIGHT)))
        story.append(Paragraph(log2vis('מדד תשומות הבנייה : ' + str(models.MadadBI.objects.latest().value)),
                               ParagraphStyle('1', fontName='David',fontSize=14, leading=15, alignment=TA_LEFT)))
        include_str = log2vis(u'המחיר כולל : ' + ', '.join(gettext(attr) for attr in ['tax','lawyer','parking','storage','registration','guarantee']
                                                           if getattr(self.pricelist, 'include_' + attr)))
        story.append(Paragraph(include_str, ParagraphStyle('1', fontName='David',fontSize=14, leading=15, alignment=TA_RIGHT)))
        include_str = log2vis(u'היתר : ' + (self.pricelist.is_permit and u'יש' or u'אין'))
        story.append(Paragraph(include_str, ParagraphStyle('1', fontName='David',fontSize=14, leading=15, alignment=TA_LEFT)))
        notinclude_str = u'המחיר אינו כולל : מס רכישה כחוק'
        if self.pricelist.include_registration == False:
            notinclude_str += ', %s  (%s)' % (gettext('register_amount'), self.pricelist.register_amount)
        if self.pricelist.include_guarantee == False:
            notinclude_str += ', %s  (%s)' % (gettext('guarantee_amount'), self.pricelist.guarantee_amount)
        if self.pricelist.include_lawyer == False:
            notinclude_str += ', %s  %%(%s)' % (gettext('lawyer_fee'), self.pricelist.lawyer_fee)
        story.append(Paragraph(log2vis(notinclude_str), ParagraphStyle('1', fontName='David',fontSize=14, leading=15, alignment=TA_RIGHT)))
        story.append(Spacer(0,10))
        assets_str = '<u>%s</u><br/>' % log2vis(u'נכסים משניים פנויים')
        assets_str += log2vis(u'מחסנים : ' + ','.join(str(s.num) for s in self.pricelist.building.storages.filter(house=None))) + '<br/>'
        assets_str += log2vis(u'חניות : ' + ','.join(str(p.num) for p in self.pricelist.building.parkings.filter(house=None))) + '<br/>'
        story.append(Paragraph(assets_str, ParagraphStyle('1', fontName='David',fontSize=14, leading=15, alignment=TA_RIGHT)))
        doc.build(story, self.addTemplate, self.addTemplate)
        return doc.canv

class BuildingClientsWriter:
    def __init__(self, houses, title, subtitle):
        self.houses, self.title, self.subtitle = houses, title, subtitle
    @property
    def pages_count(self):
        return len(self.houses) / 28 + 1
    def addTemplate(self, canv, doc):
        frame3 = Frame(50, 20, 150, 40)
        frame3.addFromList([Paragraph(log2vis(u'עמוד %s מתוך %s' % (self.current_page, self.pages_count)), 
                            ParagraphStyle('pages', fontName='David', fontSize=13,))], canv)
        self.current_page += 1
    def housesFlows(self):
        flows = []
        headers = [log2vis(n) for n in [u'דירה\nמס',u'דירה\nסוג',u'נטו\nשטח',u'קומה',u'הרוכשים\nשם',u'ת.ז',u'כתובת',u'טלפונים',
                                        u'דוא"ל',u'הרשמה\nתאריך',u'חוזה\nתאריך',u'מחירון',u'חוזה\nמחיר',u'חנייה',u'מחסן',
                                        u'נלוות\nהוצאות',u'חזוי\nאכלוס\nמועד']]
        headers.reverse()
        rows = []
        total_sale_price = 0
        i = 0
        for h in self.houses:
            parkings = '<br/>'.join([log2vis(str(p.num)) for p in h.parkings.all()])
            storages = '<br/>'.join([log2vis(str(s.num)) for s in h.storages.all()])
            sale = h.get_sale()
            signup = h.get_signup()
            if sale:
                clients_name, clients_address, clients_phone = clientsPara(sale.clients), '', clientsPara(sale.clients_phone)
                sale_price = sale.price
                total_sale_price += sale.price
            else:
                clients_name, clients_address, clients_phone, sale_price = '','','',''
            row = [h.num, log2vis(str(h.type)), h.net_size, h.floor, clients_name, '', clients_address, clients_phone, 
                   '', signup and signup.date.strftime('%d/%m/%Y'), sale and sale.sale_date.strftime('%d/%m/%Y') or '',
                   h.price and commaise(h.price) or '-', commaise(sale_price), Paragraph(parkings, styleRow), Paragraph(storages, styleRow), 
                   '','']
            row.reverse()
            rows.append(row)
            i += 1
            if i % 27 == 0:
                data = [headers]
                data.extend(rows)
                t = Table(data)
                t.setStyle(saleTableStyle)
                flows.append(t)
                if i < len(self.houses):
                    flows.extend([PageBreak(), Spacer(0, 50)])
                rows = []
        sumRow = [Paragraph(str(self.houses.count()), styleSumRow),None,None,None,None,None,None,None,None,None,None,None, 
                  Paragraph(commaise(total_sale_price), styleSumRow), None, None, None, None]
        sumRow.reverse()
        rows.append(sumRow)
        data = [headers]
        data.extend(rows)
        t = Table(data)
        t.setStyle(saleTableStyle)
        flows.append(t)
        return flows
    def build(self, filename):
        self.current_page = 1
        doc = SimpleDocTemplate(filename, pagesize = landscape(A4))
        story = []
        story.append(titlePara(self.title))
        if self.subtitle:
            story.append(Paragraph(log2vis(self.subtitle), styleSubTitle))
        story.append(Spacer(0, 10))
        story.extend(self.housesFlows())
        doc.build(story, self.addTemplate, self.addTemplate)
        return doc.canv

class EmployeeSalesWriter(DocumentBase):
    def __init__(self, project, from_month, from_year, to_month, to_year, demands):
        self.project, self.from_month, self.from_year, self.to_month, self.to_year, self.demands = \
            project, from_month, from_year,to_month , to_year, demands
    def get_flows(self):
        house_fields = [HouseNumField(), HouseBuildingNumField(), HouseRoomsField(), HouseFloorField(), HouseSizeField(), 
                        HouseGardenSizeField(), HouseTypeField()]
        sale_fields = [SaleDateField(), SaleClientsField(), SalePriceTaxedField(), SaleIncludeLawyerTaxField(), SaleEmployeeNameField()]

        house_fields.reverse()
        sale_fields.reverse()
                
        flows = []
        
        for demand in self.demands:
            sales = demand.sales_list
            houses = [sale.house for sale in sales]
            
            if len(sales) == 0:
                continue
            
            flows.append(titlePara(u"%s/%s - %s מכירות" 
                                   % (demand.month, demand.year, len(sales))))
            flows.append(Spacer(0, 10))
            
            builders = [Builder(sales, sale_fields), Builder(houses, house_fields)]
                            
            mass_builder = MassBuilder(builders)
            mass_builder.build_avg_row = False
            table = mass_builder.build()
            
            tableFlow = Table(table.rows, table.col_widths(), table.row_heights(), projectTableStyle, 1)
            flows.append(tableFlow)
        
        return flows
        
    def get_story(self):
        title_str = u'דו"ח מכירות לסוכן - ' + str(self.project)
        subtitle_str = u"%s/%s - %s/%s" %(self.from_month, self.from_year, self.to_month, self.to_year)
        story = [titlePara(title_str), titlePara(subtitle_str), Spacer(0,20)]
        story.extend(self.get_flows())
        return story

class DemandPayBalanceWriter(DocumentBase):
    def __init__(self, from_month, from_year, to_month, to_year, project_demands, demand_pay_balance, all_times):
        """
        project_demands: dictionary of demands by project
        pay_balance_type: instance of DemandPayBalanceType to indicate the type of the report
        all_times: boolean to indicate if the report is limited by time range or not
        """
        self.from_month, self.from_year, self.to_month, self.to_year, self.project_demands, self.demand_pay_balance, self.all_times = \
            from_month, from_year, to_month, to_year, project_demands, demand_pay_balance, all_times
            
    def get_flows(self):
        flows = []
        
        for project, demands in self.project_demands.items():
            projectFlow = []
            projectFlow.append(titlePara(str(project)))
            projectFlow.append(Spacer(0, 10))
            
            for attr in ['demand_contact', 'payment_contact']:
                contact = getattr(project, attr)
                # skip if the project does not have some contact person
                if not contact:
                    continue
                contact_str = str(contact) + ", " + gettext('phone') + ": " + contact.phone + ", " + gettext('fax') + ": " + \
                    contact.fax + ", " + gettext('mail') + ": " + contact.mail
                style = ParagraphStyle('contact_para', fontName='David',fontSize=12, alignment=TA_CENTER)
                paragraph = Paragraph(log2vis(contact_str), style)
                projectFlow.append(paragraph)
                projectFlow.append(Spacer(0, 10))
                        
            fields = [MonthField(), DemandSalesCountField(), DemandTotalAmountField(), InvoicesNumField(), InvoicesAmountField(),
                      InvoicesDateField(), PaymentsAmountField(), PaymentsDateField()]
            
            # add fields sepecific to the pay balance type
            if self.demand_pay_balance.id == 'un-paid':
                field = DemandTotalAmountField()
                field.title = gettext('amount_yet_paid')
                field.name += "2"
                fields.append(field)
            elif self.demand_pay_balance.id == 'mis-paid':
                fields.append(DemandDiffInvoiceField())
            elif self.demand_pay_balance.id == 'partially-paid':
                fields.append(DemandDiffInvoicePaymentField())
            elif self.demand_pay_balance.id == 'all':
                fields.extend([DemandDiffInvoiceField() ,DemandDiffInvoicePaymentField()])
                
            fields.reverse()
            
            builder = Builder(demands, fields)
            table = builder.build()
            
            tableFlow = Table(table.rows, table.col_widths(), table.row_heights(), projectTableStyle, 1)
            projectFlow.append(tableFlow)
            flows.append(KeepTogether(projectFlow))
        
        return flows
    
    def get_story(self):
        title_str = u'דו"ח מצב תשלום דרישות יזמים - ' + self.demand_pay_balance.name
        
        if self.all_times == False:
            subtitle_str = u"%s/%s - %s/%s" %(self.from_month, self.from_year, self.to_month, self.to_year)
        else:
            subtitle_str = u"כל הזמנים"
            
        story = [titlePara(title_str), titlePara(subtitle_str), Spacer(0,20)]
        story.extend(self.get_flows())
        return story

class SaleAnalysisWriter(DocumentBase):
    def __init__(self, project, from_month, from_year, to_month, to_year, sales, include_clients):
        self.project, self.from_month, self.from_year, self.to_month, self.to_year, self.sales, self.include_clients = \
            project, from_month, from_year,to_month , to_year, sales, include_clients
            
    def get_flows(self):
        flows = []
        
        for (month, year), sales_gen in itertools.groupby(self.sales, lambda sale: (sale.contractor_pay_month, sale.contractor_pay_year)):
            sales = list(sales_gen)
            houses = [sale.house for sale in sales]
            
            fields = [SaleDateField()]
            if self.include_clients:
                fields.append(SaleClientsField())

            builders = [Builder(sales, fields),
                        Builder(houses, [HouseBuildingNumField(), HouseNumField(), HouseTypeField(), HouseRoomsField(), HouseSettleDateField(),
                                         HouseFloorField(), HouseSizeField(), HouseGardenSizeField(), HousePerfectSizeField()]),
                        Builder(sales, [SalePriceTaxedField(), SalePriceTaxedForPerfectSizeField()])
                        ]

            # reverse the builders and their fields
            builders.reverse()
            for builder in builders:
                builder.fields.reverse()
            
            flows.append(titlePara(u"%s/%s - %s מכירות" 
                                   % (month, year, len(sales))))
            flows.append(Spacer(0, 10))
            
            mass_builder = MassBuilder(builders)
            table = mass_builder.build()
            
            tableFlow = Table(table.rows, table.col_widths(), table.row_heights(), projectTableStyle, 1)
            flows.append(tableFlow)
        
        return flows
    
    def get_story(self):
        title_str = u'דו"ח ניתוח וריכוז מכירות - ' + str(self.project)
        subtitle_str = u"%s/%s - %s/%s" %(self.from_month, self.from_year, self.to_month, self.to_year)
        story = [titlePara(title_str), titlePara(subtitle_str), Spacer(0,20)]
        story.extend(self.get_flows())
        return story

class DemandFollowupWriter(DocumentBase):
    def __init__(self, project, from_month, from_year, to_month, to_year, demands):
        self.project, self.from_month, self.from_year, self.to_month, self.to_year, self.demands = \
            project, from_month, from_year, to_month, to_year, demands
    def demandFlows(self):
        headers_names = [u"מס'", u"חודש", u"מכירות\nמס'", u"דרישה\nסכום'", u"חשבונית\nמס'", u"סכום", u"תאריך", u"סכום",  u"תאריך", u"לחשבונית\nדרישה", u"לחשבונית\nצ'ק", u"חשבונית\nזיכוי"]
        groups_names = [u"פרטי דרישה", None, None, None, u"פרטי חשבונית", None, None,  u"פרטי צ'קים", None, u"הפרשי דרישה", None, None]
        groups_names = [u"הפרשי דרישה", None, None, u"פרטי צ'קים", None, u"פרטי חשבונית", None, None, u"פרטי דרישה"]
        headers = [log2vis(name) for name in headers_names]
        groups = [name and log2vis(name) for name in groups_names]
        colWidths = [None, None, 30, None, 35, None, 60, None, 60, None, None, 30]
        rows = []
        
        total_sales_count, total_amount, total_invoices, total_payments, total_diff_invoice, total_diff_invoice_payment = 0,0,0,0,0,0
        
        headers.reverse()
        colWidths.reverse()
        
        for demand in self.demands:
            invoices = demand.invoices.all()
            invoice_num_str = '<br/>'.join([str(invoice.num) for invoice in invoices])
            invoice_amount_str = '<br/>'.join([commaise(invoice.amount) for invoice in invoices])
            invoice_date_str = '<br/>'.join([invoice.date.strftime('%d/%m/%Y') for invoice in invoices])

            payments = demand.payments.all()
            payment_amount_str = '<br/>'.join([commaise(payment.amount) for payment in payments])
            payment_date_str = '<br/>'.join([payment.payment_date.strftime('%d/%m/%Y') for payment in payments])
            
            offsets = [invoice.offset for invoice in invoices if invoice.offset]
            offset_amount_str = '<br/>'.join([offset.amount for offset in offsets])
            
            sales_count = demand.sales_count
            
            row = [demand.id, u'%s/%s' % (demand.month, demand.year), sales_count, commaise(demand.total_amount),
                   Paragraph(invoice_num_str, styleRow9), Paragraph(invoice_amount_str, styleRow9), Paragraph(invoice_date_str, styleRow9), 
                   Paragraph(payment_amount_str, styleRow9), Paragraph(payment_date_str, styleRow9), commaise(demand.diff_invoice),
                   commaise(demand.diff_invoice_payment), Paragraph(offset_amount_str, styleRow9)]
            
            row.reverse()
            rows.append(row)

            total_sales_count += sales_count
            total_amount += demand.total_amount
            total_invoices += demand.total_amount_offset
            total_payments += (demand.payments_amount or 0)
            total_diff_invoice += demand.diff_invoice
            total_diff_invoice_payment += demand.diff_invoice_payment
        
        sumRow = [None, None, Paragraph(str(total_sales_count), styleSumRow), Paragraph(commaise(total_amount), styleSumRow), 
                  None, Paragraph(commaise(total_invoices), styleSumRow), 
                  None, Paragraph(commaise(total_payments), styleSumRow), None, Paragraph(commaise(total_diff_invoice), styleSumRow), 
                  Paragraph(commaise(total_diff_invoice_payment), styleSumRow), None]
        sumRow.reverse()
            
        data = [groups, headers]
        data.extend(rows)
        data.append(sumRow)
        
        table = Table(data, colWidths, style = demandFollowupTableStyle, repeatRows = 2)
        return [table]
        
    def get_story(self):
        title_str = u"מעקב דרישות לתקופה - " + str(self.project)
        subtitle_str = u"%s/%s - %s/%s" %(self.from_month, self.from_year, self.to_month, self.to_year)
        story = [titlePara(title_str), titlePara(subtitle_str), Spacer(0,20)]
        story.extend(self.demandFlows())
        return story
