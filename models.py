from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, Numeric, ForeignKey
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()

class Entidade(Base):
    __tablename__ = 'entidades'

    id = Column(Integer,primary_key = True)
    tipo_pessoa = Column(String)
    razao_social = Column(String)
    nome_fantasia = Column(String)
    inscricao_estadual = Column(String)
    observacao = Column(String)
    esta_bloqueado = Column(Boolean)
    cpf_cnpj = Column(String)
    tipo_entidade = Column(Enum) #CRIAR A CLASSE ENUM RELACIONADA
    contado_id = Column(Integer,ForeignKey)

class Contato(Base):
    __tablename__ = 'contatos'

    id = Column(Integer,primary_key = True)
    entidade_id = Column(Integer,ForeignKey)
    telefone_primario = Column(String)
    telefone_secundario = Column(String)
    email = Column(String)
    logradouro = Column(String)
    numero = Column(String)
    complemento = Column(String)
    bairro = Column(String)
    cidade = Column(String)
    cep = Column(String)
    uf = Column(String)

class CondicaoDePagemento(Base):
    __tablename__ = 'condicoes_pagamento'

    id = Column(Integer,primary_key = True)
    descricao = Column(String)
    numero_parcelas = Column(Integer)
    intervalo_dias = Column(Integer)
    primeira_parcela = Column(Integer)
    desconto = Column(Numeric(10,2))
    juros = Column(Numeric(10,2))
    multa = Column(Numeric(10,2))
    ativo = Column(Boolean)

class CargoEnum(enum.Enum):
    ADMINISTRADOR = "administrador"
    FINANCEIRO = "financeiro"
    VENDAS = "vendas"
    COMPRAS = "compras"
    ESTOQUE = "estoque"
    TECNICO = "tecnico"

class Perfil(Base):
    __tablename__= "perfis"

    id = Column(Integer, primary_key=True)
    cargo = Column(enum(CargoEnum), nullable=False)

class Usuario(Base):
    __tablename__= "usuarios"

    id = Column(Integer, primary_key=True)
    nome= Column(String)
    login= Column(String)
    senha_hash= Column(String)
    perfil_id= Column(Integer, ForeignKey)

class CadastroProduto(Base):
    __tablename__='cadastro_produtos'


    id =Column(Integer,primary_key=True)
    Produto = Column (String (100))
    PrecoUnitario =Column(Numeric (10,2))
    Estoque = Column (Integer)

class Item(Base):
    __tablename__ = 'itens'

    id = Column(Integer, primary_key=True)
    codigo_item = Column(String)
    tipo_item = Column(String)
    nome = Column(String)
    descricao = Column(String)
    estoque = Column(Numeric)
    estoque_minimo = Column(Numeric)
    custo_unitario = Column(Numeric)
    preco_venda = Column(Numeric)
    fornececedor = Column(Integer, ForeignKey)
    categoria_id = Column(Integer, ForeignKey)
    marca_id = Column(Integer, ForeignKey)
    unidade_de_medida = Column(Integer, ForeignKey)
    ativo = Column(Boolean)
    data_cadastro = Column(Date)

class Categoria(Base):
    __tablename__ = 'categorias'

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    descricao = (String)
    ativo = Column(Boolean)

class Marca(Base):
    __tablename__ = 'marcas'

    id = Column(Integer, primary_key=True)
    nome_marca = Column(String)
    ativa = Column(Boolean)
    obs = Column(String)
    nome_foto = Column(String)

class UnidadeMedida(Base):
    __tablename__ = 'unidades_medida'

    id = Column(Integer, primary_key=True)
    descricao = Column(String)

class TabelaPreco(Base):
    __tablename__='tabela_precos'

    id =Column(Integer,primary_key=True)
    Produto = Column (String (100))
    Estoque = Column (Integer)
    Peso = Column(Numeric(10, 2))
    Preco_Unitario = Column(Numeric(10, 2))
    Vencimento = Column(Date)

