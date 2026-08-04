"""Testes de carrinho, estoque, entrega e pedido do projeto original."""

import pytest

from projetoafgmed import database
from projetoafgmed.models import (
    Carrinho,
    Entrega,
    ItemCarrinho,
    ItemPedido,
    PerfilUsuario,
    Produto,
)
from projetoafgmed.servicos_compras import (
    ErroCompra,
    adicionar_produto,
    alterar_quantidade,
    baixar_estoque_pedido,
    calcular_total_carrinho,
    criar_ou_atualizar_pedido,
    finalizar_pedido_local,
    montar_resposta_carrinho,
    obter_carrinho_ativo,
    remover_item,
    validar_estoque_carrinho,
)


def adicionar_quantidade(usuario_id, produto_id, quantidade):
    for _ in range(quantidade):
        adicionar_produto(usuario_id, produto_id)


def test_adicionar_produto_cria_carrinho_sem_baixar_estoque(
    criar_usuario,
    criar_produto,
):
    usuario = criar_usuario()
    produto = criar_produto(nome="Dipirona", estoque=3, preco=12.5)

    mensagem = adicionar_produto(usuario.id, produto.id)
    carrinho = obter_carrinho_ativo(usuario.id)

    assert mensagem == "Dipirona adicionado ao carrinho."
    assert carrinho.status == "ativo"
    assert carrinho.ativo is True
    assert carrinho.itens[0].quantidade == 1
    assert database.session.get(Produto, produto.id).estoque == 3


def test_adicionar_mesmo_produto_aumenta_quantidade(criar_usuario, criar_produto):
    usuario = criar_usuario()
    produto = criar_produto(estoque=5)

    adicionar_quantidade(usuario.id, produto.id, 2)

    carrinho = obter_carrinho_ativo(usuario.id)
    assert len(carrinho.itens) == 1
    assert carrinho.itens[0].quantidade == 2


@pytest.mark.parametrize(
    ("estoque", "ativo", "mensagem"),
    [
        (0, True, "Produto sem estoque"),
        (5, False, "Produto indisponível"),
    ],
)
def test_nao_adiciona_produto_indisponivel(
    criar_usuario,
    criar_produto,
    estoque,
    ativo,
    mensagem,
):
    usuario = criar_usuario()
    produto = criar_produto(estoque=estoque, ativo=ativo)

    with pytest.raises(ErroCompra, match=mensagem):
        adicionar_produto(usuario.id, produto.id)

    assert obter_carrinho_ativo(usuario.id) is None


def test_nao_adiciona_acima_do_estoque(criar_usuario, criar_produto):
    usuario = criar_usuario()
    produto = criar_produto(estoque=1)
    adicionar_produto(usuario.id, produto.id)

    with pytest.raises(ErroCompra, match="Não há mais unidades"):
        adicionar_produto(usuario.id, produto.id)

    assert obter_carrinho_ativo(usuario.id).itens[0].quantidade == 1


def test_alterar_quantidade_respeita_estoque(criar_usuario, criar_produto):
    usuario = criar_usuario()
    produto = criar_produto(estoque=2)
    adicionar_produto(usuario.id, produto.id)
    item = obter_carrinho_ativo(usuario.id).itens[0]

    alterar_quantidade(usuario.id, item.id, "aumentar")
    assert database.session.get(ItemCarrinho, item.id).quantidade == 2

    with pytest.raises(ErroCompra, match="Estoque máximo"):
        alterar_quantidade(usuario.id, item.id, "aumentar")


def test_diminuir_quantidade_um_remove_item(criar_usuario, criar_produto):
    usuario = criar_usuario()
    produto = criar_produto()
    adicionar_produto(usuario.id, produto.id)
    item_id = obter_carrinho_ativo(usuario.id).itens[0].id

    alterar_quantidade(usuario.id, item_id, "diminuir")

    assert database.session.get(ItemCarrinho, item_id) is None


def test_usuario_nao_altera_item_de_outro_usuario(criar_usuario, criar_produto):
    dono = criar_usuario()
    intruso = criar_usuario()
    produto = criar_produto()
    adicionar_produto(dono.id, produto.id)
    item = obter_carrinho_ativo(dono.id).itens[0]

    with pytest.raises(ErroCompra, match="não pode alterar"):
        alterar_quantidade(intruso.id, item.id, "aumentar")


def test_remover_item_do_carrinho(criar_usuario, criar_produto):
    usuario = criar_usuario()
    produto = criar_produto()
    adicionar_produto(usuario.id, produto.id)
    item_id = obter_carrinho_ativo(usuario.id).itens[0].id

    remover_item(usuario.id, item_id)

    assert database.session.get(ItemCarrinho, item_id) is None


