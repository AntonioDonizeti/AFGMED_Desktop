import re
import shutil
import unicodedata
from datetime import date
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import func

from desktop.estilos import aplicar_estilo
from projetoafgmed import app, database
from projetoafgmed.models import Consulta, Medico, Pedido, Produto, Usuario
from projetoafgmed.servicos_medicos import sincronizar_usuario_medico
from projetoafgmed.servicos_produtos import ErroProduto, excluir_produto


BASE_DIR = Path(__file__).resolve().parents[2]
PASTA_PRODUTOS = BASE_DIR / "projetoafgmed" / "static" / "fotos_produtos"
PASTA_MEDICOS = BASE_DIR / "projetoafgmed" / "static" / "fotos_medicos"


def formatar_real(valor):
    texto = (
        f"{float(valor or 0):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    return f"R$ {texto}"


def normalizar_busca(valor):
    """Normaliza texto para pesquisas sem diferença entre maiúsculas e acentos."""
    texto = unicodedata.normalize(
        "NFKD",
        str(valor or ""),
    )
    return "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    ).casefold().strip()


def carregar_imagem_label(label, pasta, nome_arquivo, largura=170, altura=150):
    """Carrega uma imagem no QLabel ou exibe uma mensagem alternativa."""
    label.clear()
    nome_seguro = Path(nome_arquivo or "").name

    if not nome_seguro:
        label.setText("Sem imagem")
        return

    caminho = pasta / nome_seguro

    if not caminho.exists():
        label.setText("Imagem não encontrada")
        return

    imagem = QPixmap(str(caminho))

    if imagem.isNull():
        label.setText("Imagem inválida")
        return

    label.setPixmap(
        imagem.scaled(
            largura,
            altura,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
    )


def nome_arquivo_seguro(caminho):
    nome = Path(caminho).name
    base = re.sub(r"[^A-Za-z0-9_.-]+", "_", nome)
    return f"{uuid4().hex[:8]}_{base}"


def copiar_imagem(origem, pasta_destino):
    if not origem:
        return None

    origem_path = Path(origem)
    if not origem_path.exists():
        raise FileNotFoundError("A imagem selecionada não foi encontrada.")

    pasta_destino.mkdir(parents=True, exist_ok=True)
    nome = nome_arquivo_seguro(origem_path)
    shutil.copy2(origem_path, pasta_destino / nome)
    return nome


class DialogProduto(QDialog):
    def __init__(self, produto_id=None, parent=None):
        super().__init__(parent)
        self.produto_id = produto_id
        self.caminho_foto = ""
        self.setWindowTitle("Editar produto" if produto_id else "Cadastrar produto")
        self.resize(540, 610)
        aplicar_estilo(self, "admin.qss")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        titulo = QLabel("Editar produto" if produto_id else "Cadastrar produto")
        titulo.setObjectName("tituloDialogAdmin")
        layout.addWidget(titulo)

        formulario = QFormLayout()
        formulario.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        formulario.setHorizontalSpacing(18)
        formulario.setVerticalSpacing(12)

        self.nome = QLineEdit()
        self.descricao = QTextEdit()
        self.descricao.setMaximumHeight(100)
        self.preco = QDoubleSpinBox()
        self.preco.setRange(0, 9999999)
        self.preco.setDecimals(2)
        self.preco.setPrefix("R$ ")
        self.estoque = QSpinBox()
        self.estoque.setRange(0, 999999999)
        self.ativo = QCheckBox("Produto ativo")
        self.ativo.setChecked(True)

        foto_linha = QHBoxLayout()
        self.foto_label = QLabel("Nenhuma nova imagem selecionada")
        self.foto_label.setObjectName("textoAuxiliarAdmin")
        botao_foto = QPushButton("Selecionar imagem")
        botao_foto.clicked.connect(self.selecionar_foto)
        foto_linha.addWidget(self.foto_label, 1)
        foto_linha.addWidget(botao_foto)

        formulario.addRow("Nome*", self.nome)
        formulario.addRow("Descrição", self.descricao)
        formulario.addRow("Preço*", self.preco)
        formulario.addRow("Estoque", self.estoque)
        formulario.addRow("Situação", self.ativo)
        formulario.addRow("Foto", foto_linha)

        layout.addLayout(formulario)
        layout.addStretch()

        botoes = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        botoes.button(QDialogButtonBox.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botoes.accepted.connect(self.salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

        if self.produto_id:
            self.carregar()

    def selecionar_foto(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar foto do produto",
            "",
            "Imagens (*.png *.jpg *.jpeg)",
        )
        if caminho:
            self.caminho_foto = caminho
            self.foto_label.setText(Path(caminho).name)

    def carregar(self):
        try:
            with app.app_context():
                produto = database.session.get(Produto, self.produto_id)
                if produto is None:
                    raise ValueError("Produto não encontrado.")

                dados = {
                    "nome": produto.nome or "",
                    "descricao": produto.descricao or "",
                    "preco": float(produto.preco or 0),
                    "estoque": int(produto.estoque or 0),
                    "ativo": bool(produto.ativo),
                    "foto": produto.foto or "",
                }

            self.nome.setText(dados["nome"])
            self.descricao.setPlainText(dados["descricao"])
            self.preco.setValue(dados["preco"])
            self.estoque.setValue(dados["estoque"])
            self.ativo.setChecked(dados["ativo"])
            self.foto_label.setText(
                f"Imagem atual: {dados['foto']}" if dados["foto"] else "Sem imagem"
            )

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))
            self.reject()

    def salvar(self):
        nome = self.nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Campo obrigatório", "Informe o nome do produto.")
            self.nome.setFocus()
            return

        try:
            nova_foto = copiar_imagem(self.caminho_foto, PASTA_PRODUTOS)

            with app.app_context():
                if self.produto_id:
                    produto = database.session.get(Produto, self.produto_id)
                    if produto is None:
                        raise ValueError("Produto não encontrado.")
                else:
                    produto = Produto()
                    database.session.add(produto)

                produto.nome = nome
                produto.descricao = self.descricao.toPlainText().strip()
                produto.preco = float(self.preco.value())
                produto.estoque = int(self.estoque.value())
                produto.ativo = self.ativo.isChecked()

                if nova_foto:
                    produto.foto = nova_foto
                elif not self.produto_id and not produto.foto:
                    produto.foto = "default.jpg"

                database.session.commit()

            self.accept()

        except Exception as erro:
            database.session.rollback()
            QMessageBox.critical(self, "Erro ao salvar produto", str(erro))


class DialogMedico(QDialog):
    def __init__(self, medico_id=None, parent=None):
        super().__init__(parent)
        self.medico_id = medico_id
        self.caminho_foto = ""
        self.setWindowTitle("Editar médico" if medico_id else "Cadastrar médico")
        self.resize(540, 540)
        aplicar_estilo(self, "admin.qss")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        titulo = QLabel("Editar médico" if medico_id else "Cadastrar médico")
        titulo.setObjectName("tituloDialogAdmin")
        layout.addWidget(titulo)

        formulario = QFormLayout()
        formulario.setHorizontalSpacing(18)
        formulario.setVerticalSpacing(12)

        self.nome = QLineEdit()
        self.sobrenome = QLineEdit()
        self.especialidade = QLineEdit()
        self.email = QLineEdit()
        self.telefone = QLineEdit()

        foto_linha = QHBoxLayout()
        self.foto_label = QLabel("Nenhuma nova imagem selecionada")
        self.foto_label.setObjectName("textoAuxiliarAdmin")
        botao_foto = QPushButton("Selecionar imagem")
        botao_foto.clicked.connect(self.selecionar_foto)
        foto_linha.addWidget(self.foto_label, 1)
        foto_linha.addWidget(botao_foto)

        formulario.addRow("Nome*", self.nome)
        formulario.addRow("Sobrenome*", self.sobrenome)
        formulario.addRow("Especialidade*", self.especialidade)
        formulario.addRow("E-mail*", self.email)
        formulario.addRow("Telefone", self.telefone)
        formulario.addRow("Foto", foto_linha)

        layout.addLayout(formulario)

        aviso = QLabel(
            "Ao salvar, o acesso médico será criado ou sincronizado com a senha padrão 123456."
        )
        aviso.setObjectName("avisoAdmin")
        aviso.setWordWrap(True)
        layout.addWidget(aviso)
        layout.addStretch()

        botoes = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        botoes.button(QDialogButtonBox.Save).setText("Salvar")
        botoes.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botoes.accepted.connect(self.salvar)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

        if self.medico_id:
            self.carregar()

    def selecionar_foto(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar foto do médico",
            "",
            "Imagens (*.png *.jpg *.jpeg)",
        )
        if caminho:
            self.caminho_foto = caminho
            self.foto_label.setText(Path(caminho).name)

    def carregar(self):
        try:
            with app.app_context():
                medico = database.session.get(Medico, self.medico_id)
                if medico is None:
                    raise ValueError("Médico não encontrado.")

                dados = {
                    "nome": medico.nome or "",
                    "sobrenome": medico.sobrenome or "",
                    "especialidade": medico.especialidade or "",
                    "email": medico.email or "",
                    "telefone": medico.telefone or "",
                    "foto": medico.foto or "",
                }

            self.nome.setText(dados["nome"])
            self.sobrenome.setText(dados["sobrenome"])
            self.especialidade.setText(dados["especialidade"])
            self.email.setText(dados["email"])
            self.telefone.setText(dados["telefone"])
            self.foto_label.setText(
                f"Imagem atual: {dados['foto']}" if dados["foto"] else "Sem imagem"
            )

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))
            self.reject()

    def salvar(self):
        nome = self.nome.text().strip()
        sobrenome = self.sobrenome.text().strip()
        especialidade = self.especialidade.text().strip()
        email = self.email.text().strip().lower()

        if not all([nome, sobrenome, especialidade, email]):
            QMessageBox.warning(
                self,
                "Campos obrigatórios",
                "Preencha nome, sobrenome, especialidade e e-mail.",
            )
            return

        if "@" not in email or "." not in email.split("@")[-1]:
            QMessageBox.warning(self, "E-mail inválido", "Informe um e-mail válido.")
            self.email.setFocus()
            return

        try:
            nova_foto = copiar_imagem(self.caminho_foto, PASTA_MEDICOS)

            with app.app_context():
                existente = Medico.query.filter(
                    func.lower(Medico.email) == email
                )
                if self.medico_id:
                    existente = existente.filter(Medico.id != self.medico_id)
                if existente.first():
                    raise ValueError("Já existe outro médico cadastrado com este e-mail.")

                if self.medico_id:
                    medico = database.session.get(Medico, self.medico_id)
                    if medico is None:
                        raise ValueError("Médico não encontrado.")
                else:
                    medico = Medico()
                    database.session.add(medico)

                medico.nome = nome
                medico.sobrenome = sobrenome
                medico.especialidade = especialidade
                medico.email = email
                medico.telefone = self.telefone.text().strip()

                if nova_foto:
                    medico.foto = nova_foto
                elif not self.medico_id and not medico.foto:
                    medico.foto = "default.jpg"

                database.session.flush()
                _, erro_usuario = sincronizar_usuario_medico(medico)
                if erro_usuario:
                    raise ValueError(erro_usuario)

                database.session.commit()

            self.accept()

        except Exception as erro:
            database.session.rollback()
            QMessageBox.critical(self, "Erro ao salvar médico", str(erro))


