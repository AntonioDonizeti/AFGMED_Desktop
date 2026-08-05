import os

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QCursor, QPixmap
from PySide6.QtWidgets import (
    QDialog,
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
from projetoafgmed.models import Pedido
from projetoafgmed.servicos_pagamento import (
    ErroPagamento,
    sincronizar_pagamento_pedido,
)
from .tela_pagamento import DialogPagamentoMercadoPago


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
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


def status_visual(pedido_status, pagamento_status):
    pedido = (pedido_status or "").lower()
    pagamento = (pagamento_status or "").lower()

    if pedido == "pago_pendencia_estoque":
        return {
            "texto": "Pagamento aprovado — estoque pendente",
            "tipo": "analise",
            "descricao": "Pagamento confirmado, mas o pedido exige revisão de estoque.",
        }

    if pedido == "pago" or pagamento == "approved":
        return {
            "texto": "Pagamento aprovado",
            "tipo": "aprovado",
            "descricao": "Pedido confirmado e em preparação.",
        }

    if pedido == "falha" or pagamento in {
        "rejected",
        "cancelled",
        "refunded",
    }:
        return {
            "texto": "Pagamento não aprovado",
            "tipo": "falha",
            "descricao": "Você pode tentar realizar o pagamento novamente.",
        }

    return {
        "texto": "Aguardando pagamento",
        "tipo": "pendente",
        "descricao": "O pagamento ainda não foi confirmado.",
    }


def exibir_imagem(label, nome_arquivo, largura, altura):
    caminho = (
        os.path.join(PASTA_PRODUTOS, nome_arquivo)
        if nome_arquivo
        else ""
    )

    if not caminho or not os.path.exists(caminho):
        label.setText("Imagem\nindisponível")
        return

    imagem = QPixmap(caminho)

    if imagem.isNull():
        label.setText("Imagem\nindisponível")
        return

    label.setPixmap(
        imagem.scaled(
            largura,
            altura,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
    )


class LabelImagemClicavel(QLabel):
    clicado = Signal()

    def mousePressEvent(self, evento):
        if evento.button() == Qt.LeftButton:
            self.clicado.emit()
        super().mousePressEvent(evento)


class DialogDetalhesPedido(QDialog):
    def __init__(self, pedido, parent=None):
        super().__init__(parent)
        self.pedido = pedido

        self.setObjectName("dialogDetalhesPedido")
        self.setWindowTitle(f"Detalhes do pedido nº {pedido['id']}")
        self.resize(820, 680)
        self.setMinimumSize(700, 560)
        aplicar_estilo(self, "pedidos.qss")

        self._montar_interface()

    def _montar_interface(self):
        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(20, 20, 20, 20)
        layout_raiz.setSpacing(14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(16)

        status_info = status_visual(
            self.pedido["status"],
            self.pedido["status_pagamento"],
        )

        cabecalho = QFrame()
        cabecalho.setObjectName("cabecalhoDetalhesPedido")
        cabecalho_layout = QHBoxLayout(cabecalho)
        cabecalho_layout.setContentsMargins(18, 16, 18, 16)

        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(3)

        titulo = QLabel(f"Pedido nº {self.pedido['id']}")
        titulo.setObjectName("tituloDetalhesPedido")

        data_texto = (
            self.pedido["data_criacao"].strftime("%d/%m/%Y às %H:%M")
            if self.pedido["data_criacao"]
            else "Data não informada"
        )
        data = QLabel(data_texto)
        data.setObjectName("dataDetalhesPedido")

        area_titulo.addWidget(titulo)
        area_titulo.addWidget(data)

        status = QLabel(status_info["texto"])
        status.setObjectName("statusPedido")
        status.setProperty("tipoStatus", status_info["tipo"])
        status.setAlignment(Qt.AlignCenter)

        cabecalho_layout.addLayout(area_titulo)
        cabecalho_layout.addStretch()
        cabecalho_layout.addWidget(status)

        layout.addWidget(cabecalho)

        descricao_status = QLabel(status_info["descricao"])
        descricao_status.setObjectName("descricaoDetalhesPedido")
        descricao_status.setWordWrap(True)
        layout.addWidget(descricao_status)

        titulo_produtos = QLabel("Produtos do pedido")
        titulo_produtos.setObjectName("subtituloDetalhesPedido")
        layout.addWidget(titulo_produtos)

        for item in self.pedido["itens"]:
            layout.addWidget(self._criar_item(item))

        grade = QGridLayout()
        grade.setHorizontalSpacing(14)
        grade.setVerticalSpacing(14)

        grade.addWidget(
            self._criar_painel(
                "Endereço de entrega",
                (
                    f"{self.pedido['endereco']}\n"
                    f"{self.pedido['cidade']} - {self.pedido['estado']}\n"
                    f"CEP {self.pedido['cep']}"
                ),
            ),
            0,
            0,
        )

        pagamento_texto = (
            f"Pedido: {self.pedido['status'] or '—'}\n"
            f"Pagamento: {self.pedido['status_pagamento'] or '—'}"
        )

        if self.pedido["payment_id"]:
            pagamento_texto += (
                f"\nID do pagamento: {self.pedido['payment_id']}"
            )

        grade.addWidget(
            self._criar_painel(
                "Informações do pagamento",
                pagamento_texto,
            ),
            0,
            1,
        )

        grade.setColumnStretch(0, 1)
        grade.setColumnStretch(1, 1)
        layout.addLayout(grade)

        totais = QFrame()
        totais.setObjectName("painelTotaisDetalhes")
        totais_layout = QVBoxLayout(totais)
        totais_layout.setContentsMargins(18, 15, 18, 15)

        totais_layout.addLayout(
            self._linha_total("Produtos", self.pedido["total_produtos"])
        )
        totais_layout.addLayout(
            self._linha_total("Entrega", self.pedido["total_entrega"])
        )
        totais_layout.addLayout(
            self._linha_total(
                "Total do pedido",
                self.pedido["total"],
                destaque=True,
            )
        )

        layout.addWidget(totais)
        scroll.setWidget(container)

        fechar = QPushButton("Fechar")
        fechar.setMinimumWidth(110)
        fechar.clicked.connect(self.accept)

        botoes = QHBoxLayout()
        botoes.addStretch()
        botoes.addWidget(fechar)

        layout_raiz.addWidget(scroll)
        layout_raiz.addLayout(botoes)

    def _criar_item(self, item):
        linha = QFrame()
        linha.setObjectName("itemDetalhesPedido")

        layout = QHBoxLayout(linha)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(14)

        foto = QLabel()
        foto.setObjectName("fotoItemDetalhesPedido")
        foto.setFixedSize(86, 86)
        foto.setAlignment(Qt.AlignCenter)
        exibir_imagem(foto, item["foto"], 76, 76)

        dados = QVBoxLayout()
        dados.setSpacing(3)

        nome = QLabel(item["nome"])
        nome.setObjectName("nomeItemDetalhesPedido")
        nome.setWordWrap(True)

        descricao = QLabel(
            item["descricao"] or "Descrição não informada."
        )
        descricao.setObjectName("descricaoItemDetalhesPedido")
        descricao.setWordWrap(True)

        quantidade = QLabel(
            f"{item['quantidade']} unidade(s) × "
            f"{formatar_real(item['preco'])}"
        )
        quantidade.setObjectName("textoAuxiliarPedido")

        dados.addWidget(nome)
        dados.addWidget(descricao)
        dados.addWidget(quantidade)

        subtotal = QLabel(formatar_real(item["subtotal"]))
        subtotal.setObjectName("subtotalItemDetalhesPedido")
        subtotal.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(foto)
        layout.addLayout(dados, 1)
        layout.addWidget(subtotal)

        return linha

    @staticmethod
    def _criar_painel(titulo, texto):
        painel = QFrame()
        painel.setObjectName("painelDetalhePedido")

        layout = QVBoxLayout(painel)
        layout.setContentsMargins(16, 14, 16, 14)

        rotulo = QLabel(titulo)
        rotulo.setObjectName("rotuloDetalhePedido")

        valor = QLabel(texto)
        valor.setObjectName("valorDetalhePedido")
        valor.setWordWrap(True)

        layout.addWidget(rotulo)
        layout.addWidget(valor)
        return painel

    @staticmethod
    def _linha_total(titulo, valor, destaque=False):
        linha = QHBoxLayout()

        rotulo = QLabel(titulo)
        rotulo.setObjectName(
            "rotuloTotalDestaque"
            if destaque
            else "rotuloTotalDetalhes"
        )

        valor_label = QLabel(formatar_real(valor))
        valor_label.setObjectName(
            "valorTotalDestaque"
            if destaque
            else "valorTotalDetalhes"
        )

        linha.addWidget(rotulo)
        linha.addStretch()
        linha.addWidget(valor_label)
        return linha


class TelaMeusPedidos(QWidget):
    def __init__(self, usuario):
        super().__init__()

        self.usuario_id = usuario.id
        self.cards = []
        self.pedidos = []
        self.container = None
        self.grid = None

        self.setObjectName("paginaPedidos")
        aplicar_estilo(self, "pedidos.qss")

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(26, 22, 26, 26)
        layout_principal.setSpacing(18)

        cabecalho = QHBoxLayout()
        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(2)

        titulo = QLabel("Meus pedidos")
        titulo.setObjectName("tituloPagina")

        subtitulo = QLabel(
            "Veja um resumo de cada compra. "
            "Clique na imagem para abrir todos os detalhes."
        )
        subtitulo.setObjectName("subtituloPagina")

        area_titulo.addWidget(titulo)
        area_titulo.addWidget(subtitulo)

        atualizar = QPushButton("Atualizar")
        atualizar.setMinimumHeight(42)
        atualizar.clicked.connect(self.recarregar)

        cabecalho.addLayout(area_titulo)
        cabecalho.addStretch()
        cabecalho.addWidget(atualizar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        layout_principal.addLayout(cabecalho)
        layout_principal.addWidget(self.scroll)

        self.recarregar()

    def _criar_container(self):
        self.container = QWidget()
        self.container.setObjectName("containerPedidos")

        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(0, 0, 0, 14)
        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(18)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll.setWidget(self.container)

    def recarregar(self):
        self._criar_container()
        self.cards = []
        self.pedidos = []

        try:
            with app.app_context():
                pedidos_banco = (
                    Pedido.query.filter_by(id_usuario=self.usuario_id)
                    .order_by(Pedido.data_criacao.desc())
                    .all()
                )

                for pedido in pedidos_banco:
                    itens = [
                        {
                            "nome": item.nome_produto or "Produto",
                            "descricao": item.descricao_produto or "",
                            "foto": item.foto_produto or "",
                            "quantidade": int(item.quantidade or 0),
                            "preco": float(item.preco_unitario or 0),
                            "subtotal": float(item.subtotal or 0),
                        }
                        for item in pedido.itens
                    ]

                    self.pedidos.append(
                        {
                            "id": pedido.id,
                            "status": pedido.status or "",
                            "status_pagamento": pedido.status_pagamento or "",
                            "payment_id": (
                                pedido.mercado_pago_payment_id or ""
                            ),
                            "total_produtos": float(
                                pedido.total_produtos or 0
                            ),
                            "total_entrega": float(
                                pedido.total_entrega or 0
                            ),
                            "total": float(pedido.total or 0),
                            "endereco": pedido.endereco or "",
                            "cidade": pedido.cidade or "",
                            "estado": pedido.estado or "",
                            "cep": pedido.cep or "",
                            "data_criacao": pedido.data_criacao,
                            "itens": itens,
                        }
                    )

        except Exception as erro:
            print("ERRO AO CARREGAR PEDIDOS:", erro)
            self._mostrar_mensagem(
                "Não foi possível carregar os pedidos."
            )
            return

        if not self.pedidos:
            self._mostrar_mensagem(
                "Você ainda não realizou nenhum pedido."
            )
            return

        for pedido in self.pedidos:
            self.cards.append(self._criar_card(pedido))

        self._reorganizar_cards()

    def _mostrar_mensagem(self, texto):
        mensagem = QLabel(texto)
        mensagem.setObjectName("pedidosVazio")
        mensagem.setAlignment(Qt.AlignCenter)
        mensagem.setWordWrap(True)
        self.grid.addWidget(mensagem, 0, 0, 1, 3)

    def _criar_card(self, pedido):
        card = QFrame(self.container)
        card.setObjectName("pedidoResumoCard")
        card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        card.setMinimumWidth(300)
        card.setMinimumHeight(465)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 17, 18, 18)
        layout.setSpacing(11)

        status_info = status_visual(
            pedido["status"],
            pedido["status_pagamento"],
        )

        cabecalho = QHBoxLayout()
        area_numero = QVBoxLayout()
        area_numero.setSpacing(2)

        numero = QLabel(f"Pedido nº {pedido['id']}")
        numero.setObjectName("numeroPedidoResumo")

        data_texto = (
            pedido["data_criacao"].strftime("%d/%m/%Y")
            if pedido["data_criacao"]
            else "Data não informada"
        )
        data = QLabel(data_texto)
        data.setObjectName("dataPedidoResumo")

        area_numero.addWidget(numero)
        area_numero.addWidget(data)

        status = QLabel(status_info["texto"])
        status.setObjectName("statusPedido")
        status.setProperty("tipoStatus", status_info["tipo"])
        status.setAlignment(Qt.AlignCenter)
        status.setWordWrap(True)

        cabecalho.addLayout(area_numero)
        cabecalho.addStretch()
        cabecalho.addWidget(status)
        layout.addLayout(cabecalho)

        area_imagem = QFrame()
        area_imagem.setObjectName("areaImagemPedidoResumo")
        area_imagem.setFixedHeight(180)

        imagem_layout = QVBoxLayout(area_imagem)
        imagem_layout.setContentsMargins(8, 8, 8, 8)

        imagem = LabelImagemClicavel()
        imagem.setObjectName("imagemPedidoClicavel")
        imagem.setAlignment(Qt.AlignCenter)
        imagem.setCursor(QCursor(Qt.PointingHandCursor))
        imagem.setToolTip(
            "Clique para visualizar todos os detalhes do pedido."
        )

        foto_principal = (
            pedido["itens"][0]["foto"]
            if pedido["itens"]
            else ""
        )
        exibir_imagem(imagem, foto_principal, 240, 150)

        imagem.clicado.connect(
            lambda pedido_dados=pedido: self.abrir_detalhes(
                pedido_dados
            )
        )

        imagem_layout.addWidget(imagem)
        layout.addWidget(area_imagem)

        dica = QLabel("Clique na imagem para ver detalhes")
        dica.setObjectName("dicaImagemPedido")
        dica.setAlignment(Qt.AlignCenter)
        layout.addWidget(dica)

        quantidade_itens = sum(
            item["quantidade"]
            for item in pedido["itens"]
        )

        produto_principal = QLabel(
            pedido["itens"][0]["nome"]
            if pedido["itens"]
            else "Pedido sem produtos"
        )
        produto_principal.setObjectName("produtoPrincipalPedido")
        produto_principal.setWordWrap(True)

        resumo = QLabel(f"{quantidade_itens} item(ns) no pedido")
        resumo.setObjectName("resumoItensPedido")

        local = QLabel(
            f"Entrega: {pedido['cidade']} - {pedido['estado']}"
        )
        local.setObjectName("localEntregaResumo")
        local.setWordWrap(True)

        total = QLabel(formatar_real(pedido["total"]))
        total.setObjectName("totalPedidoResumo")

        descricao = QLabel(status_info["descricao"])
        descricao.setObjectName("descricaoStatusResumo")
        descricao.setWordWrap(True)

        layout.addWidget(produto_principal)
        layout.addWidget(resumo)
        layout.addWidget(local)
        layout.addWidget(total)
        layout.addWidget(descricao)
        layout.addStretch()

        if status_info["tipo"] in {"pendente", "falha"}:
            pagar = QPushButton(
                "Continuar pagamento"
                if status_info["tipo"] == "pendente"
                else "Tentar pagar novamente"
            )
            pagar.setObjectName("botaoSucesso")
            pagar.setMinimumHeight(42)
            pagar.clicked.connect(
                lambda checked=False, pedido_id=pedido["id"]: (
                    self.abrir_pagamento(pedido_id)
                )
            )

            verificar = QPushButton("Verificar pagamento")
            verificar.setMinimumHeight(40)
            verificar.clicked.connect(
                lambda checked=False, pedido_id=pedido["id"]: (
                    self.verificar_pagamento(pedido_id)
                )
            )

            layout.addWidget(pagar)
            layout.addWidget(verificar)

        return card

    def _reorganizar_cards(self):
        if self.grid is None:
            return

        while self.grid.count():
            self.grid.takeAt(0)

        if not self.cards:
            return

        largura = self.scroll.viewport().width()
        espacamento = self.grid.horizontalSpacing()

        if largura >= 1050:
            colunas = 3
        elif largura >= 700:
            colunas = 2
        else:
            colunas = 1

        largura_util = largura - ((colunas - 1) * espacamento) - 8
        largura_card = max(300, min(410, largura_util // colunas))

        for coluna in range(3):
            self.grid.setColumnStretch(coluna, 0)

        for indice, card in enumerate(self.cards):
            linha = indice // colunas
            coluna = indice % colunas
            card.setFixedWidth(largura_card)
            card.setVisible(True)
            self.grid.addWidget(
                card,
                linha,
                coluna,
                alignment=Qt.AlignTop,
            )

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        QTimer.singleShot(0, self._reorganizar_cards)

    def abrir_detalhes(self, pedido):
        DialogDetalhesPedido(
            pedido=pedido,
            parent=self,
        ).exec()

    def abrir_pagamento(self, pedido_id):
        try:
            dialogo = DialogPagamentoMercadoPago(
                pedido_id=pedido_id,
                parent=self,
            )
            dialogo.exec()
            self.recarregar()

        except Exception as erro:
            print("ERRO AO ABRIR PAGAMENTO DO PEDIDO:", erro)
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível abrir o pagamento.",
            )

    def verificar_pagamento(self, pedido_id):
        try:
            with app.app_context():
                pagamento = sincronizar_pagamento_pedido(pedido_id)

            status = (pagamento.get("status") or "pending").lower()

            if status == "approved":
                QMessageBox.information(
                    self,
                    "Pagamento aprovado",
                    "Pagamento confirmado e estoque atualizado.",
                )
            elif status in {"rejected", "cancelled"}:
                QMessageBox.warning(
                    self,
                    "Pagamento não aprovado",
                    "O pagamento foi recusado ou cancelado.",
                )
            else:
                QMessageBox.information(
                    self,
                    "Pagamento pendente",
                    "O pagamento ainda não foi confirmado.",
                )

            self.recarregar()

        except ErroPagamento as erro:
            QMessageBox.warning(self, "Pagamento", str(erro))

        except Exception as erro:
            print("ERRO AO VERIFICAR PEDIDO:", erro)
            QMessageBox.critical(
                self,
                "Erro",
                "Não foi possível verificar o pagamento.",
            )


def tela_meus_pedidos(usuario):
    return TelaMeusPedidos(usuario)