from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
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
from projetoafgmed.models import Pedido

from .tela_pagamento import (
    DialogPagamentoMercadoPago,
)


def formatar_real(valor):
    valor = float(valor or 0)

    texto = (
        f"{valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"R$ {texto}"


def obter_status_visual(
    status_pedido,
    status_pagamento,
):
    status_pedido = (
        status_pedido or ""
    ).strip().lower()

    status_pagamento = (
        status_pagamento or ""
    ).strip().lower()

    if (
        status_pedido == "pago"
        or status_pagamento == "approved"
    ):
        return {
            "texto": "Pagamento aprovado",
            "descricao": (
                "Pedido confirmado e em preparação."
            ),
            "cor": "#176b39",
            "fundo": "#e7f5ec",
        }

    if (
        status_pedido
        == "aguardando_pagamento"
        or status_pagamento
        in [
            "pending",
            "pendente",
            "in_process",
        ]
    ):
        return {
            "texto": "Aguardando pagamento",
            "descricao": (
                "O pagamento ainda está "
                "pendente de confirmação."
            ),
            "cor": "#8a5a00",
            "fundo": "#fff4d6",
        }

    if (
        status_pedido
        in [
            "falha",
            "cancelado",
        ]
        or status_pagamento
        in [
            "rejected",
            "cancelled",
        ]
    ):
        return {
            "texto": "Pagamento não aprovado",
            "descricao": (
                "O pagamento não foi concluído."
            ),
            "cor": "#a10018",
            "fundo": "#fde8eb",
        }

    return {
        "texto": "Status em análise",
        "descricao": (
            "Estamos verificando o status "
            "do pedido."
        ),
        "cor": "#555555",
        "fundo": "#eeeeee",
    }


class TelaMeusPedidos(QWidget):
    def __init__(self, usuario):
        super().__init__()

        self.usuario = usuario
        self.usuario_id = usuario.id

        layout_principal = QVBoxLayout(self)

        layout_principal.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        layout_principal.setSpacing(12)

        # =====================================
        # CABEÇALHO
        # =====================================

        cabecalho = QHBoxLayout()

        titulo = QLabel(
            "Meus pedidos"
        )

        titulo.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
            }
            """
        )

        botao_atualizar = QPushButton(
            "Atualizar"
        )

        botao_atualizar.setMinimumHeight(
            36
        )

        botao_atualizar.clicked.connect(
            self.recarregar
        )

        cabecalho.addWidget(titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(
            botao_atualizar
        )

        # =====================================
        # ÁREA COM ROLAGEM
        # =====================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )

        self.scroll.setFrameShape(
            QFrame.NoFrame
        )

        layout_principal.addLayout(
            cabecalho
        )

        layout_principal.addWidget(
            self.scroll
        )

        self.recarregar()

    def recarregar(self):
        container = QWidget()

        lista_layout = QVBoxLayout(
            container
        )

        lista_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        lista_layout.setSpacing(14)

        try:
            with app.app_context():
                pedidos_banco = (
                    Pedido.query.filter_by(
                        id_usuario=self.usuario_id
                    )
                    .order_by(
                        Pedido.data_criacao.desc()
                    )
                    .all()
                )

                pedidos = []

                for pedido in pedidos_banco:
                    itens = []

                    for item in pedido.itens:
                        itens.append(
                            {
                                "nome": (
                                    item.nome_produto
                                    or "Produto"
                                ),
                                "quantidade": int(
                                    item.quantidade
                                    or 0
                                ),
                                "preco_unitario": float(
                                    item.preco_unitario
                                    or 0
                                ),
                                "subtotal": float(
                                    item.subtotal
                                    or 0
                                ),
                            }
                        )

                    pedidos.append(
                        {
                            "id": pedido.id,
                            "status": (
                                pedido.status or ""
                            ),
                            "status_pagamento": (
                                pedido.status_pagamento
                                or ""
                            ),
                            "total_produtos": float(
                                pedido.total_produtos
                                or 0
                            ),
                            "total_entrega": float(
                                pedido.total_entrega
                                or 0
                            ),
                            "total": float(
                                pedido.total or 0
                            ),
                            "endereco": (
                                pedido.endereco or ""
                            ),
                            "cidade": (
                                pedido.cidade or ""
                            ),
                            "estado": (
                                pedido.estado or ""
                            ),
                            "cep": (
                                pedido.cep or ""
                            ),
                            "data_criacao": (
                                pedido.data_criacao
                            ),
                            "init_point": (
                                pedido
                                .mercado_pago_init_point
                                or ""
                            ),
                            "itens": itens,
                        }
                    )

        except Exception as erro:
            mensagem = QLabel(
                "Não foi possível carregar "
                f"os pedidos.\n\n{erro}"
            )

            mensagem.setWordWrap(True)

            mensagem.setAlignment(
                Qt.AlignCenter
            )

            mensagem.setStyleSheet(
                "color: #b00020;"
            )

            lista_layout.addWidget(
                mensagem
            )

            lista_layout.addStretch()

            self.scroll.setWidget(
                container
            )

            return

        if not pedidos:
            mensagem = QLabel(
                "Você ainda não realizou "
                "nenhum pedido."
            )

            mensagem.setAlignment(
                Qt.AlignCenter
            )

            mensagem.setStyleSheet(
                """
                QLabel {
                    font-size: 16px;
                    color: #666666;
                    padding: 40px;
                }
                """
            )

            lista_layout.addWidget(
                mensagem
            )

            lista_layout.addStretch()

            self.scroll.setWidget(
                container
            )

            return

        for pedido in pedidos:
            card = self.criar_card_pedido(
                pedido
            )

            lista_layout.addWidget(card)

        lista_layout.addStretch()

        self.scroll.setWidget(
            container
        )

    def criar_card_pedido(
        self,
        pedido,
    ):
        card = QFrame()

        card.setFrameShape(
            QFrame.StyledPanel
        )

        card.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border: 1px solid #d8d8d8;
                border-radius: 8px;
            }

            QLabel {
                border: none;
            }
            """
        )

        layout_card = QVBoxLayout(card)

        layout_card.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        layout_card.setSpacing(10)

        # =====================================
        # CABEÇALHO DO PEDIDO
        # =====================================

        cabecalho = QHBoxLayout()

        numero = QLabel(
            f"Pedido nº {pedido['id']}"
        )

        numero.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        if pedido["data_criacao"]:
            data_texto = (
                pedido["data_criacao"]
                .strftime("%d/%m/%Y às %H:%M")
            )
        else:
            data_texto = (
                "Data não informada"
            )

        data = QLabel(data_texto)

        data.setStyleSheet(
            "color: #666666;"
        )

        cabecalho.addWidget(numero)
        cabecalho.addStretch()
        cabecalho.addWidget(data)

        # =====================================
        # STATUS
        # =====================================

        status_visual = obter_status_visual(
            pedido["status"],
            pedido["status_pagamento"],
        )

        status_container = QFrame()

        status_container.setStyleSheet(
            f"""
            QFrame {{
                background-color:
                    {status_visual["fundo"]};
                border: none;
                border-radius: 6px;
            }}

            QLabel {{
                border: none;
            }}
            """
        )

        status_layout = QVBoxLayout(
            status_container
        )

        status_layout.setContentsMargins(
            12,
            9,
            12,
            9,
        )

        status_layout.setSpacing(2)

        status_titulo = QLabel(
            status_visual["texto"]
        )

        status_titulo.setStyleSheet(
            f"""
            QLabel {{
                color: {status_visual["cor"]};
                font-weight: bold;
                font-size: 15px;
            }}
            """
        )

        status_descricao = QLabel(
            status_visual["descricao"]
        )

        status_descricao.setWordWrap(True)

        status_descricao.setStyleSheet(
            f"""
            QLabel {{
                color: {status_visual["cor"]};
            }}
            """
        )

        status_layout.addWidget(
            status_titulo
        )

        status_layout.addWidget(
            status_descricao
        )

        # =====================================
        # ITENS
        # =====================================

        itens_titulo = QLabel(
            "Produtos"
        )

        itens_titulo.setStyleSheet(
            "font-weight: bold;"
        )

        itens_layout = QVBoxLayout()

        itens_layout.setSpacing(4)

        for item in pedido["itens"]:
            linha_item = QHBoxLayout()

            nome_quantidade = QLabel(
                f"{item['quantidade']}x "
                f"{item['nome']}"
            )

            subtotal = QLabel(
                formatar_real(
                    item["subtotal"]
                )
            )

            subtotal.setAlignment(
                Qt.AlignRight
            )

            linha_item.addWidget(
                nome_quantidade,
                1,
            )

            linha_item.addWidget(
                subtotal
            )

            itens_layout.addLayout(
                linha_item
            )

        # =====================================
        # ENTREGA
        # =====================================

        endereco = QLabel(
            "Entrega: "
            f"{pedido['endereco']}, "
            f"{pedido['cidade']} - "
            f"{pedido['estado']}, "
            f"CEP {pedido['cep']}"
        )

        endereco.setWordWrap(True)

        endereco.setStyleSheet(
            "color: #555555;"
        )

        # =====================================
        # TOTAIS E BOTÕES
        # =====================================

        rodape = QHBoxLayout()

        totais = QVBoxLayout()

        produtos_label = QLabel(
            "Produtos: "
            f"{formatar_real(
                pedido['total_produtos']
            )}"
        )

        entrega_label = QLabel(
            "Entrega: "
            f"{formatar_real(
                pedido['total_entrega']
            )}"
        )

        total_label = QLabel(
            "Total: "
            f"{formatar_real(
                pedido['total']
            )}"
        )

        total_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        totais.addWidget(
            produtos_label
        )

        totais.addWidget(
            entrega_label
        )

        totais.addWidget(
            total_label
        )

        botoes = QHBoxLayout()

        status_pagamento = (
            pedido["status_pagamento"]
            or ""
        ).lower()

        status_pedido = (
            pedido["status"]
            or ""
        ).lower()

        pagamento_pendente = (
            status_pedido
            == "aguardando_pagamento"
            or status_pagamento
            in [
                "pending",
                "pendente",
                "in_process",
            ]
        )

        pagamento_falhou = (
            status_pedido
            in [
                "falha",
                "cancelado",
            ]
            or status_pagamento
            in [
                "rejected",
                "cancelled",
            ]
        )

        if pagamento_pendente:
            botao_pagar = QPushButton(
                "Continuar pagamento"
            )

            botao_pagar.setMinimumHeight(
                40
            )

            botao_pagar.clicked.connect(
                lambda checked=False,
                pedido_id=pedido["id"]:
                self.abrir_pagamento(
                    pedido_id
                )
            )

            botoes.addWidget(
                botao_pagar
            )

        elif pagamento_falhou:
            botao_tentar = QPushButton(
                "Tentar pagar novamente"
            )

            botao_tentar.setMinimumHeight(
                40
            )

            botao_tentar.clicked.connect(
                lambda checked=False,
                pedido_id=pedido["id"]:
                self.abrir_pagamento(
                    pedido_id
                )
            )

            botoes.addWidget(
                botao_tentar
            )

        elif pedido["init_point"]:
            botao_checkout = QPushButton(
                "Abrir comprovante/pagamento"
            )

            botao_checkout.setMinimumHeight(
                40
            )

            botao_checkout.clicked.connect(
                lambda checked=False,
                url=pedido["init_point"]:
                self.abrir_link(url)
            )

            botoes.addWidget(
                botao_checkout
            )

        rodape.addLayout(totais)

        rodape.addStretch()

        rodape.addLayout(botoes)

        # =====================================
        # MONTAGEM DO CARD
        # =====================================

        layout_card.addLayout(
            cabecalho
        )

        layout_card.addWidget(
            status_container
        )

        layout_card.addWidget(
            itens_titulo
        )

        layout_card.addLayout(
            itens_layout
        )

        layout_card.addWidget(
            endereco
        )

        layout_card.addLayout(
            rodape
        )

        return card

    def abrir_pagamento(
        self,
        pedido_id,
    ):
        try:
            dialogo = (
                DialogPagamentoMercadoPago(
                    pedido_id=pedido_id,
                    parent=self,
                )
            )

            dialogo.exec()

            # Consulta novamente o banco após
            # fechar a janela de pagamento.
            self.recarregar()

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível abrir "
                    "o pagamento."
                    f"\n\n{erro}"
                ),
            )

    def abrir_link(
        self,
        url,
    ):
        if not url:
            QMessageBox.warning(
                self,
                "Pagamento",
                (
                    "Este pedido não possui "
                    "um link de pagamento."
                ),
            )

            return

        abriu = QDesktopServices.openUrl(
            QUrl(url)
        )

        if not abriu:
            QMessageBox.warning(
                self,
                "Navegador",
                (
                    "Não foi possível abrir "
                    "o navegador."
                ),
            )


def tela_meus_pedidos(usuario):
    return TelaMeusPedidos(usuario)