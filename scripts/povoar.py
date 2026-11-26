import sys
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select

from app.crud import armazem as crud_armazem
from app.crud import categoria as crud_categoria
from app.crud import fornecedor as crud_fornecedor
from app.crud import produto as crud_produto
from app.database import SessionLocal
from app.models import (
    Armazem,
    CaracteristicaProduto,
    Categoria,
    EstoqueArmazem,
    Fornecedor,
    ItemPedidoCompra,
    Movimentacao,
    PedidoCompra,
    Produto,
    produto_fornecedor,
)
from app.schemas.armazem import ArmazemCreate
from app.schemas.categoria import CategoriaCreate
from app.schemas.fornecedor import FornecedorCreate
from app.schemas.movimentacao import SaidaIn, TransferenciaIn
from app.schemas.pedido_compra import (
    ItemPedidoIn,
    ItemRecebimento,
    PedidoCreate,
    RecebimentoIn,
)
from app.schemas.produto import CaracteristicaIn, ProdutoCreate
from app.services import movimentacao_service, pedido_service


def dias_atras(dias: int) -> datetime:
    return datetime.now() - timedelta(days=dias, hours=2)


def limpar_banco(db) -> None:
    for modelo in (Movimentacao, ItemPedidoCompra, PedidoCompra, EstoqueArmazem):
        db.execute(delete(modelo))
    db.execute(delete(produto_fornecedor))
    for modelo in (CaracteristicaProduto, Produto, Fornecedor, Armazem, Categoria):
        db.execute(delete(modelo))
    db.commit()
    print("Banco limpo.")


CATEGORIAS = [
    ("Alimentos", "Alimentos não perecíveis"),
    ("Bebidas", "Refrigerantes, águas e sucos"),
    ("Limpeza", "Produtos de limpeza doméstica"),
    ("Higiene Pessoal", "Sabonetes, cremes dentais e afins"),
    ("Papelaria", "Material escolar e de escritório"),
    ("Utilidades Domésticas", "Itens para casa"),
]

FORNECEDORES = [
    ("Distribuidora Nordeste Alimentos Ltda", "12345678000190", "vendas@nordestealimentos.com.br", True),
    ("Bebidas Ceará S.A.", "23456789000101", "comercial@bebidasceara.com.br", True),
    ("Limpeza Total Indústria", "34567890000112", "contato@limpezatotal.com.br", True),
    ("Papelaria Central Atacado", "45678901000123", "atacado@papelariacentral.com.br", True),
    ("Casa & Cia Utilidades", "56789012000134", "pedidos@casaecia.com.br", True),
    ("Atacado Regional de Mantimentos", "67890123000145", "compras@atacadoregional.com.br", True),
    ("Fornecedor Desativado Ltda", "78901234000156", None, False),
]

ARMAZENS = [
    ("Armazém Central", "Quixadá", "Av. Plácido Castelo, 1000", True),
    ("Depósito Fortaleza", "Fortaleza", "Rua do Comércio, 250", True),
    ("Depósito Sobral", "Sobral", "Rodovia CE-362, km 5", True),
    ("Depósito Antigo", "Quixadá", "Rua Velha, 12", False),
]

