"""SMTP transport using Python's standard library; no credentials are logged."""
import smtplib
from email.message import EmailMessage
from src.config.settings import settings

def send_email(recipient: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    transport = smtplib.SMTP_SSL if settings.SMTP_SSL else smtplib.SMTP
    with transport(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        if settings.SMTP_STARTTLS and not settings.SMTP_SSL:
            smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
