import os

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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
    texto = (
        f"{float(valor or 0):,.2f}"
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

        self.produtos = []
        self.cards = []
        self.grid = None
        self.container = None
        self.mensagem_filtro = None
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

        # =================================================
        # CABEÇALHO
        # =================================================

        cabecalho = QHBoxLayout()

        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(2)

        titulo = QLabel(
            "Produtos farmacêuticos"
        )

        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Medicamentos e produtos disponíveis "
            "no catálogo AFGMED."
        )

        subtitulo.setObjectName(
            "subtituloPagina"
        )

        area_titulo.addWidget(titulo)
        area_titulo.addWidget(subtitulo)

        self.busca = QLineEdit()

        self.busca.setObjectName(
            "campoBuscaProdutos"
        )

        self.busca.setPlaceholderText(
            "Buscar produto pelo nome..."
        )

        self.busca.setClearButtonEnabled(True)
        self.busca.setMinimumWidth(280)
        self.busca.setMaximumWidth(390)

        self.busca.textChanged.connect(
            self.aplicar_filtro
        )

        atualizar = QPushButton("Atualizar")

        atualizar.clicked.connect(
            self.recarregar
        )

        cabecalho.addLayout(area_titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(self.busca)
        cabecalho.addWidget(atualizar)

        # =================================================
        # ÁREA DE ROLAGEM
        # =================================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)

        self.scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        layout_principal.addLayout(
            cabecalho
        )

        layout_principal.addWidget(
            self.scroll
        )

        self.recarregar()

    # =====================================================
    # CONTAINER
    # =====================================================

    def _criar_container(self):
        self.container = QWidget()

        self.container.setObjectName(
            "containerProdutos"
        )

        self.grid = QGridLayout(
            self.container
        )

        self.grid.setContentsMargins(
            0,
            0,
            0,
            12,
        )

        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(18)

        # Mantém os cards no topo, mas permite
        # que as colunas ocupem toda a largura.
        self.grid.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(
            self.container
        )

    # =====================================================
    # CARREGAMENTO
    # =====================================================

    def recarregar(self):
        self._criar_container()

        self.cards = []
        self.produtos = []
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

                self.produtos = [
                    {
                        "id": produto.id,
                        "nome": (
                            produto.nome or ""
                        ),
                        "descricao": (
                            produto.descricao or ""
                        ),
                        "preco": float(
                            produto.preco or 0
                        ),
                        "estoque": int(
                            produto.estoque or 0
                        ),
                        "foto": (
                            produto.foto or ""
                        ),
                    }
                    for produto
                    in produtos_banco
                ]

        except Exception as erro:
            self._mostrar_mensagem(
                (
                    "Não foi possível carregar "
                    "os produtos.\n\n"
                    f"{erro}"
                ),
                "mensagemErro",
            )

            return

        if not self.produtos:
            self._mostrar_mensagem(
                (
                    "Nenhum produto disponível "
                    "no momento."
                ),
                "mensagemVazia",
            )

            return

        for produto in self.produtos:
            card = self.criar_card_produto(
                produto
            )

            card.setProperty(
                "nomeBusca",
                produto["nome"].casefold(),
            )

            self.cards.append(card)

        self.aplicar_filtro()

    # =====================================================
    # MENSAGEM
    # =====================================================

    def _mostrar_mensagem(
        self,
        texto,
        object_name="mensagemVazia",
    ):
        if self.grid is None:
            self._criar_container()

        mensagem = QLabel(texto)

        mensagem.setObjectName(
            object_name
        )

        mensagem.setWordWrap(True)

        mensagem.setAlignment(
            Qt.AlignCenter
        )

        self.grid.addWidget(
            mensagem,
            0,
            0,
            1,
            4,
        )

        self.mensagem_filtro = mensagem

    # =====================================================
    # FILTRO
    # =====================================================

    def aplicar_filtro(self):
        if self.grid is None:
            return

        termo = (
            self.busca.text()
            .strip()
            .casefold()
        )

        if self.mensagem_filtro is not None:
            self.mensagem_filtro.deleteLater()
            self.mensagem_filtro = None

        cards_visiveis = []

        for card in self.cards:
            nome = str(
                card.property(
                    "nomeBusca"
                )
                or ""
            )

            visivel = (
                not termo
                or termo in nome
            )

            card.setVisible(False)

            if visivel:
                cards_visiveis.append(
                    card
                )

        self.reorganizar_cards(
            cards_visiveis
        )

        if (
            self.cards
            and not cards_visiveis
        ):
            self._mostrar_mensagem(
                (
                    "Nenhum produto encontrado "
                    "com esse nome."
                ),
                "mensagemVazia",
            )

    # =====================================================
    # CARD DO PRODUTO
    # =====================================================

    def criar_card_produto(
        self,
        produto,
    ):
        card = QFrame(self.container)

        card.setObjectName(
            "produtoCard"
        )

        card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        # Remove o limite que causava
        # o grande espaço à direita.
        card.setMinimumWidth(0)
        card.setMaximumWidth(16777215)
        card.setMinimumHeight(470)

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            18,
            16,
            18,
            18,
        )

        layout.setSpacing(12)

        # =================================================
        # STATUS DO ESTOQUE
        # =================================================

        cabecalho = QHBoxLayout()

        badge = QLabel()

        if produto["estoque"] <= 0:
            badge.setText(
                "Sem estoque"
            )

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
            badge.setText(
                "Em estoque"
            )

            badge.setObjectName(
                "badgeDisponivel"
            )

        cabecalho.addWidget(badge)
        cabecalho.addStretch()

        # =================================================
        # IMAGEM
        # =================================================

        area_imagem = QFrame()

        area_imagem.setObjectName(
            "areaImagem"
        )

        area_imagem.setFixedHeight(175)

        layout_imagem = QVBoxLayout(
            area_imagem
        )

        layout_imagem.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        foto = QLabel()

        foto.setObjectName(
            "fotoProduto"
        )

        foto.setAlignment(
            Qt.AlignCenter
        )

        caminho_foto = (
            os.path.join(
                PASTA_PRODUTOS,
                produto["foto"],
            )
            if produto["foto"]
            else ""
        )

        if (
            caminho_foto
            and os.path.exists(
                caminho_foto
            )
        ):
            imagem = QPixmap(
                caminho_foto
            )

            if not imagem.isNull():
                foto.setPixmap(
                    imagem.scaled(
                        250,
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

        # =================================================
        # INFORMAÇÕES
        # =================================================

        nome = QLabel(
            produto["nome"]
            or "Produto"
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
            Qt.AlignTop
            | Qt.AlignLeft
        )

        descricao.setMinimumHeight(42)
        descricao.setMaximumHeight(60)

        # =================================================
        # PREÇO
        # =================================================

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

        rotulo = QLabel("Preço")

        rotulo.setObjectName(
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

        coluna_preco.addWidget(rotulo)
        coluna_preco.addWidget(valor)

        estoque = QLabel(
            f"{produto['estoque']} un."
        )

        estoque.setObjectName(
            "textoEstoque"
        )

        estoque.setAlignment(
            Qt.AlignRight
            | Qt.AlignVCenter
        )

        layout_preco.addLayout(
            coluna_preco
        )

        layout_preco.addStretch()
        layout_preco.addWidget(estoque)

        # =================================================
        # BOTÃO
        # =================================================

        botao = QPushButton(
            "Adicionar ao carrinho"
        )

        botao.setObjectName(
            "botaoComprar"
        )

        botao.setMinimumHeight(46)

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
            botao.setEnabled(False)

            botao.setToolTip(
                "Usuário não identificado."
            )

        elif (
            usuario_medico
            and not usuario_admin
        ):
            botao.setEnabled(False)

            botao.setToolTip(
                (
                    "Usuários médicos não podem "
                    "comprar como pacientes."
                )
            )

        elif produto["estoque"] <= 0:
            botao.setEnabled(False)

            botao.setText(
                "Produto indisponível"
            )

        else:
            botao.clicked.connect(
                lambda checked=False,
                produto_id=produto["id"]: (
                    self.adicionar_ao_carrinho(
                        produto_id
                    )
                )
            )

        layout.addLayout(cabecalho)
        layout.addWidget(area_imagem)
        layout.addWidget(nome)
        layout.addWidget(descricao)
        layout.addStretch()
        layout.addWidget(painel_preco)
        layout.addWidget(botao)

        return card

    # =====================================================
    # ORGANIZAÇÃO RESPONSIVA
    # =====================================================

    def reorganizar_cards(
        self,
        cards=None,
    ):
        if self.grid is None:
            return

        cards = (
            self.cards
            if cards is None
            else cards
        )

        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()

            if (
                widget is not None
                and widget not in self.cards
            ):
                widget.deleteLater()

        if not cards:
            return

        largura = (
            self.scroll.viewport().width()
        )

        if largura >= 1450:
            colunas = 4

        elif largura >= 960:
            colunas = 3

        elif largura >= 620:
            colunas = 2

        else:
            colunas = 1

        self.quantidade_colunas = (
            colunas
        )

        self.grid.setAlignment(
            Qt.AlignTop
        )

        # Cada coluna visível recebe o mesmo
        # espaço horizontal.
        for coluna in range(4):
            self.grid.setColumnStretch(
                coluna,
                1 if coluna < colunas else 0,
            )

        for indice, card in enumerate(
            cards
        ):
            linha = indice // colunas
            coluna = indice % colunas

            card.setMinimumWidth(0)
            card.setMaximumWidth(16777215)

            card.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed,
            )

            card.setVisible(True)

            # Não usamos alinhamento horizontal
            # para permitir que o card preencha
            # completamente a célula.
            self.grid.addWidget(
                card,
                linha,
                coluna,
            )

    def resizeEvent(self, evento):
        super().resizeEvent(evento)

        QTimer.singleShot(
            0,
            self.aplicar_filtro,
        )

    # =====================================================
    # CARRINHO
    # =====================================================

    def adicionar_ao_carrinho(
        self,
        produto_id,
    ):
        try:
            with app.app_context():
                mensagem = adicionar_produto(
                    usuario_id=(
                        self.usuario_id
                    ),
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
                (
                    "Não foi possível "
                    "adicionar"
                ),
                str(erro),
            )

        except Exception as erro:
            print(
                "ERRO AO ADICIONAR PRODUTO:",
                erro,
            )

            QMessageBox.critical(
                self,
                "Erro",
                (
                    "Não foi possível adicionar "
                    "o produto ao carrinho."
                ),
            )


def tela_produtos(usuario=None):
    return TelaProdutos(usuario)