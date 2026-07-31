from types import SimpleNamespace

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from desktop.estilos import aplicar_estilo
from projetoafgmed import app, bcrypt
from projetoafgmed.models import Usuario


janela_login = None


def validar_login(email, senha):
    email = email.strip().lower()

    if not email or not senha:
        return None

    with app.app_context():
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario is None:
            return None

        if not bcrypt.check_password_hash(usuario.senha, senha):
            return None

        return SimpleNamespace(
            id=usuario.id,
            nome=usuario.nome or "",
            sobrenome=usuario.sobrenome or "",
            email=usuario.email or "",
            foto=usuario.foto or "",
            is_admin=bool(usuario.is_admin),
            is_medico=bool(usuario.is_medico),
            id_medico=usuario.id_medico,
        )


def abrir_tela_login(janela_anterior=None):
    global janela_login

    if janela_anterior is not None:
        janela_anterior.close()

    janela_login = QWidget()
    janela_login.setObjectName("paginaAuth")
    janela_login.setWindowTitle("Entrar - AFGMED")
    janela_login.resize(550, 550)
    janela_login.setMinimumSize(500, 500)

    aplicar_estilo(janela_login, "auth.qss")

    config = QSettings("AFGMED", "Desktop")

    layout_raiz = QVBoxLayout(janela_login)
    layout_raiz.setContentsMargins(45, 40, 45, 40)
    layout_raiz.addStretch()

    card = QFrame()
    card.setObjectName("cardAuth")
    card.setMaximumWidth(430)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(38, 34, 38, 34)
    layout.setSpacing(13)

    marca = QLabel("AFGMED")
    marca.setObjectName("marcaAuth")
    marca.setAlignment(Qt.AlignCenter)

    titulo = QLabel("Bem-vindo de volta")
    titulo.setObjectName("tituloAuth")
    titulo.setAlignment(Qt.AlignCenter)

    subtitulo = QLabel("Entre com seu e-mail e senha para continuar.")
    subtitulo.setObjectName("subtituloAuth")
    subtitulo.setAlignment(Qt.AlignCenter)

    campo_email = QLineEdit()
    campo_email.setPlaceholderText("E-mail")
    campo_email.setClearButtonEnabled(True)
    campo_email.setText(str(config.value("ultimo_email", "") or ""))

    campo_senha = QLineEdit()
    campo_senha.setPlaceholderText("Senha")
    campo_senha.setEchoMode(QLineEdit.Password)

    mensagem = QLabel()
    mensagem.setObjectName("mensagemErro")
    mensagem.setAlignment(Qt.AlignCenter)
    mensagem.setWordWrap(True)

    btn_login = QPushButton("Entrar")
    btn_login.setObjectName("botaoPrimario")
    btn_login.setMinimumHeight(46)

    btn_voltar = QPushButton("Voltar")
    btn_voltar.setMinimumHeight(42)

    layout.addWidget(marca)
    layout.addWidget(titulo)
    layout.addWidget(subtitulo)
    layout.addSpacing(8)
    layout.addWidget(campo_email)
    layout.addWidget(campo_senha)
    layout.addWidget(mensagem)
    layout.addWidget(btn_login)
    layout.addWidget(btn_voltar)

    layout_raiz.addWidget(card, alignment=Qt.AlignCenter)
    layout_raiz.addStretch()

    def logar():
        email = campo_email.text().strip().lower()
        senha = campo_senha.text()
        mensagem.clear()

        if not email or not senha:
            mensagem.setText("Preencha o e-mail e a senha.")
            return

        btn_login.setEnabled(False)
        btn_login.setText("Entrando...")

        try:
            usuario = validar_login(email, senha)

            if usuario is None:
                mensagem.setText("Usuário ou senha inválidos.")
                campo_senha.clear()
                campo_senha.setFocus()
                return

            config.setValue("ultimo_email", email)

            from .tela_home import abrir_tela_home

            abrir_tela_home(janela_login, usuario)

        except Exception as erro:
            print("ERRO DE LOGIN:", erro)
            mensagem.setText(
                "Não foi possível acessar o banco. Tente novamente."
            )

        finally:
            btn_login.setEnabled(True)
            btn_login.setText("Entrar")

    def voltar():
        janela_login.close()
        from .tela_inicio import abrir_tela_inicio

        abrir_tela_inicio()

    btn_login.clicked.connect(logar)
    campo_senha.returnPressed.connect(logar)
    btn_voltar.clicked.connect(voltar)

    if campo_email.text():
        campo_senha.setFocus()
    else:
        campo_email.setFocus()

    janela_login.show()