# codigo, nome, categoria, preço, mínimo, fornecedores, (peso, altura, largura, prof, unidade, condição, perecível)
PRODUTOS = [
    ("ALI-001", "Arroz Branco 5kg", "Alimentos", "27.90", 100, ["Nordeste", "Regional"], (5, 30, 20, 10, "PCT", "seco", False)),
    ("ALI-002", "Feijão Carioca 1kg", "Alimentos", "8.50", 80, ["Nordeste", "Regional"], (1, 22, 14, 6, "PCT", "seco", False)),
    ("ALI-003", "Açúcar Refinado 1kg", "Alimentos", "4.80", 60, ["Nordeste"], (1, 22, 12, 7, "PCT", "seco", False)),
    ("ALI-004", "Óleo de Soja 900ml", "Alimentos", "7.20", 50, ["Nordeste"], (0.9, 24, 7, 7, "UN", "seco", False)),
    ("ALI-005", "Macarrão Espaguete 500g", "Alimentos", "4.10", 60, ["Nordeste"], (0.5, 28, 10, 4, "PCT", "seco", False)),
    ("BEB-001", "Refrigerante Cola 2L", "Bebidas", "9.90", 150, ["Bebidas"], (2.1, 32, 10, 10, "UN", "ambiente", False)),
    ("BEB-002", "Água Mineral 1,5L", "Bebidas", "3.20", 100, ["Bebidas"], (1.5, 30, 9, 9, "UN", "ambiente", False)),
    ("BEB-003", "Suco de Laranja 1L", "Bebidas", "6.40", 50, ["Bebidas"], (1.0, 24, 8, 8, "UN", "refrigerado", True)),
    ("LIM-001", "Detergente Líquido 500ml", "Limpeza", "2.60", 100, ["Limpeza", "Regional"], (0.5, 20, 6, 4, "UN", "seco", False)),
    ("LIM-002", "Água Sanitária 2L", "Limpeza", "6.90", 60, ["Limpeza"], (2.0, 30, 10, 10, "UN", "seco", False)),
    ("LIM-003", "Desinfetante Pinho 1L", "Limpeza", "7.50", 60, ["Limpeza"], (1.0, 26, 8, 8, "UN", "seco", False)),
    ("HIG-001", "Sabonete 90g", "Higiene Pessoal", "1.90", 100, ["Limpeza", "Regional"], (0.09, 3, 6, 9, "UN", "seco", False)),
    ("HIG-002", "Creme Dental 90g", "Higiene Pessoal", "3.80", 80, ["Limpeza"], (0.09, 4, 4, 17, "UN", "seco", False)),
    ("PAP-001", "Caderno 96 Folhas", "Papelaria", "12.50", 100, ["Papelaria"], (0.3, 27, 20, 1, "UN", "seco", False)),
    ("PAP-002", "Caneta Esferográfica Azul", "Papelaria", "1.20", 100, ["Papelaria"], (0.01, 15, 1, 1, "UN", "seco", False)),
    ("UTI-001", "Vassoura de Pelo", "Utilidades Domésticas", "15.90", 20, ["Casa"], (0.6, 120, 28, 8, "UN", "seco", False)),
    ("ALI-099", "Enlatado Linha Descontinuada", "Alimentos", "5.00", 0, ["Nordeste"], (0.4, 10, 7, 7, "UN", "seco", False)),
]


