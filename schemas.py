from pydantic import BaseModel, EmailStr


class ClienteCreate(BaseModel):
    nome: str
    telefone: str
    email: EmailStr


class MensagemCreate(BaseModel):
    cliente_id: int
    texto: str