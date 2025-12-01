from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGroupBox,
    QTableView, QLineEdit, QPushButton, QComboBox, QDialog,
    QDateEdit, QFormLayout
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QDate, QLocale
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import date, datetime, timedelta
import traceback 
from decimal import Decimal

from src.Models.models import Financeiro, EnumStatus


# ===============================================================
# PROXY MODEL PARA FINANCEIRO (FILTROS)
# ===============================================================
class FinanceiroFilterProxy(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.texto = ""
        self.tipo = "Todos"
        self.data_inicio = None
        self.data_fim = None

    def filterAcceptsRow(self, row, parent):
        model = self.sourceModel()

        # colunas esperadas: 0 ID, 1 Tipo, 2 Descrição, 3 Valor, 4 Vencimento, 5 Status
        tipo = model.index(row, 1, parent).data() or ""
        descricao = model.index(row, 2, parent).data() or ""
        venc_str = model.index(row, 4, parent).data() or ""

        texto_ok = self.texto in f"{tipo} {descricao}".lower()
        tipo_ok = self.tipo == "Todos" or tipo == self.tipo

        try:
            data_mov = datetime.strptime(venc_str, "%d/%m/%Y").date()
            data_ok = self.data_inicio <= data_mov <= self.data_fim
        except:
            data_ok = True

        return texto_ok and tipo_ok and data_ok


# ===============================================================
# DIALOG DE FILTRO AVANÇADO (FINANCEIRO)
# ===============================================================
class FiltroFinanceiroDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Filtros Financeiros")
        self.setModal(True)
        self.resize(420, 260)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Todos", "Pagar", "Receber"])

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
# DASHBOARD FINANCEIRO
# ===============================================================
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
        # BARRA DE BUSCA E FILTRO 
        # ---------------------------------------------------------------
        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por descrição...")
        self.btn_filtro = QPushButton("Filtro Avançado")
        top_bar.addWidget(self.search_input)
        top_bar.addWidget(self.btn_filtro)
        self.main_layout.addLayout(top_bar)

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

        # ---------------------------------------------------------------
        # Proxy / Dialog
        # ---------------------------------------------------------------
        self.proxy_model = FinanceiroFilterProxy()
        self.filtro_dialog = FiltroFinanceiroDialog(self)

        # conexões
        self.search_input.textChanged.connect(self.filtrar_texto)
        self.btn_filtro.clicked.connect(self.filtro_dialog.show)
        self.filtro_dialog.btn_aplicar.clicked.connect(self.aplicar_filtro_dialog)
        self.filtro_dialog.btn_limpar.clicked.connect(self.limpar_filtros)

        # carrega dados
        self.load_data()

    # ===================================================================
    #  Criar card KPI
    # ===================================================================
    def criar_kpi(self, titulo, valor, cor_default):
        box = QGroupBox(titulo)
        layout = QVBoxLayout(box)
        lbl = QLabel(valor)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"font-size: 20pt; font-weight: bold; color: {cor_default};")

        # Aplicar estilo ao box
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

    # ===================================================================
    #  Carregar Indicadores e tabela
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

        # -------------------------------------------------
        # Monta modelo da tabela
        # -------------------------------------------------
        query = self.session.execute(
            select(Financeiro)
            .where(Financeiro.status == EnumStatus.ABERTA)
            .order_by(Financeiro.vencimento.asc())
            .limit(500)
        ).scalars().all()

        headers = ["ID", "Tipo", "Descrição", "Valor", "Vencimento", "Status"]
        model = QStandardItemModel(len(query), len(headers))
        model.setHorizontalHeaderLabels(headers)

        for row, f in enumerate(query):
            valor_fmt = locale.toString(float(f.valor_nota), 'f', 2)
            item_valor = QStandardItem(f"R$ {valor_fmt}")
            item_vencimento = QStandardItem(f.vencimento.strftime("%d/%m/%Y"))
            item_status = QStandardItem(f.status.value.capitalize())

            model.setItem(row, 0, QStandardItem(str(f.id)))
            model.setItem(row, 1, QStandardItem("Pagar" if f.tipo_lancamento == "P" else "Receber"))
            model.setItem(row, 2, QStandardItem(f.descricao))
            model.setItem(row, 3, item_valor)
            model.setItem(row, 4, item_vencimento)
            model.setItem(row, 5, item_status)

            if f.tipo_lancamento == "P":
                for col in range(len(headers)):
                    model.item(row, col).setBackground(QColor("#f0f0f0"))

        # aplica modelo no proxy e view
        self.proxy_model.setSourceModel(model)
        self.table_view.setModel(self.proxy_model)

        # configura coluna para ocupar toda largura
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(header.ResizeMode.Stretch)

        # padrão datas
        self.proxy_model.data_inicio = date.today() - timedelta(days=365)
        self.proxy_model.data_fim = date.today()

    # ===============================================================
    # FILTROS / integração com dialog
    # ===============================================================
    def filtrar_texto(self, texto):
        self.proxy_model.texto = texto.lower()
        self.proxy_model.invalidateFilter()

    def aplicar_filtro_dialog(self):
        self.proxy_model.tipo = self.filtro_dialog.combo_tipo.currentText()
        self.proxy_model.data_inicio = self.filtro_dialog.data_inicio.date().toPyDate()
        self.proxy_model.data_fim = self.filtro_dialog.data_fim.date().toPyDate()
        self.proxy_model.invalidateFilter()
        self.filtro_dialog.close()

    def limpar_filtros(self):
        self.search_input.clear()
        self.filtro_dialog.combo_tipo.setCurrentIndex(0)
        self.filtro_dialog.data_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.filtro_dialog.data_fim.setDate(QDate.currentDate())
        self.proxy_model.texto = ""
        self.proxy_model.invalidateFilter()
