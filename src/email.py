from dataclasses import dataclass, field
from typing import Optional, List, Union
from src.status import Status
from src.utils import clean_text
from src.email_address import EmailAddress


@dataclass
class Email:
    subject: str
    body: str
    sender: EmailAddress
    recipients: Union[EmailAddress, List[EmailAddress]]
    date: Optional[str] = None
    short_body: Optional[str] = None
    status: Status = field(default=Status.DRAFT)

    def __post_init__(self):
        if isinstance(self.recipients, EmailAddress):
            self.recipients = [self.recipients]

    def get_recipients_str(self) -> str:
        return ", ".join([r.address for r in self.recipients])

    def clean_data(self) -> "Email":
        self.subject = clean_text(self.subject)
        self.body = clean_text(self.body)
        return self

    def add_short_body(self, n: int = 10) -> "Email":
        if not self.body:
            self.short_body = None
        elif len(self.body) <= n:
            self.short_body = self.body
        else:
            self.short_body = self.body[:n] + "..."
        return self

    def is_valid_fields(self) -> bool:
        return bool(self.subject and self.body)

    def prepare(self) -> "Email":
        self.clean_data()
        if self.subject and self.body and self.sender and self.recipients:
            self.status = Status.READY
        else:
            self.status = Status.INVALID
        self.add_short_body()
        return self

    def __str__(self) -> str:
        recipients_str = self.get_recipients_str()
        return (
            f"Status: {self.status}\n"
            f"Кому: {recipients_str}\n"
            f"От: {self.sender.masked}\n"
            f"Тема: {self.subject}, дата {self.date}\n"
            f"{self.short_body or self.body}"
        )

    def __repr__(self) -> str:
        return self.__str__()
