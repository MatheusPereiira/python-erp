from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGroupBox,
    QTableView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt6.QtCore import Qt
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import date, timedelta
import traceback

from src.Models.models import Item, MovimentoEstoque 


class DashboardEstoqueWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session

        self.main_layout = QVBoxLayout(self)

        title = QLabel("Dashboard de Estoque")
        title.setStyleSheet("font-size: 22pt; font-weight: bold; margin-bottom: 15px; color: #333;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(title)

        # ---------------------------------------------------------------
        # KPI CARDS
        # ---------------------------------------------------------------
        kpi_layout = QHBoxLayout()
        
  
        self.lbl_abaixo, self.kpi_abaixo = self._criar_kpi("Itens abaixo do mínimo", "0", "#FFC107") # Amarelo/Aviso
        self.lbl_total_itens, self.kpi_total_itens = self._criar_kpi("Total de Itens", "0", "#1a73e8") # Azul
        self.lbl_movimentos, self.kpi_movimentos = self._criar_kpi("Movimentos (30d)", "0", "#007BFF") # Azul Escuro
        
        kpi_layout.addWidget(self.kpi_abaixo)
        kpi_layout.addWidget(self.kpi_total_itens)
        kpi_layout.addWidget(self.kpi_movimentos)
        self.main_layout.addLayout(kpi_layout)

        # ---------------------------------------------------------------
        # TABELA MOVIMENTOS RECENTES
        # ---------------------------------------------------------------
        box = QGroupBox("Últimas Movimentações")
        box_layout = QVBoxLayout(box)
        box.setStyleSheet("font-weight: bold;")
        
        self.table = QTableView()
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

        box_layout.addWidget(self.table)
        self.main_layout.addWidget(box)

        self.load_data()

    # ===================================================================
    #  Criar card KPI 
    # ===================================================================
    def _criar_kpi(self, titulo, valor, cor_default):
        box = QGroupBox(titulo)
        layout = QVBoxLayout(box)
        lbl = QLabel(valor)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl.setStyleSheet(f"font-size: 20pt; font-weight: bold; color: {cor_default};")
        
        box.setStyleSheet("""
            QGroupBox {
                background-color: #f7f9fc;
                border-radius: 10px;
                border: 1px solid #cdd5e0;
                padding: 10px;
                margin-top: 5px;
            }
        """)
        layout.addWidget(lbl)
        return lbl, box 

    # ===================================================================
    #  Carregar Indicadores e tabela
    # ===================================================================
    def load_data(self):
        hoje = date.today()
        data_30_dias_atras = hoje - timedelta(days=30)
        
        # -------------------------------------------------
        # Consultas KPI
        # -------------------------------------------------
        try:
            total_itens = self.session.execute(select(func.count()).select_from(Item)).scalar() or 0
            
            abaixo = self.session.execute(
                select(func.count()).select_from(Item).where(Item.estoque < Item.estoque_minimo)
            ).scalar() or 0

            movimentos_30 = self.session.execute(
                select(func.count()).select_from(MovimentoEstoque).where(
                    MovimentoEstoque.data_ultima_mov >= data_30_dias_atras
                )
            ).scalar() or 0
        
        except SQLAlchemyError as e:
            print(f"Erro ao acessar o banco de dados do estoque: {e}")
            traceback.print_exc()
            total_itens = 0
            abaixo = 0
            movimentos_30 = 0
            
            self.lbl_abaixo.setText("ERRO")
            self.lbl_total_itens.setText("ERRO")
            self.lbl_movimentos.setText("ERRO")
            self.table.setModel(QStandardItemModel(0, 0))
            return 

        # -------------------------------------------------
        # Preencher KPIs e aplicar Estilo Dinâmico
        # -------------------------------------------------
        
        self.lbl_abaixo.setText(str(abaixo))
        self.lbl_total_itens.setText(str(total_itens))
        self.lbl_movimentos.setText(str(movimentos_30))
        
        if abaixo > 0:
            self.lbl_abaixo.setStyleSheet("font-size: 20pt; font-weight: bold; color: #DC3545;") # Vermelho
        else:
            self.lbl_abaixo.setStyleSheet("font-size: 20pt; font-weight: bold; color: #28A745;") # Verde (Tudo OK)
            
        # -------------------------------------------------
        # Tabela de últimas movimentações
        # -------------------------------------------------
        try:
            movimentos = self.session.execute(
                select(MovimentoEstoque).order_by(MovimentoEstoque.data_ultima_mov.desc()).limit(20)
            ).scalars().all()
        except SQLAlchemyError:
            movimentos = []

        headers = ["ID", "Item", "Tipo", "Quantidade", "Fornecedor", "Data", "Obs"]
        model = QStandardItemModel(len(movimentos), len(headers))
        model.setHorizontalHeaderLabels(headers)

        for row, m in enumerate(movimentos):
            item_nome = m.item.nome if getattr(m, "item", None) and getattr(m.item, "nome", None) else "N/A"
            fornecedor = m.fornecedor.nome if getattr(m, "fornecedor", None) and getattr(m.fornecedor, "nome", None) else ""
            
            tipo = "Entrada" if m.tipo_movimento == "entrada" else "Saída"
            
            if m.tipo_movimento == "entrada":
                background_color = QColor("#D4EDDA") 
            else: 
                background_color = QColor("#F8D7DA") 

            for col in range(len(headers)):
                item = model.item(row, col)
                if not item:
                    item = QStandardItem()
                    model.setItem(row, col, item)
                item.setBackground(background_color)

            model.setItem(row, 0, QStandardItem(str(m.id)))
            model.setItem(row, 1, QStandardItem(item_nome))
            model.setItem(row, 2, QStandardItem(tipo))
            model.setItem(row, 3, QStandardItem(str(m.quantidade)))
            model.setItem(row, 4, QStandardItem(fornecedor))
            model.setItem(row, 5, QStandardItem(m.data_ultima_mov.strftime("%d/%m/%Y") if m.data_ultima_mov else ""))
            model.setItem(row, 6, QStandardItem(m.observacao or ""))

        self.table.setModel(model)
        self.table.resizeColumnsToContents()