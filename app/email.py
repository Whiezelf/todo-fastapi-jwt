import os

import requests
from dotenv import load_dotenv

load_dotenv()

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("BREVO_SENDER_EMAIL")
    if not api_key or not sender_email:
        raise RuntimeError("BREVO_API_KEY o BREVO_SENDER_EMAIL non configurate")

    resp = requests.post(
        BREVO_API_URL,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "sender": {"email": sender_email, "name": "Todo App"},
            "to": [{"email": to_email}],
            "subject": "Reimposta la tua password",
            "htmlContent": (
                f"<p>Hai richiesto di reimpostare la password.</p>"
                f'<p><a href="{reset_link}">Clicca qui per scegliere una nuova password</a></p>'
                f"<p>Il link scade tra 30 minuti. Se non sei stato tu, ignora questa email.</p>"
            ),
        },
        timeout=10,
    )
    resp.raise_for_status()