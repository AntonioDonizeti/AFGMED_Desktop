from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import IntegrityError

from desktop.estilos import aplicar_estilo
from projetoafgmed import app, bcrypt, database
from projetoafgmed.models import PerfilUsuario, Usuario


janela_cadastro = None


def abrir_tela_cadastro(janela_anterior=None):
    global janela_cadastro

    if janela_anterior is not None:
        janela_anterior.close()

    janela_cadastro = QWidget()
    janela_cadastro.setObjectName("paginaAuth")
    janela_cadastro.setWindowTitle("Criar conta - AFGMED")
    janela_cadastro.resize(570, 700)
    janela_cadastro.setMinimumSize(520, 640)

    aplicar_estilo(janela_cadastro, "auth.qss")

    layout_raiz = QVBoxLayout(janela_cadastro)
    layout_raiz.setContentsMargins(45, 30, 45, 30)
    layout_raiz.addStretch()

    card = QFrame()
    card.setObjectName("cardAuth")
    card.setMaximumWidth(450)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(38, 30, 38, 30)
    layout.setSpacing(11)

    marca = QLabel("AFGMED")
    marca.setObjectName("marcaAuth")
    marca.setAlignment(Qt.AlignCenter)

    titulo = QLabel("Crie sua conta")
    titulo.setObjectName("tituloAuth")
    titulo.setAlignment(Qt.AlignCenter)

    subtitulo = QLabel(
        "Cadastre-se para agendar consultas e comprar produtos."
    )
    subtitulo.setObjectName("subtituloAuth")
    subtitulo.setAlignment(Qt.AlignCenter)
    subtitulo.setWordWrap(True)

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
    senha.setPlaceholderText("Senha com pelo menos 6 caracteres")
    senha.setEchoMode(QLineEdit.Password)

    confirmar = QLineEdit()
    confirmar.setPlaceholderText("Confirme a senha")
    confirmar.setEchoMode(QLineEdit.Password)

    mensagem = QLabel()
    mensagem.setObjectName("mensagemErro")
    mensagem.setAlignment(Qt.AlignCenter)
    mensagem.setWordWrap(True)

    btn_cadastrar = QPushButton("Criar conta")
    btn_cadastrar.setObjectName("botaoPrimario")
    btn_cadastrar.setMinimumHeight(46)

    btn_voltar = QPushButton("Voltar")
    btn_voltar.setMinimumHeight(42)

    layout.addWidget(marca)
    layout.addWidget(titulo)
    layout.addWidget(subtitulo)
    layout.addSpacing(6)
    layout.addWidget(nome)
    layout.addWidget(sobrenome)
    layout.addWidget(email)
    layout.addWidget(senha)
    layout.addWidget(confirmar)
    layout.addWidget(mensagem)
    layout.addWidget(btn_cadastrar)
    layout.addWidget(btn_voltar)

    layout_raiz.addWidget(card, alignment=Qt.AlignCenter)
    layout_raiz.addStretch()

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
            mensagem.setText("A senha deve ter pelo menos 6 caracteres.")
            return

        btn_cadastrar.setEnabled(False)
        btn_cadastrar.setText("Salvando...")

        try:
            with app.app_context():
                try:
                    if Usuario.query.filter_by(email=email_informado).first():
                        mensagem.setText("Este e-mail já está cadastrado.")
                        return

                    senha_hash = bcrypt.generate_password_hash(senha_informada)

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
                    database.session.flush()
                    database.session.add(
                        PerfilUsuario(id_usuario=novo_usuario.id)
                    )
                    database.session.commit()

                except Exception:
                    database.session.rollback()
                    raise

            QMessageBox.information(
                janela_cadastro,
                "Conta criada",
                "Cadastro realizado com sucesso.",
            )

            from .tela_login import abrir_tela_login

            abrir_tela_login(janela_cadastro)

        except IntegrityError:
            mensagem.setText("Este e-mail já está cadastrado.")

        except Exception as erro:
            print("ERRO DE CADASTRO:", erro)
            mensagem.setText("Não foi possível concluir o cadastro.")

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
