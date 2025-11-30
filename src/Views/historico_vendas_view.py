# sistemacomercial/src/Views/historico_vendas_view.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QTableView, QHeaderView, QLineEdit, QComboBox, QDateEdit, QGroupBox,
    QFormLayout, QDialog
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta

from src.Models.models import PedidoVenda, PedidoVendaItem, Entidade
from src.Components.Comercial.filtros_vendas_dialog import FiltroVendasDialog

class HistoricoVendasWidget(QWidget):
    def __init__(self, sessao):
        super().__init__()
        self.sessao = sessao
        self.filtros_atuais = {}
        
        self.setup_ui()
        self.carregar_dados()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("Histórico de Vendas")
        titulo.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 10px; color: #424242;")
        layout_principal.addWidget(titulo)

        # Barra de ferramentas
        toolbar_layout = QHBoxLayout()
        
        # Busca rápida
        self.busca_input = QLineEdit()
        self.busca_input.setPlaceholderText("🔍 Buscar por número do pedido, cliente ou produto...")
        self.busca_input.textChanged.connect(self.carregar_dados)
        toolbar_layout.addWidget(self.busca_input)
        
        # Filtros avançados
        self.btn_filtros = QPushButton("⚙️ Filtros Avançados")
        self.btn_filtros.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                color: #424242;
                font-weight: bold;
                border-radius: 5px;
                border: 1px solid #CCCCCC;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        self.btn_filtros.clicked.connect(self.abrir_filtros)
        toolbar_layout.addWidget(self.btn_filtros)
        
        # Botão atualizar
        self.btn_atualizar = QPushButton("🔄 Atualizar")
        self.btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
        """)
        self.btn_atualizar.clicked.connect(self.carregar_dados)
        toolbar_layout.addWidget(self.btn_atualizar)
        
        layout_principal.addLayout(toolbar_layout)

        # Estatísticas rápidas
        self.setup_estatisticas(layout_principal)

        # Tabela de vendas
        self.tabela_vendas = QTableView()
        self.tabela_vendas.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.tabela_vendas.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.tabela_vendas.setAlternatingRowColors(True)
        self.tabela_vendas.doubleClicked.connect(self.ver_detalhes_venda)
        
        # Configurar estilo da tabela
        self.tabela_vendas.setStyleSheet("""
            QTableView {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                gridline-color: #e9ecef;
                background-color: white;
                selection-background-color: #e6f0ff;
                selection-color: #495057;
            }
            QTableView::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 12px 8px;
                border: none;
                border-bottom: 1px solid #dee2e6;
                font-weight: bold;
                color: #495057;
            }
        """)
        
        layout_principal.addWidget(self.tabela_vendas)

        # Botões de ação
        botoes_layout = QHBoxLayout()
        
        self.btn_detalhes = QPushButton("👁️ Ver Detalhes")
        self.btn_detalhes.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        self.btn_detalhes.clicked.connect(self.ver_detalhes_venda)
        self.btn_detalhes.setEnabled(False)
        
        self.btn_imprimir = QPushButton("🖨️ Imprimir Relatório")
        self.btn_imprimir.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.btn_imprimir.clicked.connect(self.imprimir_relatorio)
        
        botoes_layout.addWidget(self.btn_detalhes)
        botoes_layout.addStretch()
        botoes_layout.addWidget(self.btn_imprimir)
        
        layout_principal.addLayout(botoes_layout)

        # Inicializar modelo vazio para a tabela
        self.inicializar_tabela()

    def inicializar_tabela(self):
        """Inicializa a tabela com um modelo vazio"""
        model = QStandardItemModel(0, 7)
        model.setHorizontalHeaderLabels([
            "Nº Pedido", "Data", "Cliente", "Produtos", "Quantidade", "Total (R$)", "Status"
        ])
        self.tabela_vendas.setModel(model)
        
        # AGORA podemos conectar o signal, pois a tabela tem um modelo
        self.tabela_vendas.selectionModel().selectionChanged.connect(self.on_selecao_mudou)

    def setup_estatisticas(self, layout_principal):
        stats_layout = QHBoxLayout()
        
        # Total de vendas
        self.lbl_total_vendas = QLabel("Total de Vendas: 0")
        self.lbl_total_vendas.setStyleSheet("""
            QLabel {
                background-color: #007bff;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        
        # Valor total
        self.lbl_valor_total = QLabel("Valor Total: R$ 0,00")
        self.lbl_valor_total.setStyleSheet("""
            QLabel {
                background-color: #28a745;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        
        # Vendas hoje
        self.lbl_vendas_hoje = QLabel("Vendas Hoje: 0")
        self.lbl_vendas_hoje.setStyleSheet("""
            QLabel {
                background-color: #ffc107;
                color: #212529;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        
        stats_layout.addWidget(self.lbl_total_vendas)
        stats_layout.addWidget(self.lbl_valor_total)
        stats_layout.addWidget(self.lbl_vendas_hoje)
        stats_layout.addStretch()
        
        layout_principal.addLayout(stats_layout)

    def abrir_filtros(self):
        dialog = FiltroVendasDialog(self.filtros_atuais, self.sessao, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.filtros_atuais = dialog.obter_filtros()
            self.carregar_dados()
            
            # Atualizar aparência do botão de filtros
            if any(self.filtros_atuais.values()):
                self.btn_filtros.setText("⚙️ FILTROS ATIVOS")
                self.btn_filtros.setStyleSheet("""
                    QPushButton {
                        background-color: #6c757d;
                        color: white;
                        font-weight: bold;
                        border-radius: 5px;
                        padding: 8px 15px;
                        border: none;
                    }
                """)
            else:
                self.btn_filtros.setText("⚙️ Filtros Avançados")
                self.btn_filtros.setStyleSheet("""
                    QPushButton {
                        background-color: #E0E0E0;
                        color: #424242;
                        font-weight: bold;
                        border-radius: 5px;
                        border: 1px solid #CCCCCC;
                        padding: 8px 15px;
                    }
                """)

    def carregar_dados(self):
        try:
            # Query base
            query = select(PedidoVenda).order_by(PedidoVenda.data_emissao.desc())
            
            # Aplicar filtros
            query = self.aplicar_filtros(query)
            
            # Executar query
            vendas = self.sessao.execute(query).scalars().all()
            
            # Atualizar estatísticas
            self.atualizar_estatisticas(vendas)
            
            # Preencher tabela
            self.preencher_tabela(vendas)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {str(e)}")

    def aplicar_filtros(self, query):
        busca = self.busca_input.text().strip()
        if busca:
            # Buscar em pedidos relacionados
            subquery = select(PedidoVendaItem.pedido_id).where(
                PedidoVendaItem.produto.ilike(f"%{busca}%")
            ).distinct()
            
            query = query.where(
                or_(
                    PedidoVenda.id.cast(String).ilike(f"%{busca}%"),
                    PedidoVenda.id.in_(subquery)
                )
            )

        # Aplicar filtros avançados
        if self.filtros_atuais.get('data_inicio'):
            query = query.where(PedidoVenda.data_emissao >= self.filtros_atuais['data_inicio'])
        
        if self.filtros_atuais.get('data_fim'):
            query = query.where(PedidoVenda.data_emissao <= self.filtros_atuais['data_fim'])
        
        if self.filtros_atuais.get('status'):
            query = query.where(PedidoVenda.status == self.filtros_atuais['status'])
        
        if self.filtros_atuais.get('valor_min'):
            query = query.where(PedidoVenda.preco_total >= self.filtros_atuais['valor_min'])
        
        if self.filtros_atuais.get('valor_max'):
            query = query.where(PedidoVenda.preco_total <= self.filtros_atuais['valor_max'])

        return query

    def atualizar_estatisticas(self, vendas):
        total_vendas = len(vendas)
        valor_total = sum(float(venda.preco_total or 0) for venda in vendas)
        
        hoje = datetime.now().date()
        vendas_hoje = sum(1 for venda in vendas 
                         if venda.data_emissao and venda.data_emissao == hoje)
        
        self.lbl_total_vendas.setText(f"Total de Vendas: {total_vendas}")
        self.lbl_valor_total.setText(f"Valor Total: R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        self.lbl_vendas_hoje.setText(f"Vendas Hoje: {vendas_hoje}")

    def preencher_tabela(self, vendas):
        model = QStandardItemModel(len(vendas), 7)
        model.setHorizontalHeaderLabels([
            "Nº Pedido", "Data", "Cliente", "Produtos", "Quantidade", "Total (R$)", "Status"
        ])
        
        for row, venda in enumerate(vendas):
            # Obter itens da venda
            itens_query = select(PedidoVendaItem).where(PedidoVendaItem.pedido_id == venda.id)
            itens = self.sessao.execute(itens_query).scalars().all()
            
            # Nomes dos produtos
            produtos = ", ".join([item.produto for item in itens if item.produto])
            quantidade_total = sum(item.quantidade or 0 for item in itens)
            
            model.setItem(row, 0, QStandardItem(str(venda.id)))
            model.setItem(row, 1, QStandardItem(venda.data_emissao.strftime("%d/%m/%Y") if venda.data_emissao else ""))
            model.setItem(row, 2, QStandardItem(str(venda.cliente_id or "Cliente Balcão")))
            model.setItem(row, 3, QStandardItem(produtos[:50] + "..." if len(produtos) > 50 else produtos))
            model.setItem(row, 4, QStandardItem(str(quantidade_total)))
            model.setItem(row, 5, QStandardItem(f"{venda.preco_total or 0:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')))
            model.setItem(row, 6, QStandardItem(self.obter_status_texto(venda.status)))
        
        self.tabela_vendas.setModel(model)
        self.tabela_vendas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabela_vendas.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

    def obter_status_texto(self, status):
        status_map = {
            'F': '✅ Finalizada',
            'C': '❌ Cancelada',
            'P': '⏳ Pendente'
        }
        return status_map.get(status, status or '⏳ Pendente')

    def on_selecao_mudou(self):
        selecionado = self.tabela_vendas.selectionModel().hasSelection()
        self.btn_detalhes.setEnabled(selecionado)

    def ver_detalhes_venda(self):
        indices = self.tabela_vendas.selectionModel().selectedRows()
        if not indices:
            QMessageBox.warning(self, "Atenção", "Selecione uma venda para ver os detalhes.")
            return
        
        row = indices[0].row()
        pedido_id = int(self.tabela_vendas.model().item(row, 0).text())
        
        # Buscar dados completos do pedido
        pedido = self.sessao.execute(
            select(PedidoVenda).where(PedidoVenda.id == pedido_id)
        ).scalar_one_or_none()
        
        if pedido:
            self.mostrar_detalhes_pedido(pedido)

    def mostrar_detalhes_pedido(self, pedido):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Detalhes do Pedido #{pedido.id}")
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Cabeçalho
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"<h2>Pedido #{pedido.id}</h2>"))
        header_layout.addStretch()
        header_layout.addWidget(QLabel(f"<b>Data:</b> {pedido.data_emissao.strftime('%d/%m/%Y') if pedido.data_emissao else 'N/A'}"))
        layout.addLayout(header_layout)
        
        # Informações do pedido
        info_group = QGroupBox("Informações do Pedido")
        info_layout = QFormLayout(info_group)
        
        info_layout.addRow("Cliente:", QLabel(str(pedido.cliente_id or "Cliente Balcão")))
        info_layout.addRow("Status:", QLabel(self.obter_status_texto(pedido.status)))
        info_layout.addRow("Valor Total:", QLabel(f"R$ {pedido.preco_total or 0:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')))
        
        layout.addWidget(info_group)
        
        # Itens do pedido
        itens_group = QGroupBox("Itens do Pedido")
        itens_layout = QVBoxLayout(itens_group)
        
        # Tabela de itens
        tabela_itens = QTableView()
        model_itens = QStandardItemModel(0, 4)
        model_itens.setHorizontalHeaderLabels(["Produto", "Quantidade", "Preço Unit.", "Subtotal"])
        
        itens_query = select(PedidoVendaItem).where(PedidoVendaItem.pedido_id == pedido.id)
        itens = self.sessao.execute(itens_query).scalars().all()
        
        for row, item in enumerate(itens):
            model_itens.setItem(row, 0, QStandardItem(item.produto or ""))
            model_itens.setItem(row, 1, QStandardItem(str(item.quantidade or 0)))
            model_itens.setItem(row, 2, QStandardItem(f"{item.preco_unitario or 0:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')))
            model_itens.setItem(row, 3, QStandardItem(f"{item.preco_total or 0:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')))
        
        tabela_itens.setModel(model_itens)
        tabela_itens.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        itens_layout.addWidget(tabela_itens)
        
        layout.addWidget(itens_group)
        layout.addStretch()
        
        # Botão fechar
        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(dialog.accept)
        layout.addWidget(btn_fechar)
        
        dialog.exec()

    def imprimir_relatorio(self):
        QMessageBox.information(self, "Relatório", "Funcionalidade de impressão será implementada em breve.")

    def load_data(self):
        """Método para compatibilidade com o sistema principal"""
        self.carregar_dados()