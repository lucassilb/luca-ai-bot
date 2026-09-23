# Modelagem CP2

## Antes (CP1)

- `mensagens.cliente_id` era Integer sem FK.
- Dava para gravar mensagem de cliente inexistente se a rota falhasse.
- Excluir cliente deixava conversas órfãs.
- Não havia dimensão analítica: o dashboard teria que classificar texto de novo.

## Depois

```
clientes
  id PK
  nome
  telefone UNIQUE INDEX   -- identidade do canal
  email INDEX
  criado_em

mensagens
  id PK
  cliente_id FK → clientes.id ON DELETE CASCADE INDEX
  texto
  resposta
  data_hora INDEX
  intencao INDEX          -- saudacao|pedido|preco|horario|reclamacao|atendente|agradecimento|outros
  urgencia INDEX          -- baixa|media|alta
  sentimento
  origem_resposta         -- regras|llm
```

## Normalização

- 1FN: campos atômicos; telefone só dígitos.
- 2FN/3FN: nome e contato ficam em `clientes`; a mensagem não copia o cliente.
- Não criamos tabela `intencoes`: o domínio tem um enum curto e estável, guardado como string checada na aplicação.

## Migração

`main._ensure_schema()` faz `CREATE TABLE` e `ALTER TABLE ... ADD COLUMN` no SQLite existente do CP1. Sem Alembic neste checkpoint (um arquivo local, sem deploy multi-ambiente).
