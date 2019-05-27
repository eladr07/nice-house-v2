import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import os

gmail_user = "nevehair@gmail.com"
gmail_pwd = "nevehair123"

def mail(to, cc='', bcc='', subject='', contents='', attachments = ()):
    msg = MIMEMultipart()

    msg['From'] = gmail_user
    msg['To'] = to
    msg['Cc'] = cc
    msg['Bcc'] = bcc
    msg['Subject'] = subject

    msg.attach(MIMEText(contents))
    
    for attachment in attachments:
        part = MIMEBase('application', 'octet-stream')
        if isinstance(attachment, str):
            attachment_file = open(attachment)
        else:
            attachment_file = attachment
            
        payload = attachment_file.read()
        filename = attachment_file.name

        part.set_payload(payload)
        Encoders.encode_base64(part)
        part.add_header(u'Content-Disposition', 'attachment; filename="%s"' % filename)
        msg.attach(part)

    mailServer = smtplib.SMTP("smtp.gmail.com", 25)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(gmail_user, gmail_pwd)
    mailServer.sendmail(gmail_user, to, msg.as_string())
    # Should be mailServer.quit(), but that crashes...
    mailServer.close()
