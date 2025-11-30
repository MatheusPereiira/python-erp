from PyQt6.QtWidgets import (
    QDialog, QLineEdit, QFormLayout, QTextEdit, QSizePolicy, QCheckBox,
    QComboBox, QGroupBox, QRadioButton, QVBoxLayout, QHBoxLayout, QMessageBox,
    QLabel, QPushButton, QDateEdit
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import QDate

from sqlalchemy import update
from datetime import datetime

from src.Models.models import Financeiro, EnumStatus
from src.Utils.correcaoDeValores import Converter_decimal


# ==========================================================
#   FILTRO FINANCEIRO
# ==========================================================
class FiltroFinanceiroDialog(QDialog):
    def __init__(self, current_filters, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros Financeiros")
        self.setFixedSize(420, 450)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        double_validator = QDoubleValidator(0.0, 9999999.99, 2)

        # -----------------------------
        # Status
        # -----------------------------
        status_group = QGroupBox("Status do Lançamento")
        status_layout = QHBoxLayout(status_group)
        self.radio_aberta = QRadioButton("Aberta")
        self.radio_paga = QRadioButton("Paga")
        self.radio_cancelada = QRadioButton("Cancelada")
        self.radio_todos = QRadioButton("Todos")
        self.radio_todos.setChecked(True)

        status_layout.addWidget(self.radio_aberta)
        status_layout.addWidget(self.radio_paga)
        status_layout.addWidget(self.radio_cancelada)
        status_layout.addWidget(self.radio_todos)
        form_layout.addRow(status_group)

        # -----------------------------
        # Valor mínimo/máximo
        # -----------------------------
        self.valor_min_input = QLineEdit()
        self.valor_min_input.setValidator(double_validator)
        form_layout.addRow("Valor Mínimo:", self.valor_min_input)

        self.valor_max_input = QLineEdit()
        self.valor_max_input.setValidator(double_validator)
        form_layout.addRow("Valor Máximo:", self.valor_max_input)

        # -----------------------------
        # Vencimento (intervalo)
        # -----------------------------
        self.venc_inicio = QDateEdit()
        self.venc_inicio.setDisplayFormat("dd/MM/yyyy")
        self.venc_inicio.setDate(QDate.currentDate())
        self.venc_inicio.setCalendarPopup(True)

        self.venc_final = QDateEdit()
        self.venc_final.setDisplayFormat("dd/MM/yyyy")
        self.venc_final.setDate(QDate.currentDate())
        self.venc_final.setCalendarPopup(True)

        form_layout.addRow("Vencimento Inicial:", self.venc_inicio)
        form_layout.addRow("Vencimento Final:", self.venc_final)

        # -----------------------------
        # Ordenação
        # -----------------------------
        sort_group = QGroupBox("Ordenação")
        sort_layout = QFormLayout(sort_group)

        self.sort_column_combo = QComboBox()
        self.sort_column_combo.addItems([
            "ID", "Valor", "Vencimento", "Status"
        ])
        sort_layout.addRow("Ordenar Por:", self.sort_column_combo)

        self.sort_direction_combo = QComboBox()
        self.sort_direction_combo.addItems(["Crescente (ASC)", "Decrescente (DESC)"])
        self.sort_direction_combo.setCurrentIndex(1)
        sort_layout.addRow("Direção:", self.sort_direction_combo)

        form_layout.addRow(sort_group)

        main_layout.addLayout(form_layout)
        main_layout.addStretch()

        # -----------------------------
        # Botões
        # -----------------------------
        button_layout = QHBoxLayout()
        self.limpar_btn = QPushButton("🧹 Limpar")
        self.aplicar_btn = QPushButton("✔️ Aplicar")
        self.aplicar_btn.setStyleSheet("background-color: #007bff; color: white; font-weight: bold;")

        button_layout.addWidget(self.limpar_btn)
        button_layout.addWidget(self.aplicar_btn)

        main_layout.addLayout(button_layout)

        self.limpar_btn.clicked.connect(self.limpar_filtros)
        self.aplicar_btn.clicked.connect(self.accept)

        # carrega filtros atuais
        self.carregar_filtros(current_filters)

    # --------------------------------------------------
    def carregar_filtros(self, filters):
        status = filters.get("status")
        if status == EnumStatus.ABERTA:
            self.radio_aberta.setChecked(True)
        elif status == EnumStatus.PAGA:
            self.radio_paga.setChecked(True)
        elif status == EnumStatus.CANCELADA:
            self.radio_cancelada.setChecked(True)
        else:
            self.radio_todos.setChecked(True)


        if filters.get("venc_inicio"):
            d = filters["venc_inicio"]
            self.venc_inicio.setDate(QDate(d.year, d.month, d.day))

        if filters.get("venc_final"):
            d = filters["venc_final"]
            self.venc_final.setDate(QDate(d.year, d.month, d.day))


        if filters.get("valor_min"):
            self.valor_min_input.setText(str(filters["valor_min"]))

        if filters.get("valor_max"):
            self.valor_max_input.setText(str(filters["valor_max"]))

    # --------------------------------------------------
    def filtrar(self):
        filters = {}

        if self.radio_aberta.isChecked():
            filters["status"] = EnumStatus.ABERTA
        elif self.radio_paga.isChecked():
            filters["status"] = EnumStatus.PAGA
        elif self.radio_cancelada.isChecked():
            filters["status"] = EnumStatus.CANCELADA

        valor_min = Converter_decimal(self.valor_min_input.text())
        if valor_min is not None and valor_min >= 0:
            filters["valor_min"] = valor_min

        valor_max = Converter_decimal(self.valor_max_input.text())
        if valor_max is not None and valor_max >= 0:
            filters["valor_max"] = valor_max

        # Ordenação
        sort_map = ["id", "valor_nota", "vencimento", "status"]
        filters["sort_column_field"] = sort_map[self.sort_column_combo.currentIndex()]
        filters["sort_order"] = "ASC" if self.sort_direction_combo.currentIndex() == 0 else "DESC"
        filters["venc_inicio"] = self.venc_inicio.date().toPyDate()
        filters["venc_final"] = self.venc_final.date().toPyDate()


        return filters

    # --------------------------------------------------
    def limpar_filtros(self):
        self.radio_todos.setChecked(True)
        self.venc_inicio.setDate(QDate.currentDate())
        self.venc_final.setDate(QDate.currentDate())
        self.valor_min_input.clear()
        self.valor_max_input.clear()
        self.sort_column_combo.setCurrentIndex(0)
        self.sort_direction_combo.setCurrentIndex(1)
        self.accept()
        




# ==========================================================
#   CADASTRO FINANCEIRO
# ==========================================================
class CadastroFinanceiroDialog(QDialog):
    def __init__(self, session, lancamento=None, parent=None):
        super().__init__(parent)
        self.session = session
        self.lancamento = lancamento
        self.is_editing = lancamento is not None

        titulo = "Editar Lançamento Financeiro" if self.is_editing else "Novo Lançamento Financeiro"
        self.setWindowTitle(titulo)
        self.setMinimumSize(550, 500)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # título
        title_label = QLabel(titulo)
        title_label.setStyleSheet(
            "font-size: 16pt; padding: 10px; background-color: #E6F0FF; border: 1px solid #B3CDE6;"
        )
        main_layout.addWidget(title_label)

        double_validator = QDoubleValidator(0.0, 9999999.99, 2)

        # ------------------------
        # Campos
        # ------------------------
        self.id_label = QLabel(str(lancamento.id) if self.is_editing else "Automático")

        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["Pagar (P)", "Receber (R)"])

        self.origem_combo = QComboBox()
        self.origem_combo.addItems(["Compra (C)", "Venda (V)"])

        self.descricao_input = QLineEdit()

        self.valor_input = QLineEdit()
        self.valor_input.setValidator(double_validator)

        self.vencimento_input = QDateEdit()
        self.vencimento_input.setDisplayFormat("dd/MM/yyyy")
        self.vencimento_input.setDate(QDate.currentDate())
        self.vencimento_input.setCalendarPopup(True)

        self.status_combo = QComboBox()
        self.status_combo.addItems([s.name for s in EnumStatus])


        # adiciona ao layout
        form_layout.addRow("ID:", self.id_label)
        form_layout.addRow("Tipo Lançamento:", self.tipo_combo)
        form_layout.addRow("Origem:", self.origem_combo)
        form_layout.addRow("Descrição:", self.descricao_input)
        form_layout.addRow("Valor (R$):", self.valor_input)
        form_layout.addRow("Vencimento:", self.vencimento_input)
        form_layout.addRow("Status:", self.status_combo)

        main_layout.addLayout(form_layout)
        main_layout.addStretch()

        if self.is_editing:
            self.preencher_formulario()

        # ------------------------
        # Botões
        # ------------------------
        button_layout = QHBoxLayout()
        self.cancelar_btn = QPushButton("❌ Cancelar")
        self.salvar_btn = QPushButton("💾 Salvar")
        self.salvar_btn.setStyleSheet("background-color: #28A745; color: white; font-weight: bold;")

        button_layout.addStretch()
        button_layout.addWidget(self.cancelar_btn)
        button_layout.addWidget(self.salvar_btn)
        main_layout.addLayout(button_layout)

        self.cancelar_btn.clicked.connect(self.reject)
        self.salvar_btn.clicked.connect(self.salvar)

    # ---------------------------------------------------
    def preencher_formulario(self):
        f = self.lancamento

        self.tipo_combo.setCurrentIndex(0 if f.tipo_lancamento == 'P' else 1)
        self.origem_combo.setCurrentIndex(0 if f.origem == 'C' else 1)

        self.descricao_input.setText(f.descricao or "")
        self.valor_input.setText(f"{float(f.valor_nota):.2f}")

        if f.vencimento:
            self.vencimento_input.setDate(QDate(f.vencimento.year, f.vencimento.month, f.vencimento.day))

        self.status_combo.setCurrentIndex(list(EnumStatus).index(f.status))


    # ---------------------------------------------------
    def carregar_dados(self):
        try:
            dados = {
                "tipo_lancamento": "P" if self.tipo_combo.currentIndex() == 0 else "R",
                "origem": "C" if self.origem_combo.currentIndex() == 0 else "V",
                "descricao": self.descricao_input.text().strip(),
                "valor_nota": Converter_decimal(self.valor_input.text()),
                "vencimento": self.vencimento_input.date().toPyDate(),
                "status": EnumStatus[self.status_combo.currentText()]

            }

            if not dados["descricao"]:
                raise ValueError("O campo Descrição é obrigatório.")

            if dados["valor_nota"] is None or dados["valor_nota"] <= 0:
                raise ValueError("Valor inválido.")

            return dados

        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))
            return None

    # ---------------------------------------------------
    def salvar(self):
        dados = self.carregar_dados()
        if dados is None:
            return

        if self.is_editing:
            try:
                self.session.execute(
                    update(Financeiro).where(Financeiro.id == self.lancamento.id).values(**dados)
                )
                self.session.commit()
                QMessageBox.information(self, "Sucesso", "Lançamento atualizado com sucesso!")
                self.accept()
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Erro", f"Falha ao atualizar.\n{e}")
        else:
            novo = Financeiro(**dados)

            try:
                self.session.add(novo)
                self.session.commit()
                QMessageBox.information(self, "Sucesso", "Lançamento criado com sucesso!")
                self.accept()
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Erro", f"Falha ao salvar.\n{e}")
