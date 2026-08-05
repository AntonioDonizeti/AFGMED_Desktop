from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from desktop.estilos import aplicar_estilo
from projetoafgmed import app
from projetoafgmed.models import (
    Carrinho,
    Consulta,
    Medico,
    Pedido,
    Produto,
    Usuario,
)


def formatar_real(valor):
    texto = (
        f"{float(valor or 0):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    return f"R$ {texto}"


def formatar_data(valor):
    return valor.strftime("%d/%m/%Y") if valor else "—"


class DashboardBase(QWidget):
    navegar = Signal(str)

    def __init__(self, usuario, titulo, subtitulo):
        super().__init__()
        self.usuario = usuario
        self.usuario_id = usuario.id
        self.setObjectName("paginaDashboard")
        aplicar_estilo(self, "dashboard.qss")

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.conteudo = QWidget()
        self.layout = QVBoxLayout(self.conteudo)
        self.layout.setContentsMargins(26, 24, 26, 30)
        self.layout.setSpacing(20)

        cabecalho = QHBoxLayout()
        area_titulo = QVBoxLayout()
        area_titulo.setSpacing(3)

        self.titulo = QLabel(titulo)
        self.titulo.setObjectName("tituloDashboard")

        self.subtitulo = QLabel(subtitulo)
        self.subtitulo.setObjectName("subtituloDashboard")
        self.subtitulo.setWordWrap(True)

        area_titulo.addWidget(self.titulo)
        area_titulo.addWidget(self.subtitulo)

        atualizar = QPushButton("Atualizar dados")
        atualizar.setObjectName("botaoAtualizarDashboard")
        atualizar.clicked.connect(self.recarregar)

        cabecalho.addLayout(area_titulo, 1)
        cabecalho.addWidget(atualizar)

        self.layout.addLayout(cabecalho)

        self.area_dinamica = QVBoxLayout()
        self.area_dinamica.setSpacing(20)
        self.layout.addLayout(self.area_dinamica)

        self.layout.addStretch()

        self.scroll.setWidget(self.conteudo)
        layout_raiz.addWidget(self.scroll)

    def limpar_area(self):
        while self.area_dinamica.count():
            item = self.area_dinamica.takeAt(0)
            widget = item.widget()
            layout = item.layout()

            if widget is not None:
                widget.deleteLater()
            elif layout is not None:
                self._limpar_layout(layout)

    def _limpar_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            sublayout = item.layout()

            if widget is not None:
                widget.deleteLater()
            elif sublayout is not None:
                self._limpar_layout(sublayout)

    def criar_grade_metricas(self, metricas):
        grade = QGridLayout()
        grade.setHorizontalSpacing(16)
        grade.setVerticalSpacing(16)

        for indice, metrica in enumerate(metricas):
            card = QFrame()
            card.setObjectName("cardMetrica")
            card.setProperty(
                "tipo",
                metrica.get("tipo", "padrao"),
            )

            layout = QVBoxLayout(card)
            layout.setContentsMargins(
                18,
                17,
                18,
                17,
            )
            layout.setSpacing(4)

            rotulo = QLabel(metrica["titulo"])
            rotulo.setObjectName("rotuloMetrica")

            valor = QLabel(str(metrica["valor"]))
            valor.setObjectName("valorMetrica")

            descricao = QLabel(
                metrica.get("descricao", "")
            )
            descricao.setObjectName(
                "descricaoMetrica"
            )
            descricao.setWordWrap(True)

            layout.addWidget(rotulo)
            layout.addWidget(valor)
            layout.addWidget(descricao)

            grade.addWidget(
                card,
                indice // 4,
                indice % 4,
            )

        for coluna in range(4):
            grade.setColumnStretch(coluna, 1)

        return grade

    def criar_secao(self, titulo, subtitulo=""):
        frame = QFrame()
        frame.setObjectName("secaoDashboard")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(
            20,
            18,
            20,
            20,
        )
        layout.setSpacing(12)

        cabecalho = QVBoxLayout()
        cabecalho.setSpacing(2)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName(
            "tituloSecaoDashboard"
        )
        cabecalho.addWidget(label_titulo)

        if subtitulo:
            label_subtitulo = QLabel(subtitulo)
            label_subtitulo.setObjectName(
                "subtituloSecaoDashboard"
            )
            label_subtitulo.setWordWrap(True)
            cabecalho.addWidget(label_subtitulo)

        layout.addLayout(cabecalho)

        return frame, layout

    def criar_linha_info(
        self,
        titulo,
        detalhe,
        status="",
    ):
        linha = QFrame()
        linha.setObjectName("linhaInfoDashboard")

        layout = QHBoxLayout(linha)
        layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )
        layout.setSpacing(12)

        textos = QVBoxLayout()
        textos.setSpacing(2)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName(
            "tituloLinhaDashboard"
        )
        label_titulo.setWordWrap(True)

        label_detalhe = QLabel(detalhe)
        label_detalhe.setObjectName(
            "detalheLinhaDashboard"
        )
        label_detalhe.setWordWrap(True)

        textos.addWidget(label_titulo)
        textos.addWidget(label_detalhe)

        layout.addLayout(textos, 1)

        if status:
            badge = QLabel(status)
            badge.setObjectName("badgeDashboard")
            badge.setAlignment(Qt.AlignCenter)
            layout.addWidget(badge)

        return linha

    def mostrar_erro(self, erro):
        frame, layout = self.criar_secao(
            "Não foi possível carregar o painel"
        )

        mensagem = QLabel(str(erro))
        mensagem.setObjectName(
            "mensagemErroDashboard"
        )
        mensagem.setWordWrap(True)

        layout.addWidget(mensagem)
        self.area_dinamica.addWidget(frame)

    def recarregar(self):
        raise NotImplementedError


