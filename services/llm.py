"""LLM local para classificar atendimentos e redigir relatórios.

Usa somente a API local do Ollama. Sem servidor/modelo disponível, as regras
do CP1 continuam atendendo normalmente; nenhuma API paga é chamada.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

from services.classificacao import INTENCOES, Classificacao


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:3b"
TIMEOUT_SECONDS = 90.0

_SYSTEM_ATENDIMENTO = """Você é o Luca.AI BOT, assistente de atendimento inicial.
Responda em português do Brasil, curto (2 a 4 frases), sem inventar pedido, preço ou prazo.
Se o cliente pedir atendente humano, confirme o encaminhamento.
Se for reclamação, reconheça o problema e peça o dado que falta (número do pedido, data).
Nunca peça CPF, senha, cartão ou dado bancário.
Devolva SOMENTE um JSON com as chaves:
resposta, intencao, urgencia, sentimento.
intencao ∈ {saudacao, pedido, preco, horario, reclamacao, atendente, agradecimento, outros}
urgencia ∈ {baixa, media, alta}
sentimento ∈ {positivo, neutro, negativo}
"""

_SYSTEM_RELATORIO = """Você é analista de operação de um bot de atendimento.
Com base nas contagens e classificações, escreva um relatório curto em português.
Não invente números que não estejam nos dados. Não use dados pessoais no texto.
Devolva SOMENTE um JSON com:
resumo (string, 3 a 6 frases),
riscos (lista de strings),
recomendacoes (lista de strings, ações concretas para a equipe).
"""

_ATENDIMENTO_SCHEMA = {
    "type": "object",
    "properties": {
        "resposta": {"type": "string"},
        "intencao": {"type": "string", "enum": list(INTENCOES)},
        "urgencia": {"type": "string", "enum": ["baixa", "media", "alta"]},
        "sentimento": {"type": "string", "enum": ["positivo", "neutro", "negativo"]},
    },
    "required": ["resposta", "intencao", "urgencia", "sentimento"],
}

_RELATORIO_SCHEMA = {
    "type": "object",
    "properties": {
        "resumo": {"type": "string"},
        "riscos": {"type": "array", "items": {"type": "string"}},
        "recomendacoes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["resumo", "riscos", "recomendacoes"],
}


def _base_local() -> str | None:
    base = os.getenv("OLLAMA_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        return None
    if parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        return None
    return base


def llm_configurado() -> bool:
    return (
        os.getenv("OLLAMA_ENABLED", "").strip().lower() in {"1", "true", "yes"}
        and _base_local() is not None
        and "cloud" not in modelo_atual().lower()
    )


def modelo_atual() -> str:
    return os.getenv("OLLAMA_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def llm_disponivel() -> bool:
    if not llm_configurado():
        return False
    try:
        with httpx.Client(timeout=2.0, trust_env=False) as client:
            response = client.get(f"{_base_local()}/api/tags")
            response.raise_for_status()
            return any(model.get("name") == modelo_atual() for model in response.json().get("models", []))
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return False


def _chat(system: str, user: str, schema: dict[str, Any], *, temperature: float = 0.2) -> dict[str, Any] | None:
    if not llm_disponivel():
        return None
    payload = {
        "model": modelo_atual(),
        "stream": False,
        "format": schema,
        "options": {"temperature": temperature},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS, trust_env=False) as client:
            response = client.post(f"{_base_local()}/api/chat", json=payload)
            response.raise_for_status()
            data = json.loads(response.json()["message"]["content"])
            return data if isinstance(data, dict) else None
    except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _sanitizar_classe(data: dict[str, Any], fallback: Classificacao) -> Classificacao:
    intencao = str(data.get("intencao") or fallback["intencao"]).strip().lower()
    urgencia = str(data.get("urgencia") or fallback["urgencia"]).strip().lower()
    sentimento = str(data.get("sentimento") or fallback["sentimento"]).strip().lower()
    if intencao not in INTENCOES:
        intencao = fallback["intencao"]
    if urgencia not in {"baixa", "media", "alta"}:
        urgencia = fallback["urgencia"]
    if sentimento not in {"positivo", "neutro", "negativo"}:
        sentimento = fallback["sentimento"]
    return {"intencao": intencao, "urgencia": urgencia, "sentimento": sentimento}


def responder_com_llm(texto: str, classificacao: Classificacao) -> dict[str, Any] | None:
    user = (
        f"Mensagem do cliente: {texto.strip()[:500]}\n"
        f"Classificação preliminar: {json.dumps(classificacao, ensure_ascii=False)}\n"
        "Escreva uma resposta útil no campo resposta e preencha os três rótulos. "
        "Não copie apenas a classificação preliminar."
    )
    data = _chat(_SYSTEM_ATENDIMENTO, user, _ATENDIMENTO_SCHEMA)
    if not data:
        return None
    resposta = data.get("resposta")
    if not isinstance(resposta, str) or not resposta.strip():
        return None
    classe = _sanitizar_classe(data, classificacao)
    return {"resposta": resposta.strip()[:1000], **classe}


def relatorio_com_llm(contexto: dict[str, Any]) -> dict[str, Any] | None:
    data = _chat(_SYSTEM_RELATORIO, json.dumps(contexto, ensure_ascii=False), _RELATORIO_SCHEMA, temperature=0.1)
    if not data:
        return None
    resumo = data.get("resumo")
    riscos = data.get("riscos")
    recomendacoes = data.get("recomendacoes")
    if not isinstance(resumo, str) or not resumo.strip():
        return None
    if not isinstance(riscos, list) or not isinstance(recomendacoes, list):
        return None
    return {
        "resumo": resumo.strip()[:2000],
        "riscos": [item.strip()[:300] for item in riscos[:8] if isinstance(item, str) and item.strip()],
        "recomendacoes": [item.strip()[:300] for item in recomendacoes[:8] if isinstance(item, str) and item.strip()],
    }
