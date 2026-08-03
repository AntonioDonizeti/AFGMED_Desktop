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
from .tela_admin import (
    TelaAdminConsultas,
    TelaAdminMedicos,
    TelaAdminPedidos,
    TelaAdminProdutos,
)
from .tela_agendamentos import TelaAgendamentos
from .tela_carrinho import TelaCarrinho
from .tela_consultas_medico import TelaConsultasMedico
from .tela_dashboard import criar_dashboard
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
    janela_home.resize(1360, 820)
    janela_home.setMinimumSize(1020, 680)
    janela_home.usuario = usuario

    conteudo = QWidget()
    conteudo.setObjectName("conteudoHome")
    aplicar_estilo(conteudo, "home.qss")

    layout_principal = QVBoxLayout(conteudo)
    layout_principal.setContentsMargins(0, 0, 0, 0)
    layout_principal.setSpacing(0)

    topo = QFrame()
    topo.setObjectName("topoHome")
    topo.setFixedHeight(76)

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

    is_admin = bool(getattr(usuario, "is_admin", False))
    is_medico = bool(getattr(usuario, "is_medico", False))

    if is_admin:
        nome_perfil = "Administrador"
        tipo_perfil = "admin"
    elif is_medico:
        nome_perfil = "Médico"
        tipo_perfil = "medico"
    else:
        nome_perfil = "Paciente"
        tipo_perfil = "usuario"

    badge_perfil = QLabel(nome_perfil)
    badge_perfil.setObjectName("badgePerfilHome")
    badge_perfil.setProperty("tipoPerfil", tipo_perfil)
    badge_perfil.setAlignment(Qt.AlignCenter)

    usuario_label = QLabel(nome_completo or getattr(usuario, "email", "Usuário"))
    usuario_label.setObjectName("usuarioHome")
    usuario_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    botao_logout = QPushButton("Sair")
    botao_logout.setObjectName("botaoLogout")
    botao_logout.setMinimumWidth(85)

    layout_topo.addLayout(area_marca)
    layout_topo.addStretch()
    layout_topo.addWidget(badge_perfil)
    layout_topo.addWidget(usuario_label)
    layout_topo.addWidget(botao_logout)

    abas = QTabWidget()
    abas.setObjectName("abasPrincipais")
    abas.setDocumentMode(True)
    abas.setMovable(False)
    abas.setTabsClosable(False)
    abas.setUsesScrollButtons(True)
    abas.setElideMode(Qt.ElideNone)

    mapa_abas = {}
    def adicionar_aba(chave, widget, titulo):
        indice = abas.addTab(widget, titulo)
        mapa_abas[chave] = indice
        return widget

    dashboard = adicionar_aba(
        "dashboard",
        criar_dashboard(usuario),
        "Dashboard",
    )

    if is_admin:
        produtos = adicionar_aba("produtos", TelaProdutos(usuario), "Produtos")
        carrinho = adicionar_aba("carrinho", TelaCarrinho(usuario), "Carrinho")
        adicionar_aba(
            "pedidos", TelaMeusPedidos(usuario), "Meus pedidos"
        )
        adicionar_aba(
            "consultas", TelaMedicos(usuario), "Consultas"
        )
        adicionar_aba(
            "agendamentos", TelaAgendamentos(usuario), "Meus agendamentos"
        )
        adicionar_aba(
            "admin_produtos", TelaAdminProdutos(), "Gerenciar produtos"
        )
        adicionar_aba(
            "admin_medicos", TelaAdminMedicos(), "Gerenciar médicos"
        )
        adicionar_aba(
            "admin_pedidos", TelaAdminPedidos(), "Pedidos gerais"
        )
        adicionar_aba(
            "admin_consultas", TelaAdminConsultas(), "Agenda geral"
        )
        adicionar_aba("perfil", tela_perfil(usuario), "Perfil")

        produtos.carrinho_alterado.connect(carrinho.recarregar)
        carrinho.estoque_alterado.connect(produtos.recarregar)


    elif is_medico:
        adicionar_aba(
            "consultas_medico",
            TelaConsultasMedico(usuario),
            "Minhas consultas",
        )
        adicionar_aba("produtos", TelaProdutos(usuario), "Produtos")
        adicionar_aba("perfil", tela_perfil(usuario), "Perfil")

    else:
        produtos = adicionar_aba("produtos", TelaProdutos(usuario), "Produtos")
        carrinho = adicionar_aba("carrinho", TelaCarrinho(usuario), "Carrinho")
        adicionar_aba("pedidos", TelaMeusPedidos(usuario), "Meus pedidos")
        adicionar_aba("consultas", TelaMedicos(usuario), "Consultas")
        adicionar_aba(
            "agendamentos", TelaAgendamentos(usuario), "Meus agendamentos"
        )
        adicionar_aba("perfil", tela_perfil(usuario), "Perfil")

        produtos.carrinho_alterado.connect(carrinho.recarregar)
        carrinho.estoque_alterado.connect(produtos.recarregar)

    def navegar_para(chave):
        indice = mapa_abas.get(chave)
        if indice is not None:
            abas.setCurrentIndex(indice)

    dashboard.navegar.connect(navegar_para)

    def atualizar_aba(indice):
        widget_atual = abas.widget(indice)
        metodo_recarregar = getattr(widget_atual, "recarregar", None)

        if callable(metodo_recarregar):
            metodo_recarregar()

        # Mantém o dashboard atualizado quando outras telas alteram o banco.
        if widget_atual is dashboard:
            dashboard.recarregar()

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
