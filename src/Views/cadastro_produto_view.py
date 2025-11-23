from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QLabel, QMessageBox,
    QLineEdit, QDialog, QHeaderView, QSizePolicy, QApplication, QSplitter
)
from sqlalchemy import select, update, func, delete
from decimal import Decimal
import re
import sys

from src.Models.models import Item 
from src.Components.Cadastro.cadastro_produto_dialog import CadastroProdutosDialog, FiltroProdutosDialog

class CadastroProdutosWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.main_layout = QVBoxLayout(self)

        self.PAGE_SIZE = 20
        self.current_page = 1
        self.total_records = 0
        
        self.field_to_model = { 
            'id': Item.id,
            'codigo_item': Item.codigo_item,
            'nome': Item.nome,
            'preco_venda': Item.preco_venda,
            'estoque': Item.estoque,
        }
        
        self.column_to_field = { 
            0: Item.id,
            1: Item.codigo_item,
            2: Item.nome,
            3: Item.preco_venda,
            4: Item.custo_unitario, 
            5: Item.estoque,
            6: Item.ativo
        }
        
        self.current_filters = {} 

        self.title_label = QLabel("Cadastro Produtos")
        self.title_label.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 10px;")
        self.main_layout.addWidget(self.title_label)
        
        search_filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nome do produto ou código...")
        self.search_input.textChanged.connect(lambda: self.load_data(reset_page=True))
        
        self.filter_btn = QPushButton("⚙️ Filtro Avançado")
        self.filter_btn.setStyleSheet("background-color: #E0E0E0; color: #424242; font-weight: bold; border-radius: 5px; border: 1px solid #CCCCCC;")
        self.filter_btn.setFixedWidth(150)
        self.filter_btn.clicked.connect(self.open_filter_dialog)

        search_filter_layout.addWidget(self.search_input)
        search_filter_layout.addWidget(self.filter_btn)
        self.main_layout.addLayout(search_filter_layout)


        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Adicionar")
        self.edit_btn = QPushButton("📝 Editar")
        self.delete_btn = QPushButton("❌ Excluir")
        self.refresh_btn = QPushButton("🔄 Atualizar")
        
        self.add_btn.setStyleSheet("background-color: #28a745; color: white; padding: 10px; border-radius: 5px;")
        self.edit_btn.setStyleSheet("background-color: #007bff; color: white; padding: 10px; border-radius: 5px;")
        self.delete_btn.setStyleSheet("background-color: #dc3545; color: white; padding: 10px; border-radius: 5px;")
        self.refresh_btn.setStyleSheet("background-color: #E9ECEF; color: #495057; padding: 10px; border-radius: 5px; border: 1px solid #CED4DA;")

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch() 
        
        self.main_layout.addLayout(button_layout)

        self.table_view = QTableView()
        self.table_view.verticalHeader().setVisible(False)
        
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows) 
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)   
        self.main_layout.addWidget(self.table_view)

        self.table_view.horizontalHeader().setSectionsClickable(False)

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

        self.add_btn.clicked.connect(self.open_add_dialog)
        self.edit_btn.clicked.connect(self.open_edit_dialog) 
        self.delete_btn.clicked.connect(self.delete_item)    
        self.refresh_btn.clicked.connect(self.load_data) 
        
        self.prev_btn.clicked.connect(self.go_to_previous_page)
        self.next_btn.clicked.connect(self.go_to_next_page)

        self.load_data()

    
    def open_filter_dialog(self):
        dialog = FiltroProdutosDialog(self.current_filters, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_filters = dialog.get_filters()
            self.load_data(reset_page=True)
            
            is_filter_active = any(key in self.current_filters for key in ['ativo', 'preco_min', 'preco_max', 'estoque_max']) or \
                               (self.current_filters.get('sort_column_field') != 'id') or \
                               (self.current_filters.get('sort_order') != 'DESC')
            
            if is_filter_active:
                self.filter_btn.setText("⚙️ FILTRO ATIVO")
                self.filter_btn.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; border-radius: 5px;")
            else:
                self.filter_btn.setText("⚙️ Filtro Avançado")
                self.filter_btn.setStyleSheet("background-color: #E0E0E0; color: #424242; font-weight: bold; border-radius: 5px; border: 1px solid #CCCCCC;")


    def go_to_previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def go_to_next_page(self):
        total_pages = (self.total_records + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_data()

    def load_data(self, reset_page=False):
        
        if reset_page:
            self.current_page = 1

        filtro_texto = self.search_input.text().strip()
        try:
            base_query = select(Item)
            if filtro_texto:
                base_query = base_query.where(
                    (Item.nome.ilike(f'%{filtro_texto}%')) |
                    (Item.codigo_item.ilike(f'%{filtro_texto}%'))
                )
            
            
            ativo_filter = self.current_filters.get('ativo')
            if ativo_filter is not None:
                base_query = base_query.where(Item.ativo == ativo_filter)

            preco_min_filter = self.current_filters.get('preco_min')
            if preco_min_filter is not None:
                base_query = base_query.where(Item.preco_venda >= preco_min_filter)

            preco_max_filter = self.current_filters.get('preco_max')
            if preco_max_filter is not None:
                base_query = base_query.where(Item.preco_venda <= preco_max_filter)


            estoque_max_filter = self.current_filters.get('estoque_max')
            if estoque_max_filter is not None:
                base_query = base_query.where(Item.estoque <= estoque_max_filter)


            total_count_query = select(func.count()).select_from(base_query.subquery())
            self.total_records = self.session.execute(total_count_query).scalar_one()
            
            total_pages = (self.total_records + self.PAGE_SIZE - 1) // self.PAGE_SIZE
            
            if self.current_page > total_pages and total_pages > 0:
                 self.current_page = total_pages
            elif total_pages == 0:
                 self.current_page = 1

            offset = (self.current_page - 1) * self.PAGE_SIZE
            
            sort_field_name = self.current_filters.get('sort_column_field', 'id') 
            sort_direction = self.current_filters.get('sort_order', 'DESC')
            
            sort_field = self.field_to_model.get(sort_field_name, Item.id) 
            
            if sort_direction == 'ASC':
                base_query = base_query.order_by(sort_field.asc())
            else:
                base_query = base_query.order_by(sort_field.desc())
                
            query = base_query.limit(self.PAGE_SIZE).offset(offset)

            items = self.session.execute(query).scalars().all()
        except Exception as e:
            QMessageBox.critical(self, "Erro de Dados", f"Não foi possível carregar os produtos.\nErro: {e}")
            items = []
            total_pages = 1
            self.total_records = 0

        headers = ["Id", "Código", "Nome do Produto", "Preço Venda (R$)", "Custo (R$)", "Estoque", "Ativo"]
        model = QStandardItemModel(len(items), len(headers))
        model.setHorizontalHeaderLabels(headers)

        for row, item in enumerate(items):
            model.setItem(row, 0, QStandardItem(str(item.id)))
            model.setItem(row, 1, QStandardItem(item.codigo_item or ""))
            model.setItem(row, 2, QStandardItem(item.nome or ""))
            model.setItem(row, 3, QStandardItem(f"{item.preco_venda:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')))
            model.setItem(row, 4, QStandardItem(f"{item.custo_unitario:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')))
            model.setItem(row, 5, QStandardItem(str(int(item.estoque or 0))))
            model.setItem(row, 6, QStandardItem("✅ Sim" if item.ativo else "❌ Não"))

        self.table_view.setModel(model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.hideColumn(4) 
        
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)
        self.page_info_label.setText(f"Página {self.current_page} de {total_pages if total_pages > 0 else 1}")

        main_window = self.window()
        if hasattr(main_window, 'total_registros_label'):
             main_window.total_registros_label.setText(f"Total de registros: {self.total_records}")

    def open_add_dialog(self):
        dialog = CadastroProdutosDialog(self.session, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data(reset_page=True) 

    def get_selected_item(self):
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "Seleção", "Selecione um produto na tabela para continuar.")
            return None, None

        selected_row = indexes[0].row()
        item_id = int(self.table_view.model().item(selected_row, 0).text())
        
        item = self.session.execute(select(Item).filter_by(id=item_id)).scalar_one_or_none()
        return item, item_id

    def open_edit_dialog(self):
        item, item_id = self.get_selected_item()
        if item:
            dialog = CadastroProdutosDialog(self.session, item=item, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()

    def delete_item(self):
        item, item_id = self.get_selected_item()
        if item:
            reply = QMessageBox.question(self, 'Excluir Item',
                f"Tem certeza que deseja EXCLUIR PERMANENTEMENTE o produto '{item.nome}'?\n"
                f"(Esta ação é **irreversível** e remove o registro do banco de dados. "
                f"Se deseja apenas desativar, use o botão 'Editar'.)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.No:
                return
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.session.execute(
                        delete(Item).where(Item.id == item_id) 
                    )
                    self.session.commit()
                    QMessageBox.information(self, "Sucesso", "Produto excluído permanentemente com sucesso!")
                    self.load_data(reset_page=True) 
                except Exception as e:
                    self.session.rollback()
                    QMessageBox.critical(self, "Erro no Banco de Dados", f"Erro ao excluir o item: {e}")