from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QGroupBox, QFormLayout, QLineEdit, QRadioButton, QScrollArea, QGridLayout,
    QPushButton, QDateEdit, QComboBox
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from sqlalchemy import select, func, and_
from decimal import Decimal

from src.Models.models import PedidoCompra, PedidoCompraItem, Fornecedor
from src.Utils.correcaoDeValores import Converter_decimal, Converter_inteiro


class DashboardComprasWidget(QWidget):
    def __init__(self, sessao):
        super().__init__()
        self.sessao = sessao
        layout_principal = QVBoxLayout(self)

        self.rotulo_titulo = QLabel("Dashboard de Compras")
        self.rotulo_titulo.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 10px; color: #424242;")
        layout_principal.addWidget(self.rotulo_titulo)

        # Filtros
        grupo_filtros = QGroupBox("Filtros do Dashboard de Compras")
        grupo_filtros.setStyleSheet("QGroupBox { border: 1px solid #ccc; margin-top: 10px; padding: 10px; }")
        
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

        # Fornecedor
        layout_fornecedor = QFormLayout()
        lbl_fornecedor = QLabel("Fornecedor:")
        self.combo_fornecedor = QComboBox()
        self.combo_fornecedor.addItem("Todos os Fornecedores", None)
        self.carregar_fornecedores()
        layout_fornecedor.addRow(lbl_fornecedor, self.combo_fornecedor)
        layout_filtros.addLayout(layout_fornecedor)

        # Botões
        layout_botoes = QVBoxLayout()
        self.botao_limpar = QPushButton("🧹 Limpar Filtros")
        self.botao_aplicar = QPushButton("📊 Aplicar Filtros")
        self.botao_aplicar.setStyleSheet("background-color: #E0E0E0; color: #424242; padding: 10px; border-radius: 5px; border: 1px solid #CCCCCC;")
        
        self.botao_limpar.clicked.connect(self.limpar_filtros)
        self.botao_aplicar.clicked.connect(self.carregar_dados)
        
        layout_botoes.addWidget(self.botao_aplicar)
        layout_botoes.addWidget(self.botao_limpar)
        layout_filtros.addLayout(layout_botoes)

        layout_principal.addWidget(grupo_filtros)

        # Área de KPIs
        area_scroll = QScrollArea()
        area_scroll.setWidgetResizable(True)
        widget_conteudo = QWidget()
        self.layout_kpi = QGridLayout(widget_conteudo)

        area_scroll.setWidget(widget_conteudo)
        layout_principal.addWidget(area_scroll)

        self.rotulos_kpi = {}
        self.configurar_cartoes_kpi()

        # Carregar dados iniciais
        self.carregar_dados()

    def carregar_fornecedores(self):
        """Carrega a lista de fornecedores"""
        try:
            fornecedores = self.sessao.execute(select(Fornecedor)).scalars().all()
            
            for fornecedor in fornecedores:
                self.combo_fornecedor.addItem(fornecedor.nome, fornecedor.id)
        except Exception as e:
            print(f"Erro ao carregar fornecedores: {e}")

    def limpar_filtros(self):
        """Limpa todos os filtros"""
        self.data_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.data_fim.setDate(QDate.currentDate())
        self.combo_fornecedor.setCurrentIndex(0)
        self.carregar_dados()

    def criar_cartao_kpi(self, titulo, icone, cor):
        grupo = QGroupBox()
        grupo.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {cor};
                border-radius: 8px;
                margin-top: 10px;
                background-color: #FFFFFF;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(grupo)
        rotulo_titulo = QLabel(f"<b>{icone} {titulo}</b>")
        rotulo_titulo.setStyleSheet("font-size: 10pt; color: #555;")

        rotulo_valor = QLabel("Carregando...")
        rotulo_valor.setStyleSheet(f"font-size: 22pt; font-weight: bold; color: {cor}; margin-top: 5px;")

        layout.addWidget(rotulo_titulo)
        layout.addWidget(rotulo_valor)
        layout.addStretch()

        return grupo, rotulo_valor

    def configurar_cartoes_kpi(self):
        cor_total = "#dc3545"
        cor_pedidos = "#007bff"
        cor_medio = "#6f42c1"
        cor_fornecedores = "#fd7e14"
        cor_produtos = "#e83e8c"
        cor_melhor = "#28a745"

        cartao1, self.rotulos_kpi['total_compras'] = self.criar_cartao_kpi("Total em Compras", "💰", cor_total)
        self.layout_kpi.addWidget(cartao1, 0, 0)

        cartao2, self.rotulos_kpi['total_pedidos'] = self.criar_cartao_kpi("Total de Pedidos", "📦", cor_pedidos)
        self.layout_kpi.addWidget(cartao2, 0, 1)

        cartao3, self.rotulos_kpi['valor_medio'] = self.criar_cartao_kpi("Valor Médio por Pedido", "📊", cor_medio)
        self.layout_kpi.addWidget(cartao3, 0, 2)

        cartao4, self.rotulos_kpi['fornecedores_ativos'] = self.criar_cartao_kpi("Fornecedores Ativos", "🏢", cor_fornecedores)
        self.layout_kpi.addWidget(cartao4, 1, 0)

        cartao5, self.rotulos_kpi['produtos_comprados'] = self.criar_cartao_kpi("Produtos Comprados", "📦", cor_produtos)
        self.layout_kpi.addWidget(cartao5, 1, 1)

        cartao6, self.rotulos_kpi['maior_fornecedor'] = self.criar_cartao_kpi("Maior Fornecedor", "⭐", cor_melhor)
        self.layout_kpi.addWidget(cartao6, 1, 2)

    def carregar_dados(self):
        """Carrega os dados da dashboard"""
        try:
            data_inicio = self.data_inicio.date().toPyDate()
            data_fim = self.data_fim.date().toPyDate()
            fornecedor_id = self.combo_fornecedor.currentData()

            # Query base para pedidos de compra no período
            query_base = select(PedidoCompra).where(
                and_(
                    PedidoCompra.data_emissao >= data_inicio,
                    PedidoCompra.data_emissao <= data_fim
                )
            )

            if fornecedor_id:
                query_base = query_base.where(PedidoCompra.fornecedor_id == fornecedor_id)

            # Executa a query
            pedidos = self.sessao.execute(query_base).scalars().all()

            # Cálculos dos KPIs
            total_compras = sum(pedido.preco_total or 0 for pedido in pedidos)
            total_pedidos = len(pedidos)
            valor_medio = total_compras / total_pedidos if total_pedidos > 0 else 0
            
            # Fornecedores únicos
            fornecedores_unicos = len(set(pedido.fornecedor_id for pedido in pedidos if pedido.fornecedor_id))
            
            # Total de produtos comprados
            total_produtos = self.sessao.execute(
                select(func.sum(PedidoCompraItem.quantidade)).select_from(PedidoCompraItem).join(
                    PedidoCompra, PedidoCompraItem.pedido_id == PedidoCompra.id
                ).where(
                    and_(
                        PedidoCompra.data_emissao >= data_inicio,
                        PedidoCompra.data_emissao <= data_fim
                    )
                )
            ).scalar_one() or 0

            # Maior fornecedor (por valor total)
            maior_fornecedor = "N/A"
            if pedidos:
                fornecedores_total = {}
                for pedido in pedidos:
                    if pedido.fornecedor_id:
                        fornecedores_total[pedido.fornecedor_id] = fornecedores_total.get(pedido.fornecedor_id, 0) + (pedido.preco_total or 0)
                
                if fornecedores_total:
                    maior_fornecedor_id = max(fornecedores_total, key=fornecedores_total.get)
                    # Buscar nome do fornecedor
                    fornecedor = self.sessao.execute(
                        select(Fornecedor).where(Fornecedor.id == maior_fornecedor_id)
                    ).scalar_one_or_none()
                    maior_fornecedor = fornecedor.nome if fornecedor else f"Fornecedor {maior_fornecedor_id}"

            # Atualiza os rótulos
            self.rotulos_kpi['total_compras'].setText(f"R$ {total_compras:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
            self.rotulos_kpi['total_pedidos'].setText(f"{total_pedidos:,}".replace(',', '.'))
            self.rotulos_kpi['valor_medio'].setText(f"R$ {valor_medio:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
            self.rotulos_kpi['fornecedores_ativos'].setText(f"{fornecedores_unicos:,}".replace(',', '.'))
            self.rotulos_kpi['produtos_comprados'].setText(f"{total_produtos:,}".replace(',', '.'))
            self.rotulos_kpi['maior_fornecedor'].setText(maior_fornecedor[:15] + "..." if len(maior_fornecedor) > 15 else maior_fornecedor)

        except Exception as e:
            QMessageBox.critical(self, "Erro no Dashboard de Compras", f"Não foi possível carregar os dados.\nErro: {e}")
            for label in self.rotulos_kpi.values():
                label.setText("ERRO")