#!/usr/bin/env python3
"""
IONOS Email Sender - Uses Python smtplib to avoid curl policy restrictions
"""
import smtplib
import ssl
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_email, subject, body, reply_to=None, in_reply_to=None):
    """Send email via IONOS SMTP using Python smtplib"""
    
    # IONOS credentials
    smtp_server = "smtp.ionos.de"
    smtp_port = 587
    username = "kontakt@navii-automation.de"
    password = "Billiondollar17"
    from_email = "kontakt@navii-automation.de"
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = f"Fridolin Edlmair <{from_email}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    
    if reply_to:
        msg['Reply-To'] = reply_to
    if in_reply_to:
        msg['In-Reply-To'] = in_reply_to
        msg['References'] = in_reply_to
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # Send via IONOS SMTP
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls(context=context)
        server.login(username, password)
        server.send_message(msg)
    
    print(f"SUCCESS: Email sent to {to_email}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 ionos_send.py <to> <subject> <body_file>")
        sys.exit(1)
    
    to = sys.argv[1]
    subject = sys.argv[2]
    with open(sys.argv[3], 'r') as f:
        body = f.read()
    
    send_email(to, subject, body)
