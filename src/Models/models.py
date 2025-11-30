from sqlalchemy import (create_engine, Column, Integer, String, Date, Boolean, Numeric,
                        ForeignKey, Enum, Text, DateTime, CheckConstraint, func, DECIMAL)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()

# ENUMS


class CargoPerfilEnum(enum.Enum):
    ADMINISTRADOR = "ADMINISTRADOR" 
    FINANCEIRO = "FINANCEIRO"
    VENDAS = "VENDAS"
    COMPRAS = "COMPRAS"
    ESTOQUE = "ESTOQUE"
    TECNICO = "TECNICO"


class TipoPessoaEnum(enum.Enum):
    FISICA = "FISICA"
    JURIDICA = "JURIDICA"


class EnumStatus(enum.Enum):
    ABERTA = "aberta"
    PAGA = "paga"
    CANCELADA = "cancelada"

# MODELOS

class Perfil(Base):
    __tablename__ = "perfil"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cargo = Column(Enum(CargoPerfilEnum), nullable=False)

    usuarios = relationship("Usuario", back_populates="perfil")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    login = Column(String(50), nullable=False, unique=True)
    senha_hash = Column(String(255), nullable=False)
    perfil_id = Column(Integer, ForeignKey("perfil.id"), nullable=False)

    perfil = relationship("Perfil", back_populates="usuarios")


class Entidade(Base):
    __tablename__ = "entidade"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo_pessoa = Column(Enum(TipoPessoaEnum))
    razao_social = Column(String(100))
    nome_fantasia = Column(String(100))
    inscricao_estadual = Column(String(16))
    cpf_cnpj = Column(String(20))
    obs = Column(Text)
    tipo_entidade = Column(String(50))
    esta_bloqueado = Column(Boolean, default=False)

    contatos = relationship("Contato", back_populates="entidade")


class Contato(Base):
    __tablename__ = "contato"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entidade_id = Column(Integer, ForeignKey("entidade.id"), nullable=False)
    telefone_primario = Column(String(20))
    telefone_secundario = Column(String(20))
    email = Column(String(100))
    logradouro = Column(String(100))
    numero = Column(String(20))
    complemento = Column(String(100))
    bairro = Column(String(100))
    cidade = Column(String(100))
    cep = Column(String(10))
    uf = Column(String(2))

    entidade = relationship("Entidade", back_populates="contatos")


class CondicaoDePagamento(Base):
    __tablename__ = "condicoes_de_pagamento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String(100))
    numero_parcelas = Column(Integer, nullable=False)
    intervalo_dias = Column(Integer, nullable=False)
    primeira_parcela = Column(Integer, default=0)
    desconto = Column(DECIMAL(5, 2), default=0)
    juros = Column(DECIMAL(5, 2), default=0)
    multa = Column(DECIMAL(5, 2), default=0)
    ativo = Column(Boolean, default=True)


class Fornecedor(Base):
    __tablename__ = "fornecedor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    cnpj = Column(String(18), unique=True)

    itens = relationship("Item", back_populates="fornecedor")


class Item(Base):
    __tablename__ = "itens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_item = Column(String(50), unique=True)
    tipo_item = Column(String(10), default="PRODUTO")
    nome = Column(String(100))
    estoque = Column(Numeric(10, 2), default=0)
    descricao = Column(Text)
    estoque_minimo = Column(Numeric(10, 2), default=0)
    custo_unitario = Column(Numeric(10, 2), nullable=False, default=0)
    preco_venda = Column(Numeric(10, 2), nullable=False, default=0)
    data_cadastro = Column(DateTime, default=datetime.utcnow)
    ativo = Column(Boolean, default=True)
    fornecedor_id = Column(Integer, ForeignKey("fornecedor.id"))

    fornecedor = relationship("Fornecedor", back_populates="itens")
    movimentos_estoque = relationship("MovimentoEstoque", back_populates="item")


