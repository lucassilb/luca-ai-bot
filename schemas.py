from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _somente_digitos(valor: str) -> str:
    return "".join(ch for ch in valor if ch.isdigit())


class ClienteCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    telefone: str = Field(..., min_length=10, max_length=20)
    email: Optional[EmailStr] = None

    @field_validator("nome")
    @classmethod
    def nome_limpo(cls, valor: str) -> str:
        limpo = " ".join(valor.split())
        if len(limpo) < 2:
            raise ValueError("nome deve ter ao menos 2 caracteres")
        return limpo

    @field_validator("telefone")
    @classmethod
    def telefone_valido(cls, valor: str) -> str:
        digitos = _somente_digitos(valor)
        if len(digitos) < 10 or len(digitos) > 13:
            raise ValueError("telefone deve ter entre 10 e 13 dígitos")
        return digitos


class ClienteUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=100)
    telefone: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None

    @field_validator("nome")
    @classmethod
    def nome_limpo(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        limpo = " ".join(valor.split())
        if len(limpo) < 2:
            raise ValueError("nome deve ter ao menos 2 caracteres")
        return limpo

    @field_validator("telefone")
    @classmethod
    def telefone_valido(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        digitos = _somente_digitos(valor)
        if len(digitos) < 10 or len(digitos) > 13:
            raise ValueError("telefone deve ter entre 10 e 13 dígitos")
        return digitos


class ClienteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    telefone: str
    email: Optional[str] = None
    criado_em: Optional[datetime] = None


class MensagemCreate(BaseModel):
    cliente_id: int = Field(..., gt=0)
    texto: str = Field(..., min_length=1, max_length=500)

    @field_validator("texto")
    @classmethod
    def texto_limpo(cls, valor: str) -> str:
        limpo = valor.strip()
        if not limpo:
            raise ValueError("texto não pode ser vazio")
        return limpo


class MensagemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    texto: str
    resposta: str
    data_hora: datetime
    intencao: str
    urgencia: str
    sentimento: str
    origem_resposta: str


class ConversaOut(BaseModel):
    id: int
    cliente: str
    cliente_id: int
    texto: str
    resposta: str
    data_hora: datetime
    intencao: str
    urgencia: str
    sentimento: str
    origem_resposta: str


class PaginatedClientes(BaseModel):
    total: int
    skip: int
    limit: int
    clientes: list[ClienteOut]


class PaginatedMensagens(BaseModel):
    total: int
    skip: int
    limit: int
    mensagens: list[MensagemOut]


class RelatorioRequest(BaseModel):
    cliente_id: Optional[int] = Field(None, gt=0)
    limite: int = Field(20, ge=5, le=100)


class RelatorioOut(BaseModel):
    origem: str
    modelo: str
    total_analisado: int
    resumo: str
    riscos: list[str]
    recomendacoes: list[str]
    intencoes: dict[str, int]
