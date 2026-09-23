from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Cliente, Mensagem
from schemas import ConversaOut, MensagemCreate, MensagemOut, PaginatedMensagens
from services.bot import gerar_resposta_completa

router = APIRouter(prefix="/mensagens", tags=["Mensagens"])


@router.post(
    "",
    status_code=201,
    summary="Enviar mensagem para o Luca.AI BOT",
    description=(
        "Recebe a mensagem do cliente, classifica a intenção, gera resposta "
        "(LLM se configurada, senão regras) e grava no histórico."
    ),
    responses={
        201: {"description": "Mensagem processada com sucesso."},
        404: {"description": "Cliente não encontrado."},
        422: {"description": "Dados inválidos."},
    },
)
def enviar_mensagem(mensagem: MensagemCreate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == mensagem.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    gerado = gerar_resposta_completa(mensagem.texto)
    nova = Mensagem(
        cliente_id=mensagem.cliente_id,
        texto=mensagem.texto,
        resposta=gerado["resposta"],
        intencao=gerado["intencao"],
        urgencia=gerado["urgencia"],
        sentimento=gerado["sentimento"],
        origem_resposta=gerado["origem_resposta"],
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return {
        "mensagem": "Mensagem processada com sucesso!",
        "conversa": ConversaOut(
            id=nova.id,
            cliente=cliente.nome,
            cliente_id=cliente.id,
            texto=nova.texto,
            resposta=nova.resposta,
            data_hora=nova.data_hora,
            intencao=nova.intencao,
            urgencia=nova.urgencia,
            sentimento=nova.sentimento,
            origem_resposta=nova.origem_resposta,
        ),
    }


@router.get("", response_model=PaginatedMensagens, summary="Listar mensagens")
def listar_mensagens(
    cliente_id: int | None = Query(None, gt=0),
    intencao: str | None = Query(None),
    urgencia: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    consulta = db.query(Mensagem)
    if cliente_id:
        consulta = consulta.filter(Mensagem.cliente_id == cliente_id)
    if intencao:
        consulta = consulta.filter(Mensagem.intencao == intencao)
    if urgencia:
        consulta = consulta.filter(Mensagem.urgencia == urgencia)
    total = consulta.with_entities(func.count(Mensagem.id)).scalar() or 0
    mensagens = consulta.order_by(Mensagem.data_hora.desc()).offset(skip).limit(limit).all()
    return PaginatedMensagens(
        total=total,
        skip=skip,
        limit=limit,
        mensagens=[MensagemOut.model_validate(item) for item in mensagens],
    )


@router.get("/{mensagem_id}", response_model=MensagemOut)
def buscar_mensagem(mensagem_id: int, db: Session = Depends(get_db)):
    mensagem = db.query(Mensagem).filter(Mensagem.id == mensagem_id).first()
    if not mensagem:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada.")
    return MensagemOut.model_validate(mensagem)


@router.delete("/{mensagem_id}", status_code=204)
def excluir_mensagem(mensagem_id: int, db: Session = Depends(get_db)):
    mensagem = db.query(Mensagem).filter(Mensagem.id == mensagem_id).first()
    if not mensagem:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada.")
    db.delete(mensagem)
    db.commit()
