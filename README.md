# Sistema de Controle de Estoque

Trabalho Prático 2 da disciplina QXD0099 - Desenvolvimento de Software para Persistência  
Universidade Federal do Ceará, Campus Quixadá  
Prof. Francisco Victor da Silva Pinheiro

## Integrantes

- Ivna Leite
- Maria Grazyele
- Sâmia Feitosa

## Tema

**Tema 15 - Sistema de Controle de Estoque**

Uma distribuidora comercializa produtos de várias categorias, comprados de fornecedores diferentes e guardados em mais de um armazém. O sistema registra entradas, saídas e transferências entre armazéns, calcula o estoque disponível e identifica produtos abaixo do limite mínimo, sem permitir saldo negativo.

## Objetivo

Substituir o controle por planilhas por uma API REST com persistência em banco relacional, em que:

- o saldo de cada produto é controlado **por armazém**, e o estoque geral é a soma dos saldos;
- toda entrada de mercadoria está ligada a um **pedido de compra** (e, portanto, a um fornecedor), podendo o pedido ser recebido parcialmente;
- saídas e transferências nunca deixam o saldo negativo;
- uma movimentação ou acontece por completo ou não acontece (transação atômica), sem registros parcialmente confirmados.

## Tecnologias utilizadas

| Tecnologia | Uso |
|---|---|
| Python 3.10+ | Linguagem de programação |
| FastAPI | API REST e documentação automática (Swagger) |
| Uvicorn | Servidor ASGI da aplicação |
| SQLAlchemy 2 | Mapeamento objeto-relacional (ORM) |
| Alembic | Controle e evolução das migrações do banco |
| PostgreSQL | Banco de dados relacional principal |
| SQLite | Banco de dados alternativo (alterando apenas a `DATABASE_URL`) |
| psycopg 3 | Driver de conexão com o PostgreSQL |
| Pydantic | Validação de entrada e saída de dados |
| python-dotenv | Carregamento de variáveis de ambiente via `.env` |

## Estrutura do projeto

```text
Sistema_de_Controle_de_Estoque-DSP/
├── app/
│   ├── main.py              cria a aplicação FastAPI e registra os routers
│   ├── config.py            lê a DATABASE_URL do ambiente
│   ├── database.py          engine, sessão e Base declarativa do ORM
│   ├── errors.py            exceções do domínio e handlers de erros HTTP
│   ├── models/              modelos relacionais (SQLAlchemy)
│   ├── schemas/             schemas de entrada, atualização, saída e paginação (Pydantic)
│   ├── crud/                operações de persistência, filtros e paginação no banco
│   ├── services/            regras de negócio, transações atômicas e consultas complexas
│   └── routers/             rotas da API organizadas por recurso (APIRouter)
├── alembic/                 controle de migrações do esquema
│   └── versions/
├── scripts/
│   └── povoar.py            script de povoamento inicial do banco
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```

## Entidades

| Entidade | Descrição | Principais atributos |
|---|---|---|
| Categoria | Agrupa produtos por segmento | `id`, `nome` (único), `descricao` |
| Fornecedor | Empresa que fornece mercadorias | `id`, `nome`, `cnpj` (único), `email`, `telefone`, `ativo` |
| Produto | Mercadoria comercializada | `id`, `codigo` (único), `nome`, `preco_unitario`, `estoque_minimo`, `ativo`, `categoria_id` |
| CaracteristicaProduto | Ficha técnica de armazenamento do produto | `id`, `produto_id` (único), `peso_kg`, `unidade_medida`, `condicao_armazenamento`, `perecivel` |
| Armazem | Depósito físico da distribuidora | `id`, `nome` (único), `cidade`, `endereco`, `ativo` |
| EstoqueArmazem | Saldo de um produto em um armazém específico | `produto_id`, `armazem_id`, `quantidade` (`>= 0`) |
| PedidoCompra | Ordem de compra feita a um fornecedor | `id`, `fornecedor_id`, `data_pedido`, `status` (`aberto`, `parcial`, `recebido`, `cancelado`) |
| ItemPedidoCompra | Item de produto dentro de um pedido de compra | `id`, `pedido_id`, `produto_id`, `quantidade_pedida`, `quantidade_recebida`, `preco_unitario` |
| Movimentacao | Histórico de entradas, saídas e transferências | `id`, `tipo`, `produto_id`, `quantidade`, `data_hora`, `motivo`, `armazem_origem_id`, `armazem_destino_id`, `pedido_compra_id` |

## Relacionamentos

