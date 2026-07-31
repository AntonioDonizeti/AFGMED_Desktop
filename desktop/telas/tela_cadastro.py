from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import IntegrityError

from projetoafgmed import app, bcrypt, database
from projetoafgmed.models import PerfilUsuario, Usuario


janela_cadastro = None


def abrir_tela_cadastro(janela_anterior=None):
    global janela_cadastro

    if janela_anterior is not None:
        janela_anterior.close()

    janela_cadastro = QWidget()
    janela_cadastro.setWindowTitle("Criar conta - AFGMED")
    janela_cadastro.resize(400, 480)

    layout = QVBoxLayout(janela_cadastro)
    layout.setContentsMargins(40, 35, 40, 35)
    layout.setSpacing(12)

    titulo = QLabel("Criar novo usuário")
    titulo.setAlignment(Qt.AlignCenter)
    titulo.setStyleSheet(
        "font-size: 24px; font-weight: bold;"
    )

    nome = QLineEdit()
    nome.setPlaceholderText("Nome")
    nome.setClearButtonEnabled(True)

    sobrenome = QLineEdit()
    sobrenome.setPlaceholderText("Sobrenome")
    sobrenome.setClearButtonEnabled(True)

    email = QLineEdit()
    email.setPlaceholderText("E-mail")
    email.setClearButtonEnabled(True)

    senha = QLineEdit()
    senha.setPlaceholderText("Senha")
    senha.setEchoMode(QLineEdit.Password)

    confirmar = QLineEdit()
    confirmar.setPlaceholderText("Confirmar senha")
    confirmar.setEchoMode(QLineEdit.Password)

    mensagem = QLabel()
    mensagem.setAlignment(Qt.AlignCenter)
    mensagem.setWordWrap(True)
    mensagem.setStyleSheet("color: #b00020;")

    btn_cadastrar = QPushButton("Criar conta")
    btn_voltar = QPushButton("Voltar ao início")

    btn_cadastrar.setMinimumHeight(42)
    btn_voltar.setMinimumHeight(42)

    layout.addWidget(titulo)
    layout.addSpacing(10)
    layout.addWidget(nome)
    layout.addWidget(sobrenome)
    layout.addWidget(email)
    layout.addWidget(senha)
    layout.addWidget(confirmar)
    layout.addWidget(btn_cadastrar)
    layout.addWidget(btn_voltar)
    layout.addWidget(mensagem)
    layout.addStretch()

    def cadastrar():
        nome_informado = nome.text().strip()
        sobrenome_informado = sobrenome.text().strip()
        email_informado = email.text().strip().lower()
        senha_informada = senha.text()
        confirmacao_informada = confirmar.text()

        mensagem.clear()

        if not all(
            [
                nome_informado,
                sobrenome_informado,
                email_informado,
                senha_informada,
                confirmacao_informada,
            ]
        ):
            mensagem.setText("Preencha todos os campos.")
            return

        if "@" not in email_informado or "." not in email_informado:
            mensagem.setText("Digite um e-mail válido.")
            return

        if senha_informada != confirmacao_informada:
            mensagem.setText("As senhas não conferem.")
            return

        if len(senha_informada) < 6:
            mensagem.setText(
                "A senha deve ter pelo menos 6 caracteres."
            )
            return

        btn_cadastrar.setEnabled(False)
        btn_cadastrar.setText("Salvando...")

        try:
            with app.app_context():
                try:
                    usuario_existente = Usuario.query.filter_by(
                        email=email_informado
                    ).first()

                    if usuario_existente is not None:
                        mensagem.setText(
                            "Este e-mail já está cadastrado."
                        )
                        return

                    senha_hash = bcrypt.generate_password_hash(
                        senha_informada
                    )

                    if isinstance(senha_hash, bytes):
                        senha_hash = senha_hash.decode("utf-8")

                    novo_usuario = Usuario(
                        nome=nome_informado,
                        sobrenome=sobrenome_informado,
                        email=email_informado,
                        senha=senha_hash,
                        is_admin=False,
                        is_medico=False,
                    )

                    database.session.add(novo_usuario)

                    # Gera o ID sem finalizar a transação.
                    database.session.flush()

                    # Cria também um perfil vazio para o usuário.
                    novo_perfil = PerfilUsuario(
                        id_usuario=novo_usuario.id
                    )

                    database.session.add(novo_perfil)

                    # Grava definitivamente no afgmed.db.
                    database.session.commit()

                except Exception:
                    database.session.rollback()
                    raise

            QMessageBox.information(
                janela_cadastro,
                "AFGMED",
                "Cadastro realizado!",
            )

            from .tela_login import abrir_tela_login

            abrir_tela_login(janela_cadastro)

        except IntegrityError:
            mensagem.setText(
                "Este e-mail já está cadastrado."
            )

        except Exception as erro:
            mensagem.setText(
                f"Erro ao salvar o cadastro: {erro}"
            )

        finally:
            btn_cadastrar.setEnabled(True)
            btn_cadastrar.setText("Criar conta")

    def voltar_inicio():
        janela_cadastro.close()

        from .tela_inicio import abrir_tela_inicio

        abrir_tela_inicio()

    btn_cadastrar.clicked.connect(cadastrar)
    confirmar.returnPressed.connect(cadastrar)
    btn_voltar.clicked.connect(voltar_inicio)

    nome.setFocus()
    janela_cadastro.show()