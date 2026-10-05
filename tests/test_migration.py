from sqlalchemy import create_engine, inspect, text

from migrations import ensure_schema


def test_migracao_cp1_preserva_dados_e_cria_fk(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'cp1.db'}")
    with engine.begin() as conexao:
        conexao.exec_driver_sql(
            "CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome VARCHAR(100) NOT NULL, "
            "telefone VARCHAR(20) NOT NULL UNIQUE, email VARCHAR(150))"
        )
        conexao.exec_driver_sql(
            "CREATE TABLE mensagens (id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL, "
            "texto VARCHAR(500) NOT NULL, resposta VARCHAR(1000) NOT NULL, data_hora DATETIME)"
        )
        conexao.exec_driver_sql(
            "INSERT INTO clientes VALUES (1, 'Ana', '11988887777', NULL)"
        )
        conexao.exec_driver_sql(
            "INSERT INTO mensagens VALUES (1, 1, 'oi', 'Olá', '2026-10-05 12:00:00'), "
            "(2, 999, 'órfã', 'resposta', '2026-10-05 12:00:00')"
        )

    ensure_schema(engine)
    ensure_schema(engine)

    inspector = inspect(engine)
    assert any(fk["referred_table"] == "clientes" for fk in inspector.get_foreign_keys("mensagens"))
    indices = {item["name"] for item in inspector.get_indexes("mensagens")}
    assert {"ix_mensagens_cliente_id", "ix_mensagens_intencao"} <= indices

    with engine.begin() as conexao:
        assert conexao.exec_driver_sql("PRAGMA foreign_key_list(mensagens)").first()[6] == "CASCADE"
        assert conexao.execute(text("SELECT COUNT(*) FROM mensagens")).scalar_one() == 1
        assert conexao.execute(text("SELECT texto FROM mensagens_orfas_cp1")).scalar_one() == "órfã"
        assert conexao.execute(text("SELECT criado_em FROM clientes WHERE id = 1")).scalar_one()
        conexao.execute(text("DELETE FROM clientes WHERE id = 1"))
        assert conexao.execute(text("SELECT COUNT(*) FROM mensagens")).scalar_one() == 0
