from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Cliente, Mensagem
from schemas import RelatorioOut, RelatorioRequest
from services.classificacao import INTENCOES
from services.llm import llm_configurado, modelo_atual, relatorio_com_llm

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


def _relatorio_local(intencoes: dict[str, int], total: int, reclamacoes: int, alta: int) -> dict:
    top = sorted(intencoes.items(), key=lambda item: item[1], reverse=True)
    lider = top[0][0] if top and top[0][1] else "outros"
    resumo = (
        f"Foram analisadas {total} mensagens. A intenção mais frequente é '{lider}'. "
        f"Há {reclamacoes} reclamação(ões) e {alta} caso(s) de urgência alta."
    )
    riscos = []
    recomendacoes = []
    if reclamacoes:
        riscos.append("Volume de reclamação pode indicar falha de entrega ou produto.")
        recomendacoes.append("Abrir fila humana para as conversas classificadas como reclamação.")
    if alta:
        riscos.append("Mensagens de urgência alta sem SLA definido.")
        recomendacoes.append("Definir tempo máximo de resposta para urgência alta.")
    if not riscos:
        riscos.append("Amostra ainda pequena para apontar risco estrutural.")
    if not recomendacoes:
        recomendacoes.append("Continuar registrando conversas para alimentar o dashboard.")
    return {"resumo": resumo, "riscos": riscos, "recomendacoes": recomendacoes}


@router.post("", response_model=RelatorioOut, summary="Gerar relatório operacional com LLM")
def gerar_relatorio(pedido: RelatorioRequest, db: Session = Depends(get_db)):
    consulta = db.query(Mensagem)
    if pedido.cliente_id:
        cliente = db.query(Cliente).filter(Cliente.id == pedido.cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")
        consulta = consulta.filter(Mensagem.cliente_id == pedido.cliente_id)

    mensagens = consulta.order_by(Mensagem.data_hora.desc()).limit(pedido.limite).all()
    if not mensagens:
        raise HTTPException(status_code=409, detail="Não há mensagens para analisar.")

    intencoes = {chave: 0 for chave in INTENCOES}
    for mensagem in mensagens:
        intencoes[mensagem.intencao] = intencoes.get(mensagem.intencao, 0) + 1

    reclamacoes = intencoes.get("reclamacao", 0)
    alta = sum(1 for mensagem in mensagens if mensagem.urgencia == "alta")
    contexto = {
        "total": len(mensagens),
        "intencoes": intencoes,
        "reclamacoes": reclamacoes,
        "urgencia_alta": alta,
        "amostra": [
            {
                "intencao": mensagem.intencao,
                "urgencia": mensagem.urgencia,
                "sentimento": mensagem.sentimento,
                "origem": mensagem.origem_resposta,
                "texto": mensagem.texto[:180],
            }
            for mensagem in mensagens[:15]
        ],
    }

    origem = "regras"
    modelo = "classificacao-local"
    corpo = _relatorio_local(intencoes, len(mensagens), reclamacoes, alta)
    if llm_configurado():
        gerado = relatorio_com_llm(contexto)
        if gerado:
            corpo = gerado
            origem = "llm"
            modelo = modelo_atual()

    return RelatorioOut(
        origem=origem,
        modelo=modelo,
        total_analisado=len(mensagens),
        resumo=corpo["resumo"],
        riscos=corpo["riscos"],
        recomendacoes=corpo["recomendacoes"],
        intencoes=intencoes,
    )
