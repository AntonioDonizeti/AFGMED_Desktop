import unicodedata
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop.estilos import aplicar_estilo
from projetoafgmed import app, database
from projetoafgmed.models import Consulta, Medico
from projetoafgmed.status import (
    CONSULTA_AGENDADA,
    CONSULTA_CANCELADA,
    CONSULTA_CONCLUIDA,
)


def normalizar_busca(valor):
    texto = unicodedata.normalize(
        "NFKD",
        str(valor or ""),
    )

    return "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    ).casefold().strip()


class TelaConsultasMedico(QWidget):
    def __init__(self, usuario):
        super().__init__()

        self.usuario = usuario
        self.medico_id = getattr(
            usuario,
            "id_medico",
            None,
        )

        self.setObjectName(
            "paginaConsultasMedico"
        )

        aplicar_estilo(
            self,
            "consultas_medico.qss",
        )

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(
            26,
            22,
            26,
            26,
        )
        layout_principal.setSpacing(18)

        # ==================================================
        # CABEÇALHO
        # ==================================================

        cabecalho = QHBoxLayout()

        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(2)

        titulo = QLabel("Minhas consultas")
        titulo.setObjectName("tituloPagina")

        self.subtitulo = QLabel(
            "Acompanhe seus pacientes e atualize "
            "os atendimentos agendados."
        )
        self.subtitulo.setObjectName(
            "subtituloPagina"
        )
        self.subtitulo.setWordWrap(True)

        area_titulo.addWidget(titulo)
        area_titulo.addWidget(self.subtitulo)

        self.busca = QLineEdit()
        self.busca.setObjectName(
            "campoBuscaConsultasMedico"
        )
        self.busca.setPlaceholderText(
            "Buscar paciente, e-mail, telefone ou data..."
        )
        self.busca.setClearButtonEnabled(True)
        self.busca.setMinimumWidth(290)
        self.busca.setMaximumWidth(410)
        self.busca.textChanged.connect(
            self.recarregar
        )

        self.filtro = QComboBox()
        self.filtro.addItem("Todas — abertas primeiro", "todas")
        self.filtro.addItem("Agendadas hoje", "hoje")
        self.filtro.addItem(
            "Agendadas",
            CONSULTA_AGENDADA,
        )
        self.filtro.addItem(
            "Concluídas",
            CONSULTA_CONCLUIDA,
        )
        self.filtro.addItem(
            "Canceladas",
            CONSULTA_CANCELADA,
        )
        self.filtro.currentIndexChanged.connect(
            self.recarregar
        )

        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(
            self.recarregar
        )

        cabecalho.addLayout(area_titulo, 1)
        cabecalho.addWidget(self.busca)
        cabecalho.addWidget(self.filtro)
        cabecalho.addWidget(atualizar)

        # ==================================================
        # MÉTRICAS
        # ==================================================

        self.resumo = QFrame()
        self.resumo.setObjectName(
            "resumoConsultasMedico"
        )
        self.resumo.setFixedHeight(96)

        self.layout_resumo = QHBoxLayout(
            self.resumo
        )
        self.layout_resumo.setContentsMargins(
            16,
            14,
            16,
            14,
        )
        self.layout_resumo.setSpacing(12)

        # ==================================================
        # TABELA
        # ==================================================

        self.tabela = QTableWidget(0, 5)
        self.tabela.setObjectName(
            "tabelaConsultasMedico"
        )

        self.tabela.setHorizontalHeaderLabels(
            [
                "ID",
                "Paciente",
                "Data",
                "Horário",
                "Status",
            ]
        )

        self.tabela.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.tabela.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.tabela.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.tabela.verticalHeader().setVisible(
            False
        )
        self.tabela.verticalHeader().setDefaultSectionSize(38)
        self.tabela.setAlternatingRowColors(True)

        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.Stretch,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeToContents,
        )

        self.tabela.itemSelectionChanged.connect(
            self.atualizar_detalhes
        )

        # ==================================================
        # PAINEL LATERAL
        # ==================================================

        self.painel_detalhes = (
            self._criar_painel_detalhes()
        )

        area_conteudo = QHBoxLayout()
        area_conteudo.setSpacing(16)

        area_conteudo.addWidget(
            self.tabela,
            4,
        )
        area_conteudo.addWidget(
            self.painel_detalhes,
            1,
        )

        layout_principal.addLayout(cabecalho)
        layout_principal.addWidget(self.resumo)
        layout_principal.addLayout(
            area_conteudo,
            1,
        )

        self.recarregar()

    # =====================================================
    # PAINEL DE DETALHES
    # =====================================================

    def _criar_painel_detalhes(self):
        painel = QFrame()
        painel.setObjectName(
            "painelDetalhesConsultaMedico"
        )
        painel.setMinimumWidth(300)
        painel.setMaximumWidth(345)

        layout = QVBoxLayout(painel)
        layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )
        layout.setSpacing(8)

        titulo = QLabel("Detalhes da consulta")
        titulo.setObjectName(
            "tituloPainelConsultaMedico"
        )

        self.paciente_detalhe = QLabel(
            "Nenhuma consulta selecionada"
        )
        self.paciente_detalhe.setObjectName(
            "nomePacienteConsultaMedico"
        )
        self.paciente_detalhe.setWordWrap(True)

        self.status_detalhe = QLabel("Selecione")
        self.status_detalhe.setObjectName(
            "statusConsultaMedico"
        )
        self.status_detalhe.setAlignment(
            Qt.AlignCenter
        )

        self.id_detalhe = QLabel(
            "Consulta: —"
        )
        self.data_detalhe = QLabel(
            "Data: —"
        )
        self.horario_detalhe = QLabel(
            "Horário: —"
        )
        self.email_detalhe = QLabel(
            "E-mail: —"
        )
        self.telefone_detalhe = QLabel(
            "Telefone: —"
        )

        for label in (
            self.id_detalhe,
            self.data_detalhe,
            self.horario_detalhe,
            self.email_detalhe,
            self.telefone_detalhe,
        ):
            label.setObjectName(
                "linhaDetalheConsultaMedico"
            )
            label.setWordWrap(True)
            label.setMinimumHeight(34)
            label.setMaximumHeight(42)

        self.aviso_detalhe = QLabel(
            "Selecione uma consulta na tabela "
            "para visualizar os dados do paciente."
        )
        self.aviso_detalhe.setObjectName(
            "avisoConsultaMedico"
        )
        self.aviso_detalhe.setWordWrap(True)
        self.aviso_detalhe.setMinimumHeight(36)
        self.aviso_detalhe.setMaximumHeight(52)

        self.botao_concluir = QPushButton(
            "Concluir consulta"
        )
        self.botao_concluir.setObjectName(
            "botaoConcluirConsultaMedico"
        )
        self.botao_concluir.clicked.connect(
            self.concluir_selecionada
        )


        layout.addWidget(titulo)
        layout.addWidget(self.paciente_detalhe)
        layout.addWidget(self.status_detalhe)
        layout.addWidget(self.id_detalhe)
        layout.addWidget(self.data_detalhe)
        layout.addWidget(self.horario_detalhe)
        layout.addWidget(self.email_detalhe)
        layout.addWidget(self.telefone_detalhe)
        layout.addWidget(self.aviso_detalhe)
        layout.addStretch()
        layout.addWidget(self.botao_concluir)

        self._habilitar_acoes(False)

        return painel

    def _habilitar_acoes(self, habilitado):
        self.botao_concluir.setEnabled(habilitado)
        self.botao_concluir.setVisible(habilitado)

    def limpar_detalhes(self):
        self.paciente_detalhe.setText(
            "Nenhuma consulta selecionada"
        )

        self.status_detalhe.setText(
            "Selecione"
        )
        self.status_detalhe.setProperty(
            "tipoStatus",
            "nenhum",
        )
        self._reaplicar_estilo(
            self.status_detalhe
        )

        self.id_detalhe.setText(
            "Consulta: —"
        )
        self.data_detalhe.setText(
            "Data: —"
        )
        self.horario_detalhe.setText(
            "Horário: —"
        )
        self.email_detalhe.setText(
            "E-mail: —"
        )
        self.telefone_detalhe.setText(
            "Telefone: —"
        )
        self.aviso_detalhe.setText(
            "Selecione uma consulta na tabela "
            "para visualizar os dados do paciente."
        )

        self._habilitar_acoes(False)

    @staticmethod
    def _reaplicar_estilo(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    # =====================================================
    # MÉTRICAS
    # =====================================================

    def _limpar_resumo(self):
        while self.layout_resumo.count():
            item = self.layout_resumo.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _adicionar_metrica(
        self,
        titulo,
        valor,
        tipo,
    ):
        card = QFrame()
        card.setObjectName(
            "metricaConsultaMedico"
        )
        card.setProperty(
            "tipoMetrica",
            tipo,
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            14,
            10,
            14,
            10,
        )
        layout.setSpacing(1)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName(
            "rotuloMetricaConsulta"
        )

        label_valor = QLabel(str(valor))
        label_valor.setObjectName(
            "valorMetricaConsulta"
        )

        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)

        self.layout_resumo.addWidget(card, 1)

    # =====================================================
    # CARREGAMENTO
    # =====================================================

    def recarregar(self):
        id_anterior = (
            self.consulta_selecionada_id()
        )

        self.tabela.setRowCount(0)
        self._limpar_resumo()

        if not self.medico_id:
            self.subtitulo.setText(
                "Este usuário não está vinculado "
                "a um cadastro médico."
            )
            self.limpar_detalhes()
            return

        filtro = self.filtro.currentData()
        texto_busca = normalizar_busca(
            self.busca.text()
        )

        try:
            with app.app_context():
                medico = database.session.get(
                    Medico,
                    self.medico_id,
                )

                consultas_banco = (
                    Consulta.query
                    .filter_by(
                        medico_id=self.medico_id
                    )
                    .all()
                )

                abertas = sorted(
                    (
                        consulta
                        for consulta in consultas_banco
                        if consulta.status == CONSULTA_AGENDADA
                    ),
                    key=lambda consulta: (
                        consulta.data or date.max,
                        consulta.horario or "",
                    ),
                )

                encerradas = sorted(
                    (
                        consulta
                        for consulta in consultas_banco
                        if consulta.status != CONSULTA_AGENDADA
                    ),
                    key=lambda consulta: (
                        consulta.data or date.min,
                        consulta.horario or "",
                    ),
                    reverse=True,
                )

                todas = abertas + encerradas

                dados = []

                for consulta in todas:
                    status = (
                        consulta.status
                        or CONSULTA_AGENDADA
                    )

                    if filtro == "hoje":
                        if not (
                            status == CONSULTA_AGENDADA
                            and consulta.data == date.today()
                        ):
                            continue
                    elif (
                        filtro != "todas"
                        and status != filtro
                    ):
                        continue

                    usuario = consulta.usuario

                    if usuario:
                        paciente = (
                            f"{usuario.nome or ''} "
                            f"{usuario.sobrenome or ''}"
                        ).strip()

                        email = usuario.email or ""

                        perfil = getattr(
                            usuario,
                            "perfil",
                            None,
                        )

                        telefone = (
                            getattr(
                                perfil,
                                "telefone",
                                "",
                            )
                            or "—"
                        )
                    else:
                        paciente = (
                            "Paciente não encontrado"
                        )
                        email = "—"
                        telefone = "—"

                    data_texto = (
                        consulta.data.strftime(
                            "%d/%m/%Y"
                        )
                        if consulta.data
                        else "—"
                    )

                    chave_busca = normalizar_busca(
                        (
                            f"{consulta.id} "
                            f"{paciente} "
                            f"{data_texto} "
                            f"{consulta.horario or ''} "
                            f"{status} "
                            f"{email} "
                            f"{telefone}"
                        )
                    )

                    if (
                        texto_busca
                        and texto_busca
                        not in chave_busca
                    ):
                        continue

                    dados.append(
                        {
                            "id": consulta.id,
                            "paciente": paciente,
                            "data": consulta.data,
                            "horario": (
                                consulta.horario
                                or ""
                            ),
                            "status": status,
                            "email": email,
                            "telefone": telefone,
                        }
                    )

                hoje = date.today()

                metricas = {
                    "Hoje": sum(
                        1
                        for consulta in todas
                        if (
                            consulta.data == hoje
                            and consulta.status
                            == CONSULTA_AGENDADA
                        )
                    ),
                    "Agendadas": sum(
                        1
                        for consulta in todas
                        if consulta.status
                        == CONSULTA_AGENDADA
                    ),
                    "Concluídas": sum(
                        1
                        for consulta in todas
                        if consulta.status
                        == CONSULTA_CONCLUIDA
                    ),
                    "Canceladas": sum(
                        1
                        for consulta in todas
                        if consulta.status
                        == CONSULTA_CANCELADA
                    ),
                }

                nome_medico = (
                    (
                        f"{medico.nome or ''} "
                        f"{medico.sobrenome or ''}"
                    ).strip()
                    if medico
                    else "Médico"
                )

                especialidade = (
                    medico.especialidade
                    if medico
                    else ""
                )

            self.subtitulo.setText(
                (
                    f"Agenda de {nome_medico} • "
                    f"{especialidade or 'Especialidade não informada'}"
                )
            )

            self._adicionar_metrica(
                "Hoje",
                metricas["Hoje"],
                "hoje",
            )
            self._adicionar_metrica(
                "Agendadas",
                metricas["Agendadas"],
                "agendada",
            )
            self._adicionar_metrica(
                "Concluídas",
                metricas["Concluídas"],
                "concluida",
            )
            self._adicionar_metrica(
                "Canceladas",
                metricas["Canceladas"],
                "cancelada",
            )
            linha_selecionar = None

            for linha, consulta in enumerate(
                dados
            ):
                self.tabela.insertRow(linha)

                valores = [
                    consulta["id"],
                    consulta["paciente"],
                    (
                        consulta["data"].strftime(
                            "%d/%m/%Y"
                        )
                        if consulta["data"]
                        else "—"
                    ),
                    consulta["horario"],
                    (
                        consulta["status"]
                        .replace("_", " ")
                        .title()
                    ),
                ]

                for coluna, valor in enumerate(
                    valores
                ):
                    item = QTableWidgetItem(
                        str(valor)
                    )
                    item.setData(
                        Qt.UserRole,
                        consulta,
                    )

                    if coluna in (
                        0,
                        2,
                        3,
                        4,
                    ):
                        item.setTextAlignment(
                            Qt.AlignCenter
                        )

                    self.tabela.setItem(
                        linha,
                        coluna,
                        item,
                    )

                if consulta["id"] == id_anterior:
                    linha_selecionar = linha

            if self.tabela.rowCount():
                self.tabela.selectRow(
                    (
                        linha_selecionar
                        if linha_selecionar
                        is not None
                        else 0
                    )
                )
            else:
                self.limpar_detalhes()

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro ao carregar agenda",
                str(erro),
            )

            self.limpar_detalhes()

    # =====================================================
    # SELEÇÃO E DETALHES
    # =====================================================

    def dados_selecionados(self):
        linha = self.tabela.currentRow()

        if linha < 0:
            return None

        item = self.tabela.item(
            linha,
            0,
        )

        return (
            item.data(Qt.UserRole)
            if item
            else None
        )

    def consulta_selecionada_id(self):
        dados = self.dados_selecionados()

        return (
            int(dados["id"])
            if dados
            else None
        )

    def atualizar_detalhes(self):
        dados = self.dados_selecionados()

        if not dados:
            self.limpar_detalhes()
            return

        status = (
            dados["status"]
            or CONSULTA_AGENDADA
        )

        status_texto = (
            status
            .replace("_", " ")
            .title()
        )

        self.paciente_detalhe.setText(
            dados["paciente"]
            or "Paciente"
        )

        self.status_detalhe.setText(
            status_texto
        )
        self.status_detalhe.setProperty(
            "tipoStatus",
            status,
        )
        self._reaplicar_estilo(
            self.status_detalhe
        )

        self.id_detalhe.setText(
            f"Consulta: #{dados['id']}"
        )

        self.data_detalhe.setText(
            (
                "Data: "
                f"{dados['data'].strftime('%d/%m/%Y')}"
                if dados["data"]
                else "Data: —"
            )
        )

        self.horario_detalhe.setText(
            f"Horário: {dados['horario'] or '—'}"
        )

        self.email_detalhe.setText(
            f"E-mail: {dados['email'] or '—'}"
        )

        self.telefone_detalhe.setText(
            f"Telefone: {dados['telefone'] or '—'}"
        )

        if status == CONSULTA_AGENDADA:
            self.aviso_detalhe.setText(
                "Esta consulta ainda está agendada. "
                "Após o atendimento, marque como concluída."
            )
            self._habilitar_acoes(True)

        elif status == CONSULTA_CONCLUIDA:
            self.aviso_detalhe.setText(
                "Atendimento concluído. "
                "Nenhuma ação adicional está disponível."
            )
            self._habilitar_acoes(False)

        elif status == CONSULTA_CANCELADA:
            self.aviso_detalhe.setText(
                "Consulta cancelada. "
                "Nenhuma ação adicional está disponível."
            )
            self._habilitar_acoes(False)

        else:
            self.aviso_detalhe.setText(
                "O status desta consulta não permite alterações."
            )
            self._habilitar_acoes(False)

    # =====================================================
    # AÇÃO EXCLUSIVA DO MÉDICO
    # =====================================================

    def concluir_selecionada(self):
        self._alterar_status_selecionada(
            novo_status=CONSULTA_CONCLUIDA,
            titulo_confirmacao="Concluir consulta",
            pergunta=(
                "Confirma que este atendimento "
                "foi realizado?"
            ),
            titulo_sucesso="Consulta concluída",
            mensagem_sucesso=(
                "O atendimento foi marcado "
                "como concluído."
            ),
        )

    def _alterar_status_selecionada(
        self,
        novo_status,
        titulo_confirmacao,
        pergunta,
        titulo_sucesso,
        mensagem_sucesso,
    ):
        consulta_id = (
            self.consulta_selecionada_id()
        )

        if consulta_id is None:
            QMessageBox.information(
                self,
                "Selecione uma consulta",
                (
                    "Selecione a consulta que "
                    "deseja atualizar."
                ),
            )
            return

        resposta = QMessageBox.question(
            self,
            titulo_confirmacao,
            pergunta,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if resposta != QMessageBox.Yes:
            return

        try:
            with app.app_context():
                try:
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
                        consulta.medico_id
                        != self.medico_id
                    ):
                        raise PermissionError(
                            "Esta consulta pertence "
                            "a outro médico."
                        )

                    if (
                        consulta.status
                        != CONSULTA_AGENDADA
                    ):
                        raise ValueError(
                            "Apenas consultas agendadas "
                            "podem ser alteradas."
                        )

                    consulta.status = novo_status
                    database.session.commit()

                except Exception:
                    database.session.rollback()
                    raise

            QMessageBox.information(
                self,
                titulo_sucesso,
                mensagem_sucesso,
            )

            self.recarregar()

        except (
            ValueError,
            PermissionError,
        ) as erro:
            QMessageBox.warning(
                self,
                "Não foi possível atualizar",
                str(erro),
            )

        except Exception as erro:
            print(
                "ERRO AO ATUALIZAR CONSULTA:",
                erro,
            )

            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível atualizar "
                    "a consulta. Tente novamente."
                ),
            )