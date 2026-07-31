from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from desktop.estilos import aplicar_estilo
from projetoafgmed import app
from projetoafgmed.models import Pedido
from projetoafgmed.servicos_pagamento import (
    ErroPagamento,
    criar_preferencia_mercado_pago,
    sincronizar_pagamento_pedido,
)


def formatar_real(valor):
    texto = (
        f"{float(valor or 0):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    return f"R$ {texto}"


def status_visual(status_pedido, status_pagamento):
    pedido = (status_pedido or "").lower()
    pagamento = (status_pagamento or "").lower()

    if pedido == "pago_pendencia_estoque":
        return "Pagamento aprovado com pendência de estoque", "pendente"
    if pedido == "pago" or pagamento == "approved":
        return "Pagamento aprovado", "aprovado"
    if pedido == "falha" or pagamento in {
        "rejected",
        "cancelled",
        "refunded",
    }:
        return "Pagamento não aprovado", "falha"
    return "Aguardando pagamento", "pendente"


class DialogPagamentoMercadoPago(QDialog):
    def __init__(self, pedido_id, parent=None):
        super().__init__(parent)

        self.pedido_id = pedido_id
        self.init_point = None

        self.setObjectName("dialogoPagamento")
        self.setWindowTitle("Pagamento Mercado Pago")
        self.resize(560, 420)
        aplicar_estilo(self, "pagamento.qss")

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(24, 24, 24, 24)

        card = QFrame()
        card.setObjectName("cardDialogo")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        titulo = QLabel("Pagamento com Mercado Pago")
        titulo.setObjectName("tituloDialogo")
        titulo.setAlignment(Qt.AlignCenter)

        subtitulo = QLabel(
            "O checkout seguro será aberto no navegador. Depois, use “Verificar pagamento” para atualizar o pedido."
        )
        subtitulo.setObjectName("subtituloDialogo")
        subtitulo.setWordWrap(True)
        subtitulo.setAlignment(Qt.AlignCenter)

        self.numero_pedido = QLabel()
        self.numero_pedido.setAlignment(Qt.AlignCenter)

        self.valor_total = QLabel()
        self.valor_total.setObjectName("totalDialogo")
        self.valor_total.setAlignment(Qt.AlignCenter)

        self.status_pagamento = QLabel()
        self.status_pagamento.setObjectName("statusPagamento")
        self.status_pagamento.setAlignment(Qt.AlignCenter)

        botoes = QHBoxLayout()

        self.botao_pagar = QPushButton("Pagar com Mercado Pago")
        self.botao_pagar.setObjectName("botaoSucesso")

        self.botao_verificar = QPushButton("Verificar pagamento")
        fechar = QPushButton("Fechar")

        botoes.addWidget(self.botao_pagar)
        botoes.addWidget(self.botao_verificar)
        botoes.addWidget(fechar)

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addSpacing(4)
        layout.addWidget(self.numero_pedido)
        layout.addWidget(self.valor_total)
        layout.addWidget(self.status_pagamento)
        layout.addStretch()
        layout.addLayout(botoes)

        layout_raiz.addWidget(card)

        self.botao_pagar.clicked.connect(self.abrir_pagamento)
        self.botao_verificar.clicked.connect(self.verificar_pagamento)
        fechar.clicked.connect(self.accept)

        self.carregar_pedido()

    def atualizar_estilo_status(self, tipo):
        self.status_pagamento.setProperty("tipoStatus", tipo)
        self.status_pagamento.style().unpolish(self.status_pagamento)
        self.status_pagamento.style().polish(self.status_pagamento)

    def carregar_pedido(self):
        try:
            with app.app_context():
                pedido = Pedido.query.get(self.pedido_id)

                if pedido is None:
                    raise ValueError("Pedido não encontrado.")

                numero = pedido.id
                total = float(pedido.total or 0)
                status_pedido = pedido.status
                status_pagamento = pedido.status_pagamento
                self.init_point = pedido.mercado_pago_init_point

            texto_status, tipo = status_visual(
                status_pedido,
                status_pagamento,
            )

            self.numero_pedido.setText(f"Pedido nº {numero}")
            self.valor_total.setText(f"Total: {formatar_real(total)}")
            self.status_pagamento.setText(texto_status)
            self.atualizar_estilo_status(tipo)

            aprovado = tipo == "aprovado"
            self.botao_pagar.setEnabled(not aprovado)
            self.botao_verificar.setEnabled(not aprovado)

            if aprovado:
                self.botao_pagar.setText("Pagamento aprovado")
            else:
                self.botao_pagar.setText(
                    "Abrir Mercado Pago novamente"
                    if self.init_point
                    else "Pagar com Mercado Pago"
                )

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))

    def abrir_pagamento(self):
        self.botao_pagar.setEnabled(False)
        self.botao_pagar.setText("Preparando checkout...")

        try:
            if not self.init_point:
                with app.app_context():
                    pagamento = criar_preferencia_mercado_pago(self.pedido_id)
                self.init_point = pagamento["init_point"]

            if not QDesktopServices.openUrl(QUrl(self.init_point)):
                raise ErroPagamento("Não foi possível abrir o navegador.")

            self.botao_pagar.setText("Abrir Mercado Pago novamente")

        except ErroPagamento as erro:
            QMessageBox.warning(self, "Pagamento", str(erro))
            self.botao_pagar.setText("Pagar com Mercado Pago")
        except Exception as erro:
            print("ERRO AO ABRIR PAGAMENTO:", erro)
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível iniciar o pagamento.",
            )
            self.botao_pagar.setText("Pagar com Mercado Pago")
        finally:
            self.botao_pagar.setEnabled(True)

    def verificar_pagamento(self):
        self.botao_verificar.setEnabled(False)
        self.botao_verificar.setText("Consultando...")

        try:
            with app.app_context():
                pagamento = sincronizar_pagamento_pedido(self.pedido_id)

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
                    "O Mercado Pago ainda não confirmou o pagamento.",
                )

            self.carregar_pedido()

        except ErroPagamento as erro:
            QMessageBox.warning(self, "Pagamento", str(erro))
        except Exception as erro:
            print("ERRO AO VERIFICAR PAGAMENTO:", erro)
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível verificar o pagamento.",
            )
        finally:
            self.botao_verificar.setEnabled(True)
            self.botao_verificar.setText("Verificar pagamento")
