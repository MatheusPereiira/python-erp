from PyQt6.QtWidgets import (
    QDialog, QLineEdit, QFormLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QTextEdit, QCheckBox, QComboBox, QGroupBox
)
from src.Models.models import Entidade, TipoPessoaEnum

# Mapeamentos de rótulo ↔ valor salvo no banco
TIPOS_ENTIDADE_LABEL_TO_DB = {
    "Cliente": "CLIENTE",
    "Fornecedor": "FORNECEDOR",
    "Transportadora": "TRANSPORTADORA",
    "Representante": "REPRESENTANTE",
}
TIPOS_ENTIDADE_DB_TO_LABEL = {v: k for k, v in TIPOS_ENTIDADE_LABEL_TO_DB.items()}


def parse_categorias(db_value: str) -> list[str]:
    """
    Converte a string salva no banco em lista de tokens.
    Ex: "CLIENTE,TRANSPORTADORA" -> ["CLIENTE", "TRANSPORTADORA"]
    """
    if not db_value:
        return []
    return [p.strip().upper() for p in db_value.split(",") if p.strip()]


def serialize_categorias(tokens: list[str]) -> str:
    """
    Converte lista de tokens em string única para salvar.
    Ex: ["CLIENTE", "TRANSPORTADORA"] -> "CLIENTE,TRANSPORTADORA"
    """
    tokens_norm = []
    for t in tokens:
        t = (t or "").strip().upper()
        if t and t not in tokens_norm:
            tokens_norm.append(t)
    return ",".join(tokens_norm)


