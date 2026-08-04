"""Testes de vínculo médico e permissões administrativas."""

from projetoafgmed import database
from projetoafgmed.models import Produto, Usuario
from projetoafgmed.servicos_medicos import (
    SENHA_PADRAO_MEDICO,
    sincronizar_usuario_medico,
)


def test_sincronizar_medico_cria_usuario_medico(criar_medico):
    medico = criar_medico(email="novo.medico@teste.com")

    usuario, erro = sincronizar_usuario_medico(medico)
    database.session.commit()

    assert erro is None
    assert usuario.is_medico is True
    assert usuario.id_medico == medico.id
    assert usuario.email == "novo.medico@teste.com"
    assert SENHA_PADRAO_MEDICO == "123456"


def test_sincronizar_medico_vincula_usuario_existente(
    criar_usuario,
    criar_medico,
):
    usuario_existente = criar_usuario(email="vinculo@teste.com")
    medico = criar_medico(email="vinculo@teste.com")

    usuario, erro = sincronizar_usuario_medico(medico)
    database.session.commit()

    assert erro is None
    assert usuario.id == usuario_existente.id
    assert usuario.is_medico is True
    assert usuario.id_medico == medico.id
    assert Usuario.query.count() == 1


def test_usuario_comum_nao_acessa_cadastro_de_produto(
    client,
    autenticar,
    criar_usuario,
):
    usuario = criar_usuario(is_admin=False)
    autenticar(usuario)

    resposta = client.get("/cadastro-produto", follow_redirects=False)

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/")


def test_admin_desativa_e_ativa_produto(
    client,
    autenticar,
    criar_usuario,
    criar_produto,
):
    admin = criar_usuario(is_admin=True)
    produto = criar_produto(ativo=True)
    autenticar(admin)

    client.post(f"/desativar-produto/{produto.id}")
    assert database.session.get(Produto, produto.id).ativo is False

    client.post(f"/ativar-produto/{produto.id}")
    assert database.session.get(Produto, produto.id).ativo is True


def test_admin_alterna_destaque_do_produto(
    client,
    autenticar,
    criar_usuario,
    criar_produto,
):
    admin = criar_usuario(is_admin=True)
    produto = criar_produto(destaque_home=False)
    autenticar(admin)

    client.post(f"/alternar-destaque-produto/{produto.id}")

    assert database.session.get(Produto, produto.id).destaque_home is True
