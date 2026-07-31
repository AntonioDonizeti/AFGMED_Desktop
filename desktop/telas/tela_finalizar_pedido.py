from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from desktop.estilos import aplicar_estilo
from projetoafgmed import app
from projetoafgmed.models import Carrinho, PerfilUsuario
from projetoafgmed.servicos_compras import ErroCompra, finalizar_pedido_local
from .tela_pagamento import DialogPagamentoMercadoPago


def formatar_real(valor):
    texto = (
        f"{float(valor or 0):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    return f"R$ {texto}"


class DialogFinalizarPedido(QDialog):
    def __init__(self, usuario_id, parent=None):
        super().__init__(parent)

        self.usuario_id = usuario_id
        self.pedido_id = None

        self.setObjectName("dialogoFinalizar")
        self.setWindowTitle("Finalizar pedido")
        self.resize(560, 520)
        aplicar_estilo(self, "pagamento.qss")

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(24, 24, 24, 24)

        card = QFrame()
        card.setObjectName("cardDialogo")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        titulo = QLabel("Dados de entrega")
        titulo.setObjectName("tituloDialogo")

        subtitulo = QLabel(
            "Confira o endereço. Depois da criação do pedido, o checkout do Mercado Pago será aberto."
        )
        subtitulo.setObjectName("subtituloDialogo")
        subtitulo.setWordWrap(True)

        formulario = QFormLayout()
        formulario.setSpacing(12)

        self.endereco = QLineEdit()
        self.endereco.setPlaceholderText("Rua, número e complemento")

        self.cidade = QLineEdit()
        self.cidade.setPlaceholderText("Cidade")

        self.estado = QLineEdit()
        self.estado.setMaxLength(2)
        self.estado.setPlaceholderText("Ex.: SP")

        self.cep = QLineEdit()
        self.cep.setMaxLength(9)
        self.cep.setPlaceholderText("Ex.: 00000-000")

        formulario.addRow("Endereço:", self.endereco)
        formulario.addRow("Cidade:", self.cidade)
        formulario.addRow("Estado:", self.estado)
        formulario.addRow("CEP:", self.cep)

        self.total = QLabel("Total: R$ 0,00")
        self.total.setObjectName("totalDialogo")
        self.total.setAlignment(Qt.AlignRight)

        botoes = QHBoxLayout()

        self.botao_voltar = QPushButton("Voltar")
        self.confirmar = QPushButton("Criar pedido e pagar")
        self.confirmar.setObjectName("botaoSucesso")
        self.confirmar.setMinimumWidth(190)

        botoes.addWidget(self.botao_voltar)
        botoes.addStretch()
        botoes.addWidget(self.confirmar)

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addLayout(formulario)
        layout.addWidget(self.total)
        layout.addLayout(botoes)

        layout_raiz.addWidget(card)

        self.botao_voltar.clicked.connect(self.reject)
        self.confirmar.clicked.connect(self.finalizar)

        self.carregar_dados()

    def carregar_dados(self):
        try:
            with app.app_context():
                perfil = PerfilUsuario.query.filter_by(
                    id_usuario=self.usuario_id
                ).first()

                carrinho = (
                    Carrinho.query.filter_by(
                        id_usuario=self.usuario_id,
                        status="ativo",
                    )
                    .order_by(Carrinho.id.desc())
                    .first()
                )

                dados = {
                    "endereco": perfil.endereco if perfil else "",
                    "cidade": perfil.cidade if perfil else "",
                    "estado": perfil.estado if perfil else "",
                    "cep": perfil.cep if perfil else "",
                }

                total = 0.0
                if carrinho:
                    total = sum(
                        int(item.quantidade or 0)
                        * float(item.preco_unitario or 0)
                        for item in carrinho.itens
                    )

            self.endereco.setText(dados["endereco"] or "")
            self.cidade.setText(dados["cidade"] or "")
            self.estado.setText(dados["estado"] or "")
            self.cep.setText(dados["cep"] or "")
            self.total.setText(f"Total: {formatar_real(total)}")

        except Exception as erro:
            print("ERRO AO CARREGAR FINALIZAÇÃO:", erro)
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível carregar os dados do pedido.",
            )
            self.confirmar.setEnabled(False)

    def validar_campos(self):
        dados = {
            "endereco": self.endereco.text().strip(),
            "cidade": self.cidade.text().strip(),
            "estado": self.estado.text().strip().upper(),
            "cep": self.cep.text().strip(),
        }

        if not dados["endereco"]:
            raise ErroCompra("Informe o endereço de entrega.")
        if not dados["cidade"]:
            raise ErroCompra("Informe a cidade.")
        if len(dados["estado"]) != 2:
            raise ErroCompra("Informe a sigla do estado com dois caracteres.")
        if not dados["cep"]:
            raise ErroCompra("Informe o CEP.")

        return dados

    def finalizar(self):
        self.confirmar.setEnabled(False)
        self.botao_voltar.setEnabled(False)
        self.confirmar.setText("Criando pedido...")

        try:
            dados = self.validar_campos()

            with app.app_context():
                self.pedido_id = finalizar_pedido_local(
                    usuario_id=self.usuario_id,
                    endereco=dados["endereco"],
                    cidade=dados["cidade"],
                    estado=dados["estado"],
                    cep=dados["cep"],
                )

            janela_pagamento = DialogPagamentoMercadoPago(
                pedido_id=self.pedido_id,
                parent=self,
            )
            janela_pagamento.exec()
            self.accept()

        except ErroCompra as erro:
            QMessageBox.warning(
                self,
                "Não foi possível finalizar",
                str(erro),
            )
        except Exception as erro:
            print("ERRO AO FINALIZAR PEDIDO:", erro)
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível finalizar o pedido.",
            )
        finally:
            self.confirmar.setEnabled(True)
            self.botao_voltar.setEnabled(True)
            self.confirmar.setText("Criar pedido e pagar")
