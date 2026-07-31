from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop.estilos import aplicar_estilo


janela_inicio = None


def abrir_tela_inicio():
    global janela_inicio

    janela_inicio = QWidget()
    janela_inicio.setObjectName("paginaAuth")
    janela_inicio.setWindowTitle("AFGMED")
    janela_inicio.resize(560, 520)
    janela_inicio.setMinimumSize(500, 470)

    aplicar_estilo(janela_inicio, "auth.qss")

    layout_raiz = QVBoxLayout(janela_inicio)
    layout_raiz.setContentsMargins(45, 40, 45, 40)
    layout_raiz.addStretch()

    card = QFrame()
    card.setObjectName("cardAuth")
    card.setMaximumWidth(430)

    layout_card = QVBoxLayout(card)
    layout_card.setContentsMargins(38, 34, 38, 34)
    layout_card.setSpacing(15)

    marca = QLabel("AFGMED")
    marca.setObjectName("marcaAuth")
    marca.setAlignment(Qt.AlignCenter)

    titulo = QLabel("Saúde e cuidado em um só lugar")
    titulo.setObjectName("tituloAuth")
    titulo.setAlignment(Qt.AlignCenter)
    titulo.setWordWrap(True)

    subtitulo = QLabel(
        "Acesse consultas, produtos e pedidos com segurança pelo aplicativo Desktop."
    )
    subtitulo.setObjectName("subtituloAuth")
    subtitulo.setAlignment(Qt.AlignCenter)
    subtitulo.setWordWrap(True)

    btn_login = QPushButton("Entrar na minha conta")
    btn_login.setObjectName("botaoPrimario")
    btn_login.setMinimumHeight(46)

    btn_cadastro = QPushButton("Criar uma nova conta")
    btn_cadastro.setMinimumHeight(46)

    rodape = QLabel("Sistema acadêmico integrado ao AFGMED Web")
    rodape.setObjectName("rodapeAuth")
    rodape.setAlignment(Qt.AlignCenter)

    layout_card.addWidget(marca)
    layout_card.addWidget(titulo)
    layout_card.addWidget(subtitulo)
    layout_card.addSpacing(10)
    layout_card.addWidget(btn_login)
    layout_card.addWidget(btn_cadastro)
    layout_card.addSpacing(8)
    layout_card.addWidget(rodape)

    layout_raiz.addWidget(card, alignment=Qt.AlignCenter)
    layout_raiz.addStretch()

    def abrir_login():
        from .tela_login import abrir_tela_login

        abrir_tela_login(janela_inicio)

    def abrir_cadastro():
        from .tela_cadastro import abrir_tela_cadastro

        abrir_tela_cadastro(janela_inicio)

    btn_login.clicked.connect(abrir_login)
    btn_cadastro.clicked.connect(abrir_cadastro)

    janela_inicio.show()
