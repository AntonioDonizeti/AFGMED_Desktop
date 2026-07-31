import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from desktop.estilos import aplicar_estilo
from projetoafgmed import app
from projetoafgmed.models import Carrinho
from projetoafgmed.servicos_compras import (
    ErroCompra,
    alterar_quantidade,
    remover_item,
)
from .tela_finalizar_pedido import DialogFinalizarPedido


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PASTA_PRODUTOS = os.path.join(
    BASE_DIR,
    "projetoafgmed",
    "static",
    "fotos_produtos",
)


def formatar_real(valor):
    texto = (
        f"{float(valor or 0):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    return f"R$ {texto}"


class TelaCarrinho(QWidget):
    estoque_alterado = Signal()

    def __init__(self, usuario):
        super().__init__()

        self.usuario_id = usuario.id
        self.setObjectName("paginaCarrinho")
        aplicar_estilo(self, "carrinho.qss")

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(26, 22, 26, 26)
        layout_principal.setSpacing(18)

        cabecalho = QHBoxLayout()
        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(2)

        titulo = QLabel("Meu carrinho")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Revise os itens antes de criar o pedido. O estoque só será baixado após o pagamento aprovado."
        )
        subtitulo.setObjectName("subtituloPagina")
        subtitulo.setWordWrap(True)

        area_titulo.addWidget(titulo)
        area_titulo.addWidget(subtitulo)

        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(self.recarregar)

        cabecalho.addLayout(area_titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(atualizar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        resumo = QFrame()
        resumo.setObjectName("resumoCarrinho")
        resumo_layout = QHBoxLayout(resumo)
        resumo_layout.setContentsMargins(20, 16, 20, 16)

        area_total = QVBoxLayout()
        area_total.setSpacing(1)

        rotulo_total = QLabel("Total do carrinho")
        rotulo_total.setObjectName("rotuloResumo")

        self.total_label = QLabel("R$ 0,00")
        self.total_label.setObjectName("totalCarrinho")

        area_total.addWidget(rotulo_total)
        area_total.addWidget(self.total_label)

        self.botao_finalizar = QPushButton("Finalizar pedido")
        self.botao_finalizar.setObjectName("botaoSucesso")
        self.botao_finalizar.setMinimumWidth(190)
        self.botao_finalizar.setMinimumHeight(46)
        self.botao_finalizar.clicked.connect(self.abrir_finalizacao)

        resumo_layout.addLayout(area_total)
        resumo_layout.addStretch()
        resumo_layout.addWidget(self.botao_finalizar)

        layout_principal.addLayout(cabecalho)
        layout_principal.addWidget(self.scroll, 1)
        layout_principal.addWidget(resumo)

        self.recarregar()

    def recarregar(self):
        container = QWidget()
        lista = QVBoxLayout(container)
        lista.setContentsMargins(0, 0, 0, 8)
        lista.setSpacing(12)

        try:
            with app.app_context():
                carrinho = (
                    Carrinho.query.filter_by(
                        id_usuario=self.usuario_id,
                        status="ativo",
                    )
                    .order_by(Carrinho.id.desc())
                    .first()
                )

                itens = []
                total = 0.0

                if carrinho:
                    for item in carrinho.itens:
                        produto = item.produto
                        quantidade = int(item.quantidade or 0)
                        preco = float(item.preco_unitario or 0)
                        subtotal = quantidade * preco
                        total += subtotal

                        itens.append(
                            {
                                "id": item.id,
                                "nome": produto.nome if produto else "Produto removido",
                                "foto": produto.foto if produto else "",
                                "quantidade": quantidade,
                                "preco": preco,
                                "subtotal": subtotal,
                                "estoque": int(produto.estoque or 0) if produto else 0,
                            }
                        )
        except Exception as erro:
            print("ERRO AO CARREGAR CARRINHO:", erro)
            mensagem = QLabel("Não foi possível carregar o carrinho.")
            mensagem.setObjectName("carrinhoVazio")
            mensagem.setAlignment(Qt.AlignCenter)
            lista.addWidget(mensagem)
            lista.addStretch()
            self.botao_finalizar.setEnabled(False)
            self.total_label.setText("R$ 0,00")
            self.scroll.setWidget(container)
            return

        if not itens:
            mensagem = QLabel(
                "Seu carrinho está vazio. Adicione produtos para continuar."
            )
            mensagem.setObjectName("carrinhoVazio")
            mensagem.setAlignment(Qt.AlignCenter)
            mensagem.setWordWrap(True)
            lista.addWidget(mensagem)
            lista.addStretch()
            self.botao_finalizar.setEnabled(False)
        else:
            self.botao_finalizar.setEnabled(True)

            for item in itens:
                lista.addWidget(self.criar_card_item(item))

            lista.addStretch()

        self.total_label.setText(formatar_real(total))
        self.scroll.setWidget(container)

    def criar_card_item(self, item):
        card = QFrame()
        card.setObjectName("itemCarrinhoCard")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(16)

        area_imagem = QFrame()
        area_imagem.setObjectName("imagemCarrinho")
        area_imagem.setFixedSize(90, 90)

        layout_imagem = QVBoxLayout(area_imagem)
        layout_imagem.setContentsMargins(6, 6, 6, 6)

        foto = QLabel()
        foto.setAlignment(Qt.AlignCenter)

        caminho = (
            os.path.join(PASTA_PRODUTOS, item["foto"])
            if item["foto"]
            else ""
        )

        if caminho and os.path.exists(caminho):
            imagem = QPixmap(caminho)
            if not imagem.isNull():
                foto.setPixmap(
                    imagem.scaled(
                        75,
                        75,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
            else:
                foto.setText("Sem foto")
        else:
            foto.setText("Sem foto")

        layout_imagem.addWidget(foto)

        informacoes = QVBoxLayout()
        informacoes.setSpacing(4)

        nome = QLabel(item["nome"])
        nome.setObjectName("nomeItemCarrinho")

        preco = QLabel(f"Preço unitário: {formatar_real(item['preco'])}")
        preco.setObjectName("detalheItemCarrinho")

        estoque = QLabel(f"Disponível no estoque: {item['estoque']}")
        estoque.setObjectName("detalheItemCarrinho")

        subtotal = QLabel(f"Subtotal: {formatar_real(item['subtotal'])}")
        subtotal.setObjectName("subtotalItemCarrinho")

        informacoes.addWidget(nome)
        informacoes.addWidget(preco)
        informacoes.addWidget(estoque)
        informacoes.addWidget(subtotal)

        controles = QHBoxLayout()
        controles.setSpacing(7)

        diminuir = QPushButton("−")
        diminuir.setObjectName("botaoQuantidade")

        quantidade = QLabel(str(item["quantidade"]))
        quantidade.setObjectName("quantidadeCarrinho")
        quantidade.setAlignment(Qt.AlignCenter)

        aumentar = QPushButton("+")
        aumentar.setObjectName("botaoQuantidade")

        remover = QPushButton("Remover")
        remover.setObjectName("botaoPerigo")

        diminuir.clicked.connect(
            lambda checked=False, item_id=item["id"]: self.mudar_quantidade(
                item_id,
                "diminuir",
            )
        )
        aumentar.clicked.connect(
            lambda checked=False, item_id=item["id"]: self.mudar_quantidade(
                item_id,
                "aumentar",
            )
        )
        remover.clicked.connect(
            lambda checked=False, item_id=item["id"]: self.confirmar_remocao(
                item_id
            )
        )

        controles.addWidget(diminuir)
        controles.addWidget(quantidade)
        controles.addWidget(aumentar)
        controles.addSpacing(8)
        controles.addWidget(remover)

        layout.addWidget(area_imagem)
        layout.addLayout(informacoes, 1)
        layout.addLayout(controles)

        return card

    def mudar_quantidade(self, item_id, acao):
        try:
            with app.app_context():
                alterar_quantidade(
                    usuario_id=self.usuario_id,
                    item_id=item_id,
                    acao=acao,
                )

            self.recarregar()
            self.estoque_alterado.emit()

        except ErroCompra as erro:
            QMessageBox.warning(self, "Carrinho", str(erro))
        except Exception as erro:
            print("ERRO AO ALTERAR CARRINHO:", erro)
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível alterar o item.",
            )

    def confirmar_remocao(self, item_id):
        resposta = QMessageBox.question(
            self,
            "Remover produto",
            "Deseja remover este produto do carrinho?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if resposta != QMessageBox.Yes:
            return

        try:
            with app.app_context():
                remover_item(
                    usuario_id=self.usuario_id,
                    item_id=item_id,
                )

            self.recarregar()
            self.estoque_alterado.emit()

        except ErroCompra as erro:
            QMessageBox.warning(self, "Carrinho", str(erro))
        except Exception as erro:
            print("ERRO AO REMOVER ITEM:", erro)
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível remover o produto.",
            )

    def abrir_finalizacao(self):
        dialogo = DialogFinalizarPedido(
            usuario_id=self.usuario_id,
            parent=self,
        )

        if dialogo.exec():
            self.recarregar()
            self.estoque_alterado.emit()