class CadastroPessoaDialog(QDialog):
    def __init__(self, session, entidade: Entidade | None = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.entidade = entidade
        self.is_editing = entidade is not None

        titulo = "Editar Pessoa" if self.is_editing else "Nova Pessoa"
        self.setWindowTitle(titulo)
        self.setMinimumWidth(480)

        main_layout = QVBoxLayout(self)

        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet(
            "font-size: 14pt; padding: 8px; "
            "background-color: #E6F0FF; border: 1px solid #B3CDE6;"
        )
        main_layout.addWidget(titulo_label)

        form_layout = QFormLayout()

        # ===== CATEGORIAS (CHECKBOXES) =====
        categorias_group = QGroupBox("Categorias (marque todas que se aplicam)")
        cat_layout = QHBoxLayout()

        self.chk_cliente = QCheckBox("Cliente")
        self.chk_fornecedor = QCheckBox("Fornecedor")
        self.chk_transportadora = QCheckBox("Transportadora")
        self.chk_representante = QCheckBox("Representante")

        cat_layout.addWidget(self.chk_cliente)
        cat_layout.addWidget(self.chk_fornecedor)
        cat_layout.addWidget(self.chk_transportadora)
        cat_layout.addWidget(self.chk_representante)
        categorias_group.setLayout(cat_layout)

        # Tipo de pessoa (física/jurídica)
        self.tipo_pessoa_combo = QComboBox()
        self.tipo_pessoa_combo.addItems(["Física", "Jurídica"])

        self.razao_social_input = QLineEdit()
        self.nome_fantasia_input = QLineEdit()
        self.cpf_cnpj_input = QLineEdit()
        self.inscricao_estadual_input = QLineEdit()
        self.obs_input = QTextEdit()
        self.bloqueado_check = QCheckBox("Bloqueado")

        # Montagem do form
        form_layout.addRow(categorias_group)
        form_layout.addRow("Tipo de Pessoa:", self.tipo_pessoa_combo)
        form_layout.addRow("Razão Social / Nome:", self.razao_social_input)
        form_layout.addRow("Nome Fantasia:", self.nome_fantasia_input)
        form_layout.addRow("CPF/CNPJ:", self.cpf_cnpj_input)
        form_layout.addRow("Inscrição Estadual:", self.inscricao_estadual_input)
        form_layout.addRow("Observações:", self.obs_input)
        form_layout.addRow("Status:", self.bloqueado_check)

        main_layout.addLayout(form_layout)

        # Botões
        botoes_layout = QHBoxLayout()
        cancelar_btn = QPushButton("❌ Cancelar")
        salvar_btn = QPushButton("✅ Salvar")
        salvar_btn.setStyleSheet("background-color: #28A745; color: white; font-weight: bold; border-radius: 5px; padding: 5px;")
        botoes_layout.addStretch(1)
        botoes_layout.addWidget(cancelar_btn)
        botoes_layout.addWidget(salvar_btn)
        main_layout.addLayout(botoes_layout)

        salvar_btn.clicked.connect(self.salvar)
        cancelar_btn.clicked.connect(self.reject)

        if self.is_editing:
            self._carregar_dados()
        else:
            self.bloqueado_check.setChecked(False)

    # ------------------------------------------------------------------ #
    #   CARREGAR / COLETAR DADOS
    # ------------------------------------------------------------------ #
    def _carregar_dados(self):
        # Categorias (pode ter várias)
        tokens = parse_categorias(self.entidade.tipo_entidade)

        if "CLIENTE" in tokens:
            self.chk_cliente.setChecked(True)
        if "FORNECEDOR" in tokens:
            self.chk_fornecedor.setChecked(True)
        if "TRANSPORTADORA" in tokens:
            self.chk_transportadora.setChecked(True)
        if "REPRESENTANTE" in tokens:
            self.chk_representante.setChecked(True)

        # Tipo pessoa
        if self.entidade.tipo_pessoa == TipoPessoaEnum.FISICA:
            self.tipo_pessoa_combo.setCurrentIndex(0)
        elif self.entidade.tipo_pessoa == TipoPessoaEnum.JURIDICA:
            self.tipo_pessoa_combo.setCurrentIndex(1)

        self.razao_social_input.setText(self.entidade.razao_social or "")
        self.nome_fantasia_input.setText(self.entidade.nome_fantasia or "")
        self.cpf_cnpj_input.setText(self.entidade.cpf_cnpj or "")
        self.inscricao_estadual_input.setText(self.entidade.inscricao_estadual or "")
        self.obs_input.setPlainText(self.entidade.obs or "")
        self.bloqueado_check.setChecked(bool(self.entidade.esta_bloqueado))

    def _obter_categorias_selecionadas(self) -> list[str]:
        tokens = []
        if self.chk_cliente.isChecked():
            tokens.append("CLIENTE")
        if self.chk_fornecedor.isChecked():
            tokens.append("FORNECEDOR")
        if self.chk_transportadora.isChecked():
            tokens.append("TRANSPORTADORA")
        if self.chk_representante.isChecked():
            tokens.append("REPRESENTANTE")
        return tokens

    def _coletar_dados(self):
        razao = self.razao_social_input.text().strip()
        if not razao:
            QMessageBox.warning(self, "Validação", "O campo 'Razão Social / Nome' é obrigatório.")
            return None

        categorias_tokens = self._obter_categorias_selecionadas()
        if not categorias_tokens:
            QMessageBox.warning(
                self,
                "Validação",
                "Selecione pelo menos uma categoria (Cliente, Fornecedor, etc.).",
            )
            return None

        # Tipo de pessoa
        if self.tipo_pessoa_combo.currentIndex() == 0:
            tipo_pessoa = TipoPessoaEnum.FISICA
        else:
            tipo_pessoa = TipoPessoaEnum.JURIDICA

        data = {
            "tipo_entidade": serialize_categorias(categorias_tokens),
            "tipo_pessoa": tipo_pessoa,
            "razao_social": razao,
            "nome_fantasia": self.nome_fantasia_input.text().strip() or None,
            "cpf_cnpj": self.cpf_cnpj_input.text().strip() or None,
            "inscricao_estadual": self.inscricao_estadual_input.text().strip() or None,
            "obs": self.obs_input.toPlainText().strip() or None,
            "esta_bloqueado": self.bloqueado_check.isChecked(),
        }
        return data

    # ------------------------------------------------------------------ #
    #   SALVAR
    # ------------------------------------------------------------------ #
    def salvar(self):
        data = self._coletar_dados()
        if data is None:
            return

        try:
            if self.is_editing:
                for campo, valor in data.items():
                    setattr(self.entidade, campo, valor)
                self.session.commit()
                QMessageBox.information(self, "Sucesso", "Pessoa atualizada com sucesso!")
            else:
                nova = Entidade(**data)
                self.session.add(nova)
                self.session.commit()
                QMessageBox.information(self, "Sucesso", "Pessoa cadastrada com sucesso!")
            self.accept()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(
                self, "Erro no BD", f"Não foi possível salvar a pessoa.\nErro: {e}"
            )
