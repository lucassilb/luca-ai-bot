# Luca.AI BOT — Sistema de Mensageria Inteligente

---

## 📌 1. Nome do projeto

**Luca.AI BOT — Sistema de Mensageria Inteligente**

---

## ❓ 2. Problema

Empresas recebem diariamente uma grande quantidade de mensagens de clientes, muitas delas relacionadas a dúvidas e solicitações simples.

Quando todo o atendimento é realizado manualmente, pode ocorrer demora nas respostas, sobrecarga dos atendentes e dificuldade para manter um histórico organizado das conversas.

O problema abordado pelo projeto é a necessidade de automatizar o atendimento inicial ao cliente, permitindo respostas rápidas e mantendo o histórico das interações.

---

## 💡 3. Solução

O **Luca.AI BOT** é uma API de mensageria inteligente desenvolvida em Python.

O sistema permite que um cliente envie uma mensagem e receba automaticamente uma resposta do bot.

O fluxo principal é:

1. O cliente envia uma mensagem;
2. O sistema identifica o cliente;
3. A mensagem é processada;
4. O Luca.AI BOT gera uma resposta;
5. A mensagem e a resposta são armazenadas no banco de dados;
6. O histórico pode ser consultado posteriormente.

A arquitetura também foi preparada para futuras integrações com serviços de Inteligência Artificial e plataformas de mensageria, como o WhatsApp.

---

## 👥 4. Integrantes


| 568585 | Lucas Silvério Bomtempo |
| 569268 | Caio Apolinario |
| 570557 | Lucas Herrero |
| 570110 | Arthur Lins |

---

## 🛠️ 5. Tecnologias

As principais tecnologias utilizadas no projeto são:

- **Python** — linguagem principal do backend
- **FastAPI** — desenvolvimento da API REST
- **SQLAlchemy** — comunicação com o banco de dados
- **SQLite** — banco de dados utilizado no projeto
- **Pydantic** — validação dos dados recebidos pela API
- **Uvicorn** — servidor utilizado para executar a aplicação
- **Swagger / OpenAPI** — documentação da API
- **Git e GitHub** — versionamento e armazenamento do projeto

---

## 🏗️ 6. Arquitetura

O projeto utiliza uma organização baseada na separação de responsabilidades.


Luca.AI BOT
│
├── main.py
│   └── Inicialização da aplicação e registro dos routers
│
├── routers/
│   ├── clientes.py
│   │   └── Endpoints relacionados aos clientes
│   │
│   └── mensagens.py
│       └── Endpoints relacionados às mensagens
│
├── models.py
│   └── Modelos das entidades do banco de dados
│
├── schemas.py
│   └── Validação dos dados recebidos pela API
│
├── database.py
│   └── Configuração e conexão com o banco de dados
│
├── luca_bot.py
│   └── Motor responsável pela geração das respostas
│
└── requirements.txt
    └── Dependências do projeto



---

## 🗄️ 7. Banco de dados

O projeto utiliza o SQLite para armazenamento persistente dos dados.

### Entidade Cliente

A tabela `clientes` possui os seguintes campos:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| Id | Integer | Identificador único do cliente |
| Nome | String | Nome do cliente |
| Telefone | String | Telefone do cliente |
| Email | String | E-mail do cliente |

### Entidade Mensagem

A tabela `mensagens` possui os seguintes campos:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| Id | Integer | Identificador único da mensagem |
| Cliente_id | Integer | Identificador do cliente relacionado |
| Texto | String | Texto enviado pelo cliente |
| Resposta | String | Resposta gerada pelo Luca.AI BOT |
| Data_hora | DateTime | Data e horário da mensagem |

---

## 🔗 8. Endpoints

A API do Luca.AI BOT possui endpoints responsáveis pelo gerenciamento dos clientes e das mensagens.

### Clientes

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/clientes` | Cadastrar um novo cliente |
| GET | `/clientes` | Consultar todos os clientes |
| GET | `/clientes/{cliente_id}` | Buscar um cliente específico por ID |
| PUT | `/clientes/{cliente_id}` | Atualizar os dados de um cliente |
| DELETE | `/clientes/{cliente_id}` | Excluir um cliente |
| GET | `/clientes/{cliente_id}/mensagens` | Consultar histórico de mensagens do cliente |

### Mensagens

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/mensagens` | Enviar uma mensagem e receber resposta automática |
| GET | `/mensagens` | Consultar todas as mensagens |
| GET | `/mensagens/{mensagem_id}` | Consultar uma mensagem específica por ID |
| DELETE | `/mensagens/{mensagem_id}` | Excluir uma mensagem |

### Status

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Verificar se o sistema está funcionando |

### Códigos HTTP utilizados

| Código | Descrição |
|--------|-----------|
| `200 OK` | Operação realizada com sucesso |
| `201 Created` | Recurso criado com sucesso |
| `204 No Content` | Exclusão realizada com sucesso |
| `404 Not Found` | Cliente ou mensagem não encontrado |
| `409 Conflict` | Conflito (ex: telefone já cadastrado) |

---

## 📄 9. Swagger / OpenAPI

A API possui documentação automática através do Swagger UI, disponibilizado pelo FastAPI. Essa documentação permite visualizar todos os endpoints disponíveis, seus respectivos métodos HTTP, parâmetros, dados necessários nas requisições, possíveis respostas e códigos HTTP. Além disso, o Swagger permite testar diretamente as funcionalidades da API pelo navegador, incluindo o cadastro e gerenciamento de clientes e o envio e consulta de mensagens.

A documentação pode ser acessada através do endereço `http://127.0.0.1:8000/docs` após iniciar o servidor da aplicação. A API também disponibiliza a especificação OpenAPI no endereço `http://127.0.0.1:8000/openapi.json`.

---

## 🚀 10. Como executar o projeto

Para executar o Luca.AI BOT localmente, é necessário ter o Python 3.x instalado na máquina.

### Passo a passo

1.Clone o repositório

git clone <url-do-repositorio>
cd Luca.AI-BOT

2.Crie e ative o ambiente virtual

Windows:
python -m venv .venv
.venv\Scripts\activate

Linux/Mac:
python3 -m venv .venv
source .venv/bin/activate

3.Instale as dependências

pip install -r requirements.txt

4.Execute a aplicação

uvicorn main:app --reload

5.Acesse a API

API: http://127.0.0.1:8000
Documentação Swagger: http://127.0.0.1:8000/docs

Observações

O banco de dados SQLite é criado automaticamente quando a aplicação é executada pela primeira vez, não sendo necessário realizar uma configuração manual.

O servidor será iniciado localmente com recarregamento automático (--reload), ideal para desenvolvimento.
