from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import get_db
from models import Cliente, Mensagem
from schemas import ClienteCreate, ClienteOut, ClienteUpdate, MensagemOut, PaginatedClientes

router = APIRouter(prefix="/clientes", tags=["Clientes"])


def _telefone_em_uso(db: Session, telefone: str, ignorar_id: int | None = None) -> bool:
    consulta = db.query(Cliente).filter(Cliente.telefone == telefone)
    if ignorar_id is not None:
        consulta = consulta.filter(Cliente.id != ignorar_id)
    return consulta.first() is not None


@router.post(
    "",
    status_code=201,
    summary="Cadastrar novo cliente",
    description="Cadastra um novo cliente. Telefone é único e armazenado só com dígitos.",
    responses={
        201: {"description": "Cliente criado com sucesso."},
        409: {"description": "Já existe um cliente com este telefone."},
        422: {"description": "Dados inválidos."},
    },
)
def criar_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    if _telefone_em_uso(db, cliente.telefone):
        raise HTTPException(status_code=409, detail="Já existe um cliente com este telefone.")

    novo = Cliente(nome=cliente.nome, telefone=cliente.telefone, email=cliente.email)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"mensagem": "Cliente criado com sucesso!", "cliente": ClienteOut.model_validate(novo)}


@router.get("", response_model=PaginatedClientes, summary="Listar clientes")
def listar_clientes(
    q: str | None = Query(None, description="Busca por nome, telefone ou e-mail"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    consulta = db.query(Cliente)
    if q:
        termo = f"%{q.strip()}%"
        consulta = consulta.filter(
            or_(Cliente.nome.ilike(termo), Cliente.telefone.ilike(termo), Cliente.email.ilike(termo))
        )
    total = consulta.with_entities(func.count(Cliente.id)).scalar() or 0
    clientes = consulta.order_by(Cliente.id.desc()).offset(skip).limit(limit).all()
    return PaginatedClientes(
        total=total,
        skip=skip,
        limit=limit,
        clientes=[ClienteOut.model_validate(item) for item in clientes],
    )


@router.get("/{cliente_id}", response_model=ClienteOut)
def buscar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return ClienteOut.model_validate(cliente)


@router.put("/{cliente_id}")
def atualizar_cliente(cliente_id: int, dados: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    if dados.nome is not None:
        cliente.nome = dados.nome
    if dados.telefone is not None:
        if _telefone_em_uso(db, dados.telefone, ignorar_id=cliente.id):
            raise HTTPException(status_code=409, detail="Já existe um cliente com este telefone.")
        cliente.telefone = dados.telefone
    if dados.email is not None:
        cliente.email = dados.email

    db.commit()
    db.refresh(cliente)
    return {"mensagem": "Cliente atualizado com sucesso!", "cliente": ClienteOut.model_validate(cliente)}


@router.delete("/{cliente_id}", status_code=204)
def excluir_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    db.delete(cliente)
    db.commit()


@router.get("/{cliente_id}/mensagens")
def listar_mensagens_cliente(
    cliente_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    consulta = db.query(Mensagem).filter(Mensagem.cliente_id == cliente_id)
    total = consulta.with_entities(func.count(Mensagem.id)).scalar() or 0
    mensagens = consulta.order_by(Mensagem.data_hora.desc()).offset(skip).limit(limit).all()
    return {
        "cliente": {"id": cliente.id, "nome": cliente.nome},
        "total": total,
        "skip": skip,
        "limit": limit,
        "mensagens": [MensagemOut.model_validate(item) for item in mensagens],
    }
