from flask import (
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required, current_user

from projetoafgmed import app, database
from projetoafgmed.models import Medico, Consulta
from projetoafgmed.servicos_consultas import (
    ErroConsulta,
    HORARIOS_CONSULTA,
    horarios_indisponiveis_por_tempo,
    horarios_ocupados_medico,
    salvar_consulta,
    status_visual_consulta,
)
from projetoafgmed.status import (
    CONSULTA_AGENDADA,
    CONSULTA_CANCELADA,
    CONSULTA_CONCLUIDA,
)


@app.route("/consultas/<int:medico_id>", methods=["GET", "POST"])
@login_required
def consultas(medico_id):
    if getattr(current_user, "is_medico", False) and not getattr(current_user, "is_admin", False):
        flash("Usuários médicos não podem marcar consultas como pacientes.", "warning")
        return redirect(url_for("medicos"))

    medico = Medico.query.get_or_404(medico_id)
    horarios = list(HORARIOS_CONSULTA)

    if request.method == "POST":
        horario = request.form.get("horario")
        data_consulta = request.form.get("data_consulta")

        try:
            if not horario or not data_consulta:
                raise ErroConsulta("Escolha data e horário para continuar.")

            salvar_consulta(
                medico_id=medico.id,
                usuario_id=current_user.id,
                data_consulta=data_consulta,
                horario=horario,
            )

        except ErroConsulta as erro:
            flash(str(erro), "warning")
            return redirect(url_for("consultas", medico_id=medico.id))

        except Exception:
            current_app.logger.exception("Erro ao salvar consulta")
            flash(
                "Não foi possível salvar a consulta. Tente novamente.",
                "danger",
            )
            return redirect(url_for("consultas", medico_id=medico.id))

        flash("Consulta agendada com sucesso!", "success")
        return redirect(url_for("meus_agendamentos"))

    consultas_marcadas = Consulta.query.filter_by(medico_id=medico.id).all()

    return render_template(
        "consultas.html",
        medico=medico,
        horarios=horarios,
        consultas=consultas_marcadas
    )


@app.route("/horarios_disponiveis/<int:medico_id>/<data>")
@login_required
def horarios_disponiveis(medico_id, data):
    try:
        ocupados = horarios_ocupados_medico(medico_id, data)
        indisponiveis_tempo = horarios_indisponiveis_por_tempo(data)
    except ErroConsulta:
        return jsonify([])

    return jsonify(sorted(ocupados | indisponiveis_tempo))


@app.route("/meus_agendamentos")
@login_required
def meus_agendamentos():
    consultas_usuario = Consulta.query.filter(
        Consulta.usuario_id == current_user.id,
        Consulta.status != CONSULTA_CANCELADA
    ).order_by(
        Consulta.data.asc(),
        Consulta.horario.asc()
    ).all()

    return render_template(
        "meus_agendamentos.html",
        consultas=consultas_usuario,
        status_visual_consulta=status_visual_consulta
    )


@app.route("/cancelar_consulta/<int:consulta_id>", methods=["POST"])
@login_required
def cancelar_consulta(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)

    if consulta.usuario_id != current_user.id and not getattr(current_user, "is_admin", False):
        flash("Você não pode cancelar esta consulta.", "danger")
        return redirect(url_for("meus_agendamentos"))

    if consulta.status != CONSULTA_AGENDADA:
        flash("Apenas consultas agendadas podem ser canceladas.", "warning")
        return redirect(url_for("meus_agendamentos"))

    consulta.status = CONSULTA_CANCELADA

    try:
        database.session.commit()
    except Exception:
        database.session.rollback()
        current_app.logger.exception("Erro ao cancelar consulta")
        flash(
            "Não foi possível cancelar a consulta. Tente novamente.",
            "danger",
        )
        return redirect(url_for("meus_agendamentos"))

    flash("Consulta cancelada com sucesso!", "success")
    return redirect(url_for("meus_agendamentos"))


@app.route("/concluir-consulta/<int:consulta_id>", methods=["POST"])
@login_required
def concluir_consulta(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)

    usuario_e_medico_da_consulta = (
        getattr(current_user, "is_medico", False)
        and current_user.id_medico == consulta.medico_id
    )

    if not usuario_e_medico_da_consulta and not getattr(current_user, "is_admin", False):
        flash("Você não pode concluir esta consulta.", "danger")
        return redirect(url_for("medicos"))

    if consulta.status != CONSULTA_AGENDADA:
        flash("Apenas consultas agendadas podem ser concluídas.", "warning")
        return redirect(url_for("medicos"))

    consulta.status = CONSULTA_CONCLUIDA

    try:
        database.session.commit()
    except Exception:
        database.session.rollback()
        current_app.logger.exception("Erro ao concluir consulta")
        flash(
            "Não foi possível concluir a consulta. Tente novamente.",
            "danger",
        )
        return redirect(url_for("medicos"))

    flash("Consulta concluída com sucesso!", "success")
    return redirect(url_for("medicos"))
