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
from projetoafgmed.status import (
    CARRINHO_AGUARDANDO_PAGAMENTO,
    CARRINHO_ATIVO,
    PAGAMENTO_APROVADO,
    PAGAMENTO_PENDENTE,
    PAGAMENTOS_NAO_APROVADOS,
    PAGAMENTOS_PENDENTES,
    PEDIDO_AGUARDANDO_PAGAMENTO,
    PEDIDO_FALHA,
    PEDIDO_PAGO,
    normalizar_status_pagamento,
)


class ErroCompra(Exception):
    """Erro relacionado às regras do carrinho, estoque e pedido."""


def montar_resposta_carrinho(carrinho):
    itens = carrinho.itens if carrinho else []

    return {
        "sucesso": True,
        "carrinho_id": carrinho.id if carrinho else None,
        "quantidade": sum(int(item.quantidade or 0) for item in itens),
        "total": sum(
            int(item.quantidade or 0) * float(item.preco_unitario or 0)
            for item in itens
        ),
        "itens": [
            {
                "id": item.id,
                "produto": item.produto.nome if item.produto else "Produto removido",
                "quantidade": int(item.quantidade or 0),
                "preco_unitario": float(item.preco_unitario or 0),
                "subtotal": float(
                    int(item.quantidade or 0) * float(item.preco_unitario or 0)
                ),
                "estoque": int(item.produto.estoque or 0) if item.produto else 0,
            }
            for item in itens
        ],
    }


def calcular_total_carrinho(carrinho):
    if carrinho is None:
        return 0.0

    return sum(
        int(item.quantidade or 0) * float(item.preco_unitario or 0)
        for item in carrinho.itens
    )


def criar_ou_atualizar_pedido(carrinho, endereco, cidade, estado, cep):
    """Monta ou atualiza o pedido usando os itens atuais do carrinho."""
    if carrinho is None:
        raise ErroCompra("Carrinho não encontrado.")

    validar_estoque_carrinho(carrinho)

    total_produtos = calcular_total_carrinho(carrinho)
    total_entrega = 0.0
    total = total_produtos + total_entrega

    pedido = Pedido.query.filter_by(id_carrinho=carrinho.id).first()

    if pedido is None:
        pedido = Pedido(
            id_usuario=carrinho.id_usuario,
            id_carrinho=carrinho.id,
            status=PEDIDO_AGUARDANDO_PAGAMENTO,
            status_pagamento=PAGAMENTO_PENDENTE,
            endereco=endereco,
            cidade=cidade,
            estado=estado,
            cep=cep,
            total_produtos=total_produtos,
            total_entrega=total_entrega,
            total=total,
        )
        database.session.add(pedido)
        database.session.flush()
    else:
        pedido.endereco = endereco
        pedido.cidade = cidade
        pedido.estado = estado
        pedido.cep = cep
        pedido.total_produtos = total_produtos
        pedido.total_entrega = total_entrega
        pedido.total = total
        pedido.status = PEDIDO_AGUARDANDO_PAGAMENTO
        pedido.status_pagamento = PAGAMENTO_PENDENTE

    ItemPedido.query.filter_by(id_pedido=pedido.id).delete(
        synchronize_session=False
    )
    database.session.flush()

    for item in carrinho.itens:
        produto = database.session.get(Produto, item.id_produto)

        database.session.add(
            ItemPedido(
                id_pedido=pedido.id,
                id_produto=produto.id if produto else None,
                nome_produto=produto.nome if produto else "Produto removido",
                descricao_produto=produto.descricao if produto else None,
                foto_produto=produto.foto if produto else None,
                quantidade=int(item.quantidade or 0),
                preco_unitario=float(item.preco_unitario or 0),
                subtotal=(
                    int(item.quantidade or 0)
                    * float(item.preco_unitario or 0)
                ),
            )
        )

    return pedido