class TelaAdminBase(QWidget):
    def __init__(self, object_name, titulo, subtitulo):
        super().__init__()
        self.setObjectName(object_name)
        aplicar_estilo(self, "admin.qss")

        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(26, 22, 26, 26)
        self.layout_principal.setSpacing(18)

        cabecalho = QHBoxLayout()
        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(2)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloPaginaAdmin")
        label_subtitulo = QLabel(subtitulo)
        label_subtitulo.setObjectName("subtituloPaginaAdmin")
        label_subtitulo.setWordWrap(True)

        area_titulo.addWidget(label_titulo)
        area_titulo.addWidget(label_subtitulo)
        cabecalho.addLayout(area_titulo, 1)

        self.area_acoes_topo = QHBoxLayout()
        self.area_acoes_topo.setSpacing(9)
        cabecalho.addLayout(self.area_acoes_topo)
        self.layout_principal.addLayout(cabecalho)

    def criar_tabela(self, colunas):
        tabela = QTableWidget(0, len(colunas))
        tabela.setHorizontalHeaderLabels(colunas)
        tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabela.setSelectionMode(QAbstractItemView.SingleSelection)
        tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabela.verticalHeader().setVisible(False)
        tabela.setAlternatingRowColors(True)
        tabela.setSortingEnabled(False)
        return tabela

    @staticmethod
    def id_selecionado(tabela):
        linha = tabela.currentRow()
        if linha < 0:
            return None
        item = tabela.item(linha, 0)
        return int(item.text()) if item else None


