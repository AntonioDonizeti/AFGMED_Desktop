from datetime import date, datetime


HORARIOS_CONSULTA = (
    "09:00",
    "10:00",
    "11:00",
    "14:00",
    "15:00",
    "16:00",
)


class ErroConsulta(ValueError):
    """Erro de validação relacionado ao agendamento de consultas."""


def normalizar_data_consulta(valor):
    """Converte uma data recebida em ``datetime.date``."""
    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    try:
        return datetime.strptime(str(valor), "%Y-%m-%d").date()
    except (TypeError, ValueError) as erro:
        raise ErroConsulta("Data inválida.") from erro


def converter_horario(horario):
    """Converte um horário HH:MM em ``datetime.time``."""
    try:
        return datetime.strptime(str(horario), "%H:%M").time()
    except (TypeError, ValueError) as erro:
        raise ErroConsulta("Horário inválido.") from erro


def validar_data_horario_futuro(data_consulta, horario, agora=None):
    """Valida se a consulta está em uma data e horário ainda futuros.

    Essa validação deve ser executada no momento de salvar, mesmo que a
    interface já tenha desabilitado datas e horários antigos. Dessa forma,
    alterações manuais, atrasos com a janela aberta e requisições diretas não
    conseguem gravar uma consulta no passado.
    """
    data_obj = normalizar_data_consulta(data_consulta)
    horario_texto = str(horario or "").strip()

    if horario_texto not in HORARIOS_CONSULTA:
        raise ErroConsulta("Horário inválido.")

    momento_atual = agora or datetime.now()
    momento_consulta = datetime.combine(
        data_obj,
        converter_horario(horario_texto),
    )

    if data_obj < momento_atual.date():
        raise ErroConsulta("Não é possível marcar consulta em data passada.")

    if momento_consulta <= momento_atual:
        raise ErroConsulta(
            "Esse horário já passou. Escolha um horário posterior ao atual."
        )

    return momento_consulta


def horarios_indisponiveis_por_tempo(
    data_consulta,
    horarios=HORARIOS_CONSULTA,
    agora=None,
):
    """Retorna horários que já passaram para a data informada."""
    data_obj = normalizar_data_consulta(data_consulta)
    momento_atual = agora or datetime.now()

    if data_obj < momento_atual.date():
        return set(horarios)

    if data_obj > momento_atual.date():
        return set()

    indisponiveis = set()

    for horario in horarios:
        momento_horario = datetime.combine(
            data_obj,
            converter_horario(horario),
        )

        if momento_horario <= momento_atual:
            indisponiveis.add(horario)

    return indisponiveis


def status_visual_consulta(consulta):
    status = (consulta.status or "agendada").lower()

    if status == "agendada":
        return {
            "classe": "bg-primary",
            "icone": "bi-calendar-check",
            "texto": "Agendada",
        }

    if status == "cancelada":
        return {
            "classe": "bg-danger",
            "icone": "bi-x-circle",
            "texto": "Cancelada",
        }

    if status == "concluida":
        return {
            "classe": "bg-success",
            "icone": "bi-check-circle",
            "texto": "Concluída",
        }

    return {
        "classe": "bg-secondary",
        "icone": "bi-info-circle",
        "texto": "Em análise",
    }
