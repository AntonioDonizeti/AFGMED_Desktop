# AFGMED — Sistema de Farmácia e Agendamento Médico

O **AFGMED** é um projeto integrador acadêmico desenvolvido para demonstrar, em uma única solução, funcionalidades de uma farmácia digital e de um sistema de agendamento de consultas médicas.

O projeto possui uma aplicação **web**, construída com Flask, e uma aplicação **desktop**, desenvolvida com PySide6. As duas interfaces utilizam a mesma estrutura de dados e oferecem experiências diferentes de acordo com o perfil do usuário.

> **Aviso:** este projeto foi desenvolvido exclusivamente para fins acadêmicos e de demonstração. Ele não representa uma plataforma médica ou farmacêutica em produção e não deve utilizar dados pessoais reais.

## Funcionalidades

### Usuário

- Criação de conta e autenticação;
- Consulta e atualização do perfil;
- Visualização e pesquisa de médicos;
- Agendamento e reagendamento de consultas;
- Cancelamento e acompanhamento de consultas;
- Visualização e pesquisa de produtos;
- Adição, alteração e remoção de produtos do carrinho;
- Finalização de pedidos;
- Acompanhamento do histórico e do status dos pedidos;
- Integração demonstrativa com o Mercado Pago.

### Médico

- Acesso identificado pelo perfil de médico;
- Visualização das consultas vinculadas ao profissional;
- Acompanhamento dos pacientes e horários agendados;
- Atualização do status das consultas.

### Administrador

- Dashboard com indicadores do sistema;
- Cadastro, edição e remoção de médicos;
- Cadastro, edição, ativação e desativação de produtos;
- Controle de produtos destacados;
- Gerenciamento de consultas;
- Gerenciamento de pedidos e usuários.

## Tecnologias utilizadas

- Python;
- Flask;
- PySide6;
- SQLAlchemy;
- SQLite;
- Flask-Login;
- Flask-WTF e proteção CSRF;
- Flask-Bcrypt;
- HTML5, CSS3 e Bootstrap;
- QSS para estilização da aplicação desktop;
- API do Mercado Pago;
- API do Google Maps;
- Git e GitHub.

## Estrutura do projeto

```text
AFGMED_Desktop/
├── desktop/
│   ├── estilos/              # Temas e arquivos QSS
│   ├── telas/                # Telas desenvolvidas com PySide6
│   └── main.py               # Inicialização da aplicação desktop
├── projetoafgmed/
│   ├── instance/             # Banco SQLite demonstrativo
│   ├── rotas/                # Rotas e controladores Flask
│   ├── static/               # CSS, imagens e arquivos enviados
│   ├── templates/            # Templates HTML
│   ├── __init__.py           # Configuração principal do Flask
│   ├── forms.py              # Formulários e validações
│   ├── models.py             # Models do banco de dados
│   └── servicos_*.py         # Regras de negócio compartilhadas
├── cria_banco.py             # Criação das tabelas
├── popular_banco.py          # Inclusão dos dados demonstrativos
├── tornar_admin.py           # Definição de usuário administrador
└── requirements.txt          # Dependências do projeto
```

## Pré-requisitos

Antes de começar, instale:

- Python 3.11 ou superior;
- Git;
- Um editor como PyCharm ou Visual Studio Code.

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/AntonioDonizeti/AFGMED_Desktop.git
cd AFGMED_Desktop
```

### 2. Crie o ambiente virtual

No Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo chamado `.env` na pasta principal:

```env
SECRET_KEY=adicione-uma-chave-local
DATABASE_PATH=projetoafgmed/instance/afgmed.db
GOOGLE_MAPS_API_KEY=
MERCADO_PAGO_ACCESS_TOKEN=
APP_BASE_URL=
```

Para gerar uma chave local:

```bash
python chave.py
```

As integrações externas são opcionais para a demonstração das funcionalidades principais.

## Preparação do banco de dados

Para criar as tabelas:

```bash
python cria_banco.py
```

Para cadastrar ou atualizar os médicos e produtos demonstrativos:

```bash
python popular_banco.py
```

O script de população pode ser executado novamente: registros encontrados são atualizados em vez de duplicados.

## Execução

### Aplicação desktop

```bash
python -m desktop.main
```

### Aplicação web

```bash
python -m projetoafgmed.main
```

Depois, acesse no navegador o endereço exibido pelo Flask no terminal, normalmente:

```text
http://127.0.0.1:5000
```

## Acesso demonstrativo

É possível criar um usuário comum pela tela de cadastro.

Os acessos de médico criados pelo sistema utilizam uma senha padrão somente para demonstração acadêmica. Em um ambiente de produção, essa senha deverá ser substituída por uma senha temporária individual, com troca obrigatória no primeiro acesso.

Para transformar um usuário existente em administrador, revise o e-mail configurado em `tornar_admin.py` e execute:

```bash
python tornar_admin.py
```

Utilize somente contas e informações fictícias durante a apresentação.

## Segurança e privacidade

O projeto utiliza:

- Hash de senhas com Bcrypt;
- Proteção CSRF nos formulários web;
- Controle de sessão com Flask-Login;
- Verificação de permissões por tipo de usuário;
- Consultas ao banco realizadas pelo SQLAlchemy;
- Variáveis de ambiente para chaves e tokens externos;
- Validação de extensões e geração de nomes únicos para fotos de perfil.

Por se tratar de um projeto acadêmico, recomenda-se não cadastrar dados pessoais, médicos, financeiros ou credenciais reais. O arquivo `.env` nunca deve ser enviado ao repositório.

## Limitações conhecidas

- O SQLite foi adotado por simplicidade acadêmica;
- A integração de pagamentos depende de configuração externa;
- Os dados cadastrados para apresentação são fictícios;
- O sistema não substitui atendimento médico ou farmacêutico;
- Algumas medidas adicionais seriam necessárias antes de uma utilização em produção.

## Melhorias futuras

- Recuperação e alteração de senha;
- Troca obrigatória da senha no primeiro acesso;
- Confirmação de conta por e-mail;
- Autenticação em dois fatores;
- Testes automatizados;
- Migrações de banco de dados com Flask-Migrate;
- Registro de eventos com logging;
- Validação completa dos webhooks de pagamento;
- Empacotamento da aplicação desktop em um executável;
- Implantação da aplicação web em um servidor;
- Substituição do SQLite por PostgreSQL em um cenário de produção.

## Objetivo acadêmico

O AFGMED permite aplicar, de forma integrada, conhecimentos de:

- Lógica de programação;
- Desenvolvimento orientado a objetos;
- Interfaces gráficas;
- Desenvolvimento web;
- Banco de dados relacional;
- Autenticação e autorização;
- Integração com serviços externos;
- Versionamento de código;
- Organização e documentação de software.

## Autoria

Projeto integrador desenvolvido para fins educacionais.

- Antonio Donizetti;
- Fabricio Ferreira;
- Giovana Matos;
- Turma TI-101;
- Curso Técnico em Informática — SENAC;
- Professores Leonardo Alberto, Nathan Branco e Adriano da Silva;
- Ano 2026.