from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QColorDialog, QMessageBox,
    QDialog, QFormLayout, QDoubleSpinBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

# Importa os modelos do banco
from sqlalchemy import select
from src.Models.models import TabelaPreco, Item

class EditarPrecoDialog(QDialog):
    def __init__(self, produto_nome, preco_atual, parent=None):
        super().__init__(parent)
        self.produto_nome = produto_nome
        self.preco_atual = preco_atual
        self.novo_preco = preco_atual
        
        self.setWindowTitle(f"Editar Preço - {produto_nome}")
        self.setFixedSize(400, 200)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Formulário
        form_layout = QFormLayout()
        
        lbl_produto = QLabel(self.produto_nome)
        lbl_produto.setStyleSheet("font-weight: bold; font-size: 14px;")
        form_layout.addRow("Produto:", lbl_produto)
        
        lbl_preco_atual = QLabel(f"R$ {self.preco_atual:.2f}")
        lbl_preco_atual.setStyleSheet("color: #666;")
        form_layout.addRow("Preço Atual:", lbl_preco_atual)
        
        self.input_novo_preco = QDoubleSpinBox()
        self.input_novo_preco.setRange(0.01, 999999.99)
        self.input_novo_preco.setValue(self.preco_atual)
        self.input_novo_preco.setPrefix("R$ ")
        self.input_novo_preco.setDecimals(2)
        self.input_novo_preco.setStyleSheet("padding: 8px; font-size: 14px;")
        self.input_novo_preco.valueChanged.connect(self.preco_alterado)
        form_layout.addRow("Novo Preço:", self.input_novo_preco)
        
        layout.addLayout(form_layout)
        
        # Botões
        btn_layout = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_layout.accepted.connect(self.accept)
        btn_layout.rejected.connect(self.reject)
        
        layout.addWidget(btn_layout)
    
    def preco_alterado(self, valor):
        self.novo_preco = valor
    
    def get_novo_preco(self):
        return self.novo_preco

class NovoItemDialog(QDialog):
    def __init__(self, sessao, parent=None):
        super().__init__(parent)
        self.sessao = sessao
        self.setWindowTitle("Novo Item na Tabela de Preços")
        self.setFixedSize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        lbl_titulo = QLabel("Adicionar Novo Produto")
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(lbl_titulo)
        
        # Formulário
        form_layout = QFormLayout()
        
        # Seleção de produto existente
        self.combo_produtos = QComboBox()
        self.carregar_produtos()
        form_layout.addRow("Produto Existente:", self.combo_produtos)
        
        # OU novo produto
        self.input_novo_produto = QLineEdit()
        self.input_novo_produto.setPlaceholderText("Digite o nome do novo produto...")
        form_layout.addRow("OU Novo Produto:", self.input_novo_produto)
        
        # Preço
        self.input_preco = QDoubleSpinBox()
        self.input_preco.setRange(0.01, 999999.99)
        self.input_preco.setValue(0.01)
        self.input_preco.setPrefix("R$ ")
        self.input_preco.setDecimals(2)
        form_layout.addRow("Preço de Venda:", self.input_preco)
        
        # Estoque
        self.input_estoque = QDoubleSpinBox()
        self.input_estoque.setRange(0, 999999)
        self.input_estoque.setValue(0)
        form_layout.addRow("Estoque Inicial:", self.input_estoque)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Botões
        btn_layout = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_layout.accepted.connect(self.validar_e_aceitar)
        btn_layout.rejected.connect(self.reject)
        
        layout.addWidget(btn_layout)
    
    def carregar_produtos(self):
        try:
            produtos = self.sessao.execute(
                select(Item).where(Item.tipo_item == 'PRODUTO')
            ).scalars().all()
            
            self.combo_produtos.clear()
            self.combo_produtos.addItem("Selecione um produto...", None)
            
            for produto in produtos:
                self.combo_produtos.addItem(f"{produto.nome} ({produto.codigo_item})", produto.id)
                
        except Exception as e:
            print(f"Erro ao carregar produtos: {e}")
    
    def validar_e_aceitar(self):
        produto_existente = self.combo_produtos.currentData()
        novo_produto = self.input_novo_produto.text().strip()
        preco = self.input_preco.value()
        
        if not produto_existente and not novo_produto:
            QMessageBox.warning(self, "Validação", "Selecione um produto existente OU digite um novo produto!")
            return
        
        if preco <= 0:
            QMessageBox.warning(self, "Validação", "O preço deve ser maior que zero!")
            return
        
        self.accept()
    
    def get_dados(self):
        return {
            'produto_existente_id': self.combo_produtos.currentData(),
            'novo_produto_nome': self.input_novo_produto.text().strip(),
            'preco': self.input_preco.value(),
            'estoque': self.input_estoque.value()
        }

