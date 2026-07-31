from projetoafgmed import app
from projetoafgmed.models import Usuario


with app.app_context():

    usuarios = Usuario.query.all()

    for usuario in usuarios:
        print(
            usuario.nome,
            usuario.email,
            usuario.is_admin,
            usuario.is_medico
        )