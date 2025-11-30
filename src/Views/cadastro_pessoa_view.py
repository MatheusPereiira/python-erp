from src.Components.Cadastro.filtro_avancado_pessoas_dialog import FiltroAvancadoPessoasDialog
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableView, QLabel, QMessageBox, QLineEdit, QHeaderView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt
from sqlalchemy import select


from src.Models.models import Entidade
from src.Components.Cadastro.cadastro_pessoa_dialog import (
    CadastroPessoaDialog,
    TIPOS_ENTIDADE_DB_TO_LABEL,
    parse_categorias
)

# Quais tipos de entidade aparecem nessa tela
TIPOS_ENTIDADE_PERMITIDOS = [
    "CLIENTE",
    "FORNECEDOR",
    "TRANSPORTADORA",
    "REPRESENTANTE",
]


class CadastroPessoasWidget(QWidget):
    def __init__(self, session):
        super().__init__()
        self.session = session

        self.main_layout = QVBoxLayout(self)
        self.filtros_avancados = {
        "categoria": "Todos",
        "tipo_pessoa": "TODOS",
        "razao": "",
        "cpf": "",
    }


        # ===== TÍTULO (igual ao Cadastro Produtos) =====
        self.title_label = QLabel("Cadastro de Pessoas")
        self.title_label.setStyleSheet(
            "font-size: 20pt; font-weight: bold; margin-bottom: 10px;"
        )
        self.main_layout.addWidget(self.title_label)

        # ===== BUSCA + FILTRO AVANÇADO (mesmo layout) =====
        search_filter_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nome, CPF/CNPJ...")
        self.search_input.textChanged.connect(self.load_data)

        self.filter_btn = QPushButton("⚙️ Filtro Avançado")
        # Estilo inspirado no Cadastro de Produtos
        self.filter_btn.setStyleSheet(
            "background-color: #E0E0E0; color: #333333; "
            "font-weight: bold; padding: 8px 16px; "
            "border-radius: 5px; border: 1px solid #CCCCCC;"
        )
        self.filter_btn.setFixedWidth(150)
        self.filter_btn.clicked.connect(self.open_filter_dialog)

        search_filter_layout.addWidget(self.search_input)
        search_filter_layout.addWidget(self.filter_btn)

        self.main_layout.addLayout(search_filter_layout)

        # ===== BOTÕES COLORIDOS (mesmo padrão de Produtos) =====
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ Nova Pessoa")
        self.edit_btn = QPushButton("📝 Editar")
        self.delete_btn = QPushButton("❌ Excluir")
        self.refresh_btn = QPushButton("🔄 Atualizar")

        self.add_btn.setStyleSheet(
            "background-color: #28a745; color: white; "
            "padding: 10px; border-radius: 5px;"
        )
        self.edit_btn.setStyleSheet(
            "background-color: #007bff; color: white; "
            "padding: 10px; border-radius: 5px;"
        )
        self.delete_btn.setStyleSheet(
            "background-color: #dc3545; color: white; "
            "padding: 10px; border-radius: 5px;"
        )
        self.refresh_btn.setStyleSheet(
            "background-color: #E9ECEF; color: #495057; "
            "padding: 10px; border-radius: 5px; "
            "border: 1px solid #CED4DA;"
        )

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()

        self.main_layout.addLayout(button_layout)

        # ===== TABELA =====
        self.table_view = QTableView()
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table_view.horizontalHeader().setSectionsClickable(False)

        self.main_layout.addWidget(self.table_view)

        # Modelo inicial da tabela
        self._configurar_modelo_vazio()

        # Conexões dos botões
        self.add_btn.clicked.connect(self.nova_pessoa)
        self.edit_btn.clicked.connect(self.editar_pessoa)
        self.delete_btn.clicked.connect(self.excluir_pessoa)
        self.refresh_btn.clicked.connect(self.load_data)

        # Carregar dados ao abrir
        self.load_data()

    # ------------------------------------------------------------------ #
    #   CONFIGURAÇÃO / CARREGAMENTO
    # ------------------------------------------------------------------ #
    def _configurar_modelo_vazio(self):
        headers = [
            "ID",
            "Categoria",
            "Tipo Pessoa",
            "Razão Social / Nome",
            "Nome Fantasia",
            "CPF/CNPJ",
            "Bloqueado",
        ]
        model = QStandardItemModel(0, len(headers))
        model.setHorizontalHeaderLabels(headers)
        self.table_view.setModel(model)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    def load_data(self):
        filtro = self.search_input.text().strip()
        fa = self.filtros_avancados  # filtros avançados aplicados

        # Base da consulta (somente entidades permitidas)
        stmt = select(Entidade).where(
            Entidade.tipo_entidade != None
        )

        # ==========================================================
        # FILTRO AVANÇADO — CATEGORIA (agora aceita categorias múltiplas)
        # ==========================================================
        if fa["categoria"] != "Todos":
            categoria_db = fa["categoria"].upper()
            stmt = stmt.where(Entidade.tipo_entidade.ilike(f"%{categoria_db}%"))

        # ==========================================================
        # FILTRO AVANÇADO — TIPO PESSOA
        # ==========================================================
        if fa["tipo_pessoa"] != "TODOS":
            stmt = stmt.where(Entidade.tipo_pessoa == fa["tipo_pessoa"])

        # ==========================================================
        # FILTRO AVANÇADO — RAZÃO / NOME
        # ==========================================================
        if fa["razao"]:
            like = f"%{fa['razao']}%"
            stmt = stmt.where(Entidade.razao_social.ilike(like))

        # ==========================================================
        # FILTRO AVANÇADO — CPF / CNPJ
        # ==========================================================
        if fa["cpf"]:
            like = f"%{fa['cpf']}%"
            stmt = stmt.where(Entidade.cpf_cnpj.ilike(like))

        # ==========================================================
        # BUSCA GERAL (campo de pesquisa)
        # ==========================================================
        if filtro:
            like = f"%{filtro}%"
            stmt = stmt.where(
                (Entidade.razao_social.ilike(like))
                | (Entidade.nome_fantasia.ilike(like))
                | (Entidade.cpf_cnpj.ilike(like))
            )

        stmt = stmt.order_by(Entidade.id.desc())

        # ==========================================================
        # EXECUÇÃO
        # ==========================================================
        try:
            result = self.session.execute(stmt).scalars().all()
        except Exception as e:
            QMessageBox.critical(
                self, "Erro no BD",
                f"Não foi possível carregar as pessoas.\nErro: {e}"
            )
            return

        # ==========================================================
        # MONTAGEM DO MODELO DA TABELA
        # ==========================================================
        headers = [
            "ID",
            "Categoria",
            "Tipo Pessoa",
            "Razão Social / Nome",
            "Nome Fantasia",
            "CPF/CNPJ",
            "Bloqueado",
        ]

        model = QStandardItemModel(len(result), len(headers))
        model.setHorizontalHeaderLabels(headers)

        for row_idx, ent in enumerate(result):

            # ID
            item_id = QStandardItem(str(ent.id))

            # ======================================================
            # CATEGORIAS MÚLTIPLAS (Cliente, Transportadora, etc.)
            # ======================================================
            tokens = parse_categorias(ent.tipo_entidade)
            labels = [
                TIPOS_ENTIDADE_DB_TO_LABEL.get(tok, tok.title())
                for tok in tokens
            ]
            categoria_label = ", ".join(labels)
            item_categoria = QStandardItem(categoria_label)

            # Tipo de pessoa
            tipo_pessoa_label = ""
            if ent.tipo_pessoa:
                if ent.tipo_pessoa.value == "FISICA":
                    tipo_pessoa_label = "Física"
                elif ent.tipo_pessoa.value == "JURIDICA":
                    tipo_pessoa_label = "Jurídica"
            item_tipo_pessoa = QStandardItem(tipo_pessoa_label)

            # Razão, fantasia, CPF
            item_razao = QStandardItem(ent.razao_social or "")
            item_fantasia = QStandardItem(ent.nome_fantasia or "")
            item_cpf_cnpj = QStandardItem(ent.cpf_cnpj or "")

            # Bloqueado
            bloqueado_str = "Sim" if ent.esta_bloqueado else "Não"
            item_bloqueado = QStandardItem(bloqueado_str)

            row_items = [
                item_id,
                item_categoria,
                item_tipo_pessoa,
                item_razao,
                item_fantasia,
                item_cpf_cnpj,
                item_bloqueado,
            ]

            for item in row_items:
                item.setEditable(False)

            for col_idx, item in enumerate(row_items):
                model.setItem(row_idx, col_idx, item)

        self.table_view.setModel(model)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )


    # ------------------------------------------------------------------ #
    #   AUXILIAR
    # ------------------------------------------------------------------ #
    def _get_entidade_selecionada(self):
        index = self.table_view.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Seleção", "Selecione uma pessoa na tabela.")
            return None

        row = index.row()
        model = self.table_view.model()
        id_item = model.item(row, 0)

        try:
            entidade_id = int(id_item.text())
        except (TypeError, ValueError):
            QMessageBox.warning(
                self, "Erro", "Não foi possível obter o ID da pessoa selecionada."
            )
            return None

        ent = self.session.get(Entidade, entidade_id)
        if not ent:
            QMessageBox.warning(
                self, "Erro", "Registro não encontrado no banco de dados."
            )
            return None

        return ent

    # ------------------------------------------------------------------ #
    #   AÇÕES DOS BOTÕES
    # ------------------------------------------------------------------ #
    def nova_pessoa(self):
        dialog = CadastroPessoaDialog(self.session, parent=self)
        if dialog.exec():
            self.load_data()

    def editar_pessoa(self):
        ent = self._get_entidade_selecionada()
        if not ent:
            return
        dialog = CadastroPessoaDialog(self.session, entidade=ent, parent=self)
        if dialog.exec():
            self.load_data()

    def excluir_pessoa(self):
        ent = self._get_entidade_selecionada()
        if not ent:
            return

        reply = QMessageBox.question(
            self,
            "Excluir Pessoa",
            f"Tem certeza que deseja excluir '{ent.razao_social}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.session.delete(ent)
            self.session.commit()
            QMessageBox.information(self, "Sucesso", "Pessoa excluída com sucesso!")
            self.load_data()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(
                self, "Erro no BD", f"Não foi possível excluir.\nErro: {e}"
            )

    def open_filter_dialog(self):
        dialog = FiltroAvancadoPessoasDialog(self, self.filtros_avancados)
        if dialog.exec():
            self.filtros_avancados = dialog.filtros
            self.load_data()