def status_visual_pedido(pedido):
    status_pagamento = normalizar_status_pagamento(
        pedido.status_pagamento
    )

    if pedido.status == PEDIDO_PAGO or status_pagamento == PAGAMENTO_APROVADO:
        return {
            "classe": "bg-success",
            "icone": "bi-check-circle",
            "texto": "Pagamento aprovado",
            "descricao": "Pedido confirmado e em preparação.",
        }

    if (
        pedido.status == PEDIDO_AGUARDANDO_PAGAMENTO
        or status_pagamento in PAGAMENTOS_PENDENTES
    ):
        return {
            "classe": "bg-warning text-dark",
            "icone": "bi-clock-history",
            "texto": "Aguardando pagamento",
            "descricao": "O pagamento ainda está pendente de confirmação.",
        }

    if (
        pedido.status in {PEDIDO_FALHA, "cancelado"}
        or status_pagamento in PAGAMENTOS_NAO_APROVADOS
    ):
        return {
            "classe": "bg-danger",
            "icone": "bi-x-circle",
            "texto": "Pagamento não aprovado",
            "descricao": "O pagamento não foi concluído.",
        }

    return {
        "classe": "bg-secondary",
        "icone": "bi-info-circle",
        "texto": "Status em análise",
        "descricao": "Estamos verificando o status do pedido.",
    }


def obter_carrinho_ativo(usuario_id):
    return (
        Carrinho.query.filter_by(
            id_usuario=usuario_id,
            status=CARRINHO_ATIVO,
        )
        .order_by(Carrinho.id.desc())
        .first()
    )


def validar_estoque_carrinho(carrinho):
    if carrinho is None or not carrinho.itens:
        raise ErroCompra("Seu carrinho está vazio.")

    if carrinho.status != CARRINHO_ATIVO or not carrinho.ativo:
        raise ErroCompra(
            "Este carrinho não está disponível para alterações ou finalização."
        )

    quantidades_por_produto = {}

    for item in carrinho.itens:
        produto = database.session.get(Produto, item.id_produto)
        quantidade = int(item.quantidade or 0)

        if produto is None or not produto.ativo:
            raise ErroCompra(
                f"O produto do item nº {item.id} não está mais disponível."
            )

        if quantidade <= 0:
            raise ErroCompra(
                f"A quantidade de {produto.nome} deve ser maior que zero."
            )

        dados_produto = quantidades_por_produto.setdefault(
            produto.id,
            {"produto": produto, "quantidade": 0},
        )
        dados_produto["quantidade"] += quantidade

    for dados in quantidades_por_produto.values():
        produto = dados["produto"]
        quantidade_total = dados["quantidade"]
        estoque_atual = int(produto.estoque or 0)

        if quantidade_total > estoque_atual:
            raise ErroCompra(
                f"Estoque insuficiente para {produto.nome}. "
                f"Solicitado: {quantidade_total}; disponível: {estoque_atual}."
            )

    return True


def adicionar_produto(usuario_id, produto_id):
    try:
        produto = database.session.get(Produto, produto_id)

        if produto is None:
            raise ErroCompra("Produto não encontrado.")

        if not produto.ativo:
            raise ErroCompra("Produto indisponível.")

        if int(produto.estoque or 0) <= 0:
            raise ErroCompra("Produto sem estoque.")

        carrinho = obter_carrinho_ativo(usuario_id)

        if carrinho is None:
            carrinho = Carrinho(
                id_usuario=usuario_id,
                status=CARRINHO_ATIVO,
                ativo=True,
                status_pagamento=PAGAMENTO_PENDENTE,
            )
            database.session.add(carrinho)
            database.session.flush()

        item = ItemCarrinho.query.filter_by(
            id_carrinho=carrinho.id,
            id_produto=produto.id,
        ).first()

        quantidade_atual = int(item.quantidade or 0) if item else 0

        if quantidade_atual + 1 > int(produto.estoque or 0):
            raise ErroCompra(
                f"Não há mais unidades disponíveis de {produto.nome}."
            )

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

        # O estoque NÃO é reduzido no carrinho.
        # A baixa ocorre apenas quando o pagamento for aprovado.
        database.session.flush()
        validar_estoque_carrinho(carrinho)
        database.session.commit()

        return f"{produto.nome} adicionado ao carrinho."

    except Exception:
        database.session.rollback()
        raise


