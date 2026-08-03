import mercadopago
from flask import current_app

from projetoafgmed import database
from projetoafgmed.models import Pedido
from projetoafgmed.servicos_compras import ErroCompra, baixar_estoque_pedido


class ErroPagamento(Exception):
    """Erro de integração ou sincronização de pagamento."""


def _sdk():
    access_token = (
        current_app.config.get("MERCADO_PAGO_ACCESS_TOKEN") or ""
    ).strip()

    if not access_token:
        raise ErroPagamento(
            "MERCADO_PAGO_ACCESS_TOKEN não configurado no .env."
        )

    return mercadopago.SDK(access_token)


def obter_pedido_por_referencia(external_reference):
    if not external_reference:
        return None

    referencia = str(external_reference)

    if referencia.startswith("pedido:"):
        try:
            return database.session.get(
                Pedido,
                int(referencia.replace("pedido:", "")),
            )
        except ValueError:
            return None

    try:
        carrinho_id = int(referencia)
    except ValueError:
        return None

    return Pedido.query.filter_by(id_carrinho=carrinho_id).first()


def criar_preferencia_mercado_pago(pedido_id):
    pedido = database.session.get(Pedido, pedido_id)

    if pedido is None:
        raise ErroPagamento("Pedido não encontrado.")

    if not pedido.itens:
        raise ErroPagamento("O pedido não possui itens.")

    if (
        pedido.status_pagamento in {"pending", "in_process"}
        and pedido.mercado_pago_preference_id
        and pedido.mercado_pago_init_point
    ):
        return {
            "id": pedido.mercado_pago_preference_id,
            "init_point": pedido.mercado_pago_init_point,
        }

    app_base_url = (current_app.config.get("APP_BASE_URL") or "").strip()

    if not app_base_url:
        raise ErroPagamento("APP_BASE_URL não configurada no .env.")

    app_base_url = app_base_url.rstrip("/")

    preference_data = {
        "items": [
            {
                "id": str(item.id_produto or item.id),
                "title": item.nome_produto,
                "description": item.descricao_produto or "Produto AFGMED",
                "quantity": int(item.quantidade),
                "currency_id": "BRL",
                "unit_price": float(item.preco_unitario),
            }
            for item in pedido.itens
        ],
        "external_reference": f"pedido:{pedido.id}",
        "back_urls": {
            "success": f"{app_base_url}/pagamento/sucesso",
            "failure": f"{app_base_url}/pagamento/falha",
            "pending": f"{app_base_url}/pagamento/pendente",
        },
        "auto_return": "approved",
        "notification_url": f"{app_base_url}/webhook/mercado-pago",
    }

    resposta = _sdk().preference().create(preference_data)
    status_http = resposta.get("status")
    dados = resposta.get("response", {})

    if status_http not in (200, 201):
        raise ErroPagamento(
            dados.get("message") or str(dados) or "Falha ao criar checkout."
        )

    preference_id = dados.get("id")
    init_point = dados.get("init_point") or dados.get("sandbox_init_point")

    if not preference_id or not init_point:
        raise ErroPagamento(
            "O Mercado Pago não retornou a URL do checkout."
        )

    pedido.mercado_pago_preference_id = preference_id
    pedido.mercado_pago_init_point = init_point
    pedido.status = "aguardando_pagamento"
    pedido.status_pagamento = "pending"

    if pedido.carrinho:
        pedido.carrinho.mercado_pago_preference_id = preference_id
        pedido.carrinho.mercado_pago_init_point = init_point
        pedido.carrinho.status = "aguardando_pagamento"
        pedido.carrinho.status_pagamento = "pending"

    database.session.commit()

    return {
        "id": preference_id,
        "init_point": init_point,
    }


def aplicar_pagamento_ao_pedido(pagamento):
    external_reference = pagamento.get("external_reference")
    pedido = obter_pedido_por_referencia(external_reference)

    if pedido is None:
        return pagamento

    status_novo = (pagamento.get("status") or "pending").lower()
    ja_aprovado = pedido.status == "pago"
    payment_id = pagamento.get("id")

    if payment_id:
        pedido.mercado_pago_payment_id = str(payment_id)

    pedido.status_pagamento = status_novo

    carrinho = pedido.carrinho

    if carrinho:
        if payment_id:
            carrinho.mercado_pago_payment_id = str(payment_id)
        carrinho.status_pagamento = status_novo

    if status_novo == "approved":
        if not ja_aprovado:
            try:
                baixar_estoque_pedido(pedido)
            except ErroCompra as erro:
                # O pagamento foi aprovado, então não podemos tratá-lo como
                # rejeitado. Registramos uma pendência operacional de estoque.
                pedido.status = "pago_pendencia_estoque"

                if carrinho:
                    carrinho.status = "finalizado"
                    carrinho.ativo = False

                database.session.commit()
                raise ErroPagamento(
                    "Pagamento aprovado, mas houve uma pendência de estoque: "
                    f"{erro}"
                ) from erro

        pedido.status = "pago"

        if carrinho:
            carrinho.status = "finalizado"
            carrinho.ativo = False

    elif status_novo in {"rejected", "cancelled", "refunded", "charged_back"}:
        pedido.status = "falha"
        pedido.mercado_pago_preference_id = None
        pedido.mercado_pago_payment_id = None
        pedido.mercado_pago_init_point = None

        if carrinho:
            carrinho.status = "ativo"
            carrinho.ativo = True
            carrinho.mercado_pago_preference_id = None
            carrinho.mercado_pago_payment_id = None
            carrinho.mercado_pago_init_point = None

    else:
        pedido.status = "aguardando_pagamento"

        if carrinho:
            carrinho.status = "aguardando_pagamento"

    database.session.commit()
    return pagamento


def sincronizar_pagamento_por_id(pagamento_id):
    resposta = _sdk().payment().get(str(pagamento_id))
    status_http = resposta.get("status")
    pagamento = resposta.get("response", {})

    if status_http != 200:
        raise ErroPagamento(
            pagamento.get("message") or str(pagamento) or "Pagamento não localizado."
        )

    return aplicar_pagamento_ao_pedido(pagamento)


def sincronizar_pagamento_pedido(pedido_id):
    pedido = database.session.get(Pedido, pedido_id)

    if pedido is None:
        raise ErroPagamento("Pedido não encontrado.")

    if pedido.mercado_pago_payment_id:
        return sincronizar_pagamento_por_id(
            pedido.mercado_pago_payment_id
        )

    resposta = _sdk().payment().search(
        {
            "external_reference": f"pedido:{pedido.id}",
            "sort": "date_created",
            "criteria": "desc",
        }
    )

    status_http = resposta.get("status")
    dados = resposta.get("response", {})

    if status_http != 200:
        raise ErroPagamento(
            dados.get("message") or str(dados) or "Falha ao consultar pagamento."
        )

    resultados = dados.get("results", [])

    if not resultados:
        return {
            "id": None,
            "status": pedido.status_pagamento or "pending",
            "external_reference": f"pedido:{pedido.id}",
        }

    return aplicar_pagamento_ao_pedido(resultados[0])
