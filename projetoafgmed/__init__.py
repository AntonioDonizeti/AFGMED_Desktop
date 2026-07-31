from pathlib import Path
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv


# Pasta onde está o pacote projetoafgmed
PACKAGE_DIR = Path(__file__).resolve().parent

# Pasta principal do projeto AFGMED
PROJECT_ROOT = PACKAGE_DIR.parent

# Carrega explicitamente o .env da pasta principal
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)


app = Flask(__name__)


# ==========================
# CONFIGURAÇÕES
# ==========================

app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'chave-dev-afgmed'
)


# ==========================
# BANCO DE DADOS
# ==========================

# ==========================
# BANCO DE DADOS
# ==========================

database_path_env = os.environ.get(
    "DATABASE_PATH",
    "projetoafgmed/instance/afgmed.db"
).strip()

database_path = Path(database_path_env)

# Caso o caminho do .env seja relativo,
# completa usando a pasta principal do projeto
if not database_path.is_absolute():
    database_path = PROJECT_ROOT / database_path

# Converte para um caminho absoluto normalizado
database_path = database_path.resolve()

# Garante que a pasta do banco exista
database_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{database_path.as_posix()}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# ==========================
# CONFIGURAÇÕES EXTERNAS
# ==========================

app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get(
    'GOOGLE_MAPS_API_KEY',
    ''
)


app.config['MERCADO_PAGO_ACCESS_TOKEN'] = os.environ.get(
    'MERCADO_PAGO_ACCESS_TOKEN',
    ''
)


app.config["APP_BASE_URL"] = os.environ.get(
    "APP_BASE_URL",
    ""
)



# ==========================
# UPLOADS
# ==========================

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'static',
    'uploads'
)


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



# ==========================
# EXTENSÕES
# ==========================

database = SQLAlchemy(app)

bcrypt = Bcrypt(app)

csrf = CSRFProtect(app)


login_manager = LoginManager(app)

login_manager.login_view = 'login'

login_manager.login_message_category = 'info'



# ==========================
# ROTAS
# ==========================

from projetoafgmed.rotas import registrar_rotas

registrar_rotas()