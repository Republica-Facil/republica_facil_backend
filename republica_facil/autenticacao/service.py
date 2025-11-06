import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from string import Template

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from republica_facil.database import redis_client
from republica_facil.model.models import User
from republica_facil.settings import Settings


def request_password_reset_code(db: Session, email: str):
    """
    Solicita um código de redefinição de senha.
    1. Verifica se o usuário existe
    2. Gera código aleatório
    3. Salva no Redis com TTL
    4. Envia por email (simulado)
    """
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Service unavailable',
        )

    user = db.scalar(select(User).where(User.email == email))

    # Por segurança, não revelamos se o email existe ou não
    # Mas só enviamos código se existir
    if user:
        reset_code = str(random.randint(100000, 999999))
        ttl_seconds = 600  # 10 minutos
        redis_key = f'reset_code:{email}'

        try:
            redis_client.set(redis_key, reset_code, ttl_seconds)

            send_code_email(email=email, code=reset_code, name=user.fullname)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f'Erro no serviço de cache: {e}',
            )


def send_code_email(email: str, code: str, name: str = ''):
    FILE_EMAIL_HTML = Path(__file__).parent / 'email.html'

    with open(FILE_EMAIL_HTML, 'r', encoding='utf-8') as file_html:
        text = file_html.read()
    template = Template(text)
    text_email = template.substitute(codeL=code, nameL=name)

    # Transformar essa mensagem em MIMEMultipart (to, from, subject, ...)

    mime_multipart = MIMEMultipart()
    mime_multipart['from'] = Settings().FROM_EMAIL
    mime_multipart['to'] = email
    mime_multipart['subject'] = 'Codigo para resetar a senha'

    body_email = MIMEText(text_email, 'html', 'utf-8')

    mime_multipart.attach(body_email)

    with smtplib.SMTP(Settings().SMTP_SERVER, Settings().SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(Settings().FROM_EMAIL, Settings().EMAIL_PASSWORD)
        server.send_message(mime_multipart)
        print('E-mail enviado com sucesso!')
