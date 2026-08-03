import json
import re

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
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
from projetoafgmed.servicos_compras import (
    ErroCompra,
    finalizar_pedido_local,
)

from .tela_pagamento import DialogPagamentoMercadoPago


def formatar_real(valor):
    texto = (
        f"{float(valor or 0):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"R$ {texto}"


def somente_numeros(valor):
    return re.sub(r"\D", "", valor or "")


class DialogFinalizarPedido(QDialog):
    def __init__(self, usuario_id, parent=None):
        super().__init__(parent)

        self.usuario_id = usuario_id
        self.pedido_id = None
        self._cep_em_consulta = ""

        self.setObjectName("dialogoFinalizar")
        self.setWindowTitle("Finalizar pedido")
        self.setMinimumSize(650, 620)
        self.resize(650, 620)

        aplicar_estilo(self, "pagamento.qss")

        # Responsável por fazer a consulta do CEP sem travar a interface.
        self.gerenciador_rede = QNetworkAccessManager(self)
        self.gerenciador_rede.finished.connect(
            self._processar_resposta_cep
        )

        # Aguarda alguns milissegundos antes de pesquisar automaticamente.
        self.timer_consulta_cep = QTimer(self)
        self.timer_consulta_cep.setSingleShot(True)
        self.timer_consulta_cep.setInterval(550)
        self.timer_consulta_cep.timeout.connect(self.consultar_cep)

        self._montar_interface()
        self._conectar_eventos()
        self.carregar_dados()

    def _montar_interface(self):
        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(24, 24, 24, 24)

        card = QFrame()
        card.setObjectName("cardDialogo")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 25, 28, 25)
        layout.setSpacing(16)

        titulo = QLabel("Dados de entrega")
        titulo.setObjectName("tituloDialogo")

        subtitulo = QLabel(
            "Digite o CEP para preencher automaticamente a cidade e o estado. "
            "Depois, complete o endereço e confira os dados antes de pagar."
        )
        subtitulo.setObjectName("subtituloDialogo")
        subtitulo.setWordWrap(True)

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addSpacing(4)

        formulario = QGridLayout()
        formulario.setHorizontalSpacing(14)
        formulario.setVerticalSpacing(8)

        # A primeira coluna ocupa mais espaço que a coluna do estado.
        formulario.setColumnStretch(0, 4)
        formulario.setColumnStretch(1, 1)

        # CEP
        formulario.addWidget(
            self._criar_rotulo("CEP"),
            0,
            0,
            1,
            2,
        )

        self.cep = QLineEdit()
        self.cep.setObjectName("campoCep")
        self.cep.setPlaceholderText("00000-000")
        self.cep.setMaxLength(9)
        self.cep.setClearButtonEnabled(True)

        self.botao_buscar_cep = QPushButton("Buscar CEP")
        self.botao_buscar_cep.setObjectName("botaoBuscarCep")
        self.botao_buscar_cep.setMinimumWidth(120)
        self.botao_buscar_cep.setToolTip(
            "Consulta o CEP e preenche cidade e estado."
        )

        linha_cep = QHBoxLayout()
        linha_cep.setContentsMargins(0, 0, 0, 0)
        linha_cep.setSpacing(10)
        linha_cep.addWidget(self.cep, 1)
        linha_cep.addWidget(self.botao_buscar_cep)

        formulario.addLayout(
            linha_cep,
            1,
            0,
            1,
            2,
        )

        self.status_cep = QLabel()
        self.status_cep.setObjectName("statusCep")
        self.status_cep.setWordWrap(True)
        self.status_cep.setVisible(False)

        formulario.addWidget(
            self.status_cep,
            2,
            0,
            1,
            2,
        )

        # Endereço
        formulario.addWidget(
            self._criar_rotulo("Endereço completo"),
            3,
            0,
            1,
            2,
        )

        self.endereco = QLineEdit()
        self.endereco.setPlaceholderText(
            "Rua, avenida, número e complemento"
        )
        self.endereco.setClearButtonEnabled(True)

        formulario.addWidget(
            self.endereco,
            4,
            0,
            1,
            2,
        )

        # Cidade e estado
        formulario.addWidget(
            self._criar_rotulo("Cidade"),
            5,
            0,
        )

        formulario.addWidget(
            self._criar_rotulo("Estado"),
            5,
            1,
        )

        self.cidade = QLineEdit()
        self.cidade.setPlaceholderText("Cidade")
        self.cidade.setClearButtonEnabled(True)

        self.estado = QLineEdit()
        self.estado.setObjectName("campoEstado")
        self.estado.setPlaceholderText("UF")
        self.estado.setMaxLength(2)
        self.estado.setAlignment(Qt.AlignCenter)

        formulario.addWidget(self.cidade, 6, 0)
        formulario.addWidget(self.estado, 6, 1)

        layout.addLayout(formulario)
        layout.addStretch()

        # Resumo do total
        resumo = QFrame()
        resumo.setObjectName("resumoPedido")

        layout_resumo = QHBoxLayout(resumo)
        layout_resumo.setContentsMargins(16, 13, 16, 13)

        rotulo_total = QLabel("Total do pedido")
        rotulo_total.setObjectName("rotuloTotalDialogo")

        self.total = QLabel("R$ 0,00")
        self.total.setObjectName("totalDialogo")
        self.total.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        layout_resumo.addWidget(rotulo_total)
        layout_resumo.addStretch()
        layout_resumo.addWidget(self.total)

        layout.addWidget(resumo)

        # Botões inferiores
        botoes = QHBoxLayout()
        botoes.setSpacing(10)

        self.botao_voltar = QPushButton("Voltar")

        self.confirmar = QPushButton(
            "Criar pedido e pagar"
        )
        self.confirmar.setObjectName("botaoSucesso")
        self.confirmar.setMinimumWidth(210)

        botoes.addWidget(self.botao_voltar)
        botoes.addStretch()
        botoes.addWidget(self.confirmar)

        layout.addLayout(botoes)
        layout_raiz.addWidget(card)

    def _conectar_eventos(self):
        self.botao_voltar.clicked.connect(self.reject)
        self.confirmar.clicked.connect(self.finalizar)

        self.botao_buscar_cep.clicked.connect(
            self.consultar_cep
        )

        self.cep.textChanged.connect(
            self._formatar_e_agendar_consulta_cep
        )

        self.cep.editingFinished.connect(
            self._consultar_cep_ao_sair
        )

        self.estado.textEdited.connect(
            self._normalizar_estado
        )

    @staticmethod
    def _criar_rotulo(texto):
        rotulo = QLabel(texto)
        rotulo.setObjectName("rotuloCampo")
        return rotulo

    def _normalizar_estado(self, texto):
        texto_maiusculo = texto.upper()

        if texto == texto_maiusculo:
            return

        posicao_cursor = self.estado.cursorPosition()

        self.estado.blockSignals(True)
        self.estado.setText(texto_maiusculo)
        self.estado.setCursorPosition(posicao_cursor)
        self.estado.blockSignals(False)

    def _formatar_e_agendar_consulta_cep(self, texto):
        numeros = somente_numeros(texto)[:8]
        cep_formatado = numeros

        if len(numeros) > 5:
            cep_formatado = (
                f"{numeros[:5]}-{numeros[5:]}"
            )

        if texto != cep_formatado:
            self.cep.blockSignals(True)
            self.cep.setText(cep_formatado)
            self.cep.setCursorPosition(
                len(cep_formatado)
            )
            self.cep.blockSignals(False)

        self.timer_consulta_cep.stop()

        if len(numeros) == 8:
            self._mostrar_status_cep(
                "CEP completo. Buscando cidade e estado...",
                "carregando",
            )

            self.timer_consulta_cep.start()

        elif numeros:
            self._mostrar_status_cep(
                "Digite os 8 números do CEP.",
                "informacao",
            )

        else:
            self._ocultar_status_cep()

    def _consultar_cep_ao_sair(self):
        cep = somente_numeros(self.cep.text())

        if len(cep) == 8:
            self.timer_consulta_cep.stop()
            self.consultar_cep()

    def consultar_cep(self):
        cep = somente_numeros(self.cep.text())

        if len(cep) != 8:
            self._mostrar_status_cep(
                "Informe um CEP válido com 8 números.",
                "erro",
            )

            self.cep.setFocus()
            return

        # Impede duas consultas simultâneas para o mesmo CEP.
        if self._cep_em_consulta == cep:
            return

        self._cep_em_consulta = cep

        self.botao_buscar_cep.setEnabled(False)
        self.botao_buscar_cep.setText("Buscando...")

        self._mostrar_status_cep(
            "Consultando CEP...",
            "carregando",
        )

        url = QUrl(
            f"https://viacep.com.br/ws/{cep}/json/"
        )

        requisicao = QNetworkRequest(url)
        requisicao.setRawHeader(
            b"Accept",
            b"application/json",
        )
        requisicao.setTransferTimeout(8000)

        resposta = self.gerenciador_rede.get(
            requisicao
        )

        resposta.setProperty(
            "cepConsultado",
            cep,
        )

    def _processar_resposta_cep(self, resposta):
        cep_consultado = (
            resposta.property("cepConsultado") or ""
        )

        cep_atual = somente_numeros(
            self.cep.text()
        )

        if cep_consultado == self._cep_em_consulta:
            self._cep_em_consulta = ""

            self.botao_buscar_cep.setEnabled(True)
            self.botao_buscar_cep.setText("Buscar CEP")

        try:
            # Ignora uma resposta antiga caso o usuário
            # tenha alterado o CEP durante a consulta.
            if cep_consultado != cep_atual:
                return

            if (
                resposta.error()
                != QNetworkReply.NetworkError.NoError
            ):
                self._mostrar_status_cep(
                    "Não foi possível consultar o CEP. "
                    "Confira a conexão ou preencha os dados manualmente.",
                    "erro",
                )
                return

            conteudo = bytes(
                resposta.readAll()
            ).decode("utf-8")

            dados = json.loads(conteudo)

            if dados.get("erro"):
                self._mostrar_status_cep(
                    "CEP não encontrado. Confira o número informado.",
                    "erro",
                )
                return

            cidade = str(
                dados.get("localidade") or ""
            ).strip()

            estado = str(
                dados.get("uf") or ""
            ).strip().upper()

            logradouro = str(
                dados.get("logradouro") or ""
            ).strip()

            bairro = str(
                dados.get("bairro") or ""
            ).strip()

            if not cidade or len(estado) != 2:
                self._mostrar_status_cep(
                    "O serviço não retornou cidade e estado para esse CEP.",
                    "erro",
                )
                return

            self.cidade.setText(cidade)
            self.estado.setText(estado)

            # Também preenche a rua quando ela estiver disponível.
            endereco_atual = self.endereco.text().strip()

            if logradouro and not endereco_atual:
                endereco_sugerido = logradouro

                if bairro:
                    endereco_sugerido += (
                        f" - {bairro}"
                    )

                self.endereco.setText(
                    endereco_sugerido
                )

                # Deixa o cursor no final para o usuário
                # adicionar número e complemento.
                self.endereco.setCursorPosition(
                    len(endereco_sugerido)
                )

            self._mostrar_status_cep(
                f"CEP localizado: {cidade} - {estado}. "
                "Complete o número do endereço.",
                "sucesso",
            )

            self.endereco.setFocus()

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):
            self._mostrar_status_cep(
                "Não foi possível interpretar a resposta da consulta. "
                "Preencha os dados manualmente.",
                "erro",
            )

        except Exception as erro:
            print(
                "ERRO AO PROCESSAR CEP:",
                erro,
            )

            self._mostrar_status_cep(
                "Ocorreu um erro ao consultar o CEP. "
                "Preencha os dados manualmente.",
                "erro",
            )

        finally:
            resposta.deleteLater()

    def _mostrar_status_cep(
        self,
        mensagem,
        tipo,
    ):
        self.status_cep.setText(mensagem)

        self.status_cep.setProperty(
            "tipoStatusCep",
            tipo,
        )

        self.status_cep.style().unpolish(
            self.status_cep
        )

        self.status_cep.style().polish(
            self.status_cep
        )

        self.status_cep.setVisible(True)

    def _ocultar_status_cep(self):
        self.status_cep.clear()
        self.status_cep.setVisible(False)

    def carregar_dados(self):
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

                dados = {
                    "endereco": (
                        perfil.endereco
                        if perfil
                        else ""
                    ),
                    "cidade": (
                        perfil.cidade
                        if perfil
                        else ""
                    ),
                    "estado": (
                        perfil.estado
                        if perfil
                        else ""
                    ),
                    "cep": (
                        perfil.cep
                        if perfil
                        else ""
                    ),
                }

                total = 0.0

                if carrinho:
                    total = sum(
                        int(item.quantidade or 0)
                        * float(
                            item.preco_unitario or 0
                        )
                        for item in carrinho.itens
                    )

            self.endereco.setText(
                dados["endereco"] or ""
            )

            self.cidade.setText(
                dados["cidade"] or ""
            )

            self.estado.setText(
                (dados["estado"] or "").upper()
            )

            cep_formatado = somente_numeros(
                dados["cep"] or ""
            )[:8]

            if len(cep_formatado) > 5:
                cep_formatado = (
                    f"{cep_formatado[:5]}-"
                    f"{cep_formatado[5:]}"
                )

            self.cep.blockSignals(True)
            self.cep.setText(cep_formatado)
            self.cep.blockSignals(False)

            self.total.setText(
                formatar_real(total)
            )

        except Exception as erro:
            print(
                "ERRO AO CARREGAR FINALIZAÇÃO:",
                erro,
            )

            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível carregar os dados do pedido.",
            )

            self.confirmar.setEnabled(False)

    def validar_campos(self):
        cep_numeros = somente_numeros(
            self.cep.text()
        )

        if len(cep_numeros) == 8:
            cep_formatado = (
                f"{cep_numeros[:5]}-"
                f"{cep_numeros[5:]}"
            )
        else:
            cep_formatado = (
                self.cep.text().strip()
            )

        dados = {
            "endereco": (
                self.endereco.text().strip()
            ),
            "cidade": (
                self.cidade.text().strip()
            ),
            "estado": (
                self.estado.text()
                .strip()
                .upper()
            ),
            "cep": cep_formatado,
        }

        if len(cep_numeros) != 8:
            self.cep.setFocus()

            raise ErroCompra(
                "Informe um CEP válido com 8 números."
            )

        if not dados["endereco"]:
            self.endereco.setFocus()

            raise ErroCompra(
                "Informe o endereço de entrega."
            )

        if not dados["cidade"]:
            self.cidade.setFocus()

            raise ErroCompra(
                "Informe a cidade."
            )

        if (
            len(dados["estado"]) != 2
            or not dados["estado"].isalpha()
        ):
            self.estado.setFocus()

            raise ErroCompra(
                "Informe a sigla do estado com dois caracteres."
            )

        return dados

    def finalizar(self):
        self.confirmar.setEnabled(False)
        self.botao_voltar.setEnabled(False)
        self.botao_buscar_cep.setEnabled(False)
        self.confirmar.setText("Criando pedido...")

        try:
            dados = self.validar_campos()

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

            janela_pagamento = (
                DialogPagamentoMercadoPago(
                    pedido_id=self.pedido_id,
                    parent=self,
                )
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
            print(
                "ERRO AO FINALIZAR PEDIDO:",
                erro,
            )

            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível finalizar o pedido.",
            )

        finally:
            self.confirmar.setEnabled(True)
            self.botao_voltar.setEnabled(True)

            if not self._cep_em_consulta:
                self.botao_buscar_cep.setEnabled(True)

            self.confirmar.setText(
                "Criar pedido e pagar"
            )