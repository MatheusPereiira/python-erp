# src/Views/configuracoes_view.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QWidget, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QLineEdit, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from sqlalchemy import select
from src.Models.models import Usuario, CargoPerfilEnum

# --- Diálogo auxiliar para Editar Usuário (Nome e Senha) ---
class EditarUsuarioDialog(QDialog):
    def __init__(self, usuario_alvo, session, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Editar: {usuario_alvo.login}")
        self.setFixedSize(350, 200)
        self.session = session
        self.usuario = usuario_alvo

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.input_nome = QLineEdit(self.usuario.nome)
        self.input_senha = QLineEdit(self.usuario.senha_hash) # Carrega senha atual (texto puro)
        self.input_senha.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        
        form.addRow("Nome:", self.input_nome)
        form.addRow("Senha:", self.input_senha)
        
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.salvar)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def salvar(self):
        try:
            self.usuario.nome = self.input_nome.text()
            self.usuario.senha_hash = self.input_senha.text()
            self.session.commit()
            QMessageBox.information(self, "Sucesso", "Dados atualizados!")
            self.accept()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")

# --- Tela Principal de Configurações ---
class ConfiguracoesDialog(QDialog):
    # Sinal para avisar a janela principal que é para fazer Logout
    logout_solicitado = pyqtSignal()

    def __init__(self, session, usuario_logado, parent=None):
        super().__init__(parent)
        self.session = session
        self.usuario_logado = usuario_logado
        
        self.setWindowTitle("Configurações da Conta")
        self.resize(600, 450)

        layout = QVBoxLayout(self)

        # Abas
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # ABA 1: Meu Perfil
        self.tab_perfil = QWidget()
        self.setup_tab_perfil()
        self.tabs.addTab(self.tab_perfil, "👤 Meu Perfil")

        # ABA 2: Administração (Só aparece se for Admin)
        if self.usuario_logado.perfil.cargo == CargoPerfilEnum.ADMINISTRADOR:
            self.tab_admin = QWidget()
            self.setup_tab_admin()
            self.tabs.addTab(self.tab_admin, "🛠️ Gerenciar Usuários")

    def setup_tab_perfil(self):
        layout = QVBoxLayout(self.tab_perfil)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_nome = QLabel(self.usuario_logado.nome)
        lbl_nome.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        lbl_cargo = QLabel(self.usuario_logado.perfil.cargo.value)
        lbl_cargo.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 20px;")

        btn_logout = QPushButton("🚪 Sair / Trocar de Conta")
        btn_logout.setFixedWidth(250)
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; color: white; padding: 12px;
                font-weight: bold; border-radius: 6px; font-size: 14px;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        btn_logout.clicked.connect(self.realizar_logout)

        layout.addWidget(lbl_nome, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_cargo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_logout, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def realizar_logout(self):
        confirm = QMessageBox.question(
            self, "Sair", "Deseja realmente sair do sistema?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.logout_solicitado.emit()
            self.accept()

    def setup_tab_admin(self):
        layout = QVBoxLayout(self.tab_admin)
        
        self.table_users = QTableWidget()
        self.table_users.setColumnCount(4)
        self.table_users.setHorizontalHeaderLabels(["ID", "Nome", "Login", "Perfil"])
        self.table_users.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_users.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_users.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_users.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table_users)

        btn_editar = QPushButton("✏️ Editar Usuário Selecionado")
        btn_editar.setStyleSheet("padding: 8px;")
        btn_editar.clicked.connect(self.editar_usuario_selecionado)
        layout.addWidget(btn_editar)

        self.carregar_usuarios()

    def carregar_usuarios(self):
        self.table_users.setRowCount(0)
        usuarios = self.session.execute(select(Usuario).order_by(Usuario.id)).scalars().all()
        
        for row, u in enumerate(usuarios):
            self.table_users.insertRow(row)
            self.table_users.setItem(row, 0, QTableWidgetItem(str(u.id)))
            self.table_users.setItem(row, 1, QTableWidgetItem(u.nome))
            self.table_users.setItem(row, 2, QTableWidgetItem(u.login))
            
            cargo = u.perfil.cargo.value if u.perfil else "-"
            self.table_users.setItem(row, 3, QTableWidgetItem(cargo))

    def editar_usuario_selecionado(self):
        row = self.table_users.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um usuário na tabela.")
            return
            
        id_user = int(self.table_users.item(row, 0).text())
        usuario_alvo = self.session.get(Usuario, id_user)
        
        if not usuario_alvo:
            return

        dialog = EditarUsuarioDialog(usuario_alvo, self.session, self)
        if dialog.exec():
            self.carregar_usuarios() # Recarrega a tabela para mostrar mudanças (ex: nome)