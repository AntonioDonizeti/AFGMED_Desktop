from datetime import date
from functools import wraps
import unicodedata

from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask_login import (
    current_user,
    login_required,
)

from projetoafgmed import app
from projetoafgmed.models import (
    Consulta,
    Pedido,
)

from projetoafgmed.servicos_compras import (
    status_visual_pedido,
)

from projetoafgmed.status import (
    CONSULTA_AGENDADA,
    CONSULTA_CANCELADA,
    CONSULTA_CONCLUIDA,
    PAGAMENTO_APROVADO,
    PAGAMENTOS_NAO_APROVADOS,
    PEDIDO_FALHA,
    PEDIDO_PAGO,
    PEDIDO_PAGO_PENDENCIA_ESTOQUE,
    normalizar_status_pagamento,
)


# ==========================================================
# PROTEÇÃO DAS ROTAS ADMINISTRATIVAS
# ==========================================================

def admin_required(funcao):
    """
    Permite o acesso somente para administradores.

    A proteção fica neste próprio arquivo, portanto não é
    necessário criar rotas/permissoes.py.
    """

    @wraps(funcao)
    def funcao_protegida(*args, **kwargs):
        if not current_user.is_authenticated:
            flash(
                "Faça login para acessar esta página.",
                "warning",
            )

            return redirect(
                url_for("login")
            )

        if not getattr(
            current_user,
            "is_admin",
            False,
        ):
            flash(
                "Apenas administradores podem acessar esta página.",
                "warning",
            )

            # Médico não possui acesso à Home nem a Produtos.
            if (
                getattr(
                    current_user,
                    "is_medico",
                    False,
                )
                and not getattr(
                    current_user,
                    "is_admin",
                    False,
                )
            ):
                return redirect(
                    url_for("medicos")
                )

            return redirect(
                url_for("homepage")
            )

        return funcao(*args, **kwargs)

    return funcao_protegida


# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def _normalizar(valor):
    """
    Normaliza textos para permitir buscas sem diferenciar
    letras maiúsculas, minúsculas ou acentos.
    """

    texto = unicodedata.normalize(
        "NFKD",
        str(valor or ""),
    )

    return "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    ).casefold().strip()


def _classificar_pedido(pedido):
    """
    Agrupa os diferentes status de pedido em:
    pendente, pago ou falha.
    """

    pagamento = normalizar_status_pagamento(
        pedido.status_pagamento
    )

    if (
        pedido.status
        in {
            PEDIDO_PAGO,
            PEDIDO_PAGO_PENDENCIA_ESTOQUE,
        }
        or pagamento == PAGAMENTO_APROVADO
    ):
        return "pago"

    if (
        pedido.status == PEDIDO_FALHA
        or pagamento in PAGAMENTOS_NAO_APROVADOS
    ):
        return "falha"

    return "pendente"


def _ordenar_consultas(consultas):
    """
    Mantém as consultas abertas primeiro.

    Ordem utilizada:
    1. Consultas agendadas;
    2. Data mais próxima;
    3. Horário mais próximo;
    4. Consultas encerradas depois;
    5. Encerradas mais recentes primeiro.
    """

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


# ==========================================================
# PEDIDOS GERAIS
# SOMENTE ADMINISTRADOR
# ==========================================================

@app.route("/admin/pedidos-gerais")
@login_required
@admin_required
def admin_pedidos_gerais():
    busca = (
        request.args.get("busca")
        or ""
    ).strip()

    status_atual = (
        request.args.get("status")
        or "todos"
    ).strip().lower()

    filtros_validos = {
        "todos",
        "pendente",
        "pago",
        "falha",
    }

    if status_atual not in filtros_validos:
        status_atual = "todos"

    todos_pedidos = (
        Pedido.query
        .order_by(
            Pedido.data_criacao.desc()
        )
        .all()
    )

    resumo = {
        "total": len(todos_pedidos),
        "pendentes": 0,
        "pagos": 0,
        "falhas": 0,
    }

    pedidos_formatados = []

    busca_normalizada = _normalizar(
        busca
    )

    for pedido in todos_pedidos:
        classificacao = (
            _classificar_pedido(
                pedido
            )
        )

        campo_resumo = {
            "pendente": "pendentes",
            "pago": "pagos",
            "falha": "falhas",
        }[classificacao]

        resumo[campo_resumo] += 1

        usuario = pedido.usuario

        if usuario:
            cliente = (
                f"{usuario.nome or ''} "
                f"{usuario.sobrenome or ''}"
            ).strip()

            email_cliente = (
                usuario.email or ""
            )

        else:
            cliente = (
                "Usuário não encontrado"
            )

            email_cliente = ""

        nomes_produtos = " ".join(
            item.nome_produto or ""
            for item in pedido.itens
        )

        chave_busca = _normalizar(
            (
                f"{pedido.id} "
                f"{cliente} "
                f"{email_cliente} "
                f"{pedido.cidade or ''} "
                f"{pedido.estado or ''} "
                f"{pedido.cep or ''} "
                f"{pedido.endereco or ''} "
                f"{pedido.status or ''} "
                f"{pedido.status_pagamento or ''} "
                f"{pedido.mercado_pago_payment_id or ''} "
                f"{nomes_produtos}"
            )
        )

        if (
            status_atual != "todos"
            and classificacao
            != status_atual
        ):
            continue

        if (
            busca_normalizada
            and busca_normalizada
            not in chave_busca
        ):
            continue

        quantidade_itens = sum(
            int(item.quantidade or 0)
            for item in pedido.itens
        )

        pedidos_formatados.append(
            {
                "pedido": pedido,
                "cliente": cliente,
                "email": email_cliente,
                "quantidade_itens": (
                    quantidade_itens
                ),
                "classificacao": (
                    classificacao
                ),
                "status_visual": (
                    status_visual_pedido(
                        pedido
                    )
                ),
            }
        )

    return render_template(
        "admin_pedidos_gerais.html",
        pedidos=pedidos_formatados,
        resumo=resumo,
        busca=busca,
        status_atual=status_atual,
    )


