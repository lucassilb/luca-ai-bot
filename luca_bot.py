def gerar_resposta(texto: str):

    texto = texto.lower()

    if "olá" in texto or "ola" in texto or "oi" in texto:
        return "Olá! Sou o Luca.AI BOT. Como posso ajudar você?"

    if "pedido" in texto:
        return "Claro! Posso ajudar você com informações sobre seu pedido."

    if "preço" in texto or "preco" in texto:
        return "Posso ajudar você com informações sobre preços."

    if "horário" in texto or "horario" in texto:
        return "Nosso atendimento funciona de segunda a sexta, das 08h às 18h."

    if "problema" in texto or "erro" in texto:
        return "Entendi. Pode me explicar melhor o problema para que eu possa ajudar?"

    if "atendente" in texto or "humano" in texto:
        return "Claro! Vou encaminhar sua solicitação para um atendente."

    if "obrigado" in texto or "obrigada" in texto:
        return "Por nada! Estou à disposição para ajudar."

    return "Entendi sua mensagem. Pode me explicar um pouco mais para que eu possa ajudar?"