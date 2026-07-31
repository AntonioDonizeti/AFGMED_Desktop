import os

from PySide6.QtCore import Qt
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
from projetoafgmed.models import Pedido
from projetoafgmed.servicos_pagamento import (
    ErroPagamento,
    sincronizar_pagamento_pedido,
)
from .tela_pagamento import DialogPagamentoMercadoPago


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


def status_visual(pedido_status, pagamento_status):
    pedido = (pedido_status or "").lower()
    pagamento = (pagamento_status or "").lower()

    if pedido == "pago_pendencia_estoque":
        return {
            "texto": "Pagamento aprovado — estoque pendente",
            "tipo": "analise",
            "descricao": "O pagamento foi confirmado e o pedido exige revisão de estoque.",
        }

    if pedido == "pago" or pagamento == "approved":
        return {
            "texto": "Pagamento aprovado",
            "tipo": "aprovado",
            "descricao": "Pedido confirmado e em preparação.",
        }

    if pedido == "falha" or pagamento in {
        "rejected",
        "cancelled",
        "refunded",
    }:
        return {
            "texto": "Pagamento não aprovado",
            "tipo": "falha",
            "descricao": "Você pode tentar realizar o pagamento novamente.",
        }

    return {
        "texto": "Aguardando pagamento",
        "tipo": "pendente",
        "descricao": "O pagamento ainda não foi confirmado.",
    }