class TelaDashboardUsuario(DashboardBase):
    def __init__(self, usuario):
        nome = (
            getattr(usuario, "nome", "Usuário")
            or "Usuário"
        )

        super().__init__(
            usuario,
            f"Olá, {nome}!",
            (
                "Veja seus pedidos, consultas e os "
                "próximos passos da sua conta AFGMED."
            ),
        )

        self.recarregar()

    def recarregar(self):
        self.limpar_area()

        try:
            with app.app_context():
                carrinho = (
                    Carrinho.query.filter_by(
                        id_usuario=self.usuario_id,
                        ativo=True,
                        status="ativo",
                    )
                    .order_by(Carrinho.id.desc())
                    .first()
                )

                itens_carrinho = sum(
                    int(item.quantidade or 0)
                    for item in (
                        carrinho.itens
                        if carrinho
                        else []
                    )
                )

                pedidos_pendentes = (
                    Pedido.query.filter(
                        Pedido.id_usuario
                        == self.usuario_id,
                        Pedido.status.in_(
                            [
                                "aguardando_pagamento",
                                "falha",
                            ]
                        ),
                    ).count()
                )

                consultas_futuras = (
                    Consulta.query.filter(
                        Consulta.usuario_id
                        == self.usuario_id,
                        Consulta.status
                        == "agendada",
                        Consulta.data >= date.today(),
                    )
                    .order_by(
                        Consulta.data.asc(),
                        Consulta.horario.asc(),
                    )
                    .all()
                )

                pedidos = (
                    Pedido.query.filter_by(
                        id_usuario=self.usuario_id
                    )
                    .order_by(
                        Pedido.data_criacao.desc()
                    )
                    .limit(4)
                    .all()
                )

                proxima = (
                    consultas_futuras[0]
                    if consultas_futuras
                    else None
                )

                dados_pedidos = [
                    {
                        "id": pedido.id,
                        "data": pedido.data_criacao,
                        "total": float(
                            pedido.total or 0
                        ),
                        "status": (
                            pedido.status
                            or "em análise"
                        ),
                    }
                    for pedido in pedidos
                ]

                dados_proxima = None

                if proxima:
                    dados_proxima = {
                        "medico": (
                            f"{proxima.medico.nome} "
                            f"{proxima.medico.sobrenome}"
                        ).strip(),
                        "especialidade": (
                            proxima.medico.especialidade
                            or ""
                        ),
                        "data": proxima.data,
                        "horario": proxima.horario,
                    }

            metricas = [
                {
                    "titulo": "Itens no carrinho",
                    "valor": itens_carrinho,
                    "descricao": (
                        "Produtos aguardando "
                        "finalização."
                    ),
                    "tipo": "azul",
                },
                {
                    "titulo": "Pedidos pendentes",
                    "valor": pedidos_pendentes,
                    "descricao": (
                        "Aguardando pagamento ou "
                        "nova tentativa."
                    ),
                    "tipo": "amarelo",
                },
                {
                    "titulo": "Próximas consultas",
                    "valor": len(
                        consultas_futuras
                    ),
                    "descricao": (
                        "Agendamentos futuros "
                        "confirmados."
                    ),
                    "tipo": "verde",
                },
                {
                    "titulo": "Último pedido",
                    "valor": (
                        f"#{dados_pedidos[0]['id']}"
                        if dados_pedidos
                        else "—"
                    ),
                    "descricao": (
                        formatar_real(
                            dados_pedidos[0]["total"]
                        )
                        if dados_pedidos
                        else (
                            "Nenhum pedido realizado."
                        )
                    ),
                    "tipo": "cinza",
                },
            ]

            self.area_dinamica.addLayout(
                self.criar_grade_metricas(
                    metricas
                )
            )

            grade = QGridLayout()
            grade.setHorizontalSpacing(16)
            grade.setVerticalSpacing(16)

            proxima_frame, proxima_layout = (
                self.criar_secao(
                    "Próxima consulta",
                    (
                        "Seu compromisso médico "
                        "mais próximo."
                    ),
                )
            )

            if dados_proxima:
                proxima_layout.addWidget(
                    self.criar_linha_info(
                        dados_proxima["medico"],
                        (
                            f"{dados_proxima['especialidade']} • "
                            f"{formatar_data(dados_proxima['data'])} "
                            f"às {dados_proxima['horario']}"
                        ),
                        "Agendada",
                    )
                )
            else:
                proxima_layout.addWidget(
                    self.criar_linha_info(
                        "Nenhuma consulta futura",
                        (
                            "Escolha um médico para "
                            "realizar um novo agendamento."
                        ),
                    )
                )

            pedidos_frame, pedidos_layout = (
                self.criar_secao(
                    "Pedidos recentes",
                    (
                        "Acompanhe as últimas "
                        "compras registradas."
                    ),
                )
            )

            if dados_pedidos:
                for pedido in dados_pedidos:
                    pedidos_layout.addWidget(
                        self.criar_linha_info(
                            (
                                f"Pedido #{pedido['id']} • "
                                f"{formatar_real(pedido['total'])}"
                            ),
                            (
                                "Criado em "
                                f"{pedido['data'].strftime('%d/%m/%Y %H:%M')}"
                            ),
                            (
                                pedido["status"]
                                .replace("_", " ")
                                .title()
                            ),
                        )
                    )
            else:
                pedidos_layout.addWidget(
                    self.criar_linha_info(
                        "Nenhuma compra registrada",
                        (
                            "Seus pedidos aparecerão "
                            "aqui após a finalização "
                            "do carrinho."
                        ),
                    )
                )

            grade.addWidget(
                proxima_frame,
                0,
                0,
            )
            grade.addWidget(
                pedidos_frame,
                0,
                1,
            )

            grade.setColumnStretch(0, 1)
            grade.setColumnStretch(1, 1)

            self.area_dinamica.addLayout(
                grade
            )

        except Exception as erro:
            self.mostrar_erro(erro)


