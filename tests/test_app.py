"""Testes de inicialização, rotas e sintaxe do projeto original."""

from pathlib import Path
import py_compile


def test_aplicacao_registra_33_rotas(app):
    assert len(list(app.url_map.iter_rules())) == 33


def test_rotas_principais_estao_registradas(app):
    endpoints = {regra.endpoint for regra in app.url_map.iter_rules()}
    esperados = {
        "homepage",
        "criar_conta",
        "login",
        "logout",
        "perfil",
        "medicos",
        "consultas",
        "meus_agendamentos",
        "produtos",
        "ver_carrinho",
        "entrega",
        "meus_pedidos",
    }
    assert esperados.issubset(endpoints)


def test_homepage_responde_com_sucesso(client):
    resposta = client.get("/")
    assert resposta.status_code == 200


def test_rota_protegida_redireciona_para_login(client):
    resposta = client.get("/produtos", follow_redirects=False)
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_arquivos_python_do_projeto_compilam():
    raiz = Path(__file__).resolve().parents[1]
    arquivos = []

    for pasta in (raiz / "projetoafgmed", raiz / "desktop"):
        arquivos.extend(
            caminho
            for caminho in pasta.rglob("*.py")
            if "__pycache__" not in caminho.parts
        )

    assert arquivos, "Nenhum arquivo Python foi localizado."

    for arquivo in arquivos:
        py_compile.compile(str(arquivo), doraise=True)
