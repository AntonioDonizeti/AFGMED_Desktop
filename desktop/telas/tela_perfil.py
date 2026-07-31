from pathlib import Path
from shutil import copy2
from uuid import uuid4

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDateEdit,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import IntegrityError

from desktop.estilos import aplicar_estilo
from projetoafgmed import app, database
from projetoafgmed.models import PerfilUsuario, Usuario


BASE_DIR = Path(__file__).resolve().parent.parent.parent

PASTA_FOTOS_PERFIL = (
    BASE_DIR
    / "projetoafgmed"
    / "static"
    / "fotos_perfil"
)

PASTA_FOTOS_PERFIL.mkdir(
    parents=True,
    exist_ok=True,
)

EXTENSOES_PERMITIDAS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

TAMANHO_MAXIMO_FOTO = 5 * 1024 * 1024


class TelaPerfil(QWidget):
    def __init__(self, usuario=None):
        super().__init__()

        self.usuario = usuario
        self.usuario_id = (
            usuario.id
            if usuario is not None
            else None
        )

        self.arquivo_foto_selecionada = None
        self.remover_foto_pendente = False
        self.nome_foto_atual = ""

        self.setObjectName("paginaPerfil")

        aplicar_estilo(
            self,
            "perfil.qss",
        )

        self.criar_interface()

        if self.usuario_id is None:
            self.desativar_tela()
            return

        self.carregar_dados()

    # =====================================================
    # INTERFACE
    # =====================================================

    def criar_interface(self):
        layout_externo = QVBoxLayout(self)

        layout_externo.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.scroll = QScrollArea()
        self.scroll.setObjectName("scrollPerfil")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        container = QWidget()
        container.setObjectName("containerPerfil")

        layout_container = QHBoxLayout(container)

        layout_container.setContentsMargins(
            20,
            20,
            20,
            24,
        )

        layout_container.setSpacing(20)
        layout_container.setAlignment(Qt.AlignTop)

        self.criar_painel_resumo()
        self.criar_painel_dados()

        layout_container.addWidget(
            self.painel_resumo,
            0,
            Qt.AlignTop,
        )

        layout_container.addWidget(
            self.painel_dados,
            1,
            Qt.AlignTop,
        )

        self.scroll.setWidget(container)
        layout_externo.addWidget(self.scroll)

    def criar_painel_resumo(self):
        self.painel_resumo = QFrame()
        self.painel_resumo.setObjectName(
            "painelResumoPerfil"
        )

        self.painel_resumo.setFixedWidth(250)
        self.painel_resumo.setMinimumHeight(500)

        layout = QVBoxLayout(
            self.painel_resumo
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        layout.setSpacing(12)

        self.foto = QLabel("Sem foto")
        self.foto.setObjectName("fotoPerfil")
        self.foto.setFixedSize(175, 175)
        self.foto.setAlignment(Qt.AlignCenter)

        self.botao_alterar_foto = QPushButton(
            "Alterar foto"
        )

        self.botao_alterar_foto.setObjectName(
            "botaoAlterarFoto"
        )

        self.botao_alterar_foto.setMinimumHeight(40)

        self.botao_remover_foto = QPushButton(
            "Remover foto"
        )

        self.botao_remover_foto.setObjectName(
            "botaoRemoverFoto"
        )

        self.botao_remover_foto.setMinimumHeight(38)

        self.nome_resumo = QLabel("Usuário")
        self.nome_resumo.setObjectName(
            "nomeResumoPerfil"
        )
        self.nome_resumo.setAlignment(Qt.AlignCenter)
        self.nome_resumo.setWordWrap(True)

        self.email_resumo = QLabel()
        self.email_resumo.setObjectName(
            "emailResumoPerfil"
        )
        self.email_resumo.setAlignment(Qt.AlignCenter)
        self.email_resumo.setWordWrap(True)

        self.tipo_resumo = QLabel()
        self.tipo_resumo.setObjectName(
            "tipoResumoPerfil"
        )
        self.tipo_resumo.setAlignment(Qt.AlignCenter)

        layout.addWidget(
            self.foto,
            alignment=Qt.AlignHCenter,
        )

        layout.addWidget(self.botao_alterar_foto)
        layout.addWidget(self.botao_remover_foto)

        layout.addSpacing(8)
        layout.addWidget(self.nome_resumo)
        layout.addWidget(self.email_resumo)
        layout.addWidget(self.tipo_resumo)
        layout.addStretch()

        self.botao_alterar_foto.clicked.connect(
            self.selecionar_foto
        )

        self.botao_remover_foto.clicked.connect(
            self.marcar_remocao_foto
        )

    def criar_painel_dados(self):
        self.painel_dados = QFrame()
        self.painel_dados.setObjectName(
            "painelDadosPerfil"
        )

        self.painel_dados.setMinimumWidth(570)

        layout = QVBoxLayout(
            self.painel_dados
        )

        layout.setContentsMargins(
            26,
            24,
            26,
            26,
        )

        layout.setSpacing(18)

        titulo = QLabel("Dados do perfil")
        titulo.setObjectName("tituloPerfil")

        subtitulo = QLabel(
            "Atualize seus dados pessoais, endereço e foto."
        )
        subtitulo.setObjectName("subtituloPerfil")

        grupo_pessoais = self.criar_grupo_pessoais()
        grupo_complementares = (
            self.criar_grupo_complementares()
        )
        grupo_endereco = self.criar_grupo_endereco()

        area_salvar = QHBoxLayout()
        area_salvar.addStretch()

        self.botao_salvar = QPushButton(
            "Salvar alterações"
        )

        self.botao_salvar.setObjectName(
            "botaoSalvarPerfil"
        )

        self.botao_salvar.setMinimumHeight(46)
        self.botao_salvar.setMinimumWidth(180)

        area_salvar.addWidget(self.botao_salvar)

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addWidget(grupo_pessoais)
        layout.addWidget(grupo_complementares)
        layout.addWidget(grupo_endereco)
        layout.addLayout(area_salvar)

        self.botao_salvar.clicked.connect(
            self.salvar_dados
        )

    def criar_grupo_pessoais(self):
        grupo = QGroupBox("Dados pessoais")
        grupo.setObjectName("grupoPerfil")

        grid = QGridLayout(grupo)

        grid.setContentsMargins(
            18,
            24,
            18,
            18,
        )

        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(14)

        self.campo_nome = self.criar_campo()
        self.campo_sobrenome = self.criar_campo()
        self.campo_email = self.criar_campo()

        self.campo_nome.setReadOnly(True)
        self.campo_sobrenome.setReadOnly(True)
        self.campo_email.setReadOnly(True)

        self.campo_nome.setObjectName(
            "campoSomenteLeitura"
        )
        self.campo_sobrenome.setObjectName(
            "campoSomenteLeitura"
        )
        self.campo_email.setObjectName(
            "campoSomenteLeitura"
        )

        self.adicionar_linha(
            grid,
            0,
            "Nome:",
            self.campo_nome,
        )

        self.adicionar_linha(
            grid,
            1,
            "Sobrenome:",
            self.campo_sobrenome,
        )

        self.adicionar_linha(
            grid,
            2,
            "E-mail:",
            self.campo_email,
        )

        grid.setColumnStretch(1, 1)

        return grupo

    def criar_grupo_complementares(self):
        grupo = QGroupBox(
            "Dados complementares"
        )

        grupo.setObjectName("grupoPerfil")

        grid = QGridLayout(grupo)

        grid.setContentsMargins(
            18,
            24,
            18,
            18,
        )

        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(14)

        self.campo_telefone = self.criar_campo()
        self.campo_cpf = self.criar_campo()

        self.campo_telefone.setPlaceholderText(
            "Ex.: (11) 99999-9999"
        )
        self.campo_telefone.setMaxLength(20)

        self.campo_cpf.setPlaceholderText(
            "Somente números"
        )
        self.campo_cpf.setMaxLength(14)

        self.campo_nascimento = QDateEdit()
        self.campo_nascimento.setMinimumHeight(42)
        self.campo_nascimento.setCalendarPopup(True)
        self.campo_nascimento.setDisplayFormat(
            "dd/MM/yyyy"
        )
        self.campo_nascimento.setMaximumDate(
            QDate.currentDate()
        )

        self.adicionar_linha(
            grid,
            0,
            "Telefone:",
            self.campo_telefone,
        )

        self.adicionar_linha(
            grid,
            1,
            "CPF:",
            self.campo_cpf,
        )

        self.adicionar_linha(
            grid,
            2,
            "Nascimento:",
            self.campo_nascimento,
        )

        grid.setColumnStretch(1, 1)

        return grupo

    def criar_grupo_endereco(self):
        grupo = QGroupBox("Endereço")
        grupo.setObjectName("grupoPerfil")

        grid = QGridLayout(grupo)

        grid.setContentsMargins(
            18,
            24,
            18,
            18,
        )

        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(14)

        self.campo_endereco = self.criar_campo()
        self.campo_cidade = self.criar_campo()
        self.campo_estado = self.criar_campo()
        self.campo_cep = self.criar_campo()

        self.campo_estado.setMaxLength(2)
        self.campo_estado.setPlaceholderText(
            "Ex.: SP"
        )

        self.campo_cep.setMaxLength(9)
        self.campo_cep.setPlaceholderText(
            "Ex.: 00000-000"
        )

        self.adicionar_linha(
            grid,
            0,
            "Endereço:",
            self.campo_endereco,
        )

        self.adicionar_linha(
            grid,
            1,
            "Cidade:",
            self.campo_cidade,
        )

        self.adicionar_linha(
            grid,
            2,
            "Estado:",
            self.campo_estado,
        )

        self.adicionar_linha(
            grid,
            3,
            "CEP:",
            self.campo_cep,
        )

        grid.setColumnStretch(1, 1)

        return grupo

    @staticmethod
    def criar_campo():
        campo = QLineEdit()
        campo.setMinimumHeight(42)
        return campo

    @staticmethod
    def adicionar_linha(
        grid,
        linha,
        texto,
        campo,
    ):
        rotulo = QLabel(texto)

        rotulo.setObjectName(
            "rotuloCampoPerfil"
        )

        rotulo.setMinimumWidth(85)

        rotulo.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        grid.addWidget(
            rotulo,
            linha,
            0,
        )

        grid.addWidget(
            campo,
            linha,
            1,
        )

    # =====================================================
    # CARREGAMENTO
    # =====================================================

    def carregar_dados(self):
        self.arquivo_foto_selecionada = None
        self.remover_foto_pendente = False

        try:
            with app.app_context():
                usuario_banco = database.session.get(
                    Usuario,
                    self.usuario_id,
                )

                if usuario_banco is None:
                    raise ValueError(
                        "Usuário não encontrado."
                    )

                perfil_banco = (
                    PerfilUsuario.query.filter_by(
                        id_usuario=self.usuario_id
                    ).first()
                )

                dados_usuario = {
                    "nome": usuario_banco.nome or "",
                    "sobrenome": (
                        usuario_banco.sobrenome or ""
                    ),
                    "email": usuario_banco.email or "",
                    "foto": usuario_banco.foto or "",
                    "is_admin": bool(
                        usuario_banco.is_admin
                    ),
                    "is_medico": bool(
                        usuario_banco.is_medico
                    ),
                }

                if perfil_banco:
                    dados_perfil = {
                        "telefone": (
                            perfil_banco.telefone or ""
                        ),
                        "cpf": perfil_banco.cpf or "",
                        "data_nascimento": (
                            perfil_banco.data_nascimento
                        ),
                        "endereco": (
                            perfil_banco.endereco or ""
                        ),
                        "cidade": (
                            perfil_banco.cidade or ""
                        ),
                        "estado": (
                            perfil_banco.estado or ""
                        ),
                        "cep": perfil_banco.cep or "",
                    }
                else:
                    dados_perfil = {
                        "telefone": "",
                        "cpf": "",
                        "data_nascimento": None,
                        "endereco": "",
                        "cidade": "",
                        "estado": "",
                        "cep": "",
                    }

            self.nome_foto_atual = dados_usuario[
                "foto"
            ]

            nome_completo = (
                f"{dados_usuario['nome']} "
                f"{dados_usuario['sobrenome']}"
            ).strip()

            self.nome_resumo.setText(
                nome_completo or "Usuário"
            )

            self.email_resumo.setText(
                dados_usuario["email"]
            )

            if dados_usuario["is_admin"]:
                tipo = "Administrador"
            elif dados_usuario["is_medico"]:
                tipo = "Médico"
            else:
                tipo = "Paciente"

            self.tipo_resumo.setText(tipo)

            self.campo_nome.setText(
                dados_usuario["nome"]
            )
            self.campo_sobrenome.setText(
                dados_usuario["sobrenome"]
            )
            self.campo_email.setText(
                dados_usuario["email"]
            )

            self.campo_telefone.setText(
                dados_perfil["telefone"]
            )
            self.campo_cpf.setText(
                dados_perfil["cpf"]
            )
            self.campo_endereco.setText(
                dados_perfil["endereco"]
            )
            self.campo_cidade.setText(
                dados_perfil["cidade"]
            )
            self.campo_estado.setText(
                dados_perfil["estado"]
            )
            self.campo_cep.setText(
                dados_perfil["cep"]
            )

            data_nascimento = dados_perfil[
                "data_nascimento"
            ]

            if data_nascimento:
                self.campo_nascimento.setDate(
                    QDate(
                        data_nascimento.year,
                        data_nascimento.month,
                        data_nascimento.day,
                    )
                )
            else:
                self.campo_nascimento.setDate(
                    QDate.currentDate().addYears(-18)
                )

            self.exibir_foto_salva(
                self.nome_foto_atual
            )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível carregar o perfil."
                    f"\n\n{erro}"
                ),
            )

    def recarregar(self):
        self.carregar_dados()

    def desativar_tela(self):
        self.nome_resumo.setText(
            "Usuário não identificado"
        )

        self.botao_alterar_foto.setEnabled(False)
        self.botao_remover_foto.setEnabled(False)
        self.botao_salvar.setEnabled(False)

    # =====================================================
    # FOTO
    # =====================================================

    def selecionar_foto(self):
        arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar foto de perfil",
            "",
            (
                "Imagens (*.png *.jpg *.jpeg *.webp);;"
                "Todos os arquivos (*.*)"
            ),
        )

        if not arquivo:
            return

        caminho = Path(arquivo)
        extensao = caminho.suffix.lower()

        if extensao not in EXTENSOES_PERMITIDAS:
            QMessageBox.warning(
                self,
                "Formato inválido",
                (
                    "Selecione uma imagem PNG, JPG, "
                    "JPEG ou WEBP."
                ),
            )
            return

        if caminho.stat().st_size > TAMANHO_MAXIMO_FOTO:
            QMessageBox.warning(
                self,
                "Imagem muito grande",
                "A imagem deve possuir no máximo 5 MB.",
            )
            return

        imagem = QPixmap(str(caminho))

        if imagem.isNull():
            QMessageBox.warning(
                self,
                "Imagem inválida",
                "Não foi possível abrir a imagem.",
            )
            return

        self.arquivo_foto_selecionada = caminho
        self.remover_foto_pendente = False

        self.mostrar_pixmap(imagem)

    def marcar_remocao_foto(self):
        possui_foto = bool(
            self.nome_foto_atual
            or self.arquivo_foto_selecionada
        )

        if not possui_foto:
            QMessageBox.information(
                self,
                "Foto",
                "O perfil já está sem foto.",
            )
            return

        resposta = QMessageBox.question(
            self,
            "Remover foto",
            (
                "Deseja remover a foto de perfil?\n\n"
                "Clique em Salvar alterações para "
                "confirmar."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if resposta != QMessageBox.Yes:
            return

        self.arquivo_foto_selecionada = None
        self.remover_foto_pendente = True

        self.foto.clear()
        self.foto.setText("Sem foto")

    def exibir_foto_salva(self, nome_arquivo):
        if not nome_arquivo:
            self.foto.clear()
            self.foto.setText("Sem foto")
            return

        nome_seguro = Path(nome_arquivo).name

        caminho = (
            PASTA_FOTOS_PERFIL
            / nome_seguro
        )

        if not caminho.exists():
            self.foto.clear()
            self.foto.setText("Sem foto")
            return

        imagem = QPixmap(str(caminho))

        if imagem.isNull():
            self.foto.clear()
            self.foto.setText("Imagem inválida")
            return

        self.mostrar_pixmap(imagem)

    def mostrar_pixmap(self, imagem):
        self.foto.clear()

        self.foto.setPixmap(
            imagem.scaled(
                160,
                160,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def copiar_nova_foto(self):
        origem = self.arquivo_foto_selecionada

        if origem is None:
            return None, None

        extensao = origem.suffix.lower()

        nome_novo = (
            f"perfil_{self.usuario_id}_"
            f"{uuid4().hex[:12]}"
            f"{extensao}"
        )

        destino = (
            PASTA_FOTOS_PERFIL
            / nome_novo
        )

        copy2(origem, destino)

        return nome_novo, destino

    def apagar_foto_antiga(self, nome_arquivo):
        if not nome_arquivo:
            return

        nome_seguro = Path(nome_arquivo).name

        prefixo = f"perfil_{self.usuario_id}_"

        if not nome_seguro.startswith(prefixo):
            return

        caminho = (
            PASTA_FOTOS_PERFIL
            / nome_seguro
        )

        try:
            if caminho.exists():
                caminho.unlink()
        except OSError:
            pass

    # =====================================================
    # SALVAMENTO
    # =====================================================

    def salvar_dados(self):
        telefone = (
            self.campo_telefone.text().strip()
            or None
        )

        cpf = (
            self.campo_cpf.text().strip()
            or None
        )

        endereco = (
            self.campo_endereco.text().strip()
            or None
        )

        cidade = (
            self.campo_cidade.text().strip()
            or None
        )

        estado = (
            self.campo_estado.text()
            .strip()
            .upper()
            or None
        )

        cep = (
            self.campo_cep.text().strip()
            or None
        )

        if estado and len(estado) != 2:
            QMessageBox.warning(
                self,
                "Estado inválido",
                "Informe a sigla com dois caracteres.",
            )
            return

        arquivo_novo = None
        nome_nova_foto = None
        nome_foto_anterior = ""

        self.botao_salvar.setEnabled(False)
        self.botao_alterar_foto.setEnabled(False)
        self.botao_remover_foto.setEnabled(False)
        self.botao_salvar.setText("Salvando...")

        try:
            with app.app_context():
                try:
                    usuario_banco = database.session.get(
                        Usuario,
                        self.usuario_id,
                    )

                    if usuario_banco is None:
                        raise ValueError(
                            "Usuário não encontrado."
                        )

                    nome_foto_anterior = (
                        usuario_banco.foto or ""
                    )

                    if cpf:
                        cpf_existente = (
                            PerfilUsuario.query.filter(
                                PerfilUsuario.cpf == cpf,
                                PerfilUsuario.id_usuario
                                != self.usuario_id,
                            ).first()
                        )

                        if cpf_existente:
                            raise ValueError(
                                "Este CPF já está cadastrado."
                            )

                    perfil_banco = (
                        PerfilUsuario.query.filter_by(
                            id_usuario=self.usuario_id
                        ).first()
                    )

                    if perfil_banco is None:
                        perfil_banco = PerfilUsuario(
                            id_usuario=self.usuario_id
                        )

                        database.session.add(
                            perfil_banco
                        )

                    perfil_banco.telefone = telefone
                    perfil_banco.cpf = cpf
                    perfil_banco.data_nascimento = (
                        self.campo_nascimento
                        .date()
                        .toPython()
                    )
                    perfil_banco.endereco = endereco
                    perfil_banco.cidade = cidade
                    perfil_banco.estado = estado
                    perfil_banco.cep = cep

                    if self.remover_foto_pendente:
                        usuario_banco.foto = None

                    elif self.arquivo_foto_selecionada:
                        (
                            nome_nova_foto,
                            arquivo_novo,
                        ) = self.copiar_nova_foto()

                        usuario_banco.foto = (
                            nome_nova_foto
                        )

                    database.session.commit()

                except Exception:
                    database.session.rollback()

                    if (
                        arquivo_novo is not None
                        and arquivo_novo.exists()
                    ):
                        arquivo_novo.unlink()

                    raise

            if self.remover_foto_pendente:
                self.apagar_foto_antiga(
                    nome_foto_anterior
                )

                self.nome_foto_atual = ""

                if self.usuario is not None:
                    self.usuario.foto = ""

            elif nome_nova_foto:
                self.apagar_foto_antiga(
                    nome_foto_anterior
                )

                self.nome_foto_atual = (
                    nome_nova_foto
                )

                if self.usuario is not None:
                    self.usuario.foto = (
                        nome_nova_foto
                    )

            self.arquivo_foto_selecionada = None
            self.remover_foto_pendente = False

            self.campo_estado.setText(
                estado or ""
            )

            self.exibir_foto_salva(
                self.nome_foto_atual
            )

            QMessageBox.information(
                self,
                "AFGMED",
                "Perfil atualizado com sucesso.",
            )

        except ValueError as erro:
            QMessageBox.warning(
                self,
                "Dados inválidos",
                str(erro),
            )

        except IntegrityError:
            QMessageBox.warning(
                self,
                "Dados duplicados",
                "O CPF informado já está em uso.",
            )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível salvar o perfil."
                    f"\n\n{erro}"
                ),
            )

        finally:
            self.botao_salvar.setEnabled(True)
            self.botao_alterar_foto.setEnabled(True)
            self.botao_remover_foto.setEnabled(True)
            self.botao_salvar.setText(
                "Salvar alterações"
            )


def tela_perfil(usuario=None):
    return TelaPerfil(usuario)