class TelaDashboardMedico(DashboardBase):
    def __init__(self, usuario):
        nome = (
            getattr(usuario, "nome", "Médico")
            or "Médico"
        )

        super().__init__(
            usuario,
            f"Painel médico — Dr(a). {nome}",
            (
                "Acompanhe sua agenda, os pacientes "
                "do dia e o histórico de atendimentos."
            ),
        )

        self.recarregar()

    def recarregar(self):
        self.limpar_area()

        if not getattr(
            self.usuario,
            "id_medico",
            None,
        ):
            frame, layout = self.criar_secao(
                "Cadastro médico não vinculado"
            )

            layout.addWidget(
                self.criar_linha_info(
                    (
                        "Seu usuário ainda não possui "
                        "um médico associado"
                    ),
                    (
                        "Peça ao administrador para "
                        "vincular este acesso a um "
                        "cadastro médico."
                    ),
                )
            )

            self.area_dinamica.addWidget(frame)
            return

        try:
            with app.app_context():
                medico = Medico.query.get(
                    self.usuario.id_medico
                )

                consultas = (
                    Consulta.query.filter_by(
                        medico_id=(
                            self.usuario.id_medico
                        )
                    )
                    .order_by(
                        Consulta.data.asc(),
                        Consulta.horario.asc(),
                    )
                    .all()
                )

                hoje = date.today()

                hoje_agendadas = [
                    consulta
                    for consulta in consultas
                    if (
                        consulta.data == hoje
                        and consulta.status
                        == "agendada"
                    )
                ]

                futuras = [
                    consulta
                    for consulta in consultas
                    if (
                        consulta.data >= hoje
                        and consulta.status
                        == "agendada"
                    )
                ]

                concluidas = [
                    consulta
                    for consulta in consultas
                    if consulta.status
                    == "concluida"
                ]

                canceladas = [
                    consulta
                    for consulta in consultas
                    if consulta.status
                    == "cancelada"
                ]

                proximas = []

                for consulta in futuras[:6]:
                    proximas.append(
                        {
                            "id": consulta.id,
                            "paciente": (
                                f"{consulta.usuario.nome} "
                                f"{consulta.usuario.sobrenome}"
                            ).strip(),
                            "data": consulta.data,
                            "horario": (
                                consulta.horario
                            ),
                        }
                    )

                nome_medico = (
                    (
                        f"{medico.nome} "
                        f"{medico.sobrenome}"
                    ).strip()
                    if medico
                    else "Médico não encontrado"
                )

                especialidade = (
                    medico.especialidade
                    if medico
                    else ""
                )

            metricas = [
                {
                    "titulo": "Consultas hoje",
                    "valor": len(
                        hoje_agendadas
                    ),
                    "descricao": (
                        "Atendimentos agendados "
                        "para hoje."
                    ),
                    "tipo": "azul",
                },
                {
                    "titulo": "Próximas consultas",
                    "valor": len(futuras),
                    "descricao": (
                        "Agenda futura ainda aberta."
                    ),
                    "tipo": "verde",
                },
                {
                    "titulo": "Concluídas",
                    "valor": len(concluidas),
                    "descricao": (
                        "Atendimentos finalizados "
                        "no sistema."
                    ),
                    "tipo": "cinza",
                },
                {
                    "titulo": "Canceladas",
                    "valor": len(canceladas),
                    "descricao": (
                        "Consultas canceladas "
                        "pelos usuários."
                    ),
                    "tipo": "vermelho",
                },
            ]

            self.area_dinamica.addLayout(
                self.criar_grade_metricas(
                    metricas
                )
            )

            grade = QGridLayout()
            grade.setHorizontalSpacing(16)

            perfil_frame, perfil_layout = (
                self.criar_secao(
                    "Identificação profissional",
                    (
                        "Dados vinculados ao seu "
                        "acesso médico."
                    ),
                )
            )

            perfil_layout.addWidget(
                self.criar_linha_info(
                    nome_medico,
                    (
                        especialidade
                        or (
                            "Especialidade não "
                            "informada"
                        )
                    ),
                    "Médico",
                )
            )

            agenda_frame, agenda_layout = (
                self.criar_secao(
                    "Próximos pacientes",
                    (
                        "Ordem cronológica dos "
                        "atendimentos agendados."
                    ),
                )
            )

            if proximas:
                for consulta in proximas:
                    agenda_layout.addWidget(
                        self.criar_linha_info(
                            consulta["paciente"],
                            (
                                f"Consulta #{consulta['id']} • "
                                f"{formatar_data(consulta['data'])} "
                                f"às {consulta['horario']}"
                            ),
                            "Agendada",
                        )
                    )
            else:
                agenda_layout.addWidget(
                    self.criar_linha_info(
                        "Nenhuma consulta futura",
                        (
                            "Novos agendamentos "
                            "aparecerão automaticamente "
                            "nesta lista."
                        ),
                    )
                )

            grade.addWidget(
                perfil_frame,
                0,
                0,
            )
            grade.addWidget(
                agenda_frame,
                0,
                1,
            )

            grade.setColumnStretch(0, 1)
            grade.setColumnStretch(1, 2)

            self.area_dinamica.addLayout(
                grade
            )

        except Exception as erro:
            self.mostrar_erro(erro)


