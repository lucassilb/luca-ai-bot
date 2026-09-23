"""Motor de resposta do Luca.AI BOT.

Primeiro tenta a LLM (quando configurada) com o contexto da classificação.
Se a LLM não estiver disponível, usa as regras do CP1 — o atendimento
nunca fica mudo.
"""
from __future__ import annotations

from services.classificacao import Classificacao, classificar_mensagem
from services.llm import responder_com_llm


RESPOSTAS_PADRAO = {
    "saudacao": "Olá! Sou o Luca.AI BOT. Como posso ajudar você?",
    "pedido": "Claro! Posso ajudar você com informações sobre seu pedido.",
    "preco": "Posso ajudar você com informações sobre preços.",
    "horario": "Nosso atendimento funciona de segunda a sexta, das 08h às 18h.",
    "reclamacao": "Entendi. Pode me explicar melhor o problema para que eu possa ajudar?",
    "atendente": "Claro! Vou encaminhar sua solicitação para um atendente.",
    "agradecimento": "Por nada! Estou à disposição para ajudar.",
    "outros": "Entendi sua mensagem. Pode me explicar um pouco mais para que eu possa ajudar?",
}


def resposta_por_regras(texto: str, classificacao: Classificacao | None = None) -> str:
    classe = classificacao or classificar_mensagem(texto)
    return RESPOSTAS_PADRAO.get(classe["intencao"], RESPOSTAS_PADRAO["outros"])


def gerar_resposta_completa(texto: str) -> dict:
    classificacao = classificar_mensagem(texto)
    llm = responder_com_llm(texto, classificacao)
    if llm:
        return {
            "resposta": llm["resposta"],
            "intencao": llm.get("intencao") or classificacao["intencao"],
            "urgencia": llm.get("urgencia") or classificacao["urgencia"],
            "sentimento": llm.get("sentimento") or classificacao["sentimento"],
            "origem_resposta": "llm",
        }
    return {
        "resposta": resposta_por_regras(texto, classificacao),
        **classificacao,
        "origem_resposta": "regras",
    }
