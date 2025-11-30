# sistemacomercial/src/Components/Comercial/tela_venda.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QComboBox, QMessageBox, QSpinBox, 
    QAbstractItemView, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon, QIntValidator
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray
from sqlalchemy import select
from decimal import Decimal
from datetime import date

from src.Models.models import Item, PedidoVenda, PedidoVendaItem, Entidade, Usuario, Perfil
from src.Utils.validacoes_comercial import ValidadorComercial

class TelaVenda(QWidget):
    def __init__(self, sessao=None, sistema=None, parent=None):
        super().__init__(parent)
        self.sessao = sessao
        self.sistema = sistema
        self.produtos_cache = {}
        self.validador = ValidadorComercial(sessao)
        
        # Variáveis para descontos
        self.subtotal_venda = 0.0
        self.desconto_percentual = 0.0
        self.desconto_valor = 0.0
        self.total_venda = 0.0
        
        # SVG das setas
        self.svg_seta_baixo = """
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2.5 3.5L5 6.5L7.5 3.5H2.5Z" fill="#495057"/>
        </svg>
        """
        
        # DEFINIR TODOS OS ESTILOS ANTES de setup_ui()
        self.definir_estilos()
        
        self.setup_ui()

        # Inicializa estado
        self.itens_venda = []
        
        # Carrega produtos iniciais
        self.atualizar_lista_produtos()
        
        # Carregar dados reais do banco
        self.carregar_clientes_reais()
        self.carregar_vendedores_reais()

    def definir_estilos(self):
        """Define todos os estilos CSS antes de criar a interface"""
        self.estilo_titulo = """
            QLabel {
                font-size: 20pt; 
                font-weight: bold; 
                margin-bottom: 10px;
                color: #424242;
            }
        """
        
        self.estilo_btn_verde = """
            QPushButton {
                background-color: #28a745; 
                color: white; 
                font-weight: bold;
                border-radius: 5px;
                padding: 10px;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover { 
                background-color: #218838; 
                color: white;
            }
        """
        
        self.estilo_btn_vermelho = """
            QPushButton {
                background-color: #dc3545; 
                color: white; 
                font-weight: bold;
                border-radius: 5px;
                padding: 10px;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover { 
                background-color: #c82333; 
                color: white;
            }
        """
        
        self.estilo_btn_azul = """
            QPushButton {
                background-color: #007bff; 
                color: white; 
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 25px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { 
                background-color: #0069d9; 
                color: white;
            }
        """
        
        self.estilo_btn_branco = """
            QPushButton {
                background-color: #E9ECEF; 
                color: #495057; 
                border: 1px solid #CED4DA;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { 
                background-color: #e2e6ea; 
                color: #495057;
                border: 1px solid #adb5bd;
            }
        """
        
        self.estilo_combo = """
            QComboBox {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 5px;
                background-color: white;
                color: #495057;
                font-size: 12px;
            }
            QComboBox:hover {
                border: 1px solid #6c757d;
            }
            QComboBox:focus {
                border: 1px solid #007bff;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
        """
        
        self.estilo_input = """
            QLineEdit, QDoubleSpinBox {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 5px;
                background-color: white;
                color: #495057;
                font-size: 12px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border: 1px solid #007bff;
            }
            QLineEdit:hover, QDoubleSpinBox:hover {
                border: 1px solid #6c757d;
            }
        """
        
        self.estilo_frame = """
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 5px;
            }
        """
        
        self.estilo_tabela = """
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                gridline-color: #e9ecef;
                background-color: white;
                selection-background-color: #e6f0ff;
                selection-color: #495057;
                color: #495057;
                alternate-background-color: #f8f9fa;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }
            QTableWidget::item:selected {
                background-color: #e6f0ff;
                color: #495057;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 12px 8px;
                border: none;
                border-bottom: 1px solid #dee2e6;
                font-weight: bold;
                color: #495057;
                font-size: 12px;
            }
        """
        
        self.estilo_label = """
            QLabel {
                color: #495057;
                font-weight: 500;
                font-size: 12px;
            }
        """

    def setup_ui(self):
        """Configura a interface gráfica da tela de vendas"""
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(15)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        
        # --- 1. Cabeçalho (Título) ---
        lbl_titulo = QLabel("Comercial - Nova Venda")
        lbl_titulo.setStyleSheet(self.estilo_titulo)
        layout_principal.addWidget(lbl_titulo)

        # --- 2. Área de Cabeçalho da Venda (Cliente e Vendedor) ---
        frame_dados = QFrame()
        frame_dados.setStyleSheet(self.estilo_frame)
        layout_dados = QHBoxLayout(frame_dados)
        layout_dados.setContentsMargins(15, 15, 15, 15)

        # Cliente
        layout_cliente = QVBoxLayout()
        lbl_cliente = QLabel("Cliente:")
        lbl_cliente.setStyleSheet(self.estilo_label)
        layout_cliente.addWidget(lbl_cliente)
        
        self.combo_cliente = QComboBox()
        self.combo_cliente.setPlaceholderText("Selecione o Cliente")
        self.combo_cliente.setStyleSheet(self.estilo_combo)
        self.combo_cliente.setEditable(False)
        layout_cliente.addWidget(self.combo_cliente)
        
        layout_dados.addLayout(layout_cliente, 2)

        # Vendedor
        layout_vendedor = QVBoxLayout()
        lbl_vendedor = QLabel("Vendedor:")
        lbl_vendedor.setStyleSheet(self.estilo_label)
        layout_vendedor.addWidget(lbl_vendedor)
        
        self.combo_vendedor = QComboBox()
        self.combo_vendedor.setStyleSheet(self.estilo_combo)
        self.combo_vendedor.setEditable(False)
        layout_vendedor.addWidget(self.combo_vendedor)
        
        layout_dados.addLayout(layout_vendedor, 1)

        layout_principal.addWidget(frame_dados)

        # --- 3. Barra de Ações (Inputs do Item + Botões) ---
        layout_acoes = QHBoxLayout()
        layout_acoes.setSpacing(10)

        # ComboBox para seleção de produtos
        self.combo_produtos = QComboBox()
        self.combo_produtos.setFixedWidth(300)
        self.combo_produtos.setStyleSheet(self.estilo_combo)
        self.combo_produtos.setPlaceholderText("Selecione um produto...")
        self.combo_produtos.setEditable(False)
        layout_acoes.addWidget(self.combo_produtos)

        # Input de busca
        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("🔍 Buscar produto por nome ou código...")
        self.input_busca.setStyleSheet(self.estilo_input)
        self.input_busca.textChanged.connect(self.atualizar_lista_produtos)
        layout_acoes.addWidget(self.input_busca, 2)

        # Input Quantidade
        lbl_qtd = QLabel("Qtd:")
        lbl_qtd.setStyleSheet(self.estilo_label)
        layout_acoes.addWidget(lbl_qtd)
        
        self.input_qtd = QSpinBox()
        self.input_qtd.setRange(1, 9999)
        self.input_qtd.setValue(1)
        self.input_qtd.setFixedWidth(80)
        self.input_qtd.setStyleSheet(self.estilo_input)
        self.input_qtd.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        layout_acoes.addWidget(self.input_qtd)

        # Botão Adicionar
        self.btn_adicionar = QPushButton("➕ Adicionar")
        self.btn_adicionar.setStyleSheet(self.estilo_btn_verde)
        self.btn_adicionar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_adicionar.clicked.connect(self.adicionar_item)
        layout_acoes.addWidget(self.btn_adicionar)

        # Botão Remover
        self.btn_remover = QPushButton("❌ Excluir")
        self.btn_remover.setStyleSheet(self.estilo_btn_vermelho)
        self.btn_remover.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remover.clicked.connect(self.remover_item)
        layout_acoes.addWidget(self.btn_remover)

        layout_principal.addLayout(layout_acoes)

        # --- 4. Tabela de Itens ---
        self.tabela_itens = QTableWidget()
        self.tabela_itens.setColumnCount(6)
        self.tabela_itens.setHorizontalHeaderLabels(["ID", "Código", "Produto", "Qtd", "Preço Un. (R$)", "Subtotal (R$)"])
        
        self.tabela_itens.setStyleSheet(self.estilo_tabela)
        self.tabela_itens.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabela_itens.setColumnHidden(0, True)
        self.tabela_itens.verticalHeader().setVisible(False)
        self.tabela_itens.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela_itens.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela_itens.setAlternatingRowColors(True)
        
        layout_principal.addWidget(self.tabela_itens)

        # --- 5. Área de Descontos ---
        frame_descontos = QFrame()
        frame_descontos.setStyleSheet(self.estilo_frame)
        layout_descontos = QHBoxLayout(frame_descontos)
        layout_descontos.setContentsMargins(15, 15, 15, 15)

        # Subtotal
        layout_subtotal = QVBoxLayout()
        lbl_subtotal = QLabel("Subtotal:")
        lbl_subtotal.setStyleSheet(self.estilo_label)
        layout_subtotal.addWidget(lbl_subtotal)
        
        self.lbl_subtotal_valor = QLabel("R$ 0,00")
        self.lbl_subtotal_valor.setStyleSheet("font-size: 16px; font-weight: bold; color: #6c757d;")
        layout_subtotal.addWidget(self.lbl_subtotal_valor)
        layout_descontos.addLayout(layout_subtotal)

        # Desconto Percentual
        layout_desconto_percentual = QVBoxLayout()
        lbl_desconto_perc = QLabel("Desconto (%):")
        lbl_desconto_perc.setStyleSheet(self.estilo_label)
        layout_desconto_percentual.addWidget(lbl_desconto_perc)
        
        self.input_desconto_percentual = QDoubleSpinBox()
        self.input_desconto_percentual.setRange(0, 100)
        self.input_desconto_percentual.setValue(0)
        self.input_desconto_percentual.setSuffix("%")
        self.input_desconto_percentual.setStyleSheet(self.estilo_input)
        self.input_desconto_percentual.valueChanged.connect(self.calcular_desconto_percentual)
        layout_desconto_percentual.addWidget(self.input_desconto_percentual)
        layout_descontos.addLayout(layout_desconto_percentual)

        # Desconto em Valor
        layout_desconto_valor = QVBoxLayout()
        lbl_desconto_valor = QLabel("Desconto (R$):")
        lbl_desconto_valor.setStyleSheet(self.estilo_label)
        layout_desconto_valor.addWidget(lbl_desconto_valor)
        
        self.input_desconto_valor = QDoubleSpinBox()
        self.input_desconto_valor.setRange(0, 999999.99)
        self.input_desconto_valor.setValue(0)
        self.input_desconto_valor.setPrefix("R$ ")
        self.input_desconto_valor.setStyleSheet(self.estilo_input)
        self.input_desconto_valor.valueChanged.connect(self.calcular_desconto_valor)
        layout_desconto_valor.addWidget(self.input_desconto_valor)
        layout_descontos.addLayout(layout_desconto_valor)

        # Label do Desconto Total
        layout_desconto_total = QVBoxLayout()
        lbl_desconto_total = QLabel("Desconto Total:")
        lbl_desconto_total.setStyleSheet(self.estilo_label)
        layout_desconto_total.addWidget(lbl_desconto_total)
        
        self.lbl_desconto_total_valor = QLabel("R$ 0,00")
        self.lbl_desconto_total_valor.setStyleSheet("font-size: 16px; font-weight: bold; color: #dc3545;")
        layout_desconto_total.addWidget(self.lbl_desconto_total_valor)
        layout_descontos.addLayout(layout_desconto_total)

        layout_principal.addWidget(frame_descontos)

        # --- 6. Rodapé (Totalizadores e Finalizar) ---
        frame_rodape = QFrame()
        frame_rodape.setStyleSheet(self.estilo_frame)
        layout_rodape = QHBoxLayout(frame_rodape)
        layout_rodape.setContentsMargins(20, 15, 20, 15)

        # Botão Cancelar
        btn_cancelar = QPushButton("❌ Cancelar Venda")
        btn_cancelar.setStyleSheet(self.estilo_btn_branco)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.limpar_venda)
        layout_rodape.addWidget(btn_cancelar)

        # Botão Limpar Descontos
        btn_limpar_descontos = QPushButton("🧹 Limpar Descontos")
        btn_limpar_descontos.setStyleSheet(self.estilo_btn_branco)
        btn_limpar_descontos.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_limpar_descontos.clicked.connect(self.limpar_descontos)
        layout_rodape.addWidget(btn_limpar_descontos)

        layout_rodape.addStretch()

        # Label Total
        lbl_texto_total = QLabel("Total a Pagar:")
        lbl_texto_total.setStyleSheet("font-size: 16px; color: #495057; font-weight: bold;")
        layout_rodape.addWidget(lbl_texto_total)

        self.lbl_total_valor = QLabel("R$ 0,00")
        self.lbl_total_valor.setStyleSheet("font-size: 24px; font-weight: bold; color: #28a745; margin-left: 10px;")
        layout_rodape.addWidget(self.lbl_total_valor)

        # Espaçador
        layout_rodape.addSpacing(20)

        # Botão Finalizar
        self.btn_finalizar = QPushButton("✅ Finalizar Venda")
        self.btn_finalizar.setStyleSheet(self.estilo_btn_azul)
        self.btn_finalizar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_finalizar.clicked.connect(self.finalizar_venda)
        layout_rodape.addWidget(self.btn_finalizar)

        layout_principal.addWidget(frame_rodape)

    # ============================================================
    # MÉTODOS DE PRODUTOS
    # ============================================================

    def buscar_produtos_banco(self, termo=""):
        """Busca produtos no banco de dados por nome ou código"""
        try:
            query = select(Item).where(Item.ativo == True)
            
            if termo.strip():
                query = query.where(
                    (Item.nome.ilike(f'%{termo}%')) | 
                    (Item.codigo_item.ilike(f'%{termo}%'))
                )
            
            query = query.order_by(Item.nome)
            produtos = self.sessao.execute(query).scalars().all()
            
            self.produtos_cache.clear()
            
            for produto in produtos:
                self.produtos_cache[produto.id] = produto
                
            return produtos
            
        except Exception as e:
            print(f"Erro ao buscar produtos: {e}")
            return []

    def atualizar_lista_produtos(self):
        """Atualiza a lista de produtos baseado no termo de busca"""
        termo = self.input_busca.text()
        produtos = self.buscar_produtos_banco(termo)
        
        self.combo_produtos.clear()
        self.combo_produtos.addItem("Selecione um produto...", None)
        
        for produto in produtos:
            estoque_texto = f"Estoque: {produto.estoque}" if produto.estoque > 0 else "SEM ESTOQUE"
            texto = f"{produto.nome} ({produto.codigo_item}) - R$ {produto.preco_venda:.2f} - {estoque_texto}"
            self.combo_produtos.addItem(texto, produto.id)

    # ============================================================
    # MÉTODOS DE CLIENTES E VENDEDORES
    # ============================================================

    def carregar_clientes_reais(self):
        """Carrega clientes reais do banco para o combo"""
        try:
            query = select(Entidade).where(
                (Entidade.tipo_entidade.ilike('%cliente%')) |
                (Entidade.tipo_entidade.is_(None))
            ).order_by(Entidade.nome_fantasia, Entidade.razao_social)
            
            clientes = self.sessao.execute(query).scalars().all()
            
            self.combo_cliente.clear()
            
            # Adicionar cliente balcão (ID = None)
            self.combo_cliente.addItem("Cliente Balcão", None)
            
            for cliente in clientes:
                nome = cliente.nome_fantasia or cliente.razao_social or f"Cliente #{cliente.id}"
                self.combo_cliente.addItem(nome, cliente.id)
                
            print(f"Carregados {len(clientes)} clientes do banco")
                
        except Exception as e:
            print(f"Erro ao carregar clientes: {e}")
            # Fallback mínimo
            self.combo_cliente.clear()
            self.combo_cliente.addItem("Cliente Balcão", None)
            self.combo_cliente.addItem("João Silva", 1)
            self.combo_cliente.addItem("Maria Souza", 2)

    def carregar_vendedores_reais(self):
        """Carrega vendedores reais do banco para o combo"""
        try:
            query = select(Usuario).join(Perfil).where(
                (Perfil.cargo.in_(['VENDAS', 'ADMINISTRADOR']))
            ).order_by(Usuario.nome)
            
            vendedores = self.sessao.execute(query).scalars().all()
            
            self.combo_vendedor.clear()
            
            for vendedor in vendedores:
                nome_completo = f"{vendedor.nome} ({vendedor.perfil.cargo.value})"
                self.combo_vendedor.addItem(nome_completo, vendedor.id)
                
            # Se não encontrou vendedores, adiciona opção padrão
            if self.combo_vendedor.count() == 0:
                self.combo_vendedor.addItem("Vendedor Padrão", 1)
                
            print(f"Carregados {len(vendedores)} vendedores do banco")
                
        except Exception as e:
            print(f"Erro ao carregar vendedores: {e}")
            # Fallback mínimo
            self.combo_vendedor.clear()
            self.combo_vendedor.addItem("Vendedor Padrão", 1)

    def obter_cliente_id(self):
        """Obtém o ID real do cliente selecionado"""
        return self.combo_cliente.currentData()

    def obter_vendedor_id(self):
        """Obtém o ID real do vendedor selecionado"""
        return self.combo_vendedor.currentData()

    # ============================================================
    # MÉTODOS DE DESCONTO
    # ============================================================

    def calcular_subtotal(self):
        """Calcula o subtotal da venda (sem descontos)"""
        self.subtotal_venda = 0.0
        for row in range(self.tabela_itens.rowCount()):
            subtotal_item = float(self.tabela_itens.item(row, 5).text())
            self.subtotal_venda += subtotal_item
        
        self.lbl_subtotal_valor.setText(f"R$ {self.subtotal_venda:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        self.calcular_totais()

    def calcular_desconto_percentual(self, valor):
        """Calcula desconto baseado em porcentagem"""
        self.desconto_percentual = valor
        self.calcular_totais()
        
        # Sincroniza com desconto em valor se necessário
        if self.subtotal_venda > 0:
            desconto_valor_calculado = self.subtotal_venda * (valor / 100)
            # Evita loop infinito desconectando temporariamente
            self.input_desconto_valor.valueChanged.disconnect()
            self.input_desconto_valor.setValue(desconto_valor_calculado)
            self.input_desconto_valor.valueChanged.connect(self.calcular_desconto_valor)

    def calcular_desconto_valor(self, valor):
        """Calcula desconto baseado em valor fixo"""
        self.desconto_valor = valor
        self.calcular_totais()
        
        # Sincroniza com desconto percentual se necessário
        if self.subtotal_venda > 0:
            desconto_percentual_calculado = (valor / self.subtotal_venda) * 100
            # Evita loop infinito desconectando temporariamente
            self.input_desconto_percentual.valueChanged.disconnect()
            self.input_desconto_percentual.setValue(desconto_percentual_calculado)
            self.input_desconto_percentual.valueChanged.connect(self.calcular_desconto_percentual)

    def calcular_totais(self):
        """Calcula totais finais com descontos aplicados"""
        # Usa o maior desconto entre percentual e valor
        desconto_calculado = self.subtotal_venda * (self.desconto_percentual / 100)
        desconto_final = max(desconto_calculado, self.desconto_valor)
        
        # Limita o desconto ao subtotal
        desconto_final = min(desconto_final, self.subtotal_venda)
        
        self.total_venda = self.subtotal_venda - desconto_final
        
        # Atualiza labels
        self.lbl_desconto_total_valor.setText(f"-R$ {desconto_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        self.lbl_total_valor.setText(f"R$ {self.total_venda:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    def limpar_descontos(self):
        """Limpa todos os descontos aplicados"""
        self.input_desconto_percentual.setValue(0)
        self.input_desconto_valor.setValue(0)
        self.desconto_percentual = 0.0
        self.desconto_valor = 0.0
        self.calcular_totais()

    # ============================================================
    # MÉTODOS DE GESTÃO DE ITENS
    # ============================================================

    def adicionar_item(self):
        """Adiciona item na tabela com validação"""
        if self.combo_produtos.currentIndex() == 0:
            QMessageBox.warning(self, "Atenção", "Selecione um produto válido.")
            return

        produto_id = self.combo_produtos.currentData()
        qtd = self.input_qtd.value()
        
        produto = self.produtos_cache.get(produto_id)
        if not produto:
            QMessageBox.warning(self, "Erro", "Produto não encontrado no banco de dados.")
            return

        if produto.estoque <= 0:
            QMessageBox.warning(self, "Estoque Insuficiente", "Produto sem estoque disponível.")
            return
            
        if qtd > produto.estoque:
            QMessageBox.warning(
                self, 
                "Estoque Insuficiente", 
                f"Estoque disponível: {produto.estoque}\nQuantidade solicitada: {qtd}"
            )
            return

        for row in range(self.tabela_itens.rowCount()):
            item_id = int(self.tabela_itens.item(row, 0).text())
            if item_id == produto_id:
                QMessageBox.warning(self, "Produto Duplicado", "Este produto já foi adicionado à venda.")
                return

        preco_unitario = float(produto.preco_venda)
        subtotal = preco_unitario * qtd

        row = self.tabela_itens.rowCount()
        self.tabela_itens.insertRow(row)
        
        self.tabela_itens.setItem(row, 0, QTableWidgetItem(str(produto_id)))
        self.tabela_itens.setItem(row, 1, QTableWidgetItem(produto.codigo_item or "N/A"))
        self.tabela_itens.setItem(row, 2, QTableWidgetItem(produto.nome))
        self.tabela_itens.setItem(row, 3, QTableWidgetItem(str(qtd)))
        self.tabela_itens.setItem(row, 4, QTableWidgetItem(f"{preco_unitario:.2f}"))
        self.tabela_itens.setItem(row, 5, QTableWidgetItem(f"{subtotal:.2f}"))

        # Recalcula subtotal e totais
        self.calcular_subtotal()

        self.combo_produtos.setCurrentIndex(0)
        self.input_qtd.setValue(1)
        self.input_busca.clear()
        self.input_busca.setFocus()

    def remover_item(self):
        """Remove o item selecionado da tabela"""
        row = self.tabela_itens.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um item na tabela para remover.")
            return
        
        self.tabela_itens.removeRow(row)
        
        # Recalcula subtotal e totais
        self.calcular_subtotal()

    def limpar_venda(self):
        """Limpa toda a venda atual"""
        self.tabela_itens.setRowCount(0)
        self.subtotal_venda = 0.0
        self.total_venda = 0.0
        self.limpar_descontos()
        self.calcular_subtotal()
        self.combo_produtos.setCurrentIndex(0)
        self.input_busca.clear()
        self.input_qtd.setValue(1)

    # ============================================================
    # MÉTODOS DE FINALIZAÇÃO DE VENDA
    # ============================================================

    def preparar_dados_venda(self):
        """Prepara os dados da venda para validação"""
        itens_venda = []
        
        for row in range(self.tabela_itens.rowCount()):
            produto_id = int(self.tabela_itens.item(row, 0).text())
            produto_nome = self.tabela_itens.item(row, 2).text()
            quantidade = int(self.tabela_itens.item(row, 3).text())
            preco_unitario = float(self.tabela_itens.item(row, 4).text())
            
            item = {
                'produto_id': produto_id,
                'produto_nome': produto_nome,
                'quantidade': quantidade,
                'preco_unitario': preco_unitario
            }
            itens_venda.append(item)
        
        # Obter IDs reais
        cliente_id = self.obter_cliente_id()
        vendedor_id = self.obter_vendedor_id()
        
        # Inclui informações de desconto
        dados_venda = {
            'cliente_id': cliente_id,
            'cliente_nome': self.combo_cliente.currentText(),
            'vendedor_id': vendedor_id,
            'vendedor_nome': self.combo_vendedor.currentText(),
            'valor_total': self.total_venda,
            'subtotal': self.subtotal_venda,
            'desconto_percentual': self.desconto_percentual,
            'desconto_valor': self.desconto_valor,
            'itens': itens_venda
        }
        
        return dados_venda

    def finalizar_venda(self):
        """Finaliza a venda com todas as validações"""
        if self.tabela_itens.rowCount() == 0:
            QMessageBox.warning(self, "Venda Vazia", "Adicione itens antes de finalizar.")
            return
        
        # Preparar dados para validação
        dados_venda = self.preparar_dados_venda()
        
        # Validar venda
        if not self.validador.validar_venda_completa(dados_venda, self):
            return  # Se houver erros, não continua
        
        # Confirmar venda
        resposta = QMessageBox.question(
            self,
            "Confirmar Venda",
            f"Confirmar venda no valor de R$ {self.total_venda:.2f}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if resposta != QMessageBox.StandardButton.Yes:
            return
        
        # Processar venda
        try:
            self.processar_venda(dados_venda)
            
        except Exception as e:
            self.sessao.rollback()
            QMessageBox.critical(
                self, 
                "Erro ao Finalizar Venda", 
                f"Erro ao registrar venda no banco:\n{str(e)}"
            )

    def processar_venda(self, dados_venda):
        """Processa a venda no banco de dados com informações de desconto"""
        from decimal import Decimal
        
        pedido = PedidoVenda(
            cliente_id=dados_venda['cliente_id'],
            vendedor_id=dados_venda['vendedor_id'],
            data_emissao=date.today(),
            data_entrada=date.today(),
            status='F',  # Finalizada
            preco_total=Decimal(str(dados_venda['valor_total']))
        )
        
        self.sessao.add(pedido)
        self.sessao.flush()
        
        # Processar itens e atualizar estoque
        for item_dict in dados_venda['itens']:
            produto_id = item_dict['produto_id']
            quantidade = item_dict['quantidade']
            preco_unitario = Decimal(str(item_dict['preco_unitario']))
            preco_total = preco_unitario * Decimal(str(quantidade))
            
            # Buscar produto
            produto = self.produtos_cache.get(produto_id)
            if produto:
                # Atualizar estoque
                produto.estoque -= quantidade
                
                # Adicionar item ao pedido
                item_pedido = PedidoVendaItem(
                    pedido_id=pedido.id,
                    produto=produto.nome,
                    quantidade=quantidade,
                    preco_unitario=preco_unitario,
                    preco_total=preco_total
                )
                self.sessao.add(item_pedido)
        
        self.sessao.commit()
        
        # Mensagem com informações de desconto
        mensagem = f"""Venda registrada com sucesso!

Nº Pedido: {pedido.id}
Subtotal: R$ {dados_venda['subtotal']:,.2f}
Desconto: -R$ {dados_venda['desconto_valor']:,.2f} ({dados_venda['desconto_percentual']:.1f}%)
Total: R$ {self.total_venda:,.2f}"""
        
        QMessageBox.information(self, "Venda Finalizada", mensagem)
        
        self.limpar_venda()

    def load_data(self):
        """Método para compatibilidade com o sistema principal"""
        pass

    def svg_to_icon(self, svg_string):
        """Converte SVG string para QIcon"""
        try:
            svg_data = QByteArray(svg_string.encode('utf-8'))
            renderer = QSvgRenderer(svg_data)
            if renderer.isValid():
                pixmap = QPixmap(12, 12)
                pixmap.fill(Qt.GlobalColor.transparent)
                renderer.render(pixmap)
                return QIcon(pixmap)
        except:
            pass
        return QIcon()