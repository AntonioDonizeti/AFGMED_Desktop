from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout
)

from desktop.telas.tela_login import abrir_tela_login
from desktop.telas.tela_cadastro import abrir_tela_cadastro


def abrir_tela_inicio():

    global janela_inicio


    janela_inicio = QWidget()

    janela_inicio.setWindowTitle(
        "AFGMED"
    )

    janela_inicio.resize(
        400,
        300
    )


    layout = QVBoxLayout()


    titulo = QLabel(
        "AFGMED\nSistema de Saúde"
    )

    titulo.setStyleSheet(
        """
        font-size:25px;
        font-weight:bold;
        text-align:center;
        """
    )


    btn_login = QPushButton(
        "Entrar"
    )


    btn_cadastro = QPushButton(
        "Criar Login"
    )


    layout.addWidget(titulo)

    layout.addWidget(btn_login)

    layout.addWidget(btn_cadastro)


    janela_inicio.setLayout(
        layout
    )


    btn_login.clicked.connect(
        lambda:
        abrir_tela_login(
            janela_inicio
        )
    )


    btn_cadastro.clicked.connect(
        lambda:
        abrir_tela_cadastro(
            janela_inicio
        )
    )


    janela_inicio.show()