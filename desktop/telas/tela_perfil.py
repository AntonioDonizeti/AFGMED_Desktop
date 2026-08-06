import os

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QDateEdit,
    QGroupBox,
    QMessageBox
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QDate, Qt
from sqlalchemy.exc import IntegrityError

from projetoafgmed import app, database
from projetoafgmed.models import Usuario, PerfilUsuario


def tela_perfil(usuario=None):
    tela = QWidget()

    if usuario is None:
        layout_erro = QVBoxLayout()
        layout_erro.addWidget(QLabel("Nenhum usuário foi informado."))
        tela.setLayout(layout_erro)
        return tela

    usuario_id = usuario.id

    # Busca dados atuais e cria o perfil complementar, caso ainda não exista.
    with app.app_context():
        usuario_db = database.session.get(Usuario, usuario_id)

        if usuario_db is None:
            layout_erro = QVBoxLayout()
            layout_erro.addWidget(QLabel("Usuário não encontrado no banco."))
            tela.setLayout(layout_erro)
            return tela

        perfil_db = PerfilUsuario.query.filter_by(
            id_usuario=usuario_id
        ).first()

        if perfil_db is None:
            perfil_db = PerfilUsuario(id_usuario=usuario_id)
            database.session.add(perfil_db)
            database.session.commit()

        dados_usuario = {
            "nome": usuario_db.nome,
            "sobrenome": usuario_db.sobrenome,
            "email": usuario_db.email,
            "foto_relativa": usuario_db.foto_exibicao,
            "is_admin": bool(usuario_db.is_admin),
            "is_medico": bool(usuario_db.is_medico)
        }

        dados_perfil = {
            "telefone": perfil_db.telefone or "",
            "cpf": perfil_db.cpf or "",
            "data_nascimento": perfil_db.data_nascimento,
            "endereco": perfil_db.endereco or "",
            "cidade": perfil_db.cidade or "",
            "estado": perfil_db.estado or "",
            "cep": perfil_db.cep or ""
        }

    layout_principal = QHBoxLayout()

    # Coluna esquerda
    coluna_perfil = QVBoxLayout()

    foto = QLabel()
    foto.setFixedSize(150, 150)
    foto.setAlignment(Qt.AlignCenter)

    caminho_foto = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(__file__)
            )
        ),
        "projetoafgmed",
        "static",
        *dados_usuario["foto_relativa"].split("/")
    )

    if os.path.exists(caminho_foto):
        imagem = QPixmap(caminho_foto)
        foto.setPixmap(
            imagem.scaled(
                140,
                140,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )
    else:
        foto.setText("Sem foto")

    nome_resumo = QLabel(
        f'{dados_usuario["nome"]} {dados_usuario["sobrenome"]}'
    )
    email_resumo = QLabel(dados_usuario["email"])

    tipo = QLabel()
    if dados_usuario["is_admin"]:
        tipo.setText("Administrador")
    elif dados_usuario["is_medico"]:
        tipo.setText("Médico")
    else:
        tipo.setText("Paciente")

    coluna_perfil.addWidget(foto)
    coluna_perfil.addWidget(nome_resumo)
    coluna_perfil.addWidget(email_resumo)
    coluna_perfil.addWidget(tipo)
    coluna_perfil.addStretch()

    # Dados pessoais
    dados_pessoais = QGroupBox("Dados pessoais")
    layout_pessoais = QFormLayout()

    nome_campo = QLineEdit(dados_usuario["nome"])
    sobrenome_campo = QLineEdit(dados_usuario["sobrenome"])
    email_campo = QLineEdit(dados_usuario["email"])

    layout_pessoais.addRow("Nome", nome_campo)
    layout_pessoais.addRow("Sobrenome", sobrenome_campo)
    layout_pessoais.addRow("E-mail", email_campo)
    dados_pessoais.setLayout(layout_pessoais)

    # Dados complementares
    dados_complementares = QGroupBox("Dados complementares")
    layout_complementares = QFormLayout()

    telefone = QLineEdit(dados_perfil["telefone"])
    cpf = QLineEdit(dados_perfil["cpf"])

    nascimento = QDateEdit()
    nascimento.setCalendarPopup(True)
    nascimento.setDisplayFormat("dd/MM/yyyy")

    if dados_perfil["data_nascimento"]:
        data_salva = dados_perfil["data_nascimento"]
        nascimento.setDate(
            QDate(data_salva.year, data_salva.month, data_salva.day)
        )
    else:
        nascimento.setDate(QDate.currentDate())

    layout_complementares.addRow("Telefone", telefone)
    layout_complementares.addRow("CPF", cpf)
    layout_complementares.addRow("Data de nascimento", nascimento)
    dados_complementares.setLayout(layout_complementares)

    # Endereço
    endereco_box = QGroupBox("Endereço")
    layout_endereco = QFormLayout()

    endereco = QLineEdit(dados_perfil["endereco"])
    cidade = QLineEdit(dados_perfil["cidade"])
    estado = QLineEdit(dados_perfil["estado"])
    cep = QLineEdit(dados_perfil["cep"])

    layout_endereco.addRow("Endereço", endereco)
    layout_endereco.addRow("Cidade", cidade)
    layout_endereco.addRow("Estado", estado)
    layout_endereco.addRow("CEP", cep)
    endereco_box.setLayout(layout_endereco)

    salvar = QPushButton("Salvar alterações")

    def salvar_dados():
        nome_novo = nome_campo.text().strip()
        sobrenome_novo = sobrenome_campo.text().strip()
        email_novo = email_campo.text().strip().lower()
        cpf_novo = cpf.text().strip() or None

        if not nome_novo or not sobrenome_novo or not email_novo:
            QMessageBox.warning(
                tela,
                "Atenção",
                "Nome, sobrenome e e-mail são obrigatórios."
            )
            return

        salvar.setEnabled(False)

        try:
            # Reconsulta os objetos dentro da sessão ativa.
            # Isso evita tentar salvar objetos SQLAlchemy desconectados.
            with app.app_context():
                usuario_db = database.session.get(Usuario, usuario_id)

                if usuario_db is None:
                    raise RuntimeError("Usuário não encontrado no banco.")

                email_em_uso = Usuario.query.filter(
                    Usuario.email == email_novo,
                    Usuario.id != usuario_id
                ).first()

                if email_em_uso:
                    QMessageBox.warning(
                        tela,
                        "E-mail em uso",
                        "Este e-mail já está cadastrado para outro usuário."
                    )
                    return

                perfil_db = PerfilUsuario.query.filter_by(
                    id_usuario=usuario_id
                ).first()

                if perfil_db is None:
                    perfil_db = PerfilUsuario(id_usuario=usuario_id)
                    database.session.add(perfil_db)

                if cpf_novo:
                    cpf_em_uso = PerfilUsuario.query.filter(
                        PerfilUsuario.cpf == cpf_novo,
                        PerfilUsuario.id_usuario != usuario_id
                    ).first()

                    if cpf_em_uso:
                        QMessageBox.warning(
                            tela,
                            "CPF em uso",
                            "Este CPF já está vinculado a outro usuário."
                        )
                        return

                usuario_db.nome = nome_novo
                usuario_db.sobrenome = sobrenome_novo
                usuario_db.email = email_novo

                perfil_db.telefone = telefone.text().strip() or None
                perfil_db.cpf = cpf_novo
                perfil_db.data_nascimento = nascimento.date().toPython()
                perfil_db.endereco = endereco.text().strip() or None
                perfil_db.cidade = cidade.text().strip() or None
                perfil_db.estado = estado.text().strip() or None
                perfil_db.cep = cep.text().strip() or None

                database.session.commit()

            # Atualiza também a interface e o objeto usado pela janela.
            usuario.nome = nome_novo
            usuario.sobrenome = sobrenome_novo
            usuario.email = email_novo

            nome_resumo.setText(f"{nome_novo} {sobrenome_novo}")
            email_resumo.setText(email_novo)

            QMessageBox.information(
                tela,
                "AFGMED",
                "Perfil atualizado e salvo no banco!"
            )

        except IntegrityError:
            with app.app_context():
                database.session.rollback()

            QMessageBox.critical(
                tela,
                "Erro",
                "Não foi possível salvar. Verifique se o e-mail ou CPF já está em uso."
            )

        except Exception as erro:
            with app.app_context():
                database.session.rollback()

            QMessageBox.critical(
                tela,
                "Erro",
                f"Não foi possível salvar o perfil:\n{erro}"
            )

        finally:
            salvar.setEnabled(True)

    salvar.clicked.connect(salvar_dados)

    coluna_dados = QVBoxLayout()
    coluna_dados.addWidget(dados_pessoais)
    coluna_dados.addWidget(dados_complementares)
    coluna_dados.addWidget(endereco_box)
    coluna_dados.addWidget(salvar)
    coluna_dados.addStretch()

    layout_principal.addLayout(coluna_perfil)
    layout_principal.addLayout(coluna_dados)

    tela.setLayout(layout_principal)
    return tela