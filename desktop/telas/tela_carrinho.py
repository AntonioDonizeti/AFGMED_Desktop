from PySide6.QtCore import Qt, Signal
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

from projetoafgmed import app
from projetoafgmed.models import Carrinho

from projetoafgmed.servicos_compras import (
    ErroCompra,
    alterar_quantidade,
    remover_item,
)

from .tela_finalizar_pedido import (
    DialogFinalizarPedido,
)


class TelaCarrinho(QWidget):
    estoque_alterado = Signal()

    def __init__(self, usuario):
        super().__init__()

        self.usuario_id = usuario.id

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        layout.setSpacing(12)

        cabecalho = QHBoxLayout()

        titulo = QLabel(
            "Meu carrinho"
        )

        titulo.setStyleSheet(
            "font-size: 22px; "
            "font-weight: bold;"
        )

        atualizar = QPushButton(
            "Atualizar"
        )

        atualizar.clicked.connect(
            self.recarregar
        )

        cabecalho.addWidget(titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(atualizar)

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )

        self.scroll.setFrameShape(
            QFrame.NoFrame
        )

        rodape = QHBoxLayout()

        self.total_label = QLabel(
            "Total: R$ 0,00"
        )

        self.total_label.setStyleSheet(
            "font-size: 20px; "
            "font-weight: bold;"
        )

        self.finalizar = QPushButton(
            "Finalizar pedido"
        )

        self.finalizar.setMinimumHeight(
            42
        )

        self.finalizar.clicked.connect(
            self.abrir_finalizacao
        )

        rodape.addWidget(
            self.total_label
        )

        rodape.addStretch()

        rodape.addWidget(
            self.finalizar
        )

        layout.addLayout(cabecalho)
        layout.addWidget(self.scroll)
        layout.addLayout(rodape)

        self.recarregar()

    def recarregar(self):
        container = QWidget()
        lista = QVBoxLayout(container)
        lista.setSpacing(12)

        with app.app_context():
            carrinho = (
                Carrinho.query.filter_by(
                    id_usuario=self.usuario_id,
                    status="ativo",
                )
                .order_by(
                    Carrinho.id.desc()
                )
                .first()
            )

            if carrinho is None:
                itens = []
                total = 0.0

            else:
                itens = [
                    {
                        "id": item.id,
                        "produto": (
                            item.produto.nome
                        ),
                        "quantidade": (
                            item.quantidade
                        ),
                        "preco_unitario": float(
                            item.preco_unitario
                        ),
                        "subtotal": float(
                            item.quantidade
                            * item.preco_unitario
                        ),
                        "estoque": (
                            item.produto.estoque
                        ),
                    }
                    for item in carrinho.itens
                ]

                total = sum(
                    item["subtotal"]
                    for item in itens
                )

        if not itens:
            vazio = QLabel(
                "Seu carrinho está vazio."
            )

            vazio.setAlignment(
                Qt.AlignCenter
            )

            vazio.setStyleSheet(
                "font-size: 16px; "
                "color: #666;"
            )

            lista.addWidget(vazio)
            lista.addStretch()

            self.finalizar.setEnabled(
                False
            )

        else:
            self.finalizar.setEnabled(
                True
            )

            for item in itens:
                card = QFrame()

                card.setFrameShape(
                    QFrame.StyledPanel
                )

                card_layout = QHBoxLayout(
                    card
                )

                card_layout.setContentsMargins(
                    16,
                    14,
                    16,
                    14,
                )

                dados = QVBoxLayout()

                nome = QLabel(
                    item["produto"]
                )

                nome.setStyleSheet(
                    "font-size: 17px; "
                    "font-weight: bold;"
                )

                preco = QLabel(
                    "Preço unitário: "
                    f"R$ {item['preco_unitario']:.2f}"
                )

                subtotal = QLabel(
                    "Subtotal: "
                    f"R$ {item['subtotal']:.2f}"
                )

                estoque = QLabel(
                    "Estoque disponível: "
                    f"{item['estoque']}"
                )

                dados.addWidget(nome)
                dados.addWidget(preco)
                dados.addWidget(subtotal)
                dados.addWidget(estoque)

                controles = QHBoxLayout()

                diminuir = QPushButton("−")
                quantidade = QLabel(
                    str(item["quantidade"])
                )

                aumentar = QPushButton("+")
                remover = QPushButton(
                    "Remover"
                )

                diminuir.setFixedSize(
                    38,
                    38,
                )

                aumentar.setFixedSize(
                    38,
                    38,
                )

                quantidade.setAlignment(
                    Qt.AlignCenter
                )

                quantidade.setMinimumWidth(
                    35
                )

                diminuir.clicked.connect(
                    lambda checked=False,
                    item_id=item["id"]:
                    self.mudar_quantidade(
                        item_id,
                        "diminuir",
                    )
                )

                aumentar.clicked.connect(
                    lambda checked=False,
                    item_id=item["id"]:
                    self.mudar_quantidade(
                        item_id,
                        "aumentar",
                    )
                )

                remover.clicked.connect(
                    lambda checked=False,
                    item_id=item["id"]:
                    self.remover(item_id)
                )

                controles.addWidget(diminuir)
                controles.addWidget(
                    quantidade
                )
                controles.addWidget(aumentar)
                controles.addSpacing(12)
                controles.addWidget(remover)

                card_layout.addLayout(
                    dados,
                    1,
                )

                card_layout.addLayout(
                    controles
                )

                lista.addWidget(card)

            lista.addStretch()

        total_formatado = (
            f"{total:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        self.total_label.setText(
            f"Total: R$ {total_formatado}"
        )

        self.scroll.setWidget(
            container
        )

    def mudar_quantidade(
        self,
        item_id,
        acao,
    ):
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
            QMessageBox.warning(
                self,
                "Atenção",
                str(erro),
            )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível alterar "
                    f"o item.\n\n{erro}"
                ),
            )

    def remover(self, item_id):
        resposta = QMessageBox.question(
            self,
            "Remover produto",
            (
                "Deseja remover este produto "
                "do carrinho?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
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
            QMessageBox.warning(
                self,
                "Atenção",
                str(erro),
            )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível remover "
                    f"o item.\n\n{erro}"
                ),
            )

    def abrir_finalizacao(self):
        dialogo = DialogFinalizarPedido(
            usuario_id=self.usuario_id,
            parent=self,
        )

        if dialogo.exec():
            self.recarregar()