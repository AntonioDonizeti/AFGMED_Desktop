from datetime import date
import os

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from werkzeug.utils import secure_filename

from projetoafgmed import app, database
from projetoafgmed.forms import FormMedico
from projetoafgmed.models import Consulta, Medico, Usuario
from projetoafgmed.servicos_consultas import status_visual_consulta
from projetoafgmed.servicos_medicos import (
    medico_logado,
    sincronizar_usuario_medico,
)
from projetoafgmed.status import (
    CONSULTA_AGENDADA,
    CONSULTA_CANCELADA,
    CONSULTA_CONCLUIDA,
)


def _ordenar_consultas_medico(consultas):
    """Mantém abertas primeiro; fechadas ficam da mais recente para a antiga."""
    abertas = sorted(
        (
            consulta
            for consulta in consultas
            if consulta.status == CONSULTA_AGENDADA
        ),
        key=lambda consulta: (
            consulta.data or date.max,
            consulta.horario or "",
        ),
    )

    encerradas = sorted(
        (
            consulta
            for consulta in consultas
            if consulta.status != CONSULTA_AGENDADA
        ),
        key=lambda consulta: (
            consulta.data or date.min,
            consulta.horario or "",
        ),
        reverse=True,
    )

    return abertas + encerradas


@app.route("/medicos")
@login_required
def medicos():
    if (
        getattr(current_user, "is_medico", False)
        and not getattr(current_user, "is_admin", False)
    ):
        medico = medico_logado()
        filtro_atual = (request.args.get("filtro") or "todas").strip().lower()
        filtros_validos = {
            "todas",
            "hoje",
            CONSULTA_AGENDADA,
            CONSULTA_CONCLUIDA,
            CONSULTA_CANCELADA,
        }

        if filtro_atual not in filtros_validos:
            filtro_atual = "todas"

        if not medico:
            flash(
                "Seu usuário médico ainda não está vinculado a um cadastro médico.",
                "warning",
            )
            return render_template(
                "consultas_medico.html",
                medico=None,
                consultas=[],
                filtro_atual=filtro_atual,
                resumo={
                    "total": 0,
                    "hoje": 0,
                    "agendadas": 0,
                    "concluidas": 0,
                    "canceladas": 0,
                },
                status_visual_consulta=status_visual_consulta,
            )

        todas_consultas = Consulta.query.filter_by(
            medico_id=medico.id
        ).all()

        consultas_ordenadas = _ordenar_consultas_medico(todas_consultas)
        hoje = date.today()

        resumo = {
            "total": len(todas_consultas),
            "hoje": sum(
                1
                for consulta in todas_consultas
                if (
                    consulta.status == CONSULTA_AGENDADA
                    and consulta.data == hoje
                )
            ),
            "agendadas": sum(
                1
                for consulta in todas_consultas
                if consulta.status == CONSULTA_AGENDADA
            ),
            "concluidas": sum(
                1
                for consulta in todas_consultas
                if consulta.status == CONSULTA_CONCLUIDA
            ),
            "canceladas": sum(
                1
                for consulta in todas_consultas
                if consulta.status == CONSULTA_CANCELADA
            ),
        }

        if filtro_atual == "hoje":
            consultas_exibidas = [
                consulta
                for consulta in consultas_ordenadas
                if (
                    consulta.status == CONSULTA_AGENDADA
                    and consulta.data == hoje
                )
            ]
        elif filtro_atual == "todas":
            consultas_exibidas = consultas_ordenadas
        else:
            consultas_exibidas = [
                consulta
                for consulta in consultas_ordenadas
                if consulta.status == filtro_atual
            ]

        return render_template(
            "consultas_medico.html",
            medico=medico,
            consultas=consultas_exibidas,
            filtro_atual=filtro_atual,
            resumo=resumo,
            status_visual_consulta=status_visual_consulta,
        )

    return render_template(
        "medicos.html",
        medicos=Medico.query.order_by(
            Medico.nome.asc(),
            Medico.sobrenome.asc(),
        ).all(),
    )


