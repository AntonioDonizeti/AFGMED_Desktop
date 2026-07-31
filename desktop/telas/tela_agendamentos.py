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

from projetoafgmed import app, database
from projetoafgmed.models import Consulta


class TelaAgendamentos(QWidget):
    def __init__(self, usuario):
        super().__init__()

        self.usuario_id = usuario.id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        layout.setSpacing(12)

        cabecalho = QHBoxLayout()

        titulo = QLabel(
            "Meus agendamentos"
        )

        titulo.setStyleSheet(
            "font-size: 22px; "
            "font-weight: bold;"
        )

        atualizar = QPushButton(
            "Atualizar"
        )

        atualizar.clicked.connect(
            self.recarregar
        )

        cabecalho.addWidget(titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(atualizar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(
            QFrame.NoFrame
        )

        layout.addLayout(cabecalho)
        layout.addWidget(self.scroll)

        self.recarregar()

    def recarregar(self):
        container = QWidget()
        lista = QVBoxLayout(container)
        lista.setSpacing(12)

        with app.app_context():
            consultas_banco = (
                Consulta.query.filter(
                    Consulta.usuario_id
                    == self.usuario_id,
                    Consulta.status
                    != "cancelada",
                )
                .order_by(
                    Consulta.data.asc(),
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
                    "especialidade": (
                        consulta.medico.especialidade
                        or ""
                    ),
                    "data": consulta.data,
                    "horario": consulta.horario,
                    "status": (
                        consulta.status
                        or "agendada"
                    ),
                }
                for consulta in consultas_banco
            ]

        if not consultas:
            vazio = QLabel(
                "Você não possui "
                "agendamentos ativos."
            )

            vazio.setAlignment(
                Qt.AlignCenter
            )

            vazio.setStyleSheet(
                "font-size: 16px; "
                "color: #666;"
            )

            lista.addWidget(vazio)
            lista.addStretch()

            self.scroll.setWidget(
                container
            )

            return

        hoje = date.today()

        for consulta in consultas:
            card = QFrame()
            card.setObjectName("agendamentoCard")

            card.setFrameShape(
                QFrame.StyledPanel
            )

            card_layout = QHBoxLayout(
                card
            )

            card_layout.setContentsMargins(
                16,
                14,
                16,
                14,
            )

            card_layout.setSpacing(18)

            informacoes = QVBoxLayout()

            medico = QLabel(
                consulta["medico"]
                or "Médico"
            )

            medico.setStyleSheet(
                "font-size: 18px; "
                "font-weight: bold;"
            )

            especialidade = QLabel(
                consulta["especialidade"]
                or "Especialidade não informada"
            )

            data_texto = consulta[
                "data"
            ].strftime("%d/%m/%Y")

            data_horario = QLabel(
                f"Data: {data_texto}    "
                f"Horário: "
                f"{consulta['horario']}"
            )

            status_texto = {
                "agendada": "Agendada",
                "concluida": "Concluída",
                "cancelada": "Cancelada",
            }.get(
                consulta["status"].lower(),
                "Em análise",
            )

            status = QLabel(
                f"Status: {status_texto}"
            )

            status.setStyleSheet(
                "font-weight: bold;"
            )

            informacoes.addWidget(medico)
            informacoes.addWidget(
                especialidade
            )
            informacoes.addWidget(
                data_horario
            )
            informacoes.addWidget(status)

            card_layout.addLayout(
                informacoes,
                1,
            )

            if consulta["status"] == "agendada":
                cancelar = QPushButton(
                    "Cancelar consulta"
                )

                cancelar.setMinimumHeight(
                    38
                )

                cancelar.clicked.connect(
                    lambda checked=False,
                    consulta_id=consulta["id"]:
                    self.cancelar_consulta(
                        consulta_id
                    )
                )

                card_layout.addWidget(
                    cancelar
                )

            if (
                consulta["data"] < hoje
                and consulta["status"]
                == "agendada"
            ):
                observacao = QLabel(
                    "Aguardando conclusão "
                    "pelo médico"
                )

                observacao.setStyleSheet(
                    "color: #666;"
                )

                informacoes.addWidget(
                    observacao
                )

            lista.addWidget(card)

        lista.addStretch()

        self.scroll.setWidget(
            container
        )

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
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if resposta != QMessageBox.Yes:
            return

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
                    != self.usuario_id
                ):
                    raise ValueError(
                        "Você não pode cancelar "
                        "esta consulta."
                    )

                if consulta.status != "agendada":
                    raise ValueError(
                        "Apenas consultas agendadas "
                        "podem ser canceladas."
                    )

                consulta.status = "cancelada"

                database.session.commit()

            QMessageBox.information(
                self,
                "AFGMED",
                (
                    "Consulta cancelada "
                    "com sucesso."
                ),
            )

            self.recarregar()

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível cancelar "
                    f"a consulta.\n\n{erro}"
                ),
            )


def tela_agendamentos(usuario):
    return TelaAgendamentos(usuario)