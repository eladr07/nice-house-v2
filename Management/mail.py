from django.core.mail import EmailMessage

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

from NiceHouse.settings import EMAIL_HOST_USER

def mail(to, cc='', bcc='', subject='', contents='', attachments = ()):
    email = EmailMessage(
        subject,
        '',
        EMAIL_HOST_USER,
        to,
        bcc,
        cc=cc)
    
    for attachment in attachments:
        part = MIMEBase('application', 'octet-stream')
        if isinstance(attachment, str):
            attachment_file = open(attachment, 'rb')
        else:
            attachment_file = attachment
            
        payload = attachment_file.read()
        filename = attachment_file.name

        part.set_payload(payload)
        encoders.encode_base64(part)
        part.add_header(u'Content-Disposition', 'attachment; filename="%s"' % filename)
        email.attach(part)

    email.send()
