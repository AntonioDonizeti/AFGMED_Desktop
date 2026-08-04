"""Regras compartilhadas de gerenciamento de produtos."""

from projetoafgmed import database
from projetoafgmed.models import ItemCarrinho, ItemPedido, Produto


class ErroProduto(ValueError):
    """Erro de validação relacionado ao gerenciamento de produtos."""


def excluir_produto(produto_id):
    """Exclui um produto sem apagar o histórico dos pedidos.

    Itens presentes em carrinhos são removidos. Nos pedidos já criados, apenas
    a referência ao cadastro é desassociada; nome, preço, quantidade e foto do
    item permanecem registrados no histórico.
    """
    try:
        produto = database.session.get(Produto, produto_id)

        if produto is None:
            raise ErroProduto("Produto não encontrado.")

        nome_produto = produto.nome or f"Produto nº {produto.id}"

        itens_carrinho_removidos = ItemCarrinho.query.filter_by(
            id_produto=produto.id
        ).delete(synchronize_session=False)

        itens_historico_preservados = ItemPedido.query.filter_by(
            id_produto=produto.id
        ).update(
            {ItemPedido.id_produto: None},
            synchronize_session=False,
        )

        database.session.delete(produto)
        database.session.commit()

        return {
            "nome": nome_produto,
            "itens_carrinho_removidos": itens_carrinho_removidos,
            "itens_historico_preservados": itens_historico_preservados,
        }

    except Exception:
        database.session.rollback()
        raise
