# src/Views/cadastro_produto_view.py

from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QLabel, QMessageBox,
    QLineEdit, QDialog, QHeaderView, QAbstractItemView
)
from sqlalchemy import select, func, delete, or_
import sys

# Modelos do Banco (Ajustado para o novo models.py)
from src.Models.models import Item, Entidade

# SEUS DIALOGS ORIGINAIS (Certifique-se que o arquivo cadastro_produto_dialog.py está nesta pasta)
# Se estiver na mesma pasta 'Views', o import é direto. 
# Se estiver em 'src/Components/Cadastro', ajuste o import abaixo:
try:
    from src.Components.Cadastro.cadastro_produto_dialog import CadastroProdutosDialog, FiltroProdutosDialog
except ImportError:
    # Tenta importar da mesma pasta caso você tenha movido o arquivo
    from .cadastro_produto_dialog import CadastroProdutosDialog, FiltroProdutosDialog

class CadastroProdutosWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.main_layout = QVBoxLayout(self)

        self.PAGE_SIZE = 20
        self.current_page = 1
        self.total_records = 0
        
        # Mapeamento para ordenação
        self.field_to_model = { 
            'id': Item.id,
            'codigo_item': Item.codigo_item,
            'nome': Item.nome,
            'preco_venda': Item.preco_venda,
            'estoque': Item.estoque,
        }
        
        self.current_filters = {} 

        # --- 1. TÍTULO ---
        self.title_label = QLabel("Cadastro Produtos")
        self.title_label.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 10px;")
        self.main_layout.addWidget(self.title_label)
        
        # --- 2. BARRA DE BUSCA E FILTRO ---
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

        # --- 3. BOTÕES DE AÇÃO ---
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

        # --- 4. TABELA ---
        self.table_view = QTableView()
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) 
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)    
        self.main_layout.addWidget(self.table_view)
        self.table_view.horizontalHeader().setSectionsClickable(False)

        # --- 5. PAGINAÇÃO ---
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

        # --- CONEXÕES ---
        self.add_btn.clicked.connect(self.open_add_dialog)
        self.edit_btn.clicked.connect(self.open_edit_dialog) 
        self.delete_btn.clicked.connect(self.delete_item)     
        self.refresh_btn.clicked.connect(self.load_data) 
        self.prev_btn.clicked.connect(self.go_to_previous_page)
        self.next_btn.clicked.connect(self.go_to_next_page)

        # Carrega dados iniciais
        self.load_data()

    # --- LÓGICA DE DADOS ---

    def load_data(self, reset_page=False):
        if reset_page:
            self.current_page = 1

        filtro_texto = self.search_input.text().strip()
        try:
            base_query = select(Item)
            
            # Filtro de Texto
            if filtro_texto:
                base_query = base_query.where(
                    (Item.nome.ilike(f'%{filtro_texto}%')) |
                    (Item.codigo_item.ilike(f'%{filtro_texto}%'))
                )
            
            # Filtros Avançados (Se existirem no dicionário)
            if self.current_filters.get('ativo') is not None:
                base_query = base_query.where(Item.ativo == self.current_filters.get('ativo'))

            if self.current_filters.get('preco_min') is not None:
                base_query = base_query.where(Item.preco_venda >= self.current_filters.get('preco_min'))

            if self.current_filters.get('preco_max') is not None:
                base_query = base_query.where(Item.preco_venda <= self.current_filters.get('preco_max'))

            # Paginação
            total_count_query = select(func.count()).select_from(base_query.subquery())
            self.total_records = self.session.execute(total_count_query).scalar_one()
            
            total_pages = (self.total_records + self.PAGE_SIZE - 1) // self.PAGE_SIZE
            if total_pages == 0: total_pages = 1
            if self.current_page > total_pages: self.current_page = total_pages

            offset = (self.current_page - 1) * self.PAGE_SIZE
            
            # Ordenação padrão por ID decrescente (mais recentes primeiro)
            query = base_query.order_by(Item.id.desc()).limit(self.PAGE_SIZE).offset(offset)
            items = self.session.execute(query).scalars().all()

        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            items = []
            total_pages = 1

        # Preencher Tabela
        headers = ["Id", "Código", "Nome do Produto", "Preço Venda (R$)", "Custo (R$)", "Estoque", "Fornecedor", "Ativo"]
        model = QStandardItemModel(len(items), len(headers))
        model.setHorizontalHeaderLabels(headers)

        for row, item in enumerate(items):
            model.setItem(row, 0, QStandardItem(str(item.id)))
            model.setItem(row, 1, QStandardItem(item.codigo_item or ""))
            model.setItem(row, 2, QStandardItem(item.nome or ""))
            
            preco_venda = float(item.preco_venda) if item.preco_venda else 0.0
            model.setItem(row, 3, QStandardItem(f"{preco_venda:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')))
            
            custo_unit = float(item.custo_unitario) if item.custo_unitario else 0.0
            model.setItem(row, 4, QStandardItem(f"{custo_unit:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')))
            
            estoque = int(item.estoque) if item.estoque else 0
            model.setItem(row, 5, QStandardItem(str(estoque)))
            
            # Nome do Fornecedor (Proteção contra None)
            nome_fornecedor = "-"
            if item.fornecedor:
                nome_fornecedor = item.fornecedor.nome_fantasia or item.fornecedor.razao_social
            model.setItem(row, 6, QStandardItem(nome_fornecedor))
            
            status_item = QStandardItem("✅ Sim" if item.ativo else "❌ Não")
            status_item.setForeground(QColor("green") if item.ativo else QColor("red"))
            model.setItem(row, 7, status_item)

        self.table_view.setModel(model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.hideColumn(4) # Ocultar custo se desejar
        
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)
        self.page_info_label.setText(f"Página {self.current_page} de {total_pages}")

    def go_to_previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def go_to_next_page(self):
        self.current_page += 1
        self.load_data()

    def get_selected_item(self):
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "Aviso", "Selecione um produto na tabela.")
            return None, None
        
        # Pega o ID da primeira coluna (índice 0)
        item_id_text = self.table_view.model().item(indexes[0].row(), 0).text()
        item_id = int(item_id_text)
        item = self.session.get(Item, item_id)
        return item, item_id

    def delete_item(self):
        item, item_id = self.get_selected_item()
        if not item: return

        reply = QMessageBox.question(self, 'Excluir', 
            f"Deseja excluir permanentemente o produto '{item.nome}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Exclusão Lógica (Recomendado) ou Física
                # self.session.delete(item) # Física
                item.ativo = False # Lógica
                self.session.commit()
                self.load_data(reset_page=True)
                QMessageBox.information(self, "Sucesso", "Produto desativado/excluído!")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Erro", f"Erro ao excluir: {e}")

    # --- DIALOGS EXTERNOS ---
    def open_add_dialog(self):
        # Abre o Dialog importado
        try:
            dialog = CadastroProdutosDialog(self.session, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data(reset_page=True)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir cadastro: {e}")

    def open_edit_dialog(self):
        item, item_id = self.get_selected_item()
        if item:
            try:
                dialog = CadastroProdutosDialog(self.session, item=item, parent=self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao abrir edição: {e}")

    def open_filter_dialog(self):
        try:
            dialog = FiltroProdutosDialog(self.current_filters, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.current_filters = dialog.get_filters()
                self.load_data(reset_page=True)
                
                # Muda cor do botão se tiver filtro
                if self.current_filters:
                    self.filter_btn.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; border-radius: 5px;")
                    self.filter_btn.setText("⚙️ Filtro Ativo")
                else:
                    self.filter_btn.setStyleSheet("background-color: #E0E0E0; color: #424242; font-weight: bold; border-radius: 5px;")
                    self.filter_btn.setText("⚙️ Filtro Avançado")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro no filtro: {e}")