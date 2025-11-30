# src/Components/Comercial/tela_compra.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QComboBox, QMessageBox, QSpinBox, 
    QAbstractItemView, QDateEdit, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QDate
from sqlalchemy import select
from datetime import datetime

class TelaCompra(QWidget):
    def __init__(self, sessao=None, sistema=None, parent=None):
        super().__init__(parent)
        self.sessao = sessao
        self.sistema = sistema
        self.itens_compra = []
        
        print("TelaCompra inicializada!")  # Debug
        
        self.setup_ui()

    def setup_ui(self):
        """Configura a interface gráfica da tela de compras"""
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(15)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        
        # 1. Cabeçalho
        lbl_titulo = QLabel("Comercial - Entrada de Nota Fiscal (Compra)")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #444;")
        layout_principal.addWidget(lbl_titulo)

        # 2. Dados da Compra
        frame_dados = QFrame()
        frame_dados.setStyleSheet("background-color: #fdfdfd; border: 1px solid #e0e0e0; border-radius: 5px;")
        layout_dados = QFormLayout(frame_dados)
        layout_dados.setContentsMargins(15, 15, 15, 15)

        # Fornecedor
        self.combo_fornecedor = QComboBox()
        self.combo_fornecedor.setPlaceholderText("Selecione o Fornecedor")
        self.carregar_fornecedores()
        # Aplique o estilo ao combobox de fornecedores
        combobox_style = """
        QComboBox {
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 5px;
            min-width: 150px;
        }
        QComboBox:hover {
            border: 1px solid #007bff;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #ccc;
        }
        QComboBox QAbstractItemView {
            background-color: white;
            border: 1px solid #ccc;
            selection-background-color: #e6f0ff;
            selection-color: black;
            outline: none;
        }
        QComboBox QAbstractItemView::item {
            padding: 5px;
            color: black;
        }
        QComboBox QAbstractItemView::item:hover {
            background-color: #e6f0ff;
            color: black;
        }
        QComboBox QAbstractItemView::item:selected {
            background-color: #007bff;
            color: white;
        }
        """
        self.combo_fornecedor.setStyleSheet(combobox_style)
        layout_dados.addRow("Fornecedor:", self.combo_fornecedor)

        # Número da Nota Fiscal
        self.input_nf = QLineEdit()
        self.input_nf.setPlaceholderText("Número da Nota Fiscal")
        layout_dados.addRow("Nota Fiscal:", self.input_nf)

        # Data da Compra
        self.input_data = QDateEdit()
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setCalendarPopup(True)
        layout_dados.addRow("Data da Compra:", self.input_data)

        layout_principal.addWidget(frame_dados)

        # 3. Busca de Produtos
        frame_busca = QGroupBox("Adicionar Produtos à Compra")
        layout_busca = QHBoxLayout(frame_busca)

        self.input_busca_produto = QLineEdit()
        self.input_busca_produto.setPlaceholderText("🔍 Buscar produto por nome ou código...")
        self.input_busca_produto.textChanged.connect(self.buscar_produtos)
        layout_busca.addWidget(self.input_busca_produto)

        self.combo_produtos = QComboBox()
        self.combo_produtos.setPlaceholderText("Selecione um produto")
        # Aplique o estilo ao combobox de produtos
        self.combo_produtos.setStyleSheet(combobox_style)
        layout_busca.addWidget(self.combo_produtos)

        self.input_qtd = QSpinBox()
        self.input_qtd.setRange(1, 9999)
        self.input_qtd.setValue(1)
        self.input_qtd.setFixedWidth(80)
        layout_busca.addWidget(QLabel("Quantidade:"))
        layout_busca.addWidget(self.input_qtd)

        self.input_preco = QLineEdit()
        self.input_preco.setPlaceholderText("Preço unitário")
        self.input_preco.setFixedWidth(120)
        layout_busca.addWidget(QLabel("Preço Unitário:"))
        layout_busca.addWidget(self.input_preco)

        self.btn_adicionar = QPushButton(" + Adicionar")
        self.btn_adicionar.setStyleSheet("""
            QPushButton {
                background-color: #28a745; 
                color: white; 
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        self.btn_adicionar.clicked.connect(self.adicionar_item)
        layout_busca.addWidget(self.btn_adicionar)

        layout_principal.addWidget(frame_busca)

        # 4. Tabela de Itens da Compra
        self.tabela_itens = QTableWidget()
        self.tabela_itens.setColumnCount(6)
        self.tabela_itens.setHorizontalHeaderLabels(["ID", "Produto", "Qtd", "Preço Un. (R$)", "Subtotal (R$)", "Ações"])
        
        self.tabela_itens.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #eee;
                background-color: white;
                selection-background-color: #e6f0ff;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 6px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        self.tabela_itens.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabela_itens.verticalHeader().setVisible(False)
        self.tabela_itens.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        layout_principal.addWidget(self.tabela_itens)

        # 5. Rodapé com Total e Botões
        frame_rodape = QFrame()
        layout_rodape = QHBoxLayout(frame_rodape)

        btn_limpar = QPushButton("🗑️ Limpar")
        btn_limpar.setStyleSheet("background-color: #6c757d; color: white; padding: 10px; border-radius: 5px;")
        btn_limpar.clicked.connect(self.limpar_compra)
        layout_rodape.addWidget(btn_limpar)

        layout_rodape.addStretch()

        lbl_total = QLabel("Total da Compra:")
        lbl_total.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout_rodape.addWidget(lbl_total)

        self.lbl_total_valor = QLabel("R$ 0,00")
        self.lbl_total_valor.setStyleSheet("font-size: 20px; font-weight: bold; color: #dc3545;")
        layout_rodape.addWidget(self.lbl_total_valor)

        layout_rodape.addSpacing(20)

        self.btn_finalizar = QPushButton("✓ Finalizar Compra")
        self.btn_finalizar.setStyleSheet("""
            QPushButton {
                background-color: #007bff; 
                color: white; 
                font-weight: bold;
                border-radius: 4px;
                padding: 10px 25px;
            }
            QPushButton:hover { background-color: #0069d9; }
        """)
        self.btn_finalizar.clicked.connect(self.finalizar_compra)
        layout_rodape.addWidget(self.btn_finalizar)

        layout_principal.addWidget(frame_rodape)

        self.carregar_produtos()

    def carregar_fornecedores(self):
        """Carrega a lista de fornecedores do banco de dados"""
        try:
            from src.Models.models import Fornecedor
            print("🔍 Buscando fornecedores no banco...")  # DEBUG
            
            fornecedores = self.sessao.execute(select(Fornecedor)).scalars().all()
            print(f"📋 Encontrados {len(fornecedores)} fornecedores")  # DEBUG
            
            self.combo_fornecedor.clear()
            self.combo_fornecedor.addItem("Selecione um fornecedor", None)
            
            for fornecedor in fornecedores:
                self.combo_fornecedor.addItem(fornecedor.nome, fornecedor.id)
                print(f"   ➕ {fornecedor.nome} (ID: {fornecedor.id})")  # DEBUG
                
            print("✅ Fornecedores carregados no combobox")  # DEBUG
            
        except Exception as e:
            print(f"❌ Erro ao carregar fornecedores: {e}")  # DEBUG
            QMessageBox.warning(self, "Erro", f"Erro ao carregar fornecedores: {e}")

    def carregar_produtos(self):
        """Carrega a lista completa de produtos"""
        try:
            from src.Models.models import Item
            self.produtos = self.sessao.execute(
                select(Item).where(Item.ativo == True)
            ).scalars().all()
            print(f"Carregados {len(self.produtos)} produtos")  # Debug
        except Exception as e:
            print(f"Erro ao carregar produtos: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar produtos: {e}")
            self.produtos = []

    def buscar_produtos(self):
        """Filtra produtos baseado no texto de busca"""
        texto = self.input_busca_produto.text().lower()
        self.combo_produtos.clear()
        self.combo_produtos.addItem("Selecione um produto", None)
        
        for produto in self.produtos:
            if (texto in produto.nome.lower() or 
                (produto.codigo_item and texto in produto.codigo_item.lower())):
                self.combo_produtos.addItem(
                    f"{produto.codigo_item} - {produto.nome}", 
                    produto.id
                )

    def adicionar_item(self):
        """Adiciona item à lista de compra"""
        produto_id = self.combo_produtos.currentData()
        quantidade = self.input_qtd.value()
        
        try:
            preco_texto = self.input_preco.text().replace(",", ".")
            preco = float(preco_texto) if preco_texto else 0.0
        except ValueError:
            QMessageBox.warning(self, "Erro", "Preço unitário inválido")
            return

        if not produto_id:
            QMessageBox.warning(self, "Erro", "Selecione um produto")
            return

        # Busca dados completos do produto
        try:
            from src.Models.models import Item
            produto = self.sessao.execute(
                select(Item).where(Item.id == produto_id)
            ).scalar_one()

            # Adiciona à lista interna
            item_compra = {
                'id': produto.id,
                'nome': produto.nome,
                'codigo': produto.codigo_item,
                'quantidade': quantidade,
                'preco_unitario': preco,
                'subtotal': quantidade * preco
            }
            self.itens_compra.append(item_compra)

            # Atualiza tabela
            self.atualizar_tabela_itens()
            self.calcular_total()

            # Limpa campos
            self.input_busca_produto.clear()
            self.combo_produtos.setCurrentIndex(0)
            self.input_qtd.setValue(1)
            self.input_preco.clear()

        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao adicionar item: {e}")

    def remover_item(self, row):
        """Remove item da lista de compra"""
        if 0 <= row < len(self.itens_compra):
            self.itens_compra.pop(row)
            self.atualizar_tabela_itens()
            self.calcular_total()

    def atualizar_tabela_itens(self):
        """Atualiza a tabela de itens com a lista atual"""
        self.tabela_itens.setRowCount(len(self.itens_compra))
        
        for row, item in enumerate(self.itens_compra):
            self.tabela_itens.setItem(row, 0, QTableWidgetItem(str(item['id'])))
            self.tabela_itens.setItem(row, 1, QTableWidgetItem(item['nome']))
            self.tabela_itens.setItem(row, 2, QTableWidgetItem(str(item['quantidade'])))
            self.tabela_itens.setItem(row, 3, QTableWidgetItem(f"{item['preco_unitario']:.2f}"))
            self.tabela_itens.setItem(row, 4, QTableWidgetItem(f"{item['subtotal']:.2f}"))
            
            # Botão remover
            btn_remover = QPushButton("❌")
            btn_remover.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545; 
                    color: white; 
                    font-weight: bold;
                    border-radius: 4px;
                    padding: 2px 6px;
                }
                QPushButton:hover { background-color: #c82333; }
            """)
            btn_remover.clicked.connect(lambda checked, r=row: self.remover_item(r))
            self.tabela_itens.setCellWidget(row, 5, btn_remover)

    def calcular_total(self):
        """Calcula o total da compra"""
        total = sum(item['subtotal'] for item in self.itens_compra)
        self.lbl_total_valor.setText(f"R$ {total:.2f}")

    def limpar_compra(self):
        """Limpa todos os dados da compra atual"""
        self.itens_compra.clear()
        self.atualizar_tabela_itens()
        self.calcular_total()
        self.input_nf.clear()
        self.combo_fornecedor.setCurrentIndex(0)

    def finalizar_compra(self):
        """Finaliza a compra e salva no banco de dados"""
        if not self.itens_compra:
            QMessageBox.warning(self, "Erro", "Adicione itens à compra antes de finalizar")
            return

        if not self.combo_fornecedor.currentData():
            QMessageBox.warning(self, "Erro", "Selecione um fornecedor")
            return

        if not self.input_nf.text().strip():
            QMessageBox.warning(self, "Erro", "Informe o número da nota fiscal")
            return

        try:
            from src.Models.models import PedidoCompra, PedidoCompraItem, Item
            
            # Cria pedido de compra
            pedido_compra = PedidoCompra(
                # Note: ajuste conforme sua model - pode precisar de mais campos
                data_emissao=self.input_data.date().toPyDate(),
                preco_total=sum(item['subtotal'] for item in self.itens_compra)
            )
            self.sessao.add(pedido_compra)
            self.sessao.flush()  # Para obter o ID

            # Adiciona itens do pedido
            for item in self.itens_compra:
                pedido_item = PedidoCompraItem(
                    pedido_id=pedido_compra.id,
                    quantidade=item['quantidade'],
                    preco_unitario=item['preco_unitario'],
                    preco_total=item['subtotal']
                )
                self.sessao.add(pedido_item)

                # Atualiza estoque do produto
                produto = self.sessao.execute(
                    select(Item).where(Item.id == item['id'])
                ).scalar_one()
                produto.estoque = (produto.estoque or 0) + item['quantidade']

            self.sessao.commit()

            QMessageBox.information(self, "Sucesso", 
                                  f"Compra finalizada com sucesso!\n"
                                  f"Total: R$ {pedido_compra.preco_total:.2f}\n"
                                  f"Estoque atualizado")

            self.limpar_compra()

        except Exception as e:
            self.sessao.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao finalizar compra: {e}")

    def showEvent(self, event):
        """Chamado quando a tela é mostrada"""
        super().showEvent(event)
        print("🖥️ TelaCompra foi aberta - recarregando fornecedores...")
        self.carregar_fornecedores()