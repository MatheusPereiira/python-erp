# src/Views/cadastro_estoque_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableView, QMessageBox, QHeaderView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from sqlalchemy import select, func, delete
from sqlalchemy.exc import SQLAlchemyError
from datetime import date

from src.Models.models import Item, Fornecedor
from src.Components.Estoque.cadastro_estoque_dialog import MovimentacaoDialog, FiltroEstoqueDialog

class CadastroEstoqueWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.main_layout = QVBoxLayout(self)

        self.PAGE_SIZE = 20
        self.current_page = 1
        self.total_records = 0

        # mapeamento para ordenacao
        self.field_to_model = {
            "id": Item.id,
            "nome": Item.nome,
            "estoque": Item.estoque,
            "estoque_minimo": Item.estoque_minimo
        }

        self.current_filters = {}

        # titulo
        self.title_label = QLabel("Estoque - Controle de Movimentações")
        self.title_label.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 10px;")
        self.main_layout.addWidget(self.title_label)

        # busca + filtro
        search_filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nome ou código...")
        self.search_input.textChanged.connect(lambda: self.load_data(reset_page=True))

        self.filter_btn = QPushButton("⚙️ Filtro Avançado")
        self.filter_btn.setStyleSheet(
            "background-color: #E0E0E0; color: #424242; font-weight: bold; border-radius: 5px; border: 1px solid #CCCCCC;"
        )
        self.filter_btn.setFixedWidth(150)
        self.filter_btn.clicked.connect(self.open_filter_dialog)

        search_filter_layout.addWidget(self.search_input)
        search_filter_layout.addWidget(self.filter_btn)
        self.main_layout.addLayout(search_filter_layout)

        # botoes principais (não criamos produto aqui)
        button_layout = QHBoxLayout()
        self.entrada_btn = QPushButton("➕ Entrada")
        self.saida_btn = QPushButton("➖ Saída")
        self.delete_btn = QPushButton("❌ Excluir Produto (Atenção!)")
        self.refresh_btn = QPushButton("🔄 Atualizar")

        self.entrada_btn.setStyleSheet("background-color: #28a745; color: white; padding: 10px; border-radius: 5px;")
        self.saida_btn.setStyleSheet("background-color: #ffc107; color: #212529; padding: 10px; border-radius: 5px;")
        self.delete_btn.setStyleSheet("background-color: #dc3545; color: white; padding: 10px; border-radius: 5px;")
        self.refresh_btn.setStyleSheet(
            "background-color: #E9ECEF; color: #495057; padding: 10px; border-radius: 5px; border: 1px solid #CED4DA;"
        )

        button_layout.addWidget(self.entrada_btn)
        button_layout.addWidget(self.saida_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        self.main_layout.addLayout(button_layout)

        # tabela
        self.table_view = QTableView()
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.main_layout.addWidget(self.table_view)
        self.table_view.horizontalHeader().setSectionsClickable(False)

        # paginacao
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

        # conexoes
        self.entrada_btn.clicked.connect(self.open_entrada_dialog)
        self.saida_btn.clicked.connect(self.open_saida_dialog)
        self.delete_btn.clicked.connect(self.delete_item)  # opcional: exclui o produto do cadastro (atenção)
        self.refresh_btn.clicked.connect(self.load_data)

        self.prev_btn.clicked.connect(self.go_to_previous_page)
        self.next_btn.clicked.connect(self.go_to_next_page)

        self.load_data()

    # filtros
    def open_filter_dialog(self):
        dialog = FiltroEstoqueDialog(self.current_filters, parent=self)
        if dialog.exec():
            self.current_filters = dialog.filtrar()
            self.load_data(reset_page=True)

            if any(key in self.current_filters for key in ["produto", "min_qtd", "critico"]):
                self.filter_btn.setText("⚙️ FILTRO ATIVO")
                self.filter_btn.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; border-radius: 5px;")
            else:
                self.filter_btn.setText("⚙️ Filtro Avançado")
                self.filter_btn.setStyleSheet(
                    "background-color: #E0E0E0; color: #424242; font-weight: bold; border-radius: 5px; border: 1px solid #CCCCCC;"
                )

    # navegacao
    def go_to_previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def go_to_next_page(self):
        total_pages = (self.total_records + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_data()

    # carregar dados
    def load_data(self, reset_page=False):
        if reset_page:
            self.current_page = 1

        filtro = self.search_input.text().strip()

        try:
            base_query = select(Item)

            # filtro por texto (nome ou código)
            if filtro:
                base_query = base_query.where(
                    (Item.nome.ilike(f"%{filtro}%")) | (Item.codigo_item.ilike(f"%{filtro}%"))
                )

            # filtros avançados
            if self.current_filters.get("produto"):
                prod = self.current_filters["produto"]
                base_query = base_query.where(
                    (Item.nome.ilike(f"%{prod}%")) | (Item.codigo_item.ilike(f"%{prod}%"))
                )

            if self.current_filters.get("min_qtd") is not None:
                base_query = base_query.where(Item.estoque >= self.current_filters["min_qtd"])

            if self.current_filters.get("critico"):
                base_query = base_query.where(Item.estoque < Item.estoque_minimo)

            # total registros
            total_count = select(func.count()).select_from(base_query.subquery())
            self.total_records = self.session.execute(total_count).scalar_one()
            total_pages = (self.total_records + self.PAGE_SIZE - 1) // self.PAGE_SIZE
            if self.current_page > total_pages and total_pages > 0:
                self.current_page = total_pages
            elif total_pages == 0:
                self.current_page = 1

            offset = (self.current_page - 1) * self.PAGE_SIZE

            # ordenacao
            sort_field_name = self.current_filters.get("sort_column_field", "id")
            sort_direction = self.current_filters.get("sort_order", "DESC")
            sort_field = self.field_to_model.get(sort_field_name, Item.id)
            if sort_direction == "ASC":
                base_query = base_query.order_by(sort_field.asc())
            else:
                base_query = base_query.order_by(sort_field.desc())

            # executar query com paginação
            query = base_query.offset(offset).limit(self.PAGE_SIZE)
            items = self.session.execute(query).scalars().all()
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar dados.\n{e}")
            items = []
            total_pages = 1
            self.total_records = 0

        # montar tabela
        headers = ["ID", "Código", "Nome", "Estoque", "Estoque Mínimo", "Fornecedor", "Custo Unit.", "Preço Venda", "Última Mov."]
        model = QStandardItemModel(len(items), len(headers))
        model.setHorizontalHeaderLabels(headers)

        for row, it in enumerate(items):
            fornecedor_nome = ""
            try:
                fornecedor_nome = it.fornecedor.nome if hasattr(it, "fornecedor") and it.fornecedor else ""
            except Exception:
                fornecedor_nome = ""

            ultima_mov = ""
            try:
                if it.movimentos_estoque:
                    last = sorted(it.movimentos_estoque, key=lambda m: m.data_ultima_mov or date.min)[-1]
                    ultima_mov = last.data_ultima_mov.strftime("%d/%m/%Y")
            except Exception:
                ultima_mov = ""

            model.setItem(row, 0, QStandardItem(str(it.id)))
            model.setItem(row, 1, QStandardItem(it.codigo_item or ""))
            model.setItem(row, 2, QStandardItem(it.nome or ""))
            model.setItem(row, 3, QStandardItem(f"{float(it.estoque):,.2f}".replace(".", ",")))
            model.setItem(row, 4, QStandardItem(f"{float(it.estoque_minimo):,.2f}".replace(".", ",")))
            model.setItem(row, 5, QStandardItem(fornecedor_nome))
            model.setItem(row, 6, QStandardItem(f"{float(it.custo_unitario):,.2f}".replace(".", ",")))
            model.setItem(row, 7, QStandardItem(f"{float(it.preco_venda):,.2f}".replace(".", ",")))
            model.setItem(row, 8, QStandardItem(ultima_mov))

        self.table_view.setModel(model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)

        self.page_info_label.setText(f"Página {self.current_page} de {total_pages if total_pages > 0 else 1}")

        main_window = self.window()
        if hasattr(main_window, "total_registros_label"):
            main_window.total_registros_label.setText(f"Total: {self.total_records}")

    # seleção e dialogs
    def get_selected_item(self):
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "Aviso", "Selecione um item para continuar.")
            return None, None

        row = indexes[0].row()
        try:
            row_id = int(self.table_view.model().item(row, 0).text())
        except Exception:
            QMessageBox.warning(self, "Aviso", "ID inválido selecionado.")
            return None, None

        item = self.session.execute(select(Item).filter_by(id=row_id)).scalar_one_or_none()
        return item, row_id

    def open_entrada_dialog(self):
        item, _ = self.get_selected_item()
        if item:
            dialog = MovimentacaoDialog(self.session, item=item, type_="entrada", parent=self)
            if dialog.exec():
                self.load_data(reset_page=True)

    def open_saida_dialog(self):
        item, _ = self.get_selected_item()
        if item:
            dialog = MovimentacaoDialog(self.session, item=item, type_="saida", parent=self)
            if dialog.exec():
                self.load_data(reset_page=True)

    def delete_item(self):
        """
        Exclui o produto (atenção: operação irreversível). Mantive o botão
        porque estava no layout anterior, porém use com cautela.
        """
        item, row_id = self.get_selected_item()
        if not item:
            return

        reply = QMessageBox.question(
            self,
            "Excluir",
            f"Tem certeza que deseja excluir o item:\n\n{item.nome} ?\n\nIsto removerá o produto do cadastro (movimentos não serão apagados automaticamente).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.session.execute(delete(Item).where(Item.id == row_id))
                self.session.commit()
                QMessageBox.information(self, "Sucesso", "Item excluído.")
                self.load_data(reset_page=True)
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Erro", f"Erro ao excluir.\n{e}")
