from datetime import datetime
import os
from uuid import uuid4

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.utils import secure_filename

from projetoafgmed import app, database
from projetoafgmed.models import PerfilUsuario, Usuario


EXTENSOES_PERMITIDAS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

ADMIN_DEMO_EMAIL = "admin.demo@afgmed.com"


def usuario_e_admin_demo(usuario):
    return bool(
        getattr(usuario, "is_admin", False)
        and (usuario.email or "").strip().lower() == ADMIN_DEMO_EMAIL
    )


def obter_medico_vinculado(usuario):
    if not getattr(usuario, "is_medico", False):
        return None

    if getattr(usuario, "is_admin", False):
        return None

    if not getattr(usuario, "id_medico", None):
        return None

    return usuario.medico


def obter_perfil_usuario(usuario):
    """
    Retorna o perfil complementar existente.

    Quando ainda não existe, cria apenas um objeto temporário usando
    id_usuario. Não usa PerfilUsuario(usuario=usuario), pois essa forma
    altera usuario.perfil antes de o novo objeto entrar na sessão e pode
    gerar SAWarning durante consultas automáticas dos templates.
    """

    perfil_existente = usuario.perfil

    if perfil_existente is not None:
        return perfil_existente

    return PerfilUsuario(
        id_usuario=usuario.id,
    )


def salvar_foto_perfil(arquivo, usuario, medico_vinculado):
    nome_original = secure_filename(
        arquivo.filename
    )

    extensao = os.path.splitext(
        nome_original
    )[1].lower()

    if extensao not in EXTENSOES_PERMITIDAS:
        raise ValueError(
            "Formato de imagem inválido. Use JPG, PNG ou WEBP."
        )

    nome_foto = f"{uuid4().hex}{extensao}"

    if medico_vinculado is not None:
        nome_pasta = "fotos_medicos"
    else:
        nome_pasta = "fotos_perfil"

    pasta_fotos = os.path.join(
        app.root_path,
        "static",
        nome_pasta,
    )

    os.makedirs(
        pasta_fotos,
        exist_ok=True,
    )

    caminho = os.path.join(
        pasta_fotos,
        nome_foto,
    )

    arquivo.save(
        caminho
    )

    if medico_vinculado is not None:
        medico_vinculado.foto = nome_foto
    else:
        usuario.foto = nome_foto


@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    usuario = current_user

    medico_vinculado = obter_medico_vinculado(
        usuario
    )

    perfil_usuario = obter_perfil_usuario(
        usuario
    )

    conta_demo = usuario_e_admin_demo(
        usuario
    )

    if request.method == "POST":
        arquivo_foto = request.files.get(
            "foto"
        )

        if arquivo_foto and arquivo_foto.filename:
            try:
                salvar_foto_perfil(
                    arquivo_foto,
                    usuario,
                    medico_vinculado,
                )

            except ValueError as erro:
                flash(
                    str(erro),
                    "danger",
                )

                return redirect(
                    url_for("perfil")
                )

        usuario.nome = (
            request.form.get("nome")
            or usuario.nome
        ).strip()

        usuario.sobrenome = (
            request.form.get("sobrenome")
            or usuario.sobrenome
        ).strip()

        email_novo = (
            request.form.get("email")
            or usuario.email
        ).strip().lower()

        if conta_demo:
            email_novo = ADMIN_DEMO_EMAIL

        email_em_uso = Usuario.query.filter(
            Usuario.email == email_novo,
            Usuario.id != current_user.id,
        ).first()

        if email_em_uso:
            flash(
                "Este e-mail já está em uso.",
                "danger",
            )

            return redirect(
                url_for("perfil")
            )

        usuario.email = email_novo

        perfil_usuario.telefone = (
            request.form.get("telefone")
            or None
        )

        perfil_usuario.cpf = (
            request.form.get("cpf")
            or None
        )

        data_nascimento = request.form.get(
            "data_nascimento"
        )

        if data_nascimento:
            try:
                perfil_usuario.data_nascimento = (
                    datetime.strptime(
                        data_nascimento,
                        "%Y-%m-%d",
                    ).date()
                )

            except ValueError:
                flash(
                    "Data de nascimento inválida.",
                    "danger",
                )

                return redirect(
                    url_for("perfil")
                )

        else:
            perfil_usuario.data_nascimento = None

        perfil_usuario.endereco = (
            request.form.get("endereco")
            or None
        )

        perfil_usuario.cidade = (
            request.form.get("cidade")
            or None
        )

        perfil_usuario.estado = (
            request.form.get("estado")
            or None
        )

        perfil_usuario.cep = (
            request.form.get("cep")
            or None
        )

        try:
            database.session.add(
                usuario
            )

            database.session.add(
                perfil_usuario
            )

            if medico_vinculado is not None:
                database.session.add(
                    medico_vinculado
                )

            database.session.commit()

        except IntegrityError:
            database.session.rollback()

            flash(
                "Não foi possível atualizar o perfil porque o e-mail "
                "ou CPF informado já está em uso.",
                "danger",
            )

            return redirect(
                url_for("perfil")
            )

        except SQLAlchemyError:
            database.session.rollback()

            app.logger.exception(
                "Erro ao atualizar o perfil do usuário %s.",
                current_user.id,
            )

            flash(
                "Não foi possível salvar o perfil. Tente novamente.",
                "danger",
            )

            return redirect(
                url_for("perfil")
            )

        if conta_demo:
            flash(
                "Perfil atualizado. O e-mail da conta demonstrativa "
                "foi mantido para preservar o acesso público.",
                "info",
            )

        else:
            flash(
                "Perfil atualizado com sucesso!",
                "success",
            )

        return redirect(
            url_for("perfil")
        )

    return render_template(
        "perfil.html",
        usuario=usuario,
        perfil=perfil_usuario,
        conta_demo=conta_demo,
    )