from src.email_address import EmailAddress
from src.email import Email
from src.status import Status
from src.service import EmailService, LoggingEmailService
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