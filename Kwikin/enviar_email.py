from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

# Email parameters
FromAddr = 'contacto@kwikin.com'
ToAddr = 'arturor19@gmail.com'
SMTP = 'kwikin.mx'
Port = 25


body = f"""<html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
    <p>Dear User,</p>
    <p>Thanks for requesting access to HPI's data catalog: <b>ATLAS</b>
    <p>Please note that a second step needs to be taken in order to fully grant you with access to the tool, first go to 
    <a href="https://accessmanager.austin.hp.com/uam/">UAM</a> 
    <p>Then, search for <b>ATLAS</b> and request access to the <b>PRO</b> instance (Please refer to the screenshot below
    ,choose the <b>Atlas (PRO)</b> 
    <p>Your manager will receive an e-mail to approve your access, once your manager approves; you will be granted with 
    access.</p> 
    <p>Thanks.</p>
    </body>
    </html>
    """

def enviar_correo(FromAddr, ToAddr, html_body):
    subject = "Atlas Data Catalog Access/UAM Request Needed."
    msg = MIMEMultipart()
    msg["From"] = FromAddr
    msg["To"] = ToAddr
    msg["Subject"] = subject
    msgText = MIMEText(html_body, 'html')
    msg.attach(msgText)   # Added, and edited the previous line


    text = msg.as_string()
    server = smtplib.SMTP(SMTP, Port)
    server.sendmail(FromAddr, ToAddr, text)

if  __name__ == "__main__":
    enviar_correo('root@kwikin.mx', 'arturor19@gmail.com', body)