class TelaDashboardAdmin(DashboardBase):
    def __init__(self, usuario):
        nome = (
            getattr(
                usuario,
                "nome",
                "Administrador",
            )
            or "Administrador"
        )

        super().__init__(
            usuario,
            (
                "Painel administrativo — "
                f"{nome}"
            ),
            (
                "Visão geral da operação AFGMED "
                "no banco compartilhado entre "
                "web e desktop."
            ),
        )

        self.recarregar()

    def recarregar(self):
        self.limpar_area()

        try:
            with app.app_context():
                total_usuarios = (
                    Usuario.query.count()
                )

                total_medicos = (
                    Medico.query.count()
                )

                produtos_ativos = (
                    Produto.query.filter_by(
                        ativo=True
                    ).count()
                )

                estoque_baixo = (
                    Produto.query.filter(
                        Produto.ativo.is_(True),
                        Produto.estoque <= 5,
                    ).count()
                )

                pedidos_pendentes = (
                    Pedido.query.filter(
                        Pedido.status.in_(
                            [
                                "aguardando_pagamento",
                                "falha",
                            ]
                        )
                    ).count()
                )

                consultas_agendadas = (
                    Consulta.query.filter(
                        Consulta.status
                        == "agendada",
                        Consulta.data
                        >= date.today(),
                    ).count()
                )

                produtos_criticos = (
                    Produto.query.filter(
                        Produto.ativo.is_(True),
                        Produto.estoque <= 10,
                    )
                    .order_by(
                        Produto.estoque.asc(),
                        Produto.nome.asc(),
                    )
                    .limit(6)
                    .all()
                )

                pedidos_recentes = (
                    Pedido.query.order_by(
                        Pedido.data_criacao.desc()
                    )
                    .limit(6)
                    .all()
                )

                lista_estoque = [
                    {
                        "nome": produto.nome,
                        "estoque": int(
                            produto.estoque or 0
                        ),
                        "ativo": bool(
                            produto.ativo
                        ),
                    }
                    for produto
                    in produtos_criticos
                ]

                lista_pedidos = [
                    {
                        "id": pedido.id,
                        "cliente": (
                            f"{pedido.usuario.nome} "
                            f"{pedido.usuario.sobrenome}"
                        ).strip(),
                        "total": float(
                            pedido.total or 0
                        ),
                        "status": (
                            pedido.status
                            or "em análise"
                        ),
                    }
                    for pedido
                    in pedidos_recentes
                ]

            metricas = [
                {
                    "titulo": "Usuários",
                    "valor": total_usuarios,
                    "descricao": (
                        "Contas cadastradas "
                        "no sistema."
                    ),
                    "tipo": "azul",
                },
                {
                    "titulo": "Médicos",
                    "valor": total_medicos,
                    "descricao": (
                        "Profissionais disponíveis."
                    ),
                    "tipo": "verde",
                },
                {
                    "titulo": "Produtos ativos",
                    "valor": produtos_ativos,
                    "descricao": (
                        f"{estoque_baixo} com "
                        "estoque crítico."
                    ),
                    "tipo": (
                        "amarelo"
                        if estoque_baixo
                        else "cinza"
                    ),
                },
                {
                    "titulo": "Consultas futuras",
                    "valor": consultas_agendadas,
                    "descricao": (
                        "Agendamentos ainda "
                        "em aberto."
                    ),
                    "tipo": "verde",
                },
                {
                    "titulo": "Pedidos pendentes",
                    "valor": pedidos_pendentes,
                    "descricao": (
                        "Aguardando pagamento "
                        "ou correção."
                    ),
                    "tipo": (
                        "vermelho"
                        if pedidos_pendentes
                        else "cinza"
                    ),
                },
            ]

            self.area_dinamica.addLayout(
                self.criar_grade_metricas(
                    metricas
                )
            )

            grade = QGridLayout()
            grade.setHorizontalSpacing(16)
            grade.setVerticalSpacing(16)

            estoque_frame, estoque_layout = (
                self.criar_secao(
                    "Atenção ao estoque",
                    (
                        "Produtos ativos com até "
                        "10 unidades disponíveis."
                    ),
                )
            )

            if lista_estoque:
                for produto in lista_estoque:
                    status = (
                        "Sem estoque"
                        if produto["estoque"] <= 0
                        else "Estoque baixo"
                    )

                    estoque_layout.addWidget(
                        self.criar_linha_info(
                            produto["nome"],
                            (
                                "Quantidade disponível: "
                                f"{produto['estoque']} "
                                "unidade(s)"
                            ),
                            status,
                        )
                    )
            else:
                estoque_layout.addWidget(
                    self.criar_linha_info(
                        "Nenhum estoque crítico",
                        (
                            "Todos os produtos ativos "
                            "possuem mais de 10 unidades."
                        ),
                        "Normal",
                    )
                )

            pedidos_frame, pedidos_layout = (
                self.criar_secao(
                    "Pedidos recentes",
                    (
                        "Últimas movimentações "
                        "de compra registradas."
                    ),
                )
            )

            if lista_pedidos:
                for pedido in lista_pedidos:
                    pedidos_layout.addWidget(
                        self.criar_linha_info(
                            (
                                f"Pedido #{pedido['id']} — "
                                f"{pedido['cliente']}"
                            ),
                            formatar_real(
                                pedido["total"]
                            ),
                            (
                                pedido["status"]
                                .replace("_", " ")
                                .title()
                            ),
                        )
                    )
            else:
                pedidos_layout.addWidget(
                    self.criar_linha_info(
                        "Nenhum pedido registrado",
                        (
                            "As compras dos usuários "
                            "aparecerão nesta área."
                        ),
                    )
                )

            grade.addWidget(
                estoque_frame,
                0,
                0,
            )
            grade.addWidget(
                pedidos_frame,
                0,
                1,
            )

            grade.setColumnStretch(0, 1)
            grade.setColumnStretch(1, 1)

            self.area_dinamica.addLayout(
                grade
            )

        except Exception as erro:
            self.mostrar_erro(erro)


def criar_dashboard(usuario):
    if bool(
        getattr(
            usuario,
            "is_admin",
            False,
        )
    ):
        return TelaDashboardAdmin(usuario)

    if bool(
        getattr(
            usuario,
            "is_medico",
            False,
        )
    ):
        return TelaDashboardMedico(usuario)

    return TelaDashboardUsuario(usuario)