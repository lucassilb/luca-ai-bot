"""Compatibilidade com o CP1: gera_resposta(texto) continua existindo."""
from services.bot import resposta_por_regras


def gerar_resposta(texto: str) -> str:
    return resposta_por_regras(texto)
