import os

from PySide6.QtCore import (
    QDate,
    Qt,
    QTimer,
)

from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from desktop.estilos import aplicar_estilo

from projetoafgmed import (
    app,
    database,
)

from projetoafgmed.models import (
    Consulta,
    Medico,
    Usuario,
)

from projetoafgmed.servicos_consultas import (
    ErroConsulta,
    HORARIOS_CONSULTA,
    horarios_indisponiveis_por_tempo,
    horarios_ocupados_medico,
    salvar_consulta,
)

from projetoafgmed.status import (
    CONSULTA_AGENDADA,
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

HORARIOS = list(
    HORARIOS_CONSULTA
)


class TelaMedicos(QWidget):
    def __init__(self, usuario=None):
        super().__init__()

        self.usuario = usuario

        self.usuario_id = (
            usuario.id
            if usuario is not None
            else None
        )

        self.medicos = []
        self.cards = []
        self.grid = None
        self.container = None
        self.mensagem_filtro = None
        self.quantidade_colunas = 0

        self.setObjectName(
            "paginaMedicos"
        )

        aplicar_estilo(
            self,
            "medicos.qss",
        )

        layout_principal = QVBoxLayout(
            self
        )

        layout_principal.setContentsMargins(
            24,
            20,
            24,
            24,
        )

        layout_principal.setSpacing(16)

        # =================================================
        # CABEÇALHO
        # =================================================

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
            (
                "Escolha um profissional, "
                "uma data e um horário "
                "para a consulta."
            )
        )

        subtitulo.setObjectName(
            "subtituloPagina"
        )

        area_titulo.addWidget(titulo)
        area_titulo.addWidget(subtitulo)

        self.busca = QLineEdit()

        self.busca.setObjectName(
            "campoBuscaMedicos"
        )

        self.busca.setPlaceholderText(
            (
                "Buscar médico por "
                "especialidade..."
            )
        )

        self.busca.setClearButtonEnabled(
            True
        )

        self.busca.setMinimumWidth(290)
        self.busca.setMaximumWidth(400)

        self.busca.textChanged.connect(
            self.aplicar_filtro
        )

        botao_atualizar = QPushButton(
            "Atualizar"
        )

        botao_atualizar.setObjectName(
            "botaoSecundario"
        )

        botao_atualizar.setMinimumHeight(
            42
        )

        botao_atualizar.setMinimumWidth(
            90
        )

        botao_atualizar.clicked.connect(
            self.recarregar
        )

        cabecalho.addLayout(area_titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(self.busca)
        cabecalho.addWidget(
            botao_atualizar
        )

        # =================================================
        # ÁREA DE ROLAGEM
        # =================================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)

        self.scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        layout_principal.addLayout(
            cabecalho
        )

        layout_principal.addWidget(
            self.scroll
        )

        self.recarregar()

    # =====================================================
    # CONTAINER
    # =====================================================

    def _criar_container(self):
        self.container = QWidget()

        self.container.setObjectName(
            "containerMedicos"
        )

        self.grid = QGridLayout(
            self.container
        )

        self.grid.setContentsMargins(
            0,
            0,
            0,
            14,
        )

        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(18)

        self.grid.setAlignment(
            Qt.AlignTop
        )

        self.scroll.setWidget(
            self.container
        )

    # =====================================================
    # CARREGAMENTO
    # =====================================================

    def recarregar(self):
        self._criar_container()

        self.cards = []
        self.medicos = []
        self.quantidade_colunas = 0

        if self.usuario_id is None:
            self._mostrar_mensagem(
                (
                    "Não foi possível identificar "
                    "o usuário conectado."
                ),
                "mensagemErro",
            )

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

                self.medicos = [
                    {
                        "id": medico.id,
                        "nome": (
                            medico.nome or ""
                        ),
                        "sobrenome": (
                            medico.sobrenome or ""
                        ),
                        "especialidade": (
                            medico.especialidade
                            or ""
                        ),
                        "foto": (
                            medico.foto or ""
                        ),
                    }
                    for medico
                    in medicos_banco
                ]

        except Exception as erro:
            self._mostrar_mensagem(
                (
                    "Não foi possível carregar "
                    "os médicos.\n\n"
                    f"{erro}"
                ),
                "mensagemErro",
            )

            return

        if not self.medicos:
            self._mostrar_mensagem(
                (
                    "Nenhum médico disponível "
                    "no momento."
                ),
                "mensagemVazia",
            )

            return

        for medico in self.medicos:
            card = self.criar_card_medico(
                medico
            )

            card.setProperty(
                "especialidadeBusca",
                medico[
                    "especialidade"
                ].casefold(),
            )

            self.cards.append(card)

        self.aplicar_filtro()

    # =====================================================
    # MENSAGEM
    # =====================================================

    def _mostrar_mensagem(
        self,
        texto,
        object_name="mensagemVazia",
    ):
        mensagem = QLabel(texto)

        mensagem.setObjectName(
            object_name
        )

        mensagem.setWordWrap(True)

        mensagem.setAlignment(
            Qt.AlignCenter
        )

        self.grid.addWidget(
            mensagem,
            0,
            0,
            1,
            4,
        )

        self.mensagem_filtro = mensagem

    # =====================================================
    # FILTRO
    # =====================================================

    def aplicar_filtro(self):
        if self.grid is None:
            return

        termo = (
            self.busca.text()
            .strip()
            .casefold()
        )

        if self.mensagem_filtro is not None:
            self.mensagem_filtro.deleteLater()
            self.mensagem_filtro = None

        cards_visiveis = []

        for card in self.cards:
            especialidade = str(
                card.property(
                    "especialidadeBusca"
                )
                or ""
            )

            visivel = (
                not termo
                or termo in especialidade
            )

            card.setVisible(False)

            if visivel:
                cards_visiveis.append(
                    card
                )

        self.reorganizar_cards(
            cards_visiveis
        )

        if (
            self.cards
            and not cards_visiveis
        ):
            self._mostrar_mensagem(
                (
                    "Nenhum médico encontrado "
                    "para essa especialidade."
                ),
                "mensagemVazia",
            )

    # =====================================================
    # CARD DO MÉDICO
    # =====================================================

    def criar_card_medico(
        self,
        medico,
    ):
        card = QFrame(self.container)

        card.setObjectName(
            "medicoCard"
        )

        card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        # Permite que o card ocupe
        # toda a largura da coluna.
        card.setMinimumWidth(0)
        card.setMaximumWidth(16777215)

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

        # =================================================
        # ESPECIALIDADE
        # =================================================

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

        # =================================================
        # FOTO
        # =================================================

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

        caminho_foto = (
            os.path.join(
                PASTA_MEDICOS,
                medico["foto"],
            )
            if medico["foto"]
            else ""
        )

        if (
            caminho_foto
            and os.path.exists(
                caminho_foto
            )
        ):
            imagem = QPixmap(
                caminho_foto
            )

            if not imagem.isNull():
                foto.setPixmap(
                    imagem.scaled(
                        250,
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

        # =================================================
        # DADOS
        # =================================================

        nome_completo = (
            f"{medico['nome']} "
            f"{medico['sobrenome']}"
        ).strip()

        nome = QLabel(
            nome_completo
            or "Médico"
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

        especialidade.setWordWrap(True)

        informacao = QLabel(
            (
                "Atendimento mediante "
                "agendamento de data "
                "e horário."
            )
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

        layout_painel = QVBoxLayout(
            painel
        )

        layout_painel.setContentsMargins(
            13,
            10,
            13,
            10,
        )

        disponibilidade = QLabel(
            (
                "Horários disponíveis "
                "pela manhã e tarde"
            )
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
            medico_dados=medico: (
                abrir_agendamento(
                    self.usuario_id,
                    medico_dados,
                    parent=self,
                )
            )
        )

        layout_card.addLayout(
            cabecalho_card
        )

        layout_card.addWidget(
            area_foto
        )

        layout_card.addWidget(nome)

        layout_card.addWidget(
            especialidade
        )

        layout_card.addWidget(
            informacao
        )

        layout_card.addStretch()

        layout_card.addWidget(painel)
        layout_card.addWidget(botao)

        return card

    # =====================================================
    # ORGANIZAÇÃO RESPONSIVA
    # =====================================================

    def reorganizar_cards(
        self,
        cards=None,
    ):
        if self.grid is None:
            return

        cards = (
            self.cards
            if cards is None
            else cards
        )

        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()

            if (
                widget is not None
                and widget not in self.cards
            ):
                widget.deleteLater()

        if not cards:
            return

        largura = (
            self.scroll.viewport().width()
        )

        if largura >= 1450:
            colunas = 4

        elif largura >= 960:
            colunas = 3

        elif largura >= 620:
            colunas = 2

        else:
            colunas = 1

        self.quantidade_colunas = (
            colunas
        )

        self.grid.setAlignment(
            Qt.AlignTop
        )

        for coluna in range(4):
            self.grid.setColumnStretch(
                coluna,
                1 if coluna < colunas else 0,
            )

        for indice, card in enumerate(
            cards
        ):
            linha = indice // colunas
            coluna = indice % colunas

            card.setMinimumWidth(0)
            card.setMaximumWidth(16777215)

            card.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed,
            )

            card.setVisible(True)

            self.grid.addWidget(
                card,
                linha,
                coluna,
            )

    def resizeEvent(self, evento):
        super().resizeEvent(evento)

        QTimer.singleShot(
            0,
            self.aplicar_filtro,
        )


# =========================================================
# AGENDAMENTO E REAGENDAMENTO
# =========================================================

def abrir_agendamento(
    usuario_id,
    medico,
    consulta_id=None,
    parent=None,
):
    janela = QDialog(parent)

    reagendando = (
        consulta_id is not None
    )

    janela.setObjectName(
        "dialogoAgendamento"
    )

    janela.setWindowTitle(
        (
            "Reagendar consulta"
            if reagendando
            else "Agendar consulta"
        )
    )

    janela.resize(570, 400)

    aplicar_estilo(
        janela,
        "medicos.qss",
    )

    consulta_atual = None

    if reagendando:
        try:
            with app.app_context():
                consulta = (
                    database.session.get(
                        Consulta,
                        consulta_id,
                    )
                )

                if consulta is None:
                    raise ValueError(
                        "Consulta não encontrada."
                    )

                if (
                    consulta.usuario_id
                    != usuario_id
                ):
                    raise ValueError(
                        (
                            "Você não pode "
                            "reagendar esta consulta."
                        )
                    )

                if (
                    consulta.status
                    != CONSULTA_AGENDADA
                ):
                    raise ValueError(
                        (
                            "Apenas consultas agendadas "
                            "podem ser reagendadas."
                        )
                    )

                consulta_atual = {
                    "data": consulta.data,
                    "horario": (
                        consulta.horario
                    ),
                    "medico_id": (
                        consulta.medico_id
                    ),
                }

                if (
                    consulta.medico_id
                    != medico["id"]
                ):
                    raise ValueError(
                        (
                            "O médico da consulta "
                            "não corresponde."
                        )
                    )

        except Exception as erro:
            QMessageBox.warning(
                parent,
                (
                    "Não foi possível "
                    "reagendar"
                ),
                str(erro),
            )

            return False

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

    data.setMinimumDate(
        QDate.currentDate()
    )

    if (
        consulta_atual
        and consulta_atual["data"]
    ):
        data_original = QDate(
            consulta_atual["data"].year,
            consulta_atual["data"].month,
            consulta_atual["data"].day,
        )

        data.setDate(
            (
                data_original
                if data_original
                >= QDate.currentDate()
                else QDate.currentDate()
            )
        )

    else:
        data.setDate(
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

    horarios_layout.setHorizontalSpacing(
        8
    )

    horarios_layout.setVerticalSpacing(
        8
    )

    for indice, horario in enumerate(
        HORARIOS
    ):
        botao = QPushButton(horario)

        botao.setObjectName(
            "botaoHorario"
        )

        botao.setCheckable(True)
        botao.setMinimumHeight(40)

        botoes_horarios[
            horario
        ] = botao

        horarios_layout.addWidget(
            botao,
            indice // 3,
            indice % 3,
        )

        botao.clicked.connect(
            lambda checked=False,
            horario_atual=horario: (
                selecionar_horario(
                    horario_atual,
                    horario_escolhido,
                    botoes_horarios,
                )
            )
        )

    salvar = QPushButton(
        (
            "Confirmar reagendamento"
            if reagendando
            else "Confirmar consulta"
        )
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
        horario_escolhido[
            "valor"
        ] = None

        data_escolhida = (
            data.date().toPython()
        )

        with app.app_context():
            ocupados = (
                horarios_ocupados_medico(
                    medico_id=medico["id"],
                    data_consulta=(
                        data_escolhida
                    ),
                    consulta_id=consulta_id,
                )
            )

        horarios_passados = (
            horarios_indisponiveis_por_tempo(
                data_escolhida,
                HORARIOS,
            )
        )

        for (
            horario,
            botao,
        ) in botoes_horarios.items():
            ocupado = (
                horario in ocupados
            )

            horario_passado = (
                horario
                in horarios_passados
            )

            indisponivel = (
                ocupado
                or horario_passado
            )

            botao.setChecked(False)

            botao.setEnabled(
                not indisponivel
            )

            if horario_passado:
                botao.setText(
                    f"{horario} encerrado"
                )

                botao.setToolTip(
                    "Esse horário já passou."
                )

            elif ocupado:
                botao.setText(
                    f"{horario} ocupado"
                )

                botao.setToolTip(
                    (
                        "Esse horário já "
                        "está reservado."
                    )
                )

            else:
                botao.setText(horario)

                botao.setToolTip(
                    "Horário disponível."
                )

        if (
            consulta_atual
            and data_escolhida
            == consulta_atual["data"]
            and consulta_atual["horario"]
            not in ocupados
        ):
            selecionar_horario(
                consulta_atual["horario"],
                horario_escolhido,
                botoes_horarios,
            )

    def confirmar():
        horario = horario_escolhido[
            "valor"
        ]

        if not horario:
            QMessageBox.warning(
                janela,
                "Escolha um horário",
                (
                    "Selecione um horário "
                    "disponível."
                ),
            )

            return

        salvar.setEnabled(False)

        salvar.setText(
            (
                "Reagendando..."
                if reagendando
                else "Salvando consulta..."
            )
        )

        try:
            with app.app_context():
                usuario_existe = (
                    database.session.get(
                        Usuario,
                        usuario_id,
                    )
                )

                if usuario_existe is None:
                    raise ErroConsulta(
                        (
                            "O usuário conectado "
                            "não existe no banco."
                        )
                    )

                data_python = (
                    data.date().toPython()
                )

                salvar_consulta(
                    medico_id=medico["id"],
                    usuario_id=usuario_id,
                    data_consulta=(
                        data_python
                    ),
                    horario=horario,
                    consulta_id=consulta_id,
                )

            QMessageBox.information(
                janela,
                (
                    "Consulta reagendada"
                    if reagendando
                    else "Consulta agendada"
                ),
                (
                    (
                        "Sua consulta foi "
                        "reagendada com sucesso."
                    )
                    if reagendando
                    else (
                        "Sua consulta foi "
                        "agendada com sucesso."
                    )
                ),
            )

            janela.accept()

        except ErroConsulta as erro:
            QMessageBox.warning(
                janela,
                (
                    "Não foi possível "
                    "reagendar"
                    if reagendando
                    else (
                        "Não foi possível "
                        "agendar"
                    )
                ),
                str(erro),
            )

            atualizar_horarios()

        except Exception as erro:
            print(
                "ERRO AO SALVAR CONSULTA:",
                erro,
            )

            QMessageBox.critical(
                janela,
                "Erro",
                (
                    "Não foi possível salvar "
                    "a consulta. Tente novamente."
                ),
            )

        finally:
            salvar.setEnabled(True)

            salvar.setText(
                (
                    "Confirmar reagendamento"
                    if reagendando
                    else "Confirmar consulta"
                )
            )

    data.dateChanged.connect(
        atualizar_horarios
    )

    salvar.clicked.connect(
        confirmar
    )

    atualizar_horarios()

    return (
        janela.exec()
        == QDialog.Accepted
    )


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

    for (
        horario_atual,
        botao,
    ) in botoes.items():
        botao.setChecked(
            horario_atual == horario
        )


def tela_medicos(usuario=None):
    return TelaMedicos(usuario)