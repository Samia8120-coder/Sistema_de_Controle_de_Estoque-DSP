# Controle de Estoque

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
- uma movimentação ou acontece por completo ou não acontece (transação), sem registros parcialmente confirmados.

## Tecnologias utilizadas

| Tecnologia | Uso |
|---|---|
| Python 3.10+ | Linguagem |
| FastAPI | API REST e documentação automática |
| Uvicorn | Servidor da aplicação |
| SQLAlchemy 2 | Mapeamento objeto-relacional (ORM) |
| Alembic | Migrações do esquema do banco |
| PostgreSQL | Banco principal |
| SQLite | Banco alternativo (troca só a `DATABASE_URL`) |
| psycopg 3 | Driver do PostgreSQL |
| Pydantic | Validação de entrada e saída |
| python-dotenv | Leitura do arquivo `.env` |

## Estrutura do projeto

```
Controle_Estoque-DSP/
├── app/
│   ├── main.py              cria a aplicação e registra os routers
│   ├── config.py            lê a DATABASE_URL
│   ├── database.py          conexão, sessão e Base do ORM
│   ├── errors.py            exceções do domínio e tratamento de erros HTTP
│   ├── models/              tabelas (SQLAlchemy)
│   ├── schemas/             validação de entrada e saída (Pydantic)
│   ├── crud/                consultas e operações simples no banco
│   ├── services/            regras de negócio, transações e consultas complexas
│   └── routers/             rotas da API (um APIRouter por recurso)
├── alembic/                 migrações do banco
│   └── versions/
├── scripts/
│   └── povoar.py            povoamento inicial
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```

## Entidades

| Entidade | Descrição | Principais atributos |
|---|---|---|
| Categoria | Agrupa produtos | nome (único), descrição |
| Fornecedor | Quem vende para a distribuidora | nome, CNPJ (único), e-mail, telefone, ativo |
| Produto | Mercadoria comercializada | código (único), nome, preço, estoque mínimo, ativo, categoria |
| CaracteristicaProduto | Dados de armazenamento do produto | peso, dimensões, unidade, condição de armazenamento, perecível |
| Armazém | Depósito | nome (único), cidade, endereço, ativo |
| EstoqueArmazem | Saldo de um produto em um armazém | quantidade (nunca negativa) |
| PedidoCompra | Compra feita a um fornecedor | fornecedor, data, status (aberto, parcial, recebido, cancelado) |
| ItemPedidoCompra | Produto e quantidades de um pedido | quantidade pedida, quantidade recebida, preço |
| Movimentacao | Histórico de entradas, saídas e transferências | tipo, produto, quantidade, data e hora, motivo, armazéns de origem e destino, pedido |

## Relacionamentos

| Tipo | Relacionamento |
|---|---|
| 1:1 | Produto e CaracteristicaProduto |
| 1:N | Categoria tem vários Produtos |
| 1:N | Fornecedor tem vários PedidosCompra |
| 1:N | PedidoCompra tem vários ItensPedidoCompra |
| 1:N | Produto tem várias Movimentacoes |
| N:N | Produto e Fornecedor, pela tabela associativa `produto_fornecedor` |
| N:N | Produto e Armazém, pela entidade associativa `EstoqueArmazem` (guarda a quantidade) |

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

## Instalação

### 1. Criar o ambiente virtual

```powershell
git clone https://github.com/Samia8120-coder/Sistema_de_Controle_de_Estoque-DSP.git
cd Sistema_de_Controle_de_Estoque-DSP
python -m venv .venv
.venv\Scripts\activate
```

Se o PowerShell bloquear a ativação, rode uma vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### 2. Instalar as dependências

```powershell
pip install -r requirements.txt
```

### 3. Configurar o banco de dados

A aplicação lê a variável `DATABASE_URL`. Copie o arquivo de exemplo e edite:

```powershell
copy .env.example .env
```

#### PostgreSQL (banco principal)

Com o PostgreSQL instalado, abra o **SQL Shell (psql)** como usuário `postgres` e rode:

```sql
CREATE USER estoque WITH PASSWORD 'estoque123';
CREATE DATABASE estoque_db OWNER estoque;
```

No `.env`:

```
DATABASE_URL=postgresql+psycopg://estoque:estoque123@localhost:5432/estoque_db
```

Formato geral: `postgresql+psycopg://usuario:senha@host:porta/banco`. Se a senha tiver caracteres especiais (`@`, `/`, `:`), eles precisam ser codificados (por exemplo, `@` vira `%40`).

#### SQLite (alternativa, sem instalar nada)

No `.env`:

```
DATABASE_URL=sqlite:///./estoque.db
```

Para trocar de banco, basta mudar essa linha. Nenhuma classe, router ou operação precisa ser alterada.

### 4. Executar as migrações

```powershell
alembic upgrade head
```

Isso cria todas as tabelas. Outros comandos úteis:

| Comando | O que faz |
|---|---|
| `alembic current` | Mostra a versão atual do banco |
| `alembic history` | Lista as migrações |
| `alembic downgrade -1` | Desfaz a última migração |
| `alembic revision --autogenerate -m "descricao"` | Gera uma nova migração a partir dos modelos |

O projeto tem duas migrações. A `0001` cria o esquema inicial. A `0002` é uma alteração estrutural aplicada depois, que adiciona a coluna `telefone` em `fornecedores` e cria o índice `ix_movimentacoes_data_hora`. Ela pode ser aplicada em um banco que já tem dados, sem recriá-lo.

### 5. Povoar o banco

```powershell
python -m scripts.povoar
```

O script cadastra 6 categorias, 7 fornecedores, 4 armazéns, 17 produtos, 7 pedidos de compra (abertos, parciais, recebidos e cancelado) e 33 movimentações. Ele usa as mesmas funções da API, então respeita todas as regras de integridade, e as movimentações têm datas espalhadas nos últimos 45 dias.

Para apagar tudo e povoar de novo (renovando as datas): `python -m scripts.povoar --limpar`.

### 6. Executar a aplicação

```powershell
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Documentação interativa (Swagger): `http://127.0.0.1:8000/docs`
