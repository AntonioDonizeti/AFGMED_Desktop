from projetoafgmed import database
from projetoafgmed.models import (
    Carrinho,
    Entrega,
    ItemCarrinho,
    ItemPedido,
    Pedido,
    PerfilUsuario,
    Produto,
)


class ErroCompra(Exception):
    """Erro relacionado às regras do carrinho e do pedido."""


def obter_carrinho_ativo(usuario_id):
    return (
        Carrinho.query.filter_by(
            id_usuario=usuario_id,
            status="ativo",
        )
        .order_by(Carrinho.id.desc())
        .first()
    )


def adicionar_produto(usuario_id, produto_id):
    try:
        produto = database.session.get(
            Produto,
            produto_id,
        )

        if produto is None:
            raise ErroCompra(
                "Produto não encontrado."
            )

        if not produto.ativo:
            raise ErroCompra(
                "Produto indisponível."
            )

        if (produto.estoque or 0) <= 0:
            raise ErroCompra(
                "Produto sem estoque."
            )

        carrinho = obter_carrinho_ativo(
            usuario_id
        )

        if carrinho is None:
            carrinho = Carrinho(
                id_usuario=usuario_id,
                status="ativo",
                ativo=True,
                status_pagamento="pendente",
            )

            database.session.add(carrinho)
            database.session.flush()

        item = ItemCarrinho.query.filter_by(
            id_carrinho=carrinho.id,
            id_produto=produto.id,
        ).first()

        if item is None:
            item = ItemCarrinho(
                id_carrinho=carrinho.id,
                id_produto=produto.id,
                quantidade=1,
                preco_unitario=produto.preco,
            )

            database.session.add(item)

        else:
            item.quantidade += 1

        produto.estoque -= 1

        database.session.commit()

        return (
            f"{produto.nome} adicionado "
            "ao carrinho."
        )

    except Exception:
        database.session.rollback()
        raise


def alterar_quantidade(
    usuario_id,
    item_id,
    acao,
):
    try:
        item = database.session.get(
            ItemCarrinho,
            item_id,
        )

        if item is None:
            raise ErroCompra(
                "Item não encontrado."
            )

        carrinho = database.session.get(
            Carrinho,
            item.id_carrinho,
        )

        if (
            carrinho is None
            or carrinho.id_usuario != usuario_id
        ):
            raise ErroCompra(
                "Você não pode alterar este item."
            )

        if carrinho.status != "ativo":
            raise ErroCompra(
                "Este carrinho já foi finalizado."
            )

        produto = database.session.get(
            Produto,
            item.id_produto,
        )

        if produto is None:
            raise ErroCompra(
                "O produto não existe mais."
            )

        if acao == "aumentar":
            if (produto.estoque or 0) <= 0:
                raise ErroCompra(
                    "Produto sem estoque."
                )

            item.quantidade += 1
            produto.estoque -= 1

        elif acao == "diminuir":
            if item.quantidade > 1:
                item.quantidade -= 1
                produto.estoque += 1

            else:
                produto.estoque += 1
                database.session.delete(item)

        else:
            raise ErroCompra(
                "Ação inválida."
            )

        database.session.commit()

    except Exception:
        database.session.rollback()
        raise


def remover_item(
    usuario_id,
    item_id,
):
    try:
        item = database.session.get(
            ItemCarrinho,
            item_id,
        )

        if item is None:
            raise ErroCompra(
                "Item não encontrado."
            )

        carrinho = database.session.get(
            Carrinho,
            item.id_carrinho,
        )

        if (
            carrinho is None
            or carrinho.id_usuario != usuario_id
        ):
            raise ErroCompra(
                "Você não pode remover este item."
            )

        if carrinho.status != "ativo":
            raise ErroCompra(
                "Este carrinho já foi finalizado."
            )

        produto = database.session.get(
            Produto,
            item.id_produto,
        )

        if produto is not None:
            produto.estoque += item.quantidade

        database.session.delete(item)
        database.session.commit()

    except Exception:
        database.session.rollback()
        raise


