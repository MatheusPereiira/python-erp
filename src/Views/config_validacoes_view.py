# sistemacomercial/src/Views/config_validacoes_view.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QFormLayout, QCheckBox, QLineEdit, QMessageBox
)
from PyQt6.QtGui import QDoubleValidator  # ✅ CORREÇÃO: QDoubleValidator está em QtGui
from PyQt6.QtCore import Qt

class ConfigValidacoesWidget(QWidget):
    def __init__(self, sessao):
        super().__init__()
        self.sessao = sessao
        self.configuracoes = {}
        
        self.setup_ui()
        self.carregar_configuracoes()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("Configurações de Validações Comerciais")
        titulo.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 10px; color: #424242;")
        layout_principal.addWidget(titulo)

        # Grupo de Validações
        grupo_validacoes = QGroupBox("Validações Ativas")
        layout_validacoes = QFormLayout(grupo_validacoes)
        
        self.check_cliente_obrigatorio = QCheckBox("Cliente obrigatório")
        self.check_cliente_obrigatorio.setChecked(True)
        layout_validacoes.addRow(self.check_cliente_obrigatorio)
        
        self.check_limite_credito = QCheckBox("Validar limite de crédito")
        self.check_limite_credito.setChecked(True)
        layout_validacoes.addRow(self.check_limite_credito)
        
        self.check_preco_minimo = QCheckBox("Validar preço mínimo")
        self.check_preco_minimo.setChecked(True)
        layout_validacoes.addRow(self.check_preco_minimo)
        
        self.check_validade = QCheckBox("Validar data de validade")
        self.check_validade.setChecked(True)
        layout_validacoes.addRow(self.check_validade)
        
        self.check_estoque = QCheckBox("Validar estoque")
        self.check_estoque.setChecked(True)
        layout_validacoes.addRow(self.check_estoque)
        
        layout_principal.addWidget(grupo_validacoes)

        # Grupo de Parâmetros
        grupo_parametros = QGroupBox("Parâmetros das Validações")
        layout_parametros = QFormLayout(grupo_parametros)
        
        self.input_limite_padrao = QLineEdit()
        self.input_limite_padrao.setValidator(QDoubleValidator(0, 9999999.99, 2))  # ✅ CORRIGIDO
        self.input_limite_padrao.setText("5000.00")
        self.input_limite_padrao.setPlaceholderText("R$ 0,00")
        layout_parametros.addRow("Limite de crédito padrão:", self.input_limite_padrao)
        
        self.input_margem_minima = QLineEdit()
        self.input_margem_minima.setValidator(QDoubleValidator(0, 100, 2))  # ✅ CORRIGIDO
        self.input_margem_minima.setText("10.00")
        self.input_margem_minima.setPlaceholderText("%")
        layout_parametros.addRow("Margem mínima (%):", self.input_margem_minima)
        
        layout_principal.addWidget(grupo_parametros)

        # Botões
        botoes_layout = QHBoxLayout()
        
        btn_salvar = QPushButton("💾 Salvar Configurações")
        btn_salvar.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_salvar.clicked.connect(self.salvar_configuracoes)
        
        btn_restaurar = QPushButton("🔄 Restaurar Padrões")
        btn_restaurar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_restaurar.clicked.connect(self.restaurar_padroes)
        
        botoes_layout.addWidget(btn_restaurar)
        botoes_layout.addStretch()
        botoes_layout.addWidget(btn_salvar)
        
        layout_principal.addLayout(botoes_layout)
        layout_principal.addStretch()

    def carregar_configuracoes(self):
        """Carrega as configurações salvas"""
        # Aqui você pode carregar do banco de dados ou arquivo de configuração
        # Por enquanto, usamos valores padrão
        pass

    def salvar_configuracoes(self):
        """Salva as configurações"""
        try:
            # Coletar configurações
            self.configuracoes = {
                'cliente_obrigatorio': self.check_cliente_obrigatorio.isChecked(),
                'limite_credito': self.check_limite_credito.isChecked(),
                'preco_minimo': self.check_preco_minimo.isChecked(),
                'validade': self.check_validade.isChecked(),
                'estoque': self.check_estoque.isChecked(),
                'limite_padrao': float(self.input_limite_padrao.text().replace(',', '.')),
                'margem_minima': float(self.input_margem_minima.text().replace(',', '.'))
            }
            
            # Aqui você salvaria no banco de dados ou arquivo
            QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!")
            
        except ValueError as e:
            QMessageBox.warning(self, "Erro", "Verifique os valores informados.")

    def restaurar_padroes(self):
        """Restaura as configurações padrão"""
        self.check_cliente_obrigatorio.setChecked(True)
        self.check_limite_credito.setChecked(True)
        self.check_preco_minimo.setChecked(True)
        self.check_validade.setChecked(True)
        self.check_estoque.setChecked(True)
        self.input_limite_padrao.setText("5000.00")
        self.input_margem_minima.setText("10.00")
        
        QMessageBox.information(self, "Sucesso", "Configurações restauradas para os valores padrão.")