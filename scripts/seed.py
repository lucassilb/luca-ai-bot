"""Popula o banco com clientes e conversas para o dashboard do CP2."""
from datetime import datetime, timedelta

from database import Base, SessionLocal, engine
from models import Cliente, Mensagem
from services.bot import gerar_resposta_completa

AMOSTRAS = [
    ("Ana Souza", "11988887771", "ana@empresa.com", [
        "oi, bom dia",
        "quero saber o status do meu pedido 4412",
        "obrigada",
    ]),
    ("Bruno Lima", "11988887772", "bruno@loja.com", [
        "quanto custa o plano mensal?",
        "vocês abrem sábado?",
    ]),
    ("Carla Dias", "11988887773", "carla@mail.com", [
        "meu pedido atrasou e ninguém responde, isso é urgente",
        "quero falar com um atendente agora",
    ]),
    ("Diego Alves", "11988887774", None, [
        "deu erro no pagamento, não funciona",
        "valeu pela ajuda",
    ]),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Cliente).count() >= 4:
            print("banco já tem clientes; seed ignorado")
            return
        agora = datetime.utcnow()
        for indice, (nome, telefone, email, textos) in enumerate(AMOSTRAS):
            cliente = Cliente(nome=nome, telefone=telefone, email=email)
            db.add(cliente)
            db.flush()
            for offset, texto in enumerate(textos):
                gerado = gerar_resposta_completa(texto)
                db.add(
                    Mensagem(
                        cliente_id=cliente.id,
                        texto=texto,
                        resposta=gerado["resposta"],
                        intencao=gerado["intencao"],
                        urgencia=gerado["urgencia"],
                        sentimento=gerado["sentimento"],
                        origem_resposta=gerado["origem_resposta"],
                        data_hora=agora - timedelta(hours=20 - indice * 3 - offset),
                    )
                )
        db.commit()
        print("seed ok")
    finally:
        db.close()


if __name__ == "__main__":
    main()