class TelaAdminProdutos(TelaAdminBase):
    def __init__(self):
        super().__init__(
            "paginaAdminProdutos",
            "Gerenciar produtos",
            "Pesquise, filtre e selecione um produto para visualizar ou alterar seus dados.",
        )

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar por nome ou descrição...")
        self.busca.setClearButtonEnabled(True)
        self.busca.setMinimumWidth(250)
        self.busca.textChanged.connect(self.recarregar)

        self.filtro_status = QComboBox()
        self.filtro_status.addItem("Todos", "todos")
        self.filtro_status.addItem("Ativos", "ativos")
        self.filtro_status.addItem("Inativos", "inativos")
        self.filtro_status.currentIndexChanged.connect(self.recarregar)

        self.filtro_estoque = QComboBox()
        self.filtro_estoque.addItem("Qualquer estoque", "todos")
        self.filtro_estoque.addItem("Sem estoque", "sem")
        self.filtro_estoque.addItem("Estoque baixo", "baixo")
        self.filtro_estoque.addItem("Estoque normal", "normal")
        self.filtro_estoque.currentIndexChanged.connect(self.recarregar)

        novo = QPushButton("Novo produto")
        novo.setObjectName("botaoPrimario")
        novo.clicked.connect(self.novo_produto)

        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(self.recarregar)

        self.area_acoes_topo.addWidget(self.busca)
        self.area_acoes_topo.addWidget(self.filtro_status)
        self.area_acoes_topo.addWidget(self.filtro_estoque)
        self.area_acoes_topo.addWidget(novo)
        self.area_acoes_topo.addWidget(atualizar)

        area_conteudo = QHBoxLayout()
        area_conteudo.setSpacing(16)

        self.tabela = self.criar_tabela(
            ["ID", "Produto", "Preço", "Estoque", "Situação", "Imagem"]
        )
        self.tabela.setMinimumWidth(690)

        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        self.tabela.itemSelectionChanged.connect(self.atualizar_detalhes)
        self.tabela.doubleClicked.connect(self.editar_produto)

        self.painel_detalhes = self._criar_painel_detalhes()

        area_conteudo.addWidget(self.tabela, 3)
        area_conteudo.addWidget(self.painel_detalhes, 1)

        self.layout_principal.addLayout(area_conteudo, 1)
        self.recarregar()

    def _criar_painel_detalhes(self):
        painel = QFrame()
        painel.setObjectName("painelDetalhesAdmin")
        painel.setMinimumWidth(280)
        painel.setMaximumWidth(390)

        layout = QVBoxLayout(painel)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        titulo = QLabel("Detalhes do produto")
        titulo.setObjectName("tituloPainelAdmin")

        self.foto_detalhe = QLabel("Selecione um produto")
        self.foto_detalhe.setObjectName("imagemPainelAdmin")
        self.foto_detalhe.setFixedHeight(125)
        self.foto_detalhe.setAlignment(Qt.AlignCenter)

        self.nome_detalhe = QLabel("Nenhum produto selecionado")
        self.nome_detalhe.setObjectName("nomePainelAdmin")
        self.nome_detalhe.setWordWrap(True)

        self.descricao_detalhe = QLabel(
            "Selecione uma linha da tabela para visualizar as informações."
        )
        self.descricao_detalhe.setObjectName("textoPainelAdmin")
        self.descricao_detalhe.setWordWrap(True)
        self.descricao_detalhe.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.descricao_detalhe.setMinimumHeight(34)
        self.descricao_detalhe.setMaximumHeight(44)

        self.preco_detalhe = QLabel("Preço: —")
        self.estoque_detalhe = QLabel("Estoque: —")
        self.status_detalhe = QLabel("Situação: —")
        self.arquivo_detalhe = QLabel("Imagem: —")

        for label in (
            self.preco_detalhe,
            self.estoque_detalhe,
            self.status_detalhe,
            self.arquivo_detalhe,
        ):
            label.setObjectName("linhaPainelAdmin")
            label.setWordWrap(True)

        self.botao_editar = QPushButton("Editar produto")
        self.botao_editar.setObjectName("botaoPrimario")
        self.botao_editar.clicked.connect(self.editar_produto)

        self.botao_ativo = QPushButton("Ativar / desativar")
        self.botao_ativo.clicked.connect(self.alternar_ativo)

        self.botao_excluir = QPushButton("Excluir produto")
        self.botao_excluir.setObjectName("botaoPerigo")
        self.botao_excluir.clicked.connect(self.remover_produto)

        layout.addWidget(titulo)
        layout.addWidget(self.foto_detalhe)
        layout.addWidget(self.nome_detalhe)
        layout.addWidget(self.descricao_detalhe)
        layout.addWidget(self.preco_detalhe)
        layout.addWidget(self.estoque_detalhe)
        layout.addWidget(self.status_detalhe)
        layout.addWidget(self.arquivo_detalhe)
        layout.addStretch()
        layout.addWidget(self.botao_editar)
        layout.addWidget(self.botao_ativo)
        layout.addWidget(self.botao_excluir)

        self._habilitar_acoes(False)
        return painel

    def _habilitar_acoes(self, habilitado):
        self.botao_editar.setEnabled(habilitado)
        self.botao_ativo.setEnabled(habilitado)
        self.botao_excluir.setEnabled(habilitado)

    def recarregar(self):
        texto = normalizar_busca(self.busca.text())
        filtro_status = self.filtro_status.currentData()
        filtro_estoque = self.filtro_estoque.currentData()
        id_anterior = self.id_selecionado(self.tabela)

        try:
            with app.app_context():
                produtos = Produto.query.order_by(Produto.nome.asc()).all()
                dados = []

                for produto in produtos:
                    chave_busca = normalizar_busca(
                        f"{produto.id} {produto.nome or ''} {produto.descricao or ''}"
                    )

                    if texto and texto not in chave_busca:
                        continue

                    if filtro_status == "ativos" and not produto.ativo:
                        continue

                    if filtro_status == "inativos" and produto.ativo:
                        continue

                    estoque = int(produto.estoque or 0)

                    if filtro_estoque == "sem" and estoque != 0:
                        continue

                    if filtro_estoque == "baixo" and not (1 <= estoque <= 5):
                        continue

                    if filtro_estoque == "normal" and estoque <= 5:
                        continue

                    dados.append(
                        {
                            "id": produto.id,
                            "nome": produto.nome or "",
                            "descricao": produto.descricao or "",
                            "preco": float(produto.preco or 0),
                            "estoque": estoque,
                            "ativo": bool(produto.ativo),
                            "foto": produto.foto or "",
                        }
                    )

            self.tabela.setRowCount(0)

            linha_selecionar = None

            for linha, produto in enumerate(dados):
                self.tabela.insertRow(linha)

                valores = [
                    produto["id"],
                    produto["nome"],
                    formatar_real(produto["preco"]),
                    produto["estoque"],
                    "Ativo" if produto["ativo"] else "Inativo",
                    produto["foto"] or "—",
                ]

                for coluna, valor in enumerate(valores):
                    item = QTableWidgetItem(str(valor))
                    item.setData(Qt.UserRole, produto)

                    if coluna not in (1, 5):
                        item.setTextAlignment(Qt.AlignCenter)

                    self.tabela.setItem(linha, coluna, item)

                if produto["id"] == id_anterior:
                    linha_selecionar = linha

            if self.tabela.rowCount():
                self.tabela.selectRow(
                    linha_selecionar if linha_selecionar is not None else 0
                )
            else:
                self.limpar_detalhes()

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))

    def dados_selecionados(self):
        linha = self.tabela.currentRow()

        if linha < 0:
            return None

        item = self.tabela.item(linha, 0)
        return item.data(Qt.UserRole) if item else None

    def atualizar_detalhes(self):
        dados = self.dados_selecionados()

        if not dados:
            self.limpar_detalhes()
            return

        self.nome_detalhe.setText(dados["nome"] or "Produto")
        self.descricao_detalhe.setText(
            dados["descricao"] or "Descrição não informada."
        )
        self.preco_detalhe.setText(f"Preço: {formatar_real(dados['preco'])}")
        self.estoque_detalhe.setText(
            f"Estoque disponível: {dados['estoque']} unidade(s)"
        )
        self.status_detalhe.setText(
            "Situação: Ativo" if dados["ativo"] else "Situação: Inativo"
        )
        self.arquivo_detalhe.setText(
            f"Imagem: {dados['foto'] or 'não informada'}"
        )
        self.botao_ativo.setText(
            "Desativar produto" if dados["ativo"] else "Ativar produto"
        )

        carregar_imagem_label(
            self.foto_detalhe,
            PASTA_PRODUTOS,
            dados["foto"],
            largura=145,
            altura=105,
        )
        self._habilitar_acoes(True)

    def limpar_detalhes(self):
        self.foto_detalhe.clear()
        self.foto_detalhe.setText("Selecione um produto")
        self.nome_detalhe.setText("Nenhum produto selecionado")
        self.descricao_detalhe.setText(
            "Selecione uma linha da tabela para visualizar as informações."
        )
        self.preco_detalhe.setText("Preço: —")
        self.estoque_detalhe.setText("Estoque: —")
        self.status_detalhe.setText("Situação: —")
        self.arquivo_detalhe.setText("Imagem: —")
        self._habilitar_acoes(False)

    def novo_produto(self):
        if DialogProduto(parent=self).exec() == QDialog.Accepted:
            self.recarregar()

    def editar_produto(self):
        produto_id = self.id_selecionado(self.tabela)

        if produto_id is None:
            QMessageBox.information(
                self,
                "Selecione",
                "Selecione um produto para editar.",
            )
            return

        if DialogProduto(produto_id, self).exec() == QDialog.Accepted:
            self.recarregar()

    def alternar_ativo(self):
        produto_id = self.id_selecionado(self.tabela)

        if produto_id is None:
            QMessageBox.information(
                self,
                "Selecione",
                "Selecione um produto.",
            )
            return

        try:
            with app.app_context():
                produto = database.session.get(Produto, produto_id)

                if produto is None:
                    raise ValueError("Produto não encontrado.")

                produto.ativo = not bool(produto.ativo)
                database.session.commit()

            self.recarregar()

        except Exception as erro:
            database.session.rollback()
            QMessageBox.critical(self, "Erro", str(erro))

    def remover_produto(self):
        produto_id = self.id_selecionado(self.tabela)

        if produto_id is None:
            QMessageBox.information(
                self,
                "Selecione um produto",
                "Selecione o produto que deseja excluir.",
            )
            return

        dados = self.dados_selecionados()
        nome_produto = dados["nome"] if dados else "produto selecionado"

        resposta = QMessageBox.question(
            self,
            "Excluir produto",
            (
                f"Deseja excluir definitivamente '{nome_produto}'?\n\n"
                "O produto será removido dos carrinhos, mas continuará "
                "registrado no histórico dos pedidos."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if resposta != QMessageBox.Yes:
            return

        try:
            with app.app_context():
                excluir_produto(produto_id)

            QMessageBox.information(
                self,
                "Produto excluído",
                f"O produto '{nome_produto}' foi excluído com sucesso.",
            )
            self.recarregar()

        except ErroProduto as erro:
            QMessageBox.warning(
                self,
                "Não foi possível excluir",
                str(erro),
            )

        except Exception as erro:
            print("ERRO AO EXCLUIR PRODUTO:", erro)
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível excluir o produto. Tente novamente.",
            )


class TelaAdminMedicos(TelaAdminBase):
    def __init__(self):
        super().__init__(
            "paginaAdminMedicos",
            "Gerenciar médicos",
            "Filtre profissionais e selecione uma linha para visualizar ou alterar o cadastro.",
        )

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar médico, e-mail ou telefone...")
        self.busca.setClearButtonEnabled(True)
        self.busca.setMinimumWidth(250)
        self.busca.textChanged.connect(self.recarregar)

        self.filtro_especialidade = QComboBox()
        self.filtro_especialidade.addItem("Todas as especialidades", "todas")
        self.filtro_especialidade.currentIndexChanged.connect(self.recarregar)

        self.filtro_vinculo = QComboBox()
        self.filtro_vinculo.addItem("Todos os acessos", "todos")
        self.filtro_vinculo.addItem("Com acesso vinculado", "sim")
        self.filtro_vinculo.addItem("Sem acesso vinculado", "nao")
        self.filtro_vinculo.currentIndexChanged.connect(self.recarregar)

        novo = QPushButton("Novo médico")
        novo.setObjectName("botaoPrimario")
        novo.clicked.connect(self.novo_medico)

        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(self.recarregar)

        self.area_acoes_topo.addWidget(self.busca)
        self.area_acoes_topo.addWidget(self.filtro_especialidade)
        self.area_acoes_topo.addWidget(self.filtro_vinculo)
        self.area_acoes_topo.addWidget(novo)
        self.area_acoes_topo.addWidget(atualizar)

        area_conteudo = QHBoxLayout()
        area_conteudo.setSpacing(16)

        self.tabela = self.criar_tabela(
            [
                "ID",
                "Médico",
                "Especialidade",
                "E-mail",
                "Telefone",
                "Acesso",
            ]
        )
        self.tabela.setMinimumWidth(720)

        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.tabela.itemSelectionChanged.connect(self.atualizar_detalhes)
        self.tabela.doubleClicked.connect(self.editar_medico)

        self.painel_detalhes = self._criar_painel_detalhes()

        area_conteudo.addWidget(self.tabela, 3)
        area_conteudo.addWidget(self.painel_detalhes, 1)

        self.layout_principal.addLayout(area_conteudo, 1)
        self.recarregar()

    def _criar_painel_detalhes(self):
        painel = QFrame()
        painel.setObjectName("painelDetalhesAdmin")
        painel.setMinimumWidth(280)
        painel.setMaximumWidth(390)

        layout = QVBoxLayout(painel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel("Detalhes do médico")
        titulo.setObjectName("tituloPainelAdmin")

        self.foto_detalhe = QLabel("Selecione um médico")
        self.foto_detalhe.setObjectName("imagemPainelAdmin")
        self.foto_detalhe.setFixedHeight(180)
        self.foto_detalhe.setAlignment(Qt.AlignCenter)

        self.nome_detalhe = QLabel("Nenhum médico selecionado")
        self.nome_detalhe.setObjectName("nomePainelAdmin")
        self.nome_detalhe.setWordWrap(True)

        self.especialidade_detalhe = QLabel("Especialidade: —")
        self.email_detalhe = QLabel("E-mail: —")
        self.telefone_detalhe = QLabel("Telefone: —")
        self.vinculo_detalhe = QLabel("Acesso médico: —")

        for label in (
            self.especialidade_detalhe,
            self.email_detalhe,
            self.telefone_detalhe,
            self.vinculo_detalhe,
        ):
            label.setObjectName("linhaPainelAdmin")
            label.setWordWrap(True)

        self.botao_editar = QPushButton("Editar médico")
        self.botao_editar.setObjectName("botaoPrimario")
        self.botao_editar.clicked.connect(self.editar_medico)

        self.botao_remover = QPushButton("Remover médico")
        self.botao_remover.setObjectName("botaoPerigo")
        self.botao_remover.clicked.connect(self.remover_medico)

        layout.addWidget(titulo)
        layout.addWidget(self.foto_detalhe)
        layout.addWidget(self.nome_detalhe)
        layout.addWidget(self.especialidade_detalhe)
        layout.addWidget(self.email_detalhe)
        layout.addWidget(self.telefone_detalhe)
        layout.addWidget(self.vinculo_detalhe)
        layout.addStretch()
        layout.addWidget(self.botao_editar)
        layout.addWidget(self.botao_remover)

        self._habilitar_acoes(False)
        return painel

    def _habilitar_acoes(self, habilitado):
        self.botao_editar.setEnabled(habilitado)
        self.botao_remover.setEnabled(habilitado)

    def _atualizar_especialidades(self, medicos):
        selecionada = self.filtro_especialidade.currentData()

        especialidades = sorted(
            {
                (medico.especialidade or "").strip()
                for medico in medicos
                if (medico.especialidade or "").strip()
            },
            key=normalizar_busca,
        )

        self.filtro_especialidade.blockSignals(True)
        self.filtro_especialidade.clear()
        self.filtro_especialidade.addItem("Todas as especialidades", "todas")

        for especialidade in especialidades:
            self.filtro_especialidade.addItem(especialidade, especialidade)

        indice = self.filtro_especialidade.findData(selecionada)

        if indice >= 0:
            self.filtro_especialidade.setCurrentIndex(indice)

        self.filtro_especialidade.blockSignals(False)

    def recarregar(self):
        texto = normalizar_busca(self.busca.text())
        filtro_especialidade = self.filtro_especialidade.currentData()
        filtro_vinculo = self.filtro_vinculo.currentData()
        id_anterior = self.id_selecionado(self.tabela)

        try:
            with app.app_context():
                medicos = Medico.query.order_by(
                    Medico.nome.asc(),
                    Medico.sobrenome.asc(),
                ).all()

                self._atualizar_especialidades(medicos)
                filtro_especialidade = self.filtro_especialidade.currentData()
                dados = []

                for medico in medicos:
                    usuario = Usuario.query.filter_by(id_medico=medico.id).first()
                    vinculado = bool(usuario and usuario.is_medico)

                    chave_busca = normalizar_busca(
                        (
                            f"{medico.id} {medico.nome or ''} "
                            f"{medico.sobrenome or ''} "
                            f"{medico.especialidade or ''} "
                            f"{medico.email or ''} "
                            f"{medico.telefone or ''}"
                        )
                    )

                    if texto and texto not in chave_busca:
                        continue

                    if (
                        filtro_especialidade != "todas"
                        and medico.especialidade != filtro_especialidade
                    ):
                        continue

                    if filtro_vinculo == "sim" and not vinculado:
                        continue

                    if filtro_vinculo == "nao" and vinculado:
                        continue

                    dados.append(
                        {
                            "id": medico.id,
                            "nome": (
                                f"{medico.nome or ''} "
                                f"{medico.sobrenome or ''}"
                            ).strip(),
                            "especialidade": medico.especialidade or "",
                            "email": medico.email or "",
                            "telefone": medico.telefone or "—",
                            "foto": medico.foto or "",
                            "vinculado": vinculado,
                        }
                    )

            self.tabela.setRowCount(0)
            linha_selecionar = None

            for linha, medico in enumerate(dados):
                self.tabela.insertRow(linha)

                valores = [
                    medico["id"],
                    medico["nome"],
                    medico["especialidade"],
                    medico["email"],
                    medico["telefone"],
                    "Sim" if medico["vinculado"] else "Não",
                ]

                for coluna, valor in enumerate(valores):
                    item = QTableWidgetItem(str(valor))
                    item.setData(Qt.UserRole, medico)

                    if coluna in (0, 5):
                        item.setTextAlignment(Qt.AlignCenter)

                    self.tabela.setItem(linha, coluna, item)

                if medico["id"] == id_anterior:
                    linha_selecionar = linha

            if self.tabela.rowCount():
                self.tabela.selectRow(
                    linha_selecionar if linha_selecionar is not None else 0
                )
            else:
                self.limpar_detalhes()

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))

    def dados_selecionados(self):
        linha = self.tabela.currentRow()

        if linha < 0:
            return None

        item = self.tabela.item(linha, 0)
        return item.data(Qt.UserRole) if item else None

    def atualizar_detalhes(self):
        dados = self.dados_selecionados()

        if not dados:
            self.limpar_detalhes()
            return

        self.nome_detalhe.setText(dados["nome"] or "Médico")
        self.especialidade_detalhe.setText(
            f"Especialidade: {dados['especialidade'] or 'não informada'}"
        )
        self.email_detalhe.setText(
            f"E-mail: {dados['email'] or 'não informado'}"
        )
        self.telefone_detalhe.setText(
            f"Telefone: {dados['telefone'] or 'não informado'}"
        )
        self.vinculo_detalhe.setText(
            "Acesso médico: vinculado"
            if dados["vinculado"]
            else "Acesso médico: não vinculado"
        )

        carregar_imagem_label(
            self.foto_detalhe,
            PASTA_MEDICOS,
            dados["foto"],
            largura=180,
            altura=165,
        )
        self._habilitar_acoes(True)

    def limpar_detalhes(self):
        self.foto_detalhe.clear()
        self.foto_detalhe.setText("Selecione um médico")
        self.nome_detalhe.setText("Nenhum médico selecionado")
        self.especialidade_detalhe.setText("Especialidade: —")
        self.email_detalhe.setText("E-mail: —")
        self.telefone_detalhe.setText("Telefone: —")
        self.vinculo_detalhe.setText("Acesso médico: —")
        self._habilitar_acoes(False)

    def novo_medico(self):
        if DialogMedico(parent=self).exec() == QDialog.Accepted:
            self.recarregar()

    def editar_medico(self):
        medico_id = self.id_selecionado(self.tabela)

        if medico_id is None:
            QMessageBox.information(
                self,
                "Selecione",
                "Selecione um médico para editar.",
            )
            return

        if DialogMedico(medico_id, self).exec() == QDialog.Accepted:
            self.recarregar()

    def remover_medico(self):
        medico_id = self.id_selecionado(self.tabela)

        if medico_id is None:
            QMessageBox.information(
                self,
                "Selecione",
                "Selecione um médico.",
            )
            return

        dados = self.dados_selecionados()
        nome_medico = dados["nome"] if dados else "médico selecionado"

        resposta = QMessageBox.question(
            self,
            "Remover médico",
            (
                f"Deseja remover '{nome_medico}'?\n\n"
                "As consultas vinculadas também serão removidas."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if resposta != QMessageBox.Yes:
            return

        try:
            with app.app_context():
                medico = database.session.get(Medico, medico_id)

                if medico is None:
                    raise ValueError("Médico não encontrado.")

                usuario = Usuario.query.filter_by(id_medico=medico.id).first()
                Consulta.query.filter_by(medico_id=medico.id).delete()

                if usuario:
                    usuario.is_medico = False
                    usuario.id_medico = None

                database.session.delete(medico)
                database.session.commit()

            self.recarregar()

        except Exception as erro:
            database.session.rollback()
            QMessageBox.critical(self, "Erro", str(erro))


class TelaAdminPedidos(TelaAdminBase):
    def __init__(self):
        super().__init__(
            "paginaAdminPedidos",
            "Pedidos gerais",
            "Pesquise compras por cliente, produto, cidade, número ou status.",
        )

        self.busca = QLineEdit()
        self.busca.setPlaceholderText(
            "Buscar pedido, cliente, produto ou cidade..."
        )
        self.busca.setClearButtonEnabled(True)
        self.busca.setMinimumWidth(300)
        self.busca.textChanged.connect(self.recarregar)

        self.filtro = QComboBox()
        self.filtro.addItem("Todos os status", "todos")
        self.filtro.addItem("Aguardando pagamento", "aguardando_pagamento")
        self.filtro.addItem("Pagos", "pago")
        self.filtro.addItem("Falha / cancelados", "falha")
        self.filtro.currentIndexChanged.connect(self.recarregar)

        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(self.recarregar)

        self.area_acoes_topo.addWidget(self.busca)
        self.area_acoes_topo.addWidget(self.filtro)
        self.area_acoes_topo.addWidget(atualizar)

        self.tabela = self.criar_tabela(
            [
                "ID",
                "Cliente",
                "Data",
                "Total",
                "Pedido",
                "Pagamento",
                "Itens",
                "Cidade/UF",
            ]
        )

        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Stretch)

        self.layout_principal.addWidget(self.tabela, 1)
        self.recarregar()

    def recarregar(self):
        filtro = self.filtro.currentData()
        texto = normalizar_busca(self.busca.text())

        try:
            with app.app_context():
                query = Pedido.query

                if filtro == "pago":
                    query = query.filter(
                        (Pedido.status == "pago")
                        | (Pedido.status_pagamento == "approved")
                    )

                elif filtro == "falha":
                    query = query.filter(
                        Pedido.status.in_(["falha", "cancelado"])
                    )

                elif filtro != "todos":
                    query = query.filter(Pedido.status == filtro)

                pedidos = query.order_by(Pedido.data_criacao.desc()).all()
                dados = []

                for pedido in pedidos:
                    usuario = pedido.usuario

                    cliente = (
                        (
                            f"{usuario.nome or ''} "
                            f"{usuario.sobrenome or ''}"
                        ).strip()
                        if usuario
                        else "Usuário não encontrado"
                    )

                    nomes_produtos = " ".join(
                        item.nome_produto or ""
                        for item in pedido.itens
                    )

                    data_texto = (
                        pedido.data_criacao.strftime("%d/%m/%Y %H:%M")
                        if pedido.data_criacao
                        else ""
                    )

                    chave_busca = normalizar_busca(
                        (
                            f"{pedido.id} {cliente} {data_texto} "
                            f"{pedido.cidade or ''} {pedido.estado or ''} "
                            f"{pedido.status or ''} "
                            f"{pedido.status_pagamento or ''} "
                            f"{pedido.mercado_pago_payment_id or ''} "
                            f"{nomes_produtos}"
                        )
                    )

                    if texto and texto not in chave_busca:
                        continue

                    cidade = pedido.cidade or ""
                    estado = pedido.estado or ""

                    if cidade and estado:
                        local = f"{cidade}/{estado}"
                    else:
                        local = cidade or estado or "—"

                    dados.append(
                        {
                            "id": pedido.id,
                            "cliente": cliente,
                            "data": pedido.data_criacao,
                            "total": float(pedido.total or 0),
                            "status": pedido.status or "",
                            "pagamento": pedido.status_pagamento or "",
                            "itens": sum(
                                int(item.quantidade or 0)
                                for item in pedido.itens
                            ),
                            "local": local,
                        }
                    )

            self.tabela.setRowCount(0)

            for linha, pedido in enumerate(dados):
                self.tabela.insertRow(linha)

                valores = [
                    pedido["id"],
                    pedido["cliente"],
                    (
                        pedido["data"].strftime("%d/%m/%Y %H:%M")
                        if pedido["data"]
                        else "—"
                    ),
                    formatar_real(pedido["total"]),
                    pedido["status"].replace("_", " ").title() or "—",
                    pedido["pagamento"].replace("_", " ").title() or "—",
                    pedido["itens"],
                    pedido["local"],
                ]

                for coluna, valor in enumerate(valores):
                    item = QTableWidgetItem(str(valor))

                    if coluna not in (1, 7):
                        item.setTextAlignment(Qt.AlignCenter)

                    self.tabela.setItem(linha, coluna, item)

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))


