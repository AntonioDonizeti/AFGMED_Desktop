from flask_login import current_user

from projetoafgmed import app
from projetoafgmed.models import Carrinho


def contexto_carrinho_vazio():
    return {
        "carrinho": None,
        "itens_carrinho": [],
        "total_carrinho": 0,
        "quantidade_carrinho": 0,
    }


@app.context_processor
def carrinho_global():
    if not current_user.is_authenticated:
        return contexto_carrinho_vazio()

    # Médico comum não possui acesso a produtos, carrinho ou pedidos.
    if (
        getattr(current_user, "is_medico", False)
        and not getattr(current_user, "is_admin", False)
    ):
        return contexto_carrinho_vazio()

    carrinho = Carrinho.query.filter_by(
        id_usuario=current_user.id,
        status="ativo",
    ).first()

    itens = (
        carrinho.itens
        if carrinho
        else []
    )

    total = sum(
        (item.quantidade or 0)
        * (item.preco_unitario or 0)
        for item in itens
    )

    quantidade = sum(
        item.quantidade or 0
        for item in itens
    )

    return {
        "carrinho": carrinho,
        "itens_carrinho": itens,
        "total_carrinho": total,
        "quantidade_carrinho": quantidade,
    }