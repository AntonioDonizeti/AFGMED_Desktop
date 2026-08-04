"""Testes de cadastro, login e logout."""

from projetoafgmed.models import Usuario


def test_criar_conta_normaliza_email(client):
    resposta = client.post(
        "/criar-conta",
        data={
            "nome": "Fabricio",
            "sobrenome": "Ferreira",
            "email": "FABRICIO@TESTE.COM",
            "senha": "123456",
            "confirmacao_senha": "123456",
            "botao_confirmacao": "Cadastrar",
        },
        follow_redirects=False,
    )

    usuario = Usuario.query.one()
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]
    assert usuario.email == "fabricio@teste.com"


def test_nao_cria_conta_com_email_duplicado(client, criar_usuario):
    criar_usuario(email="duplicado@teste.com")

    resposta = client.post(
        "/criar-conta",
        data={
            "nome": "Outro",
            "sobrenome": "Usuário",
            "email": "duplicado@teste.com",
            "senha": "123456",
            "confirmacao_senha": "123456",
            "botao_confirmacao": "Cadastrar",
        },
    )

    assert resposta.status_code == 200
    assert Usuario.query.count() == 1


def test_login_correto_redireciona_para_home(client, criar_usuario):
    criar_usuario(email="login@teste.com", senha="senha123")

    resposta = client.post(
        "/login",
        data={
            "email": "login@teste.com",
            "senha": "senha123",
            "botao_confirmacao": "Entrar",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/")


def test_login_incorreto_nao_autentica(client, criar_usuario):
    criar_usuario(email="login@teste.com", senha="senha123")

    resposta = client.post(
        "/login",
        data={
            "email": "login@teste.com",
            "senha": "errada",
            "botao_confirmacao": "Entrar",
        },
    )

    assert resposta.status_code == 200
    with client.session_transaction() as sessao:
        mensagens = [texto for _, texto in sessao.get("_flashes", [])]
    assert "Email ou senha incorretos." in mensagens


def test_login_medico_redireciona_para_medicos(
    client,
    criar_usuario,
    criar_medico,
):
    medico = criar_medico()
    criar_usuario(
        email="medico.login@teste.com",
        senha="123456",
        is_medico=True,
        id_medico=medico.id,
    )

    resposta = client.post(
        "/login",
        data={
            "email": "medico.login@teste.com",
            "senha": "123456",
            "botao_confirmacao": "Entrar",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert "/medicos" in resposta.headers["Location"]


def test_logout_encerra_sessao(client, autenticar, criar_usuario):
    usuario = criar_usuario()
    autenticar(usuario)

    resposta = client.get("/logout", follow_redirects=False)

    assert resposta.status_code == 302
    with client.session_transaction() as sessao:
        assert "_user_id" not in sessao
