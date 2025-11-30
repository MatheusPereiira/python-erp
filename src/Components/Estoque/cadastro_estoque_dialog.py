# src/Components/Estoque/cadastro_estoque_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QLineEdit, QFormLayout, QTextEdit, QComboBox, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QMessageBox, QSpinBox, QDateEdit
)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import QDate

from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError

from datetime import date

from src.Models.models import Item, Fornecedor, MovimentoEstoque

class FiltroEstoqueDialog(QDialog):
    def __init__(self, current_filters=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros de Estoque")
        self.setFixedSize(420, 380)

        self.current_filters = current_filters or {}
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Texto (nome / código)
        self.produto_input = QLineEdit()
        self.produto_input.setPlaceholderText("Ex: Parafuso, Tinta, ou código...")
        form_layout.addRow("Produto / Código contém:", self.produto_input)

        # Quantidade mínima (estoque)
        self.qtd_min_input = QLineEdit()
        self.qtd_min_input.setValidator(QDoubleValidator(0.0, 9999999.99, 2))
        self.qtd_min_input.setPlaceholderText("Somente itens com estoque >= ...")
        form_layout.addRow("Quantidade Mínima:", self.qtd_min_input)

        # Somente abaixo do mínimo
        from PyQt6.QtWidgets import QCheckBox
        self.chk_critico = QCheckBox("Somente itens abaixo do estoque mínimo")
        form_layout.addRow(self.chk_critico)

        # Ordenação (similar ao financeiro)
        self.sort_column_combo = QComboBox()
        self.sort_column_combo.addItems(["ID", "Nome", "Estoque", "Estoque Mínimo"])
        form_layout.addRow("Ordenar por:", self.sort_column_combo)

        self.sort_direction_combo = QComboBox()
        self.sort_direction_combo.addItems(["Crescente (ASC)", "Decrescente (DESC)"])
        self.sort_direction_combo.setCurrentIndex(1)
        form_layout.addRow("Direção:", self.sort_direction_combo)

        main_layout.addLayout(form_layout)
        main_layout.addStretch()

        # Botões
        button_layout = QHBoxLayout()
        self.limpar_btn = QPushButton("🧹 Limpar")
        self.aplicar_btn = QPushButton("✔️ Aplicar")
        self.aplicar_btn.setStyleSheet("background-color: #007bff; color: white; font-weight: bold;")
        button_layout.addWidget(self.limpar_btn)
        button_layout.addWidget(self.aplicar_btn)
        main_layout.addLayout(button_layout)

        self.limpar_btn.clicked.connect(self.limpar_filtros)
        self.aplicar_btn.clicked.connect(self.accept)

        # carregar filtros atuais
        self.carregar_filtros(self.current_filters)

    def carregar_filtros(self, filters):
        if filters.get("produto"):
            self.produto_input.setText(filters["produto"])
        if filters.get("min_qtd") is not None:
            self.qtd_min_input.setText(str(filters["min_qtd"]))
        self.chk_critico.setChecked(bool(filters.get("critico", False)))

        # ordenação
        sort_map = {"id":0, "nome":1, "estoque":2, "estoque_minimo":3}
        col = self.current_filters.get("sort_column_field")
        if col and col in sort_map:
            self.sort_column_combo.setCurrentIndex(sort_map[col])
        self.sort_direction_combo.setCurrentIndex(0 if self.current_filters.get("sort_order","DESC") == "ASC" else 1)

    def filtrar(self):
        f = {}
        if self.produto_input.text().strip():
            f["produto"] = self.produto_input.text().strip()
        if self.qtd_min_input.text().strip():
            try:
                f["min_qtd"] = float(self.qtd_min_input.text().strip())
            except ValueError:
                pass
        if self.chk_critico.isChecked():
            f["critico"] = True

        sort_map = ["id", "nome", "estoque", "estoque_minimo"]
        f["sort_column_field"] = sort_map[self.sort_column_combo.currentIndex()]
        f["sort_order"] = "ASC" if self.sort_direction_combo.currentIndex() == 0 else "DESC"

        return f

    def limpar_filtros(self):
        self.produto_input.clear()
        self.qtd_min_input.clear()
        self.chk_critico.setChecked(False)
        self.sort_column_combo.setCurrentIndex(0)
        self.sort_direction_combo.setCurrentIndex(1)
        self.accept()


class MovimentacaoDialog(QDialog):
    """
    Dialog para registrar Entrada ou Saída de estoque.
    type_ = "entrada" ou "saida"
    Não cadastra novos produtos — o combo de produto é só leitura da tabela itens.
    """
    def __init__(self, session, item: Item, type_: str = "entrada", parent=None):
        super().__init__(parent)
        self.session = session
        self.item = item
        self.type_ = type_  # 'entrada' ou 'saida'
        self.setMinimumSize(520, 380)
        self.setWindowTitle(f"{'Entrada' if type_=='entrada' else 'Saída'} - {item.nome}")

        main_layout = QVBoxLayout(self)
        form = QFormLayout()

        # Quantidade
        self.qtd_spin = QSpinBox()
        self.qtd_spin.setMinimum(1)
        self.qtd_spin.setMaximum(10_000_000)

        # Fornecedor - preenche com fornecedores do DB e seleciona fornecedor do item se existir
        self.fornecedor_combo = QComboBox()
        self._load_fornecedores()
        # tenta pré-selecionar fornecedor do item
        if getattr(item, "fornecedor_id", None):
            idx = self.fornecedor_combo.findData(item.fornecedor_id)
            if idx >= 0:
                self.fornecedor_combo.setCurrentIndex(idx)

        # Preços
        double_validator = QDoubleValidator(0.0, 9999999.99, 2)
        self.preco_compra_input = QLineEdit()
        self.preco_compra_input.setValidator(double_validator)
        self.preco_compra_input.setPlaceholderText("Apenas para entradas (opcional)")

        self.preco_venda_input = QLineEdit()
        self.preco_venda_input.setValidator(double_validator)
        self.preco_venda_input.setPlaceholderText("Registrar preço de venda (recomendado)")

        self.obs_input = QLineEdit()
        self.data_edit = QDateEdit()
        self.data_edit.setCalendarPopup(True)
        self.data_edit.setDate(QDate.currentDate())

        form.addRow("Quantidade:", self.qtd_spin)
        form.addRow("Preço Compra (R$):", self.preco_compra_input)
        form.addRow("Preço Venda (R$):", self.preco_venda_input)
        form.addRow("Fornecedor:", self.fornecedor_combo)
        form.addRow("Data:", self.data_edit)
        form.addRow("Observação:", self.obs_input)

        main_layout.addLayout(form)
        main_layout.addStretch()

        # Botões
        btns = QHBoxLayout()
        self.cancel_btn = QPushButton("❌ Cancelar")
        self.save_btn = QPushButton("✔️ Registrar")
        self.save_btn.setStyleSheet("background-color: #28A745; color: white; font-weight: bold;")
        btns.addStretch()
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.save_btn)
        main_layout.addLayout(btns)

        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.registrar)

    def _load_fornecedores(self):
        try:
            self.fornecedor_combo.clear()
            fornecedores = self.session.query(Fornecedor).all()
            self.fornecedor_combo.addItem("— Selecionar —", None)
            for f in fornecedores:
                self.fornecedor_combo.addItem(f.nome or "—", f.id)
        except SQLAlchemyError:
            self.fornecedor_combo.clear()
            self.fornecedor_combo.addItem("— Selecionar —", None)

    def registrar(self):
        qtd = int(self.qtd_spin.value())
        try:
            preco_compra = float(self.preco_compra_input.text() or 0)
        except Exception:
            QMessageBox.warning(self, "Erro", "Preço de compra inválido.")
            return

        try:
            preco_venda = float(self.preco_venda_input.text() or 0)
        except Exception:
            QMessageBox.warning(self, "Erro", "Preço de venda inválido.")
            return

        fornecedor_id = self.fornecedor_combo.currentData() or getattr(self.item, "fornecedor_id", None)

        # requisito do modelo: fornecedor_id não pode ser None (models.movimento_estoque tem nullable=False)
        if fornecedor_id is None:
            QMessageBox.warning(self, "Erro", "Selecione um fornecedor (ou preencha o fornecedor no cadastro do produto).")
            return

        obs = self.obs_input.text().strip()
        data_mov = self.data_edit.date().toPyDate()

        novo_estoque = float(self.item.estoque or 0)
        if self.type_ == "entrada":
            novo_estoque += qtd
        else:
            if qtd > novo_estoque:
                QMessageBox.warning(self, "Erro", "Quantidade de saída maior que estoque disponível.")
                return
            novo_estoque -= qtd

        try:
            mov = MovimentoEstoque(
                item_id=self.item.id,
                quantidade=qtd,
                preco_venda=preco_venda,
                preco_compra=preco_compra,
                fornecedor_id=fornecedor_id,
                estoque_minimo=int(self.item.estoque_minimo or 0),
                estoque_maximo=0,
                data_ultima_mov=data_mov,
                tipo_movimento=self.type_,
                observacao=obs
            )
            self.session.add(mov)

            # atualizar item
            self.session.execute(update(Item).where(Item.id == self.item.id).values(estoque=novo_estoque))
            self.session.commit()
            QMessageBox.information(self, "Sucesso", "Movimentação registrada.")
            self.accept()
        except SQLAlchemyError as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erro DB", f"Falha ao registrar movimentação.\n{e}")
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erro", f"Falha ao registrar movimentação.\n{e}")
