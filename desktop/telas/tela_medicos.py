import os

from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QFormLayout,
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
from projetoafgmed.models import (
    Consulta,
    Medico,
    Usuario,
)


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

PASTA_MEDICOS = os.path.join(
    BASE_DIR,
    "projetoafgmed",
    "static",
    "fotos_medicos",
)

HORARIOS = [
    "09:00",
    "10:00",
    "11:00",
    "14:00",
    "15:00",
    "16:00",
]


class TelaMedicos(QWidget):
    def __init__(self, usuario=None):
        super().__init__()

        self.usuario = usuario

        self.usuario_id = (
            usuario.id
            if usuario is not None
            else None
        )

        self.cards = []
        self.grid = None
        self.quantidade_colunas = 0

        self.setObjectName("paginaMedicos")

        aplicar_estilo(
            self,
            "medicos.qss",
        )

        layout_principal = QVBoxLayout(self)

        layout_principal.setContentsMargins(
            24,
            20,
            24,
            24,
        )

        layout_principal.setSpacing(16)

        # ==========================================
        # CABEÇALHO
        # ==========================================

        cabecalho = QHBoxLayout()

        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(3)

        titulo = QLabel(
            "Especialistas disponíveis"
        )

        titulo.setObjectName(
            "tituloPagina"
        )

        subtitulo = QLabel(
            "Escolha um profissional, uma data "
            "e um horário para a consulta."
        )

        subtitulo.setObjectName(
            "subtituloPagina"
        )

        area_titulo.addWidget(titulo)
        area_titulo.addWidget(subtitulo)

        botao_atualizar = QPushButton(
            "Atualizar"
        )

        botao_atualizar.setObjectName(
            "botaoSecundario"
        )

        botao_atualizar.setMinimumHeight(42)
        botao_atualizar.setMinimumWidth(90)

        botao_atualizar.clicked.connect(
            self.recarregar
        )

        cabecalho.addLayout(area_titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(botao_atualizar)

        # ==========================================
        # ÁREA DE ROLAGEM
        # ==========================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)

        self.scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        layout_principal.addLayout(cabecalho)
        layout_principal.addWidget(self.scroll)

        self.recarregar()

    def recarregar(self):
        container = QWidget()

        container.setObjectName(
            "containerMedicos"
        )

        self.grid = QGridLayout(container)

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

        self.cards = []
        self.quantidade_colunas = 0

        if self.usuario_id is None:
            mensagem = QLabel(
                "Não foi possível identificar "
                "o usuário conectado."
            )

            mensagem.setObjectName(
                "mensagemErro"
            )

            mensagem.setAlignment(
                Qt.AlignCenter
            )

            self.grid.addWidget(
                mensagem,
                0,
                0,
            )

            self.scroll.setWidget(container)
            return

        try:
            with app.app_context():
                medicos_banco = (
                    Medico.query
                    .order_by(
                        Medico.nome.asc(),
                        Medico.sobrenome.asc(),
                    )
                    .all()
                )

                medicos = [
                    {
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
                    for medico in medicos_banco
                ]

        except Exception as erro:
            mensagem = QLabel(
                "Não foi possível carregar os médicos."
                f"\n\n{erro}"
            )

            mensagem.setObjectName(
                "mensagemErro"
            )

            mensagem.setWordWrap(True)

            mensagem.setAlignment(
                Qt.AlignCenter
            )

            self.grid.addWidget(
                mensagem,
                0,
                0,
            )

            self.scroll.setWidget(container)
            return

        if not medicos:
            mensagem = QLabel(
                "Nenhum médico disponível no momento."
            )

            mensagem.setObjectName(
                "mensagemVazia"
            )

            mensagem.setAlignment(
                Qt.AlignCenter
            )

            self.grid.addWidget(
                mensagem,
                0,
                0,
            )

            self.scroll.setWidget(container)
            return

        for medico in medicos:
            card = self.criar_card_medico(
                medico
            )

            self.cards.append(card)

        self.scroll.setWidget(container)

        QTimer.singleShot(
            0,
            self.reorganizar_cards,
        )

    def criar_card_medico(self, medico):
        card = QFrame()
        card.setObjectName("medicoCard")

        card.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )

        card.setMinimumHeight(500)
        card.setMaximumHeight(500)

        layout_card = QVBoxLayout(card)

        layout_card.setContentsMargins(
            18,
            16,
            18,
            18,
        )

        layout_card.setSpacing(12)

        # ==========================================
        # ESPECIALIDADE
        # ==========================================

        cabecalho_card = QHBoxLayout()

        badge = QLabel(
            medico["especialidade"]
            or "Especialista"
        )

        badge.setObjectName(
            "badgeEspecialidade"
        )

        cabecalho_card.addWidget(
            badge,
            alignment=Qt.AlignLeft,
        )

        cabecalho_card.addStretch()

        # ==========================================
        # FOTO
        # ==========================================

        area_foto = QFrame()

        area_foto.setObjectName(
            "areaFotoMedico"
        )

        area_foto.setFixedHeight(185)

        layout_foto = QVBoxLayout(
            area_foto
        )

        layout_foto.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        foto = QLabel()

        foto.setObjectName(
            "fotoMedico"
        )

        foto.setAlignment(
            Qt.AlignCenter
        )

        caminho_foto = ""

        if medico["foto"]:
            caminho_foto = os.path.join(
                PASTA_MEDICOS,
                medico["foto"],
            )

        if (
            caminho_foto
            and os.path.exists(caminho_foto)
        ):
            imagem = QPixmap(caminho_foto)

            if not imagem.isNull():
                foto.setPixmap(
                    imagem.scaled(
                        210,
                        155,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
            else:
                foto.setText(
                    "Foto indisponível"
                )
        else:
            foto.setText(
                "Foto indisponível"
            )

        layout_foto.addWidget(foto)

        # ==========================================
        # DADOS
        # ==========================================

        nome_completo = (
            f"{medico['nome']} "
            f"{medico['sobrenome']}"
        ).strip()

        nome = QLabel(
            nome_completo or "Médico"
        )

        nome.setObjectName(
            "nomeMedico"
        )

        nome.setWordWrap(True)

        especialidade = QLabel(
            medico["especialidade"]
            or "Especialidade não informada"
        )

        especialidade.setObjectName(
            "especialidadeMedico"
        )

        informacao = QLabel(
            "Atendimento mediante agendamento "
            "de data e horário."
        )

        informacao.setObjectName(
            "informacaoMedico"
        )

        informacao.setWordWrap(True)
        informacao.setMinimumHeight(42)

        painel = QFrame()

        painel.setObjectName(
            "painelDisponibilidade"
        )

        layout_painel = QVBoxLayout(painel)

        layout_painel.setContentsMargins(
            13,
            10,
            13,
            10,
        )

        disponibilidade = QLabel(
            "Horários disponíveis pela manhã e tarde"
        )

        disponibilidade.setObjectName(
            "textoDisponibilidade"
        )

        disponibilidade.setWordWrap(True)

        layout_painel.addWidget(
            disponibilidade
        )

        botao = QPushButton(
            "Agendar consulta"
        )

        botao.setObjectName(
            "botaoAgendar"
        )

        botao.setMinimumHeight(48)

        botao.clicked.connect(
            lambda checked=False,
            medico_dados=medico:
            abrir_agendamento(
                self.usuario_id,
                medico_dados,
            )
        )

        layout_card.addLayout(cabecalho_card)
        layout_card.addWidget(area_foto)
        layout_card.addWidget(nome)
        layout_card.addWidget(especialidade)
        layout_card.addWidget(informacao)
        layout_card.addStretch()
        layout_card.addWidget(painel)
        layout_card.addWidget(botao)

        return card

    def reorganizar_cards(self):
        if self.grid is None or not self.cards:
            return

        largura = self.scroll.viewport().width()
        espacamento = self.grid.horizontalSpacing()

        if largura >= 1030:
            colunas = 3
        elif largura >= 680:
            colunas = 2
        else:
            colunas = 1

        largura_util = (
            largura
            - ((colunas - 1) * espacamento)
            - 8
        )

        largura_card = largura_util // colunas

        largura_card = max(
            285,
            min(360, largura_card),
        )

        self.quantidade_colunas = colunas

        while self.grid.count():
            self.grid.takeAt(0)

        self.grid.setAlignment(
            Qt.AlignTop | Qt.AlignLeft
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


def abrir_agendamento(
    usuario_id,
    medico,
):
    janela = QDialog()

    janela.setObjectName(
        "dialogoAgendamento"
    )

    janela.setWindowTitle(
        "Agendar consulta"
    )

    janela.resize(
        570,
        400,
    )

    aplicar_estilo(
        janela,
        "medicos.qss",
    )

    layout = QFormLayout(janela)

    layout.setContentsMargins(
        24,
        24,
        24,
        24,
    )

    layout.setSpacing(16)

    nome_completo = (
        f"{medico['nome']} "
        f"{medico['sobrenome']}"
    ).strip()

    nome_medico = QLabel(
        nome_completo or "Médico"
    )

    nome_medico.setObjectName(
        "nomeDialogoMedico"
    )

    especialidade = QLabel(
        medico["especialidade"]
        or "Especialidade não informada"
    )

    especialidade.setObjectName(
        "especialidadeDialogo"
    )

    profissional_widget = QWidget()

    profissional_layout = QVBoxLayout(
        profissional_widget
    )

    profissional_layout.setContentsMargins(
        0,
        0,
        0,
        0,
    )

    profissional_layout.setSpacing(2)

    profissional_layout.addWidget(
        nome_medico
    )

    profissional_layout.addWidget(
        especialidade
    )

    data = QDateEdit()

    data.setCalendarPopup(True)

    data.setDisplayFormat(
        "dd/MM/yyyy"
    )

    data.setDate(
        QDate.currentDate()
    )

    data.setMinimumDate(
        QDate.currentDate()
    )

    horario_escolhido = {
        "valor": None
    }

    botoes_horarios = {}

    horarios_widget = QWidget()

    horarios_layout = QGridLayout(
        horarios_widget
    )

    horarios_layout.setContentsMargins(
        0,
        0,
        0,
        0,
    )

    horarios_layout.setHorizontalSpacing(8)
    horarios_layout.setVerticalSpacing(8)

    for indice, horario in enumerate(
        HORARIOS
    ):
        botao = QPushButton(horario)

        botao.setObjectName(
            "botaoHorario"
        )

        botao.setCheckable(True)
        botao.setMinimumHeight(40)

        botoes_horarios[horario] = botao

        linha = indice // 3
        coluna = indice % 3

        horarios_layout.addWidget(
            botao,
            linha,
            coluna,
        )

        botao.clicked.connect(
            lambda checked=False,
            horario_atual=horario:
            selecionar_horario(
                horario_atual,
                horario_escolhido,
                botoes_horarios,
            )
        )

    salvar = QPushButton(
        "Confirmar consulta"
    )

    salvar.setObjectName(
        "botaoConfirmarConsulta"
    )

    salvar.setMinimumHeight(46)

    layout.addRow(
        "Profissional:",
        profissional_widget,
    )

    layout.addRow(
        "Data:",
        data,
    )

    layout.addRow(
        "Horário:",
        horarios_widget,
    )

    layout.addWidget(salvar)

    def atualizar_horarios():
        horario_escolhido["valor"] = None

        data_escolhida = (
            data.date().toPython()
        )

        with app.app_context():
            consultas = (
                Consulta.query.filter_by(
                    medico_id=medico["id"],
                    data=data_escolhida,
                    status="agendada",
                ).all()
            )

            ocupados = {
                consulta.horario
                for consulta in consultas
            }

        for horario, botao in (
            botoes_horarios.items()
        ):
            ocupado = horario in ocupados

            botao.setChecked(False)
            botao.setEnabled(
                not ocupado
            )

            if ocupado:
                botao.setText(
                    f"{horario} ocupado"
                )
            else:
                botao.setText(horario)

    def confirmar():
        horario = horario_escolhido[
            "valor"
        ]

        if not horario:
            QMessageBox.warning(
                janela,
                "Escolha um horário",
                "Selecione um horário disponível.",
            )
            return

        salvar.setEnabled(False)

        salvar.setText(
            "Salvando consulta..."
        )

        try:
            with app.app_context():
                try:
                    usuario_existe = (
                        Usuario.query.filter_by(
                            id=usuario_id
                        ).first()
                    )

                    if usuario_existe is None:
                        raise ValueError(
                            "O usuário conectado não "
                            "existe no banco."
                        )

                    data_python = (
                        data.date().toPython()
                    )

                    consulta_existente = (
                        Consulta.query.filter_by(
                            medico_id=medico["id"],
                            data=data_python,
                            horario=horario,
                            status="agendada",
                        ).first()
                    )

                    if consulta_existente:
                        raise ValueError(
                            "Este horário já foi reservado."
                        )

                    consulta = Consulta(
                        medico_id=medico["id"],
                        usuario_id=usuario_id,
                        data=data_python,
                        horario=horario,
                        status="agendada",
                    )

                    database.session.add(
                        consulta
                    )

                    database.session.commit()

                except Exception:
                    database.session.rollback()
                    raise

            QMessageBox.information(
                janela,
                "Consulta agendada",
                (
                    "Sua consulta foi agendada "
                    "com sucesso."
                ),
            )

            janela.accept()

        except ValueError as erro:
            QMessageBox.warning(
                janela,
                "Não foi possível agendar",
                str(erro),
            )

            atualizar_horarios()

        except Exception as erro:
            QMessageBox.critical(
                janela,
                "Erro",
                (
                    "Não foi possível salvar "
                    f"a consulta.\n\n{erro}"
                ),
            )

        finally:
            salvar.setEnabled(True)

            salvar.setText(
                "Confirmar consulta"
            )

    data.dateChanged.connect(
        atualizar_horarios
    )

    salvar.clicked.connect(
        confirmar
    )

    atualizar_horarios()
    janela.exec()


def selecionar_horario(
    horario,
    controle,
    botoes,
):
    botao_escolhido = botoes.get(
        horario
    )

    if (
        botao_escolhido is None
        or not botao_escolhido.isEnabled()
    ):
        return

    controle["valor"] = horario

    for horario_atual, botao in (
        botoes.items()
    ):
        botao.setChecked(
            horario_atual == horario
        )


def tela_medicos(usuario=None):
    return TelaMedicos(usuario)