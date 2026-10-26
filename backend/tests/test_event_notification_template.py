from datetime import date, datetime, time
from email import policy
from email.parser import BytesParser
from html import escape
from html.parser import HTMLParser
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import qrcode

from app.application.services.EventNotificationApplication import EventNotificationApplication
from app.domain.dtos.EventDto import EventResponseDto
from app.infrastructure.db.config import settings


@pytest.fixture
def notification(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_USERNAME", None)
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "sender@example.com")
    monkeypatch.setattr(settings, "SMTP_FROM_NAME", "Capacitaciones")
    monkeypatch.setattr(settings, "SMTP_REPLY_TO", "reply@example.com")
    event = EventResponseDto(
        IdEvent=1,
        titleEvent='Taller <seguro> & "equipo"',
        dateEvent=date(2026, 10, 8),
        startTimeEvent=time(9, 5),
        endTimeEvent=time(11, 35),
        eventPlace='Sala <A> & "B"',
        IdEventStatus=1,
        attendanceStartDateTime=datetime(2026, 10, 6, 8, 0),
        attendanceEndDateTime=datetime(2026, 10, 8, 12, 5),
        tokenEvent="test-token",
        publicUrlEvent="https://example.com/attendance/test-token?a=1&b=2",
        qrPathEvent="/uploads/qrs/qr_event_test-token.png",
        durationEvent="DURACION_OMITIDA",
        facilitatorNameEvent="FACILITADOR_OMITIDO",
        createdByUserLogin="CREADOR_OMITIDO",
    )
    qrPath = tmp_path / "qrs" / "qr_event_test-token.png"
    qrPath.parent.mkdir()
    qrcode.make(event.publicUrlEvent).save(qrPath)
    service = EventNotificationApplication(Mock(), Mock())
    service._sendMessage = Mock()
    return service, event, qrPath


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def test_email_contains_only_requested_content_in_plain_text_and_html(notification):
    service, event, _ = notification
    message = service._buildMessage(event, ["recipient@example.com"])
    plain = message.get_body(preferencelist=("plain",)).get_content()
    html = message.get_body(preferencelist=("html",)).get_content()
    expected = (
        "¡Espacio registrado exitosamente!\n\n"
        "El espacio formativo ha sido creado y registrado correctamente en el software de capacitaciones.\n\n"
        "Puedes consultar y realizar el seguimiento de la información, participantes y demás detalles asociados al espacio desde la plataforma.\n\n"
        f"TEMA: {event.titleEvent}\n"
        "DÍA: 08/10/2026\n"
        "HORA: 09:05 - 11:35\n"
        f"LUGAR: {event.eventPlace}\n\n"
        f"Link de asistencia y QR\n{event.publicUrlEvent}\n"
    )
    assert plain == expected
    parser = VisibleText()
    parser.feed(html)
    assert " ".join(" ".join(parser.parts).split()) == " ".join(expected.split())
    assert message["Subject"] == "¡Espacio registrado exitosamente!"
    assert message["From"] == "Capacitaciones <sender@example.com>"
    assert message["To"] == "recipient@example.com"
    assert message["Reply-To"] == "reply@example.com"
    assert escape(event.titleEvent) in html
    assert escape(event.eventPlace) in html
    assert f'href="{escape(event.publicUrlEvent, quote=True)}"' in html
    for removed in (
        "Mensaje sugerido:", "Nuevo evento creado", "Cordial saludo",
        "Centro de soluciones", "Duración", "Facilitador", "Creado por",
        "Este es un mensaje automático, por favor no responda a este correo.",
        event.durationEvent, event.facilitatorNameEvent, event.createdByUserLogin,
    ):
        assert removed not in plain
        assert removed not in html


def test_existing_event_qr_is_embedded_and_survives_email_serialization(notification, monkeypatch):
    service, event, qrPath = notification
    generator = Mock(side_effect=AssertionError("The existing QR must be reused"))
    monkeypatch.setattr(qrcode, "make", generator)

    message = service._buildMessage(event, ["recipient@example.com"])
    parsed = BytesParser(policy=policy.default).parsebytes(message.as_bytes())
    images = [part for part in parsed.walk() if part.get_content_type() == "image/png"]
    assert len(images) == 1
    qrImage = images[0]
    assert qrImage.get_content_disposition() == "inline"
    assert qrImage.get_payload(decode=True) == qrPath.read_bytes()
    assert f'cid:{qrImage["Content-ID"][1:-1]}' in parsed.get_body(preferencelist=("html",)).get_content()
    generator.assert_not_called()


@pytest.mark.parametrize("qrPath", [None, "/uploads/qrs/missing.png"])
def test_missing_qr_uses_existing_generator_with_the_same_attendance_url(notification, monkeypatch, qrPath):
    service, event, _ = notification
    event = event.model_copy(update={"qrPathEvent": qrPath})
    expectedImage = BytesIO()
    qrcode.make(event.publicUrlEvent).save(expectedImage, format="PNG")
    generator = Mock(wraps=qrcode.make)
    monkeypatch.setattr(qrcode, "make", generator)

    message = service._buildMessage(event, ["recipient@example.com"])

    generator.assert_called_once_with(event.publicUrlEvent)
    image = next(part for part in message.walk() if part.get_content_type() == "image/png")
    assert image.get_payload(decode=True) == expectedImage.getvalue()


def test_notification_keeps_creator_and_configured_recipients_without_sending_real_email(notification):
    service, event, _ = notification
    service.parameterRepository.getByNameInsensitive.return_value = SimpleNamespace(
        valueParameter="ops@example.com; CREATOR@example.com; ops@example.com"
    )
    service.wordpressUserRepository.getByLogin.return_value = {
        "wordpressUserEmail": "Creator@example.com"
    }

    result = service.notifyEventCreated(event)

    assert result.sent is True
    service._sendMessage.assert_called_once()
    message, recipients = service._sendMessage.call_args.args
    assert recipients == ["creator@example.com", "ops@example.com"]
    assert message["To"] == "undisclosed-recipients:;"
    assert message.get_body(preferencelist=("html",)) is not None
    service.wordpressUserRepository.getByLogin.assert_called_once_with(event.createdByUserLogin)


def test_invalid_recipients_still_prevent_sending(notification):
    service, event, _ = notification
    service.parameterRepository.getByNameInsensitive.return_value = SimpleNamespace(
        valueParameter="invalid-address"
    )

    assert service.notifyEventCreated(event).sent is False
    service._sendMessage.assert_not_called()
