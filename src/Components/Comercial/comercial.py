from PyQt6.QtWidgets import (
    QDialog, QLineEdit, QFormLayout, QTextEdit, QSizePolicy, QCheckBox,
    QComboBox, QGroupBox, QRadioButton, QVBoxLayout, QHBoxLayout, QMessageBox,
    QLabel, QPushButton
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from sqlalchemy import update
from datetime import datetime

from src.Models.models import Item 
from src.Utils.correcaoDeValores import  Converter_decimal, Converter_inteiro

class FiltroProdutosDialog(QDialog):
    def __init__(self, current_filters, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros Avançados de Produtos e Ordenação") 
        self.setFixedSize(400, 450) 
        
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        double_validator = QDoubleValidator(0.0, 9999999.99, 2)
        integer_validator = QIntValidator(0, 9999999) 

        status_group = QGroupBox("Status do Produto")
        status_layout = QHBoxLayout(status_group)
        self.radio_ativo = QRadioButton("Ativo")
        self.radio_inativo = QRadioButton("Inativo")
        self.radio_todos = QRadioButton("Todos")
        self.radio_todos.setChecked(True)
        
        status_layout.addWidget(self.radio_ativo)
        status_layout.addWidget(self.radio_inativo)
        status_layout.addWidget(self.radio_todos)
        form_layout.addRow(status_group)

        self.preco_min_input = QLineEdit()
        self.preco_min_input.setValidator(double_validator)
        self.preco_min_input.setPlaceholderText("R$ 0,00")
        form_layout.addRow("Preço Mínimo:", self.preco_min_input)

        self.preco_max_input = QLineEdit()
        self.preco_max_input.setValidator(double_validator)
        self.preco_max_input.setPlaceholderText("R$ 0,00")
        form_layout.addRow("Preço Máximo:", self.preco_max_input)

        self.estoque_max_input = QLineEdit() 
        self.estoque_max_input.setValidator(integer_validator) 
        self.estoque_max_input.setPlaceholderText("0")
        form_layout.addRow("Estoque Máximo (Atual):", self.estoque_max_input)
        
        sort_group = QGroupBox("Ordem da Tabela")
        sort_layout = QFormLayout(sort_group)
        
        self.sort_column_combo = QComboBox()
        self.sort_column_combo.addItems([
            "ID do Produto", 
            "Nome do Produto (Alfabética)", 
            "Estoque Atual", 
            "Preço de Venda"
        ])
        sort_layout.addRow("Ordenar Por:", self.sort_column_combo)
        
        self.sort_direction_combo = QComboBox()
        self.sort_direction_combo.addItems(["Crescente (ASC)", "Decrescente (DESC)"])
        self.sort_direction_combo.setCurrentIndex(1)
        sort_layout.addRow("Direção:", self.sort_direction_combo)
        
        form_layout.addRow(sort_group) 
        
        main_layout.addLayout(form_layout)
        main_layout.addStretch()
        
        button_layout = QHBoxLayout()
        self.limpar_btn = QPushButton("🧹 Limpar Filtros")
        self.aplicar_btn = QPushButton("✔️ Aplicar Filtros")
        self.aplicar_btn.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; border-radius: 5px;")

        button_layout.addWidget(self.limpar_btn)
        button_layout.addWidget(self.aplicar_btn)
        
        main_layout.addLayout(button_layout)

        self.limpar_btn.clicked.connect(self.limpar_filtros)
        self.aplicar_btn.clicked.connect(self.accept) 

        self.carregar_filtros(current_filters)


    def carregar_filtros(self, filters):
        if filters.get('ativo') is True:
            self.radio_ativo.setChecked(True)
        elif filters.get('ativo') is False:
            self.radio_inativo.setChecked(True)
        else:
            self.radio_todos.setChecked(True)

        if filters.get('preco_min'):
             self.preco_min_input.setText(f"{filters['preco_min']:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
        
        if filters.get('preco_max'): 
             self.preco_max_input.setText(f"{filters['preco_max']:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))

        if filters.get('estoque_max'): 
             self.estoque_max_input.setText(str(int(filters['estoque_max'])))

        if filters.get('sort_column_field') is not None:
             column_map = {
                'id': 0, 'nome': 1, 'estoque': 2, 'preco_venda': 3
             }
             index = column_map.get(filters['sort_column_field'], 0)
             self.sort_column_combo.setCurrentIndex(index)
        
        if filters.get('sort_order'):
             direction_index = 0 if filters['sort_order'] == 'ASC' else 1
             self.sort_direction_combo.setCurrentIndex(direction_index)

    def filtrar(self):
        filters = {}

        if self.radio_ativo.isChecked():
            filters['ativo'] = True
        elif self.radio_inativo.isChecked():
            filters['ativo'] = False

        preco_min = Converter_decimal(self.preco_min_input.text()) 
        if preco_min is not None and preco_min >= 0:
            filters['preco_min'] = preco_min
            
        preco_max = Converter_decimal(self.preco_max_input.text()) 
        if preco_max is not None and preco_max >= 0:
            filters['preco_max'] = preco_max

        estoque_max = Converter_inteiro(self.estoque_max_input.text()) 
        if estoque_max is not None and estoque_max >= 0:
            filters['estoque_max'] = estoque_max
        
        sort_map = ["id", "nome", "estoque", "preco_venda"] 
        selected_index = self.sort_column_combo.currentIndex()
        
        filters['sort_column_field'] = sort_map[selected_index]
        filters['sort_order'] = 'ASC' if self.sort_direction_combo.currentIndex() == 0 else 'DESC'
            
        return filters


    def limpar_filtros(self):
        self.radio_todos.setChecked(True)
        self.preco_min_input.clear()
        self.preco_max_input.clear() 
        self.estoque_max_input.clear() 
        
        self.sort_column_combo.setCurrentIndex(0) 
        self.sort_direction_combo.setCurrentIndex(1) 
        
        self.accept() 

class CadastroProdutosDialog(QDialog):
    def __init__(self, session, item=None, parent=None):
        super().__init__(parent)
        self.session = session
        self.item = item 
        self.is_editing = item is not None
        
        titulo = "Editar - Cadastro Produtos" if self.is_editing else "Adicionar - Cadastro Produtos"
        self.setWindowTitle(titulo)
        self.setMinimumSize(550, 450)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        title_label = QLabel(titulo)
        title_label.setStyleSheet("font-size: 16pt; padding: 10px; background-color: #E6F0FF; border: 1px solid #B3CDE6;")
        main_layout.addWidget(title_label)
        
        double_validator = QDoubleValidator(0.0, 9999999.99, 2)
        integer_validator = QIntValidator(0, 9999999)

        self.id_label = QLabel(str(item.id) if self.is_editing else "Automático")
        self.codigo_input = QLineEdit() 
        self.produto_input = QLineEdit()
        self.custo_input = QLineEdit() 
        self.preco_input = QLineEdit()
        self.estoque_input = QLineEdit()
        self.estoque_minimo_input = QLineEdit() 
        self.descricao_input = QTextEdit() 
        self.ativo_check = QCheckBox("Produto Ativo") 

        self.custo_input.setValidator(double_validator)
        self.preco_input.setValidator(double_validator)
        self.estoque_input.setValidator(integer_validator) 
        self.estoque_minimo_input.setValidator(integer_validator) 
        
        self.descricao_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ativo_check.setChecked(True)

        form_layout.addRow("Id:", self.id_label)
        form_layout.addRow("Código Item:", self.codigo_input)
        form_layout.addRow("Nome Produto:", self.produto_input)
        form_layout.addRow("Custo Unitário (R$):", self.custo_input)
        form_layout.addRow("Preço Venda (R$):", self.preco_input)
        form_layout.addRow("Estoque Atual:", self.estoque_input)
        form_layout.addRow("Estoque Mínimo:", self.estoque_minimo_input)
        form_layout.addRow("Descrição:", self.descricao_input)
        form_layout.addRow("Status:", self.ativo_check)
        
        main_layout.addLayout(form_layout)
        main_layout.addStretch()

        if self.is_editing:
            self.preencher_formulario()
            
        # Botões
        button_layout = QHBoxLayout()
        self.cancelar_btn = QPushButton("❌ Cancelar")
        self.salvar_btn = QPushButton("✅ Salvar")
        self.salvar_btn.setStyleSheet("background-color: #28A745; color: white; font-weight: bold;")

        button_layout.addStretch()
        button_layout.addWidget(self.cancelar_btn)
        button_layout.addWidget(self.salvar_btn)
        
        main_layout.addLayout(button_layout)

        self.cancelar_btn.clicked.connect(self.reject)
        self.salvar_btn.clicked.connect(self.salvar_produto)

    def preencher_formulario(self):
        if self.item:
            self.codigo_input.setText(self.item.codigo_item or "")
            self.produto_input.setText(self.item.nome or "")
            self.custo_input.setText(f"{self.item.custo_unitario:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
            self.preco_input.setText(f"{self.item.preco_venda:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
            
            self.estoque_input.setText(str(int(self.item.estoque or 0)))
            self.estoque_minimo_input.setText(str(int(self.item.estoque_minimo or 0)))
            
            self.descricao_input.setText(self.item.descricao or "")
            self.ativo_check.setChecked(self.item.ativo)

    def carregar_dados_formulario(self):
        data = {}
        try:
            data['nome'] = self.produto_input.text().strip()
            data['codigo_item'] = self.codigo_input.text().strip()
            data['descricao'] = self.descricao_input.toPlainText().strip()
            data['ativo'] = self.ativo_check.isChecked()

            data['custo_unitario'] = Converter_decimal(self.custo_input.text())
            data['preco_venda'] = Converter_decimal(self.preco_input.text())
            
            data['estoque'] = Converter_inteiro(self.estoque_input.text())
            data['estoque_minimo'] = Converter_inteiro(self.estoque_minimo_input.text())

            if not data['nome'] or not data['codigo_item']:
                raise ValueError("Nome e Código do Item são obrigatórios.")
            
            return data
        
        except ValueError as e:
            QMessageBox.warning(self, "Erro de Validação", f"{e}")
            return None
        except Exception as e:
            QMessageBox.critical(self, "Erro na Conversão", f"Ocorreu um erro ao processar os dados numéricos. Verifique o formato.\nErro: {e}")
            return None

    def salvar_produto(self):
        data = self.carregar_dados_formulario()
        if data is None:
            return

        if self.is_editing:
            reply = QMessageBox.question(self, 'Confirmar Alteração',
                f"Tem certeza que deseja salvar as alterações no produto '{self.item.nome}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.No:
                return 

            try:
                self.session.execute(
                    update(Item).where(Item.id == self.item.id).values(**data)
                )
                self.session.commit()
                QMessageBox.information(self, "Sucesso", "Produto atualizado com sucesso!")
                self.accept()
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Erro no BD", f"Não foi possível atualizar o produto.\nErro: {e}")
        else:
            novo_item = Item(
                **data,
                tipo_item='PRODUTO',
                data_cadastro=datetime.utcnow()
            )
            try:
                self.session.add(novo_item)
                self.session.commit()
                QMessageBox.information(self, "Sucesso", "Produto cadastrado com sucesso!")
                self.accept() 
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Erro no BD", f"Não foi possível salvar o produto.\nErro: {e}")
# src/Components/Comercial/comercial.py

class PedidosCompra:
    def __init__(self, sessao):
        self.sessao = sessao

    def criar_pedido(self, fornecedor, itens, valor_total, condicao_pagamento):
        print("Pedido de compra criado (básico).")
        # implementar depois
        return True

    def listar_pedidos(self):
        print("Listando pedidos de compra...")
        return []


class PedidosVenda:
    def __init__(self, sessao):
        self.sessao = sessao

    def criar_pedido(self, cliente, itens, valor_total, condicao_pagamento):
        print("Pedido de venda criado (básico).")
        # implementar depois
        return True

    def listar_pedidos(self):
        print("Listando pedidos de venda...")
        return []


class ComercialSistema:
    def __init__(self, sessao):
        self.sessao = sessao

        # Módulos internos
        self.pedidos_compra = PedidosCompra(sessao)
        self.pedidos_venda = PedidosVenda(sessao)

    def sincronizar(self):
        print("Sincronizando comercial...")
        # futuramente sincroniza com DB / estoque
        return True
