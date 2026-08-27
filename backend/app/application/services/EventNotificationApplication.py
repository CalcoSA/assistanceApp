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
from typing import Protocol
from html import escape
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
        solutionCenterName = self._getSolutionCenterName(event)

        message = EmailMessage()
        message["Subject"] = f"[ASISTENCIA][EVENTO CREADO] {eventTitle}"
        message["From"] = (
            f"{senderName} <{senderEmail}>" if senderName else senderEmail
        )
        message["To"] = (
            recipients[0] if len(recipients) == 1 else "undisclosed-recipients:;"
        )

        if settings.SMTP_REPLY_TO:
            message["Reply-To"] = settings.SMTP_REPLY_TO.strip()

        plainUrl = eventUrl or "No disponible"
        plainBody = (
            "Cordial saludo,\n\n"
            "Se creó un nuevo evento en el Sistema de Registro de Asistencia.\n\n"
            f"Centro de soluciones: {solutionCenterName}\n"
            f"Título: {eventTitle}\n"
            f"Fecha: {event.dateEvent.strftime('%d/%m/%Y')}\n"
            f"Horario: {event.startTimeEvent.strftime('%H:%M')} - "
            f"{event.endTimeEvent.strftime('%H:%M')}\n"
            f"Duración: {event.durationEvent or 'No especificada'}\n"
            f"Lugar: {event.eventPlace or 'No especificado'}\n"
            f"Facilitador: {event.facilitatorNameEvent or 'No especificado'}\n"
            f"Creado por: {event.createdByUserLogin}\n"
            f"Enlace de asistencia: {plainUrl}\n\n"
            "Este es un mensaje automático, por favor no responda a este correo."
        )
        message.set_content(plainBody)

        attendanceLink = (
            f'<a href="{escape(eventUrl, quote=True)}" '
            'style="display:inline-block;padding:10px 16px;background:#4B2E1F;'
            'color:#FFFFFF;text-decoration:none;border-radius:8px;font-weight:600;">'
            "Abrir registro de asistencia</a>"
            if eventUrl
            else "<span>No disponible</span>"
        )
        htmlBody = f"""
        <!doctype html>
        <html lang="es">
          <body style="margin:0;padding:24px;background:#F8F3EC;color:#4B2E1F;font-family:Segoe UI,Arial,sans-serif;">
            <div style="max-width:680px;margin:0 auto;background:#FFFDF8;border:1px solid #E0CDBB;border-radius:12px;overflow:hidden;">
              <div style="padding:20px 24px;background:#4B2E1F;color:#F7E8D8;">
                <h2 style="margin:0;font-size:21px;">Nuevo evento creado</h2>
              </div>
              <div style="padding:24px;">
                <p style="margin-top:0;">Cordial saludo,</p>
                <p>Se creó un nuevo evento en el Sistema de Registro de Asistencia.</p>
                <table style="width:100%;border-collapse:collapse;margin:20px 0;">
                  {self._detailRow("Centro de soluciones", solutionCenterName)}
                  {self._detailRow("Título", eventTitle)}
                  {self._detailRow("Fecha", event.dateEvent.strftime('%d/%m/%Y'))}
                  {self._detailRow("Horario", f"{event.startTimeEvent.strftime('%H:%M')} - {event.endTimeEvent.strftime('%H:%M')}")}
                  {self._detailRow("Duración", event.durationEvent or "No especificada")}
                  {self._detailRow("Lugar", event.eventPlace or "No especificado")}
                  {self._detailRow("Facilitador", event.facilitatorNameEvent or "No especificado")}
                  {self._detailRow("Creado por", event.createdByUserLogin)}
                </table>
                <div style="margin-top:22px;">{attendanceLink}</div>
                <p style="margin:24px 0 0;color:#7A6252;font-size:12px;">Este es un mensaje automático, por favor no responda a este correo.</p>
              </div>
            </div>
          </body>
        </html>
        """
        message.add_alternative(htmlBody, subtype="html")
        return message

    def _getSolutionCenterName(self, event: EventResponseDto) -> str:
        solutionCenter = event.solutionCenter

        if not solutionCenter:
            return "No especificado"

        code = solutionCenter.codeSolutionCenter.strip()
        name = solutionCenter.nameSolutionCenter.strip()

        if code and name:
            return f"{code} - {name}"

        return code or name or "No especificado"

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