class TabelaPrecoWidget(QWidget):
    def __init__(self, sessao=None):
        super().__init__()
        self.sessao = sessao
        
        self.setup_ui()
        self.sincronizar_e_carregar()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(15)
        layout_principal.setContentsMargins(20, 20, 20, 20)

        # Título
        lbl_titulo = QLabel("Tabela de Preços (Custo x Venda)")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: #333;")
        layout_principal.addWidget(lbl_titulo)

        # Barra de Busca
        layout_busca = QHBoxLayout()
        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("🔍 Buscar por nome do produto...")
        self.input_busca.setStyleSheet("""
            QLineEdit {
                padding: 8px; 
                border: 1px solid #ccc; 
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #007bff;
            }
        """)
        self.input_busca.textChanged.connect(self.filtrar_tabela)
        layout_busca.addWidget(self.input_busca)

        layout_principal.addLayout(layout_busca)

        # Barra de Botões - AGORA FUNCIONA PORRA! 🚀
        layout_acoes = QHBoxLayout()
        layout_acoes.setSpacing(10)

        # BOTÃO NOVO ITEM - FUNCIONAL
        self.btn_adicionar = QPushButton("➕ NOVO ITEM")
        self.btn_adicionar.setStyleSheet("""
            QPushButton {
                background-color: #28a745; 
                color: white; 
                font-weight: bold; 
                border-radius: 4px; 
                padding: 10px 20px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { 
                background-color: #218838; 
            }
        """)
        self.btn_adicionar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_adicionar.clicked.connect(self.adicionar_item)

        # BOTÃO EDITAR PREÇO - FUNCIONAL  
        self.btn_editar = QPushButton("✏️ EDITAR PREÇO")
        self.btn_editar.setStyleSheet("""
            QPushButton {
                background-color: #007bff; 
                color: white; 
                font-weight: bold; 
                border-radius: 4px; 
                padding: 10px 20px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { 
                background-color: #0069d9; 
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_editar.clicked.connect(self.editar_preco)

        # BOTÃO EXCLUIR - FUNCIONAL
        self.btn_excluir = QPushButton("🗑️ EXCLUIR")
        self.btn_excluir.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; 
                color: white; 
                font-weight: bold; 
                border-radius: 4px; 
                padding: 10px 20px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { 
                background-color: #c82333; 
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.btn_excluir.clicked.connect(self.excluir_item)
        
        # BOTÃO ATUALIZAR - FUNCIONAL
        self.btn_atualizar = QPushButton("🔄 ATUALIZAR")
        self.btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d; 
                color: white; 
                font-weight: bold; 
                border-radius: 4px; 
                padding: 10px 20px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover { 
                background-color: #5a6268; 
            }
        """)
        self.btn_atualizar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_atualizar.clicked.connect(self.sincronizar_e_carregar)

        layout_acoes.addWidget(self.btn_adicionar)
        layout_acoes.addWidget(self.btn_editar)
        layout_acoes.addWidget(self.btn_excluir)
        layout_acoes.addWidget(self.btn_atualizar)
        layout_acoes.addStretch()

        layout_principal.addLayout(layout_acoes)

        # Tabela
        self.tabela = QTableWidget()
        colunas = ["ID", "Produto", "Estoque", "Preço Compra (Custo)", "Preço Venda", "Margem (%)", "Vencimento"]
        self.tabela.setColumnCount(len(colunas))
        self.tabela.setHorizontalHeaderLabels(colunas)
        
        self.tabela.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                background-color: white;
                selection-background-color: #e6f0ff;
                selection-color: black;
                gridline-color: #f0f0f0;
                font-size: 13px;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
                color: #555;
            }
        """)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabela.setAlternatingRowColors(True)
        
        self.tabela.itemSelectionChanged.connect(self.atualizar_botoes)

        layout_principal.addWidget(self.tabela)

        # Rodapé
        layout_rodape = QHBoxLayout()
        self.lbl_status = QLabel("Mostrando 0 registros")
        self.lbl_status.setStyleSheet("color: #666; font-size: 12px;")
        layout_rodape.addWidget(self.lbl_status)
        layout_rodape.addStretch()
        
        layout_principal.addLayout(layout_rodape)
        
        self.atualizar_botoes()

    def atualizar_botoes(self):
        tem_selecao = self.tabela.currentRow() >= 0
        self.btn_editar.setEnabled(tem_selecao)
        self.btn_excluir.setEnabled(tem_selecao)

    # 🔥 AGORA FUNCIONA PORRA! - NOVO ITEM
    def adicionar_item(self):
        """Adiciona novo item à tabela de preços - AGORA FUNCIONAL!"""
        dialog = NovoItemDialog(self.sessao, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dados = dialog.get_dados()
            
            try:
                # Verifica se é produto existente ou novo
                if dados['produto_existente_id']:
                    # Produto existente - busca no banco
                    produto = self.sessao.get(Item, dados['produto_existente_id'])
                    if produto:
                        # Atualiza preço do produto existente
                        produto.preco_venda = dados['preco']
                        # Cria entrada na tabela de preços se não existir
                        existe_tabela = self.sessao.execute(
                            select(TabelaPreco).where(TabelaPreco.produto == produto.nome)
                        ).scalar_one_or_none()
                        
                        if not existe_tabela:
                            novo_item = TabelaPreco(
                                produto=produto.nome,
                                estoque=produto.estoque or 0,
                                preco_unitario=dados['preco'],
                                vencimento=None
                            )
                            self.sessao.add(novo_item)
                        
                        self.sessao.commit()
                        QMessageBox.information(self, "Sucesso", f"Preço de {produto.nome} atualizado para R$ {dados['preco']:.2f}!")
                
                elif dados['novo_produto_nome']:
                    # Novo produto - cria em ambas as tabelas
                    novo_produto = Item(
                        nome=dados['novo_produto_nome'],
                        codigo_item=f"COD_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        tipo_item='PRODUTO',
                        preco_venda=dados['preco'],
                        custo_unitario=0,
                        estoque=dados['estoque'],
                        ativo=True
                    )
                    self.sessao.add(novo_produto)
                    
                    novo_tabela_preco = TabelaPreco(
                        produto=dados['novo_produto_nome'],
                        estoque=dados['estoque'],
                        preco_unitario=dados['preco'],
                        vencimento=None
                    )
                    self.sessao.add(novo_tabela_preco)
                    
                    self.sessao.commit()
                    QMessageBox.information(self, "Sucesso", f"Novo produto '{dados['novo_produto_nome']}' criado com preço R$ {dados['preco']:.2f}!")
                
                self.sincronizar_e_carregar()
                
            except Exception as e:
                self.sessao.rollback()
                QMessageBox.critical(self, "Erro", f"Erro ao adicionar item: {str(e)}")

    # 🔥 AGORA FUNCIONA PORRA! - EDITAR PREÇO
    def editar_preco(self):
        """Edita o preço do item selecionado - AGORA FUNCIONAL!"""
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um item para editar!")
            return
        
        item_id = int(self.tabela.item(linha, 0).text())
        produto_nome = self.tabela.item(linha, 1).text()
        preco_atual_texto = self.tabela.item(linha, 4).text().replace('R$ ', '').replace(',', '')
        preco_atual = float(preco_atual_texto)
        
        # Abre dialog de edição
        dialog = EditarPrecoDialog(produto_nome, preco_atual, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            novo_preco = dialog.get_novo_preco()
            
            if novo_preco != preco_atual:
                try:
                    # Atualiza na tabela TabelaPreco
                    item_tabela = self.sessao.get(TabelaPreco, item_id)
                    if item_tabela:
                        item_tabela.preco_unitario = novo_preco
                    
                    # Atualiza também na tabela Item se existir
                    produto_item = self.sessao.execute(
                        select(Item).where(Item.nome == produto_nome)
                    ).scalar_one_or_none()
                    
                    if produto_item:
                        produto_item.preco_venda = novo_preco
                    
                    self.sessao.commit()
                    
                    QMessageBox.information(self, "Sucesso", 
                                          f"Preço de {produto_nome} atualizado!\n"
                                          f"De: R$ {preco_atual:.2f}\n"
                                          f"Para: R$ {novo_preco:.2f}")
                    
                    self.sincronizar_e_carregar()
                    
                except Exception as e:
                    self.sessao.rollback()
                    QMessageBox.critical(self, "Erro", f"Erro ao atualizar preço: {str(e)}")

    # 🔥 JÁ FUNCIONAVA - EXCLUIR ITEM
    def excluir_item(self):
        """Exclui o item selecionado"""
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um item para excluir!")
            return
        
        item_id = int(self.tabela.item(linha, 0).text())
        produto_nome = self.tabela.item(linha, 1).text()
        
        resposta = QMessageBox.question(
            self, 
            "Confirmar Exclusão", 
            f"Tem certeza que deseja excluir:\n{produto_nome}?\n\n"
            f"⚠️  Esta ação remove apenas da tabela de preços, não do cadastro de produtos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if resposta == QMessageBox.StandardButton.Yes:
            try:
                item = self.sessao.get(TabelaPreco, item_id)
                if item:
                    self.sessao.delete(item)
                    self.sessao.commit()
                    QMessageBox.information(self, "Sucesso", "Item excluído da tabela de preços!")
                    self.sincronizar_e_carregar()
                else:
                    QMessageBox.warning(self, "Erro", "Item não encontrado!")
            except Exception as e:
                self.sessao.rollback()
                QMessageBox.critical(self, "Erro", f"Erro ao excluir item: {str(e)}")

    # 🔥 JÁ FUNCIONAVA - SINCRONIZAR E CARREGAR
    def sincronizar_e_carregar(self):
        """Sincroniza e carrega os dados"""
        if not self.sessao: 
            QMessageBox.warning(self, "Erro", "Sessão do banco não disponível!")
            return

        try:
            # Sincronização básica
            produtos_cadastro = self.sessao.execute(
                select(Item).where(Item.tipo_item == 'PRODUTO')
            ).scalars().all()
            
            novos_itens = 0
            for prod in produtos_cadastro:
                existe = self.sessao.execute(
                    select(TabelaPreco).where(TabelaPreco.produto == prod.nome)
                ).scalar_one_or_none()
                
                if not existe:
                    novo_preco = TabelaPreco(
                        produto=prod.nome,
                        estoque=prod.estoque or 0,
                        preco_unitario=prod.preco_venda or 0, 
                        vencimento=None
                    )
                    self.sessao.add(novo_preco)
                    novos_itens += 1
            
            if novos_itens > 0:
                self.sessao.commit()

            # Carregamento
            self.tabela.setRowCount(0)
            
            query = (
                select(TabelaPreco, Item.custo_unitario)
                .outerjoin(Item, TabelaPreco.produto == Item.nome)
            )
            resultados = self.sessao.execute(query).all()

            for row_idx, (tabela_preco, custo_item) in enumerate(resultados):
                self.tabela.insertRow(row_idx)
                
                # Preenche a tabela (código existente)
                self.tabela.setItem(row_idx, 0, QTableWidgetItem(str(tabela_preco.id)))
                self.tabela.setItem(row_idx, 1, QTableWidgetItem(tabela_preco.produto))
                self.tabela.setItem(row_idx, 2, QTableWidgetItem(str(tabela_preco.estoque or 0)))
                
                custo = float(custo_item or 0.00)
                self.tabela.setItem(row_idx, 3, QTableWidgetItem(f"R$ {custo:.2f}"))
                
                venda = float(tabela_preco.preco_unitario or 0.00)
                self.tabela.setItem(row_idx, 4, QTableWidgetItem(f"R$ {venda:.2f}"))
                
                # Margem
                if custo > 0:
                    margem = ((venda - custo) / custo) * 100
                    margem_str = f"{margem:.1f}%"
                    item_margem = QTableWidgetItem(margem_str)
                    
                    if margem < 0: 
                        item_margem.setForeground(QColor("#dc3545"))
                    elif margem < 20:
                        item_margem.setForeground(QColor("#d39e00"))
                    else: 
                        item_margem.setForeground(QColor("#28a745"))
                    
                    self.tabela.setItem(row_idx, 5, item_margem)
                else:
                    self.tabela.setItem(row_idx, 5, QTableWidgetItem("N/A"))

                self.tabela.setItem(row_idx, 6, QTableWidgetItem(
                    tabela_preco.vencimento.strftime("%d/%m/%Y") if tabela_preco.vencimento else "-"
                ))

            self.lbl_status.setText(f"Mostrando {len(resultados)} produtos")
            self.atualizar_botoes()

        except Exception as e:
            print(f"Erro ao sincronizar/carregar: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar dados: {str(e)}")

    def filtrar_tabela(self, texto):
        texto = texto.lower()
        linhas_visiveis = 0
        
        for i in range(self.tabela.rowCount()):
            item = self.tabela.item(i, 1)
            if item and texto in item.text().lower():
                self.tabela.setRowHidden(i, False)
                linhas_visiveis += 1
            else:
                self.tabela.setRowHidden(i, True)
        
        self.lbl_status.setText(f"Mostrando {linhas_visiveis} de {self.tabela.rowCount()} produtos")

    def load_data(self):
        self.sincronizar_e_carregar()

# Adicione o import necessário no topo do arquivo
from datetime import datetime
from PyQt6.QtWidgets import QComboBox, QDialogButtonBox