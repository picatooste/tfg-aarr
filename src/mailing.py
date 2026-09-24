"""
Envio de correos electronicos con adjuntos.

Dos modos:
- Real: se conecta al SMTP configurado en .env y envia
- Sandbox: si falta configuracion, simula el envio devolviendo el
  correo como texto (util para desarrollo y demos)
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional


RUTA_PLANTILLAS = Path(__file__).parent.parent / "templates" / "emails"


class Email:
    """Representacion inmutable de un correo listo para revisar o enviar."""
    def __init__(
        self,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        adjunto_bytes: Optional[bytes] = None,
        adjunto_nombre: Optional[str] = None,
    ):
        self.destinatario = destinatario
        self.asunto = asunto
        self.cuerpo = cuerpo
        self.adjunto_bytes = adjunto_bytes
        self.adjunto_nombre = adjunto_nombre

    def resumen(self) -> str:
        """Devuelve el correo como texto plano para preview en UI."""
        lineas = [
            f"Para: {self.destinatario}",
            f"Asunto: {self.asunto}",
            "",
            self.cuerpo,
        ]
        if self.adjunto_nombre:
            lineas.append("")
            lineas.append(f"[Adjunto: {self.adjunto_nombre}]")
        return "\n".join(lineas)


def _cargar_plantilla(nombre: str, variables: dict) -> str:
    """Lee una plantilla y sustituye las {variables}."""
    ruta = RUTA_PLANTILLAS / nombre
    contenido = ruta.read_text(encoding="utf-8")
    return contenido.format(**variables)


def _configuracion_smtp_disponible() -> bool:
    return all(os.environ.get(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"))


def _enviar_via_smtp(email: Email) -> None:
    """Envio real via SMTP con TLS. Requiere .env configurado."""
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    from_name = os.environ.get("SMTP_FROM_NAME", "Herramienta AARR")

    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{user}>"
    msg["To"] = email.destinatario
    msg["Subject"] = email.asunto
    msg.attach(MIMEText(email.cuerpo, "plain", "utf-8"))

    if email.adjunto_bytes and email.adjunto_nombre:
        parte = MIMEBase("application", "octet-stream")
        parte.set_payload(email.adjunto_bytes)
        encoders.encode_base64(parte)
        parte.add_header(
            "Content-Disposition",
            f"attachment; filename=\"{email.adjunto_nombre}\"",
        )
        msg.attach(parte)

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)


def enviar(email: Email) -> tuple[bool, str]:
    """
    Envia el correo. Devuelve (exito, mensaje).
    Si no hay configuracion SMTP, entra en modo sandbox y no envia.
    """
    if not _configuracion_smtp_disponible():
        return False, (
            "Modo sandbox: no hay SMTP configurado en .env. "
            "El correo NO se ha enviado."
        )
    try:
        _enviar_via_smtp(email)
        return True, f"Correo enviado a {email.destinatario}"
    except Exception as e:
        return False, f"Error al enviar: {e}"


# =============================================================================
# CONSTRUCTORES ESPECIFICOS
# =============================================================================

def construir_email_service_manager(
    destinatario: str,
    nombre_service_manager: str,
    nombre_app: str,
    remitente_visible: str,
    plantilla_excel_bytes: bytes,
) -> Email:
    """Correo al Service Manager con la plantilla Excel vacia."""
    cuerpo = _cargar_plantilla(
        "service_manager_plantilla.txt",
        variables={
            "nombre_service_manager": nombre_service_manager,
            "nombre_app": nombre_app,
            "remitente": remitente_visible,
        },
    )
    return Email(
        destinatario=destinatario,
        asunto=f"Inicio AARR - Plantilla ficha aplicacion {nombre_app}",
        cuerpo=cuerpo,
        adjunto_bytes=plantilla_excel_bytes,
        adjunto_nombre=f"plantilla_ficha_{nombre_app}.xlsx",
    )


def construir_email_cliente(
    destinatario: str,
    nombre_cliente: str,
    nombre_app: str,
    remitente_visible: str,
    total_amenazas: int,
    n_criticos: int,
    n_altos: int,
    n_salvaguardas: int,
    informe_pdf_bytes: bytes,
) -> Email:
    """Correo al cliente con el informe PDF."""
    cuerpo = _cargar_plantilla(
        "cliente_informe.txt",
        variables={
            "nombre_cliente": nombre_cliente,
            "nombre_app": nombre_app,
            "total_amenazas": total_amenazas,
            "n_criticos": n_criticos,
            "n_altos": n_altos,
            "n_salvaguardas": n_salvaguardas,
            "remitente": remitente_visible,
        },
    )
    return Email(
        destinatario=destinatario,
        asunto=f"Informe AARR - {nombre_app}",
        cuerpo=cuerpo,
        adjunto_bytes=informe_pdf_bytes,
        adjunto_nombre=f"AARR_{nombre_app}.pdf",
    )