import os

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import IntegrityError

from projetoafgmed import app, database
from projetoafgmed.models import PerfilUsuario, Usuario


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

PASTA_FOTOS_PERFIL = os.path.join(
    BASE_DIR,
    "projetoafgmed",
    "static",
    "fotos_perfil",
)


def tela_perfil(usuario=None):
    tela = QWidget()

    if usuario is None:
        layout = QVBoxLayout(tela)

        mensagem = QLabel(
            "Não foi possível identificar o usuário conectado."
        )

        mensagem.setAlignment(Qt.AlignCenter)
        mensagem.setStyleSheet("color: #b00020;")

        layout.addWidget(mensagem)

        return tela

    usuario_id = usuario.id

    # Busca os dados atuais do banco.
    with app.app_context():
        usuario_banco = Usuario.query.filter_by(
            id=usuario_id
        ).first()

        if usuario_banco is None:
            layout = QVBoxLayout(tela)

            mensagem = QLabel(
                "Usuário não encontrado no banco de dados."
            )

            mensagem.setAlignment(Qt.AlignCenter)
            mensagem.setStyleSheet("color: #b00020;")

            layout.addWidget(mensagem)

            return tela

        perfil = PerfilUsuario.query.filter_by(
            id_usuario=usuario_id
        ).first()

        usuario_dados = {
            "nome": usuario_banco.nome or "",
            "sobrenome": usuario_banco.sobrenome or "",
            "email": usuario_banco.email or "",
            "foto": usuario_banco.foto or "",
            "is_admin": bool(usuario_banco.is_admin),
            "is_medico": bool(usuario_banco.is_medico),
        }

        if perfil is not None:
            perfil_dados = {
                "telefone": perfil.telefone or "",
                "cpf": perfil.cpf or "",
                "data_nascimento": perfil.data_nascimento,
                "endereco": perfil.endereco or "",
                "cidade": perfil.cidade or "",
                "estado": perfil.estado or "",
                "cep": perfil.cep or "",
            }
        else:
            perfil_dados = {
                "telefone": "",
                "cpf": "",
                "data_nascimento": None,
                "endereco": "",
                "cidade": "",
                "estado": "",
                "cep": "",
            }

    layout_principal = QHBoxLayout(tela)
    layout_principal.setContentsMargins(
        25,
        25,
        25,
        25
    )
    layout_principal.setSpacing(30)

    # ======================================
    # RESUMO DO PERFIL
    # ======================================

    coluna_perfil = QVBoxLayout()
    coluna_perfil.setSpacing(10)

    foto = QLabel()
    foto.setFixedSize(160, 160)
    foto.setAlignment(Qt.AlignCenter)

    foto.setStyleSheet(
        """
        QLabel {
            border: 1px solid #bdbdbd;
            border-radius: 8px;
        }
        """
    )

    if usuario_dados["foto"]:
        caminho_foto = os.path.join(
            PASTA_FOTOS_PERFIL,
            usuario_dados["foto"]
        )
    else:
        caminho_foto = ""

    if caminho_foto and os.path.exists(caminho_foto):
        imagem = QPixmap(caminho_foto)

        foto.setPixmap(
            imagem.scaled(
                150,
                150,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
    else:
        foto.setText("Sem foto")

    nome_completo = (
        f'{usuario_dados["nome"]} '
        f'{usuario_dados["sobrenome"]}'
    ).strip()

    nome = QLabel(
        nome_completo or "Usuário"
    )

    nome.setStyleSheet(
        "font-size: 20px; font-weight: bold;"
    )

    nome.setWordWrap(True)

    email_label = QLabel(
        usuario_dados["email"]
    )
    email_label.setWordWrap(True)

    if usuario_dados["is_admin"]:
        texto_tipo = "Administrador"
    elif usuario_dados["is_medico"]:
        texto_tipo = "Médico"
    else:
        texto_tipo = "Paciente"

    tipo = QLabel(texto_tipo)

    coluna_perfil.addWidget(
        foto,
        alignment=Qt.AlignHCenter
    )

    coluna_perfil.addWidget(nome)
    coluna_perfil.addWidget(email_label)
    coluna_perfil.addWidget(tipo)
    coluna_perfil.addStretch()

    # ======================================
    # DADOS PESSOAIS
    # ======================================

    dados_pessoais = QGroupBox(
        "Dados pessoais"
    )

    layout_pessoais = QFormLayout(
        dados_pessoais
    )

    nome_campo = QLineEdit(
        usuario_dados["nome"]
    )

    sobrenome_campo = QLineEdit(
        usuario_dados["sobrenome"]
    )

    email_campo = QLineEdit(
        usuario_dados["email"]
    )

    nome_campo.setReadOnly(True)
    sobrenome_campo.setReadOnly(True)
    email_campo.setReadOnly(True)

    layout_pessoais.addRow(
        "Nome:",
        nome_campo
    )

    layout_pessoais.addRow(
        "Sobrenome:",
        sobrenome_campo
    )

    layout_pessoais.addRow(
        "E-mail:",
        email_campo
    )

    # ======================================
    # DADOS COMPLEMENTARES
    # ======================================

    dados_complementares = QGroupBox(
        "Dados complementares"
    )

    layout_complementares = QFormLayout(
        dados_complementares
    )

    telefone = QLineEdit(
        perfil_dados["telefone"]
    )

    telefone.setPlaceholderText(
        "Ex.: (11) 99999-9999"
    )

    telefone.setMaxLength(20)

    cpf = QLineEdit(
        perfil_dados["cpf"]
    )

    cpf.setPlaceholderText(
        "Somente números"
    )

    cpf.setMaxLength(14)

    nascimento = QDateEdit()
    nascimento.setCalendarPopup(True)
    nascimento.setDisplayFormat(
        "dd/MM/yyyy"
    )

    nascimento.setMaximumDate(
        QDate.currentDate()
    )

    if perfil_dados["data_nascimento"]:
        data_nascimento = perfil_dados[
            "data_nascimento"
        ]

        nascimento.setDate(
            QDate(
                data_nascimento.year,
                data_nascimento.month,
                data_nascimento.day,
            )
        )
    else:
        nascimento.setDate(
            QDate.currentDate().addYears(-18)
        )

    layout_complementares.addRow(
        "Telefone:",
        telefone
    )

    layout_complementares.addRow(
        "CPF:",
        cpf
    )

    layout_complementares.addRow(
        "Data de nascimento:",
        nascimento
    )

    # ======================================
    # ENDEREÇO
    # ======================================

    endereco_box = QGroupBox("Endereço")
    layout_endereco = QFormLayout(
        endereco_box
    )

    endereco = QLineEdit(
        perfil_dados["endereco"]
    )

    cidade = QLineEdit(
        perfil_dados["cidade"]
    )

    estado = QLineEdit(
        perfil_dados["estado"]
    )

    cep = QLineEdit(
        perfil_dados["cep"]
    )

    estado.setMaxLength(2)
    estado.setPlaceholderText("Ex.: SP")

    cep.setMaxLength(9)
    cep.setPlaceholderText("Ex.: 00000-000")

    layout_endereco.addRow(
        "Endereço:",
        endereco
    )

    layout_endereco.addRow(
        "Cidade:",
        cidade
    )

    layout_endereco.addRow(
        "Estado:",
        estado
    )

    layout_endereco.addRow(
        "CEP:",
        cep
    )

    salvar = QPushButton(
        "Salvar alterações"
    )

    salvar.setMinimumHeight(42)

    def salvar_dados():
        telefone_valor = (
            telefone.text().strip() or None
        )

        cpf_valor = (
            cpf.text().strip() or None
        )

        endereco_valor = (
            endereco.text().strip() or None
        )

        cidade_valor = (
            cidade.text().strip() or None
        )

        estado_valor = (
            estado.text().strip().upper() or None
        )

        cep_valor = (
            cep.text().strip() or None
        )

        salvar.setEnabled(False)
        salvar.setText("Salvando...")

        try:
            with app.app_context():
                try:
                    # Verifica se o CPF pertence
                    # a outro usuário.
                    if cpf_valor:
                        cpf_existente = (
                            PerfilUsuario.query.filter(
                                PerfilUsuario.cpf
                                == cpf_valor,
                                PerfilUsuario.id_usuario
                                != usuario_id,
                            ).first()
                        )

                        if cpf_existente is not None:
                            raise ValueError(
                                "Este CPF já está cadastrado."
                            )

                    perfil_banco = (
                        PerfilUsuario.query.filter_by(
                            id_usuario=usuario_id
                        ).first()
                    )

                    if perfil_banco is None:
                        perfil_banco = PerfilUsuario(
                            id_usuario=usuario_id
                        )

                        database.session.add(
                            perfil_banco
                        )

                    perfil_banco.telefone = (
                        telefone_valor
                    )

                    perfil_banco.cpf = (
                        cpf_valor
                    )

                    perfil_banco.data_nascimento = (
                        nascimento.date().toPython()
                    )

                    perfil_banco.endereco = (
                        endereco_valor
                    )

                    perfil_banco.cidade = (
                        cidade_valor
                    )

                    perfil_banco.estado = (
                        estado_valor
                    )

                    perfil_banco.cep = (
                        cep_valor
                    )

                    # Grava as mudanças no afgmed.db.
                    database.session.commit()

                except Exception:
                    database.session.rollback()
                    raise

            estado.setText(
                estado_valor or ""
            )

            QMessageBox.information(
                tela,
                "AFGMED",
                "Perfil atualizado!",
            )

        except ValueError as erro:
            QMessageBox.warning(
                tela,
                "Dados inválidos",
                str(erro),
            )

        except IntegrityError:
            QMessageBox.warning(
                tela,
                "Dados duplicados",
                (
                    "O CPF informado já está sendo "
                    "usado por outro usuário."
                ),
            )

        except Exception as erro:
            QMessageBox.critical(
                tela,
                "Erro",
                (
                    "Não foi possível salvar o perfil."
                    f"\n\n{erro}"
                ),
            )

        finally:
            salvar.setEnabled(True)
            salvar.setText(
                "Salvar alterações"
            )

    salvar.clicked.connect(
        salvar_dados
    )

    coluna_dados = QVBoxLayout()
    coluna_dados.setSpacing(15)

    coluna_dados.addWidget(
        dados_pessoais
    )

    coluna_dados.addWidget(
        dados_complementares
    )

    coluna_dados.addWidget(
        endereco_box
    )

    coluna_dados.addWidget(
        salvar
    )

    coluna_dados.addStretch()

    layout_principal.addLayout(
        coluna_perfil,
        1
    )

    layout_principal.addLayout(
        coluna_dados,
        3
    )

    return tela