def povoar(db) -> None:
    categorias = {}
    for nome, descricao in CATEGORIAS:
        categorias[nome] = crud_categoria.criar(db, CategoriaCreate(nome=nome, descricao=descricao))

    fornecedores = {}
    for nome, cnpj, email, ativo in FORNECEDORES:
        fornecedor = crud_fornecedor.criar(
            db, FornecedorCreate(nome=nome, cnpj=cnpj, email=email, ativo=ativo)
        )
        fornecedores[nome.split()[0]] = fornecedor
    fornecedores["Nordeste"] = fornecedores["Distribuidora"]
    fornecedores["Regional"] = fornecedores["Atacado"]

    armazens = {}
    for nome, cidade, endereco, ativo in ARMAZENS:
        armazens[nome] = crud_armazem.criar(
            db, ArmazemCreate(nome=nome, cidade=cidade, endereco=endereco, ativo=ativo)
        )
    central = armazens["Armazém Central"].id
    fortaleza = armazens["Depósito Fortaleza"].id
    sobral = armazens["Depósito Sobral"].id

    produtos = {}
    for codigo, nome, categoria, preco, minimo, forn, caract in PRODUTOS:
        peso, altura, largura, prof, unidade, condicao, perecivel = caract
        produtos[codigo] = crud_produto.criar(
            db,
            ProdutoCreate(
                codigo=codigo,
                nome=nome,
                preco_unitario=preco,
                estoque_minimo=minimo,
                categoria_id=categorias[categoria].id,
                ativo=(codigo != "ALI-099"),
                fornecedores_ids=[fornecedores[f].id for f in forn],
                caracteristica=CaracteristicaIn(
                    peso_kg=peso, altura_cm=altura, largura_cm=largura,
                    profundidade_cm=prof, unidade_medida=unidade,
                    condicao_armazenamento=condicao, perecivel=perecivel,
                ),
            ),
        )

    def pid(codigo: str) -> int:
        return produtos[codigo].id

    def pedido(fornecedor: str, itens: list[tuple[str, int]], dias: int, obs: str):
        criado = pedido_service.criar_pedido(
            db,
            PedidoCreate(
                fornecedor_id=fornecedores[fornecedor].id,
                observacao=obs,
                itens=[ItemPedidoIn(produto_id=pid(c), quantidade=q) for c, q in itens],
            ),
        )
        criado.data_pedido = dias_atras(dias + 3)
        db.commit()
        return criado.id

    def receber(pedido_id: int, armazem_id: int, itens: list[tuple[str, int]], dias: int):
        movimentacao_service.receber_pedido(
            db,
            pedido_id,
            RecebimentoIn(
                armazem_id=armazem_id,
                itens=[ItemRecebimento(produto_id=pid(c), quantidade=q) for c, q in itens],
            ),
            data_hora=dias_atras(dias),
        )

    def saida(codigo: str, armazem_id: int, qtd: int, dias: int, motivo: str = "venda a cliente"):
        movimentacao_service.registrar_saida(
            db,
            SaidaIn(produto_id=pid(codigo), armazem_id=armazem_id, quantidade=qtd, motivo=motivo),
            data_hora=dias_atras(dias),
        )

    def transferir(codigo: str, origem: int, destino: int, qtd: int, dias: int):
        movimentacao_service.registrar_transferencia(
            db,
            TransferenciaIn(
                produto_id=pid(codigo), armazem_origem_id=origem,
                armazem_destino_id=destino, quantidade=qtd,
            ),
            data_hora=dias_atras(dias),
        )

    p1 = pedido("Nordeste", [("ALI-001", 200), ("ALI-002", 150), ("ALI-003", 100), ("ALI-004", 120), ("ALI-005", 180)], 40, "Reposição mensal de alimentos")
    p2 = pedido("Bebidas", [("BEB-001", 300), ("BEB-002", 400), ("BEB-003", 100)], 35, "Reposição de bebidas")
    p3 = pedido("Limpeza", [("LIM-001", 250), ("LIM-002", 120), ("LIM-003", 90), ("HIG-001", 200), ("HIG-002", 150)], 45, "Limpeza e higiene")
    p4 = pedido("Papelaria", [("PAP-001", 200), ("PAP-002", 100)], 20, "Volta às aulas")
    pedido("Casa", [("UTI-001", 60)], 5, "Pedido de vassouras aguardando entrega")
    p6 = pedido("Regional", [("ALI-001", 100), ("ALI-002", 80)], 10, "Complemento de arroz e feijão")
    p7 = pedido("Papelaria", [("PAP-001", 50)], 15, "Pedido cancelado por mudança de planejamento")
    pedido_service.cancelar_pedido(db, p7)

    receber(p1, central, [("ALI-001", 200), ("ALI-002", 150), ("ALI-003", 100), ("ALI-004", 120), ("ALI-005", 180)], 40)
    receber(p2, fortaleza, [("BEB-001", 300), ("BEB-002", 400), ("BEB-003", 100)], 35)
    receber(p3, central, [("LIM-001", 250), ("LIM-002", 120), ("LIM-003", 90), ("HIG-001", 200), ("HIG-002", 150)], 45)
    receber(p4, sobral, [("PAP-001", 120), ("PAP-002", 100)], 20)
    receber(p6, fortaleza, [("ALI-001", 100), ("ALI-002", 30)], 10)

    saida("ALI-001", central, 60, 25)
    saida("ALI-002", central, 40, 20)
    saida("BEB-001", fortaleza, 120, 15)
    saida("LIM-001", central, 70, 18)
    transferir("ALI-001", central, fortaleza, 50, 14)
    saida("ALI-001", central, 30, 12)
    saida("BEB-003", fortaleza, 60, 11)
    saida("PAP-001", sobral, 50, 8)
    transferir("BEB-001", fortaleza, sobral, 100, 7)
    saida("LIM-003", central, 40, 9)
    transferir("LIM-001", central, sobral, 60, 6)
    saida("BEB-001", fortaleza, 50, 5)
    saida("BEB-002", fortaleza, 150, 3)
    transferir("ALI-002", central, fortaleza, 40, 2)
    saida("PAP-002", sobral, 30, 4)
    saida("LIM-001", sobral, 20, 1, motivo="consumo interno")


def main() -> None:
    db = SessionLocal()
    try:
        if "--limpar" in sys.argv:
            limpar_banco(db)

        if db.scalar(select(func.count(Categoria.id))):
            print("O banco já possui dados. Rode com --limpar para apagar e povoar de novo.")
            return

        povoar(db)

        print("Povoamento concluído:")
        for nome, modelo in [
            ("categorias", Categoria), ("fornecedores", Fornecedor), ("armazéns", Armazem),
            ("produtos", Produto), ("pedidos de compra", PedidoCompra),
            ("movimentações", Movimentacao), ("saldos por armazém", EstoqueArmazem),
        ]:
            print(f"  {nome}: {db.scalar(select(func.count()).select_from(modelo))}")
    finally:
        db.close()


if __name__ == "__main__":
    main()