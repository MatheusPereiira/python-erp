import sys
from PyQt6.QtWidgets import QApplication, QDialog
from sqlalchemy.orm import Session

# Importa as configurações do Banco de Dados
from src.Models.models import engine 

# Importa a tela de Login
from src.Views.login_view import LoginDialog

# Importa a Janela Principal (o arquivo que acabamos de corrigir)
from main_app import MainAppUnificado, aplicar_tema_calmo

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplica o tema visual
    aplicar_tema_calmo(app)

    # LOOP PRINCIPAL: LOGIN -> APP -> LOGOUT -> LOGIN
    while True:
        # 1. Cria sessão e abre Login
        session = Session(engine)
        login_window = LoginDialog(session)
        
        # Se fechar o login sem entrar, encerra o programa
        if login_window.exec() != QDialog.DialogCode.Accepted:
            break
            
        # 2. Pega o usuário logado
        usuario = getattr(login_window, 'usuario_logado', None)
        
        # 3. Abre o Sistema Principal
        janela_principal = MainAppUnificado(usuario_logado=usuario)
        janela_principal.showMaximized()
        
        # 4. Aguarda o fechamento da janela principal
        app.exec()
        
        # O loop reinicia (volta pro login) a menos que fechemos o terminal