from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QComboBox, QPushButton, QMessageBox, QLabel)
from PyQt6.QtCore import Qt
from sqlalchemy import select
from src.Models.models import Usuario, Perfil

class CadastroUsuarioDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Cadastrar Novo Usuário")
        self.setFixedSize(400, 350)
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        titulo = QLabel("Novo Usuário do Sistema")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Formulário
        form_layout = QFormLayout()
        
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome completo")
        
        self.input_login = QLineEdit()
        self.input_login.setPlaceholderText("Login de acesso")
        
        self.input_senha = QLineEdit()
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_senha.setPlaceholderText("Senha")

        self.combo_perfil = QComboBox()
        self.carregar_perfis() # Preenche o combo com dados do banco

        form_layout.addRow("Nome:", self.input_nome)
        form_layout.addRow("Login:", self.input_login)
        form_layout.addRow("Senha:", self.input_senha)
        form_layout.addRow("Perfil:", self.combo_perfil)
        
        layout.addLayout(form_layout)
        layout.addStretch()

        # Botão Salvar
        self.btn_salvar = QPushButton("Salvar Usuário")
        self.btn_salvar.setStyleSheet("""
            QPushButton {
                background-color: #28a745; 
                color: white; 
                font-weight: bold; 
                padding: 10px; 
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.btn_salvar.clicked.connect(self.salvar_usuario)
        layout.addWidget(self.btn_salvar)

    def carregar_perfis(self):
        """Busca todos os perfis no banco e preenche o ComboBox"""
        try:
            perfis = self.session.execute(select(Perfil)).scalars().all()
            for p in perfis:
                # Armazena o ID do perfil no 'userData' do item (segundo argumento)
                # Exibe o nome do cargo (p.cargo.value se for enum, ou str(p.cargo))
                cargo_str = p.cargo.value if hasattr(p.cargo, 'value') else str(p.cargo)
                self.combo_perfil.addItem(cargo_str.upper(), userData=p.id)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao carregar perfis: {e}")

    def salvar_usuario(self):
        nome = self.input_nome.text().strip()
        login = self.input_login.text().strip()
        senha = self.input_senha.text().strip()
        perfil_id = self.combo_perfil.currentData() # Pega o ID oculto no combo

        if not nome or not login or not senha or not perfil_id:
            QMessageBox.warning(self, "Aviso", "Todos os campos são obrigatórios!")
            return

        # Verifica se login já existe
        usuario_existente = self.session.execute(
            select(Usuario).where(Usuario.login == login)
        ).scalar_one_or_none()

        if usuario_existente:
            QMessageBox.warning(self, "Aviso", "Este login já está em uso.")
            return

        try:
            novo_usuario = Usuario(
                nome=nome,
                login=login,
                senha_hash=senha, # Salvando sem hash conforme seu padrão atual
                perfil_id=perfil_id
            )
            self.session.add(novo_usuario)
            self.session.commit()
            
            QMessageBox.information(self, "Sucesso", f"Usuário '{login}' cadastrado com sucesso!")
            self.accept() # Fecha a janela
            
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao salvar usuário: {e}")