def test_carrinho_vazio_e_rejeitado():
    with pytest.raises(ErroCompra, match="carrinho está vazio"):
        validar_estoque_carrinho(None)


def test_validacao_detecta_quantidade_maior_que_estoque(
    criar_usuario,
    criar_produto,
):
    usuario = criar_usuario()
    produto = criar_produto(estoque=2)
    adicionar_produto(usuario.id, produto.id)
    carrinho = obter_carrinho_ativo(usuario.id)
    carrinho.itens[0].quantidade = 3
    database.session.commit()

    with pytest.raises(ErroCompra, match="Estoque insuficiente"):
        validar_estoque_carrinho(carrinho)


def test_total_e_resposta_do_carrinho(criar_usuario, criar_produto):
    usuario = criar_usuario()
    produto = criar_produto(nome="Vitamina", preco=7.5, estoque=5)
    adicionar_quantidade(usuario.id, produto.id, 2)
    carrinho = obter_carrinho_ativo(usuario.id)

    resposta = montar_resposta_carrinho(carrinho)

    assert calcular_total_carrinho(carrinho) == pytest.approx(15.0)
    assert resposta["quantidade"] == 2
    assert resposta["total"] == pytest.approx(15.0)
    assert resposta["itens"][0]["produto"] == "Vitamina"


def test_criar_pedido_copia_itens_e_total(criar_usuario, criar_produto):
    usuario = criar_usuario()
    produto = criar_produto(nome="Paracetamol", preco=8.0, estoque=5)
    adicionar_quantidade(usuario.id, produto.id, 2)
    carrinho = obter_carrinho_ativo(usuario.id)

    pedido = criar_ou_atualizar_pedido(
        carrinho,
        endereco="Rua Teste, 10",
        cidade="São Paulo",
        estado="SP",
        cep="01000-000",
    )
    database.session.commit()

    assert pedido.total_produtos == pytest.approx(16.0)
    assert pedido.total == pytest.approx(16.0)
    assert pedido.status == "aguardando_pagamento"
    assert ItemPedido.query.filter_by(id_pedido=pedido.id).count() == 1
    assert pedido.itens[0].quantidade == 2
    assert pedido.itens[0].nome_produto == "Paracetamol"


def test_finalizar_pedido_local_salva_entrega_e_perfil(
    criar_usuario,
    criar_produto,
):
    usuario = criar_usuario()
    produto = criar_produto()
    adicionar_produto(usuario.id, produto.id)

    pedido_id = finalizar_pedido_local(
        usuario.id,
        "Rua das Flores, 100",
        "Santo André",
        "sp",
        "09000-000",
    )

    carrinho = database.session.get(Carrinho, obter_carrinho_ativo(usuario.id).id) if obter_carrinho_ativo(usuario.id) else Carrinho.query.filter_by(id_usuario=usuario.id).one()
    perfil = PerfilUsuario.query.filter_by(id_usuario=usuario.id).one()
    entrega = Entrega.query.filter_by(id_carrinho=carrinho.id).one()

    assert pedido_id is not None
    assert carrinho.status == "aguardando_pagamento"
    assert perfil.estado == "SP"
    assert entrega.endereco == "Rua das Flores, 100"


def test_baixar_estoque_do_pedido(criar_usuario, criar_produto):
    usuario = criar_usuario()
    produto = criar_produto(estoque=5)
    adicionar_quantidade(usuario.id, produto.id, 2)
    pedido = criar_ou_atualizar_pedido(
        obter_carrinho_ativo(usuario.id),
        "Rua A",
        "São Paulo",
        "SP",
        "01000-000",
    )
    database.session.commit()

    baixar_estoque_pedido(pedido)
    database.session.commit()

    assert database.session.get(Produto, produto.id).estoque == 3


def test_baixa_nao_ocorre_quando_estoque_e_insuficiente(
    criar_usuario,
    criar_produto,
):
    usuario = criar_usuario()
    produto = criar_produto(estoque=2)
    adicionar_quantidade(usuario.id, produto.id, 2)
    pedido = criar_ou_atualizar_pedido(
        obter_carrinho_ativo(usuario.id),
        "Rua A",
        "São Paulo",
        "SP",
        "01000-000",
    )
    database.session.commit()
    produto.estoque = 1
    database.session.commit()

    with pytest.raises(ErroCompra, match="Estoque insuficiente"):
        baixar_estoque_pedido(pedido)

    assert database.session.get(Produto, produto.id).estoque == 1
