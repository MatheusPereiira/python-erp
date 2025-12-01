from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QSpinBox, 
    QPushButton, QMessageBox, QLabel, QFrame, QRadioButton, 
    QButtonGroup, QHBoxLayout, QDoubleSpinBox
)
from sqlalchemy import select, or_
from datetime import datetime
# CORREÇÃO: Usamos Entidade em vez de Fornecedor
from src.Models.models import Item, MovimentoEstoque, Entidade

class CadastroEstoqueWidget(QWidget):
    def __init__(self, sessao):
        super().__init__()
        self.sessao = sessao
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_titulo = QLabel("Movimentação Manual de Estoque")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_titulo)

        # Frame do Formulário
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        form_layout = QFormLayout(form_frame)
        form_layout.setContentsMargins(20, 20, 20, 20)

        # Tipo de Movimento
        self.radio_entrada = QRadioButton("Entrada")
        self.radio_saida = QRadioButton("Saída")
        self.radio_entrada.setChecked(True)
        
        self.group_tipo = QButtonGroup()
        self.group_tipo.addButton(self.radio_entrada)
        self.group_tipo.addButton(self.radio_saida)
        
        layout_radios = QHBoxLayout()
        layout_radios.addWidget(self.radio_entrada)
        layout_radios.addWidget(self.radio_saida)
        form_layout.addRow("Tipo:", layout_radios)

        # Campos
        self.combo_produto = QComboBox()
        self.spin_qtd = QSpinBox()
        self.spin_qtd.setRange(1, 99999)
        
        self.combo_fornecedor = QComboBox() # Será usado apenas na Entrada
        
        # Preços (Opcionais na movimentação manual, mas bons para histórico)
        self.spin_preco = QDoubleSpinBox()
        self.spin_preco.setRange(0, 999999)
        self.spin_preco.setPrefix("R$ ")

        form_layout.addRow("Produto:", self.combo_produto)
        form_layout.addRow("Quantidade:", self.spin_qtd)
        form_layout.addRow("Custo/Preço:", self.spin_preco)
        form_layout.addRow("Fornecedor (Opcional):", self.combo_fornecedor)

        layout.addWidget(form_frame)

        # Botão Salvar
        self.btn_salvar = QPushButton("Registrar Movimentação")
        self.btn_salvar.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 10px;")
        self.btn_salvar.clicked.connect(self.salvar_movimento)
        layout.addWidget(self.btn_salvar)
        
        layout.addStretch()

    def load_data(self):
        try:
            # 1. Carregar Produtos
            produtos = self.sessao.execute(select(Item).where(Item.ativo == True)).scalars().all()
            self.combo_produto.clear()
            for p in produtos:
                self.combo_produto.addItem(f"{p.codigo_item} - {p.nome}", p.id)

            # 2. Carregar Fornecedores (Da tabela Entidade)
            fornecedores = self.sessao.execute(
                select(Entidade).where(
                    or_(
                        Entidade.tipo_entidade.ilike('%FORNECEDOR%'),
                        Entidade.tipo_entidade.ilike('%AMBOS%')
                    )
                )
            ).scalars().all()
            
            self.combo_fornecedor.clear()
            self.combo_fornecedor.addItem("Sem Fornecedor", None)
            for f in fornecedores:
                nome = f.nome_fantasia or f.razao_social
                self.combo_fornecedor.addItem(nome, f.id)

        except Exception as e:
            print(f"Erro ao carregar dados estoque: {e}")

    def salvar_movimento(self):
        produto_id = self.combo_produto.currentData()
        qtd = self.spin_qtd.value()
        preco = self.spin_preco.value()
        forn_id = self.combo_fornecedor.currentData()
        
        if not produto_id:
            QMessageBox.warning(self, "Aviso", "Selecione um produto.")
            return

        tipo = "entrada" if self.radio_entrada.isChecked() else "saida"

        try:
            # Busca produto para atualizar estoque atual
            produto = self.sessao.get(Item, produto_id)
            estoque_antigo = float(produto.estoque or 0)
            
            if tipo == "entrada":
                produto.estoque = estoque_antigo + qtd
                # Atualiza custo se for entrada
                if preco > 0: produto.custo_unitario = preco
            else:
                produto.estoque = estoque_antigo - qtd

            # Cria registro de histórico
            # Se não selecionou fornecedor, tenta usar o padrão do produto ou None (se o banco permitir, senão 1)
            if not forn_id and produto.fornecedor_id:
                forn_id = produto.fornecedor_id
            
            # Se ainda for nulo e o banco obrigar, cuidado. Vamos assumir que pode ser nulo ou pegamos o primeiro.
            
            mov = MovimentoEstoque(
                item_id=produto.id,
                quantidade=qtd,
                tipo_movimento=tipo,
                data_ultima_mov=datetime.now(),
                observacao="Movimentação Manual",
                estoque_minimo=0,
                estoque_maximo=0,
                preco_venda=produto.preco_venda or 0,
                preco_compra=preco if tipo == 'entrada' else (produto.custo_unitario or 0),
                fornecedor_id=forn_id # Pode ser None se o banco aceitar, ou precisa tratar no models
            )
            
            self.sessao.add(mov)
            self.sessao.commit()
            
            QMessageBox.information(self, "Sucesso", f"Estoque atualizado!\nNovo saldo: {produto.estoque}")
            self.spin_qtd.setValue(1)
            
        except Exception as e:
            self.sessao.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")