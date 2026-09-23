"""Integração com LLM para atendimento e relatório operacional.

A LLM entra no fluxo real do bot: classifica a mensagem do cliente e
gera a resposta usada na conversa. Sem chave, o sistema cai nas regras
do CP1. Nada de chatbot genérico desconectado do banco.

Variáveis:
  OPENAI_API_KEY   chave do provedor (OpenAI-compatible)
  OPENAI_BASE_URL  default https://api.openai.com/v1
  OPENAI_MODEL     default gpt-4o-mini
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx

from services.classificacao import INTENCOES, Classificacao

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
TIMEOUT_SECONDS = 20.0

_SYSTEM_ATENDIMENTO = """Você é o Luca.AI BOT, assistente de atendimento inicial de uma empresa.
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
Com base nas mensagens classificadas, escreva um relatório curto em português.
Não invente números que não estejam nos dados. Não use dados pessoais (nome, telefone, e-mail) no texto.
Devolva SOMENTE um JSON com:
resumo (string, 3 a 6 frases),
riscos (lista de strings),
recomendacoes (lista de strings, ações concretas para a equipe).
"""


def llm_configurado() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def modelo_atual() -> str:
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def _chat(system: str, user: str, *, temperature: float = 0.2) -> Optional[dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    base = os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    payload = {
        "model": modelo_atual(),
        "temperature": temperature,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
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


def responder_com_llm(texto: str, classificacao: Classificacao) -> Optional[dict[str, Any]]:
    user = (
        f"Classificação preliminar do sistema (regras): {json.dumps(classificacao, ensure_ascii=False)}\n"
        f"Mensagem do cliente: {texto.strip()[:500]}"
    )
    data = _chat(_SYSTEM_ATENDIMENTO, user)
    if not data:
        return None
    resposta = str(data.get("resposta") or "").strip()
    if not resposta:
        return None
    classe = _sanitizar_classe(data, classificacao)
    return {"resposta": resposta[:1000], **classe}


def relatorio_com_llm(contexto: dict[str, Any]) -> Optional[dict[str, Any]]:
    data = _chat(_SYSTEM_RELATORIO, json.dumps(contexto, ensure_ascii=False, default=str), temperature=0.1)
    if not data:
        return None
    resumo = str(data.get("resumo") or "").strip()
    if not resumo:
        return None
    riscos = [str(item).strip() for item in (data.get("riscos") or []) if str(item).strip()]
    recomendacoes = [str(item).strip() for item in (data.get("recomendacoes") or []) if str(item).strip()]
    return {
        "resumo": resumo[:2000],
        "riscos": riscos[:8],
        "recomendacoes": recomendacoes[:8],
    }
