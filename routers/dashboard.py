from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Cliente, Mensagem
from services.classificacao import INTENCOES
from services.llm import llm_configurado, modelo_atual

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _contagem(db: Session, coluna) -> dict[str, int]:
    linhas = db.query(coluna, func.count(Mensagem.id)).group_by(coluna).all()
    return {str(chave): int(total) for chave, total in linhas if chave is not None}


@router.get("", summary="Indicadores operacionais do atendimento")
def obter_dashboard(db: Session = Depends(get_db)):
    agora = datetime.utcnow()
    inicio_hoje = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_semana = agora - timedelta(days=7)

    total_clientes = db.query(func.count(Cliente.id)).scalar() or 0
    total_mensagens = db.query(func.count(Mensagem.id)).scalar() or 0
    mensagens_hoje = (
        db.query(func.count(Mensagem.id)).filter(Mensagem.data_hora >= inicio_hoje).scalar() or 0
    )
    mensagens_semana = (
        db.query(func.count(Mensagem.id)).filter(Mensagem.data_hora >= inicio_semana).scalar() or 0
    )
    por_intencao = _contagem(db, Mensagem.intencao)
    por_urgencia = _contagem(db, Mensagem.urgencia)
    por_sentimento = _contagem(db, Mensagem.sentimento)
    por_origem = _contagem(db, Mensagem.origem_resposta)

    reclamacoes = por_intencao.get("reclamacao", 0)
    alta = por_urgencia.get("alta", 0)
    alertas: list[dict] = []
    if reclamacoes:
        alertas.append(
            {
                "tipo": "reclamacao",
                "nivel": "alto" if reclamacoes >= 3 else "medio",
                "texto": f"{reclamacoes} reclamação(ões) no histórico — priorize retorno humano.",
            }
        )
    if alta:
        alertas.append(
            {
                "tipo": "urgencia",
                "nivel": "alto",
                "texto": f"{alta} mensagem(ns) classificada(s) como urgência alta.",
            }
        )

    recentes = (
        db.query(Mensagem, Cliente.nome)
        .join(Cliente, Cliente.id == Mensagem.cliente_id)
        .order_by(Mensagem.data_hora.desc())
        .limit(8)
        .all()
    )
    historico = [
        {
            "id": mensagem.id,
            "cliente": nome,
            "texto": mensagem.texto,
            "resposta": mensagem.resposta,
            "intencao": mensagem.intencao,
            "urgencia": mensagem.urgencia,
            "sentimento": mensagem.sentimento,
            "origem_resposta": mensagem.origem_resposta,
            "data_hora": mensagem.data_hora,
        }
        for mensagem, nome in recentes
    ]

    intencoes = [{"intencao": chave, "total": por_intencao.get(chave, 0)} for chave in INTENCOES]

    return {
        "gerado_em": agora,
        "indicadores": {
            "clientes": total_clientes,
            "mensagens": total_mensagens,
            "mensagens_hoje": mensagens_hoje,
            "mensagens_7d": mensagens_semana,
            "reclamacoes": reclamacoes,
            "urgencia_alta": alta,
            "llm_ativa": llm_configurado(),
            "llm_modelo": modelo_atual() if llm_configurado() else None,
        },
        "intencoes": intencoes,
        "urgencia": por_urgencia,
        "sentimento": por_sentimento,
        "origem_resposta": por_origem,
        "alertas": alertas,
        "historico": historico,
    }