class TelaMeusPedidos(QWidget):
    def __init__(self, usuario):
        super().__init__()

        self.usuario_id = usuario.id
        self.setObjectName("paginaPedidos")
        aplicar_estilo(self, "pedidos.qss")

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(26, 22, 26, 26)
        layout_principal.setSpacing(18)

        cabecalho = QHBoxLayout()
        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(2)

        titulo = QLabel("Meus pedidos")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Acompanhe pagamentos, produtos, endereço e total de cada compra."
        )
        subtitulo.setObjectName("subtituloPagina")

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

        layout_principal.addLayout(cabecalho)
        layout_principal.addWidget(self.scroll)

        self.recarregar()

    def recarregar(self):
        container = QWidget()
        lista = QVBoxLayout(container)
        lista.setContentsMargins(0, 0, 0, 10)
        lista.setSpacing(14)

        try:
            with app.app_context():
                pedidos_banco = (
                    Pedido.query.filter_by(id_usuario=self.usuario_id)
                    .order_by(Pedido.data_criacao.desc())
                    .all()
                )

                pedidos = []

                for pedido in pedidos_banco:
                    itens = []
                    for item in pedido.itens:
                        itens.append(
                            {
                                "nome": item.nome_produto or "Produto",
                                "foto": item.foto_produto or "",
                                "quantidade": int(item.quantidade or 0),
                                "preco": float(item.preco_unitario or 0),
                                "subtotal": float(item.subtotal or 0),
                            }
                        )

                    pedidos.append(
                        {
                            "id": pedido.id,
                            "status": pedido.status or "",
                            "status_pagamento": pedido.status_pagamento or "",
                            "total_produtos": float(pedido.total_produtos or 0),
                            "total_entrega": float(pedido.total_entrega or 0),
                            "total": float(pedido.total or 0),
                            "endereco": pedido.endereco or "",
                            "cidade": pedido.cidade or "",
                            "estado": pedido.estado or "",
                            "cep": pedido.cep or "",
                            "data_criacao": pedido.data_criacao,
                            "itens": itens,
                        }
                    )
        except Exception as erro:
            print("ERRO AO CARREGAR PEDIDOS:", erro)
            mensagem = QLabel("Não foi possível carregar os pedidos.")
            mensagem.setObjectName("pedidosVazio")
            mensagem.setAlignment(Qt.AlignCenter)
            lista.addWidget(mensagem)
            lista.addStretch()
            self.scroll.setWidget(container)
            return

        if not pedidos:
            mensagem = QLabel(
                "Você ainda não realizou nenhum pedido."
            )
            mensagem.setObjectName("pedidosVazio")
            mensagem.setAlignment(Qt.AlignCenter)
            lista.addWidget(mensagem)
            lista.addStretch()
            self.scroll.setWidget(container)
            return

        for pedido in pedidos:
            lista.addWidget(self.criar_card_pedido(pedido))

        lista.addStretch()
        self.scroll.setWidget(container)

    def criar_card_pedido(self, pedido):
        card = QFrame()
        card.setObjectName("pedidoCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(11)

        cabecalho = QHBoxLayout()

        area_numero = QVBoxLayout()
        area_numero.setSpacing(2)

        numero = QLabel(f"Pedido nº {pedido['id']}")
        numero.setObjectName("numeroPedido")

        data_texto = (
            pedido["data_criacao"].strftime("%d/%m/%Y às %H:%M")
            if pedido["data_criacao"]
            else "Data não informada"
        )

        data = QLabel(data_texto)
        data.setObjectName("dataPedido")

        area_numero.addWidget(numero)
        area_numero.addWidget(data)

        status_info = status_visual(
            pedido["status"],
            pedido["status_pagamento"],
        )

        status = QLabel(status_info["texto"])
        status.setObjectName("statusPedido")
        status.setProperty("tipoStatus", status_info["tipo"])
        status.setAlignment(Qt.AlignCenter)

        cabecalho.addLayout(area_numero)
        cabecalho.addStretch()
        cabecalho.addWidget(status)

        descricao_status = QLabel(status_info["descricao"])
        descricao_status.setObjectName("enderecoPedido")
        descricao_status.setWordWrap(True)

        produtos_titulo = QLabel("Produtos")
        produtos_titulo.setStyleSheet(
            "color: #10263b; font-weight: 750; font-size: 14px;"
        )

        itens_layout = QVBoxLayout()
        itens_layout.setSpacing(7)

        for item in pedido["itens"]:
            itens_layout.addWidget(self.criar_linha_produto(item))

        endereco = QLabel(
            "Entrega: "
            f"{pedido['endereco']}, {pedido['cidade']} - "
            f"{pedido['estado']}, CEP {pedido['cep']}"
        )
        endereco.setObjectName("enderecoPedido")
        endereco.setWordWrap(True)

        rodape = QHBoxLayout()

        area_totais = QVBoxLayout()
        area_totais.setSpacing(2)

        produtos_total = QLabel(
            f"Produtos: {formatar_real(pedido['total_produtos'])}"
        )
        produtos_total.setObjectName("enderecoPedido")

        entrega_total = QLabel(
            f"Entrega: {formatar_real(pedido['total_entrega'])}"
        )
        entrega_total.setObjectName("enderecoPedido")

        total = QLabel(f"Total: {formatar_real(pedido['total'])}")
        total.setObjectName("totalPedido")

        area_totais.addWidget(produtos_total)
        area_totais.addWidget(entrega_total)
        area_totais.addWidget(total)

        botoes = QHBoxLayout()
        tipo_status = status_info["tipo"]

        if tipo_status in {"pendente", "falha"}:
            pagar = QPushButton(
                "Continuar pagamento"
                if tipo_status == "pendente"
                else "Tentar pagar novamente"
            )
            pagar.setObjectName("botaoSucesso")
            pagar.clicked.connect(
                lambda checked=False, pedido_id=pedido["id"]: (
                    self.abrir_pagamento(pedido_id)
                )
            )
            botoes.addWidget(pagar)

            verificar = QPushButton("Verificar pagamento")
            verificar.clicked.connect(
                lambda checked=False, pedido_id=pedido["id"]: (
                    self.verificar_pagamento(pedido_id)
                )
            )
            botoes.addWidget(verificar)

        rodape.addLayout(area_totais)
        rodape.addStretch()
        rodape.addLayout(botoes)

        layout.addLayout(cabecalho)
        layout.addWidget(descricao_status)
        layout.addWidget(produtos_titulo)
        layout.addLayout(itens_layout)
        layout.addWidget(endereco)
        layout.addLayout(rodape)

        return card

    def criar_linha_produto(self, item):
        linha = QFrame()
        linha.setObjectName("linhaProdutoPedido")

        layout = QHBoxLayout(linha)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        foto = QLabel()
        foto.setFixedSize(58, 58)
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
                        50,
                        50,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
            else:
                foto.setText("—")
        else:
            foto.setText("—")

        dados = QVBoxLayout()
        dados.setSpacing(2)

        nome = QLabel(item["nome"])
        nome.setObjectName("nomeProdutoPedido")

        detalhe = QLabel(
            f"{item['quantidade']}x de {formatar_real(item['preco'])}"
        )
        detalhe.setObjectName("detalheProdutoPedido")

        dados.addWidget(nome)
        dados.addWidget(detalhe)

        subtotal = QLabel(formatar_real(item["subtotal"]))
        subtotal.setObjectName("subtotalProdutoPedido")
        subtotal.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(foto)
        layout.addLayout(dados, 1)
        layout.addWidget(subtotal)

        return linha

    def abrir_pagamento(self, pedido_id):
        try:
            dialogo = DialogPagamentoMercadoPago(
                pedido_id=pedido_id,
                parent=self,
            )
            dialogo.exec()
            self.recarregar()
        except Exception as erro:
            print("ERRO AO ABRIR PAGAMENTO DO PEDIDO:", erro)
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível abrir o pagamento.",
            )

    def verificar_pagamento(self, pedido_id):
        try:
            with app.app_context():
                pagamento = sincronizar_pagamento_pedido(pedido_id)

            status = (pagamento.get("status") or "pending").lower()

            if status == "approved":
                QMessageBox.information(
                    self,
                    "Pagamento aprovado",
                    "Pagamento confirmado e estoque atualizado.",
                )
            elif status in {"rejected", "cancelled"}:
                QMessageBox.warning(
                    self,
                    "Pagamento não aprovado",
                    "O pagamento foi recusado ou cancelado.",
                )
            else:
                QMessageBox.information(
                    self,
                    "Pagamento pendente",
                    "O pagamento ainda não foi confirmado.",
                )

            self.recarregar()

        except ErroPagamento as erro:
            QMessageBox.warning(self, "Pagamento", str(erro))
        except Exception as erro:
            print("ERRO AO VERIFICAR PEDIDO:", erro)
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível verificar o pagamento.",
            )


def tela_meus_pedidos(usuario):
    return TelaMeusPedidos(usuario)
