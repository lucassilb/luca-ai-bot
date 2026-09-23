# Luca.AI BOT — Sistema de Mensageria Inteligente (CP2)

API FastAPI + SQLite de atendimento inicial, agora com interface, dashboard operacional, classificação de mensagens, testes e LLM opcional.

## Problema

Empresas acumulam mensagens simples (pedido, preço, horário, reclamação) sem fila organizada. O atendimento manual atrasa a primeira resposta e perde o histórico.

## Solução (CP2)

1. O cliente é cadastrado.
2. A mensagem entra na API.
3. O sistema classifica intenção, urgência e sentimento.
4. A resposta sai por LLM (se houver chave) ou pelas regras do CP1.
5. Tudo grava no SQLite, com FK cliente → mensagens.
6. O dashboard e o relatório leem esses dados reais.

A LLM não é um chat genérico: ela classifica e responde *a mensagem do cliente* e redige o relatório operacional a partir do histórico classificado.

## Integrantes

| RM | Nome |
|---|---|
| 568585 | Lucas Silvério Bomtempo |
| 569268 | Caio Apolinario |
| 570557 | Lucas Herrero |
| 570110 | Arthur Lins |

## O que mudou em relação ao CP1

- Backend: validações Pydantic, telefone normalizado, e-mail opcional, PUT parcial, paginação e filtros, erros `{ok, erro, status}`.
- Banco: `ForeignKey` + `ON DELETE CASCADE`, índices, colunas `intencao`, `urgencia`, `sentimento`, `origem_resposta`, `criado_em`. Bancos antigos do CP1 são migrados na subida.
- Frontend em `/` e `/app`: cadastro, conversa, dashboard e relatório.
- Dashboard em `GET /dashboard` (indicadores, barras de intenção, alertas, histórico).
- LLM em `services/llm.py` (OpenAI-compatible). Sem `OPENAI_API_KEY` o bot continua nas regras.
- Testes em `tests/` (pytest + TestClient).
- Swagger em `/docs`.

## Arquitetura

```text
frontend/index.html          UI (dashboard, atendimento, clientes, relatório)
main.py                      FastAPI, CORS, schema CP2, arquivos estáticos
routers/clientes.py          CRUD + busca + histórico paginado
routers/mensagens.py         envio + listagem filtrada
routers/dashboard.py         indicadores reais
routers/relatorios.py        relatório LLM ou consolidado local
services/classificacao.py    regras de intenção/urgência/sentimento
services/bot.py              orquestra regras + LLM
services/llm.py              POST /chat/completions (JSON)
models.py / schemas.py / database.py
tests/                       unitário + integração de endpoints
```

## Banco (revisão CP2)

`clientes (1) ──< mensagens (N)`

| Tabela | Decisão |
|---|---|
| `clientes.telefone` unique + só dígitos | evita duplicidade do mesmo WhatsApp/celular |
| `mensagens.cliente_id` FK CASCADE | histórico some com o cliente; integridade referencial |
| `intencao` / `urgencia` / `sentimento` | dashboard e relatório sem reler o texto toda vez |
| `origem_resposta` | `regras` ou `llm` — dá para auditar o que a IA gerou |
| índices em telefone, cliente_id, data_hora, intencao | listagens e filtros do dashboard |

SQLite permanece no CP2 (um arquivo, zero ops). Relacionamento está na 3FN para o domínio atual: cliente e mensagem, sem repetir nome/telefone em cada linha de conversa.

## API

| Método | Rota | Notas |
|---|---|---|
| GET | `/api/status` | saúde |
| GET | `/docs` | Swagger |
| POST | `/clientes` | 201 / 409 telefone |
| GET | `/clientes?q=&skip=&limit=` | paginado |
| GET | `/clientes/{id}` | |
| PUT | `/clientes/{id}` | parcial |
| DELETE | `/clientes/{id}` | 204, cascade nas mensagens |
| GET | `/clientes/{id}/mensagens` | paginado |
| POST | `/mensagens` | classifica + responde |
| GET | `/mensagens?cliente_id=&intencao=&urgencia=&skip=&limit=` | |
| GET | `/dashboard` | indicadores |
| POST | `/relatorios` | LLM ou regras |

Códigos: `200`, `201`, `204`, `404`, `409`, `422`.

## LLM

| Item | Valor |
|---|---|
| Serviço | OpenAI-compatible `POST /chat/completions` |
| Default | `gpt-4o-mini` em `https://api.openai.com/v1` |
| Finalidade | (1) responder e rotular a mensagem; (2) redigir relatório operacional |
| Dados enviados | texto da mensagem + classificação preliminar; no relatório, totais e amostra **sem** nome/telefone/e-mail |
| Uso na app | grava `resposta` + rótulos na tabela `mensagens`; o dashboard lê isso |
| Sem chave | fallback para `services/classificacao.py` + frases do CP1 |
| Limites | timeout 20s, JSON obrigatório, rótulos fora do enum são descartados |
| Segurança | prompt proíbe pedir CPF/senha/cartão; relatório não inclui PII |

## Como executar

```bash
git clone https://github.com/lucassilb/luca-ai-bot.git
cd luca-ai-bot
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # opcional: preencha OPENAI_API_KEY
python scripts/seed.py      # opcional: dados de demo para o dashboard
uvicorn main:app --reload
```

- App: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Dashboard API: http://127.0.0.1:8000/dashboard

O SQLite `luca_bot.db` nasce sozinho. Se o arquivo for do CP1, as colunas novas são adicionadas na primeira subida.

## Testes

```bash
pytest -q
```

Cobertura inicial: classificação, CRUD de cliente, conflito de telefone, envio de mensagem, paginação/filtro, dashboard e relatório com dados reais (sem LLM).

## Otimizações da API (CP2)

- Listagens com `skip`/`limit` (teto 100) — o frontend não baixa o banco inteiro.
- Filtros `q`, `intencao`, `urgencia`, `cliente_id` no SQL, não em memória.
- Índices nas colunas filtradas.
- PUT parcial: não obriga reenviar telefone/e-mail.
- Telefone gravado só com dígitos: uma busca encontra `(11) 98888-7771` e `11988887771`.
- Dashboard em um GET: totais + agrupamentos, em vez de N requests por gráfico.

## Trello / Notion

Quadro sugerido (atualizar o link real do grupo na apresentação):

1. CP1 entregue (backend mensagens/clientes)
2. CP2 backend (validações, FK, paginação)
3. Frontend + dashboard
4. LLM de triagem e relatório
5. Testes pytest
6. README / Swagger / seed

## Apresentação

Roteiro curto: problema → fluxo CP1 ainda vivo → tela de atendimento → dashboard com seed → filtro/paginação no Swagger → `pytest -q` → ligar/desligar `OPENAI_API_KEY` e mostrar `origem_resposta`.
