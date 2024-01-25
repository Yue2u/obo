import random
import smtplib
from email.message import EmailMessage


def generate_restore_code():
    return random.randint(100000, 999999)


def send_restore_password_email(email: str, generated_code: int):
    msg = EmailMessage()
    msg['Subject'] = "OBO Guarantor: Восстановление пароля"
    msg['From'] = "oboguarantor@noreply"
    msg['To'] = email
    msg.set_content(
        f'Ваш код для восстановления пароля: {generated_code}'
        )

    with smtplib.SMTP_SSL('localhost') as smtp:
        smtp.send_message(msg)