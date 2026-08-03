from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
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


class TelaConsultasMedico(QWidget):
    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self.medico_id = getattr(usuario, "id_medico", None)
        self.setObjectName("paginaConsultasMedico")
        aplicar_estilo(self, "consultas_medico.qss")

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(26, 22, 26, 26)
        layout_principal.setSpacing(18)

        cabecalho = QHBoxLayout()
        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(2)

        titulo = QLabel("Minhas consultas")
        titulo.setObjectName("tituloPagina")

        self.subtitulo = QLabel(
            "Acompanhe os pacientes agendados e conclua os atendimentos realizados."
        )
        self.subtitulo.setObjectName("subtituloPagina")

        area_titulo.addWidget(titulo)
        area_titulo.addWidget(self.subtitulo)

        self.filtro = QComboBox()
        self.filtro.addItem("Todas", "todas")
        self.filtro.addItem("Agendadas", "agendada")
        self.filtro.addItem("Concluídas", "concluida")
        self.filtro.addItem("Canceladas", "cancelada")
        self.filtro.currentIndexChanged.connect(self.recarregar)

        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(self.recarregar)

        cabecalho.addLayout(area_titulo, 1)
        cabecalho.addWidget(QLabel("Status:"))
        cabecalho.addWidget(self.filtro)
        cabecalho.addWidget(atualizar)

        self.resumo = QFrame()
        self.resumo.setObjectName("resumoConsultasMedico")
        self.layout_resumo = QHBoxLayout(self.resumo)
        self.layout_resumo.setContentsMargins(16, 14, 16, 14)
        self.layout_resumo.setSpacing(12)

        self.tabela = QTableWidget(0, 7)
        self.tabela.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Data", "Horário", "Status", "E-mail", "Telefone"]
        )
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabela.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)

        acoes = QHBoxLayout()
        self.botao_concluir = QPushButton("Concluir consulta selecionada")
        self.botao_concluir.setObjectName("botaoSucesso")
        self.botao_concluir.clicked.connect(self.concluir_selecionada)

        acoes.addStretch()
        acoes.addWidget(self.botao_concluir)

        layout_principal.addLayout(cabecalho)
        layout_principal.addWidget(self.resumo)
        layout_principal.addWidget(self.tabela, 1)
        layout_principal.addLayout(acoes)

        self.recarregar()

    def _limpar_resumo(self):
        while self.layout_resumo.count():
            item = self.layout_resumo.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _adicionar_metrica(self, titulo, valor):
        card = QFrame()
        card.setObjectName("metricaConsultaMedico")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(1)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("rotuloMetricaConsulta")
        label_valor = QLabel(str(valor))
        label_valor.setObjectName("valorMetricaConsulta")

        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)
        self.layout_resumo.addWidget(card)

    def recarregar(self):
        self.tabela.setRowCount(0)
        self._limpar_resumo()

        if not self.medico_id:
            self.subtitulo.setText(
                "Este usuário não está vinculado a um cadastro médico."
            )
            self.botao_concluir.setEnabled(False)
            return

        try:
            with app.app_context():
                medico = database.session.get(Medico, self.medico_id)
                consulta_query = Consulta.query.filter_by(medico_id=self.medico_id)
                todas = consulta_query.order_by(
                    Consulta.data.desc(), Consulta.horario.asc()
                ).all()

                filtro = self.filtro.currentData()
                consultas = (
                    [c for c in todas if c.status == filtro]
                    if filtro != "todas"
                    else todas
                )

                dados = []
                for consulta in consultas:
                    perfil = getattr(consulta.usuario, "perfil", None)
                    dados.append(
                        {
                            "id": consulta.id,
                            "paciente": (
                                f"{consulta.usuario.nome} {consulta.usuario.sobrenome}"
                            ).strip(),
                            "data": consulta.data,
                            "horario": consulta.horario,
                            "status": consulta.status or "agendada",
                            "email": consulta.usuario.email or "",
                            "telefone": getattr(perfil, "telefone", "") or "—",
                        }
                    )

                hoje = date.today()
                metricas = {
                    "Hoje": sum(
                        1 for c in todas if c.data == hoje and c.status == "agendada"
                    ),
                    "Agendadas": sum(1 for c in todas if c.status == "agendada"),
                    "Concluídas": sum(1 for c in todas if c.status == "concluida"),
                    "Canceladas": sum(1 for c in todas if c.status == "cancelada"),
                }

                nome_medico = (
                    f"{medico.nome} {medico.sobrenome}".strip()
                    if medico
                    else "Médico"
                )
                especialidade = medico.especialidade if medico else ""

            self.subtitulo.setText(
                f"Agenda de {nome_medico} • {especialidade or 'Especialidade não informada'}"
            )

            for titulo, valor in metricas.items():
                self._adicionar_metrica(titulo, valor)
            self.layout_resumo.addStretch()

            for linha, consulta in enumerate(dados):
                self.tabela.insertRow(linha)
                valores = [
                    str(consulta["id"]),
                    consulta["paciente"],
                    consulta["data"].strftime("%d/%m/%Y"),
                    consulta["horario"],
                    consulta["status"].title(),
                    consulta["email"],
                    consulta["telefone"],
                ]

                for coluna, valor in enumerate(valores):
                    item = QTableWidgetItem(valor)
                    if coluna in (0, 2, 3, 4):
                        item.setTextAlignment(Qt.AlignCenter)
                    self.tabela.setItem(linha, coluna, item)

            self.botao_concluir.setEnabled(bool(dados))

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro ao carregar agenda",
                str(erro),
            )

    def consulta_selecionada_id(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            return None

        item = self.tabela.item(linha, 0)
        return int(item.text()) if item else None

    def concluir_selecionada(self):
        consulta_id = self.consulta_selecionada_id()
        if consulta_id is None:
            QMessageBox.information(
                self,
                "Selecione uma consulta",
                "Selecione a linha da consulta que deseja concluir.",
            )
            return

        resposta = QMessageBox.question(
            self,
            "Concluir consulta",
            "Confirma que este atendimento foi realizado?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resposta != QMessageBox.Yes:
            return

        try:
            with app.app_context():
                consulta = database.session.get(Consulta, consulta_id)

                if consulta is None:
                    raise ValueError("Consulta não encontrada.")
                if consulta.medico_id != self.medico_id:
                    raise PermissionError("Esta consulta pertence a outro médico.")
                if consulta.status != "agendada":
                    raise ValueError("Apenas consultas agendadas podem ser concluídas.")

                consulta.status = "concluida"
                database.session.commit()

            QMessageBox.information(
                self,
                "Consulta concluída",
                "O atendimento foi marcado como concluído.",
            )
            self.recarregar()

        except Exception as erro:
            database.session.rollback()
            QMessageBox.critical(self, "Erro", str(erro))
