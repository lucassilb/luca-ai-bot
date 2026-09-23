"""Regras de negócio para classificar a mensagem do cliente.

A classificação alimenta o dashboard (volume por intenção, alertas de
reclamação) e o relatório de atendimento. A LLM pode refinar esses
rótulos; se ela falhar, estas regras continuam valendo.
"""
from __future__ import annotations

import unicodedata
from typing import TypedDict


class Classificacao(TypedDict):
    intencao: str
    urgencia: str
    sentimento: str


INTENCOES = (
    "saudacao",
    "pedido",
    "preco",
    "horario",
    "reclamacao",
    "atendente",
    "agradecimento",
    "outros",
)


def _normalizar(texto: str) -> str:
    valor = unicodedata.normalize("NFKD", texto or "")
    valor = "".join(ch for ch in valor if not unicodedata.combining(ch))
    return valor.lower()


def classificar_mensagem(texto: str) -> Classificacao:
    t = _normalizar(texto)

    if any(p in t for p in ("obrigado", "obrigada", "valeu", "agradec")):
        return {"intencao": "agradecimento", "urgencia": "baixa", "sentimento": "positivo"}

    if any(p in t for p in ("atendente", "humano", "pessoa real", "falar com alguem")):
        return {"intencao": "atendente", "urgencia": "alta", "sentimento": "neutro"}

    if any(
        p in t
        for p in (
            "problema",
            "erro",
            "reclam",
            "nao funciona",
            "nao chegou",
            "ninguem responde",
            "atras",
            "pessimo",
            "horrivel",
            "raiva",
        )
    ):
        urgencia = "alta" if any(p in t for p in ("urgente", "agora", "hoje", "nao chegou")) else "media"
        return {"intencao": "reclamacao", "urgencia": urgencia, "sentimento": "negativo"}

    if any(p in t for p in ("pedido", "rastre", "entrega", "encomenda", "status do")):
        return {"intencao": "pedido", "urgencia": "media", "sentimento": "neutro"}

    if any(p in t for p in ("preco", "preço", "valor", "quanto custa", "orcamento", "orçamento")):
        return {"intencao": "preco", "urgencia": "baixa", "sentimento": "neutro"}

    if any(p in t for p in ("horario", "horário", "funcionam", "abre", "expediente")):
        return {"intencao": "horario", "urgencia": "baixa", "sentimento": "neutro"}

    if any(p in t for p in ("ola", "olá", "oi", "bom dia", "boa tarde", "boa noite")):
        return {"intencao": "saudacao", "urgencia": "baixa", "sentimento": "positivo"}

    return {"intencao": "outros", "urgencia": "baixa", "sentimento": "neutro"}
