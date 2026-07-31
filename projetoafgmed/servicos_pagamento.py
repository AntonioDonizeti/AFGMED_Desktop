import os

import mercadopago

from projetoafgmed import database
from projetoafgmed.models import Pedido


class ErroPagamento(Exception):
    pass


def criar_preferencia_mercado_pago(pedido_id):
    access_token = os.getenv(
        "MERCADO_PAGO_ACCESS_TOKEN",
        "",
    ).strip()

    app_base_url = os.getenv(
        "APP_BASE_URL",
        "",
    ).strip().rstrip("/")

    if not access_token:
        raise ErroPagamento(
            "MERCADO_PAGO_ACCESS_TOKEN não configurado."
        )

    if not app_base_url:
        raise ErroPagamento(
            "APP_BASE_URL não configurada."
        )

    pedido = database.session.get(
        Pedido,
        pedido_id,
    )

    if pedido is None:
        raise ErroPagamento(
            "Pedido não encontrado."
        )

    if not pedido.itens:
        raise ErroPagamento(
            "O pedido não possui itens."
        )

    sdk = mercadopago.SDK(access_token)

    itens_mercado_pago = []

    for item in pedido.itens:
        itens_mercado_pago.append(
            {
                "id": str(item.id_produto or item.id),
                "title": item.nome_produto,
                "description": (
                    item.descricao_produto or ""
                ),
                "quantity": int(item.quantidade),
                "currency_id": "BRL",
                "unit_price": float(
                    item.preco_unitario
                ),
            }
        )

    preference_data = {
        "items": itens_mercado_pago,

        # Relaciona o pagamento ao pedido local.
        "external_reference": str(pedido.id),

        "back_urls": {
            "success": (
                f"{app_base_url}/pagamento/sucesso"
            ),
            "pending": (
                f"{app_base_url}/pagamento/pendente"
            ),
            "failure": (
                f"{app_base_url}/pagamento/falha"
            ),
        },

        "auto_return": "approved",

        "notification_url": (
            f"{app_base_url}/webhook/mercado-pago"
        ),
    }

    resposta = sdk.preference().create(
        preference_data
    )

    status_http = resposta.get("status")
    dados = resposta.get("response", {})

    if status_http not in (200, 201):
        mensagem = dados.get(
            "message",
            "Não foi possível criar o pagamento.",
        )

        raise ErroPagamento(mensagem)

    preference_id = dados.get("id")
    init_point = dados.get("init_point")

    if not preference_id or not init_point:
        raise ErroPagamento(
            "O Mercado Pago não retornou "
            "a URL do checkout."
        )

    pedido.mercado_pago_preference_id = (
        preference_id
    )

    pedido.mercado_pago_init_point = (
        init_point
    )

    pedido.status = "aguardando_pagamento"
    pedido.status_pagamento = "pending"

    database.session.commit()

    return {
        "preference_id": preference_id,
        "init_point": init_point,
    }