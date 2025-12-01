from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGroupBox,
    QTableView, QLineEdit, QPushButton, QComboBox, QDialog,
    QDateEdit, QFormLayout
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QDate
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import date, timedelta, datetime
import traceback

from src.Models.models import Item, MovimentoEstoque


# ===============================================================
# PROXY MODEL (FILTROS)
# ===============================================================
class MovimentoFilterProxy(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.texto = ""
        self.tipo = "Todos"
        self.data_inicio = None
        self.data_fim = None

    def filterAcceptsRow(self, row, parent):
        model = self.sourceModel()

        item = model.index(row, 1, parent).data() or ""
        tipo = model.index(row, 2, parent).data() or ""
        data_str = model.index(row, 5, parent).data() or ""
        obs = model.index(row, 6, parent).data() or ""

        texto_ok = self.texto in f"{item} {obs}".lower()
        tipo_ok = self.tipo == "Todos" or tipo == self.tipo

        try:
            data_mov = datetime.strptime(data_str, "%d/%m/%Y").date()
            data_ok = self.data_inicio <= data_mov <= self.data_fim
        except Exception:
            data_ok = True

        return texto_ok and tipo_ok and data_ok


# ===============================================================
# DIALOG DE FILTRO AVANÇADO
# ===============================================================
class FiltroMovimentosDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Filtro Avançado")
        self.setModal(True)
        self.resize(420, 260)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Todos", "Entrada", "Saída"])

        self.data_inicio = QDateEdit()
        self.data_inicio.setCalendarPopup(True)
        self.data_inicio.setDate(QDate.currentDate().addMonths(-1))

        self.data_fim = QDateEdit()
        self.data_fim.setCalendarPopup(True)
        self.data_fim.setDate(QDate.currentDate())

        form.addRow("Tipo:", self.combo_tipo)
        form.addRow("Data inicial:", self.data_inicio)
        form.addRow("Data final:", self.data_fim)

        layout.addLayout(form)

        btns = QHBoxLayout()
        self.btn_limpar = QPushButton("Limpar")
        self.btn_aplicar = QPushButton("Aplicar")

        btns.addWidget(self.btn_limpar)
        btns.addWidget(self.btn_aplicar)
        layout.addLayout(btns)


# ===============================================================
# DASHBOARD DE ESTOQUE
# ===============================================================
class DashboardEstoqueWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session

        self.main_layout = QVBoxLayout(self)

        # ------------------- TÍTULO -------------------
        title = QLabel("Dashboard de Estoque")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22pt; font-weight: bold; margin-bottom: 15px; color: #333;")
        self.main_layout.addWidget(title)

        # ===========================================================
        # KPI CARDS
        # ===========================================================
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)

        self.lbl_total, self.kpi_total = self._criar_kpi("Total de Itens", "0", "#1a73e8")
        self.lbl_mov_30, self.kpi_mov_30 = self._criar_kpi("Movimentações (30 dias)", "0", "#1a73e8")
        self.lbl_abaixo, self.kpi_abaixo = self._criar_kpi("Abaixo do Mínimo", "0", "#f59e0b")

        kpi_layout.addWidget(self.kpi_total)
        kpi_layout.addWidget(self.kpi_mov_30)
        kpi_layout.addWidget(self.kpi_abaixo)

        self.main_layout.addLayout(kpi_layout)

        # ===========================================================
        # BARRA DE BUSCA
        # ===========================================================
        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por descrição...")
        self.btn_filtro = QPushButton("Filtro Avançado")
        top_bar.addWidget(self.search_input)
        top_bar.addWidget(self.btn_filtro)
        self.main_layout.addLayout(top_bar)

        # ===========================================================
        # TABELA
        # ===========================================================
        box = QGroupBox()
        box_layout = QVBoxLayout(box)

        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(header.ResizeMode.Stretch)

        box_layout.addWidget(self.table)
        self.main_layout.addWidget(box)

        # ===========================================================
        # FILTRO
        # ===========================================================
        self.proxy_model = MovimentoFilterProxy()
        self.filtro_dialog = FiltroMovimentosDialog(self)

        self.search_input.textChanged.connect(self._filtrar_texto)
        self.btn_filtro.clicked.connect(self.filtro_dialog.show)
        self.filtro_dialog.btn_aplicar.clicked.connect(self._aplicar_filtro)
        self.filtro_dialog.btn_limpar.clicked.connect(self._limpar_filtros)

        self.load_data()

    # ===============================================================
    # KPI
    # ===============================================================
    def _criar_kpi(self, titulo, valor, cor):
        box = QGroupBox(titulo)
        layout = QVBoxLayout(box)

        lbl = QLabel(valor)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"font-size: 20pt; font-weight: bold; color: {cor};")

        box.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #cdd5e0;
                padding: 10px;
                margin-top: 5px;
            }
        """)

        layout.addWidget(lbl)
        return lbl, box

    # ===============================================================
    def load_data(self):
        hoje = date.today()
        data_30 = hoje - timedelta(days=30)

        try:
            total_itens = self.session.execute(
                select(func.count()).select_from(Item)
            ).scalar() or 0

            mov_30 = self.session.execute(
                select(func.count())
                .select_from(MovimentoEstoque)
                .where(MovimentoEstoque.data_ultima_mov >= data_30)
            ).scalar() or 0

            abaixo = self.session.execute(
                select(func.count())
                .select_from(Item)
                .where(Item.estoque < Item.estoque_minimo)
            ).scalar() or 0

            movimentos = self.session.execute(
                select(MovimentoEstoque)
                .order_by(MovimentoEstoque.data_ultima_mov.desc())
            ).scalars().all()

        except SQLAlchemyError:
            traceback.print_exc()
            return

        # KPIs
        self.lbl_total.setText(str(total_itens))
        self.lbl_mov_30.setText(str(mov_30))
        self.lbl_abaixo.setText(str(abaixo))

        # Tabela
        headers = ["ID", "Item", "Tipo", "Quantidade", "Fornecedor", "Data", "Obs"]
        model = QStandardItemModel(len(movimentos), len(headers))
        model.setHorizontalHeaderLabels(headers)

        for row, m in enumerate(movimentos):
            dados = [
                str(m.id),
                getattr(m.item, "nome", ""),
                "Entrada" if m.tipo_movimento == "entrada" else "Saída",
                str(m.quantidade),
                getattr(m.fornecedor, "nome", ""),
                m.data_ultima_mov.strftime("%d/%m/%Y") if m.data_ultima_mov else "",
                m.observacao or ""
            ]
            for col, v in enumerate(dados):
                model.setItem(row, col, QStandardItem(v))

        self.proxy_model.setSourceModel(model)
        self.table.setModel(self.proxy_model)

        self.proxy_model.data_inicio = hoje - timedelta(days=365)
        self.proxy_model.data_fim = hoje

    # ===============================================================
    def _filtrar_texto(self, texto):
        self.proxy_model.texto = texto.lower()
        self.proxy_model.invalidateFilter()

    def _aplicar_filtro(self):
        self.proxy_model.tipo = self.filtro_dialog.combo_tipo.currentText()
        self.proxy_model.data_inicio = self.filtro_dialog.data_inicio.date().toPyDate()
        self.proxy_model.data_fim = self.filtro_dialog.data_fim.date().toPyDate()
        self.proxy_model.invalidateFilter()
        self.filtro_dialog.close()

    def _limpar_filtros(self):
        self.search_input.clear()
        self.filtro_dialog.combo_tipo.setCurrentIndex(0)
        self.proxy_model.texto = ""
        self.proxy_model.invalidateFilter()
