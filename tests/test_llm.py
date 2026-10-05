import json

from services import llm


def test_somente_ollama_local_e_json_validado(monkeypatch):
    monkeypatch.setenv("OLLAMA_ENABLED", "1")
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://example.com/v1")
    assert llm.llm_configurado() is False

    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    posts = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": json.dumps({
                "resposta": "Vamos verificar seu pedido.",
                "intencao": "pedido", "urgencia": "invalida", "sentimento": "neutro",
            })}}

    class Client:
        def __init__(self, **kwargs):
            assert kwargs["trust_env"] is False

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def post(self, url, json):
            posts.append((url, json))
            return Response()

        def get(self, url):
            assert url == "http://127.0.0.1:11434/api/tags"
            class TagsResponse:
                def raise_for_status(self):
                    pass

                def json(self):
                    return {"models": [{"name": "qwen2.5:3b"}]}

            return TagsResponse()

    monkeypatch.setattr(llm.httpx, "Client", Client)
    fallback = {"intencao": "reclamacao", "urgencia": "alta", "sentimento": "negativo"}
    resultado = llm.responder_com_llm("Meu pedido atrasou", fallback)
    assert resultado["resposta"] == "Vamos verificar seu pedido."
    assert resultado["urgencia"] == "alta"
    assert posts[0][0] == "http://127.0.0.1:11434/api/chat"
    assert posts[0][1]["model"] == "qwen2.5:3b"
    assert "resposta" in posts[0][1]["format"]["required"]
    assert posts[0][1]["stream"] is False


def test_relatorio_nao_envia_texto_pessoal_ao_modelo(client, monkeypatch):
    cliente = client.post("/clientes", json={
        "nome": "Ana", "telefone": "11988887771", "email": "ana@empresa.com",
    }).json()["cliente"]
    client.post("/mensagens", json={
        "cliente_id": cliente["id"], "texto": "meu email é segredo@example.com; pedido atrasou",
    })

    enviado = []
    monkeypatch.setenv("OLLAMA_ENABLED", "1")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

    def gerar(system, user, *_args, **_kwargs):
        enviado.append(user)
        return {"resumo": "Uma reclamação.", "riscos": [], "recomendacoes": ["Responder."]}

    monkeypatch.setattr(llm, "_chat", gerar)
    resposta = client.post("/relatorios", json={"limite": 20})
    assert resposta.status_code == 200
    assert resposta.json()["origem"] == "llm"
    assert "segredo@example.com" not in enviado[0]
    assert "ana@empresa.com" not in enviado[0]
    assert "11988887771" not in enviado[0]


def test_resposta_llm_e_persistida_no_historico(client, monkeypatch):
    cliente = client.post("/clientes", json={
        "nome": "Lia", "telefone": "11988887772",
    }).json()["cliente"]
    monkeypatch.setenv("OLLAMA_ENABLED", "1")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setattr(llm, "_chat", lambda *_args, **_kwargs: {
        "resposta": "Vou verificar o atraso do seu pedido.",
        "intencao": "reclamacao", "urgencia": "alta", "sentimento": "negativo",
    })

    enviada = client.post("/mensagens", json={
        "cliente_id": cliente["id"], "texto": "meu pedido atrasou",
    })
    assert enviada.status_code == 201
    assert enviada.json()["conversa"]["origem_resposta"] == "llm"

    historico = client.get(f"/clientes/{cliente['id']}/mensagens").json()
    assert historico["total"] == 1
    assert historico["mensagens"][0]["resposta"] == "Vou verificar o atraso do seu pedido."
    assert historico["mensagens"][0]["origem_resposta"] == "llm"
