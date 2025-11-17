import smtplib
from email.message import EmailMessage
from flask import current_app


def send_email_alert(to_email: str, subject: str, body: str):
    """
    Envía un correo simple de texto usando los datos SMTP
    configurados en Flask (Config).
    """
    host = current_app.config.get("SMTP_HOST")
    port = current_app.config.get("SMTP_PORT")
    user = current_app.config.get("SMTP_USER")
    password = current_app.config.get("SMTP_PASS")

    if not all([host, port, user, password]):
        print("⚠️ Configuración SMTP incompleta. No se envía correo.")
        return

    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()  # TLS
            server.login(user, password)
            server.send_message(msg)
            print(f"📧 Alerta enviada a {to_email}")
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")
