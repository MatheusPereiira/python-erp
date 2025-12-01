# src/Views/dashboard_produto_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout)
from PyQt6.QtCore import Qt
from sqlalchemy import select, func, or_
# CORREÇÃO: Importamos Entidade em vez de Fornecedor
from src.Models.models import Item, Entidade

class DashboardProdutosWidget(QWidget):
    def __init__(self, sessao):
        super().__init__()
        self.sessao = sessao
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_titulo = QLabel("Dashboard de Produtos")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(lbl_titulo)

        # Cards de Resumo
        self.cards_layout = QHBoxLayout()
        self.card_total_produtos = self.criar_card("Total Produtos", "0", "#007bff")
        self.card_valor_estoque = self.criar_card("Valor em Estoque", "R$ 0,00", "#28a745")
        self.card_total_fornecedores = self.criar_card("Fornecedores", "0", "#17a2b8")
        
        self.cards_layout.addWidget(self.card_total_produtos)
        self.cards_layout.addWidget(self.card_valor_estoque)
        self.cards_layout.addWidget(self.card_total_fornecedores)
        
        layout.addLayout(self.cards_layout)
        layout.addStretch()

    def criar_card(self, titulo, valor, cor):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {cor};
                border-radius: 10px;
                color: white;
            }}
        """)
        frame.setFixedSize(200, 100)
        
        layout = QVBoxLayout(frame)
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-size: 14px; font-weight: bold;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_valor = QLabel(valor)
        lbl_valor.setStyleSheet("font-size: 20px; font-weight: 900;")
        lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        
        # Guardar referência para atualizar depois
        if titulo == "Total Produtos": self.lbl_total_prod = lbl_valor
        if titulo == "Valor em Estoque": self.lbl_valor_est = lbl_valor
        if titulo == "Fornecedores": self.lbl_total_forn = lbl_valor
        
        return frame

    def load_data(self):
        try:
            # 1. Total de Produtos Ativos
            total_prod = self.sessao.query(func.count(Item.id)).where(Item.ativo == True).scalar()
            self.lbl_total_prod.setText(str(total_prod))

            # 2. Valor Total do Estoque (Custo * Quantidade)
            # Calcula em Python para evitar problemas de tipos no SQL se estiver vazio
            produtos = self.sessao.execute(select(Item).where(Item.ativo == True)).scalars().all()
            valor_total = sum((p.estoque or 0) * (p.custo_unitario or 0) for p in produtos)
            self.lbl_valor_est.setText(f"R$ {valor_total:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))

            # 3. Total de Fornecedores (CORREÇÃO: Busca na tabela Entidade)
            total_forn = self.sessao.query(func.count(Entidade.id)).where(
                or_(
                    Entidade.tipo_entidade.ilike('%FORNECEDOR%'),
                    Entidade.tipo_entidade.ilike('%AMBOS%')
                )
            ).scalar()
            self.lbl_total_forn.setText(str(total_forn))

        except Exception as e:
            print(f"Erro ao carregar dashboard produtos: {e}")