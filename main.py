from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from database import Base, engine
from routers.clientes import router as clientes_router
from routers.dashboard import router as dashboard_router
from routers.mensagens import router as mensagens_router
from routers.relatorios import router as relatorios_router

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


def _ensure_schema() -> None:
    """Cria tabelas novas e adiciona colunas do CP2 em bancos do CP1."""
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "mensagens" not in inspector.get_table_names():
        return
    existentes = {coluna["name"] for coluna in inspector.get_columns("mensagens")}
    alteracoes = {
        "intencao": "ALTER TABLE mensagens ADD COLUMN intencao VARCHAR(40) NOT NULL DEFAULT 'outros'",
        "urgencia": "ALTER TABLE mensagens ADD COLUMN urgencia VARCHAR(20) NOT NULL DEFAULT 'baixa'",
        "sentimento": "ALTER TABLE mensagens ADD COLUMN sentimento VARCHAR(20) NOT NULL DEFAULT 'neutro'",
        "origem_resposta": "ALTER TABLE mensagens ADD COLUMN origem_resposta VARCHAR(20) NOT NULL DEFAULT 'regras'",
    }
    with engine.begin() as conexao:
        for coluna, sql in alteracoes.items():
            if coluna not in existentes:
                conexao.execute(text(sql))
        if "clientes" in inspector.get_table_names():
            clientes_cols = {coluna["name"] for coluna in inspector.get_columns("clientes")}
            if "criado_em" not in clientes_cols:
                conexao.execute(text("ALTER TABLE clientes ADD COLUMN criado_em DATETIME"))


_ensure_schema()

app = FastAPI(
    title="Luca.AI BOT",
    description=(
        "API de mensageria inteligente (CP2). "
        "Classifica intenções, responde com regras ou LLM e expõe dashboard operacional."
    ),
    version="2.0.0",
    contact={"name": "Luca.AI BOT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clientes_router)
app.include_router(mensagens_router)
app.include_router(dashboard_router)
app.include_router(relatorios_router)


@app.exception_handler(HTTPException)
async def erro_http(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return await http_exception_handler(request, exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"ok": False, "erro": str(exc.detail), "status": exc.status_code},
    )


@app.exception_handler(RequestValidationError)
async def erro_validacao(request: Request, exc: RequestValidationError):
    return await request_validation_exception_handler(request, exc)


@app.get("/api/status", tags=["Status"], summary="Saúde da API")
def status():
    return {
        "ok": True,
        "nome": "Luca.AI BOT",
        "versao": "2.0.0",
        "checkpoint": "CP2",
    }


@app.get("/", include_in_schema=False)
def inicio():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        from fastapi.responses import FileResponse

        return FileResponse(index)
    return {"mensagem": "Luca.AI BOT funcionando!", "versao": "2.0.0"}


if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
