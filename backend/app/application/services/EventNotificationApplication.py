from app.application.interfaces.IEventNotificationApplication import (
    EventNotificationResult,
    IEventNotificationApplication,
)
from app.domain.constants.ParameterNames import (
    EVENT_NOTIFICATION_RECIPIENTS_PARAMETER,
)
from app.domain.interfaces.IParameterRepository import IParameterRepository
from app.infrastructure.logging.loggerConfig import getLogger
from app.infrastructure.db.config import settings
from app.domain.dtos.EventDto import EventResponseDto
from email.message import EmailMessage
from email.utils import make_msgid
from io import BytesIO
from pathlib import Path
from typing import Protocol
from html import escape
import os
import qrcode
import re
import smtplib
import ssl


logger = getLogger(__name__)
EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.I)
RECIPIENT_SEPARATOR = re.compile(r"[,;\r\n]+")


class WordpressUserReader(Protocol):
    def getByLogin(self, userLogin: str) -> dict | None:
        ...


class EventNotificationApplication(IEventNotificationApplication):

    def __init__(
        self,
        parameterRepository: IParameterRepository,
        wordpressUserRepository: WordpressUserReader,
    ):
        self.parameterRepository = parameterRepository
        self.wordpressUserRepository = wordpressUserRepository

    def notifyEventCreated(
        self, event: EventResponseDto
    ) -> EventNotificationResult:
        parameter = self.parameterRepository.getByNameInsensitive(
            EVENT_NOTIFICATION_RECIPIENTS_PARAMETER
        )

        configuredRecipients: list[str] = []
        invalidRecipients: list[str] = []

        if parameter and parameter.valueParameter.strip():
            configuredRecipients, invalidRecipients = self._parseRecipients(
                parameter.valueParameter
            )

        if invalidRecipients:
            logger.warning(
                "Notificación de evento omitida | IdEvent=%s | "
                "motivo=destinatarios_invalidos | cantidad=%s",
                event.IdEvent,
                len(invalidRecipients),
            )
            return EventNotificationResult(
                sent=False,
                message=(
                    "El evento fue creado, pero el parámetro de destinatarios "
                    "contiene uno o más correos no válidos."
                ),
            )

        creatorEmail = self._getCreatorEmail(event.createdByUserLogin)
        recipients = list(
            dict.fromkeys(
                ([creatorEmail] if creatorEmail else []) + configuredRecipients
            )
        )

        if not recipients:
            logger.warning(
                "Notificación de evento omitida | IdEvent=%s | motivo=sin_destinatarios_validos",
                event.IdEvent,
            )
            return EventNotificationResult(
                sent=False,
                message=(
                    "El evento fue creado, pero el creador no tiene un correo "
                    "válido y no hay destinatarios configurados para la notificación."
                ),
            )

        configurationError = self._getConfigurationError()

        if configurationError:
            logger.warning(
                "Notificación de evento omitida | IdEvent=%s | motivo=smtp_no_configurado",
                event.IdEvent,
            )
            return EventNotificationResult(
                sent=False,
                message=f"El evento fue creado, pero {configurationError}",
            )

        try:
            message = self._buildMessage(event, recipients)
            self._sendMessage(message, recipients)
            logger.info(
                "Notificación de evento enviada | IdEvent=%s | destinatarios=%s | creador_incluido=%s",
                event.IdEvent,
                len(recipients),
                bool(creatorEmail),
            )
            return EventNotificationResult(
                sent=True,
                message=(
                    "Evento creado y notificación enviada correctamente a "
                    f"{len(recipients)} destinatario(s)."
                ),
            )

        except Exception:
            logger.exception(
                "Error enviando notificación de evento | IdEvent=%s",
                event.IdEvent,
            )
            return EventNotificationResult(
                sent=False,
                message=(
                    "El evento fue creado, pero no fue posible enviar la "
                    "notificación. Revisa la configuración de correo y los logs."
                ),
            )

    def _parseRecipients(self, rawValue: str) -> tuple[list[str], list[str]]:
        values = [
            value.strip().lower()
            for value in RECIPIENT_SEPARATOR.split(rawValue)
            if value.strip()
        ]
        uniqueValues = list(dict.fromkeys(values))
        validRecipients = [
            value for value in uniqueValues if EMAIL_PATTERN.fullmatch(value)
        ]
        invalidRecipients = [
            value for value in uniqueValues if not EMAIL_PATTERN.fullmatch(value)
        ]
        return validRecipients, invalidRecipients

    def _getCreatorEmail(self, userLogin: str) -> str | None:
        try:
            wordpressUser = self.wordpressUserRepository.getByLogin(userLogin)
        except Exception:
            logger.exception(
                "No fue posible consultar el correo del creador | userLogin=%s",
                userLogin,
            )
            return None

        creatorEmail = (
            str(wordpressUser.get("wordpressUserEmail") or "").strip().lower()
            if wordpressUser
            else ""
        )

        if not creatorEmail:
            logger.warning(
                "Creador sin correo para notificación | userLogin=%s",
                userLogin,
            )
            return None

        if not EMAIL_PATTERN.fullmatch(creatorEmail):
            logger.warning(
                "Correo inválido del creador para notificación | userLogin=%s",
                userLogin,
            )
            return None

        return creatorEmail

    def _getConfigurationError(self) -> str | None:
        smtpHost = (settings.SMTP_HOST or "").strip()
        smtpUsername = (settings.SMTP_USERNAME or "").strip()
        smtpPassword = settings.SMTP_PASSWORD or ""
        senderEmail = self._getSenderEmail()

        if not smtpHost:
            return "el servidor SMTP no está configurado."

        if not senderEmail or not EMAIL_PATTERN.fullmatch(senderEmail):
            return "el correo remitente SMTP no está configurado correctamente."

        if smtpUsername and not smtpPassword:
            return "la contraseña SMTP no está configurada."

        return None

    def _getSenderEmail(self) -> str:
        return (
            (settings.SMTP_FROM_EMAIL or "").strip()
            or (settings.SMTP_USERNAME or "").strip()
        )

    def _buildMessage(
        self, event: EventResponseDto, recipients: list[str]
    ) -> EmailMessage:
        senderEmail = self._getSenderEmail()
        senderName = settings.SMTP_FROM_NAME.strip()
        eventTitle = event.titleEvent.strip()
        eventUrl = (event.publicUrlEvent or "").strip()
        eventDate = event.dateEvent.strftime('%d/%m/%Y')
        eventSchedule = f"{event.startTimeEvent.strftime('%H:%M')} - {event.endTimeEvent.strftime('%H:%M')}"
        eventPlace = event.eventPlace or ""

        message = EmailMessage()
        message["Subject"] = "¡Espacio registrado exitosamente!"
        message["From"] = (
            f"{senderName} <{senderEmail}>" if senderName else senderEmail
        )
        message["To"] = (
            recipients[0] if len(recipients) == 1 else "undisclosed-recipients:;"
        )

        if settings.SMTP_REPLY_TO:
            message["Reply-To"] = settings.SMTP_REPLY_TO.strip()

        plainBody = (
            "¡Espacio registrado exitosamente!\n\n"
            "El espacio formativo ha sido creado y registrado correctamente en el software de capacitaciones.\n\n"
            "Puedes consultar y realizar el seguimiento de la información, participantes y demás detalles asociados al espacio desde la plataforma.\n\n"
            f"TEMA: {eventTitle}\n"
            f"DÍA: {eventDate}\n"
            f"HORA: {eventSchedule}\n"
            f"LUGAR: {eventPlace}\n\n"
            f"Link de asistencia y QR\n{eventUrl}"
        )
        message.set_content(plainBody)

        attendanceLink = (
            f'<a href="{escape(eventUrl, quote=True)}" '
            'style="color:#4B2E1F;word-break:break-all;">'
            f"{escape(eventUrl)}</a>"
            if eventUrl
            else ""
        )
        qrContentId = make_msgid() if eventUrl else None
        qrImage = (
            f'<img src="cid:{qrContentId[1:-1]}" alt="QR de asistencia" '
            'width="220" style="display:block;width:100%;max-width:220px;height:auto;margin:18px auto 0;">'
            if qrContentId
            else ""
        )
        htmlBody = f"""
        <!doctype html>
        <html lang="es">
          <body style="margin:0;padding:24px;background:#F8F3EC;color:#4B2E1F;font-family:Segoe UI,Arial,sans-serif;">
            <div style="max-width:680px;margin:0 auto;background:#FFFDF8;border:1px solid #E0CDBB;border-radius:12px;overflow:hidden;">
              <div style="padding:20px 24px;background:#4B2E1F;color:#F7E8D8;">
                <h2 style="margin:0;font-size:21px;text-align:center;">¡Espacio registrado exitosamente!</h2>
              </div>
              <div style="padding:24px;">
                <p style="margin-top:0;">El espacio formativo ha sido creado y registrado correctamente en el software de capacitaciones.</p>
                <p>Puedes consultar y realizar el seguimiento de la información, participantes y demás detalles asociados al espacio desde la plataforma.</p>
                <table style="width:100%;border-collapse:collapse;margin:20px 0;">
                  {self._detailRow("TEMA:", eventTitle)}
                  {self._detailRow("DÍA:", eventDate)}
                  {self._detailRow("HORA:", eventSchedule)}
                  {self._detailRow("LUGAR:", eventPlace)}
                </table>
                <div style="margin-top:22px;">
                  <p style="font-weight:700;">Link de asistencia y QR</p>
                  {attendanceLink}
                  {qrImage}
                </div>
              </div>
            </div>
          </body>
        </html>
        """
        message.add_alternative(htmlBody, subtype="html")
        if qrContentId:
            message.get_payload()[-1].add_related(
                self._getQrImage(event, eventUrl),
                maintype="image",
                subtype="png",
                cid=qrContentId,
                disposition="inline",
                filename="qr_asistencia.png",
            )
        return message

    def _getQrImage(self, event: EventResponseDto, eventUrl: str) -> bytes:
        if event.qrPathEvent:
            qrPath = Path(os.getenv("UPLOAD_DIR", "uploads")) / "qrs" / Path(event.qrPathEvent).name
            try:
                return qrPath.read_bytes()
            except OSError:
                pass

        imageBuffer = BytesIO()
        qrcode.make(eventUrl).save(imageBuffer, format="PNG")
        return imageBuffer.getvalue()

    def _detailRow(self, label: str, value: str) -> str:
        return (
            '<tr style="border-bottom:1px solid #F7E8D8;">'
            f'<td style="padding:9px 8px;font-weight:700;width:190px;">{escape(label)}</td>'
            f'<td style="padding:9px 8px;">{escape(value)}</td>'
            "</tr>"
        )

    def _sendMessage(
        self, message: EmailMessage, recipients: list[str]
    ) -> None:
        smtpHost = settings.SMTP_HOST.strip()
        smtpPort = settings.SMTP_PORT
        smtpUsername = (settings.SMTP_USERNAME or "").strip()
        smtpPassword = settings.SMTP_PASSWORD or ""
        senderEmail = self._getSenderEmail()
        sslContext = ssl.create_default_context()

        if settings.SMTP_USE_SSL:
            smtpClient = smtplib.SMTP_SSL(
                smtpHost,
                smtpPort,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
                context=sslContext,
            )
        else:
            smtpClient = smtplib.SMTP(
                smtpHost,
                smtpPort,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
            )

        with smtpClient:
            smtpClient.ehlo()

            if settings.SMTP_USE_TLS and not settings.SMTP_USE_SSL:
                smtpClient.starttls(context=sslContext)
                smtpClient.ehlo()

            if smtpUsername:
                smtpClient.login(smtpUsername, smtpPassword)

            smtpClient.send_message(
                message,
                from_addr=senderEmail,
                to_addrs=recipients,
            )
