from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from sqlalchemy import select
from src.Models.models import Usuario

class LoginDialog(QDialog):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setWindowTitle("Login - SGCFE")
        self.setFixedSize(300, 320) # Aumentei um pouco a altura para caber os textos
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint) 

        layout = QVBoxLayout(self)
        layout.setSpacing(10) # Espaço entre os elementos
        layout.setContentsMargins(30, 30, 30, 30)

        # Título
        lbl_titulo = QLabel("Acesso ao Sistema")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #424242; margin-bottom: 10px;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)

        # --- USUÁRIO ---
        lbl_user = QLabel("Usuário:")
        lbl_user.setStyleSheet("font-weight: bold; color: #555;")
        layout.addWidget(lbl_user)

        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Digite seu login...")
        self.input_user.setStyleSheet("padding: 8px; border-radius: 4px; border: 1px solid #ccc;")
        layout.addWidget(self.input_user)

        # --- SENHA ---
        lbl_pass = QLabel("Senha:")
        lbl_pass.setStyleSheet("font-weight: bold; color: #555; margin-top: 5px;")
        layout.addWidget(lbl_pass)

        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Digite sua senha...")
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password) 
        self.input_senha.setStyleSheet("padding: 8px; border-radius: 4px; border: 1px solid #ccc;")
        self.input_senha.returnPressed.connect(self.verificar_login)
        layout.addWidget(self.input_senha)

        layout.addSpacing(15) # Espaço extra antes dos botões

        # Botão Entrar
        self.btn_entrar = QPushButton("Entrar")
        self.btn_entrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_entrar.clicked.connect(self.verificar_login)
        self.btn_entrar.setStyleSheet("""
            QPushButton {
                background-color: #007bff; 
                color: white; 
                font-weight: bold; 
                padding: 10px; 
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        layout.addWidget(self.btn_entrar)

        # Botão Sair
        self.btn_sair = QPushButton("Sair")
        self.btn_sair.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sair.clicked.connect(self.reject)
        self.btn_sair.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                color: #6c757d; 
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #495057;
                text-decoration: underline;
            }
        """)
        layout.addWidget(self.btn_sair)

    def verificar_login(self):
        usuario_txt = self.input_user.text().strip()
        senha_txt = self.input_senha.text().strip()

        if not usuario_txt or not senha_txt:
            QMessageBox.warning(self, "Aviso", "Preencha usuário e senha.")
            return

        try:
            # Busca usuário pelo login
            query = select(Usuario).where(Usuario.login == usuario_txt)
            usuario_db = self.session.execute(query).scalar_one_or_none()

            # Verificação simples (sem hash)
            if usuario_db and usuario_db.senha_hash == senha_txt:
                self.usuario_logado = usuario_db  # Salva o objeto usuário
                self.accept()
            else:
                QMessageBox.critical(self, "Erro", "Usuário ou senha incorretos.")
                self.input_senha.clear()
        
        except Exception as e:
            QMessageBox.critical(self, "Erro no Banco", f"Falha ao consultar usuário: {e}")