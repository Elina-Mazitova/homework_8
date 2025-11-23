from datetime import date
import copy
from typing import List
from .email import Email
from .status import Status

class EmailService:
    def __init__(self, email: Email):
        self.email = email

    def add_send_date(self) -> str:
        return date.today().strftime("%Y-%m-%d")

    def send_email(self) -> List[Email]:
        sent_emails = []
        if not self.email.recipients:
            return []
        for recipient in self.email.recipients:
            new_email = copy.deepcopy(self.email)
            new_email.recipients = [recipient]
            new_email.date = self.add_send_date()
            if self.email.status == Status.READY:
                new_email.status = Status.SENT
            else:
                new_email.status = Status.FAILED
            sent_emails.append(new_email)
        return sent_emails

class LoggingEmailService(EmailService):
    def send_email(self) -> List[Email]:
        sent_emails = super().send_email()
        with open("send.log", "a", encoding="utf-8") as log_file:
            for email in sent_emails:
                log_file.write(
                    f"[{email.date}] Status: {email.status}, "
                    f"От: {email.sender.address}, "
                    f"Кому: {email.get_recipients_str()}, "
                    f"Тема: {email.subject}\n"
                )
        return sent_emails
