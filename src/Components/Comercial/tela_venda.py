# src/Components/Comercial/tela_venda.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QComboBox, QMessageBox, 
    QAbstractItemView, QDoubleSpinBox, QGroupBox, QDateEdit, QSpinBox, QFormLayout
)
from PyQt6.QtCore import Qt, QDate
from sqlalchemy import select
from datetime import date, datetime

# Modelos do Banco de Dados
from src.Models.models import (
    Item, PedidoVenda, PedidoVendaItem, Entidade, 
    MovimentoEstoque, Financeiro, EnumStatus
)

class TelaVenda(QWidget):
    def __init__(self, sessao=None, sistema=None, parent=None):
        super().__init__(parent)
        self.sessao = sessao
        self.sistema = sistema
        
        # Lista para guardar os itens antes de salvar
        self.itens_venda = [] 
        
        self.setup_ui()
        self.carregar_dados_iniciais()

    def setup_ui(self):
        """Configura a interface visualmente idêntica à de Compra"""
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(15)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        
        # 1. TÍTULO
        lbl_titulo = QLabel("Comercial - Saída / Venda")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #444;")
        layout_principal.addWidget(lbl_titulo)

        # 2. GRUPO: DADOS DA VENDA (Cliente e Data)
        grupo_dados = QGroupBox("Dados da Venda")
        grupo_dados.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #ccc; padding: 10px; margin-top: 10px; }")
        layout_dados = QHBoxLayout(grupo_dados)
        
        # Cliente
        layout_dados.addWidget(QLabel("Cliente:"))
        self.combo_cliente = QComboBox()
        self.combo_cliente.setPlaceholderText("Selecione o Cliente")
        self.combo_cliente.setMinimumWidth(300)
        self.combo_cliente.setStyleSheet("QComboBox { background-color: white; border: 1px solid #ccc; padding: 5px; }")
        layout_dados.addWidget(self.combo_cliente)
        
        # Data
        layout_dados.addWidget(QLabel("Data:"))
        self.data_emissao = QDateEdit()
        self.data_emissao.setCalendarPopup(True)
        self.data_emissao.setDate(QDate.currentDate())
        self.data_emissao.setFixedWidth(120)
        layout_dados.addWidget(self.data_emissao)
        
        layout_dados.addStretch() # Empurra para esquerda
        layout_principal.addWidget(grupo_dados)

        # 3. GRUPO: ADICIONAR PRODUTOS (Visual Ajustado)
        grupo_itens = QGroupBox("Adicionar Produtos")
        grupo_itens.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #ccc; padding: 10px; margin-top: 10px; }")
        layout_itens = QHBoxLayout(grupo_itens)

        # Produto (Label + Combobox juntos)
        layout_itens.addWidget(QLabel("Produto:"))
        self.combo_produto = QComboBox()
        self.combo_produto.setPlaceholderText("Selecione o Produto")
        self.combo_produto.setMinimumWidth(250)
        self.combo_produto.setStyleSheet("QComboBox { background-color: white; border: 1px solid #ccc; padding: 5px; }")
        self.combo_produto.currentIndexChanged.connect(self.atualizar_preco_produto)
        layout_itens.addWidget(self.combo_produto)

        # Quantidade
        layout_itens.addWidget(QLabel("Qtd:"))
        self.spin_qtd = QDoubleSpinBox()
        self.spin_qtd.setRange(0.01, 9999)
        self.spin_qtd.setValue(1.0)
        self.spin_qtd.setDecimals(0)
        self.spin_qtd.setFixedWidth(80)
        layout_itens.addWidget(self.spin_qtd)

        # Preço
        layout_itens.addWidget(QLabel("Preço Venda:"))
        self.spin_preco = QDoubleSpinBox()
        self.spin_preco.setRange(0.0, 999999)
        self.spin_preco.setPrefix("R$ ")
        self.spin_preco.setFixedWidth(100)
        layout_itens.addWidget(self.spin_preco)

        # Botão Adicionar
        self.btn_add = QPushButton(" + Adicionar")
        self.btn_add.setStyleSheet("""
            QPushButton { background-color: #28a745; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }
            QPushButton:hover { background-color: #218838; }
        """)
        self.btn_add.clicked.connect(self.adicionar_item)
        layout_itens.addWidget(self.btn_add)
        
        layout_itens.addStretch() # Mantém tudo compacto à esquerda
        layout_principal.addWidget(grupo_itens)

        # 4. TABELA DE ITENS
        self.table_itens = QTableWidget()
        self.table_itens.setColumnCount(6)
        self.table_itens.setHorizontalHeaderLabels(["ID", "Produto", "Qtd", "Preço Unit.", "Subtotal", "Ações"])
        self.table_itens.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Coluna Produto estica
        self.table_itens.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_itens.setAlternatingRowColors(True)
        self.table_itens.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #ddd; }
            QHeaderView::section { background-color: #f8f9fa; padding: 6px; border: 1px solid #ddd; font-weight: bold; }
        """)
        
        layout_principal.addWidget(self.table_itens)

        # 5. RODAPÉ
        frame_rodape = QFrame()
        layout_rodape = QHBoxLayout(frame_rodape)
        
        # Pagamento
        self.combo_pagamento = QComboBox()
        self.combo_pagamento.addItems(["Dinheiro", "Pix", "Cartão Crédito", "Cartão Débito", "Boleto", "Prazo"])
        self.combo_pagamento.setFixedWidth(150)
        self.combo_pagamento.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 5px;")
        
        layout_rodape.addWidget(QLabel("Pagamento:"))
        layout_rodape.addWidget(self.combo_pagamento)

        layout_rodape.addStretch()

        # Total
        self.lbl_total = QLabel("Total: R$ 0,00")
        self.lbl_total.setStyleSheet("font-size: 22px; font-weight: bold; color: #007bff; margin-right: 20px;")
        layout_rodape.addWidget(self.lbl_total)

        # Botão Finalizar
        btn_finalizar = QPushButton("✓ FINALIZAR VENDA")
        btn_finalizar.setMinimumHeight(45)
        btn_finalizar.setMinimumWidth(180)
        btn_finalizar.setStyleSheet("""
            QPushButton { background-color: #007bff; color: white; font-size: 14px; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #0056b3; }
        """)
        btn_finalizar.clicked.connect(self.finalizar_venda)
        layout_rodape.addWidget(btn_finalizar)

        layout_principal.addWidget(frame_rodape)

    # --- LÓGICA (MANTIDA IGUAL À VERSÃO CORRIGIDA) ---

    def carregar_dados_iniciais(self):
        try:
            # Carregar Clientes
            clientes = self.sessao.execute(select(Entidade)).scalars().all()
            self.combo_cliente.clear()
            self.combo_cliente.addItem("Selecione o Cliente", None)
            for c in clientes:
                nome = c.nome_fantasia if c.nome_fantasia else c.razao_social
                self.combo_cliente.addItem(nome, c.id)

            # Carregar Produtos
            produtos = self.sessao.execute(select(Item).where(Item.tipo_item == 'PRODUTO')).scalars().all()
            self.combo_produto.clear()
            self.combo_produto.addItem("Selecione o Produto", None)
            for p in produtos:
                self.combo_produto.addItem(p.nome, p.id) 

        except Exception as e:
            print(f"Erro ao carregar dados: {e}")

    def atualizar_preco_produto(self):
        produto_id = self.combo_produto.currentData()
        if not produto_id:
            return
        try:
            produto = self.sessao.get(Item, produto_id)
            if produto:
                preco = float(produto.preco_venda or 0.0)
                self.spin_preco.setValue(preco)
        except Exception as e:
            print(f"Erro ao buscar preço: {e}")

    def adicionar_item(self):
        produto_id = self.combo_produto.currentData()
        if not produto_id:
            QMessageBox.warning(self, "Aviso", "Selecione um produto.")
            return

        nome_produto = self.combo_produto.currentText()
        qtd = self.spin_qtd.value()
        preco = self.spin_preco.value()
        subtotal = qtd * preco

        if qtd <= 0:
            QMessageBox.warning(self, "Aviso", "Qtd deve ser maior que 0.")
            return

        self.itens_venda.append({
            "id": produto_id,
            "nome": nome_produto,
            "quantidade": int(qtd),
            "preco_unitario": preco,
            "subtotal": subtotal
        })

        self.atualizar_tabela()
        
        # Resetar campos para facilitar próxima adição
        self.combo_produto.setCurrentIndex(0)
        self.spin_qtd.setValue(1)
        self.spin_preco.setValue(0.0)

    def remover_item_selecionado(self, row):
        if row >= 0:
            self.itens_venda.pop(row)
            self.atualizar_tabela()

    def atualizar_tabela(self):
        self.table_itens.setRowCount(len(self.itens_venda))
        total_geral = 0.0
        
        for i, item in enumerate(self.itens_venda):
            self.table_itens.setItem(i, 0, QTableWidgetItem(str(item['id'])))
            self.table_itens.setItem(i, 1, QTableWidgetItem(item['nome']))
            self.table_itens.setItem(i, 2, QTableWidgetItem(str(item['quantidade'])))
            self.table_itens.setItem(i, 3, QTableWidgetItem(f"R$ {item['preco_unitario']:.2f}"))
            self.table_itens.setItem(i, 4, QTableWidgetItem(f"R$ {item['subtotal']:.2f}"))
            
            # Botão remover igual ao da compra
            btn_remover = QPushButton("❌")
            btn_remover.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; border-radius: 4px;")
            btn_remover.clicked.connect(lambda checked, r=i: self.remover_item_selecionado(r))
            self.table_itens.setCellWidget(i, 5, btn_remover)
            
            total_geral += item['subtotal']
            
        self.lbl_total.setText(f"Total: R$ {total_geral:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))

    def finalizar_venda(self):
        if not self.itens_venda:
            QMessageBox.warning(self, "Aviso", "Adicione produtos antes de finalizar.")
            return

        cliente_id = self.combo_cliente.currentData()
        if not cliente_id:
            QMessageBox.warning(self, "Aviso", "Selecione um cliente.")
            return

        total_final = sum(i['subtotal'] for i in self.itens_venda)
        data_hj = self.data_emissao.date().toPyDate()

        try:
            # 1. PEDIDO DE VENDA
            pedido = PedidoVenda(
                cliente_id=cliente_id,
                preco_total=total_final,  
                data_emissao=data_hj,
                status="FINALIZADO"
            )
            
            if self.sistema and hasattr(self.sistema, 'usuario_atual') and self.sistema.usuario_atual:
                pedido.vendedor_id = self.sistema.usuario_atual.id

            self.sessao.add(pedido)
            self.sessao.flush() 

            # 2. ITENS E ESTOQUE
            for item in self.itens_venda:
                # Item do Pedido
                novo_item = PedidoVendaItem(
                    pedido_id=pedido.id,
                    produto=item['nome'], 
                    quantidade=item['quantidade'],
                    preco_unitario=item['preco_unitario'],
                    preco_total=item['subtotal']
                )
                self.sessao.add(novo_item)

                # Atualizar Estoque
                produto_db = self.sessao.get(Item, item['id'])
                if produto_db:
                    estoque_atual = float(produto_db.estoque or 0)
                    produto_db.estoque = estoque_atual - item['quantidade']
                    
                    # Movimentação (Preenchendo campos obrigatórios do seu model)
                    forn_id = produto_db.fornecedor_id if produto_db.fornecedor_id else 1 
                    
                    mov = MovimentoEstoque(
                        item_id=produto_db.id,
                        quantidade=item['quantidade'],
                        tipo_movimento='saida',
                        data_ultima_mov=datetime.now(), # Corrigido: data_ultima_mov
                        observacao=f"Venda PDV #{pedido.id}",
                        estoque_minimo=0, 
                        estoque_maximo=0, 
                        preco_venda=item['preco_unitario'], 
                        preco_compra=produto_db.custo_unitario or 0, 
                        fornecedor_id=forn_id 
                    )
                    self.sessao.add(mov)

            # 3. FINANCEIRO
            is_pago = self.combo_pagamento.currentText() in ["Dinheiro", "Pix", "Cartão Débito"]
            status_fin = EnumStatus.PAGA if is_pago else EnumStatus.ABERTA

            conta = Financeiro(
                descricao=f"Venda #{pedido.id}",
                tipo_lancamento='R', 
                origem='V',          # Corrigido: Origem Venda
                valor_nota=total_final,
                data_emissao=data_hj,
                vencimento=data_hj,
                status=status_fin,
                pedido_venda_id=pedido.id,
                cliente_id=cliente_id
            )
            self.sessao.add(conta)

            self.sessao.commit()
            
            QMessageBox.information(self, "Sucesso", f"Venda #{pedido.id} realizada!")
            self.limpar_tela()

        except Exception as e:
            self.sessao.rollback()
            QMessageBox.critical(self, "Erro", f"Erro no banco de dados: {e}")
            print(f"Erro detalhado: {e}")

    def limpar_tela(self):
        self.itens_venda = []
        self.table_itens.setRowCount(0)
        self.spin_qtd.setValue(1)
        self.atualizar_tabela()
        self.lbl_total.setText("Total: R$ 0,00")
        self.combo_cliente.setCurrentIndex(0)
        self.combo_produto.setCurrentIndex(0)