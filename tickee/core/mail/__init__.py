# -*- coding: utf-8 -*-
from email.Header import Header
from email.MIMEText import MIMEText
from email.Utils import parseaddr, formataddr
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
from tickee.core.exceptions import CoreError
import logging
import tickee.settings

tlogger = logging.getLogger('technical')

def send_email(sender, recipient, subject, body, body_plain="", noreply=False):
    """Send an email.

    All arguments should be Unicode strings (plain ASCII works as well).

    Only the real name part of sender and recipient addresses may contain
    non-ASCII characters.

    The email will be properly MIME encoded and delivered though SMTP.

    The charset of the email will be the first one out of US-ASCII, ISO-8859-1
    and UTF-8 that can represent all the characters occurring in the email.
    """

    # Header class is smart enough to try US-ASCII, then the charset we
    # provide, then fall back to UTF-8.
    header_charset = 'ISO-8859-1'

    # We must choose the body charset manually
    for body_charset in 'US-ASCII', 'ISO-8859-1', 'UTF-8':
        try:
            body.encode(body_charset)
        except UnicodeError:
            pass
        else:
            break

    # Split real name (which is optional) and email address parts
    sender_name, sender_addr = parseaddr(sender)
    recipient_name, recipient_addr = parseaddr(recipient)

    # We must always pass Unicode strings to Header, otherwise it will
    # use RFC 2047 encoding even on plain ASCII strings.
    sender_name = str(Header(unicode(sender_name), header_charset))
    recipient_name = str(Header(unicode(recipient_name), header_charset))

    # Make sure email addresses do not contain non-ASCII characters
    sender_addr = sender_addr.encode('ascii')
    recipient_addr = recipient_addr.encode('ascii')

    # Create the message
    msg = MIMEMultipart('alternative')
    html_part = MIMEText(body.encode(body_charset), 'html', body_charset)
    plain_part = MIMEText(body_plain.encode(body_charset), 'plain', body_charset)
    msg.attach(plain_part)
    msg.attach(html_part)
    msg['From'] = formataddr((sender_name, sender_addr))
    msg['To'] = formataddr((recipient_name, recipient_addr))
    msg['Subject'] = Header(unicode(subject), header_charset)

    # Send the message via SMTP via one of the configured smtp servers
    # If all servers fail, throw an error
    sent = False
    for smtp_server in tickee.settings.SMTP_SERVERS:
        try:
            smtp = SMTP(smtp_server.get('host'), smtp_server.get('port'))
            smtp.starttls()
            smtp.login(smtp_server.get('username'), smtp_server.get('password'))
            smtp.sendmail(sender, recipient, msg.as_string())
            smtp.quit()
        except Exception as e:
            tlogger.error("failed sending mail to '%s' using smtp '%s'" % (recipient, smtp_server.get('name')))
            continue # continue to the next smtp server
        else:
            sent = True
            break # stop trying to send the mail
    if not sent:
        raise CoreError('Failed sending email.')