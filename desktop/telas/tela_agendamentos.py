from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from desktop.estilos import aplicar_estilo
from projetoafgmed import app, database
from projetoafgmed.models import Consulta


class TelaAgendamentos(QWidget):
    def __init__(self, usuario):
        super().__init__()

        self.usuario_id = usuario.id
        self.setObjectName("paginaAgendamentos")
        aplicar_estilo(self, "agendamentos.qss")

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(26, 22, 26, 26)
        layout_principal.setSpacing(18)

        cabecalho = QHBoxLayout()
        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(2)

        titulo = QLabel("Meus agendamentos")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Acompanhe consultas agendadas, concluídas e canceladas."
        )
        subtitulo.setObjectName("subtituloPagina")

        area_titulo.addWidget(titulo)
        area_titulo.addWidget(subtitulo)

        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(self.recarregar)

        cabecalho.addLayout(area_titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(atualizar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        layout_principal.addLayout(cabecalho)
        layout_principal.addWidget(self.scroll)

        self.recarregar()

    def recarregar(self):
        container = QWidget()
        lista = QVBoxLayout(container)
        lista.setContentsMargins(0, 0, 0, 10)
        lista.setSpacing(12)

        try:
            with app.app_context():
                consultas_banco = (
                    Consulta.query.filter_by(usuario_id=self.usuario_id)
                    .order_by(
                        Consulta.data.desc(),
                        Consulta.horario.asc(),
                    )
                    .all()
                )

                consultas = [
                    {
                        "id": consulta.id,
                        "medico": (
                            f"{consulta.medico.nome} "
                            f"{consulta.medico.sobrenome}"
                        ).strip(),
                        "especialidade": consulta.medico.especialidade or "",
                        "data": consulta.data,
                        "horario": consulta.horario,
                        "status": consulta.status or "agendada",
                    }
                    for consulta in consultas_banco
                ]
        except Exception as erro:
            print("ERRO AO CARREGAR AGENDAMENTOS:", erro)
            consultas = []

        if not consultas:
            vazio = QLabel("Você ainda não possui agendamentos.")
            vazio.setObjectName("agendamentosVazio")
            vazio.setAlignment(Qt.AlignCenter)
            lista.addWidget(vazio)
            lista.addStretch()
            self.scroll.setWidget(container)
            return

        for consulta in consultas:
            lista.addWidget(self.criar_card(consulta))

        lista.addStretch()
        self.scroll.setWidget(container)

    def criar_card(self, consulta):
        card = QFrame()
        card.setObjectName("agendamentoCard")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(18)

        informacoes = QVBoxLayout()
        informacoes.setSpacing(4)

        medico = QLabel(consulta["medico"] or "Médico")
        medico.setObjectName("nomeMedicoAgendamento")

        especialidade = QLabel(
            consulta["especialidade"] or "Especialidade não informada"
        )
        especialidade.setObjectName("especialidadeAgendamento")

        data_texto = consulta["data"].strftime("%d/%m/%Y")
        detalhe = QLabel(
            f"Data: {data_texto}   •   Horário: {consulta['horario']}"
        )
        detalhe.setObjectName("detalheAgendamento")

        informacoes.addWidget(medico)
        informacoes.addWidget(especialidade)
        informacoes.addWidget(detalhe)

        status_valor = (consulta["status"] or "agendada").lower()
        status_texto = {
            "agendada": "Agendada",
            "concluida": "Concluída",
            "cancelada": "Cancelada",
        }.get(status_valor, "Em análise")

        status = QLabel(status_texto)
        status.setObjectName("statusAgendamento")
        status.setProperty("tipoStatus", status_valor)
        status.setAlignment(Qt.AlignCenter)

        acoes = QHBoxLayout()
        acoes.addWidget(status)

        if status_valor == "agendada":
            cancelar = QPushButton("Cancelar consulta")
            cancelar.setObjectName("botaoPerigo")
            cancelar.clicked.connect(
                lambda checked=False, consulta_id=consulta["id"]: (
                    self.cancelar_consulta(consulta_id)
                )
            )
            acoes.addWidget(cancelar)

            if consulta["data"] < date.today():
                observacao = QLabel("Aguardando conclusão pelo médico")
                observacao.setObjectName("detalheAgendamento")
                informacoes.addWidget(observacao)

        layout.addLayout(informacoes, 1)
        layout.addLayout(acoes)

        return card

    def cancelar_consulta(self, consulta_id):
        resposta = QMessageBox.question(
            self,
            "Cancelar consulta",
            "Deseja realmente cancelar esta consulta?",
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

                if consulta.usuario_id != self.usuario_id:
                    raise ValueError("Você não pode cancelar esta consulta.")

                if consulta.status != "agendada":
                    raise ValueError(
                        "Apenas consultas agendadas podem ser canceladas."
                    )

                consulta.status = "cancelada"
                database.session.commit()

            QMessageBox.information(
                self,
                "Consulta cancelada",
                "A consulta foi cancelada com sucesso.",
            )
            self.recarregar()

        except Exception as erro:
            database.session.rollback()
            QMessageBox.critical(self, "Erro", str(erro))


def tela_agendamentos(usuario):
    return TelaAgendamentos(usuario)