| Tipo | Relacionamento | Descrição |
|---|---|---|
| 1:1 | `Produto` e `CaracteristicaProduto` | Cada produto possui uma ficha opcional de armazenamento vinculada exclusivamente a ele |
| 1:N | `Categoria` e `Produto` | Uma categoria agrupa vários produtos; cada produto pertence a uma categoria |
| 1:N | `Fornecedor` e `PedidoCompra` | Um fornecedor recebe vários pedidos de compra; cada pedido pertence a um fornecedor |
| 1:N | `PedidoCompra` e `ItemPedidoCompra` | Um pedido contém um ou mais itens de produto |
| 1:N | `Produto` e `ItemPedidoCompra` | Um produto pode constar em vários itens de pedidos distintos |
| 1:N | `Produto` e `Movimentacao` | Um produto possui vários registros no histórico de movimentações |
| 1:N | `Armazem` e `Movimentacao` | Um armazém pode atuar como origem (saídas/transferências) ou destino (entradas/transferências) |
| 1:N | `PedidoCompra` e `Movimentacao` | Um pedido de compra pode originar uma ou mais entradas (recebimento parcial) |
| N:N | `Produto` e `Fornecedor` | Associação via tabela `produto_fornecedor`, indicando quais fornecedores vendem cada produto |
| N:N | `Produto` e `Armazem` | Associação via entidade `EstoqueArmazem`, armazenando o saldo atual de cada produto por depósito |

## Diagrama do modelo relacional

```mermaid
erDiagram
    CATEGORIAS ||--o{ PRODUTOS : classifica
    PRODUTOS ||--o| CARACTERISTICAS_PRODUTO : possui
    PRODUTOS ||--o{ PRODUTO_FORNECEDOR : "e fornecido por"
    FORNECEDORES ||--o{ PRODUTO_FORNECEDOR : fornece
    FORNECEDORES ||--o{ PEDIDOS_COMPRA : recebe
    PEDIDOS_COMPRA ||--|{ ITENS_PEDIDO_COMPRA : contem
    PRODUTOS ||--o{ ITENS_PEDIDO_COMPRA : "aparece em"
    PRODUTOS ||--o{ ESTOQUE_ARMAZEM : "tem saldo"
    ARMAZENS ||--o{ ESTOQUE_ARMAZEM : guarda
    PRODUTOS ||--o{ MOVIMENTACOES : movimenta
    ARMAZENS |o--o{ MOVIMENTACOES : "origem / destino"
    PEDIDOS_COMPRA |o--o{ MOVIMENTACOES : origina

    CATEGORIAS {
        int id PK
        string nome UK
        string descricao
    }
    FORNECEDORES {
        int id PK
        string nome
        string cnpj UK
        string email
        string telefone
        bool ativo
    }
    PRODUTOS {
        int id PK
        string codigo UK
        string nome
        decimal preco_unitario
        int estoque_minimo
        bool ativo
        int categoria_id FK
    }
    CARACTERISTICAS_PRODUTO {
        int id PK
        int produto_id FK, UK
        decimal peso_kg
        string unidade_medida
        string condicao_armazenamento
        bool perecivel
    }
    PRODUTO_FORNECEDOR {
        int produto_id PK, FK
        int fornecedor_id PK, FK
    }
    ARMAZENS {
        int id PK
        string nome UK
        string cidade
        string endereco
        bool ativo
    }
    ESTOQUE_ARMAZEM {
        int produto_id PK, FK
        int armazem_id PK, FK
        int quantidade "CHECK >= 0"
    }
    PEDIDOS_COMPRA {
        int id PK
        int fornecedor_id FK
        datetime data_pedido
        string status
    }
    ITENS_PEDIDO_COMPRA {
        int id PK
        int pedido_id FK
        int produto_id FK
        int quantidade_pedida
        int quantidade_recebida
        decimal preco_unitario
    }
    MOVIMENTACOES {
        int id PK
        string tipo
        int produto_id FK
        int quantidade
        datetime data_hora
        string motivo
        int armazem_origem_id FK
        int armazem_destino_id FK
        int pedido_compra_id FK
    }
```

## Funcionalidade específica do tema

A funcionalidade central do **Controle de Estoque (Tema 15)** integra o controle de saldo distribuído por armazém com a rastreabilidade de compras e movimentações:

- **Cálculo de estoque por armazém e total:** o saldo é persistido na tabela `estoque_armazem` para cada par `(produto, armazém)`, enquanto o estoque geral do produto é calculado dinamicamente pela soma dos saldos em todos os depósitos.
- **Alertas de estoque mínimo:** o sistema compara o estoque total de cada produto com seu `estoque_minimo` cadastrado, identificando itens em nível crítico e calculando a quantidade faltante para reposição.
- **Fluxo completo de movimentação:** entradas são vinculadas obrigatoriamente a um `PedidoCompra` (atualizando as quantidades recebidas e o status do pedido entre `aberto`, `parcial` e `recebido`), enquanto saídas e transferências abatem ou redistribuem os saldos entre armazéns dentro de uma única transação atômica.

