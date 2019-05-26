from Management.templatetags.management_extras import commaise
from styles import *
from reportlab.platypus import Paragraph
from django.utils.translation import ugettext

import decimal

class Row(list):
    def __init__(self, *args, **kw):
        super(Row, self).__init__(*args, **kw)
        self.height = None

class Col(object):
    __slots__ = ('name', 'title', 'width')
    
    def __init__(self, name, title, width):
        self.name, self.title, self.width = name, title, width

class Table(object):
    def __init__(self, cols = None, rows = None):
        self.cols, self.rows = cols or [], rows or []
    def row_heights(self):
        return [row.height for row in self.rows]
    def col_widths(self):
        return [col.width for col in self.cols]
    def __len__(self):
        return self.rows.__len__()
    def __iter__(self):
        return self.rows.__iter__()

class MassBuilder(object):
    def __init__(self, builders):
        self.builders = builders
        self.build_sum_row = self.has_sum_row
        self.build_avg_row = self.has_avg_row
        
    @property
    def has_sum_row(self):
        for builder in self.builders:
            if builder.has_sum_row:
                return True
        return False
    @property
    def has_avg_row(self):
        for builder in self.builders:
            if builder.has_avg_row:
                return True
        return False
    
    def build(self):        
        root_table = Table()
        
        for builder in self.builders:
            builder.build_sum_row = self.build_sum_row
            builder.build_avg_row = self.build_avg_row
            
            table = builder.build()
            root_table.cols.extend(table.cols)
            
            for i in range(len(table.rows)):
                if i == len(root_table.rows):
                    root_table.rows.append(Row())
                root_table.rows[i] += table.rows[i]
                root_table.rows[i].height = max(root_table.rows[i].height, table.rows[i].height)
        
        return root_table

class Builder(object):
    def __init__(self, items, fields):
        self.items = items
        self.fields = fields
        self.build_sum_row = self.has_sum_row
        self.build_avg_row = self.has_avg_row
    
    @property
    def has_sum_row(self):
        for field in self.fields:
            if field.is_commaised:
                return True
        return False
    
    @property
    def has_avg_row(self):
        for field in self.fields:
            if field.is_averaged:
                return True
        return False
    
    def _build_sum_row(self):
        sum_row = Row()
        for field in self.fields:
            if field.is_summarized:
                # exclude null values because it causes inavlid arithmatic
                col_values = [val for val in self.col_values[field.name] if val != None]
                col_sum = sum(col_values)
                cell_value = Paragraph(commaise(col_sum), styleSumRow)
            else:
                cell_value = ''
                
            sum_row.append(cell_value)
            
        return sum_row

    def _build_avg_row(self):
        avg_row = Row()
        for field in self.fields:
            if field.is_averaged:
                # exclude null values because it causes inavlid arithmatic
                col_values = [val for val in self.col_values[field.name] if val != None]
                avg = sum(col_values, 0.0) / len(col_values)
                avg = avg > 1000 and commaise(avg) or round(avg, 2)
                decimal.Decimal()
                cell_value = Paragraph(unicode(avg), styleBoldGreenRow)
            else:
                cell_value = ''

            avg_row.append(cell_value)
            
        return avg_row
    
    def build(self):
        col_values = dict([(field.name, []) for field in self.fields])
        
        cols = [Col(field.name, field.title, field.width) for field in self.fields]
        
        if not cols:
            return Table()
        
        table = Table(cols = cols)
        
        title_row = Row([unicode(field.title) for field in self.fields])
        
        table.rows.append(title_row)
            
        for item in self.items:
            row = Row()
            
            for field in self.fields:
                cell_value = field.format(item)
                row.height = max(row.height, field.get_height(item))
                
                col_values[field.name].append(cell_value)
                    
                if field.is_commaised:
                    cell_value = commaise(cell_value)
    
                row.append(cell_value)
                
            table.rows.append(row)
        
        self.col_values = col_values
        
        if self.build_sum_row:
            sum_row = self._build_sum_row()
            table.rows.append(sum_row)
            
        if self.build_avg_row:
            avg_row = self._build_avg_row()
            table.rows.append(avg_row)

        return table