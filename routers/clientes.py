from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Cliente, Mensagem
from schemas import ClienteCreate


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)


@router.post(
    "",
    status_code=201,
    summary="Cadastrar novo cliente",
    description="Cadastra um novo cliente no sistema do Luca.AI BOT.",
    responses={
        201: {
            "description": "Cliente criado com sucesso."
        },
        409: {
            "description": "Já existe um cliente com este telefone."
        }
    }
)
def criar_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db)
):
    cliente_existente = db.query(Cliente).filter(
        Cliente.telefone == cliente.telefone
    ).first()

    if cliente_existente:
        raise HTTPException(
            status_code=409,
            detail="Já existe um cliente com este telefone."
        )

    novo_cliente = Cliente(
        nome=cliente.nome,
        telefone=cliente.telefone,
        email=cliente.email
    )

    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)

    return {
        "mensagem": "Cliente criado com sucesso!",
        "cliente": {
            "id": novo_cliente.id,
            "nome": novo_cliente.nome,
            "telefone": novo_cliente.telefone,
            "email": novo_cliente.email
        }
    }


@router.get("")
def listar_clientes(db: Session = Depends(get_db)):
    clientes = db.query(Cliente).all()

    return {
        "clientes": [
            {
                "id": cliente.id,
                "nome": cliente.nome,
                "telefone": cliente.telefone,
                "email": cliente.email
            }
            for cliente in clientes
        ]
    }


@router.get("/{cliente_id}")
def buscar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    cliente = db.query(Cliente).filter(
        Cliente.id == cliente_id
    ).first()

    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado."
        )

    return {
        "id": cliente.id,
        "nome": cliente.nome,
        "telefone": cliente.telefone,
        "email": cliente.email
    }


@router.put("/{cliente_id}")
def atualizar_cliente(
    cliente_id: int,
    dados: ClienteCreate,
    db: Session = Depends(get_db)
):
    cliente = db.query(Cliente).filter(
        Cliente.id == cliente_id
    ).first()

    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado."
        )

    cliente.nome = dados.nome
    cliente.telefone = dados.telefone
    cliente.email = dados.email

    db.commit()
    db.refresh(cliente)

    return {
        "mensagem": "Cliente atualizado com sucesso!",
        "cliente": {
            "id": cliente.id,
            "nome": cliente.nome,
            "telefone": cliente.telefone,
            "email": cliente.email
        }
    }


@router.delete("/{cliente_id}", status_code=204)
def excluir_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    cliente = db.query(Cliente).filter(
        Cliente.id == cliente_id
    ).first()

    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado."
        )

    db.delete(cliente)
    db.commit()


@router.get("/{cliente_id}/mensagens")
def listar_mensagens_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    cliente = db.query(Cliente).filter(
        Cliente.id == cliente_id
    ).first()

    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado."
        )

    mensagens = db.query(Mensagem).filter(
        Mensagem.cliente_id == cliente_id
    ).all()

    return {
        "cliente": {
            "id": cliente.id,
            "nome": cliente.nome
        },
        "mensagens": [
            {
                "id": mensagem.id,
                "texto": mensagem.texto,
                "resposta": mensagem.resposta,
                "data_hora": mensagem.data_hora
            }
            for mensagem in mensagens
        ]
    }