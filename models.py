from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    telefone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(150), nullable=True, index=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    mensagens = relationship(
        "Mensagem",
        back_populates="cliente",
        cascade="all, delete-orphan",
        order_by="Mensagem.data_hora",
    )


class Mensagem(Base):
    __tablename__ = "mensagens"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(
        Integer,
        ForeignKey("clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    texto = Column(String(500), nullable=False)
    resposta = Column(Text, nullable=False)
    data_hora = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    intencao = Column(String(40), nullable=False, default="outros", index=True)
    urgencia = Column(String(20), nullable=False, default="baixa", index=True)
    sentimento = Column(String(20), nullable=False, default="neutro")
    origem_resposta = Column(String(20), nullable=False, default="regras")

    cliente = relationship("Cliente", back_populates="mensagens")