def finalizar_pedido_local(
    usuario_id,
    endereco,
    cidade,
    estado,
    cep,
):
    endereco = (endereco or "").strip()
    cidade = (cidade or "").strip()
    estado = (estado or "").strip().upper()
    cep = (cep or "").strip()

    if not all(
        [
            endereco,
            cidade,
            estado,
            cep,
        ]
    ):
        raise ErroCompra(
            "Preencha todos os dados de entrega."
        )

    try:
        carrinho = obter_carrinho_ativo(
            usuario_id
        )

        if (
            carrinho is None
            or not carrinho.itens
        ):
            raise ErroCompra(
                "Seu carrinho está vazio."
            )

        total_produtos = sum(
            item.quantidade
            * item.preco_unitario
            for item in carrinho.itens
        )

        total_entrega = 0.0
        total = total_produtos + total_entrega

        perfil = PerfilUsuario.query.filter_by(
            id_usuario=usuario_id
        ).first()

        if perfil is None:
            perfil = PerfilUsuario(
                id_usuario=usuario_id
            )

            database.session.add(perfil)

        perfil.endereco = endereco
        perfil.cidade = cidade
        perfil.estado = estado
        perfil.cep = cep

        entrega = Entrega.query.filter_by(
            id_carrinho=carrinho.id
        ).first()

        if entrega is None:
            entrega = Entrega(
                id_carrinho=carrinho.id,
                endereco=endereco,
                cidade=cidade,
                estado=estado,
                cep=cep,
            )

            database.session.add(entrega)

        else:
            entrega.endereco = endereco
            entrega.cidade = cidade
            entrega.estado = estado
            entrega.cep = cep

        pedido = Pedido.query.filter_by(
            id_carrinho=carrinho.id
        ).first()

        if pedido is None:
            pedido = Pedido(
                id_usuario=usuario_id,
                id_carrinho=carrinho.id,
                endereco=endereco,
                cidade=cidade,
                estado=estado,
                cep=cep,
                total_produtos=total_produtos,
                total_entrega=total_entrega,
                total=total,
                status="aguardando_pagamento",
                status_pagamento="pending",
            )

            database.session.add(pedido)
            database.session.flush()

        else:
            pedido.endereco = endereco
            pedido.cidade = cidade
            pedido.estado = estado
            pedido.cep = cep

            pedido.total_produtos = (
                total_produtos
            )

            pedido.total_entrega = (
                total_entrega
            )

            pedido.total = total

            pedido.status = (
                "aguardando_pagamento"
            )

            pedido.status_pagamento = (
                "pending"
            )

        ItemPedido.query.filter_by(
            id_pedido=pedido.id
        ).delete(
            synchronize_session=False
        )

        database.session.flush()

        for item in carrinho.itens:
            produto = database.session.get(
                Produto,
                item.id_produto,
            )

            item_pedido = ItemPedido(
                id_pedido=pedido.id,
                id_produto=(
                    produto.id
                    if produto
                    else None
                ),
                nome_produto=(
                    produto.nome
                    if produto
                    else "Produto removido"
                ),
                descricao_produto=(
                    produto.descricao
                    if produto
                    else None
                ),
                foto_produto=(
                    produto.foto
                    if produto
                    else None
                ),
                quantidade=item.quantidade,
                preco_unitario=(
                    item.preco_unitario
                ),
                subtotal=(
                    item.quantidade
                    * item.preco_unitario
                ),
            )

            database.session.add(
                item_pedido
            )

        carrinho.status = (
            "aguardando_pagamento"
        )

        carrinho.status_pagamento = (
            "pending"
        )

        carrinho.mercado_pago_preference_id = None
        carrinho.mercado_pago_payment_id = None
        carrinho.mercado_pago_init_point = None

        pedido.mercado_pago_preference_id = None
        pedido.mercado_pago_payment_id = None
        pedido.mercado_pago_init_point = None

        database.session.commit()

        return pedido.id

    except Exception:
        database.session.rollback()
        raise