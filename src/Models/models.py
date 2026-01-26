from sqlalchemy import (create_engine, Column, Integer, String, Date, Boolean, Numeric,
                        ForeignKey, Enum, Text, DateTime, CheckConstraint, func, DECIMAL)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()

# --- ENUMS ---
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

# --- MODELOS ---

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
    tipo_entidade = Column(String(50)) # Ex: CLIENTE, FORNECEDOR, AMBOS
    esta_bloqueado = Column(Boolean, default=False)
    contatos = relationship("Contato", back_populates="entidade")
    # Relacionamentos adicionados para compatibilidade
    itens_fornecidos = relationship("Item", back_populates="fornecedor")

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
    ativo = Column(Boolean, default=True)

# NOTA: Removemos a classe 'Fornecedor' separada. Usaremos 'Entidade'.

class Item(Base):
    __tablename__ = "itens"

    id = Column(Integer, primary_key=True, autoincrement=True)

    codigo_item = Column(String(50), unique=True, nullable=False)
    tipo_item = Column(String(10), default="PRODUTO", nullable=False)

    nome = Column(String(100), nullable=False)
    descricao = Column(Text)

    estoque = Column(Numeric(10, 2), default=0)
    estoque_minimo = Column(Numeric(10, 2), default=0)

    custo_unitario = Column(Numeric(10, 2), nullable=False, default=0)
    preco_venda = Column(Numeric(10, 2), nullable=False, default=0)

    ativo = Column(Boolean, default=True)

  
    data_cadastro = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    fornecedor_id = Column(Integer, ForeignKey("entidade.id"))
    fornecedor = relationship(
        "Entidade",
        back_populates="itens_fornecidos"
    )
    
    # CORREÇÃO: Aponta para Entidade agora
    fornecedor_id = Column(Integer, ForeignKey("entidade.id")) 
    fornecedor = relationship("Entidade", back_populates="itens_fornecidos")
    
    movimentos_estoque = relationship("MovimentoEstoque", back_populates="item")

class MovimentoEstoque(Base):
    __tablename__ = "movimento_estoque"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("itens.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    
    # Campos obrigatórios que mantivemos para compatibilidade
    preco_venda = Column(Numeric(10, 2), default=0)
    preco_compra = Column(Numeric(10, 2), default=0)
    estoque_minimo = Column(Integer, default=0)
    estoque_maximo = Column(Integer, default=0)
    
    # CORREÇÃO: Aponta para Entidade
    fornecedor_id = Column(Integer, ForeignKey("entidade.id"), nullable=True)
    
    data_ultima_mov = Column(Date, nullable=False, server_default=func.current_date())
    tipo_movimento = Column(String(10), nullable=False)
    observacao = Column(Text)

    item = relationship("Item", back_populates="movimentos_estoque")
    fornecedor = relationship("Entidade")

class PedidoVenda(Base):
    __tablename__ = "pedido_vendas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, nullable=True)
    vendedor_id = Column(Integer, nullable=True)
    preco_total = Column(Numeric(10, 2)) # Unificado nome
    data_emissao = Column(Date)
    status = Column(String(20))
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
    preco_total = Column(Numeric(10, 2))
    data_emissao = Column(Date)
    status = Column(String(20))
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
    tipo_lancamento = Column(String(1), nullable=False) # 'P' ou 'R'
    origem = Column(String(1), nullable=False)          # 'C' ou 'V'
    
    pedido_compra_id = Column(Integer, ForeignKey("pedido_compras.id"), nullable=True)
    pedido_venda_id = Column(Integer, ForeignKey("pedido_vendas.id"), nullable=True)
    
    # Ambos apontam para Entidade
    cliente_id = Column(Integer, ForeignKey("entidade.id"), nullable=True)
    fornecedor_id = Column(Integer, ForeignKey("entidade.id"), nullable=True)
    
    descricao = Column(String(255), nullable=False)
    valor_nota = Column(Numeric(10, 2), nullable=False)
    vencimento = Column(Date, nullable=False)
    status = Column(Enum(EnumStatus), nullable=False, default=EnumStatus.ABERTA)
    data_emissao = Column(Date, nullable=False, server_default=func.current_date())


# ==========================================================
# CONEXÃO COM O BANCO (SQLite LOCAL)
# ==========================================================

engine = create_engine(
    "sqlite:///erp.db",
    echo=False,
    future=True
)

Base.metadata.create_all(engine)

from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine)

def criar_admin_padrao():
    session = SessionLocal()

    # Criar TODOS os perfis, se não existirem
    perfis_existentes = {
        p.cargo for p in session.query(Perfil).all()
    }

    for cargo in CargoPerfilEnum:
        if cargo not in perfis_existentes:
            session.add(Perfil(cargo=cargo))

    session.commit()

    # Criar usuário admin se não existir
    admin_existente = session.query(Usuario).filter_by(login="ADMIN").first()
    if admin_existente:
        session.close()
        return

    perfil_admin = session.query(Perfil).filter_by(
        cargo=CargoPerfilEnum.ADMINISTRADOR
    ).first()

    usuario_admin = Usuario(
        nome="Administrador",
        login="ADMIN",
        senha_hash="123",
        perfil_id=perfil_admin.id
    )

    session.add(usuario_admin)
    session.commit()
    session.close()

    print("✅ Perfis criados e usuário admin disponível")


criar_admin_padrao()
