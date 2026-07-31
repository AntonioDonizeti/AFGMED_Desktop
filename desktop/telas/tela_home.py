from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
)

from .tela_agendamentos import TelaAgendamentos
from .tela_carrinho import TelaCarrinho
from .tela_medicos import TelaMedicos
from .tela_meus_pedidos import TelaMeusPedidos
from .tela_perfil import tela_perfil
from .tela_produtos import TelaProdutos


janela_home = None


def abrir_tela_home(
    janela_anterior,
    usuario,
):
    global janela_home

    if janela_anterior is not None:
        janela_anterior.close()

    janela_home = QMainWindow()
    janela_home.setObjectName("janelaHome")

    janela_home.setWindowTitle(
        "AFGMED Desktop"
    )

    janela_home.resize(
        1280,
        760,
    )

    janela_home.setMinimumSize(
        900,
        600,
    )

    # Mantém os dados do usuário durante a sessão.
    janela_home.usuario = usuario

    abas = QTabWidget()
    abas.setObjectName("abasPrincipais")

    abas.setDocumentMode(True)
    abas.setMovable(False)
    abas.setTabsClosable(False)
    abas.setUsesScrollButtons(True)

    # Instâncias das telas.
    produtos = TelaProdutos(usuario)
    carrinho = TelaCarrinho(usuario)
    meus_pedidos = TelaMeusPedidos(usuario)
    consultas = TelaMedicos(usuario)
    agendamentos = TelaAgendamentos(usuario)
    perfil = tela_perfil(usuario)

    abas.addTab(
        produtos,
        "Produtos",
    )

    abas.addTab(
        carrinho,
        "Carrinho",
    )

    abas.addTab(
        meus_pedidos,
        "Meus pedidos",
    )

    abas.addTab(
        consultas,
        "Consultas",
    )

    abas.addTab(
        agendamentos,
        "Meus agendamentos",
    )

    abas.addTab(
        perfil,
        "Perfil",
    )

    # Quando um produto é adicionado,
    # atualiza a aba do carrinho.
    produtos.carrinho_alterado.connect(
        carrinho.recarregar
    )

    # Quando a quantidade ou o estoque muda,
    # atualiza a lista de produtos.
    carrinho.estoque_alterado.connect(
        produtos.recarregar
    )

    def atualizar_aba(indice):
        widget_atual = abas.widget(indice)

        metodo_recarregar = getattr(
            widget_atual,
            "recarregar",
            None,
        )

        if callable(metodo_recarregar):
            metodo_recarregar()

    abas.currentChanged.connect(
        atualizar_aba
    )

    janela_home.setCentralWidget(abas)
    janela_home.show()