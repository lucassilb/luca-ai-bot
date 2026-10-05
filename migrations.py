"""Migração pequena e transacional do SQLite do CP1 para o esquema do CP2."""
from __future__ import annotations

from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from database import Base
import models  # noqa: F401 - registra as tabelas no metadata


NOVAS_COLUNAS = {
    "intencao": ("VARCHAR(40) NOT NULL DEFAULT 'outros'", "'outros'"),
    "urgencia": ("VARCHAR(20) NOT NULL DEFAULT 'baixa'", "'baixa'"),
    "sentimento": ("VARCHAR(20) NOT NULL DEFAULT 'neutro'", "'neutro'"),
    "origem_resposta": ("VARCHAR(20) NOT NULL DEFAULT 'regras'", "'regras'"),
}


def _recriar_mensagens(conexao, existentes: set[str]) -> None:
    """Recria a tabela antiga com FK; preserva órfãs em tabela de arquivo."""
    conexao.exec_driver_sql(
        "CREATE TABLE IF NOT EXISTS mensagens_orfas_cp1 AS "
        "SELECT * FROM mensagens WHERE 0"
    )
    conexao.exec_driver_sql(
        "INSERT INTO mensagens_orfas_cp1 SELECT m.* FROM mensagens m "
        "LEFT JOIN clientes c ON c.id = m.cliente_id WHERE c.id IS NULL"
    )
    conexao.exec_driver_sql(
        """CREATE TABLE mensagens_cp2_migracao (
            id INTEGER PRIMARY KEY,
            cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
            texto VARCHAR(500) NOT NULL,
            resposta TEXT NOT NULL,
            data_hora DATETIME NOT NULL,
            intencao VARCHAR(40) NOT NULL DEFAULT 'outros',
            urgencia VARCHAR(20) NOT NULL DEFAULT 'baixa',
            sentimento VARCHAR(20) NOT NULL DEFAULT 'neutro',
            origem_resposta VARCHAR(20) NOT NULL DEFAULT 'regras'
        )"""
    )
    campos = ["id", "cliente_id", "texto", "resposta", "data_hora", *NOVAS_COLUNAS]
    origens = [
        "COALESCE(m.data_hora, CURRENT_TIMESTAMP)" if campo == "data_hora"
        else f"m.{campo}" if campo in existentes
        else NOVAS_COLUNAS[campo][1]
        for campo in campos
    ]
    conexao.exec_driver_sql(
        f"INSERT INTO mensagens_cp2_migracao ({', '.join(campos)}) "
        f"SELECT {', '.join(origens)} FROM mensagens m "
        "JOIN clientes c ON c.id = m.cliente_id"
    )
    conexao.exec_driver_sql("DROP TABLE mensagens")
    conexao.exec_driver_sql("ALTER TABLE mensagens_cp2_migracao RENAME TO mensagens")


def ensure_schema(engine: Engine) -> None:
    with engine.begin() as conexao:
        Base.metadata.create_all(bind=conexao)
        inspector = inspect(conexao)

        clientes = {col["name"] for col in inspector.get_columns("clientes")}
        if "criado_em" not in clientes:
            conexao.exec_driver_sql("ALTER TABLE clientes ADD COLUMN criado_em DATETIME")
        conexao.exec_driver_sql(
            "UPDATE clientes SET criado_em = CURRENT_TIMESTAMP WHERE criado_em IS NULL"
        )

        existentes = {col["name"] for col in inspector.get_columns("mensagens")}
        chaves = inspector.get_foreign_keys("mensagens")
        possui_fk = any(
            chave["referred_table"] == "clientes"
            and chave["constrained_columns"] == ["cliente_id"]
            for chave in chaves
        )
        if not possui_fk:
            _recriar_mensagens(conexao, existentes)
        else:
            for coluna, (definicao, _) in NOVAS_COLUNAS.items():
                if coluna not in existentes:
                    conexao.exec_driver_sql(
                        f"ALTER TABLE mensagens ADD COLUMN {coluna} {definicao}"
                    )

        for tabela in Base.metadata.tables.values():
            for indice in tabela.indexes:
                indice.create(bind=conexao, checkfirst=True)
