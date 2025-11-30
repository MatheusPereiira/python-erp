from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGroupBox,
    QTableView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt6.QtCore import Qt, QLocale
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import date
import traceback 
from decimal import Decimal

from src.Models.models import Financeiro, EnumStatus


class DashboardFinanceiroWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session

        self.main_layout = QVBoxLayout(self)

        titulo = QLabel("Dashboard Financeiro")
        titulo.setStyleSheet("font-size: 22pt; font-weight: bold; margin-bottom: 15px; color: #333;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(titulo)

        # ---------------------------------------------------------------
        # KPI CARDS
        # ---------------------------------------------------------------
        kpi_layout = QHBoxLayout()

        self.lbl_receber, self.kpi_receber = self.criar_kpi("A Receber", "R$ 0,00", "#28A745") # Verde
        self.lbl_pagar, self.kpi_pagar = self.criar_kpi("A Pagar", "R$ 0,00", "#DC3545")      # Vermelho
        self.lbl_saldo, self.kpi_saldo = self.criar_kpi("Saldo Previsto", "R$ 0,00", "#1a73e8")
        self.lbl_atrasados, self.kpi_atrasados = self.criar_kpi("Atrasados", "0", "#FFC107") # Amarelo/Laranja

        kpi_layout.addWidget(self.kpi_receber)
        kpi_layout.addWidget(self.kpi_pagar)
        kpi_layout.addWidget(self.kpi_saldo)
        kpi_layout.addWidget(self.kpi_atrasados)

        self.main_layout.addLayout(kpi_layout)

        # ---------------------------------------------------------------
        # TABELA DE PRÓXIMOS LANÇAMENTOS
        # ---------------------------------------------------------------
        box_proximos = QGroupBox("Próximos Vencimentos (15 dias)")
        box_layout = QVBoxLayout(box_proximos)
        box_proximos.setStyleSheet("font-weight: bold;")

        self.table_view = QTableView()
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

        box_layout.addWidget(self.table_view)
        self.main_layout.addWidget(box_proximos)

        self.load_data()

    # ===================================================================
    #  Criar card KPI 
    # ===================================================================
    def criar_kpi(self, titulo, valor, cor_default):
        box = QGroupBox(titulo)
        layout = QVBoxLayout(box)
        lbl = QLabel(valor)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Define a cor inicial. A cor do Saldo será atualizada dinamicamente.
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
        locale = QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil)
        try:
            total_receber = self.session.execute(
                select(func.sum(Financeiro.valor_nota)).where(
                    Financeiro.tipo_lancamento == "R",
                    Financeiro.status == EnumStatus.ABERTA
                )
            ).scalar() or Decimal("0")

            total_pagar = self.session.execute(
                select(func.sum(Financeiro.valor_nota)).where(
                    Financeiro.tipo_lancamento == "P",
                    Financeiro.status == EnumStatus.ABERTA
                )
            ).scalar() or Decimal("0")

            hoje = date.today()
            atrasados = self.session.execute(
                select(func.count()).where(
                    Financeiro.status == EnumStatus.ABERTA,
                    Financeiro.vencimento < hoje
                )
            ).scalar() or 0

            saldo = total_receber - total_pagar
            
        except SQLAlchemyError as e:
            print(f"Erro ao acessar o banco de dados: {e}")
            traceback.print_exc()
            total_receber = total_pagar = saldo = 0.0
            atrasados = 0
            
            self.lbl_receber.setText("ERRO")
            self.lbl_pagar.setText("ERRO")
            self.lbl_saldo.setText("ERRO")
            self.lbl_atrasados.setText("ERRO")
            self.table_view.setModel(QStandardItemModel(0, 0))
            return 

        # -------------------------------------------------
        # Preencher KPIs e aplicar Estilo Dinâmico
        # -------------------------------------------------
        
        receber_fmt = locale.toString(float(total_receber), 'f', 2)
        pagar_fmt = locale.toString(float(total_pagar), 'f', 2)
        saldo_fmt = locale.toString(float(saldo), 'f', 2)

        self.lbl_receber.setText(f"R$ {receber_fmt}")
        self.lbl_pagar.setText(f"R$ {pagar_fmt}")
        self.lbl_atrasados.setText(str(atrasados))

        self.lbl_saldo.setText(f"R$ {saldo_fmt}")
        if saldo > 0:
            self.lbl_saldo.setStyleSheet("font-size: 20pt; font-weight: bold; color: #28A745;") # Verde
        elif saldo < 0:
            self.lbl_saldo.setStyleSheet("font-size: 20pt; font-weight: bold; color: #DC3545;") # Vermelho
        else:
            self.lbl_saldo.setStyleSheet("font-size: 20pt; font-weight: bold; color: #1a73e8;") # Azul Padrão

        query = self.session.execute(
            select(Financeiro)
            .where(Financeiro.status == EnumStatus.ABERTA)
            .order_by(Financeiro.vencimento.asc())
            .limit(15)
        ).scalars().all()

        headers = ["ID", "Tipo", "Descrição", "Valor", "Vencimento", "Status"]

        model = QStandardItemModel(len(query), len(headers))
        model.setHorizontalHeaderLabels(headers)

        for row, f in enumerate(query):
            valor_fmt = locale.toString(float(f.valor_nota), 'f', 2)
            
            item_valor = QStandardItem(f"R$ {valor_fmt}")
            item_vencimento = QStandardItem(f.vencimento.strftime("%d/%m/%Y"))
            item_status = QStandardItem(f.status.value.capitalize())
            
            if f.status == EnumStatus.ABERTA:
                 item_status.setForeground(QColor("#FF8C00")) # Laranja            
            

            model.setItem(row, 0, QStandardItem(str(f.id)))
            model.setItem(row, 1, QStandardItem("Pagar" if f.tipo_lancamento == "P" else "Receber"))
            model.setItem(row, 2, QStandardItem(f.descricao))
            model.setItem(row, 3, item_valor)
            model.setItem(row, 4, item_vencimento)
            model.setItem(row, 5, item_status)

            if f.tipo_lancamento == "P":
                for col in range(len(headers)):
                    model.item(row, col).setBackground(QColor("#f0f0f0")) 

        self.table_view.setModel(model)
        self.table_view.resizeColumnsToContents()