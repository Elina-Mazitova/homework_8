from enum import StrEnum
from dataclasses import dataclass, field
from typing import Optional, List, Union

class Status(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    SENT = "sent"
    FAILED = "failed"
    INVALID = "invalid"

def clean_text(text: str) -> str:
    """Заменяет \t и \n на пробелы, лишние пробелы обрезает."""
    return " ".join(text.replace("\n", " ").replace("\t", " ").split())

@dataclass
class Email:
    subject: str
    body: str
    sender: "EmailAddress"
    recipients: Union["EmailAddress", List["EmailAddress"]]
    date: Optional[str] = None
    short_body: Optional[str] = None
    status: Status = field(default=Status.DRAFT)

    def __post_init__(self):
        if isinstance(self.recipients, EmailAddress):
            self.recipients = [self.recipients]

    def get_recipients_str(self) -> str:
        """Возвращает строку со списком всех recipients через запятую"""
        return ", ".join([r.address for r in self.recipients])

    def clean_data(self) -> "Email":
        """Очищает subject и body от лишних пробелов и переносов"""
        self.subject = clean_text(self.subject)
        self.body = clean_text(self.body)
        return self

    def add_short_body(self, n: int = 10) -> "Email":
        """Формирует сокращённую версию тела письма"""
        if not self.body:
            self.short_body = None
        elif len(self.body) <= n:
            self.short_body = self.body
        else:
            self.short_body = self.body[:n] + "..."
        return self

    def is_valid_fields(self) -> bool:
        """Проверяет заполненность обязательных полей"""
        return bool(self.subject and self.body)

    def prepare(self) -> "Email":
        """Подготавливает письмо к отправке"""
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

class EmailAddress:
    def __init__(self, address: str):
        normalized = self.normalize_address(address)
        if not self._check_correct_email(normalized):
            raise ValueError(f"Некорректный email: {address}")
        self._address = normalized

    @property
    def address(self) -> str:
        return self._address

    @property
    def masked(self) -> str:
        local, domain = self._address.split("@")
        return f"{local[:2]}***@{domain}"

    def normalize_address(self, address: str) -> str:
        return address.lower().strip()

    def _check_correct_email(self, address: str) -> bool:
        return (
            "@" in address
            and (address.endswith(".com") or address.endswith(".ru") or address.endswith(".net"))
        )
from datetime import date
import copy

class EmailService:
    def __init__(self, email: Email):
        self.email = email

    def add_send_date(self) -> str:
        """Возвращает текущую дату в формате YYYY-MM-DD"""
        return date.today().strftime("%Y-%m-%d")

    def send_email(self) -> List[Email]:
        """Имитация отправки писем. Возвращает список новых писем (одно на получателя)."""
        sent_emails = []

        # если нет получателей → пустой список
        if not self.email.recipients:
            return []

        for recipient in self.email.recipients:
            # создаём глубокую копию исходного письма
            new_email = copy.deepcopy(self.email)

            # заменяем список получателей на одного конкретного
            new_email.recipients = [recipient]

            # выставляем дату отправки
            new_email.date = self.add_send_date()

            # меняем статус
            if self.email.status == Status.READY:
                new_email.status = Status.SENT
            else:
                new_email.status = Status.FAILED

            sent_emails.append(new_email)

        return sent_emails

class LoggingEmailService(EmailService):
    def send_email(self) -> List[Email]:
        # вызываем родительский метод
        sent_emails = super().send_email()

        # открываем файл send.log для записи (append mode)
        with open("send.log", "a", encoding="utf-8") as log_file:
            for email in sent_emails:
                log_file.write(
                    f"[{email.date}] Status: {email.status}, "
                    f"От: {email.sender.address}, "
                    f"Кому: {email.get_recipients_str()}, "
                    f"Тема: {email.subject}\n"
                )

        return sent_emails

#тесты
import pytest


def test_email_address_valid():
    addr = EmailAddress("USER@GMAIL.COM")
    assert addr.address == "user@gmail.com"
    assert addr.masked.startswith("us***")


def test_email_address_invalid():
    with pytest.raises(ValueError):
        EmailAddress("not-an-email")


def test_email_prepare_sets_ready():
    email = Email(
        subject="Hello",
        body="World",
        sender=EmailAddress("a@a.com"),
        recipients=EmailAddress("b@b.com"),
    )
    email.prepare()
    assert email.status == Status.READY


def test_email_prepare_sets_invalid():
    email = Email(
        subject="",
        body="",
        sender=EmailAddress("a@a.com"),
        recipients=EmailAddress("b@b.com"),
    )
    email.prepare()
    assert email.status == Status.INVALID


def test_recipients_auto_list():
    email = Email(
        subject="Hi",
        body="Msg",
        sender=EmailAddress("a@a.com"),
        recipients=EmailAddress("b@b.com"),
    )
    assert isinstance(email.recipients, list)
    assert len(email.recipients) == 1


def test_send_email_single_recipient():
    email = Email(
        subject="Hello",
        body="Msg",
        sender=EmailAddress("a@a.com"),
        recipients=EmailAddress("b@b.com"),
        status=Status.READY,
    )

    service = EmailService(email)
    results = service.send_email()

    assert len(results) == 1
    sent = results[0]
    assert sent.status == Status.SENT
    assert sent.recipients[-1].address == "b@b.com"


def test_send_email_multiple_recipients():
    email = Email(
        subject="Hello",
        body="Msg",
        sender=EmailAddress("a@a.com"),
        recipients=[
            EmailAddress("b@b.com"),
            EmailAddress("c@c.com"),
            EmailAddress("d@d.com"),
        ],
        status=Status.READY,
    )

    service = EmailService(email)
    results = service.send_email()

    assert len(results) == 3
    assert all(msg.status == Status.SENT for msg in results)
    assert {msg.recipients[0].address for msg in results} == {"b@b.com", "c@c.com", "d@d.com"}


def test_send_email_failed_if_not_ready():
    email = Email(
        subject="Hello",
        body="Msg",
        sender=EmailAddress("a@a.com"),
        recipients=[EmailAddress("b@b.com")],
        status=Status.DRAFT,
    )

    service = EmailService(email)
    results = service.send_email()

    assert results[0].status == Status.FAILED


def test_email_address_normalization_and_masking():
    addr = EmailAddress("USER@GMAIL.COM")
    assert addr.address == "user@gmail.com"
    assert addr.masked == "us***@gmail.com"


@pytest.mark.parametrize("invalid", ["abc", "test@mail", "name@domain.xx"])
def test_email_address_invalid_variants(invalid):
    with pytest.raises(ValueError):
        EmailAddress(invalid)


def test_email_prepare_cleans_text_and_sets_ready():
    email = Email(
        subject="  Hello   world  ",
        body=" Test   body\nwith   spaces ",
        sender=EmailAddress("a@a.com"),
        recipients=EmailAddress("b@b.com"),
    )
    email.prepare()
    assert email.status == Status.READY
    assert email.subject == "Hello world"
    assert email.body == "Test body with spaces"


def test_email_prepare_invalid_when_body_missing():
    email = Email(
        subject="Hello",
        body="",
        sender=EmailAddress("a@a.com"),
        recipients=EmailAddress("b@b.com"),
    )
    email.prepare()
    assert email.status == Status.INVALID


def test_add_short_body():
    email = Email(
        subject="Hi",
        body="This text is long",
        sender=EmailAddress("a@a.com"),
        recipients=EmailAddress("b@b.com"),
    )
    email.add_short_body(5)
    assert email.short_body == "This ..."


def test_recipients_auto_wraps_to_list():
    email = Email(
        subject="Hi",
        body="Msg",
        sender=EmailAddress("a@a.com"),
        recipients=EmailAddress("b@b.com"),
    )
    assert isinstance(email.recipients, list)
    assert len(email.recipients) == 1
    assert email.recipients[0].address == "b@b.com"


def test_send_email_single_recipient_creates_new_object():
    email = Email(
        subject="Hello",
        body="Msg",
        sender=EmailAddress("a@a.com"),
        recipients=EmailAddress("b@b.com"),
        status=Status.READY,
    )

    service = EmailService(email)
    results = service.send_email()

    assert len(results) == 1
    sent = results[0]


    assert sent.status == Status.SENT


    assert sent is not email
    assert sent.recipients[0].address == "b@b.com"


    assert email.date is None
    assert email.recipients is not results[0].recipients
    assert email.recipients[0] is results[0].recipients[0]


def test_send_email_failed_if_status_not_ready():
    email = Email(
        subject="Hello",
        body="Msg",
        sender=EmailAddress("a@a.com"),
        recipients=[EmailAddress("b@b.com")],
        status=Status.DRAFT,
    )

    service = EmailService(email)
    results = service.send_email()

    assert results[0].status == Status.FAILED


def test_repr_has_expected_format():
    email = Email(
        subject="Hello",
        body="World",
        sender=EmailAddress("a@a.com"),
        recipients=[EmailAddress("b@b.com")],
    ).prepare()

    text = repr(email)

    assert "Status:" in text
    assert "Кому:" in text
    assert "От:" in text
    assert "Тема:" in text


@pytest.mark.parametrize("valid", [
    "test@gmail.com",
    "User@MAIL.RU",
    "a@a.net",
])
def test_email_address_valid_equivalence(valid):
    addr = EmailAddress(valid)
    assert "@" in addr.address

@pytest.mark.parametrize("valid", [
    "test@gmail.com",
    "User@MAIL.RU",
    "User@MAIL.RU",
    "USER@GMAIL.COM",
    "a@a.net",
    "  a@a.net   ",
])
def test_email_address_valid_variants(valid):
    assert EmailAddress(valid).address == valid.lower().strip()

@pytest.mark.parametrize("invalid", [
    "noatsymbol.com",
    "name@domain.xyz",
    "",
    "    "
])
def test_email_address_invalid_equivalence(invalid):
    with pytest.raises(ValueError):
        EmailAddress(invalid)


def test_add_short_body_boundary():
    email = Email("s", "12345", EmailAddress("a@a.com"), EmailAddress("b@b.com"))
    email.add_short_body(5)
    assert email.short_body == "12345"
    email = Email("s", "123456", EmailAddress("a@a.com"), EmailAddress("b@b.com"))
    email.add_short_body(5)
    assert email.short_body == "12345..."

    email = Email("s", "", EmailAddress("a@a.com"), EmailAddress("b@b.com"))
    email.add_short_body(5)
    assert email.short_body is None


@pytest.mark.parametrize("subject, body, expected", [
    ("Hello", "World", Status.READY),
    ("", "World", Status.INVALID),
    ("Hello", "", Status.INVALID),
])
def test_prepare_equivalence(subject, body, expected):
    email = Email(subject, body, EmailAddress("a@a.com"), EmailAddress("b@b.com"))
    email.prepare()
    assert email.status == expected


def test_send_zero_recipients():
    email = Email(
        subject="Test",
        body="Body",
        sender=EmailAddress("a@a.com"),
        recipients=[],
        status=Status.READY,
    )

    service = EmailService(email)
    assert service.send_email() == []


def test_send_two_recipients():
    email = Email(
        subject="T",
        body="B",
        sender=EmailAddress("a@a.com"),
        recipients=[EmailAddress("b@b.com"), EmailAddress("c@c.com")],
        status=Status.READY,
    )
    service = EmailService(email)
    results = service.send_email()
    assert len(results) == 2


def test_send_many_recipients_large():
    recipients = [EmailAddress(f"user{i}@mail.com") for i in range(10)]
    email = Email(
        subject="Hi",
        body="Msg",
        sender=EmailAddress("sender@mail.com"),
        recipients=recipients,
        status=Status.READY,
    )

    service = EmailService(email)
    results = service.send_email()

    assert len(results) == 10
    assert all(msg.status == Status.SENT for msg in results)
    assert all(len(msg.recipients) == 1 for msg in results)


@pytest.mark.parametrize("invalid", [
    "abc",
    "name@domain.xyz",
    "noatsymbol.com",
    "",
    "   ",
])
def test_email_address_invalid(invalid):
    with pytest.raises(ValueError):
        EmailAddress(invalid)


def test_email_address_normalization():
    addr = EmailAddress("  USER@GMAIL.COM  ")
    assert addr.address == "user@gmail.com"


def test_email_address_masking():
    addr = EmailAddress("user@gmail.com")
    assert addr.masked == "us***@gmail.com"


def test_clean_data_and_prepare():
    email = Email(
        "  Hello   world  ",
        " Test   body\nwith   spaces ",
        EmailAddress("a@a.com"),
        EmailAddress("b@b.com"),
    )
    email.prepare()
    assert email.subject == "Hello world"
    assert email.body == "Test body with spaces"
    assert email.status == Status.READY


def test_add_short_body_cut():
    email = Email("Hi", "This text is long", EmailAddress("a@a.com"), EmailAddress("b@b.com"))
    email.add_short_body(5)
    assert email.short_body == "This ..."


def test_add_short_body_exact():
    email = Email("s", "12345", EmailAddress("a@a.com"), EmailAddress("b@b.com"))
    email.add_short_body(5)
    assert email.short_body == "12345"


def test_add_short_body_empty_body():
    email = Email("s", "", EmailAddress("a@a.com"), EmailAddress("b@b.com"))
    email.add_short_body(5)
    assert email.short_body is None

@pytest.mark.parametrize("subject, body, expected", [
    ("Hello", "World", Status.READY),
    ("", "World", Status.INVALID),
    ("Hello", "", Status.INVALID),
])
def test_prepare_status_logic(subject, body, expected):
    email = Email(subject, body, EmailAddress("a@a.com"), EmailAddress("b@b.com"))
    email.prepare()
    assert email.status == expected


def test_prepare_invalid_if_no_recipients():
    email = Email("Hello", "Body", EmailAddress("a@a.com"), [])
    email.prepare()
    assert email.status == Status.INVALID


def test_send_email_single_ready():
    email = Email("Hello", "Msg", EmailAddress("a@a.com"), EmailAddress("b@b.com"), status=Status.READY)
    service = EmailService(email)
    results = service.send_email()

    assert len(results) == 1
    assert results[0].status == Status.SENT


def test_send_email_single_fails_if_not_ready():
    email = Email("Hello", "Msg", EmailAddress("a@a.com"), EmailAddress("b@b.com"), status=Status.DRAFT)
    service = EmailService(email)
    results = service.send_email()
    assert results[0].status == Status.FAILED


def test_send_does_not_mutate_original():
    email = Email("Hello", "Msg", EmailAddress("a@a.com"), EmailAddress("b@b.com"), status=Status.READY)
    service = EmailService(email)
    results = service.send_email()

    assert email.date is None
    assert results[0] is not email
    assert len(results[0].recipients) == 1


def test_status_transitions():
    email = Email("S", "B", EmailAddress("a@a.com"), EmailAddress("b@b.com"))

    assert email.status == Status.DRAFT

    email.prepare()
    assert email.status == Status.READY

    service = EmailService(email)
    sent = service.send_email()[0]
    assert sent.status == Status.SENT