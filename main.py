from fastapi import FastAPI

from database import Base, engine

from routers.clientes import router as clientes_router
from routers.mensagens import router as mensagens_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Luca.AI BOT",
    description="API de mensageria inteligente",
    version="1.0.0"
)


app.include_router(clientes_router)
app.include_router(mensagens_router)


@app.get("/")
def inicio():
    return {
        "mensagem": "Luca.AI BOT funcionando!"
    }