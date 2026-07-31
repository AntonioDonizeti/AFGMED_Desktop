from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from projetoafgmed import app
from projetoafgmed.models import Pedido
from projetoafgmed.servicos_pagamento import (
    ErroPagamento,
    criar_preferencia_mercado_pago,
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


class DialogPagamentoMercadoPago(QDialog):
    def __init__(
        self,
        pedido_id,
        parent=None,
    ):
        super().__init__(parent)

        self.pedido_id = pedido_id
        self.init_point = None

        self.setWindowTitle(
            "Pagamento Mercado Pago"
        )

        self.resize(500, 340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            28,
            28,
            28,
            28,
        )
        layout.setSpacing(14)

        titulo = QLabel(
            "Pagamento com Mercado Pago"
        )
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet(
            "font-size: 23px; font-weight: bold;"
        )

        self.numero_pedido = QLabel()
        self.valor_total = QLabel()
        self.status_pagamento = QLabel()

        self.valor_total.setStyleSheet(
            "font-size: 22px; font-weight: bold;"
        )

        self.status_pagamento.setStyleSheet(
            "font-size: 16px;"
        )

        aviso = QLabel(
            "O checkout será aberto no navegador "
            "para garantir uma autenticação segura."
        )
        aviso.setWordWrap(True)
        aviso.setStyleSheet(
            "color: #555555;"
        )

        botoes = QHBoxLayout()

        self.botao_pagar = QPushButton(
            "Pagar com Mercado Pago"
        )
        self.botao_pagar.setMinimumHeight(44)

        self.botao_verificar = QPushButton(
            "Verificar pagamento"
        )
        self.botao_verificar.setMinimumHeight(44)

        fechar = QPushButton("Fechar")
        fechar.setMinimumHeight(44)

        botoes.addWidget(self.botao_pagar)
        botoes.addWidget(self.botao_verificar)
        botoes.addWidget(fechar)

        layout.addWidget(titulo)
        layout.addSpacing(8)
        layout.addWidget(self.numero_pedido)
        layout.addWidget(self.valor_total)
        layout.addWidget(self.status_pagamento)
        layout.addWidget(aviso)
        layout.addStretch()
        layout.addLayout(botoes)

        self.botao_pagar.clicked.connect(
            self.abrir_pagamento
        )

        self.botao_verificar.clicked.connect(
            self.carregar_pedido
        )

        fechar.clicked.connect(self.reject)

        self.carregar_pedido()

    def carregar_pedido(self):
        try:
            with app.app_context():
                pedido = Pedido.query.get(
                    self.pedido_id
                )

                if pedido is None:
                    raise ValueError(
                        "Pedido não encontrado."
                    )

                numero = pedido.id
                total = float(pedido.total or 0)

                status = (
                    pedido.status_pagamento
                    or "pending"
                )

                self.init_point = (
                    pedido.mercado_pago_init_point
                )

            status_texto = {
                "approved": "Pagamento aprovado",
                "pending": "Pagamento pendente",
                "rejected": "Pagamento recusado",
                "cancelled": "Pagamento cancelado",
            }.get(
                status,
                status,
            )

            self.numero_pedido.setText(
                f"Pedido nº {numero}"
            )

            self.valor_total.setText(
                f"Total: {formatar_real(total)}"
            )

            self.status_pagamento.setText(
                f"Status: {status_texto}"
            )

            if status == "approved":
                self.botao_pagar.setEnabled(False)
                self.botao_pagar.setText(
                    "Pagamento aprovado"
                )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                str(erro),
            )

    def abrir_pagamento(self):
        self.botao_pagar.setEnabled(False)
        self.botao_pagar.setText(
            "Preparando pagamento..."
        )

        try:
            if not self.init_point:
                with app.app_context():
                    pagamento = (
                        criar_preferencia_mercado_pago(
                            self.pedido_id
                        )
                    )

                self.init_point = pagamento[
                    "init_point"
                ]

            abriu = QDesktopServices.openUrl(
                QUrl(self.init_point)
            )

            if not abriu:
                raise ErroPagamento(
                    "Não foi possível abrir o navegador."
                )

            self.botao_pagar.setText(
                "Abrir Mercado Pago novamente"
            )

        except ErroPagamento as erro:
            QMessageBox.warning(
                self,
                "Pagamento",
                str(erro),
            )

            self.botao_pagar.setText(
                "Pagar com Mercado Pago"
            )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível iniciar "
                    f"o pagamento.\n\n{erro}"
                ),
            )

            self.botao_pagar.setText(
                "Pagar com Mercado Pago"
            )

        finally:
            self.botao_pagar.setEnabled(True)