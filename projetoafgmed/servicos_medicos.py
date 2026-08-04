from flask_login import current_user

from projetoafgmed import bcrypt, database
from projetoafgmed.models import Medico, Usuario

# Senha utilizada exclusivamente em ambiente acadêmico/demonstração.
# Em produção, deve ser substituída por senha temporária aleatória.

SENHA_PADRAO_MEDICO = "123456"


def sincronizar_usuario_medico(medico):
    email_medico = (medico.email or "").strip().lower()

    if not email_medico:
        return None, "Informe um e-mail para o médico."

    usuario_com_email = Usuario.query.filter_by(email=email_medico).first()
    usuario_vinculado = Usuario.query.filter_by(id_medico=medico.id).first()

    if (
        usuario_com_email
        and usuario_com_email.id_medico
        and usuario_com_email.id_medico != medico.id
    ):
        return None, "Este e-mail já está vinculado a outro médico."

    if usuario_vinculado and usuario_vinculado.email != email_medico:
        email_em_uso = Usuario.query.filter_by(email=email_medico).first()

        if email_em_uso and email_em_uso.id != usuario_vinculado.id:
            return None, "Este e-mail já está sendo usado por outro usuário."

        usuario = usuario_vinculado
        usuario.email = email_medico

    elif usuario_com_email:
        usuario = usuario_com_email

    else:
        senha_hash = bcrypt.generate_password_hash(
            SENHA_PADRAO_MEDICO
        ).decode("utf-8")

        usuario = Usuario(
            nome=medico.nome,
            sobrenome=medico.sobrenome,
            email=email_medico,
            senha=senha_hash,
            is_medico=True,
            id_medico=medico.id,
        )
        database.session.add(usuario)

    usuario.nome = medico.nome
    usuario.sobrenome = medico.sobrenome
    usuario.is_medico = True
    usuario.id_medico = medico.id

    return usuario, None


def medico_logado():
    if not getattr(current_user, "is_medico", False):
        return None

    if not current_user.id_medico:
        return None

    return database.session.get(Medico, current_user.id_medico)
