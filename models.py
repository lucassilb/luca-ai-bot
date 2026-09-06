from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    telefone = Column(String(20), unique=True, nullable=False)
    email = Column(String(150), nullable=True)


class Mensagem(Base):
    __tablename__ = "mensagens"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, nullable=False)
    texto = Column(String(500), nullable=False)
    resposta = Column(String(1000), nullable=False)
    data_hora = Column(DateTime, default=datetime.utcnow)