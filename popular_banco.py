from projetoafgmed import app, bcrypt, database
from projetoafgmed.models import Medico, Produto
from projetoafgmed.servicos_medicos import (
    SENHA_PADRAO_MEDICO,
    sincronizar_usuario_medico,
)


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
        "alexandra.png",
    ),
    (
        "Fernanda",
        "Oliveira",
        "Pediatria",
        "fernanda.oliveira@medteste.com",
        "(11) 98765-1002",
        "medica_Fernanda.png",
    ),
    (
        "Juliana",
        "Almeida",
        "Ginecologia",
        "juliana.almeida@medteste.com",
        "(11) 98765-1003",
        "medica_juliana.png",
    ),
    (
        "Marcela",
        "Costa",
        "Dermatologia",
        "marcela.costa@medteste.com",
        "(11) 98765-1004",
        "medica_marcela.png",
    ),
    (
        "Patrícia",
        "Mendes",
        "Oftalmologia",
        "patricia.mendes@medteste.com",
        "(11) 98765-1005",
        "medica_patricia.png",
    ),
    (
        "Adriano",
        "Silva",
        "Clínico Geral",
        "adriano.silva@medteste.com",
        "(11) 98765-1006",
        "medico_Adriano.png",
    ),
    (
        "Carlos",
        "Ferreira",
        "Ortopedia",
        "carlos.ferreira@medteste.com",
        "(11) 98765-1007",
        "medico_carlos.png",
    ),
    (
        "Kauan",
        "Santos",
        "Cardiologia",
        "kauan.santos@medteste.com",
        "(11) 98765-1008",
        "medico_kauan.png",
    ),
    (
        "Camila",
        "Rodrigues",
        "Endocrinologia",
        "camila.rodrigues@medteste.com",
        "(11) 98765-1009",
        "medica_camila.png",
    ),
    (
        "Renata",
        "Carvalho",
        "Reumatologia",
        "renata.carvalho@medteste.com",
        "(11) 98765-1010",
        "medica_renata.png",
    ),
    (
        "Larissa",
        "Teixeira",
        "Infectologia",
        "larissa.teixeira@medteste.com",
        "(11) 98765-1011",
        "medica_larissa.png",
    ),
    (
        "Beatriz",
        "Moreira",
        "Hematologia",
        "beatriz.moreira@medteste.com",
        "(11) 98765-1012",
        "medica_beatriz.png",
    ),
    (
        "Bruno",
        "Martins",
        "Urologia",
        "bruno.martins@medteste.com",
        "(11) 98765-1013",
        "medico_bruno.png",
    ),
    (
        "Ricardo",
        "Pereira",
        "Neurologia",
        "ricardo.pereira@medteste.com",
        "(11) 98765-1014",
        "medico_ricardo.png",
    ),
    (
        "Rafael",
        "Souza",
        "Psiquiatria",
        "rafael.souza@medteste.com",
        "(11) 98765-1015",
        "medico_rafael.png",
    ),
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
        "Amoxicilina_500mg.png",
    ),
    (
        "Ibuprofeno 400mg",
        "Medicamento com ação anti-inflamatória e analgésica.",
        12.90,
        220,
        "Ibuprofeno_400mg.png",
    ),
    (
        "Paracetamol 500mg",
        "Analgésico e antitérmico para alívio de dores e febre.",
        8.50,
        300,
        "Paracetamol_500mg.png",
    ),
    (
        "Dipirona 500mg",
        "Analgésico e antitérmico em comprimidos.",
        12.90,
        250,
        "Dipirona_500mg.png",
    ),
    (
        "Dorflex",
        "Analgésico e relaxante muscular em comprimidos.",
        16.99,
        160,
        "Dorflex.png",
    ),
    (
        "Benegrip",
        "Medicamento para alívio dos sintomas de gripes e resfriados.",
        24.90,
        130,
        "Benegrip.png",
    ),
    (
        "Neosoro Adulto",
        "Solução nasal de uso adulto.",
        9.90,
        80,
        "Neosoro_Adulto.png",
    ),
    (
        "Buscopan",
        "Medicamento utilizado para o alívio de cólicas.",
        23.90,
        90,
        "Buscopan.png",
    ),
    (
        "Simeticona 40mg",
        "Medicamento utilizado para o alívio de gases.",
        10.90,
        100,
        "Simeticona_40mg.png",
    ),
    (
        "Omeprazol 20mg",
        "Medicamento utilizado para redução da acidez no estômago.",
        19.90,
        180,
        "Omeprazol_20mg.png",
    ),
    (
        "Loratadina 10mg",
        "Medicamento antialérgico em comprimidos.",
        11.50,
        120,
        "Loratadina_10mg.png",
    ),
]


