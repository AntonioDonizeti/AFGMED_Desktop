import os

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from desktop.estilos import aplicar_estilo
from projetoafgmed import app
from projetoafgmed.models import Produto
from projetoafgmed.servicos_compras import (
    ErroCompra,
    adicionar_produto,
)


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

PASTA_PRODUTOS = os.path.join(
    BASE_DIR,
    "projetoafgmed",
    "static",
    "fotos_produtos",
)


def formatar_real(valor):
    valor = float(valor or 0)

    texto = (
        f"{valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"R$ {texto}"


class TelaProdutos(QWidget):
    carrinho_alterado = Signal()

    def __init__(self, usuario=None):
        super().__init__()

        self.usuario = usuario

        self.usuario_id = (
            usuario.id
            if usuario is not None
            else None
        )

        self.cards = []
        self.grid = None
        self.quantidade_colunas = 0

        self.setObjectName("paginaProdutos")

        aplicar_estilo(
            self,
            "produtos.qss",
        )

        layout_principal = QVBoxLayout(self)

        layout_principal.setContentsMargins(
            26,
            22,
            26,
            26,
        )

        layout_principal.setSpacing(18)

        # =====================================
        # CABEÇALHO
        # =====================================

        cabecalho = QHBoxLayout()
        cabecalho.setSpacing(12)

        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(3)

        titulo = QLabel(
            "Produtos farmacêuticos"
        )

        titulo.setObjectName(
            "tituloPagina"
        )

        subtitulo = QLabel(
            "Encontre medicamentos e produtos "
            "disponíveis para compra."
        )

        subtitulo.setObjectName(
            "subtituloPagina"
        )

        area_titulo.addWidget(titulo)
        area_titulo.addWidget(subtitulo)

        botao_atualizar = QPushButton(
            "Atualizar produtos"
        )

        botao_atualizar.setObjectName(
            "botaoSecundario"
        )

        botao_atualizar.setMinimumHeight(40)

        botao_atualizar.clicked.connect(
            self.recarregar
        )

        cabecalho.addLayout(area_titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(botao_atualizar)

        # =====================================
        # ÁREA DE ROLAGEM
        # =====================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)

        self.scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        layout_principal.addLayout(cabecalho)
        layout_principal.addWidget(self.scroll)

        self.recarregar()

    def recarregar(self):
        container = QWidget()

        container.setObjectName(
            "containerProdutos"
        )

        self.grid = QGridLayout(container)

        self.grid.setContentsMargins(
            0,
            0,
            0,
            12,
        )

        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(18)

        self.grid.setAlignment(
            Qt.AlignTop | Qt.AlignHCenter
        )

        self.cards = []
        self.quantidade_colunas = 0

        try:
            with app.app_context():
                produtos_banco = (
                    Produto.query
                    .filter_by(ativo=True)
                    .order_by(
                        Produto.nome.asc()
                    )
                    .all()
                )

                produtos = [
                    {
                        "id": produto.id,
                        "nome": produto.nome or "",
                        "descricao": (
                            produto.descricao or ""
                        ),
                        "preco": float(
                            produto.preco or 0
                        ),
                        "estoque": int(
                            produto.estoque or 0
                        ),
                        "foto": produto.foto or "",
                    }
                    for produto in produtos_banco
                ]

        except Exception as erro:
            mensagem = QLabel(
                "Não foi possível carregar os produtos."
                f"\n\n{erro}"
            )

            mensagem.setObjectName(
                "mensagemErro"
            )

            mensagem.setAlignment(
                Qt.AlignCenter
            )

            mensagem.setWordWrap(True)

            self.grid.addWidget(
                mensagem,
                0,
                0,
            )

            self.scroll.setWidget(container)
            return

        if not produtos:
            mensagem = QLabel(
                "Nenhum produto disponível no momento."
            )

            mensagem.setObjectName(
                "mensagemVazia"
            )

            mensagem.setAlignment(
                Qt.AlignCenter
            )

            self.grid.addWidget(
                mensagem,
                0,
                0,
            )

            self.scroll.setWidget(container)
            return

        for produto in produtos:
            card = self.criar_card_produto(
                produto
            )

            self.cards.append(card)

        self.scroll.setWidget(container)

        QTimer.singleShot(
            0,
            self.reorganizar_cards,
        )

    def criar_card_produto(
        self,
        produto,
    ):
        card = QFrame()
        card.setObjectName("produtoCard")

        card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        card.setMinimumWidth(275)
        card.setMaximumWidth(365)
        card.setMinimumHeight(470)

        layout_card = QVBoxLayout(card)

        layout_card.setContentsMargins(
            18,
            17,
            18,
            18,
        )

        layout_card.setSpacing(12)

        # =====================================
        # STATUS DE ESTOQUE
        # =====================================

        cabecalho_card = QHBoxLayout()

        badge = QLabel()

        if produto["estoque"] <= 0:
            badge.setText("Sem estoque")

            badge.setObjectName(
                "badgeSemEstoque"
            )

        elif produto["estoque"] <= 5:
            badge.setText(
                "Últimas unidades"
            )

            badge.setObjectName(
                "badgePoucoEstoque"
            )

        else:
            badge.setText("Em estoque")

            badge.setObjectName(
                "badgeDisponivel"
            )

        cabecalho_card.addWidget(
            badge,
            alignment=Qt.AlignLeft,
        )

        cabecalho_card.addStretch()

        # =====================================
        # IMAGEM
        # =====================================

        area_imagem = QFrame()

        area_imagem.setObjectName(
            "areaImagem"
        )

        area_imagem.setFixedHeight(175)

        layout_imagem = QVBoxLayout(
            area_imagem
        )

        layout_imagem.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        foto = QLabel()

        foto.setObjectName(
            "fotoProduto"
        )

        foto.setAlignment(
            Qt.AlignCenter
        )

        caminho_foto = ""

        if produto["foto"]:
            caminho_foto = os.path.join(
                PASTA_PRODUTOS,
                produto["foto"],
            )

        if (
            caminho_foto
            and os.path.exists(caminho_foto)
        ):
            imagem = QPixmap(caminho_foto)

            if not imagem.isNull():
                foto.setPixmap(
                    imagem.scaled(
                        220,
                        145,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )

            else:
                foto.setText(
                    "Imagem indisponível"
                )

        else:
            foto.setText(
                "Imagem indisponível"
            )

        layout_imagem.addWidget(foto)

        # =====================================
        # INFORMAÇÕES
        # =====================================

        nome = QLabel(
            produto["nome"] or "Produto"
        )

        nome.setObjectName(
            "nomeProduto"
        )

        nome.setWordWrap(True)

        descricao = QLabel(
            produto["descricao"]
            or "Descrição não informada."
        )

        descricao.setObjectName(
            "descricaoProduto"
        )

        descricao.setWordWrap(True)

        descricao.setAlignment(
            Qt.AlignTop | Qt.AlignLeft
        )

        descricao.setMinimumHeight(42)
        descricao.setMaximumHeight(60)

        # =====================================
        # PREÇO E ESTOQUE
        # =====================================

        painel_preco = QFrame()

        painel_preco.setObjectName(
            "painelPreco"
        )

        layout_preco = QHBoxLayout(
            painel_preco
        )

        layout_preco.setContentsMargins(
            14,
            10,
            14,
            10,
        )

        coluna_preco = QVBoxLayout()
        coluna_preco.setSpacing(1)

        rotulo_preco = QLabel("Preço")

        rotulo_preco.setObjectName(
            "rotuloPreco"
        )

        valor = QLabel(
            formatar_real(
                produto["preco"]
            )
        )

        valor.setObjectName(
            "valorProduto"
        )

        coluna_preco.addWidget(
            rotulo_preco
        )

        coluna_preco.addWidget(valor)

        estoque = QLabel(
            f"{produto['estoque']} un."
        )

        estoque.setObjectName(
            "textoEstoque"
        )

        estoque.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        layout_preco.addLayout(
            coluna_preco
        )

        layout_preco.addStretch()

        layout_preco.addWidget(
            estoque
        )

        # =====================================
        # BOTÃO
        # =====================================

        botao_adicionar = QPushButton(
            "Adicionar ao carrinho"
        )

        botao_adicionar.setObjectName(
            "botaoComprar"
        )

        botao_adicionar.setMinimumHeight(
            46
        )

        usuario_medico = bool(
            getattr(
                self.usuario,
                "is_medico",
                False,
            )
        )

        usuario_admin = bool(
            getattr(
                self.usuario,
                "is_admin",
                False,
            )
        )

        if self.usuario_id is None:
            botao_adicionar.setEnabled(False)

            botao_adicionar.setToolTip(
                "Usuário não identificado."
            )

        elif (
            usuario_medico
            and not usuario_admin
        ):
            botao_adicionar.setEnabled(False)

            botao_adicionar.setToolTip(
                "O acesso de médico não pode "
                "realizar compras."
            )

        elif produto["estoque"] <= 0:
            botao_adicionar.setEnabled(False)

            botao_adicionar.setText(
                "Produto indisponível"
            )

        else:
            botao_adicionar.clicked.connect(
                lambda checked=False,
                produto_id=produto["id"]:
                self.adicionar_ao_carrinho(
                    produto_id
                )
            )

        layout_card.addLayout(
            cabecalho_card
        )

        layout_card.addWidget(
            area_imagem
        )

        layout_card.addWidget(nome)
        layout_card.addWidget(descricao)
        layout_card.addStretch()

        layout_card.addWidget(
            painel_preco
        )

        layout_card.addWidget(
            botao_adicionar
        )

        return card

    def reorganizar_cards(self):
        if (
            self.grid is None
            or not self.cards
        ):
            return

        largura = (
            self.scroll.viewport().width()
        )

        if largura >= 1030:
            colunas = 3

        elif largura >= 680:
            colunas = 2

        else:
            colunas = 1

        if (
            colunas
            == self.quantidade_colunas
        ):
            return

        self.quantidade_colunas = colunas

        while self.grid.count():
            self.grid.takeAt(0)

        for coluna in range(3):
            self.grid.setColumnStretch(
                coluna,
                0,
            )

        for coluna in range(colunas):
            self.grid.setColumnStretch(
                coluna,
                1,
            )

        for indice, card in enumerate(
            self.cards
        ):
            linha = indice // colunas
            coluna = indice % colunas

            self.grid.addWidget(
                card,
                linha,
                coluna,
                alignment=(
                    Qt.AlignTop
                    | Qt.AlignHCenter
                ),
            )

    def resizeEvent(self, evento):
        super().resizeEvent(evento)

        QTimer.singleShot(
            0,
            self.reorganizar_cards,
        )

    def adicionar_ao_carrinho(
        self,
        produto_id,
    ):
        try:
            with app.app_context():
                mensagem = adicionar_produto(
                    usuario_id=self.usuario_id,
                    produto_id=produto_id,
                )

            QMessageBox.information(
                self,
                "Produto adicionado",
                mensagem,
            )

            self.recarregar()

            self.carrinho_alterado.emit()

        except ErroCompra as erro:
            QMessageBox.warning(
                self,
                "Não foi possível adicionar",
                str(erro),
            )

        except Exception as erro:
            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível adicionar "
                    "o produto ao carrinho."
                    f"\n\n{erro}"
                ),
            )


def tela_produtos(usuario=None):
    return TelaProdutos(usuario)