class TelaAdminConsultas(TelaAdminBase):
    def __init__(self):
        super().__init__(
            "paginaAdminConsultas",
            "Agenda geral",
            (
                "Visualize e pesquise consultas por médico, "
                "especialidade, paciente, data ou horário."
            ),
        )

        # A agenda do administrador é somente para consulta.
        # Concluir e cancelar são ações exclusivas do médico.
        self.busca = QLineEdit()
        self.busca.setPlaceholderText(
            "Buscar médico, paciente, especialidade ou data..."
        )
        self.busca.setClearButtonEnabled(True)
        self.busca.setMinimumWidth(300)
        self.busca.textChanged.connect(self.recarregar)

        self.filtro = QComboBox()
        self.filtro.addItem("Todas", "todas")
        self.filtro.addItem("Agendadas", "agendada")
        self.filtro.addItem("Concluídas", "concluida")
        self.filtro.addItem("Canceladas", "cancelada")
        self.filtro.currentIndexChanged.connect(self.recarregar)

        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(self.recarregar)

        self.area_acoes_topo.addWidget(self.busca)
        self.area_acoes_topo.addWidget(self.filtro)
        self.area_acoes_topo.addWidget(atualizar)

        self.tabela = self.criar_tabela(
            [
                "ID",
                "Data",
                "Horário",
                "Médico",
                "Especialidade",
                "Paciente",
                "Status",
            ]
        )

        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.Stretch,
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.Stretch,
        )
        header.setSectionResizeMode(
            5,
            QHeaderView.Stretch,
        )
        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeToContents,
        )

        self.layout_principal.addWidget(
            self.tabela,
            1,
        )

        self.recarregar()

    def recarregar(self):
        filtro = self.filtro.currentData()
        texto = normalizar_busca(
            self.busca.text()
        )

        try:
            with app.app_context():
                query = Consulta.query

                if filtro != "todas":
                    query = query.filter(
                        Consulta.status == filtro
                    )

                consultas = (
                    query
                    .order_by(
                        Consulta.data.desc(),
                        Consulta.horario.asc(),
                    )
                    .all()
                )

                dados = []

                for consulta in consultas:
                    medico = consulta.medico
                    paciente = consulta.usuario

                    nome_medico = (
                        (
                            f"{medico.nome or ''} "
                            f"{medico.sobrenome or ''}"
                        ).strip()
                        if medico
                        else "Médico não encontrado"
                    )

                    especialidade = (
                        medico.especialidade or ""
                        if medico
                        else ""
                    )

                    nome_paciente = (
                        (
                            f"{paciente.nome or ''} "
                            f"{paciente.sobrenome or ''}"
                        ).strip()
                        if paciente
                        else "Paciente não encontrado"
                    )

                    data_formatada = (
                        consulta.data.strftime(
                            "%d/%m/%Y"
                        )
                        if consulta.data
                        else ""
                    )

                    data_iso = (
                        consulta.data.isoformat()
                        if consulta.data
                        else ""
                    )

                    chave_busca = normalizar_busca(
                        (
                            f"{consulta.id} "
                            f"{data_formatada} "
                            f"{data_iso} "
                            f"{consulta.horario or ''} "
                            f"{nome_medico} "
                            f"{especialidade} "
                            f"{nome_paciente} "
                            f"{consulta.status or ''}"
                        )
                    )

                    if (
                        texto
                        and texto not in chave_busca
                    ):
                        continue

                    dados.append(
                        {
                            "id": consulta.id,
                            "data": consulta.data,
                            "horario": (
                                consulta.horario or ""
                            ),
                            "medico": nome_medico,
                            "especialidade": especialidade,
                            "paciente": nome_paciente,
                            "status": (
                                consulta.status
                                or "agendada"
                            ),
                        }
                    )

            self.tabela.setRowCount(0)

            for linha, consulta in enumerate(
                dados
            ):
                self.tabela.insertRow(linha)

                data_texto = (
                    consulta["data"].strftime(
                        "%d/%m/%Y"
                    )
                    if consulta["data"]
                    else "—"
                )

                valores = [
                    consulta["id"],
                    data_texto,
                    consulta["horario"],
                    consulta["medico"],
                    consulta["especialidade"],
                    consulta["paciente"],
                    (
                        consulta["status"]
                        .replace("_", " ")
                        .title()
                    ),
                ]

                for coluna, valor in enumerate(
                    valores
                ):
                    item = QTableWidgetItem(
                        str(valor)
                    )

                    if coluna in (
                        0,
                        1,
                        2,
                        6,
                    ):
                        item.setTextAlignment(
                            Qt.AlignCenter
                        )

                    self.tabela.setItem(
                        linha,
                        coluna,
                        item,
                    )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                str(erro),
            )
