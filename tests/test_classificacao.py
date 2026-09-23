from luca_bot import gerar_resposta
from services.bot import gerar_resposta_completa
from services.classificacao import classificar_mensagem


def test_saudacao_e_pedido():
    assert classificar_mensagem("Oi, tudo bem?")["intencao"] == "saudacao"
    assert classificar_mensagem("Cadê o rastreio do meu pedido?")["intencao"] == "pedido"


def test_reclamacao_urgente():
    classe = classificar_mensagem("Meu pedido não chegou, isso é urgente")
    assert classe["intencao"] == "reclamacao"
    assert classe["urgencia"] == "alta"
    assert classe["sentimento"] == "negativo"


def test_compatibilidade_cp1_gerar_resposta():
    texto = gerar_resposta("olá")
    assert "Luca.AI BOT" in texto


def test_resposta_completa_sem_llm_usa_regras(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    resultado = gerar_resposta_completa("quero falar com um atendente")
    assert resultado["origem_resposta"] == "regras"
    assert resultado["intencao"] == "atendente"
    assert "atendente" in resultado["resposta"].lower()
