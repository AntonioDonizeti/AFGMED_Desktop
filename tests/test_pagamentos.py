"""Testes do pagamento sem realizar chamadas reais ao Mercado Pago."""

import pytest

from projetoafgmed import database
from projetoafgmed.models import Carrinho, Produto
from projetoafgmed.servicos_compras import (
    adicionar_produto,
    criar_ou_atualizar_pedido,
    obter_carrinho_ativo,
)
from projetoafgmed.servicos_pagamento import (
    ErroPagamento,
    aplicar_pagamento_ao_pedido,
    obter_pedido_por_referencia,
)


def criar_pedido(usuario, produto, quantidade=1):
    for _ in range(quantidade):
        adicionar_produto(usuario.id, produto.id)

    carrinho = obter_carrinho_ativo(usuario.id)
    pedido = criar_ou_atualizar_pedido(
        carrinho,
        endereco="Rua Pagamento, 1",
        cidade="São Paulo",
        estado="SP",
        cep="01000-000",
    )
    database.session.commit()
    return pedido


def test_localiza_pedido_pelas_referencias(criar_usuario, criar_produto):
    usuario = criar_usuario()
    produto = criar_produto()
    pedido = criar_pedido(usuario, produto)

    assert obter_pedido_por_referencia(f"pedido:{pedido.id}").id == pedido.id
    assert obter_pedido_por_referencia(str(pedido.id_carrinho)).id == pedido.id
    assert obter_pedido_por_referencia("invalida") is None


def test_pagamento_aprovado_baixa_estoque_e_finaliza_carrinho(
    criar_usuario,
    criar_produto,
):
    usuario = criar_usuario()
    produto = criar_produto(estoque=5)
    pedido = criar_pedido(usuario, produto, quantidade=2)

    aplicar_pagamento_ao_pedido(
        {
            "id": 987,
            "status": "approved",
            "external_reference": f"pedido:{pedido.id}",
        }
    )

    carrinho = database.session.get(Carrinho, pedido.id_carrinho)
    assert pedido.status == "pago"
    assert pedido.status_pagamento == "approved"
    assert pedido.mercado_pago_payment_id == "987"
    assert carrinho.status == "finalizado"
    assert carrinho.ativo is False
    assert database.session.get(Produto, produto.id).estoque == 3


def test_aprovacao_repetida_nao_baixa_estoque_duas_vezes(
    criar_usuario,
    criar_produto,
):
    usuario = criar_usuario()
    produto = criar_produto(estoque=5)
    pedido = criar_pedido(usuario, produto, quantidade=2)
    pagamento = {
        "id": 123,
        "status": "approved",
        "external_reference": f"pedido:{pedido.id}",
    }

    aplicar_pagamento_ao_pedido(pagamento)
    aplicar_pagamento_ao_pedido(pagamento)

    assert database.session.get(Produto, produto.id).estoque == 3


def test_pagamento_rejeitado_reabre_carrinho(criar_usuario, criar_produto):
    usuario = criar_usuario()
    produto = criar_produto(estoque=5)
    pedido = criar_pedido(usuario, produto)
    pedido.mercado_pago_preference_id = "pref-123"
    pedido.mercado_pago_init_point = "http://checkout.teste"
    pedido.carrinho.status = "aguardando_pagamento"
    pedido.carrinho.ativo = False
    database.session.commit()

    aplicar_pagamento_ao_pedido(
        {
            "id": 456,
            "status": "rejected",
            "external_reference": f"pedido:{pedido.id}",
        }
    )

    assert pedido.status == "falha"
    assert pedido.carrinho.status == "ativo"
    assert pedido.carrinho.ativo is True
    assert pedido.mercado_pago_preference_id is None
    assert pedido.mercado_pago_payment_id is None
    assert database.session.get(Produto, produto.id).estoque == 5


def test_aprovacao_sem_estoque_registra_pendencia(
    criar_usuario,
    criar_produto,
):
    usuario = criar_usuario()
    produto = criar_produto(estoque=2)
    pedido = criar_pedido(usuario, produto, quantidade=2)
    produto.estoque = 1
    database.session.commit()

    with pytest.raises(ErroPagamento, match="pendência de estoque"):
        aplicar_pagamento_ao_pedido(
            {
                "id": 789,
                "status": "approved",
                "external_reference": f"pedido:{pedido.id}",
            }
        )

    assert pedido.status == "pago_pendencia_estoque"
    assert pedido.carrinho.status == "finalizado"
    assert pedido.carrinho.ativo is False
    assert database.session.get(Produto, produto.id).estoque == 1
