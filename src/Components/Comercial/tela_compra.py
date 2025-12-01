# src/Components/Comercial/tela_compra.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QComboBox, QMessageBox, QSpinBox, 
    QAbstractItemView, QDateEdit, QFormLayout, QGroupBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QDate
from sqlalchemy import select, or_
from datetime import date, datetime

# Agora importamos Entidade em vez de Fornecedor
from src.Models.models import (
    Item, PedidoCompra, PedidoCompraItem, Entidade, 
    MovimentoEstoque, Financeiro, EnumStatus
)

class TelaCompra(QWidget):
    def __init__(self, sessao=None, sistema=None, parent=None):
        super().__init__(parent)
        self.sessao = sessao
        self.sistema = sistema
        
        self.itens_compra = []
        self.total_compra_float = 0.0
        
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
        grupo_dados = QGroupBox("Dados da Nota Fiscal")
        grupo_dados.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #ccc; padding: 10px; margin-top: 10px; }")
        layout_dados = QHBoxLayout(grupo_dados)
        
        # Fornecedor (Agora busca de Entidade)
        layout_dados.addWidget(QLabel("Fornecedor:"))
        self.combo_fornecedor = QComboBox()
        self.combo_fornecedor.setPlaceholderText("Selecione o Fornecedor")
        self.combo_fornecedor.setMinimumWidth(250)
        self.combo_fornecedor.setStyleSheet("QComboBox { background-color: white; border: 1px solid #ccc; padding: 5px; }")
        self.carregar_fornecedores() # Função atualizada abaixo
        layout_dados.addWidget(self.combo_fornecedor)

        # NF e Data
        layout_dados.addWidget(QLabel("NF:"))
        self.input_nf = QLineEdit()
        self.input_nf.setPlaceholderText("Nº Nota Fiscal")
        self.input_nf.setFixedWidth(150)
        layout_dados.addWidget(self.input_nf)

        layout_dados.addWidget(QLabel("Data:"))
        self.input_data = QDateEdit()
        self.input_data.setDate(QDate.currentDate())
        self.input_data.setCalendarPopup(True)
        self.input_data.setFixedWidth(120)
        layout_dados.addWidget(self.input_data)
        
        layout_dados.addStretch()
        layout_principal.addWidget(grupo_dados)

        # 3. Busca de Produtos (Visual Ajustado)
        grupo_busca = QGroupBox("Adicionar Produtos à Compra")
        grupo_busca.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #ccc; padding: 10px; margin-top: 10px; }")
        layout_busca = QHBoxLayout(grupo_busca)

        layout_busca.addWidget(QLabel("Produto:"))
        self.combo_produtos = QComboBox()
        self.combo_produtos.setPlaceholderText("Selecione um produto")
        self.combo_produtos.setStyleSheet("QComboBox { background-color: white; border: 1px solid #ccc; padding: 5px; }")
        self.combo_produtos.setMinimumWidth(250)
        self.carregar_produtos()
        layout_busca.addWidget(self.combo_produtos)

        layout_busca.addWidget(QLabel("Qtd:"))
        self.input_qtd = QSpinBox()
        self.input_qtd.setRange(1, 9999)
        self.input_qtd.setValue(1)
        self.input_qtd.setFixedWidth(80)
        layout_busca.addWidget(self.input_qtd)

        layout_busca.addWidget(QLabel("Custo Unit:"))
        self.input_preco = QDoubleSpinBox()
        self.input_preco.setRange(0.0, 999999.99)
        self.input_preco.setPrefix("R$ ")
        self.input_preco.setDecimals(2)
        self.input_preco.setFixedWidth(100)
        layout_busca.addWidget(self.input_preco)

        self.btn_adicionar = QPushButton(" + Adicionar")
        self.btn_adicionar.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; border-radius: 4px; padding: 6px 12px; } QPushButton:hover { background-color: #218838; }")
        self.btn_adicionar.clicked.connect(self.adicionar_item)
        layout_busca.addWidget(self.btn_adicionar)
        
        layout_busca.addStretch()
        layout_principal.addWidget(grupo_busca)

        # 4. Tabela
        self.tabela_itens = QTableWidget()
        self.tabela_itens.setColumnCount(6)
        self.tabela_itens.setHorizontalHeaderLabels(["ID", "Produto", "Qtd", "Custo Un.", "Subtotal", "Ações"])
        self.tabela_itens.setStyleSheet("QTableWidget { border: 1px solid #ddd; background-color: white; } QHeaderView::section { background-color: #f8f9fa; padding: 6px; font-weight: bold; }")
        self.tabela_itens.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabela_itens.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela_itens.setAlternatingRowColors(True)
        layout_principal.addWidget(self.tabela_itens)

        # 5. Rodapé
        frame_rodape = QFrame()
        layout_rodape = QHBoxLayout(frame_rodape)

        btn_limpar = QPushButton("🗑️ Limpar")
        btn_limpar.setStyleSheet("background-color: #6c757d; color: white; padding: 10px; border-radius: 5px;")
        btn_limpar.clicked.connect(self.limpar_compra)
        layout_rodape.addWidget(btn_limpar)

        layout_rodape.addStretch()

        self.lbl_total_valor = QLabel("Total: R$ 0,00")
        self.lbl_total_valor.setStyleSheet("font-size: 20px; font-weight: bold; color: #dc3545; margin-right: 20px;")
        layout_rodape.addWidget(self.lbl_total_valor)

        self.btn_finalizar = QPushButton("✓ Finalizar Compra")
        self.btn_finalizar.setStyleSheet("QPushButton { background-color: #007bff; color: white; font-weight: bold; border-radius: 4px; padding: 10px 25px; } QPushButton:hover { background-color: #0069d9; }")
        self.btn_finalizar.clicked.connect(self.finalizar_compra)
        layout_rodape.addWidget(self.btn_finalizar)

        layout_principal.addWidget(frame_rodape)

    # --- LÓGICA DE DADOS ---

    def carregar_fornecedores(self):
        """Carrega FORNECEDORES da tabela ENTIDADE"""
        try:
            # Busca Entidades que tenham 'FORNECEDOR' no tipo
            query = select(Entidade).where(
                or_(
                    Entidade.tipo_entidade.ilike('%FORNECEDOR%'),
                    Entidade.tipo_entidade.ilike('%AMBOS%')
                )
            )
            fornecedores = self.sessao.execute(query).scalars().all()
            
            self.combo_fornecedor.clear()
            self.combo_fornecedor.addItem("Selecione o Fornecedor", None)
            
            for f in fornecedores:
                nome = f.nome_fantasia if f.nome_fantasia else f.razao_social
                self.combo_fornecedor.addItem(nome, f.id)
                
        except Exception as e:
            print(f"Erro ao carregar fornecedores: {e}")

    def carregar_produtos(self):
        try:
            produtos = self.sessao.execute(select(Item).where(Item.ativo == True)).scalars().all()
            self.combo_produtos.clear()
            self.combo_produtos.addItem("Selecione um produto", None)
            for p in produtos:
                self.combo_produtos.addItem(f"{p.id} - {p.nome}", p.id)
        except Exception as e:
            print(f"Erro ao carregar produtos: {e}")

    def adicionar_item(self):
        produto_id = self.combo_produtos.currentData()
        qtd = self.input_qtd.value()
        preco = self.input_preco.value()

        if not produto_id:
            QMessageBox.warning(self, "Aviso", "Selecione um produto.")
            return

        nome_produto = self.combo_produtos.currentText().split(" - ", 1)[-1]
        subtotal = qtd * preco
        
        item_compra = {
            'id': produto_id,
            'nome': nome_produto,
            'quantidade': qtd,
            'preco_unitario': preco,
            'subtotal': subtotal
        }
        self.itens_compra.append(item_compra)
        self.atualizar_tabela_itens()
        self.calcular_total()

        self.combo_produtos.setCurrentIndex(0)
        self.input_qtd.setValue(1)
        self.input_preco.setValue(0.0)

    def remover_item(self, row):
        if 0 <= row < len(self.itens_compra):
            self.itens_compra.pop(row)
            self.atualizar_tabela_itens()
            self.calcular_total()

    def atualizar_tabela_itens(self):
        self.tabela_itens.setRowCount(len(self.itens_compra))
        for row, item in enumerate(self.itens_compra):
            self.tabela_itens.setItem(row, 0, QTableWidgetItem(str(item['id'])))
            self.tabela_itens.setItem(row, 1, QTableWidgetItem(item['nome']))
            self.tabela_itens.setItem(row, 2, QTableWidgetItem(str(item['quantidade'])))
            self.tabela_itens.setItem(row, 3, QTableWidgetItem(f"R$ {item['preco_unitario']:.2f}"))
            self.tabela_itens.setItem(row, 4, QTableWidgetItem(f"R$ {item['subtotal']:.2f}"))
            
            btn_remover = QPushButton("❌")
            btn_remover.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; border-radius: 4px;")
            btn_remover.clicked.connect(lambda checked, r=row: self.remover_item(r))
            self.tabela_itens.setCellWidget(row, 5, btn_remover)

    def calcular_total(self):
        self.total_compra_float = sum(item['subtotal'] for item in self.itens_compra)
        self.lbl_total_valor.setText(f"Total: R$ {self.total_compra_float:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))

    def limpar_compra(self):
        self.itens_compra = []
        self.total_compra_float = 0.0
        self.atualizar_tabela_itens()
        self.calcular_total()
        self.input_nf.clear()
        self.combo_fornecedor.setCurrentIndex(0)

    def finalizar_compra(self):
        if not self.itens_compra:
            QMessageBox.warning(self, "Aviso", "Adicione itens à compra.")
            return

        fornecedor_id = self.combo_fornecedor.currentData()
        if not fornecedor_id:
            QMessageBox.warning(self, "Aviso", "Selecione um fornecedor.")
            return

        data_hj = self.input_data.date().toPyDate()

        try:
            # 1. PEDIDO DE COMPRA
            pedido = PedidoCompra(
                preco_total=self.total_compra_float,
                data_emissao=data_hj
            )
            self.sessao.add(pedido)
            self.sessao.flush()

            # 2. ITENS E ESTOQUE
            for item in self.itens_compra:
                item_pedido = PedidoCompraItem(
                    pedido_id=pedido.id,
                    quantidade=item['quantidade'],
                    preco_unitario=item['preco_unitario'],
                    preco_total=item['subtotal']
                )
                self.sessao.add(item_pedido)

                produto_db = self.sessao.get(Item, item['id'])
                if produto_db:
                    estoque_antigo = float(produto_db.estoque or 0)
                    produto_db.estoque = estoque_antigo + item['quantidade']
                    produto_db.custo_unitario = item['preco_unitario']

                    # AGORA USAMOS A TABELA ENTIDADE COMO FORNECEDOR
                    mov = MovimentoEstoque(
                        item_id=produto_db.id,
                        quantidade=item['quantidade'],
                        tipo_movimento='entrada',
                        data_ultima_mov=datetime.now(), 
                        observacao=f"Compra NF {self.input_nf.text()}",
                        estoque_minimo=0, 
                        estoque_maximo=0,
                        preco_venda=produto_db.preco_venda or 0,
                        preco_compra=item['preco_unitario'],
                        fornecedor_id=fornecedor_id # ID da Entidade, agora compatível
                    )
                    self.sessao.add(mov)

            # 3. FINANCEIRO (Conta a Pagar)
            conta_pagar = Financeiro(
                descricao=f"Compra NF {self.input_nf.text()} - Pedido #{pedido.id}",
                tipo_lancamento='P', 
                origem='C', 
                valor_nota=self.total_compra_float,
                data_emissao=data_hj,
                vencimento=data_hj, 
                status=EnumStatus.ABERTA,
                pedido_compra_id=pedido.id,
                fornecedor_id=fornecedor_id # ID da Entidade, compatível com a tabela Financeiro
            )
            self.sessao.add(conta_pagar)

            self.sessao.commit()
            
            QMessageBox.information(self, "Sucesso", f"Compra #{pedido.id} registrada com sucesso!")
            self.limpar_compra()

        except Exception as e:
            self.sessao.rollback()
            print(f"Erro detalhado: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao finalizar compra: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        self.carregar_fornecedores()
        self.carregar_produtos()