class MovimentoEstoque(Base):
    __tablename__ = "movimento_estoque"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("itens.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_venda = Column(Numeric(10, 2), nullable=False)
    preco_compra = Column(Numeric(10, 2), nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("fornecedor.id"), nullable=False)
    estoque_minimo = Column(Integer, nullable=False, default=0)
    estoque_maximo = Column(Integer, nullable=False, default=0)
    data_ultima_mov = Column(Date, nullable=False, server_default=func.current_date())
    tipo_movimento = Column(String(10), nullable=False)
    observacao = Column(Text)

    __table_args__ = (
        CheckConstraint("tipo_movimento IN ('entrada', 'saida')", name="chk_tipo_movimento"),
    )

    item = relationship("Item", back_populates="movimentos_estoque")
    fornecedor = relationship("Fornecedor")


class PedidoVenda(Base):
    __tablename__ = "pedido_vendas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, nullable=True)
    vendedor_id = Column(Integer, nullable=True)
    produto = Column(String(100))
    data_emissao = Column(Date)
    data_entrada = Column(Date)
    data_vencimento = Column(Date)
    quantidade = Column(Integer)
    preco_unitario = Column(Numeric(10, 2))
    preco_total = Column(Numeric(10, 2))
    status = Column(String(20))
    peso = Column(Numeric(10, 2))

    itens = relationship("PedidoVendaItem", back_populates="pedido")


class PedidoVendaItem(Base):
    __tablename__ = "pedido_vendas_itens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedido_vendas.id"))
    produto = Column(String(100))
    quantidade = Column(Integer)
    preco_unitario = Column(Numeric(10, 2))
    preco_total = Column(Numeric(10, 2))

    pedido = relationship("PedidoVenda", back_populates="itens")


class PedidoCompra(Base):
    __tablename__ = "pedido_compras"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, nullable=True)
    vendedor_id = Column(Integer, nullable=True)
    produto = Column(String(100))
    data_emissao = Column(Date)
    data_entrada = Column(Date)
    data_vencimento = Column(Date)
    quantidade = Column(Integer)
    preco_unitario = Column(Numeric(10, 2))
    preco_total = Column(Numeric(10, 2))
    peso = Column(Numeric(10, 2))

    itens = relationship("PedidoCompraItem", back_populates="pedido")


class PedidoCompraItem(Base):
    __tablename__ = "pedido_compras_itens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedido_compras.id"))
    quantidade = Column(Integer)
    preco_unitario = Column(Numeric(10, 2))
    preco_total = Column(Numeric(10, 2))

    pedido = relationship("PedidoCompra", back_populates="itens")


class Financeiro(Base):
    __tablename__ = "financeiro"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo_lancamento = Column(String(1), nullable=False)  # 'P' = pagar, 'R' = receber
    origem = Column(String(1), nullable=False)            # 'C' = compra, 'V' = venda
    pedido_compra_id = Column(Integer, ForeignKey("pedido_compras.id"))
    pedido_venda_id = Column(Integer, ForeignKey("pedido_vendas.id"))
    cliente_id = Column(Integer, ForeignKey("entidade.id"))
    fornecedor_id = Column(Integer, ForeignKey("entidade.id"))
    condicao_pagamento_id = Column(Integer, ForeignKey("condicoes_de_pagamento.id"))
    descricao = Column(String(255), nullable=False)
    valor_nota = Column(Numeric(10, 2), nullable=False)
    vencimento = Column(Date, nullable=False)
    status = Column(Enum(EnumStatus), nullable=False, default=EnumStatus.ABERTA)
    data_emissao = Column(Date, nullable=False, server_default=func.current_date())

    pedido_compra = relationship("PedidoCompra", backref="lancamentos_financeiros")
    pedido_venda = relationship("PedidoVenda", backref="lancamentos_financeiros")
    cliente = relationship("Entidade", foreign_keys=[cliente_id])
    fornecedor = relationship("Entidade", foreign_keys=[fornecedor_id])
    condicao_pagamento = relationship("CondicaoDePagamento")


# ==========================================================
# CONEXÃO COM O BANCO
# ==========================================================

usuario = "sgcfe_user"
senha = "SGCFE-ES2FANS123%2A"
host = "3.16.180.102"
banco = "SGCFE-ES2FANS"

engine = create_engine(f"postgresql+psycopg2://{usuario}:{senha}@{host}:5432/{banco}")

Base.metadata.create_all(engine)

print("✅ Conexão bem-sucedida e tabelas criadas no PostgreSQL!")

#engine = create_engine('sqlite:///sistema.db')