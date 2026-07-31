from types import SimpleNamespace

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from projetoafgmed import app, bcrypt
from projetoafgmed.models import Usuario

from .tela_home import abrir_tela_home


janela_login = None


def validar_login(email, senha):
    email = email.strip().lower()

    if not email or not senha:
        return None

    with app.app_context():
        usuario = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario is None:
            return None

        senha_correta = bcrypt.check_password_hash(
            usuario.senha,
            senha
        )

        if not senha_correta:
            return None

        # Cria uma cópia simples dos dados.
        # Isso evita usar o objeto SQLAlchemy fora
        # do contexto do Flask.
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
    janela_login.setWindowTitle("Login - AFGMED")
    janela_login.resize(400, 350)

    config = QSettings("AFGMED", "Desktop")

    layout = QVBoxLayout(janela_login)
    layout.setContentsMargins(40, 35, 40, 35)
    layout.setSpacing(12)

    titulo = QLabel("Entrar no AFGMED")
    titulo.setAlignment(Qt.AlignCenter)
    titulo.setStyleSheet(
        "font-size: 24px; font-weight: bold;"
    )

    campo_email = QLineEdit()
    campo_email.setPlaceholderText("E-mail")
    campo_email.setClearButtonEnabled(True)

    ultimo_email = config.value(
        "ultimo_email",
        ""
    )

    campo_email.setText(
        str(ultimo_email or "")
    )

    campo_senha = QLineEdit()
    campo_senha.setPlaceholderText("Senha")
    campo_senha.setEchoMode(QLineEdit.Password)

    mensagem = QLabel()
    mensagem.setAlignment(Qt.AlignCenter)
    mensagem.setWordWrap(True)
    mensagem.setStyleSheet("color: #b00020;")

    btn_login = QPushButton("Entrar")
    btn_voltar = QPushButton("Voltar")

    btn_login.setMinimumHeight(42)
    btn_voltar.setMinimumHeight(42)

    layout.addWidget(titulo)
    layout.addSpacing(15)
    layout.addWidget(campo_email)
    layout.addWidget(campo_senha)
    layout.addWidget(btn_login)
    layout.addWidget(btn_voltar)
    layout.addWidget(mensagem)
    layout.addStretch()

    def logar():
        email = campo_email.text().strip().lower()
        senha = campo_senha.text()

        mensagem.clear()

        if not email or not senha:
            mensagem.setText(
                "Preencha o e-mail e a senha."
            )
            return

        btn_login.setEnabled(False)
        btn_login.setText("Entrando...")

        try:
            usuario = validar_login(
                email,
                senha
            )

            if usuario is None:
                mensagem.setText(
                    "Usuário ou senha inválidos."
                )

                campo_senha.clear()
                campo_senha.setFocus()
                return

            config.setValue(
                "ultimo_email",
                email
            )

            abrir_tela_home(
                janela_login,
                usuario
            )

        except Exception as erro:
            mensagem.setText(
                f"Erro ao consultar o banco: {erro}"
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