import re
import shutil
from datetime import date
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import Qt
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
        self.destaque = QCheckBox("Exibir nos destaques da home")

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
        formulario.addRow("Destaque", self.destaque)
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
                    "destaque": bool(produto.destaque_home),
                    "foto": produto.foto or "",
                }

            self.nome.setText(dados["nome"])
            self.descricao.setPlainText(dados["descricao"])
            self.preco.setValue(dados["preco"])
            self.estoque.setValue(dados["estoque"])
            self.ativo.setChecked(dados["ativo"])
            self.destaque.setChecked(dados["destaque"])
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
                produto.destaque_home = self.destaque.isChecked()

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
            "Cadastre e edite produtos seguindo os mesmos campos disponíveis no projeto web.",
        )

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar produto...")
        self.busca.setClearButtonEnabled(True)
        self.busca.textChanged.connect(self.recarregar)

        novo = QPushButton("Novo produto")
        novo.setObjectName("botaoPrimario")
        novo.clicked.connect(self.novo_produto)
        editar = QPushButton("Editar")
        editar.clicked.connect(self.editar_produto)
        alternar = QPushButton("Ativar / desativar")
        alternar.clicked.connect(self.alternar_ativo)
        remover = QPushButton("Excluir")
        remover.setObjectName("botaoPerigo")
        remover.clicked.connect(self.remover_produto)
        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(self.recarregar)

        self.area_acoes_topo.addWidget(self.busca)
        self.area_acoes_topo.addWidget(novo)
        self.area_acoes_topo.addWidget(editar)
        self.area_acoes_topo.addWidget(alternar)
        self.area_acoes_topo.addWidget(remover)
        self.area_acoes_topo.addWidget(atualizar)

        self.tabela = self.criar_tabela(
            ["ID", "Produto", "Preço", "Estoque", "Ativo", "Destaque", "Imagem"]
        )
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for coluna in range(2, 7):
            header.setSectionResizeMode(coluna, QHeaderView.ResizeToContents)
        self.tabela.doubleClicked.connect(self.editar_produto)

        self.layout_principal.addWidget(self.tabela, 1)
        self.recarregar()

    def recarregar(self):
        texto = self.busca.text().strip().lower()
        try:
            with app.app_context():
                produtos = Produto.query.order_by(Produto.nome.asc()).all()
                dados = [
                    {
                        "id": p.id,
                        "nome": p.nome or "",
                        "preco": float(p.preco or 0),
                        "estoque": int(p.estoque or 0),
                        "ativo": bool(p.ativo),
                        "destaque": bool(p.destaque_home),
                        "foto": p.foto or "",
                    }
                    for p in produtos
                    if not texto or texto in (p.nome or "").lower()
                ]

            self.tabela.setRowCount(0)
            for linha, produto in enumerate(dados):
                self.tabela.insertRow(linha)
                valores = [
                    produto["id"],
                    produto["nome"],
                    formatar_real(produto["preco"]),
                    produto["estoque"],
                    "Sim" if produto["ativo"] else "Não",
                    "Sim" if produto["destaque"] else "Não",
                    produto["foto"],
                ]
                for coluna, valor in enumerate(valores):
                    item = QTableWidgetItem(str(valor))
                    if coluna != 1:
                        item.setTextAlignment(Qt.AlignCenter)
                    self.tabela.setItem(linha, coluna, item)

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))

    def novo_produto(self):
        if DialogProduto(parent=self).exec() == QDialog.Accepted:
            self.recarregar()

    def editar_produto(self):
        produto_id = self.id_selecionado(self.tabela)
        if produto_id is None:
            QMessageBox.information(self, "Selecione", "Selecione um produto para editar.")
            return
        if DialogProduto(produto_id, self).exec() == QDialog.Accepted:
            self.recarregar()

    def alternar_ativo(self):
        produto_id = self.id_selecionado(self.tabela)
        if produto_id is None:
            QMessageBox.information(self, "Selecione", "Selecione um produto.")
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

        linha = self.tabela.currentRow()
        item_nome = self.tabela.item(linha, 1)
        nome_produto = item_nome.text() if item_nome else "produto selecionado"

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
            QMessageBox.warning(self, "Não foi possível excluir", str(erro))
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
            "Cadastre profissionais e sincronize automaticamente o acesso médico usado pelo web e desktop.",
        )

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar médico ou especialidade...")
        self.busca.setClearButtonEnabled(True)
        self.busca.textChanged.connect(self.recarregar)

        novo = QPushButton("Novo médico")
        novo.setObjectName("botaoPrimario")
        novo.clicked.connect(self.novo_medico)
        editar = QPushButton("Editar")
        editar.clicked.connect(self.editar_medico)
        remover = QPushButton("Remover")
        remover.setObjectName("botaoPerigo")
        remover.clicked.connect(self.remover_medico)
        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(self.recarregar)

        self.area_acoes_topo.addWidget(self.busca)
        self.area_acoes_topo.addWidget(novo)
        self.area_acoes_topo.addWidget(editar)
        self.area_acoes_topo.addWidget(remover)
        self.area_acoes_topo.addWidget(atualizar)

        self.tabela = self.criar_tabela(
            ["ID", "Médico", "Especialidade", "E-mail", "Telefone", "Acesso vinculado"]
        )
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tabela.doubleClicked.connect(self.editar_medico)

        self.layout_principal.addWidget(self.tabela, 1)
        self.recarregar()

    def recarregar(self):
        texto = self.busca.text().strip().lower()
        try:
            with app.app_context():
                medicos = Medico.query.order_by(Medico.nome.asc()).all()
                dados = []
                for medico in medicos:
                    chave = f"{medico.nome} {medico.sobrenome} {medico.especialidade}".lower()
                    if texto and texto not in chave:
                        continue
                    usuario = Usuario.query.filter_by(id_medico=medico.id).first()
                    dados.append(
                        {
                            "id": medico.id,
                            "nome": f"{medico.nome} {medico.sobrenome}".strip(),
                            "especialidade": medico.especialidade or "",
                            "email": medico.email or "",
                            "telefone": medico.telefone or "—",
                            "vinculado": "Sim" if usuario and usuario.is_medico else "Não",
                        }
                    )

            self.tabela.setRowCount(0)
            for linha, medico in enumerate(dados):
                self.tabela.insertRow(linha)
                valores = [
                    medico["id"],
                    medico["nome"],
                    medico["especialidade"],
                    medico["email"],
                    medico["telefone"],
                    medico["vinculado"],
                ]
                for coluna, valor in enumerate(valores):
                    item = QTableWidgetItem(str(valor))
                    if coluna in (0, 5):
                        item.setTextAlignment(Qt.AlignCenter)
                    self.tabela.setItem(linha, coluna, item)

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))

    def novo_medico(self):
        if DialogMedico(parent=self).exec() == QDialog.Accepted:
            self.recarregar()

    def editar_medico(self):
        medico_id = self.id_selecionado(self.tabela)
        if medico_id is None:
            QMessageBox.information(self, "Selecione", "Selecione um médico para editar.")
            return
        if DialogMedico(medico_id, self).exec() == QDialog.Accepted:
            self.recarregar()

    def remover_medico(self):
        medico_id = self.id_selecionado(self.tabela)
        if medico_id is None:
            QMessageBox.information(self, "Selecione", "Selecione um médico.")
            return

        resposta = QMessageBox.question(
            self,
            "Remover médico",
            "As consultas vinculadas também serão removidas. Deseja continuar?",
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
            "Visualize as compras de todos os usuários registradas no banco compartilhado.",
        )

        self.filtro = QComboBox()
        self.filtro.addItem("Todos os status", "todos")
        self.filtro.addItem("Aguardando pagamento", "aguardando_pagamento")
        self.filtro.addItem("Pagos", "pago")
        self.filtro.addItem("Falha / cancelados", "falha")
        self.filtro.currentIndexChanged.connect(self.recarregar)
        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(self.recarregar)
        self.area_acoes_topo.addWidget(self.filtro)
        self.area_acoes_topo.addWidget(atualizar)

        self.tabela = self.criar_tabela(
            ["ID", "Cliente", "Data", "Total", "Pedido", "Pagamento", "Itens", "Cidade/UF"]
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
        try:
            with app.app_context():
                query = Pedido.query
                if filtro == "pago":
                    query = query.filter(
                        (Pedido.status == "pago") | (Pedido.status_pagamento == "approved")
                    )
                elif filtro == "falha":
                    query = query.filter(
                        Pedido.status.in_(["falha", "cancelado"])
                    )
                elif filtro != "todos":
                    query = query.filter(Pedido.status == filtro)

                pedidos = query.order_by(Pedido.data_criacao.desc()).all()
                dados = [
                    {
                        "id": p.id,
                        "cliente": f"{p.usuario.nome} {p.usuario.sobrenome}".strip(),
                        "data": p.data_criacao,
                        "total": float(p.total or 0),
                        "status": p.status or "",
                        "pagamento": p.status_pagamento or "",
                        "itens": sum(int(item.quantidade or 0) for item in p.itens),
                        "local": f"{p.cidade}/{p.estado}",
                    }
                    for p in pedidos
                ]

            self.tabela.setRowCount(0)
            for linha, pedido in enumerate(dados):
                self.tabela.insertRow(linha)
                valores = [
                    pedido["id"],
                    pedido["cliente"],
                    pedido["data"].strftime("%d/%m/%Y %H:%M"),
                    formatar_real(pedido["total"]),
                    pedido["status"].replace("_", " ").title(),
                    pedido["pagamento"].replace("_", " ").title(),
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
            "Acompanhe consultas de todos os médicos e altere atendimentos quando necessário.",
        )

        self.filtro = QComboBox()
        self.filtro.addItem("Todas", "todas")
        self.filtro.addItem("Agendadas", "agendada")
        self.filtro.addItem("Concluídas", "concluida")
        self.filtro.addItem("Canceladas", "cancelada")
        self.filtro.currentIndexChanged.connect(self.recarregar)
        concluir = QPushButton("Concluir")
        concluir.setObjectName("botaoSucesso")
        concluir.clicked.connect(self.concluir)
        cancelar = QPushButton("Cancelar")
        cancelar.setObjectName("botaoPerigo")
        cancelar.clicked.connect(self.cancelar)
        atualizar = QPushButton("Atualizar")
        atualizar.clicked.connect(self.recarregar)

        self.area_acoes_topo.addWidget(self.filtro)
        self.area_acoes_topo.addWidget(concluir)
        self.area_acoes_topo.addWidget(cancelar)
        self.area_acoes_topo.addWidget(atualizar)

        self.tabela = self.criar_tabela(
            ["ID", "Data", "Horário", "Médico", "Especialidade", "Paciente", "Status"]
        )
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.layout_principal.addWidget(self.tabela, 1)
        self.recarregar()

    def recarregar(self):
        filtro = self.filtro.currentData()
        try:
            with app.app_context():
                query = Consulta.query
                if filtro != "todas":
                    query = query.filter(Consulta.status == filtro)
                consultas = query.order_by(
                    Consulta.data.desc(), Consulta.horario.asc()
                ).all()
                dados = [
                    {
                        "id": c.id,
                        "data": c.data,
                        "horario": c.horario,
                        "medico": f"{c.medico.nome} {c.medico.sobrenome}".strip(),
                        "especialidade": c.medico.especialidade or "",
                        "paciente": f"{c.usuario.nome} {c.usuario.sobrenome}".strip(),
                        "status": c.status or "agendada",
                    }
                    for c in consultas
                ]

            self.tabela.setRowCount(0)
            for linha, consulta in enumerate(dados):
                self.tabela.insertRow(linha)
                valores = [
                    consulta["id"],
                    consulta["data"].strftime("%d/%m/%Y"),
                    consulta["horario"],
                    consulta["medico"],
                    consulta["especialidade"],
                    consulta["paciente"],
                    consulta["status"].title(),
                ]
                for coluna, valor in enumerate(valores):
                    item = QTableWidgetItem(str(valor))
                    if coluna in (0, 1, 2, 6):
                        item.setTextAlignment(Qt.AlignCenter)
                    self.tabela.setItem(linha, coluna, item)

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))

    def alterar_status(self, novo_status):
        consulta_id = self.id_selecionado(self.tabela)
        if consulta_id is None:
            QMessageBox.information(self, "Selecione", "Selecione uma consulta.")
            return

        try:
            with app.app_context():
                consulta = database.session.get(Consulta, consulta_id)
                if consulta is None:
                    raise ValueError("Consulta não encontrada.")
                if consulta.status != "agendada":
                    raise ValueError("Apenas consultas agendadas podem ser alteradas.")
                consulta.status = novo_status
                database.session.commit()
            self.recarregar()
        except Exception as erro:
            database.session.rollback()
            QMessageBox.critical(self, "Erro", str(erro))

    def concluir(self):
        self.alterar_status("concluida")

    def cancelar(self):
        self.alterar_status("cancelada")
