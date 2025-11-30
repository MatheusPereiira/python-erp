from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QTableView, QMessageBox, QHeaderView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from sqlalchemy import select, func, delete

from src.Models.models import Financeiro, EnumStatus
from src.Components.Financeiro.cadastro_financeiro_dialog import CadastroFinanceiroDialog, FiltroFinanceiroDialog


class CadastroFinanceiroWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.main_layout = QVBoxLayout(self)

        self.PAGE_SIZE = 20
        self.current_page = 1
        self.total_records = 0
        
        # Mapeamento de campos para ordenação
        self.field_to_model = {
            "id": Financeiro.id,
            "valor_nota": Financeiro.valor_nota,
            "vencimento": Financeiro.vencimento,
            "status": Financeiro.status
        }

        self.current_filters = {}

        # -----------------------------
        # Título
        # -----------------------------
        self.title_label = QLabel("Financeiro - Lançamentos")
        self.title_label.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 10px;")
        self.main_layout.addWidget(self.title_label)

        # -----------------------------
        # Barra de busca + filtro
        # -----------------------------
        search_filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por descrição...")
        self.search_input.textChanged.connect(lambda: self.load_data(reset_page=True))

        self.filter_btn = QPushButton("⚙️ Filtro Avançado")
        self.filter_btn.setStyleSheet(
            "background-color: #E0E0E0; color: #424242; font-weight: bold; border-radius: 5px; "
            "border: 1px solid #CCCCCC;"
        )
        self.filter_btn.setFixedWidth(150)
        self.filter_btn.clicked.connect(self.open_filter_dialog)

        search_filter_layout.addWidget(self.search_input)
        search_filter_layout.addWidget(self.filter_btn)
        self.main_layout.addLayout(search_filter_layout)

        # -----------------------------
        # Botões principais
        # -----------------------------
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Adicionar")
        self.edit_btn = QPushButton("📝 Editar")
        self.delete_btn = QPushButton("❌ Excluir")
        self.refresh_btn = QPushButton("🔄 Atualizar")

        self.add_btn.setStyleSheet("background-color: #28a745; color: white; padding: 10px; border-radius: 5px;")
        self.edit_btn.setStyleSheet("background-color: #007bff; color: white; padding: 10px; border-radius: 5px;")
        self.delete_btn.setStyleSheet("background-color: #dc3545; color: white; padding: 10px; border-radius: 5px;")
        self.refresh_btn.setStyleSheet(
            "background-color: #E9ECEF; color: #495057; padding: 10px; border-radius: 5px; border: 1px solid #CED4DA;"
        )

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        
        self.main_layout.addLayout(button_layout)

        # -----------------------------
        # Tabela
        # -----------------------------
        self.table_view = QTableView()
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        self.main_layout.addWidget(self.table_view)
        self.table_view.horizontalHeader().setSectionsClickable(False)

        # -----------------------------
        # Paginação
        # -----------------------------
        pagination_layout = QHBoxLayout()
        self.page_info_label = QLabel("Página 1 de 1")
        self.prev_btn = QPushButton("◀ Anterior")
        self.next_btn = QPushButton("Próxima ▶")

        pagination_layout.addStretch(1)
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch(1)
        self.main_layout.addLayout(pagination_layout)

        # Conectar botões
        self.add_btn.clicked.connect(self.open_add_dialog)
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        self.delete_btn.clicked.connect(self.delete_item)
        self.refresh_btn.clicked.connect(self.load_data)

        self.prev_btn.clicked.connect(self.go_to_previous_page)
        self.next_btn.clicked.connect(self.go_to_next_page)

        self.load_data()


    # =========================================================================
    #  FILTRO
    # =========================================================================
    def open_filter_dialog(self):
        dialog = FiltroFinanceiroDialog(self.current_filters, parent=self)
        if dialog.exec():
            self.current_filters = dialog.filtrar()
            self.load_data(reset_page=True)

            if any(key in self.current_filters for key in ["status", "valor_min", "valor_max"]):
                self.filter_btn.setText("⚙️ FILTRO ATIVO")
                self.filter_btn.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; border-radius: 5px;")
            else:
                self.filter_btn.setText("⚙️ Filtro Avançado")
                self.filter_btn.setStyleSheet(
                    "background-color: #E0E0E0; color: #424242; font-weight: bold; border-radius: 5px; border: 1px solid #CCCCCC;"
                )


    # =========================================================================
    #  NAVEGAÇÃO
    # =========================================================================
    def go_to_previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def go_to_next_page(self):
        total_pages = (self.total_records + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_data()


    # =========================================================================
    #  CARREGAR DADOS
    # =========================================================================
    def load_data(self, reset_page=False):

        if reset_page:
            self.current_page = 1

        filtro = self.search_input.text().strip()

        try:
            # ==============================
            #  Query base
            # ==============================
            base_query = select(Financeiro)

            # ---- Filtro texto (descrição)
            if filtro:
                base_query = base_query.where(Financeiro.descricao.ilike(f"%{filtro}%"))

            # ---- Filtros avançados
            if self.current_filters.get("status"):
                base_query = base_query.where(Financeiro.status == self.current_filters["status"])

            if self.current_filters.get("valor_min"):
                base_query = base_query.where(Financeiro.valor_nota >= self.current_filters["valor_min"])

            if self.current_filters.get("valor_max"):
                base_query = base_query.where(Financeiro.valor_nota <= self.current_filters["valor_max"])

            # ==============================
            #  Total registros
            # ==============================
            total_count = select(func.count()).select_from(base_query.subquery())
            self.total_records = self.session.execute(total_count).scalar_one()
            total_pages = (self.total_records + self.PAGE_SIZE - 1) // self.PAGE_SIZE

            if self.current_page > total_pages and total_pages > 0:
                self.current_page = total_pages
            elif total_pages == 0:
                self.current_page = 1

            offset = (self.current_page - 1) * self.PAGE_SIZE

            # ==============================
            #  Ordenação
            # ==============================
            sort_field_name = self.current_filters.get("sort_column_field", "id")
            sort_direction = self.current_filters.get("sort_order", "DESC")

            sort_field = self.field_to_model.get(sort_field_name, Financeiro.id)

            if sort_direction == "ASC":
                base_query = base_query.order_by(sort_field.asc())
            else:
                base_query = base_query.order_by(sort_field.desc())

            # ==============================
            #  Exec Query
            # ==============================
            query = base_query.offset(offset).limit(self.PAGE_SIZE)
            items = self.session.execute(query).scalars().all()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar dados.\n{e}")
            items = []
            total_pages = 1
            self.total_records = 0

        # ==============================
        #  Montar tabela
        # ==============================
        headers = ["ID", "Tipo", "Origem", "Descrição", "Valor (R$)", "Vencimento", "Status"]

        model = QStandardItemModel(len(items), len(headers))
        model.setHorizontalHeaderLabels(headers)

        for row, f in enumerate(items):
            model.setItem(row, 0, QStandardItem(str(f.id)))
            model.setItem(row, 1, QStandardItem("Pagar" if f.tipo_lancamento == "P" else "Receber"))
            model.setItem(row, 2, QStandardItem("Compra" if f.origem == "C" else "Venda"))
            model.setItem(row, 3, QStandardItem(f.descricao or ""))
            model.setItem(row, 4, QStandardItem(f"{float(f.valor_nota):,.2f}".replace(".", ",") ))
            model.setItem(row, 5, QStandardItem(f.vencimento.strftime("%d/%m/%Y")))
            model.setItem(row, 6, QStandardItem(f.status.value.capitalize()))

        self.table_view.setModel(model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)

        self.page_info_label.setText(f"Página {self.current_page} de {total_pages if total_pages > 0 else 1}")

        main_window = self.window()
        if hasattr(main_window, "total_registros_label"):
            main_window.total_registros_label.setText(f"Total: {self.total_records}")



    # =========================================================================
    #  ADD / EDIT / DELETE
    # =========================================================================
    def open_add_dialog(self):
        dialog = CadastroFinanceiroDialog(self.session, parent=self)
        if dialog.exec():
            self.load_data(reset_page=True)

    def get_selected_item(self):
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "Aviso", "Selecione um lançamento para continuar.")
            return None

        row = indexes[0].row()
        row_id = int(self.table_view.model().item(row, 0).text())

        lanc = self.session.execute(
            select(Financeiro).filter_by(id=row_id)
        ).scalar_one_or_none()

        return lanc

    def open_edit_dialog(self):
        item = self.get_selected_item()
        if item:
            dialog = CadastroFinanceiroDialog(self.session, lancamento=item, parent=self)
            if dialog.exec():
                self.load_data()


    def delete_item(self):
        item, lanc_id = self.get_selected_item()
        if item:
            reply = QMessageBox.question(
                self,
                "Excluir",
                f"Tem certeza que deseja excluir o lançamento:\n\n{item.descricao}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.session.execute(delete(Financeiro).where(Financeiro.id == lanc_id))
                    self.session.commit()
                    QMessageBox.information(self, "Sucesso", "Lançamento excluído.")
                    self.load_data(reset_page=True)
                except Exception as e:
                    self.session.rollback()
                    QMessageBox.critical(self, "Erro", f"Erro ao excluir.\n{e}")