from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Cliente, Mensagem
from schemas import MensagemCreate
from luca_bot import gerar_resposta


router = APIRouter(
    prefix="/mensagens",
    tags=["Mensagens"]
)


@router.post(
    "",
    status_code=201,
    summary="Enviar mensagem para o Luca.AI BOT",
    description="Recebe uma mensagem de um cliente, processa a solicitação e gera uma resposta automática do Luca.AI BOT.",
    responses={
        201: {
            "description": "Mensagem processada com sucesso."
        },
        404: {
            "description": "Cliente não encontrado."
        }
    }
)
def enviar_mensagem(
    mensagem: MensagemCreate,
    db: Session = Depends(get_db)
):

    cliente = db.query(Cliente).filter(
        Cliente.id == mensagem.cliente_id
    ).first()

    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado."
        )

    resposta = gerar_resposta(mensagem.texto)

    nova_mensagem = Mensagem(
        cliente_id=mensagem.cliente_id,
        texto=mensagem.texto,
        resposta=resposta
    )

    db.add(nova_mensagem)
    db.commit()
    db.refresh(nova_mensagem)

    return {
        "mensagem": "Mensagem processada com sucesso!",
        "conversa": {
            "id": nova_mensagem.id,
            "cliente": cliente.nome,
            "texto": nova_mensagem.texto,
            "resposta": nova_mensagem.resposta,
            "data_hora": nova_mensagem.data_hora
        }
    }


@router.get("")
def listar_mensagens(
    db: Session = Depends(get_db)
):

    mensagens = db.query(Mensagem).all()

    return mensagens


@router.get("/{mensagem_id}")
def buscar_mensagem(
    mensagem_id: int,
    db: Session = Depends(get_db)
):

    mensagem = db.query(Mensagem).filter(
        Mensagem.id == mensagem_id
    ).first()

    if not mensagem:
        raise HTTPException(
            status_code=404,
            detail="Mensagem não encontrada."
        )

    return mensagem


@router.delete("/{mensagem_id}", status_code=204)
def excluir_mensagem(
    mensagem_id: int,
    db: Session = Depends(get_db)
):

    mensagem = db.query(Mensagem).filter(
        Mensagem.id == mensagem_id
    ).first()

    if not mensagem:
        raise HTTPException(
            status_code=404,
            detail="Mensagem não encontrada."
        )

    db.delete(mensagem)
    db.commit()