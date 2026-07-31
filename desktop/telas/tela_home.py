from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from desktop.estilos import aplicar_estilo
from .tela_agendamentos import TelaAgendamentos
from .tela_carrinho import TelaCarrinho
from .tela_medicos import TelaMedicos
from .tela_meus_pedidos import TelaMeusPedidos
from .tela_perfil import tela_perfil
from .tela_produtos import TelaProdutos


janela_home = None


def abrir_tela_home(janela_anterior, usuario):
    global janela_home

    if janela_anterior is not None:
        janela_anterior.close()

    janela_home = QMainWindow()
    janela_home.setWindowTitle("AFGMED Desktop")
    janela_home.resize(1280, 780)
    janela_home.setMinimumSize(980, 650)
    janela_home.usuario = usuario

    conteudo = QWidget()
    conteudo.setObjectName("conteudoHome")
    aplicar_estilo(conteudo, "home.qss")

    layout_principal = QVBoxLayout(conteudo)
    layout_principal.setContentsMargins(0, 0, 0, 0)
    layout_principal.setSpacing(0)

    topo = QFrame()
    topo.setObjectName("topoHome")
    topo.setFixedHeight(72)

    layout_topo = QHBoxLayout(topo)
    layout_topo.setContentsMargins(24, 10, 24, 10)
    layout_topo.setSpacing(14)

    area_marca = QVBoxLayout()
    area_marca.setSpacing(0)

    marca = QLabel("AFGMED")
    marca.setObjectName("marcaHome")

    submarca = QLabel("Saúde integrada — Web e Desktop")
    submarca.setObjectName("submarcaHome")

    area_marca.addWidget(marca)
    area_marca.addWidget(submarca)

    nome_completo = (
        f"{getattr(usuario, 'nome', '')} "
        f"{getattr(usuario, 'sobrenome', '')}"
    ).strip()

    usuario_label = QLabel(nome_completo or getattr(usuario, "email", "Usuário"))
    usuario_label.setObjectName("usuarioHome")
    usuario_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    botao_logout = QPushButton("Sair")
    botao_logout.setObjectName("botaoLogout")
    botao_logout.setMinimumWidth(85)

    layout_topo.addLayout(area_marca)
    layout_topo.addStretch()
    layout_topo.addWidget(usuario_label)
    layout_topo.addWidget(botao_logout)

    abas = QTabWidget()
    abas.setObjectName("abasPrincipais")
    abas.setDocumentMode(True)
    abas.setMovable(False)
    abas.setTabsClosable(False)
    abas.setUsesScrollButtons(True)

    produtos = TelaProdutos(usuario)
    carrinho = TelaCarrinho(usuario)
    meus_pedidos = TelaMeusPedidos(usuario)
    consultas = TelaMedicos(usuario)
    agendamentos = TelaAgendamentos(usuario)
    perfil = tela_perfil(usuario)

    abas.addTab(produtos, "Produtos")
    abas.addTab(carrinho, "Carrinho")
    abas.addTab(meus_pedidos, "Meus pedidos")
    abas.addTab(consultas, "Consultas")
    abas.addTab(agendamentos, "Meus agendamentos")
    abas.addTab(perfil, "Perfil")

    produtos.carrinho_alterado.connect(carrinho.recarregar)
    carrinho.estoque_alterado.connect(produtos.recarregar)

    def atualizar_aba(indice):
        widget_atual = abas.widget(indice)
        metodo_recarregar = getattr(widget_atual, "recarregar", None)

        if callable(metodo_recarregar):
            metodo_recarregar()

    abas.currentChanged.connect(atualizar_aba)

    def logout():
        resposta = QMessageBox.question(
            janela_home,
            "Sair da conta",
            "Deseja encerrar esta sessão e voltar para o login?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if resposta != QMessageBox.Yes:
            return

        janela_home.usuario = None
        janela_home.close()

        from .tela_login import abrir_tela_login

        abrir_tela_login()

    botao_logout.clicked.connect(logout)

    layout_principal.addWidget(topo)
    layout_principal.addWidget(abas, 1)

    janela_home.setCentralWidget(conteudo)
    janela_home.show()