@app.route("/cadastro-medico", methods=["GET", "POST"])
@login_required
def cadastro_medico():
    if not getattr(current_user, "is_admin", False):
        flash("Apenas administradores podem acessar esta página.", "warning")
        return redirect(url_for("homepage"))

    form = FormMedico()

    if form.validate_on_submit():
        email_medico = form.email.data.strip().lower()

        medico_existente = Medico.query.filter(
            func.lower(Medico.email) == email_medico
        ).first()

        if medico_existente:
            flash("Já existe um médico cadastrado com este e-mail.", "danger")
            return redirect(url_for("cadastro_medico"))

        nome_arquivo = "default.jpg"

        if form.foto.data:
            arquivo = form.foto.data
            nome_arquivo = secure_filename(arquivo.filename)

            caminho = os.path.join(
                current_app.root_path,
                "static/fotos_medicos",
                nome_arquivo
            )

            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            arquivo.save(caminho)

        medico = Medico(
            nome=form.nome.data,
            sobrenome=form.sobrenome.data,
            especialidade=form.especialidade.data,
            email=email_medico,
            telefone=form.telefone.data,
            foto=nome_arquivo
        )

        database.session.add(medico)
        database.session.flush()

        usuario_medico, erro_usuario = sincronizar_usuario_medico(medico)

        if erro_usuario:
            database.session.rollback()
            flash(erro_usuario, "danger")
            return redirect(url_for("cadastro_medico"))

        database.session.commit()

        flash(
            "Médico cadastrado com sucesso! Usuário médico criado/vinculado com senha padrão 123456.",
            "success"
        )

        return redirect(url_for("medicos"))

    return render_template("cadastro_medico.html", form=form, medico=None)


@app.route("/editar-medico/<int:id_medico>", methods=["GET", "POST"])
@login_required
def editar_medico(id_medico):
    if not getattr(current_user, "is_admin", False):
        flash("Apenas administradores podem acessar esta página.", "warning")
        return redirect(url_for("homepage"))

    medico = Medico.query.get_or_404(id_medico)
    form = FormMedico()

    if request.method == "GET":
        form.nome.data = medico.nome
        form.sobrenome.data = medico.sobrenome
        form.especialidade.data = medico.especialidade
        form.email.data = medico.email
        form.telefone.data = medico.telefone

    if form.validate_on_submit():
        email_medico = form.email.data.strip().lower()

        medico_com_email = Medico.query.filter(
            func.lower(Medico.email) == email_medico,
            Medico.id != medico.id
        ).first()

        if medico_com_email:
            flash("Já existe outro médico cadastrado com este e-mail.", "danger")
            return redirect(url_for("editar_medico", id_medico=medico.id))

        medico.nome = form.nome.data
        medico.sobrenome = form.sobrenome.data
        medico.especialidade = form.especialidade.data
        medico.email = email_medico
        medico.telefone = form.telefone.data

        if form.foto.data:
            arquivo = form.foto.data
            nome_foto = secure_filename(arquivo.filename)

            caminho = os.path.join(
                current_app.root_path,
                "static/fotos_medicos",
                nome_foto
            )

            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            arquivo.save(caminho)

            medico.foto = nome_foto

        usuario_medico, erro_usuario = sincronizar_usuario_medico(medico)

        if erro_usuario:
            database.session.rollback()
            flash(erro_usuario, "danger")
            return redirect(url_for("editar_medico", id_medico=medico.id))

        database.session.commit()

        flash("Médico atualizado com sucesso! Usuário médico sincronizado.", "success")
        return redirect(url_for("medicos"))

    return render_template("cadastro_medico.html", form=form, medico=medico)


@app.route("/remover-medico/<int:id_medico>", methods=["POST"])
@login_required
def remover_medico(id_medico):
    if not getattr(current_user, "is_admin", False):
        flash("Apenas administradores podem acessar.", "warning")
        return redirect(url_for("homepage"))

    medico = Medico.query.get_or_404(id_medico)

    usuario_medico = Usuario.query.filter_by(id_medico=medico.id).first()

    Consulta.query.filter_by(medico_id=id_medico).delete()

    if usuario_medico:
        usuario_medico.is_medico = False
        usuario_medico.id_medico = None

    database.session.delete(medico)
    database.session.commit()

    flash("Médico removido com sucesso! O usuário vinculado deixou de ser médico.", "success")
    return redirect(url_for("medicos"))