## Principais endpoints

### Cadastros base (CRUD)

| Método | Rota | Descrição |
|---|---|---|
| `POST` / `GET` | `/categorias` | Cadastra ou lista categorias (com paginação e filtros) |
| `GET` / `PATCH` / `DELETE` | `/categorias/{id}` | Consulta, atualiza ou remove uma categoria |
| `POST` / `GET` | `/fornecedores` | Cadastra ou lista fornecedores (com paginação e filtros) |
| `GET` / `PATCH` / `DELETE` | `/fornecedores/{id}` | Consulta, atualiza ou remove um fornecedor |
| `POST` / `GET` | `/armazens` | Cadastra ou lista armazéns (com paginação e filtros) |
| `GET` / `PATCH` / `DELETE` | `/armazens/{id}` | Consulta, atualiza ou remove um armazém |
| `POST` / `GET` | `/produtos` | Cadastra (com categoria, fornecedores e característica) ou lista produtos |
| `GET` / `PATCH` / `DELETE` | `/produtos/{id}` | Consulta detalhes completos, atualiza ou remove um produto |

### Pedidos de compra, movimentações e estoque

| Método | Rota | Descrição |
|---|---|---|
| `POST` / `GET` | `/pedidos-compra` | Cria um pedido de compra com itens ou lista pedidos |
| `GET` / `DELETE` | `/pedidos-compra/{id}` | Consulta detalhes/itens do pedido ou remove pedido sem recebimentos |
| `POST` | `/pedidos-compra/{id}/receber` | Registra recebimento total ou parcial de itens em um armazém (gera entrada) |
| `POST` | `/pedidos-compra/{id}/cancelar` | Cancela um pedido de compra aberto |
| `GET` / `GET /{id}` | `/movimentacoes` | Lista histórico de movimentações ou consulta registro específico |
| `POST` | `/movimentacoes/saida` | Registra saída de mercadoria de um armazém |
| `POST` | `/movimentacoes/transferencia` | Transfere mercadoria entre dois armazéns distintos |
| `GET` | `/estoque/produtos/{id}` | Retorna saldo por armazém, estoque total e indicador de mínimo do produto |
| `GET` | `/estoque/abaixo-do-minimo` | Lista produtos cujo estoque total está abaixo do `estoque_minimo` |
| `GET` | `/estatisticas` | Retorna métricas agregadas do domínio (totais, médias, valor em estoque e por categoria) |
| `GET` | `/saude` | Verifica o status da API e da conexão com o banco de dados |

## Filtros disponíveis e paginação

As listagens realizam paginação diretamente no banco via parâmetros `offset` e `limit` (retornando `total`, `pagina_atual`, `total_paginas` e os itens) e aceitam filtros combináveis na query string:

- **Produtos (`GET /produtos`):** `nome`, `codigo`, `categoria_id`, `ativo`, `perecivel`
- **Categorias (`GET /categorias`):** `nome`
- **Fornecedores (`GET /fornecedores`):** `nome`, `cnpj`, `ativo`
- **Armazéns (`GET /armazens`):** `nome`, `cidade`, `ativo`
- **Pedidos de compra (`GET /pedidos-compra`):** `fornecedor_id`, `status`
- **Movimentações (`GET /movimentacoes`):** `tipo` (`entrada`, `saida`, `transferencia`), `produto_id`, `armazem_id`

## Consultas específicas

### Consultas envolvendo relacionamentos

- `GET /categorias/{id}/produtos` — lista os produtos pertencentes a uma categoria.
- `GET /produtos/{id}/movimentacoes` — consulta o histórico de entradas, saídas e transferências de um produto.
- `GET /fornecedores/{id}/pedidos` — lista os pedidos de compra realizados para um fornecedor.
- `GET /armazens/{id}/estoque` — lista os produtos e quantidades armazenados em um depósito específico.

### Consultas complexas e estatísticas

- **Movimentações por período:** consulta entradas, saídas e transferências filtradas por intervalo de datas e tipo, consolidando quantidades movimentadas.
- **Produtos sem movimentação:** identifica produtos cadastrados que não tiveram registros de movimentação dentro de um período (dias sem giro).
- **Comparação de saldos entre armazéns:** cruza os saldos de `EstoqueArmazem` entre os depósitos ativos para evidenciar distribuição e desbalanceamento de estoque.
- **Estatísticas gerais (`GET /estatisticas`):** calcula totais de entidades, valor financeiro total em estoque (`SUM(quantidade * preco_unitario)`), preço médio dos produtos e distribuição de produtos por categoria e pedidos por status.