def popular_banco():
    with app.app_context():
        medicos_novos = 0
        medicos_atualizados = 0
        medicos_vinculados = 0
        medicos_com_erro = 0

        produtos_novos = 0
        produtos_atualizados = 0

        try:
            # ==================================================
            # CADASTRAR, ATUALIZAR E VINCULAR MÉDICOS
            # ==================================================

            print()
            print("=" * 55)
            print("CADASTRANDO E VINCULANDO MÉDICOS")
            print("=" * 55)

            for (
                nome,
                sobrenome,
                especialidade,
                email,
                telefone,
                foto,
            ) in medicos:
                email_normalizado = email.strip().lower()

                medico = Medico.query.filter_by(
                    email=email_normalizado
                ).first()

                if medico:
                    medico.nome = nome
                    medico.sobrenome = sobrenome
                    medico.especialidade = especialidade
                    medico.email = email_normalizado
                    medico.telefone = telefone
                    medico.foto = foto

                    medicos_atualizados += 1

                    print(
                        f"Médico atualizado: "
                        f"{medico.nome} {medico.sobrenome}"
                    )

                else:
                    medico = Medico(
                        nome=nome,
                        sobrenome=sobrenome,
                        especialidade=especialidade,
                        email=email_normalizado,
                        telefone=telefone,
                        foto=foto,
                    )

                    database.session.add(medico)

                    medicos_novos += 1

                    print(
                        f"Novo médico cadastrado: "
                        f"{nome} {sobrenome}"
                    )

                # Garante que o médico possua um ID antes
                # de criar o vínculo na tabela Usuario.
                database.session.flush()

                usuario_medico, erro_vinculo = (
                    sincronizar_usuario_medico(medico)
                )

                if erro_vinculo:
                    medicos_com_erro += 1

                    print(
                        f"ERRO no vínculo de "
                        f"{nome} {sobrenome}: "
                        f"{erro_vinculo}"
                    )

                    continue

                # Define a senha padrão para todas as contas
                # médicas de demonstração.
                usuario_medico.senha = (
                    bcrypt.generate_password_hash(
                        SENHA_PADRAO_MEDICO
                    ).decode("utf-8")
                )

                usuario_medico.nome = nome
                usuario_medico.sobrenome = sobrenome
                usuario_medico.email = email_normalizado
                usuario_medico.is_medico = True
                usuario_medico.id_medico = medico.id

                medicos_vinculados += 1

                print(
                    f"Acesso médico vinculado: "
                    f"{email_normalizado}"
                )

            # ==================================================
            # CADASTRAR OU ATUALIZAR PRODUTOS
            # ==================================================

            print()
            print("=" * 55)
            print("CADASTRANDO E ATUALIZANDO PRODUTOS")
            print("=" * 55)

            for (
                nome,
                descricao,
                preco,
                estoque,
                foto,
            ) in produtos:
                produto = Produto.query.filter_by(
                    nome=nome
                ).first()

                if produto:
                    produto.descricao = descricao
                    produto.preco = preco
                    produto.estoque = estoque
                    produto.foto = foto
                    produto.ativo = True

                    produtos_atualizados += 1

                    print(
                        f"Produto atualizado: "
                        f"{produto.nome}"
                    )

                else:
                    produto = Produto(
                        nome=nome,
                        descricao=descricao,
                        preco=preco,
                        estoque=estoque,
                        foto=foto,
                        ativo=True,
                    )

                    database.session.add(produto)

                    produtos_novos += 1

                    print(
                        f"Novo produto cadastrado: "
                        f"{nome}"
                    )

            # ==================================================
            # SALVAR ALTERAÇÕES
            # ==================================================

            database.session.commit()

            print()
            print("=" * 55)
            print("BANCO DE DADOS ATUALIZADO COM SUCESSO")
            print("=" * 55)

            print(f"Médicos novos: {medicos_novos}")
            print(
                f"Médicos atualizados: "
                f"{medicos_atualizados}"
            )
            print(
                f"Médicos com acesso vinculado: "
                f"{medicos_vinculados}"
            )
            print(
                f"Médicos com erro de vínculo: "
                f"{medicos_com_erro}"
            )

            print()
            print(f"Produtos novos: {produtos_novos}")
            print(
                f"Produtos atualizados: "
                f"{produtos_atualizados}"
            )

            print()
            print("=" * 55)
            print("ACESSO DOS MÉDICOS")
            print("=" * 55)
            print(
                "Login: e-mail cadastrado de cada médico"
            )
            print(
                f"Senha padrão: "
                f"{SENHA_PADRAO_MEDICO}"
            )
            print("=" * 55)

        except Exception as erro:
            database.session.rollback()

            print()
            print("=" * 55)
            print("NÃO FOI POSSÍVEL ATUALIZAR O BANCO")
            print("=" * 55)
            print(f"Erro: {erro}")

            raise


if __name__ == "__main__":
    popular_banco()

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