# ==========================================================
# AGENDA GERAL
# SOMENTE VISUALIZAÇÃO PELO ADMINISTRADOR
# ==========================================================

@app.route("/admin/agenda-geral")
@login_required
@admin_required
def admin_agenda_geral():
    busca = (
        request.args.get("busca")
        or ""
    ).strip()

    status_atual = (
        request.args.get("status")
        or "todas"
    ).strip().lower()

    filtros_validos = {
        "todas",
        "hoje",
        CONSULTA_AGENDADA,
        CONSULTA_CONCLUIDA,
        CONSULTA_CANCELADA,
    }

    if status_atual not in filtros_validos:
        status_atual = "todas"

    todas_consultas = (
        Consulta.query.all()
    )

    consultas_ordenadas = (
        _ordenar_consultas(
            todas_consultas
        )
    )

    hoje = date.today()

    resumo = {
        "total": len(
            todas_consultas
        ),
        "hoje": sum(
            1
            for consulta in todas_consultas
            if (
                consulta.status
                == CONSULTA_AGENDADA
                and consulta.data == hoje
            )
        ),
        "agendadas": sum(
            1
            for consulta in todas_consultas
            if consulta.status
            == CONSULTA_AGENDADA
        ),
        "concluidas": sum(
            1
            for consulta in todas_consultas
            if consulta.status
            == CONSULTA_CONCLUIDA
        ),
        "canceladas": sum(
            1
            for consulta in todas_consultas
            if consulta.status
            == CONSULTA_CANCELADA
        ),
    }

    busca_normalizada = _normalizar(
        busca
    )

    consultas_exibidas = []

    for consulta in consultas_ordenadas:
        medico = consulta.medico
        paciente = consulta.usuario

        if medico:
            nome_medico = (
                f"{medico.nome or ''} "
                f"{medico.sobrenome or ''}"
            ).strip()

            especialidade = (
                medico.especialidade or ""
            )

        else:
            nome_medico = (
                "Médico não encontrado"
            )

            especialidade = ""

        if paciente:
            nome_paciente = (
                f"{paciente.nome or ''} "
                f"{paciente.sobrenome or ''}"
            ).strip()

            email_paciente = (
                paciente.email or ""
            )

            perfil_paciente = getattr(
                paciente,
                "perfil",
                None,
            )

            telefone = (
                getattr(
                    perfil_paciente,
                    "telefone",
                    "",
                )
                or ""
            )

        else:
            nome_paciente = (
                "Paciente não encontrado"
            )

            email_paciente = ""
            telefone = ""

        # Filtro: consultas agendadas para hoje.
        if status_atual == "hoje":
            if not (
                consulta.status
                == CONSULTA_AGENDADA
                and consulta.data == hoje
            ):
                continue

        # Filtro pelos demais status.
        elif (
            status_atual != "todas"
            and consulta.status
            != status_atual
        ):
            continue

        data_texto = (
            consulta.data.strftime(
                "%d/%m/%Y"
            )
            if consulta.data
            else ""
        )

        chave_busca = _normalizar(
            (
                f"{consulta.id} "
                f"{nome_medico} "
                f"{especialidade} "
                f"{nome_paciente} "
                f"{email_paciente} "
                f"{telefone} "
                f"{data_texto} "
                f"{consulta.data or ''} "
                f"{consulta.horario or ''} "
                f"{consulta.status or ''}"
            )
        )

        if (
            busca_normalizada
            and busca_normalizada
            not in chave_busca
        ):
            continue

        consultas_exibidas.append(
            {
                "consulta": consulta,
                "medico": nome_medico,
                "especialidade": (
                    especialidade
                ),
                "paciente": (
                    nome_paciente
                ),
                "email": (
                    email_paciente
                ),
                "telefone": (
                    telefone or "—"
                ),
            }
        )

    return render_template(
        "admin_agenda_geral.html",
        consultas=consultas_exibidas,
        resumo=resumo,
        busca=busca,
        status_atual=status_atual,
    )