def alterar_quantidade(usuario_id, item_id, acao):
    try:
        item = database.session.get(ItemCarrinho, item_id)

        if item is None:
            raise ErroCompra("Item não encontrado.")

        carrinho = database.session.get(Carrinho, item.id_carrinho)

        if carrinho is None or carrinho.id_usuario != usuario_id:
            raise ErroCompra("Você não pode alterar este item.")

        if carrinho.status != CARRINHO_ATIVO:
            raise ErroCompra("Este carrinho já foi enviado para pagamento.")

        produto = database.session.get(Produto, item.id_produto)

        if produto is None or not produto.ativo:
            raise ErroCompra("O produto não está mais disponível.")

        if acao == "aumentar":
            nova_quantidade = int(item.quantidade or 0) + 1

            if nova_quantidade > int(produto.estoque or 0):
                raise ErroCompra(
                    f"Estoque máximo disponível: {produto.estoque}."
                )

            item.quantidade = nova_quantidade

        elif acao == "diminuir":
            if int(item.quantidade or 0) > 1:
                item.quantidade -= 1
            else:
                database.session.delete(item)

        else:
            raise ErroCompra("Ação inválida.")

        database.session.flush()

        if carrinho.itens:
            validar_estoque_carrinho(carrinho)

        database.session.commit()

    except Exception:
        database.session.rollback()
        raise


def remover_item(usuario_id, item_id):
    try:
        item = database.session.get(ItemCarrinho, item_id)

        if item is None:
            raise ErroCompra("Item não encontrado.")

        carrinho = database.session.get(Carrinho, item.id_carrinho)

        if carrinho is None or carrinho.id_usuario != usuario_id:
            raise ErroCompra("Você não pode remover este item.")

        if carrinho.status != CARRINHO_ATIVO:
            raise ErroCompra("Este carrinho já foi enviado para pagamento.")

        # Não existe devolução de estoque porque o carrinho não reserva estoque.
        database.session.delete(item)
        database.session.commit()

    except Exception:
        database.session.rollback()
        raise


def baixar_estoque_pedido(pedido):
    """
    Faz a baixa física do estoque para um pedido pago.

    Esta função deve ser chamada somente na transição para pagamento aprovado.
    Ela primeiro valida todos os itens e só depois altera as quantidades, evitando
    uma baixa parcial em caso de falta de estoque.
    """
    if pedido is None or not pedido.itens:
        raise ErroCompra("O pedido não possui itens para atualizar o estoque.")

    itens_por_produto = {}

    for item in pedido.itens:
        produto = database.session.get(Produto, item.id_produto)

        if produto is None:
            raise ErroCompra(
                f"O produto '{item.nome_produto}' não existe mais no cadastro."
            )

        quantidade = int(item.quantidade or 0)
        if quantidade <= 0:
            raise ErroCompra(
                f"Quantidade inválida no produto '{item.nome_produto}'."
            )

        dados_produto = itens_por_produto.setdefault(
            produto.id,
            {"produto": produto, "quantidade": 0},
        )
        dados_produto["quantidade"] += quantidade

    itens_para_baixa = []

    for dados in itens_por_produto.values():
        produto = dados["produto"]
        quantidade = dados["quantidade"]
        estoque_atual = int(produto.estoque or 0)

        if estoque_atual < quantidade:
            raise ErroCompra(
                f"Estoque insuficiente para '{produto.nome}'. "
                f"Necessário: {quantidade}; disponível: {estoque_atual}."
            )

        itens_para_baixa.append((produto, quantidade))

    for produto, quantidade in itens_para_baixa:
        produto.estoque -= quantidade


def finalizar_pedido_local(usuario_id, endereco, cidade, estado, cep):
    endereco = (endereco or "").strip()
    cidade = (cidade or "").strip()
    estado = (estado or "").strip().upper()
    cep = (cep or "").strip()

    if not all([endereco, cidade, estado, cep]):
        raise ErroCompra("Preencha todos os dados de entrega.")

    try:
        carrinho = obter_carrinho_ativo(usuario_id)
        validar_estoque_carrinho(carrinho)

        perfil = PerfilUsuario.query.filter_by(
            id_usuario=usuario_id
        ).first()

        if perfil is None:
            perfil = PerfilUsuario(id_usuario=usuario_id)
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

        pedido = criar_ou_atualizar_pedido(
            carrinho=carrinho,
            endereco=endereco,
            cidade=cidade,
            estado=estado,
            cep=cep,
        )

        carrinho.status = CARRINHO_AGUARDANDO_PAGAMENTO
        carrinho.status_pagamento = PAGAMENTO_PENDENTE

        # O estoque continua intacto até o pagamento ser aprovado.
        database.session.commit()
        return pedido.id

    except Exception:
        database.session.rollback()
        raise
