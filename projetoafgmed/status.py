"""Status padronizados usados pelo AFGMED.

Os valores armazenados no banco ficam centralizados neste arquivo para evitar
variações como ``pendente`` e ``pending`` representando a mesma situação.
"""

# Consultas
CONSULTA_AGENDADA = "agendada"
CONSULTA_CANCELADA = "cancelada"
CONSULTA_CONCLUIDA = "concluida"
CONSULTAS_QUE_OCUPAM_HORARIO = (
    CONSULTA_AGENDADA,
    CONSULTA_CONCLUIDA,
)

# Carrinhos
CARRINHO_ATIVO = "ativo"
CARRINHO_AGUARDANDO_PAGAMENTO = "aguardando_pagamento"
CARRINHO_FINALIZADO = "finalizado"

# Pedidos
PEDIDO_AGUARDANDO_PAGAMENTO = "aguardando_pagamento"
PEDIDO_PAGO = "pago"
PEDIDO_FALHA = "falha"
PEDIDO_PAGO_PENDENCIA_ESTOQUE = "pago_pendencia_estoque"

# Status retornados pelo Mercado Pago
PAGAMENTO_PENDENTE = "pending"
PAGAMENTO_EM_PROCESSAMENTO = "in_process"
PAGAMENTO_APROVADO = "approved"
PAGAMENTO_REJEITADO = "rejected"
PAGAMENTO_CANCELADO = "cancelled"
PAGAMENTO_REEMBOLSADO = "refunded"
PAGAMENTO_CONTESTADO = "charged_back"

PAGAMENTOS_PENDENTES = (
    PAGAMENTO_PENDENTE,
    PAGAMENTO_EM_PROCESSAMENTO,
)

PAGAMENTOS_NAO_APROVADOS = (
    PAGAMENTO_REJEITADO,
    PAGAMENTO_CANCELADO,
    PAGAMENTO_REEMBOLSADO,
    PAGAMENTO_CONTESTADO,
)


def normalizar_status_pagamento(status):
    """Converte valores antigos do banco para o padrão atual da aplicação."""
    valor = str(status or PAGAMENTO_PENDENTE).strip().lower()

    equivalencias = {
        "pendente": PAGAMENTO_PENDENTE,
        "processando": PAGAMENTO_EM_PROCESSAMENTO,
        "aprovado": PAGAMENTO_APROVADO,
        "falha": PAGAMENTO_REJEITADO,
        "cancelado": PAGAMENTO_CANCELADO,
    }

    return equivalencias.get(valor, valor)
