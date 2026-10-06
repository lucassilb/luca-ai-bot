# Luca.AI BOT — Sistema de Mensageria Inteligente (CP2)

API FastAPI + SQLite de atendimento inicial, agora com interface, dashboard operacional, classificação de mensagens, testes e LLM opcional.

## Problema

Empresas acumulam mensagens simples (pedido, preço, horário, reclamação) sem fila organizada. O atendimento manual atrasa a primeira resposta e perde o histórico.

## Solução (CP2)

1. O cliente é cadastrado.
2. A mensagem entra na API.
3. O sistema classifica intenção, urgência e sentimento.
4. A resposta sai pelo modelo local (se estiver ativo) ou pelas regras do CP1.
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
| 573213 | Gustavo Santin |

## O que mudou em relação ao CP1

- Backend: validações Pydantic, telefone normalizado, e-mail opcional, PUT parcial, paginação e filtros, erros HTTP.
- Banco: `ForeignKey` + `ON DELETE CASCADE`, índices, colunas `intencao`, `urgencia`, `sentimento`, `origem_resposta`, `criado_em`. Bancos antigos do CP1 são migrados na subida, inclusive a chave estrangeira.
- Frontend em `/` e `/app`: cadastro e edição de clientes, conversa, dashboard e relatório.
- Dashboard em `GET /dashboard` (indicadores, barras de intenção, alertas, histórico).
- LLM local em `services/llm.py` (Ollama + Qwen2.5 3B). Sem Ollama, o bot continua nas regras.
- Testes em `tests/` (pytest + TestClient).
- Swagger em `/docs`.

## Arquitetura

```text
frontend/index.html          UI (dashboard, atendimento, clientes, relatório)
main.py / migrations.py      FastAPI, migração CP1→CP2, arquivos estáticos
routers/clientes.py          CRUD + busca + histórico paginado
routers/mensagens.py         envio + listagem filtrada
routers/dashboard.py         indicadores reais
routers/relatorios.py        relatório LLM ou consolidado local
services/classificacao.py    regras de intenção/urgência/sentimento
services/bot.py              orquestra regras + LLM
services/llm.py              POST local /api/chat (JSON)
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
| Serviço | Ollama local, `POST http://127.0.0.1:11434/api/chat` |
| Modelo padrão | `qwen2.5:3b`, pesos gratuitos baixados pelo Ollama |
| Finalidade | (1) responder e rotular a mensagem; (2) redigir relatório operacional |
| Dados enviados | mensagem do cliente + classificação preliminar **somente ao servidor local**; no relatório, apenas contagens e rótulos, sem textos, nomes ou contatos |
| Resposta obtida | JSON com `resposta`, `intencao`, `urgencia`, `sentimento`; relatório com `resumo`, `riscos`, `recomendacoes` |
| Uso na app | grava resposta e rótulos em `mensagens`; dashboard e relatório leem os dados gravados |
| Sem Ollama/modelo | fallback para `services/classificacao.py` + frases do CP1; `origem_resposta` indica `regras` ou `llm` |
| Limites | timeout 90s, saída JSON validada, rótulos fora do conjunto aceito são descartados; a LLM pode errar ou inventar detalhes |
| Segurança | conexão restrita ao próprio computador; prompt proíbe pedir CPF/senha/cartão; relatório não envia texto original nem dados cadastrais |

Não há configuração de API comercial nem chave de provedor pago. `OLLAMA_BASE_URL` aceita somente `http://localhost`, `http://127.0.0.1` ou `http://[::1]`. O modelo deve estar baixado localmente; nomes com `cloud` são rejeitados.

## Como executar

Linux/macOS:

```bash
git clone https://github.com/lucassilb/luca-ai-bot.git
cd luca-ai-bot
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m uvicorn main:app --reload
```

Windows PowerShell:

```powershell
git clone https://github.com/lucassilb/luca-ai-bot.git
Set-Location luca-ai-bot
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Para usar a LLM gratuita, [instale o Ollama](https://docs.ollama.com/windows) e baixe o modelo com `ollama pull qwen2.5:3b`. Copie `.env.example` para `.env` antes de iniciar a API (`Copy-Item .env.example .env` no PowerShell ou `cp .env.example .env` no Linux/macOS). O Ollama precisa estar servindo em `127.0.0.1:11434`; no Windows costuma iniciar em segundo plano, ou use `ollama serve`. Defina `OLLAMA_NO_CLOUD=1` no ambiente **do servidor Ollama** e reinicie-o para desativar todos os recursos de nuvem. Para testar o dashboard com dados de exemplo, execute `.venv\Scripts\python.exe -m scripts.seed` no Windows ou `./.venv/bin/python -m scripts.seed` no Linux/macOS. O seed é opcional.

- App: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Dashboard API: http://127.0.0.1:8000/dashboard

O SQLite `luca_bot.db` nasce sozinho. Se o arquivo for do CP1, a primeira subida adiciona as colunas, recria `mensagens` com chave estrangeira e índices e guarda eventuais mensagens órfãs em `mensagens_orfas_cp1` para conferência.

## Testes

```bash
./.venv/bin/python -m pytest -q
```

No Windows, use `.\.venv\Scripts\python.exe -m pytest -q`. Cobertura: classificação, CRUD e edição de cliente, envio de mensagem, filtros, dashboard, relatório, protocolo da LLM local e migração de banco CP1.

## Otimizações da API (CP2)

- Listagens com `skip`/`limit` (teto 100) — o frontend não baixa o banco inteiro.
- Filtros `q`, `intencao`, `urgencia`, `cliente_id` no SQL, não em memória.
- Índices nas colunas filtradas.
- PUT parcial: não obriga reenviar telefone/e-mail.
- Telefone gravado só com dígitos: uma busca encontra `(11) 98888-7771` e `11988887771`.
- Dashboard em um GET: totais + agrupamentos, em vez de N requests por gráfico.
