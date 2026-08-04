from projetoafgmed import app, database
from projetoafgmed.models import Medico, Produto


# ==========================================================
# LISTA DE MÉDICOS
# nome, sobrenome, especialidade, e-mail, telefone, foto
# ==========================================================

medicos = [
    (
        "Alexandra",
        "Moura",
        "Clínico Geral",
        "alexandra.moura@medteste.com",
        "(11) 98765-1001",
        "alexandra.png"
    ),
    (
        "Fernanda",
        "Oliveira",
        "Pediatria",
        "fernanda.oliveira@medteste.com",
        "(11) 98765-1002",
        "medica_Fernanda.png"
    ),
    (
        "Juliana",
        "Almeida",
        "Ginecologia",
        "juliana.almeida@medteste.com",
        "(11) 98765-1003",
        "medica_juliana.png"
    ),
    (
        "Marcela",
        "Costa",
        "Dermatologia",
        "marcela.costa@medteste.com",
        "(11) 98765-1004",
        "medica_marcela.png"
    ),
    (
        "Patrícia",
        "Mendes",
        "Oftalmologia",
        "patricia.mendes@medteste.com",
        "(11) 98765-1005",
        "medica_patricia.png"
    ),
    (
        "Adriano",
        "Silva",
        "Clínico Geral",
        "adriano.silva@medteste.com",
        "(11) 98765-1006",
        "medico_Adriano.png"
    ),
    (
        "Carlos",
        "Ferreira",
        "Ortopedia",
        "carlos.ferreira@medteste.com",
        "(11) 98765-1007",
        "medico_carlos.png"
    ),
    (
        "Kauan",
        "Santos",
        "Cardiologia",
        "kauan.santos@medteste.com",
        "(11) 98765-1008",
        "medico_kauan.png"
    ),
    (
        "Camila",
        "Rodrigues",
        "Endocrinologia",
        "camila.rodrigues@medteste.com",
        "(11) 98765-1009",
        "medica_camila.png"
    ),
    (
        "Renata",
        "Carvalho",
        "Reumatologia",
        "renata.carvalho@medteste.com",
        "(11) 98765-1010",
        "medica_renata.png"
    ),
    (
        "Larissa",
        "Teixeira",
        "Infectologia",
        "larissa.teixeira@medteste.com",
        "(11) 98765-1011",
        "medica_larissa.png"
    ),
    (
        "Beatriz",
        "Moreira",
        "Hematologia",
        "beatriz.moreira@medteste.com",
        "(11) 98765-1012",
        "medica_beatriz.png"
    ),
    (
        "Bruno",
        "Martins",
        "Urologia",
        "bruno.martins@medteste.com",
        "(11) 98765-1013",
        "medico_bruno.png"
    ),
    (
        "Ricardo",
        "Pereira",
        "Neurologia",
        "ricardo.pereira@medteste.com",
        "(11) 98765-1014",
        "medico_ricardo.png"
    ),
    (
        "Rafael",
        "Souza",
        "Psiquiatria",
        "rafael.souza@medteste.com",
        "(11) 98765-1015",
        "medico_rafael.png"
    )
]


# ==========================================================
# LISTA DE PRODUTOS
# nome, descrição, preço, estoque, foto
# ==========================================================

produtos = [
    (
        "Amoxicilina 500mg",
        "Antibiótico utilizado no tratamento de infecções bacterianas.",
        24.90,
        150,
        "Amoxicilina_500mg.png"
    ),
    (
        "Ibuprofeno 400mg",
        "Medicamento com ação anti-inflamatória e analgésica.",
        12.90,
        220,
        "Ibuprofeno_400mg.png"
    ),
    (
        "Paracetamol 500mg",
        "Analgésico e antitérmico para alívio de dores e febre.",
        8.50,
        300,
        "Paracetamol_500mg.png"
    ),
    (
        "Dipirona 500mg",
        "Analgésico e antitérmico em comprimidos.",
        12.90,
        250,
        "Dipirona_500mg.png"
    ),
    (
        "Dorflex",
        "Analgésico e relaxante muscular em comprimidos.",
        16.99,
        160,
        "Dorflex.png"
    ),
    (
        "Benegrip",
        "Medicamento para alívio dos sintomas de gripes e resfriados.",
        24.90,
        130,
        "Benegrip.png"
    ),
    (
        "Neosoro Adulto",
        "Solução nasal de uso adulto.",
        9.90,
        80,
        "Neosoro_Adulto.png"
    ),
    (
        "Buscopan",
        "Medicamento utilizado para o alívio de cólicas.",
        23.90,
        90,
        "Buscopan.png"
    ),
    (
        "Simeticona 40mg",
        "Medicamento utilizado para o alívio de gases.",
        10.90,
        100,
        "Simeticona_40mg.png"
    ),
    (
        "Omeprazol 20mg",
        "Medicamento utilizado para redução da acidez no estômago.",
        19.90,
        180,
        "Omeprazol_20mg.png"
    ),
    (
        "Loratadina 10mg",
        "Medicamento antialérgico em comprimidos.",
        11.50,
        120,
        "Loratadina_10mg.png"
    )
]


# ==========================================================
# POPULAR E ATUALIZAR O BANCO DE DADOS
# ==========================================================

with app.app_context():

    medicos_novos = 0
    medicos_atualizados = 0

    produtos_novos = 0
    produtos_atualizados = 0

    try:

        # ==================================================
        # CADASTRAR OU ATUALIZAR MÉDICOS
        # ==================================================

        for (
            nome,
            sobrenome,
            especialidade,
            email,
            telefone,
            foto
        ) in medicos:

            medico = Medico.query.filter_by(email=email).first()

            if medico:
                medico.nome = nome
                medico.sobrenome = sobrenome
                medico.especialidade = especialidade
                medico.telefone = telefone
                medico.foto = foto

                medicos_atualizados += 1

                print(
                    f"Médico atualizado: "
                    f"{medico.nome} {medico.sobrenome}"
                )

            else:
                novo_medico = Medico(
                    nome=nome,
                    sobrenome=sobrenome,
                    especialidade=especialidade,
                    email=email,
                    telefone=telefone,
                    foto=foto
                )

                database.session.add(novo_medico)
                medicos_novos += 1

                print(
                    f"Novo médico cadastrado: "
                    f"{nome} {sobrenome}"
                )

        # ==================================================
        # CADASTRAR OU ATUALIZAR PRODUTOS
        # ==================================================

        for nome, descricao, preco, estoque, foto in produtos:

            produto = Produto.query.filter_by(nome=nome).first()

            if produto:
                produto.descricao = descricao
                produto.preco = preco
                produto.estoque = estoque
                produto.foto = foto

                produtos_atualizados += 1

                print(f"Produto atualizado: {produto.nome}")

            else:
                novo_produto = Produto(
                    nome=nome,
                    descricao=descricao,
                    preco=preco,
                    estoque=estoque,
                    foto=foto
                )

                database.session.add(novo_produto)
                produtos_novos += 1

                print(f"Novo produto cadastrado: {nome}")

        # ==================================================
        # SALVAR ALTERAÇÕES
        # ==================================================

        database.session.commit()

        print("\n==========================================")
        print("BANCO DE DADOS ATUALIZADO COM SUCESSO!")
        print("==========================================")

        print(f"Médicos novos: {medicos_novos}")
        print(f"Médicos atualizados: {medicos_atualizados}")

        print(f"Produtos novos: {produtos_novos}")
        print(f"Produtos atualizados: {produtos_atualizados}")

    except Exception as erro:

        database.session.rollback()

        print("\nNão foi possível atualizar o banco.")
        print(f"Erro: {erro}")