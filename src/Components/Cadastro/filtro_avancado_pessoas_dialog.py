from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton,
    QGroupBox, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt

CATEGORIAS_LISTA = [
    "Todos",
    "Cliente",
    "Fornecedor",
    "Transportadora",
    "Representante",
]


class FiltroAvancadoPessoasDialog(QDialog):
    def __init__(self, parent=None, filtros_atuais=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros Avançados - Pessoas")
        self.setMinimumWidth(450)

        self.filtros_atuais = filtros_atuais or {}

        main_layout = QVBoxLayout(self)

        # ==========================
        # Categoria
        # ==========================
        categoria_group = QGroupBox("Categoria")
        categoria_layout = QVBoxLayout()

        self.combo_categoria = QComboBox()
        self.combo_categoria.addItems(CATEGORIAS_LISTA)
        categoria_layout.addWidget(self.combo_categoria)

        categoria_group.setLayout(categoria_layout)

        # ==========================
        # Tipo Pessoa
        # ==========================
        tipo_group = QGroupBox("Tipo de Pessoa")
        tipo_layout = QHBoxLayout()

        self.radio_fisica = QRadioButton("Física")
        self.radio_juridica = QRadioButton("Jurídica")
        self.radio_todos = QRadioButton("Todos")
        self.radio_todos.setChecked(True)

        tipo_layout.addWidget(self.radio_fisica)
        tipo_layout.addWidget(self.radio_juridica)
        tipo_layout.addWidget(self.radio_todos)

        tipo_group.setLayout(tipo_layout)

        # ==========================
        # Campos de texto
        # ==========================
        self.input_razao = QLineEdit()
        self.input_razao.setPlaceholderText("Razão Social / Nome contém...")

        self.input_cpf = QLineEdit()
        self.input_cpf.setPlaceholderText("CPF/CNPJ contém...")

        # ==========================
        # Botões
        # ==========================
        botoes_layout = QHBoxLayout()

        self.btn_limpar = QPushButton("🧹 Limpar Filtros")
        self.btn_aplicar = QPushButton("✔️ Aplicar Filtros")

        self.btn_limpar.setStyleSheet(
            "background-color: #f8d7da; border: 1px solid #dc3545; padding: 8px;"
        )
        self.btn_aplicar.setStyleSheet(
            "background-color: #007bff; color: white; padding: 8px;"
        )

        self.btn_limpar.clicked.connect(self.limpar_filtros)
        self.btn_aplicar.clicked.connect(self.aplicar)

        botoes_layout.addWidget(self.btn_limpar)
        botoes_layout.addWidget(self.btn_aplicar)

        # ==========================
        # Monta layout final
        # ==========================
        main_layout.addWidget(categoria_group)
        main_layout.addWidget(tipo_group)
        main_layout.addWidget(QLabel("Razão Social / Nome:"))
        main_layout.addWidget(self.input_razao)
        main_layout.addWidget(QLabel("CPF/CNPJ:"))
        main_layout.addWidget(self.input_cpf)
        main_layout.addStretch()
        main_layout.addLayout(botoes_layout)

    # APPLY
    def aplicar(self):
        filtros = {
            "categoria": self.combo_categoria.currentText(),
            "tipo_pessoa": (
                "FISICA" if self.radio_fisica.isChecked()
                else "JURIDICA" if self.radio_juridica.isChecked()
                else "TODOS"
            ),
            "razao": self.input_razao.text().strip(),
            "cpf": self.input_cpf.text().strip(),
        }
        self.filtros = filtros
        self.accept()

    # LIMPAR
    def limpar_filtros(self):
        self.combo_categoria.setCurrentIndex(0)
        self.radio_todos.setChecked(True)
        self.input_razao.clear()
        self.input_cpf.clear()
