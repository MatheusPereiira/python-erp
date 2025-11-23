from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QComboBox, QMessageBox, QSpinBox, QAbstractItemView, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QColor

class TelaVenda(QWidget):
    def __init__(self, sessao=None, sistema=None, parent=None):
        super().__init__(parent)
        self.sessao = sessao
        self.sistema = sistema
        
        # Estilos CSS baseados na sua imagem de referência (Cadastro)
        self.estilo_btn_verde = """
            QPushButton {
                background-color: #28a745; 
                color: white; 
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #218838; }
        """
        self.estilo_btn_vermelho = """
            QPushButton {
                background-color: #dc3545; 
                color: white; 
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #c82333; }
        """
        self.estilo_btn_azul = """
            QPushButton {
                background-color: #007bff; 
                color: white; 
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #0069d9; }
        """
        self.estilo_btn_branco = """
            QPushButton {
                background-color: #f8f9fa; 
                color: #333; 
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #e2e6ea; }
        """

        self.setup_ui()

    def setup_ui(self):
        """Configura a interface gráfica da tela de vendas com visual padronizado."""
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(15)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        
        # --- 1. Cabeçalho (Título) ---
        lbl_titulo = QLabel("Comercial - Nova Venda")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #444;")
        layout_principal.addWidget(lbl_titulo)

        # --- 2. Área de Cabeçalho da Venda (Cliente e Vendedor) ---
        # Vamos colocar em um Frame para destacar levemente
        frame_dados = QFrame()
        frame_dados.setStyleSheet("background-color: #fdfdfd; border: 1px solid #e0e0e0; border-radius: 5px;")
        layout_dados = QHBoxLayout(frame_dados)
        layout_dados.setContentsMargins(15, 15, 15, 15)

        # Cliente
        layout_cliente = QVBoxLayout()
        lbl_cliente = QLabel("Cliente:")
        lbl_cliente.setStyleSheet("font-weight: bold; color: #555;")
        layout_cliente.addWidget(lbl_cliente)
        
        self.combo_cliente = QComboBox()
        self.combo_cliente.setPlaceholderText("Selecione o Cliente")
        self.combo_cliente.addItems(["Cliente Balcão", "João Silva", "Maria Souza"]) # Placeholder
        self.combo_cliente.setStyleSheet("padding: 5px;")
        layout_cliente.addWidget(self.combo_cliente)
        
        layout_dados.addLayout(layout_cliente, 2) # Stretch factor 2 (ocupa mais espaço)

        # Vendedor
        layout_vendedor = QVBoxLayout()
        lbl_vendedor = QLabel("Vendedor:")
        lbl_vendedor.setStyleSheet("font-weight: bold; color: #555;")
        layout_vendedor.addWidget(lbl_vendedor)
        
        self.combo_vendedor = QComboBox()
        self.combo_vendedor.addItems(["Vendedor Padrão", "Vendedor 1", "Vendedor 2"]) # Placeholder
        self.combo_vendedor.setStyleSheet("padding: 5px;")
        layout_vendedor.addWidget(self.combo_vendedor)
        
        layout_dados.addLayout(layout_vendedor, 1)

        layout_principal.addWidget(frame_dados)

        # --- 3. Barra de Ações (Inputs do Item + Botões) ---
        # Aqui tentaremos imitar a barra de ferramentas da tela de Cadastro
        layout_acoes = QHBoxLayout()
        layout_acoes.setSpacing(10)

        # Input Produto (Imitando a barra de busca)
        self.input_produto = QLineEdit()
        self.input_produto.setPlaceholderText("🔍 Buscar produto por nome ou código...")
        self.input_produto.setStyleSheet("padding: 6px; border: 1px solid #ccc; border-radius: 4px;")
        layout_acoes.addWidget(self.input_produto, 3)

        # Input Quantidade
        self.input_qtd = QSpinBox()
        self.input_qtd.setRange(1, 9999)
        self.input_qtd.setValue(1)
        self.input_qtd.setFixedWidth(80)
        self.input_qtd.setStyleSheet("padding: 6px; border: 1px solid #ccc; border-radius: 4px;")
        layout_acoes.addWidget(self.input_qtd)

        # Botão Adicionar (Verde - Estilo "Adicionar" do Cadastro)
        self.btn_adicionar = QPushButton(" + Adicionar Item")
        self.btn_adicionar.setStyleSheet(self.estilo_btn_verde)
        self.btn_adicionar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_adicionar.clicked.connect(self.adicionar_item)
        layout_acoes.addWidget(self.btn_adicionar)

        # Botão Remover (Vermelho - Estilo "Excluir" do Cadastro)
        self.btn_remover = QPushButton(" X Remover Item")
        self.btn_remover.setStyleSheet(self.estilo_btn_vermelho)
        self.btn_remover.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remover.clicked.connect(self.remover_item)
        layout_acoes.addWidget(self.btn_remover)

        layout_principal.addLayout(layout_acoes)

        # --- 4. Tabela de Itens ---
        self.tabela_itens = QTableWidget()
        self.tabela_itens.setColumnCount(5)
        self.tabela_itens.setHorizontalHeaderLabels(["Código", "Produto", "Qtd", "Preço Un. (R$)", "Subtotal (R$)"])
        
        # Estilo da Tabela para parecer com a referência
        self.tabela_itens.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #eee;
                background-color: white;
                selection-background-color: #e6f0ff;
                selection-color: black;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 6px;
                border: 1px solid #ddd;
                font-weight: bold;
                color: #555;
            }
        """)
        self.tabela_itens.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Coluna Produto estica
        self.tabela_itens.verticalHeader().setVisible(False)
        self.tabela_itens.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela_itens.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        layout_principal.addWidget(self.tabela_itens)

        # --- 5. Rodapé (Totalizadores e Finalizar) ---
        frame_rodape = QFrame()
        frame_rodape.setStyleSheet("background-color: #f1f3f5; border-top: 1px solid #ddd;")
        layout_rodape = QHBoxLayout(frame_rodape)
        layout_rodape.setContentsMargins(20, 15, 20, 15)

        # Botão Cancelar (Estilo Branco/Cinza)
        btn_cancelar = QPushButton("Cancelar Venda")
        btn_cancelar.setStyleSheet(self.estilo_btn_branco)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.limpar_venda)
        layout_rodape.addWidget(btn_cancelar)

        layout_rodape.addStretch()

        # Label Total
        lbl_texto_total = QLabel("Total a Pagar:")
        lbl_texto_total.setStyleSheet("font-size: 14px; color: #666;")
        layout_rodape.addWidget(lbl_texto_total)

        self.lbl_total_valor = QLabel("R$ 0,00")
        self.lbl_total_valor.setStyleSheet("font-size: 24px; font-weight: bold; color: #28a745;")
        layout_rodape.addWidget(self.lbl_total_valor)

        # Espaçador
        layout_rodape.addSpacing(20)

        # Botão Finalizar (Azul - Estilo "Editar/Confirmar")
        self.btn_finalizar = QPushButton("✓ Finalizar Venda")
        self.btn_finalizar.setStyleSheet("""
            QPushButton {
                background-color: #007bff; 
                color: white; 
                font-weight: bold;
                font-size: 14px;
                border-radius: 4px;
                padding: 10px 25px;
            }
            QPushButton:hover { background-color: #0069d9; }
        """)
        self.btn_finalizar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_finalizar.clicked.connect(self.finalizar_venda)
        layout_rodape.addWidget(self.btn_finalizar)

        layout_principal.addWidget(frame_rodape)

        # Inicializa estado
        self.total_venda = 0.0

    def adicionar_item(self):
        """Adiciona item na tabela (Simulação visual)."""
        produto_texto = self.input_produto.text()
        qtd = self.input_qtd.value()
        
        if not produto_texto:
            QMessageBox.warning(self, "Atenção", "Digite o nome ou código do produto.")
            return

        # Aqui viria a lógica de buscar no banco 'cadastro_produto'
        # Simulando dados para teste:
        codigo = "001"
        preco_unitario = 15.50  # Preço fictício
        subtotal = preco_unitario * qtd

        row = self.tabela_itens.rowCount()
        self.tabela_itens.insertRow(row)
        
        self.tabela_itens.setItem(row, 0, QTableWidgetItem(codigo))
        self.tabela_itens.setItem(row, 1, QTableWidgetItem(produto_texto))
        self.tabela_itens.setItem(row, 2, QTableWidgetItem(str(qtd)))
        self.tabela_itens.setItem(row, 3, QTableWidgetItem(f"{preco_unitario:.2f}"))
        self.tabela_itens.setItem(row, 4, QTableWidgetItem(f"{subtotal:.2f}"))
        
        # Atualiza total
        self.total_venda += subtotal
        self.atualizar_total_lbl()

        # Limpa campos
        self.input_produto.clear()
        self.input_qtd.setValue(1)
        self.input_produto.setFocus()

    def remover_item(self):
        """Remove o item selecionado da tabela."""
        row = self.tabela_itens.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um item na tabela para remover.")
            return
        
        # Subtrai do total
        item_subtotal = self.tabela_itens.item(row, 4).text()
        self.total_venda -= float(item_subtotal.replace(",", ".")) # Tratamento simples
        self.atualizar_total_lbl()

        self.tabela_itens.removeRow(row)

    def limpar_venda(self):
        self.tabela_itens.setRowCount(0)
        self.total_venda = 0.0
        self.atualizar_total_lbl()
        self.input_produto.clear()

    def atualizar_total_lbl(self):
        self.lbl_total_valor.setText(f"R$ {self.total_venda:.2f}")

    def finalizar_venda(self):
        if self.tabela_itens.rowCount() == 0:
            QMessageBox.warning(self, "Vazia", "Adicione itens antes de finalizar.")
            return
        
        # Aqui entraria a lógica de gravar em 'pedido_venda' e 'pedido_venda_item'
        # e dar baixa no 'estoque' da tabela 'cadastro_produto'.
        
        QMessageBox.information(self, "Sucesso", f"Venda finalizada!\nTotal: R$ {self.total_venda:.2f}")
        self.limpar_venda()