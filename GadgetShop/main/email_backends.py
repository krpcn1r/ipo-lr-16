"""
Кастомный Django email-backend, отправляющий письма через HTTP API Brevo.

Зачем: на бесплатном тарифе Railway заблокированы исходящие SMTP-порты
(25/465/587), поэтому стандартный SMTP-бэкенд падает с "Network is unreachable".
Brevo принимает письма по HTTPS (порт 443), который не блокируется.

Бэкенд полностью совместим с обычным кодом отправки (EmailMessage.send()),
включая вложения (чек receipt.xlsx).

Настройка через переменные окружения:
    EMAIL_BACKEND=main.email_backends.BrevoApiEmailBackend
    BREVO_API_KEY=<ключ из Brevo: Settings -> SMTP & API -> API Keys>
    DEFAULT_FROM_EMAIL=<подтверждённый в Brevo отправитель>
"""
import base64
import json
import urllib.request
import urllib.error

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


class BrevoApiEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, "BREVO_API_KEY", "")

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        if not self.api_key:
            if not self.fail_silently:
                raise ValueError("BREVO_API_KEY не задан в переменных окружения")
            return 0

        sent = 0
        for message in email_messages:
            try:
                self._send(message)
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent

    def _send(self, message):
        from_email = message.from_email or settings.DEFAULT_FROM_EMAIL
        payload = {
            "sender": {"email": from_email},
            "to": [{"email": addr} for addr in message.to],
            "subject": message.subject,
            "textContent": message.body or " ",
        }
        if message.cc:
            payload["cc"] = [{"email": addr} for addr in message.cc]
        if message.bcc:
            payload["bcc"] = [{"email": addr} for addr in message.bcc]

        # HTML-альтернатива, если есть
        for content, mimetype in getattr(message, "alternatives", []) or []:
            if mimetype == "text/html":
                payload["htmlContent"] = content

        # Вложения (например, чек receipt.xlsx)
        attachments = []
        for attachment in message.attachments:
            # attachment = (filename, content, mimetype)
            filename, content = attachment[0], attachment[1]
            if isinstance(content, str):
                content = content.encode("utf-8")
            attachments.append({
                "name": filename or "attachment",
                "content": base64.b64encode(content).decode("ascii"),
            })
        if attachments:
            payload["attachment"] = attachments

        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            BREVO_ENDPOINT,
            data=data,
            method="POST",
            headers={
                "api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"Brevo API {exc.code}: {detail}") from exc
