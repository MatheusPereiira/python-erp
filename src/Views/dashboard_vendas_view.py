from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QGroupBox, QFormLayout, QPushButton, QDateEdit, QComboBox, QScrollArea, QGridLayout
)
from PyQt6.QtCore import QDate, Qt
from sqlalchemy import select, func

from src.Models.models import (
    PedidoVenda,
    PedidoVendaItem,
    Entidade,
    Item,
    TipoEntidadeEnum
)


class DashboardVendasWidget(QWidget):
    def __init__(self, sessao):
        super().__init__()
        self.sessao = sessao
        self.rotulos_kpi = {}
        
        self.setup_ui()
        self.carregar_vendedores()
        self.carregar_clientes()
        self.carregar_dados()

    def setup_ui(self):
        """Configura a interface do usuário"""
        layout_principal = QVBoxLayout(self)

        # Título
        self.rotulo_titulo = QLabel("Dashboard de Vendas")
        self.rotulo_titulo.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 10px; color: #424242;")
        layout_principal.addWidget(self.rotulo_titulo)

        # Filtros
        grupo_filtros = QGroupBox("Filtros")
        layout_filtros = QHBoxLayout(grupo_filtros)

        # Período
        layout_periodo = QFormLayout()
        lbl_periodo = QLabel("Período:")
        
        self.data_inicio = QDateEdit()
        self.data_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.data_inicio.setCalendarPopup(True)
        
        self.data_fim = QDateEdit()
        self.data_fim.setDate(QDate.currentDate())
        self.data_fim.setCalendarPopup(True)
        
        layout_periodo_h = QHBoxLayout()
        layout_periodo_h.addWidget(self.data_inicio)
        layout_periodo_h.addWidget(QLabel("até"))
        layout_periodo_h.addWidget(self.data_fim)
        
        layout_periodo.addRow(lbl_periodo, layout_periodo_h)
        layout_filtros.addLayout(layout_periodo)

        # Vendedor
        form_vendedor = QFormLayout()
        self.combo_vendedor = QComboBox()
        self.combo_vendedor.addItem("Todos os Vendedores", None)
        form_vendedor.addRow(QLabel("Vendedor:"), self.combo_vendedor)
        layout_filtros.addLayout(form_vendedor)

        # Cliente
        form_cliente = QFormLayout()
        self.combo_cliente = QComboBox()
        self.combo_cliente.addItem("Todos os Clientes", None)
        form_cliente.addRow(QLabel("Cliente:"), self.combo_cliente)
        layout_filtros.addLayout(form_cliente)

        # Botões
        btn_atualizar = QPushButton("Atualizar")
        btn_atualizar.clicked.connect(self.carregar_dados)
        
        btn_limpar = QPushButton("Limpar")
        btn_limpar.clicked.connect(self.limpar_filtros)
        
        layout_botoes = QVBoxLayout()
        layout_botoes.addWidget(btn_atualizar)
        layout_botoes.addWidget(btn_limpar)
        
        layout_filtros.addLayout(layout_botoes)
        layout_principal.addWidget(grupo_filtros)

        # KPIs em Grid
        self.setup_kpis(layout_principal)
        
        layout_principal.addStretch()

    def setup_kpis(self, layout_principal):
        """Configura a seção de KPIs"""
        area_scroll = QScrollArea()
        area_scroll.setWidgetResizable(True)
        
        widget_conteudo = QWidget()
        self.layout_kpi = QGridLayout(widget_conteudo)
        self.layout_kpi.setSpacing(10)

        area_scroll.setWidget(widget_conteudo)
        layout_principal.addWidget(area_scroll)

        self.configurar_cartoes_kpi()

    def criar_cartao_kpi(self, titulo, valor, cor):
        """Cria um cartão de KPI simples"""
        grupo = QGroupBox()
        grupo.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {cor};
                border-radius: 5px;
                margin: 5px;
                background-color: white;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(grupo)
        
        rotulo_titulo = QLabel(titulo)
        rotulo_titulo.setStyleSheet("font-size: 10pt; color: #555;")

        rotulo_valor = QLabel(valor)
        rotulo_valor.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {cor};")
        rotulo_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(rotulo_titulo)
        layout.addWidget(rotulo_valor)

        return grupo, rotulo_valor

    def configurar_cartoes_kpi(self):
        """Configura todos os cartões de KPI"""
        # KPIs principais
        cartao1, self.rotulos_kpi['total_vendas'] = self.criar_cartao_kpi("Total Vendas", "R$ 0,00", "#28a745")
        self.layout_kpi.addWidget(cartao1, 0, 0)

        cartao2, self.rotulos_kpi['total_pedidos'] = self.criar_cartao_kpi("Total Pedidos", "0", "#007bff")
        self.layout_kpi.addWidget(cartao2, 0, 1)

        cartao3, self.rotulos_kpi['ticket_medio'] = self.criar_cartao_kpi("Ticket Médio", "R$ 0,00", "#6f42c1")
        self.layout_kpi.addWidget(cartao3, 0, 2)

        cartao4, self.rotulos_kpi['clientes_ativos'] = self.criar_cartao_kpi("Clientes Ativos", "0", "#fd7e14")
        self.layout_kpi.addWidget(cartao4, 1, 0)

    def carregar_vendedores(self):
        try:
            self.combo_vendedor.clear()
            self.combo_vendedor.addItem("Todos os Vendedores", None)

            vendedores = self.sessao.execute(
                select(Entidade).where(
                    Entidade.tipo_entidade == TipoEntidadeEnum.VENDEDOR,
                    Entidade.ativo == True
            )
            ).scalars().all()

            for vendedor in vendedores:
                nome = self.obter_nome_entidade(vendedor)
                self.combo_vendedor.addItem(nome, vendedor.id)

        except Exception as e:
            print(f"Erro ao carregar vendedores: {e}")


    def carregar_clientes(self):
        try:
            self.combo_cliente.clear()
            self.combo_cliente.addItem("Todos os Clientes", None)

            clientes = self.sessao.execute(
                select(Entidade).where(
                    Entidade.tipo_entidade == TipoEntidadeEnum.CLIENTE,
                    Entidade.ativo == True
                )
            ).scalars().all()

            for cliente in clientes:
                nome = self.obter_nome_entidade(cliente)
                self.combo_cliente.addItem(nome, cliente.id)

        except Exception as e:
            print(f"Erro ao carregar clientes: {e}")


    def obter_nome_entidade(self, entidade):
        """Obtém o nome apropriado para uma entidade"""
        return (getattr(entidade, "nome_fantasia", None) or 
                getattr(entidade, "razao_social", None) or 
                "Nome não informado")

    def limpar_filtros(self):
        """Limpa todos os filtros para os valores padrão"""
        self.data_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.data_fim.setDate(QDate.currentDate())
        self.combo_vendedor.setCurrentIndex(0)
        self.combo_cliente.setCurrentIndex(0)
        self.carregar_dados()

    def carregar_dados(self):
        """Carrega e exibe os dados do dashboard"""
        try:
            data_inicio = self.data_inicio.date().toPyDate()
            data_fim = self.data_fim.date().toPyDate()
            
            if data_inicio > data_fim:
                QMessageBox.warning(self, "Aviso", "Data inicial não pode ser maior que data final")
                return

            # Consulta principal para vendas
            query = (
                select(
                    func.count(PedidoVenda.id.distinct()).label("quantidade_pedidos"),
                    func.coalesce(func.sum(PedidoVendaItem.preco_total), 0).label("total_vendas")
                )
                .select_from(PedidoVenda)
                .join(PedidoVendaItem, PedidoVendaItem.pedido_id == PedidoVenda.id)
                .where(PedidoVenda.data_emissao >= data_inicio)
                .where(PedidoVenda.data_emissao <= data_fim)
            )

            # Aplicar filtros
            vendedor_id = self.combo_vendedor.currentData()
            if vendedor_id:
                query = query.where(PedidoVenda.vendedor_id == vendedor_id)

            cliente_id = self.combo_cliente.currentData()
            if cliente_id:
                query = query.where(PedidoVenda.cliente_id == cliente_id)

            resultado = self.sessao.execute(query).one()
            
            quantidade_pedidos = int(getattr(resultado, "quantidade_pedidos", 0) or 0)
            total_vendas = float(getattr(resultado, "total_vendas", 0) or 0.0)
            ticket_medio = total_vendas / quantidade_pedidos if quantidade_pedidos > 0 else 0.0

            # Clientes ativos
            clientes_ativos = self.sessao.execute(
                select(func.count(PedidoVenda.cliente_id.distinct()))
                .where(PedidoVenda.data_emissao >= data_inicio)
                .where(PedidoVenda.data_emissao <= data_fim)
            ).scalar_one() or 0

            # Atualizar interface
            self.rotulos_kpi['total_vendas'].setText(f"R$ {total_vendas:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
            self.rotulos_kpi['total_pedidos'].setText(f"{quantidade_pedidos}")
            self.rotulos_kpi['ticket_medio'].setText(f"R$ {ticket_medio:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
            self.rotulos_kpi['clientes_ativos'].setText(f"{clientes_ativos}")
            
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao carregar dados: {e}")