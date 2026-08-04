"""Configuração dos testes para a versão ORIGINAL do AFGMED Desktop.

O banco de testes é criado em uma pasta temporária. O banco real do projeto
(projetoafgmed/instance/afgmed.db) nunca é alterado.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest


TEST_DATABASE_DIR = Path(tempfile.mkdtemp(prefix="afgmed_original_pytest_"))
TEST_DATABASE_PATH = TEST_DATABASE_DIR / "afgmed_testes.db"

# Estas variáveis precisam ser definidas antes de importar projetoafgmed,
# porque a aplicação configura o SQLAlchemy durante o import.
os.environ["DATABASE_PATH"] = str(TEST_DATABASE_PATH)
os.environ["SECRET_KEY"] = "chave-exclusiva-dos-testes"
os.environ["MERCADO_PAGO_ACCESS_TOKEN"] = "token-falso-dos-testes"
os.environ["APP_BASE_URL"] = "http://localhost:5000"

from projetoafgmed import app as aplicacao_flask  # noqa: E402
from projetoafgmed import bcrypt, database  # noqa: E402
from projetoafgmed.models import Medico, Produto, Usuario  # noqa: E402


@pytest.fixture(scope="session")
def app():
    aplicacao_flask.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="chave-exclusiva-dos-testes",
        PROPAGATE_EXCEPTIONS=True,
    )
    return aplicacao_flask


@pytest.fixture(scope="session", autouse=True)
def limpar_arquivos_temporarios(app):
    yield

    with app.app_context():
        database.session.remove()
        database.engine.dispose()

    shutil.rmtree(TEST_DATABASE_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def banco_limpo(app):
    """Cria um banco vazio antes de cada teste."""
    with app.app_context():
        database.session.remove()
        database.drop_all()
        database.create_all()
        yield
        database.session.rollback()
        database.session.remove()
        database.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def criar_usuario():
    def _criar_usuario(
        *,
        nome="Usuário",
        sobrenome="Teste",
        email=None,
        senha="123456",
        is_admin=False,
        is_medico=False,
        id_medico=None,
    ):
        usuario = Usuario(
            nome=nome,
            sobrenome=sobrenome,
            email=email or f"usuario-{uuid4().hex}@teste.com",
            senha=bcrypt.generate_password_hash(senha).decode("utf-8"),
            is_admin=is_admin,
            is_medico=is_medico,
            id_medico=id_medico,
        )
        database.session.add(usuario)
        database.session.commit()
        return usuario

    return _criar_usuario


@pytest.fixture
def criar_medico():
    def _criar_medico(
        *,
        nome="Médico",
        sobrenome="Teste",
        especialidade="Clínico Geral",
        email=None,
        telefone="(11) 99999-9999",
    ):
        medico = Medico(
            nome=nome,
            sobrenome=sobrenome,
            especialidade=especialidade,
            email=email or f"medico-{uuid4().hex}@teste.com",
            telefone=telefone,
            foto="default.jpg",
        )
        database.session.add(medico)
        database.session.commit()
        return medico

    return _criar_medico


@pytest.fixture
def criar_produto():
    def _criar_produto(
        *,
        nome=None,
        descricao="Produto criado durante os testes.",
        preco=10.0,
        estoque=5,
        ativo=True,
        destaque_home=False,
    ):
        produto = Produto(
            nome=nome or f"Produto {uuid4().hex[:8]}",
            descricao=descricao,
            preco=preco,
            estoque=estoque,
            ativo=ativo,
            destaque_home=destaque_home,
            foto="default.jpg",
        )
        database.session.add(produto)
        database.session.commit()
        return produto

    return _criar_produto


@pytest.fixture
def autenticar(client):
    """Autentica diretamente pela sessão do Flask-Login."""
    def _autenticar(usuario):
        with client.session_transaction() as sessao:
            sessao["_user_id"] = str(usuario.id)
            sessao["_fresh"] = True
        return usuario

    return _autenticar
