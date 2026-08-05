from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from desktop.estilos import aplicar_estilo
from projetoafgmed import app, database
from projetoafgmed.models import Consulta
from projetoafgmed.status import (
    CONSULTA_AGENDADA,
    CONSULTA_CANCELADA,
    CONSULTA_CONCLUIDA,
)

from .tela_medicos import abrir_agendamento


class TelaAgendamentos(QWidget):
    def __init__(self, usuario):
        super().__init__()

        self.usuario_id = usuario.id

        self.cards = []
        self.container = None
        self.grid = None

        self.setObjectName("paginaAgendamentos")

        aplicar_estilo(
            self,
            "agendamentos.qss",
        )

        layout_principal = QVBoxLayout(self)

        layout_principal.setContentsMargins(
            26,
            22,
            26,
            26,
        )

        layout_principal.setSpacing(18)

        # =================================================
        # CABEÇALHO
        # =================================================

        cabecalho = QHBoxLayout()

        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(2)

        titulo = QLabel("Meus agendamentos")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Acompanhe, reagende ou cancele suas consultas."
        )

        subtitulo.setObjectName("subtituloPagina")

        area_titulo.addWidget(titulo)
        area_titulo.addWidget(subtitulo)

        atualizar = QPushButton("Atualizar")
        atualizar.setObjectName("botaoAtualizar")
        atualizar.setMinimumHeight(42)
        atualizar.clicked.connect(self.recarregar)

        cabecalho.addLayout(area_titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(atualizar)

        # =================================================
        # ÁREA DE ROLAGEM
        # =================================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        layout_principal.addLayout(cabecalho)
        layout_principal.addWidget(self.scroll)

        self.recarregar()

    # =====================================================
    # CONTAINER DOS CARDS
    # =====================================================

    def criar_container(self):
        self.container = QWidget()
        self.container.setObjectName(
            "containerAgendamentos"
        )

        self.grid = QGridLayout(self.container)

        self.grid.setContentsMargins(
            0,
            0,
            0,
            14,
        )

        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(18)

        self.grid.setAlignment(
            Qt.AlignTop | Qt.AlignLeft
        )

        self.scroll.setWidget(self.container)

    # =====================================================
    # CARREGAMENTO
    # =====================================================

    def recarregar(self):
        self.criar_container()
        self.cards = []

        try:
            with app.app_context():
                consultas_banco = (
                    Consulta.query.filter_by(
                        usuario_id=self.usuario_id
                    )
                    .order_by(
                        Consulta.data.desc(),
                        Consulta.horario.asc(),
                    )
                    .all()
                )

                consultas = []

                for consulta in consultas_banco:
                    medico = consulta.medico

                    consultas.append(
                        {
                            "id": consulta.id,
                            "medico": (
                                (
                                    f"{medico.nome} "
                                    f"{medico.sobrenome}"
                                ).strip()
                                if medico
                                else "Médico não encontrado"
                            ),
                            "especialidade": (
                                medico.especialidade or ""
                                if medico
                                else ""
                            ),
                            "data": consulta.data,
                            "horario": (
                                consulta.horario or ""
                            ),
                            "status": (
                                consulta.status
                                or CONSULTA_AGENDADA
                            ),
                        }
                    )

        except Exception as erro:
            print(
                "ERRO AO CARREGAR AGENDAMENTOS:",
                erro,
            )

            mensagem = QLabel(
                "Não foi possível carregar os agendamentos."
            )

            mensagem.setObjectName("agendamentosVazio")
            mensagem.setAlignment(Qt.AlignCenter)
            mensagem.setWordWrap(True)

            self.grid.addWidget(
                mensagem,
                0,
                0,
                1,
                3,
            )

            return

        if not consultas:
            mensagem = QLabel(
                "Você ainda não possui agendamentos."
            )

            mensagem.setObjectName("agendamentosVazio")
            mensagem.setAlignment(Qt.AlignCenter)

            self.grid.addWidget(
                mensagem,
                0,
                0,
                1,
                3,
            )

            return

        for consulta in consultas:
            card = self.criar_card(consulta)
            self.cards.append(card)

        self.reorganizar_cards()

    # =====================================================
    # CARD
    # =====================================================

    def criar_card(self, consulta):
        card = QFrame(self.container)

        card.setObjectName("agendamentoCard")

        card.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Minimum,
        )

        card.setMinimumWidth(300)
        card.setMinimumHeight(290)

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        layout.setSpacing(12)

        # =================================================
        # TOPO DO CARD
        # =================================================

        cabecalho = QHBoxLayout()

        numero = QLabel(
            f"Consulta #{consulta['id']}"
        )

        numero.setObjectName(
            "numeroAgendamento"
        )

        status_valor = (
            consulta["status"]
            or CONSULTA_AGENDADA
        ).lower()

        status_texto = {
            CONSULTA_AGENDADA: "Agendada",
            CONSULTA_CONCLUIDA: "Concluída",
            CONSULTA_CANCELADA: "Cancelada",
        }.get(
            status_valor,
            "Em análise",
        )

        status = QLabel(status_texto)

        status.setObjectName(
            "statusAgendamento"
        )

        status.setProperty(
            "tipoStatus",
            status_valor,
        )

        status.setAlignment(Qt.AlignCenter)
        status.setMinimumHeight(30)

        cabecalho.addWidget(numero)
        cabecalho.addStretch()
        cabecalho.addWidget(status)

        # =================================================
        # MÉDICO
        # =================================================

        medico = QLabel(
            consulta["medico"] or "Médico"
        )

        medico.setObjectName(
            "nomeMedicoAgendamento"
        )

        medico.setWordWrap(True)

        especialidade = QLabel(
            consulta["especialidade"]
            or "Especialidade não informada"
        )

        especialidade.setObjectName(
            "especialidadeAgendamento"
        )

        especialidade.setWordWrap(True)

        # =================================================
        # DATA E HORÁRIO
        # =================================================

        painel_data = QFrame()

        painel_data.setObjectName(
            "painelDataAgendamento"
        )

        layout_data = QHBoxLayout(painel_data)

        layout_data.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        layout_data.setSpacing(18)

        coluna_data = QVBoxLayout()
        coluna_data.setSpacing(2)

        rotulo_data = QLabel("Data")

        rotulo_data.setObjectName(
            "rotuloInformacaoAgendamento"
        )

        data_texto = (
            consulta["data"].strftime("%d/%m/%Y")
            if consulta["data"]
            else "Não informada"
        )

        valor_data = QLabel(data_texto)

        valor_data.setObjectName(
            "valorInformacaoAgendamento"
        )

        coluna_data.addWidget(rotulo_data)
        coluna_data.addWidget(valor_data)

        coluna_horario = QVBoxLayout()
        coluna_horario.setSpacing(2)

        rotulo_horario = QLabel("Horário")

        rotulo_horario.setObjectName(
            "rotuloInformacaoAgendamento"
        )

        valor_horario = QLabel(
            consulta["horario"] or "Não informado"
        )

        valor_horario.setObjectName(
            "valorInformacaoAgendamento"
        )

        coluna_horario.addWidget(rotulo_horario)
        coluna_horario.addWidget(valor_horario)

        layout_data.addLayout(coluna_data)
        layout_data.addStretch()
        layout_data.addLayout(coluna_horario)

        layout.addLayout(cabecalho)
        layout.addWidget(medico)
        layout.addWidget(especialidade)
        layout.addWidget(painel_data)
        layout.addStretch()

        # =================================================
        # BOTÕES
        # =================================================

        consulta_futura = (
            self.consulta_esta_no_futuro(
                consulta
            )
        )

        if (
            status_valor == CONSULTA_AGENDADA
            and consulta_futura
        ):
            acoes = QHBoxLayout()
            acoes.setSpacing(10)

            reagendar = QPushButton("Reagendar")

            reagendar.setObjectName(
                "botaoReagendar"
            )

            reagendar.setMinimumHeight(42)

            reagendar.clicked.connect(
                lambda checked=False,
                consulta_id=consulta["id"]: (
                    self.reagendar_consulta(
                        consulta_id
                    )
                )
            )

            cancelar = QPushButton("Cancelar")

            cancelar.setObjectName(
                "botaoPerigo"
            )

            cancelar.setMinimumHeight(42)

            cancelar.clicked.connect(
                lambda checked=False,
                consulta_id=consulta["id"]: (
                    self.cancelar_consulta(
                        consulta_id
                    )
                )
            )

            acoes.addWidget(reagendar, 1)
            acoes.addWidget(cancelar, 1)

            layout.addLayout(acoes)

        elif status_valor == CONSULTA_AGENDADA:
            observacao = QLabel(
                "Consulta encerrada. "
                "Aguardando atualização do médico."
            )

            observacao.setObjectName(
                "observacaoAgendamento"
            )

            observacao.setWordWrap(True)
            observacao.setAlignment(Qt.AlignCenter)

            layout.addWidget(observacao)

        return card

    # =====================================================
    # VERIFICAÇÃO DE DATA
    # =====================================================

    @staticmethod
    def consulta_esta_no_futuro(consulta):
        try:
            horario = datetime.strptime(
                consulta["horario"],
                "%H:%M",
            ).time()

            momento_consulta = datetime.combine(
                consulta["data"],
                horario,
            )

            return momento_consulta > datetime.now()

        except (
            TypeError,
            ValueError,
        ):
            return False

    # =====================================================
    # ORGANIZAÇÃO RESPONSIVA
    # =====================================================

    def reorganizar_cards(self):
        if self.grid is None:
            return

        while self.grid.count():
            self.grid.takeAt(0)

        if not self.cards:
            return

        largura = self.scroll.viewport().width()
        espacamento = self.grid.horizontalSpacing()

        if largura >= 1050:
            colunas = 3

        elif largura >= 700:
            colunas = 2

        else:
            colunas = 1

        largura_util = (
            largura
            - ((colunas - 1) * espacamento)
            - 8
        )

        largura_card = max(
            300,
            min(
                420,
                largura_util // colunas,
            ),
        )

        for coluna in range(3):
            self.grid.setColumnStretch(
                coluna,
                0,
            )

        for indice, card in enumerate(
            self.cards
        ):
            linha = indice // colunas
            coluna = indice % colunas

            card.setFixedWidth(
                largura_card
            )

            card.setVisible(True)

            self.grid.addWidget(
                card,
                linha,
                coluna,
                alignment=Qt.AlignTop,
            )

    def resizeEvent(self, evento):
        super().resizeEvent(evento)

        QTimer.singleShot(
            0,
            self.reorganizar_cards,
        )

    # =====================================================
    # REAGENDAMENTO
    # =====================================================

    def reagendar_consulta(
        self,
        consulta_id,
    ):
        try:
            with app.app_context():
                consulta = database.session.get(
                    Consulta,
                    consulta_id,
                )

                if consulta is None:
                    raise ValueError(
                        "Consulta não encontrada."
                    )

                if (
                    consulta.usuario_id
                    != self.usuario_id
                ):
                    raise PermissionError(
                        "Você não pode reagendar "
                        "esta consulta."
                    )

                if (
                    consulta.status
                    != CONSULTA_AGENDADA
                ):
                    raise ValueError(
                        "Apenas consultas agendadas "
                        "podem ser reagendadas."
                    )

                medico = consulta.medico

                if medico is None:
                    raise ValueError(
                        "O médico desta consulta "
                        "não foi encontrado."
                    )

                dados_medico = {
                    "id": medico.id,
                    "nome": medico.nome or "",
                    "sobrenome": (
                        medico.sobrenome or ""
                    ),
                    "especialidade": (
                        medico.especialidade or ""
                    ),
                    "foto": medico.foto or "",
                }

            alterado = abrir_agendamento(
                usuario_id=self.usuario_id,
                medico=dados_medico,
                consulta_id=consulta_id,
                parent=self,
            )

            if alterado:
                self.recarregar()

        except (
            ValueError,
            PermissionError,
        ) as erro:
            QMessageBox.warning(
                self,
                "Não foi possível reagendar",
                str(erro),
            )

        except Exception as erro:
            print(
                "ERRO AO REAGENDAR CONSULTA:",
                erro,
            )

            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível reagendar "
                    "a consulta."
                ),
            )

    # =====================================================
    # CANCELAMENTO
    # =====================================================

    def cancelar_consulta(
        self,
        consulta_id,
    ):
        resposta = QMessageBox.question(
            self,
            "Cancelar consulta",
            (
                "Deseja realmente cancelar "
                "esta consulta?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if resposta != QMessageBox.Yes:
            return

        try:
            with app.app_context():
                try:
                    consulta = database.session.get(
                        Consulta,
                        consulta_id,
                    )

                    if consulta is None:
                        raise ValueError(
                            "Consulta não encontrada."
                        )

                    if (
                        consulta.usuario_id
                        != self.usuario_id
                    ):
                        raise PermissionError(
                            "Você não pode cancelar "
                            "esta consulta."
                        )

                    if (
                        consulta.status
                        != CONSULTA_AGENDADA
                    ):
                        raise ValueError(
                            "Apenas consultas agendadas "
                            "podem ser canceladas."
                        )

                    horario = datetime.strptime(
                        consulta.horario,
                        "%H:%M",
                    ).time()

                    momento_consulta = (
                        datetime.combine(
                            consulta.data,
                            horario,
                        )
                    )

                    if (
                        momento_consulta
                        <= datetime.now()
                    ):
                        raise ValueError(
                            "Não é possível cancelar "
                            "uma consulta que já passou."
                        )

                    consulta.status = (
                        CONSULTA_CANCELADA
                    )

                    database.session.commit()

                except Exception:
                    database.session.rollback()
                    raise

            QMessageBox.information(
                self,
                "Consulta cancelada",
                (
                    "A consulta foi cancelada "
                    "com sucesso."
                ),
            )

            self.recarregar()

        except (
            ValueError,
            PermissionError,
        ) as erro:
            QMessageBox.warning(
                self,
                "Não foi possível cancelar",
                str(erro),
            )

        except Exception as erro:
            print(
                "ERRO AO CANCELAR CONSULTA:",
                erro,
            )

            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível cancelar "
                    "a consulta."
                ),
            )


def tela_agendamentos(usuario):
    return TelaAgendamentos(usuario)