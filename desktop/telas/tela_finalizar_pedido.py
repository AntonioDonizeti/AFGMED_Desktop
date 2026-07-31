from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from projetoafgmed import app
from projetoafgmed.models import (
    Carrinho,
    PerfilUsuario,
)
from projetoafgmed.servicos_compras import (
    ErroCompra,
    finalizar_pedido_local,
)

from .tela_pagamento import (
    DialogPagamentoMercadoPago,
)


class DialogFinalizarPedido(QDialog):
    def __init__(
        self,
        usuario_id,
        parent=None,
    ):
        super().__init__(parent)

        self.usuario_id = usuario_id
        self.pedido_id = None

        self.setWindowTitle(
            "Finalizar pedido"
        )

        self.resize(
            520,
            420,
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        layout.setSpacing(14)

        # ==================================
        # TÍTULO
        # ==================================

        titulo = QLabel(
            "Dados de entrega"
        )

        titulo.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
            }
            """
        )

        aviso = QLabel(
            "Confira os dados de entrega. "
            "Após criar o pedido, a janela de "
            "pagamento do Mercado Pago será aberta."
        )

        aviso.setWordWrap(True)

        aviso.setStyleSheet(
            """
            QLabel {
                color: #555555;
            }
            """
        )

        # ==================================
        # FORMULÁRIO
        # ==================================

        formulario = QFormLayout()

        formulario.setSpacing(12)

        self.endereco = QLineEdit()

        self.endereco.setPlaceholderText(
            "Rua, número e complemento"
        )

        self.cidade = QLineEdit()

        self.cidade.setPlaceholderText(
            "Cidade"
        )

        self.estado = QLineEdit()

        self.estado.setMaxLength(2)

        self.estado.setPlaceholderText(
            "Ex.: SP"
        )

        self.cep = QLineEdit()

        self.cep.setMaxLength(9)

        self.cep.setPlaceholderText(
            "Ex.: 00000-000"
        )

        formulario.addRow(
            "Endereço:",
            self.endereco,
        )

        formulario.addRow(
            "Cidade:",
            self.cidade,
        )

        formulario.addRow(
            "Estado:",
            self.estado,
        )

        formulario.addRow(
            "CEP:",
            self.cep,
        )

        # ==================================
        # TOTAL
        # ==================================

        self.total = QLabel(
            "Total: R$ 0,00"
        )

        self.total.setAlignment(
            Qt.AlignRight
        )

        self.total.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
            }
            """
        )

        # ==================================
        # BOTÕES
        # ==================================

        botoes = QHBoxLayout()

        self.botao_voltar = QPushButton(
            "Voltar"
        )

        self.confirmar = QPushButton(
            "Criar pedido e pagar"
        )

        self.botao_voltar.setMinimumHeight(
            42
        )

        self.confirmar.setMinimumHeight(
            42
        )

        self.confirmar.setMinimumWidth(
            190
        )

        botoes.addWidget(
            self.botao_voltar
        )

        botoes.addStretch()

        botoes.addWidget(
            self.confirmar
        )

        # ==================================
        # MONTAGEM
        # ==================================

        layout.addWidget(titulo)
        layout.addWidget(aviso)
        layout.addSpacing(5)
        layout.addLayout(formulario)
        layout.addWidget(self.total)
        layout.addStretch()
        layout.addLayout(botoes)

        self.botao_voltar.clicked.connect(
            self.reject
        )

        self.confirmar.clicked.connect(
            self.finalizar
        )

        self.carregar_dados()

    def carregar_dados(self):
        """
        Carrega o endereço salvo no perfil e
        calcula o total do carrinho ativo.
        """

        try:
            with app.app_context():
                perfil = (
                    PerfilUsuario.query.filter_by(
                        id_usuario=self.usuario_id
                    ).first()
                )

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

                dados_perfil = {
                    "endereco": "",
                    "cidade": "",
                    "estado": "",
                    "cep": "",
                }

                if perfil is not None:
                    dados_perfil = {
                        "endereco": (
                            perfil.endereco or ""
                        ),
                        "cidade": (
                            perfil.cidade or ""
                        ),
                        "estado": (
                            perfil.estado or ""
                        ),
                        "cep": (
                            perfil.cep or ""
                        ),
                    }

                total = 0.0

                if carrinho is not None:
                    total = sum(
                        float(
                            item.preco_unitario or 0
                        )
                        * int(
                            item.quantidade or 0
                        )
                        for item in carrinho.itens
                    )

            self.endereco.setText(
                dados_perfil["endereco"]
            )

            self.cidade.setText(
                dados_perfil["cidade"]
            )

            self.estado.setText(
                dados_perfil["estado"]
            )

            self.cep.setText(
                dados_perfil["cep"]
            )

            self.total.setText(
                f"Total: {self.formatar_real(total)}"
            )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível carregar "
                    "os dados do pedido."
                    f"\n\n{erro}"
                ),
            )

            self.confirmar.setEnabled(
                False
            )

    @staticmethod
    def formatar_real(valor):
        valor = float(valor or 0)

        texto = (
            f"{valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        return f"R$ {texto}"

    def validar_campos(self):
        endereco = self.endereco.text().strip()
        cidade = self.cidade.text().strip()
        estado = self.estado.text().strip().upper()
        cep = self.cep.text().strip()

        if not endereco:
            raise ErroCompra(
                "Informe o endereço de entrega."
            )

        if not cidade:
            raise ErroCompra(
                "Informe a cidade."
            )

        if not estado:
            raise ErroCompra(
                "Informe o estado."
            )

        if len(estado) != 2:
            raise ErroCompra(
                "Informe a sigla do estado "
                "com dois caracteres."
            )

        if not cep:
            raise ErroCompra(
                "Informe o CEP."
            )

        return {
            "endereco": endereco,
            "cidade": cidade,
            "estado": estado,
            "cep": cep,
        }

    def finalizar(self):
        self.confirmar.setEnabled(False)

        self.botao_voltar.setEnabled(False)

        self.confirmar.setText(
            "Criando pedido..."
        )

        try:
            dados = self.validar_campos()

            # Cria o Pedido, ItemPedido e Entrega
            # no banco de dados.
            with app.app_context():
                self.pedido_id = (
                    finalizar_pedido_local(
                        usuario_id=self.usuario_id,
                        endereco=dados["endereco"],
                        cidade=dados["cidade"],
                        estado=dados["estado"],
                        cep=dados["cep"],
                    )
                )

            QMessageBox.information(
                self,
                "Pedido criado",
                (
                    f"Pedido nº {self.pedido_id} "
                    "criado com sucesso.\n\n"
                    "Agora você será direcionado "
                    "para o pagamento."
                ),
            )

            self.abrir_janela_pagamento()

        except ErroCompra as erro:
            QMessageBox.warning(
                self,
                "Não foi possível finalizar",
                str(erro),
            )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível finalizar "
                    "o pedido."
                    f"\n\n{erro}"
                ),
            )

        finally:
            self.confirmar.setEnabled(True)

            self.botao_voltar.setEnabled(True)

            self.confirmar.setText(
                "Criar pedido e pagar"
            )

    def abrir_janela_pagamento(self):
        """
        Abre a janela que cria a preferência e
        encaminha o usuário ao Mercado Pago.
        """

        if self.pedido_id is None:
            QMessageBox.warning(
                self,
                "Pedido",
                "Nenhum pedido foi criado.",
            )
            return

        try:
            janela_pagamento = (
                DialogPagamentoMercadoPago(
                    pedido_id=self.pedido_id,
                    parent=self,
                )
            )

            janela_pagamento.exec()

            # Fecha a finalização depois que
            # a janela de pagamento for fechada.
            self.accept()

        except Exception as erro:
            QMessageBox.warning(
                self,
                "Pedido salvo",
                (
                    f"O pedido nº {self.pedido_id} "
                    "foi salvo no banco, mas a janela "
                    "de pagamento não pôde ser aberta."
                    f"\n\n{erro}"
                ),
            )

            # Mesmo que o pagamento não abra,
            # o pedido já existe no banco.
            self.accept()