class PedidoVenda(Base):
    __tablename__='pedido_vendas'

    id =Column(Integer,primary_key=True)
    Cliente_Id = Column(Integer)
    Vendedor_Id = Column (Integer)
    Produto = Column (String (100))
    Data_Emissao = Column (Date)
    Data_Entrada = Column (Date)
    Data_Vencimento = Column (Date)
    Quantidade = Column (Integer)
    Preco_Unitario = Column (Numeric(10, 2))
    Preco_Total = Column (Numeric(10, 2))
    Status = Column (String (20))
    Peso = Column (Numeric(10, 2))

class PedidoVendaItem(Base):
    __tablename__='pedido_vendas_itens'

    id =Column(Integer,primary_key=True)
    Pedido_Id = Column(Integer, ForeignKey('pedido_vendas.id'))
    Produto = Column (String (100))
    Quantidade = Column (Integer)
    Preco_Unitario = Column (Numeric(10, 2))
    Preco_Total = Column (Numeric(10, 2))

class PedidoCompra(Base):
    __tablename__='pedido_compras'

    id =Column(Integer,primary_key=True)
    Cliente_Id = Column(Integer)
    Vendedor_Id = Column (Integer)
    Produto = Column (String (100))
    Data_Emissao = Column (Date)
    Data_Entrada = Column (Date)
    Data_Vencimento = Column (Date)
    Quantidade = Column (Integer)
    Preco_Unitario = Column (Numeric(10, 2))
    Preco_Total = Column (Numeric(10, 2))
    Peso = Column (Numeric(10, 2))

class PedidoCompraItem(Base):
    __tablename__='pedido_compras_itens'
    
    id =Column(Integer,primary_key=True)
    Pedido_Id = Column(Integer, ForeignKey('pedido_compras.id'))
    Quantidade = Column (Integer)
    Preco_Unitario = Column (Numeric(10, 2))
    Preco_Total = Column (Numeric(10, 2))

class EnumStatus(enum.Enum):
  Aberta = "aberta"
  Paga = "paga"
  Atrasada = "atrasada"
  
class MovimentoEstoque(Base):
    __tablename__ = 'movimento_estoque'

    id = Column(Integer, ForeignKey, primary_key=True, autoincrement=True)
    id_produto = Column(Integer, ForeignKey, nullable=False)
    quantidade = Column(Integer, ForeignKey, nullable=False)
    preco_venda = Column(Numeric(10, 2), ForeignKey, nullable=False)
    preco_compra = Column(Numeric(10, 2), ForeignKey, nullable=False)
    id_fornecedor = Column(Integer, ForeignKey, nullable=False)
    estoque_minimo = Column(Integer, ForeignKey, nullable=False)
    estoque_maximo = Column(Integer, ForeignKey, nullable=False)
    data_ultima_mov = Column(Date, ForeignKey, nullable=False)

class Financeiro(Base):
    __tablename__ = 'financeiro'

    id = Column(Integer, ForeignKey, primary_key=True, autoincrement=True)
    tipo_lancamento = Column(String(1), ForeignKey, nullable=False)
    origem = Column(String(1), ForeignKey, nullable=False)
    id_pedido_compra = Column(Integer, ForeignKey, nullable=True)
    id_pedido_venda = Column(Integer, ForeignKey, nullable=True)
    id_cliente = Column(Integer, ForeignKey, nullable=True)
    id_fornecedor = Column(Integer, ForeignKey, nullable=True)
    id_vendedor = Column(Integer, ForeignKey, nullable=True)
    id_transportadora = Column(Integer, ForeignKey, nullable=True)
    condicao_pagamento_id = Column(String, ForeignKey, nullable=False)
    descricao = Column(String, ForeignKey(255), nullable=False)
    valor_nota = Column(Numeric, ForeignKey(10,2), nullable=False)
    vencimento = Column(Date, ForeignKey, nullable=False)
    status = Column(String(8), ForeignKey, nullable=False, default=EnumStatus.Aberta.value)
