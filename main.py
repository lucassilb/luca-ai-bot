from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from database import engine
from migrations import ensure_schema
from routers.clientes import router as clientes_router
from routers.dashboard import router as dashboard_router
from routers.mensagens import router as mensagens_router
from routers.relatorios import router as relatorios_router

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


ensure_schema(engine)

app = FastAPI(
    title="Luca.AI BOT",
    description=(
        "API de mensageria inteligente (CP2). "
        "Classifica intenções, responde com regras ou LLM e expõe dashboard operacional."
    ),
    version="2.0.0",
    contact={"name": "Luca.AI BOT"},
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
