"""Testes das regras e rotas de consultas existentes no primeiro ZIP."""

from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest

from projetoafgmed import database
from projetoafgmed.models import Consulta
from projetoafgmed.servicos_consultas import (
    ErroConsulta,
    HORARIOS_CONSULTA,
    horarios_indisponiveis_por_tempo,
    normalizar_data_consulta,
    status_visual_consulta,
    validar_data_horario_futuro,
)


def data_futura():
    return date.today() + timedelta(days=30)


def test_normalizar_data_consulta():
    assert normalizar_data_consulta("2030-05-20") == date(2030, 5, 20)
    assert normalizar_data_consulta(datetime(2030, 5, 20, 10, 0)) == date(2030, 5, 20)


def test_data_invalida_gera_erro():
    with pytest.raises(ErroConsulta, match="Data inválida"):
        normalizar_data_consulta("20/05/2030")


def test_validar_consulta_futura():
    agora = datetime(2030, 1, 10, 8, 0)
    momento = validar_data_horario_futuro("2030-01-10", "09:00", agora=agora)
    assert momento == datetime(2030, 1, 10, 9, 0)


def test_rejeita_horario_fora_da_grade():
    with pytest.raises(ErroConsulta, match="Horário inválido"):
        validar_data_horario_futuro("2030-01-10", "12:30", agora=datetime(2030, 1, 9))


def test_rejeita_data_passada():
    with pytest.raises(ErroConsulta, match="data passada"):
        validar_data_horario_futuro("2030-01-09", "09:00", agora=datetime(2030, 1, 10))


def test_horarios_indisponiveis_no_dia_atual():
    agora = datetime(2030, 1, 10, 10, 30)
    indisponiveis = horarios_indisponiveis_por_tempo(date(2030, 1, 10), agora=agora)
    assert indisponiveis == {"09:00", "10:00"}


def test_status_visual_consulta():
    assert status_visual_consulta(SimpleNamespace(status="agendada"))["texto"] == "Agendada"
    assert status_visual_consulta(SimpleNamespace(status="cancelada"))["texto"] == "Cancelada"
    assert status_visual_consulta(SimpleNamespace(status="concluida"))["texto"] == "Concluída"
    assert status_visual_consulta(SimpleNamespace(status="outro"))["texto"] == "Em análise"


def test_rota_cria_consulta_valida(
    client,
    autenticar,
    criar_usuario,
    criar_medico,
):
    usuario = criar_usuario()
    medico = criar_medico()
    autenticar(usuario)

    resposta = client.post(
        f"/consultas/{medico.id}",
        data={"data_consulta": data_futura().isoformat(), "horario": HORARIOS_CONSULTA[0]},
        follow_redirects=False,
    )

    consulta = Consulta.query.one()
    assert resposta.status_code == 302
    assert consulta.usuario_id == usuario.id
    assert consulta.medico_id == medico.id
    assert consulta.status == "agendada"


def test_rota_impede_mesmo_horario_para_o_medico(
    client,
    autenticar,
    criar_usuario,
    criar_medico,
):
    usuario_1 = criar_usuario()
    usuario_2 = criar_usuario()
    medico = criar_medico()
    dados = {"data_consulta": data_futura().isoformat(), "horario": "09:00"}

    autenticar(usuario_1)
    client.post(f"/consultas/{medico.id}", data=dados)

    client.get("/logout")
    autenticar(usuario_2)
    client.post(f"/consultas/{medico.id}", data=dados)

    assert Consulta.query.count() == 1


def test_horarios_disponiveis_retorna_ocupados(
    client,
    autenticar,
    criar_usuario,
    criar_medico,
):
    usuario = criar_usuario()
    medico = criar_medico()
    autenticar(usuario)
    data = data_futura()
    database.session.add(
        Consulta(
            medico_id=medico.id,
            usuario_id=usuario.id,
            data=data,
            horario="10:00",
            status="agendada",
        )
    )
    database.session.commit()

    resposta = client.get(f"/horarios_disponiveis/{medico.id}/{data.isoformat()}")

    assert resposta.status_code == 200
    assert resposta.get_json() == ["10:00"]


def test_paciente_cancela_propria_consulta(
    client,
    autenticar,
    criar_usuario,
    criar_medico,
):
    usuario = criar_usuario()
    medico = criar_medico()
    consulta = Consulta(
        medico_id=medico.id,
        usuario_id=usuario.id,
        data=data_futura(),
        horario="09:00",
        status="agendada",
    )
    database.session.add(consulta)
    database.session.commit()
    autenticar(usuario)

    resposta = client.post(f"/cancelar_consulta/{consulta.id}")

    assert resposta.status_code == 302
    assert database.session.get(Consulta, consulta.id).status == "cancelada"


def test_paciente_nao_cancela_consulta_de_outro(
    client,
    autenticar,
    criar_usuario,
    criar_medico,
):
    dono = criar_usuario()
    outro = criar_usuario()
    medico = criar_medico()
    consulta = Consulta(
        medico_id=medico.id,
        usuario_id=dono.id,
        data=data_futura(),
        horario="09:00",
        status="agendada",
    )
    database.session.add(consulta)
    database.session.commit()
    autenticar(outro)

    client.post(f"/cancelar_consulta/{consulta.id}")

    assert database.session.get(Consulta, consulta.id).status == "agendada"


def test_medico_vinculado_conclui_consulta(
    client,
    autenticar,
    criar_usuario,
    criar_medico,
):
    paciente = criar_usuario()
    medico = criar_medico()
    usuario_medico = criar_usuario(is_medico=True, id_medico=medico.id)
    consulta = Consulta(
        medico_id=medico.id,
        usuario_id=paciente.id,
        data=data_futura(),
        horario="11:00",
        status="agendada",
    )
    database.session.add(consulta)
    database.session.commit()
    autenticar(usuario_medico)

    client.post(f"/concluir-consulta/{consulta.id}")

    assert database.session.get(Consulta, consulta.id).status == "concluida"


def test_usuario_medico_nao_agenda_como_paciente(
    client,
    autenticar,
    criar_usuario,
    criar_medico,
):
    medico_atendimento = criar_medico()
    medico_vinculado = criar_medico()
    usuario_medico = criar_usuario(is_medico=True, id_medico=medico_vinculado.id)
    autenticar(usuario_medico)

    resposta = client.post(
        f"/consultas/{medico_atendimento.id}",
        data={"data_consulta": data_futura().isoformat(), "horario": "09:00"},
    )

    assert resposta.status_code == 302
    assert Consulta.query.count() == 0