## Regras de negócio

1. **Bloqueio de saldo negativo:** saídas e transferências validam o saldo disponível no armazém de origem antes de efetivar a operação (retornando HTTP `409` se insuficiente), além de haver restrição `CHECK (quantidade >= 0)` no banco.
2. **Transações atômicas e bloqueio de concorrência:** toda movimentação executa atualização de saldo, registro histórico e atualização de pedido dentro de uma única transação com bloqueio de linha (`SELECT ... FOR UPDATE`), impedindo inconsistências em operações simultâneas.
3. **Entrada vinculada a pedido de compra e recebimento parcial:** entradas só ocorrem a partir de um `PedidoCompra` válido (não cancelado/concluído), impedindo receber quantidade maior que o saldo pendente do item e atualizando automaticamente o status do pedido para `parcial` ou `recebido`.
4. **Vínculo produto–fornecedor obrigatório:** um pedido de compra só aceita itens de produtos previamente associados ao fornecedor selecionado na tabela `produto_fornecedor`.
5. **Validação de origem e destino nas movimentações:** transferências exigem armazéns de origem e destino diferentes; entradas exigem destino e pedido; saídas exigem apenas origem.
6. **Bloqueio de operações com entidades inativas:** produtos, fornecedores ou armazéns com `ativo = false` não podem participar de novos pedidos ou movimentações.
7. **Unicidade de identificadores de negócio:** impede duplicidade de `nome` em categorias e armazéns, `cnpj` em fornecedores e `codigo` em produtos (HTTP `409`).
8. **Integridade na exclusão:** impede remover categorias com produtos vinculados, armazéns com saldo positivo ou histórico, e pedidos de compra que já possuam recebimentos registrados (HTTP `409`).

## Instalação e execução

### 1. Clonar o repositório e criar o ambiente virtual

```powershell
git clone https://github.com/Samia8120-coder/Sistema_de_Controle_de_Estoque-DSP.git
cd Sistema_de_Controle_de_Estoque-DSP
python -m venv .venv
.venv\Scripts\activate
```

Se o PowerShell bloquear a ativação do ambiente virtual, execute uma vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2. Instalar as dependências

```powershell
pip install -r requirements.txt
```

### 3. Configurar o banco de dados (`DATABASE_URL`)

Copie o arquivo de exemplo para criar o `.env`:

```powershell
copy .env.example .env
```

#### Opção A: PostgreSQL (banco principal)

Com o PostgreSQL instalado, abra o **SQL Shell (psql)** como usuário `postgres` e execute:

```sql
CREATE USER estoque WITH PASSWORD 'estoque123';
CREATE DATABASE estoque_db OWNER estoque;
```

Configure o `.env`:

```env
DATABASE_URL=postgresql+psycopg://estoque:estoque123@localhost:5432/estoque_db
```

*(Caso a senha contenha caracteres especiais como `@`, `/` ou `:`, utilize codificação URL, por exemplo `%40` no lugar de `@`.)*

#### Opção B: SQLite (banco alternativo)

Para utilizar SQLite sem alterar nenhuma classe, router ou operação CRUD, defina no `.env`:

```env
DATABASE_URL=sqlite:///./estoque.db
```

### 4. Executar as migrações com Alembic

```powershell
alembic upgrade head
```

Comandos adicionais do Alembic:

| Comando | Descrição |
|---|---|
| `alembic current` | Exibe a revisão atual aplicada no banco |
| `alembic history` | Lista o histórico de migrações |
| `alembic downgrade -1` | Reverte a última migração |
| `alembic revision --autogenerate -m "descricao"` | Gera uma nova migração a partir dos modelos |

O histórico conta com duas migrações: a `0001` cria a estrutura inicial das tabelas e a `0002` aplica uma evolução estrutural adicionando a coluna `telefone` em `fornecedores` e o índice `ix_movimentacoes_data_hora` em `movimentacoes`, sem necessidade de recriar o banco.

### 5. Povoar o banco com dados iniciais

```powershell
python -m scripts.povoar
```

O script cadastra 6 categorias, 7 fornecedores, 4 armazéns, 17 produtos, 7 pedidos de compra (em diferentes status) e 33 movimentações distribuídas nos últimos 45 dias, utilizando as mesmas regras de negócio e validações da API.

Para limpar os dados e repovoar novamente:

```powershell
python -m scripts.povoar --limpar
```

### 6. Iniciar a aplicação

```powershell
uvicorn app.main:app --reload
```

- **Base URL da API:** `http://127.0.0.1:8000`
- **Documentação interativa (Swagger UI):** `http://127.0.0.1:8000/docs`