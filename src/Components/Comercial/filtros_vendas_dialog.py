# sistemacomercial/src/Components/Comercial/filtros_vendas_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QDateEdit, QLineEdit, QFormLayout, QGroupBox
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QDoubleValidator
from datetime import datetime, timedelta

class FiltroVendasDialog(QDialog):
    def __init__(self, filtros_atuais, sessao, parent=None):
        super().__init__(parent)
        self.filtros_atuais = filtros_atuais or {}
        self.sessao = sessao
        
        self.setWindowTitle("Filtros de Vendas")
        self.setFixedSize(400, 500)
        
        self.setup_ui()
        self.carregar_filtros_existentes()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Filtros por data
        grupo_data = QGroupBox("Filtrar por Data")
        layout_data = QFormLayout(grupo_data)
        
        self.data_inicio = QDateEdit()
        self.data_inicio.setDate(QDate.currentDate().addDays(-30))
        self.data_inicio.setCalendarPopup(True)
        layout_data.addRow("Data Início:", self.data_inicio)
        
        self.data_fim = QDateEdit()
        self.data_fim.setDate(QDate.currentDate())
        self.data_fim.setCalendarPopup(True)
        layout_data.addRow("Data Fim:", self.data_fim)
        
        layout.addWidget(grupo_data)
        
        # Filtros por status
        grupo_status = QGroupBox("Filtrar por Status")
        layout_status = QFormLayout(grupo_status)
        
        self.combo_status = QComboBox()
        self.combo_status.addItem("Todos os Status", "")
        self.combo_status.addItem("✅ Finalizada", "F")
        self.combo_status.addItem("⏳ Pendente", "P")
        self.combo_status.addItem("❌ Cancelada", "C")
        layout_status.addRow("Status:", self.combo_status)
        
        layout.addWidget(grupo_status)
        
        # Filtros por valor
        grupo_valor = QGroupBox("Filtrar por Valor")
        layout_valor = QFormLayout(grupo_valor)
        
        validador = QDoubleValidator(0, 9999999.99, 2)
        
        self.valor_min = QLineEdit()
        self.valor_min.setValidator(validador)
        self.valor_min.setPlaceholderText("R$ 0,00")
        layout_valor.addRow("Valor Mínimo:", self.valor_min)
        
        self.valor_max = QLineEdit()
        self.valor_max.setValidator(validador)
        self.valor_max.setPlaceholderText("R$ 0,00")
        layout_valor.addRow("Valor Máximo:", self.valor_max)
        
        layout.addWidget(grupo_valor)
        
        layout.addStretch()
        
        # Botões
        botoes_layout = QHBoxLayout()
        
        btn_limpar = QPushButton("🧹 Limpar Filtros")
        btn_limpar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_limpar.clicked.connect(self.limpar_filtros)
        
        btn_aplicar = QPushButton("✅ Aplicar Filtros")
        btn_aplicar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_aplicar.clicked.connect(self.aplicar_filtros)
        
        botoes_layout.addWidget(btn_limpar)
        botoes_layout.addStretch()
        botoes_layout.addWidget(btn_aplicar)
        
        layout.addLayout(botoes_layout)

    def carregar_filtros_existentes(self):
        if self.filtros_atuais.get('data_inicio'):
            self.data_inicio.setDate(QDate(self.filtros_atuais['data_inicio']))
        
        if self.filtros_atuais.get('data_fim'):
            self.data_fim.setDate(QDate(self.filtros_atuais['data_fim']))
        
        if self.filtros_atuais.get('status'):
            index = self.combo_status.findData(self.filtros_atuais['status'])
            if index >= 0:
                self.combo_status.setCurrentIndex(index)
        
        if self.filtros_atuais.get('valor_min'):
            self.valor_min.setText(f"{self.filtros_atuais['valor_min']:.2f}")
        
        if self.filtros_atuais.get('valor_max'):
            self.valor_max.setText(f"{self.filtros_atuais['valor_max']:.2f}")

    def limpar_filtros(self):
        self.data_inicio.setDate(QDate.currentDate().addDays(-30))
        self.data_fim.setDate(QDate.currentDate())
        self.combo_status.setCurrentIndex(0)
        self.valor_min.clear()
        self.valor_max.clear()
        
        self.filtros_atuais = {}
        self.accept()

    def aplicar_filtros(self):
        filtros = {}
        
        # Data
        if self.data_inicio.date() != QDate.currentDate().addDays(-30):
            filtros['data_inicio'] = self.data_inicio.date().toPyDate()
        
        if self.data_fim.date() != QDate.currentDate():
            filtros['data_fim'] = self.data_fim.date().toPyDate()
        
        # Status
        status = self.combo_status.currentData()
        if status:
            filtros['status'] = status
        
        # Valor
        if self.valor_min.text().strip():
            try:
                valor = float(self.valor_min.text().replace(',', '.'))
                filtros['valor_min'] = valor
            except ValueError:
                pass
        
        if self.valor_max.text().strip():
            try:
                valor = float(self.valor_max.text().replace(',', '.'))
                filtros['valor_max'] = valor
            except ValueError:
                pass
        
        self.filtros_atuais = filtros
        self.accept()

    def obter_filtros(self):
        return self.filtros_atuais