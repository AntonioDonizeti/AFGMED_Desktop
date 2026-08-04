from flask import (
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from projetoafgmed import app
from projetoafgmed.servicos_compras import (
    ErroCompra,
    adicionar_produto,
    alterar_quantidade,
    calcular_total_carrinho,
    montar_resposta_carrinho,
    obter_carrinho_ativo,
    remover_item as remover_item_carrinho,
    validar_estoque_carrinho,
)


@app.route("/adicionar-carrinho/<int:id_produto>", methods=["POST"])
@login_required
def adicionar_carrinho(id_produto):
    if getattr(current_user, "is_medico", False) and not getattr(
        current_user, "is_admin", False
    ):
        flash(
            "Usuários médicos não podem comprar produtos como pacientes.",
            "warning",
        )
        return redirect(url_for("homepage"))

    try:
        mensagem = adicionar_produto(
            usuario_id=current_user.id,
            produto_id=id_produto,
        )
        flash(mensagem, "success")

    except ErroCompra as erro:
        flash(str(erro), "warning")

    except Exception:
        current_app.logger.exception("Erro ao adicionar produto ao carrinho")
        flash(
            "Não foi possível adicionar o produto. Tente novamente.",
            "danger",
        )

    return redirect(request.referrer or url_for("produtos"))


@app.route("/atualizar-item/<int:id_item>", methods=["POST"])
@login_required
def atualizar_item(id_item):
    acao = request.form.get("acao")

    try:
        alterar_quantidade(
            usuario_id=current_user.id,
            item_id=id_item,
            acao=acao,
        )
        carrinho = obter_carrinho_ativo(current_user.id)
        return jsonify(montar_resposta_carrinho(carrinho))

    except ErroCompra as erro:
        return jsonify({
            "sucesso": False,
            "mensagem": str(erro),
        }), 400

    except Exception:
        current_app.logger.exception("Erro ao atualizar item do carrinho")
        return jsonify({
            "sucesso": False,
            "mensagem": "Não foi possível atualizar o item. Tente novamente.",
        }), 500


@app.route("/remover-item/<int:id_item>", methods=["POST"])
@login_required
def remover_item(id_item):
    try:
        remover_item_carrinho(
            usuario_id=current_user.id,
            item_id=id_item,
        )
        carrinho = obter_carrinho_ativo(current_user.id)
        return jsonify(montar_resposta_carrinho(carrinho))

    except ErroCompra as erro:
        return jsonify({
            "sucesso": False,
            "mensagem": str(erro),
        }), 400

    except Exception:
        current_app.logger.exception("Erro ao remover item do carrinho")
        return jsonify({
            "sucesso": False,
            "mensagem": "Não foi possível remover o item. Tente novamente.",
        }), 500


@app.route("/ver-carrinho")
@login_required
def ver_carrinho():
    carrinho = obter_carrinho_ativo(current_user.id)
    itens = carrinho.itens if carrinho else []

    return render_template(
        "_carrinho_lateral.html",
        itens_carrinho=itens,
        total_carrinho=calcular_total_carrinho(carrinho),
        carrinho=carrinho,
    )


@app.route("/finalizar-carrinho", methods=["POST"])
@login_required
def finalizar_carrinho():
    carrinho = obter_carrinho_ativo(current_user.id)

    try:
        validar_estoque_carrinho(carrinho)
    except ErroCompra as erro:
        flash(str(erro), "warning")
        return redirect(url_for("ver_carrinho"))

    except Exception:
        current_app.logger.exception("Erro ao validar carrinho")
        flash(
            "Não foi possível validar o carrinho. Tente novamente.",
            "danger",
        )
        return redirect(url_for("ver_carrinho"))

    return redirect(url_for("entrega", id_carrinho=carrinho.id))
