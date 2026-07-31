from projetoafgmed import app, database
from projetoafgmed.models import Medico, Produto

medicos = [
    ("Adriano", "Silva", "Clínico Geral", "adriano.silva@medteste.com", "(11)98765-1234", "medico_adriano.jpg"),
    ("Fernanda", "Oliveira", "Pediatria", "fernanda.oliveira@medteste.com", "(11)98877-2233", "medica_fernanda.jpg"),
    ("Kauan", "Santos", "Cardiologia", "kauan.santos@medteste.com", "(11)99111-3344", "medico_kauan.jpg"),
    ("Marcela", "Costa", "Dermatologia", "marcela.costa@medteste.com", "(11)99222-4455", "medica_marcela.jpg"),
    ("Carlos", "Ferreira", "Ortopedia", "carlos.ferreira@medteste.com", "(11)99333-5566", "medico_carlos.jpg")
]

produtos = [
    ("Amoxicilina 500mg", "Antibiótico utilizado no tratamento de infecções bacterianas.", 24.90, 150, "Amoxicilina_500mg.jpg"),
    ("Paracetamol 500mg", "Redução da febre e alívio de dores leves.", 8.50, 300, "Paracetamol_500mg.jpg"),
    ("Ibuprofeno 400mg", "Anti-inflamatório e analgésico.", 12.90, 220, "Ibuprofeno_400mg.jpg")
]

with app.app_context():

    for nome, sobrenome, especialidade, email, telefone, foto in medicos:
        medico = Medico(
            nome=nome,
            sobrenome=sobrenome,
            especialidade=especialidade,
            email=email,
            telefone=telefone,
            foto=foto
        )
        database.session.add(medico)

    for nome, descricao, preco, estoque, foto in produtos:
        produto = Produto(
            nome=nome,
            descricao=descricao,
            preco=preco,
            estoque=estoque,
            foto=foto
        )
        database.session.add(produto)

    database.session.commit()

    print("Dados cadastrados com sucesso!")