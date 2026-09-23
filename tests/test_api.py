def test_status(client):
    resposta = client.get("/api/status")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["ok"] is True
    assert corpo["checkpoint"] == "CP2"


def test_criar_cliente_e_validar_telefone(client):
    ok = client.post(
        "/clientes",
        json={"nome": "Ana Souza", "telefone": "(11) 98888-7771", "email": "ana@empresa.com"},
    )
    assert ok.status_code == 201
    cliente = ok.json()["cliente"]
    assert cliente["telefone"] == "11988887771"

    duplicado = client.post(
        "/clientes",
        json={"nome": "Outra", "telefone": "11988887771", "email": "outra@empresa.com"},
    )
    assert duplicado.status_code == 409
    assert duplicado.json()["erro"]

    invalido = client.post("/clientes", json={"nome": "X", "telefone": "123"})
    assert invalido.status_code == 422


def test_fluxo_mensagem_classifica_e_grava(client):
    cliente = client.post(
        "/clientes",
        json={"nome": "Bruno Lima", "telefone": "11988887772", "email": "bruno@loja.com"},
    ).json()["cliente"]

    mensagem = client.post(
        "/mensagens",
        json={"cliente_id": cliente["id"], "texto": "meu pedido atrasou e ninguém responde"},
    )
    assert mensagem.status_code == 201
    conversa = mensagem.json()["conversa"]
    assert conversa["intencao"] == "reclamacao"
    assert conversa["origem_resposta"] == "regras"
    assert conversa["cliente_id"] == cliente["id"]

    inexistente = client.post("/mensagens", json={"cliente_id": 999, "texto": "oi"})
    assert inexistente.status_code == 404


def test_listas_paginadas_e_filtro(client):
    primeiro = client.post(
        "/clientes",
        json={"nome": "Carla Dias", "telefone": "11988887773", "email": "carla@mail.com"},
    ).json()["cliente"]
    client.post("/clientes", json={"nome": "Diego Alves", "telefone": "11988887774"})
    client.post("/mensagens", json={"cliente_id": primeiro["id"], "texto": "oi"})
    client.post("/mensagens", json={"cliente_id": primeiro["id"], "texto": "qual o preço?"})

    clientes = client.get("/clientes", params={"q": "Carla", "limit": 10})
    assert clientes.status_code == 200
    assert clientes.json()["total"] == 1

    mensagens = client.get("/mensagens", params={"intencao": "preco"})
    assert mensagens.status_code == 200
    assert mensagens.json()["total"] >= 1
    assert all(item["intencao"] == "preco" for item in mensagens.json()["mensagens"])


def test_dashboard_e_relatorio_usam_dados_reais(client):
    cliente = client.post(
        "/clientes",
        json={"nome": "Eva Nunes", "telefone": "11988887775", "email": "eva@mail.com"},
    ).json()["cliente"]
    client.post("/mensagens", json={"cliente_id": cliente["id"], "texto": "quero um atendente"})
    client.post("/mensagens", json={"cliente_id": cliente["id"], "texto": "pedido 12 não chegou, urgente"})

    painel = client.get("/dashboard")
    assert painel.status_code == 200
    dados = painel.json()
    assert dados["indicadores"]["clientes"] == 1
    assert dados["indicadores"]["mensagens"] == 2
    assert dados["indicadores"]["llm_ativa"] is False
    assert any(item["intencao"] == "reclamacao" and item["total"] >= 1 for item in dados["intencoes"])
    assert dados["historico"]

    relatorio = client.post("/relatorios", json={"limite": 20})
    assert relatorio.status_code == 200
    corpo = relatorio.json()
    assert corpo["total_analisado"] == 2
    assert corpo["origem"] == "regras"
    assert "reclamacao" in corpo["intencoes"]
    assert corpo["resumo"]


def test_atualizar_cliente_parcial(client):
    criado = client.post(
        "/clientes",
        json={"nome": "Felipe Costa", "telefone": "11988887776", "email": "felipe@mail.com"},
    ).json()["cliente"]
    atualizado = client.put(f"/clientes/{criado['id']}", json={"nome": "Felipe C."})
    assert atualizado.status_code == 200
    assert atualizado.json()["cliente"]["nome"] == "Felipe C."
    assert atualizado.json()["cliente"]["telefone"] == "11988887776"
