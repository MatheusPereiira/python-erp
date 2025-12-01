from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect
)
# CORREÇÃO: Adicionado QPoint na importação
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QPoint
from PyQt6.QtGui import QColor, QFont
from sqlalchemy import select
from src.Models.models import Usuario
import hashlib

class LoginDialog(QDialog):
    def __init__(self, sessao):
        super().__init__()
        self.sessao = sessao
        self.usuario_logado = None
        
        self.setWindowTitle("Login - Sistema ERP")
        self.setFixedSize(400, 450)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint) 
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) 
        
        self.setup_ui()

    def setup_ui(self):
        # Layout Principal
        layout_main = QVBoxLayout(self)
        layout_main.setContentsMargins(10, 10, 10, 10)

        # Frame Central (Cartão Branco)
        self.frame_card = QFrame()
        self.frame_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        self.frame_card.setGraphicsEffect(shadow)
        
        layout_card = QVBoxLayout(self.frame_card)
        layout_card.setSpacing(15)
        layout_card.setContentsMargins(40, 40, 40, 40)

        # Título
        lbl_titulo = QLabel("BEM-VINDO")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; letter-spacing: 2px;")
        layout_card.addWidget(lbl_titulo)
        
        lbl_sub = QLabel("Faça login para continuar")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("font-size: 12px; color: #777; margin-bottom: 20px;")
        layout_card.addWidget(lbl_sub)

        # --- CAMPO USUÁRIO ---
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Usuário")
        self.input_user.setFixedHeight(45)
        self.input_user.setStyleSheet("""
            QLineEdit {
                background-color: #f5f7fa;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding-left: 15px;
                font-size: 14px;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
                background-color: #fff;
            }
        """)
        
        # Converte para maiúsculo enquanto digita
        self.input_user.textChanged.connect(lambda: self.input_user.setText(self.input_user.text().upper()))
        
        layout_card.addWidget(self.input_user)

        # --- CAMPO SENHA ---
        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Senha")
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_senha.setFixedHeight(45)
        self.input_senha.setStyleSheet(self.input_user.styleSheet())
        self.input_senha.returnPressed.connect(self.verificar_login)
        layout_card.addWidget(self.input_senha)

        # Botão Entrar
        self.btn_entrar = QPushButton("ENTRAR")
        self.btn_entrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_entrar.setFixedHeight(45)
        self.btn_entrar.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                font-size: 14px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004494;
            }
        """)
        self.btn_entrar.clicked.connect(self.verificar_login)
        layout_card.addWidget(self.btn_entrar)

        # Botão Sair
        btn_sair = QPushButton("Fechar Sistema")
        btn_sair.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_sair.setStyleSheet("background: transparent; color: #888; font-size: 11px;")
        btn_sair.clicked.connect(self.reject)
        layout_card.addWidget(btn_sair)

        layout_main.addWidget(self.frame_card)

    def verificar_login(self):
        usuario_txt = self.input_user.text().strip()
        senha_txt = self.input_senha.text().strip()

        if not usuario_txt or not senha_txt:
            self.animar_erro()
            return

        try:
            # Busca usuário no banco
            stmt = select(Usuario).where(Usuario.login == usuario_txt)
            usuario_db = self.sessao.execute(stmt).scalar_one_or_none()

            if usuario_db:
                if usuario_db.senha_hash == senha_txt:
                    self.usuario_logado = usuario_db
                    self.accept()
                else:
                    self.animar_erro() # Treme a tela
                    QMessageBox.warning(self, "Acesso Negado", "Senha incorreta.")
                    self.input_senha.clear()
            else:
                self.animar_erro() # Treme a tela
                QMessageBox.warning(self, "Acesso Negado", "Usuário não encontrado.")
        
        except Exception as e:
            print(f"Erro no login: {e}")
            QMessageBox.critical(self, "Erro", "Erro ao conectar com o banco de dados.")

    def animar_erro(self):
        """Faz a janela tremer se errar (efeito visual)"""
        animation = QPropertyAnimation(self, b"pos")
        animation.setDuration(100)
        animation.setLoopCount(3)
        pos = self.pos()
        
        # CORREÇÃO: Usando QPoint direto, sem Qt.
        animation.setKeyValueAt(0, pos)
        animation.setKeyValueAt(0.2, pos + QPoint(5, 0)) 
        animation.setKeyValueAt(0.7, pos + QPoint(-5, 0)) 
        animation.setKeyValueAt(1, pos)
        
        animation.start()