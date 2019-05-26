from reportlab.platypus.tables import TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import *
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import darkblue, darkgreen

styleN = ParagraphStyle('normal', fontName='David',fontSize=16, leading=15, alignment=TA_RIGHT)
styleNormal13 = ParagraphStyle('normal', fontName='David',fontSize=13, leading=15, alignment=TA_RIGHT)
styleDate = ParagraphStyle('date', fontName='David',fontSize=14, leading=15)
styleRow = ParagraphStyle('sumRow', fontName='David',fontSize=11, leading=15)
styleRow9 = ParagraphStyle('sumRow', fontName='David',fontSize=9, leading=15, alignment=TA_RIGHT)
styleRow10 = ParagraphStyle('clients', fontName = 'David', fontSize=10, alignment = TA_CENTER)
styleSumRow = ParagraphStyle('Row', fontName='David-Bold',fontSize=11, leading=15, textColor=darkblue)
styleBoldGreenRow = ParagraphStyle('Row', fontName='David-Bold',fontSize=11, leading=15, textColor=darkgreen)
styleSaleSumRow = ParagraphStyle('Row', fontName='David-Bold',fontSize=9, leading=15)
styleSubj = ParagraphStyle('subject', fontName='David',fontSize=16, leading=15, alignment=TA_CENTER)
styleSubTitleBold = ParagraphStyle('subtitle', fontName='David-Bold', fontSize=15, alignment=TA_CENTER)
styleSubTitle = ParagraphStyle('subtitle', fontName='David', fontSize=15, alignment=TA_CENTER)

saleTableStyle = TableStyle(
                            [('FONTNAME', (0,0), (-1,0), 'David-Bold'),
                             ('FONTNAME', (0,1), (-1,-1), 'David'),
                             ('FONTSIZE', (0,0), (-1,-1), 9),
                             ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                             ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                             ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                             ('LEFTPADDING', (0,0), (-1,-1), 8),
                             ('RIGHTPADDING', (0,0), (-1,-1), 8),
                             ]
                            )
nhsalariesTableStyle = TableStyle(
                            [('FONTNAME', (0,0), (-1,0), 'David-Bold'),
                             ('FONTNAME', (0,1), (-1,-1), 'David'),
                             ('FONTSIZE', (0,0), (-1,-1), 9),
                             ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                             ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                             ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                             ('LEFTPADDING', (0,0), (-1,-1), 8),
                             ('RIGHTPADDING', (0,0), (-1,-1), 8),
                             ]
                            )
salariesTableStyle = TableStyle(
                            [('FONTNAME', (0,0), (-1,1), 'David-Bold'),
                             ('FONTNAME', (0,2), (-1,-1), 'David'),
                             ('SPAN',(0,0),(5,0)),
                             ('SPAN',(6,0),(-1,0)),
                             ('FONTSIZE', (0,0), (-1,-1), 10),
                             ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                             ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                             ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                             ('LEFTPADDING', (0,0), (-1,-1), 8),
                             ('RIGHTPADDING', (0,0), (-1,-1), 8),
                             ]
                            )
demandFollowupTableStyle = TableStyle(
                            [('FONTNAME', (0,0), (-1,1), 'David-Bold'),
                             ('FONTNAME', (0,2), (-1,-1), 'David'),
                             ('SPAN',(0,0),(2,0)),
                             ('SPAN',(3,0),(4,0)),
                             ('SPAN',(5,0),(7,0)),
                             ('SPAN',(8,0),(-1,0)),
                             ('FONTSIZE', (0,0), (-1,-1), 10),
                             ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                             ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                             ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                             ('LEFTPADDING', (0,0), (-1,-1), 8),
                             ('RIGHTPADDING', (0,0), (-1,-1), 8),
                             ]
                            )
projectTableStyle = TableStyle(
                               [('FONTNAME', (0,0), (-1,0), 'David-Bold'),
                                ('FONTNAME', (0,1), (-1,-1), 'David'),
                                ('FONTSIZE', (0,0), (-1,-1), 12),
                                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                                ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                                ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                                ('LEFTPADDING', (0,0), (-1,-1), 8),
                                ('RIGHTPADDING', (0,0), (-1,-1), 8),
                                ]
                               )