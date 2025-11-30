import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QToolButton, QScrollArea, QSizePolicy, QSpacerItem, QMessageBox
)
from PyQt6.QtGui import QPalette, QColor, QIcon, QFont, QPixmap
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from sqlalchemy.orm import Session

# --- IMPORTAÇÕES DO MODELO ---
from src.Models.models import engine, Usuario, CargoPerfilEnum

# --- IMPORTAÇÕES DAS VIEWS (Agora todas confirmadas) ---
# GRUPO 1 - CADASTROS E CORE
from src.Views.cadastro_produto_view import CadastroProdutosWidget
from src.Views.dashboard_produto_view import DashboardProdutosWidget
from src.Views.cadastro_pessoa_view import CadastroPessoasWidget
from src.Views.cadastro_usuario_view import CadastroUsuarioDialog
from src.Views.configuracoes_view import ConfiguracoesDialog 

# GRUPO 2 - COMERCIAL
from src.Components.Comercial.comercial import ComercialSistema
# Tratamento de erro caso falte algum arquivo específico do comercial, mas o app abre
try:
    from src.Components.Comercial.tela_venda import TelaVenda
    from src.Components.Comercial.tela_compra import TelaCompra
    from src.Views.historico_vendas_view import HistoricoVendasWidget
except ImportError:
    class TelaVenda(QWidget): pass
    class TelaCompra(QWidget): pass
    class HistoricoVendasWidget(QWidget): pass

# GRUPO 3 - FINANCEIRO E ESTOQUE
from src.Views.cadastro_financeiro_view import CadastroFinanceiroWidget
from src.Views.dashboard_financeiro_view import DashboardFinanceiroWidget
from src.Views.cadastro_estoque_view import CadastroEstoqueWidget
from src.Views.dashboard_estoque_view import DashboardEstoqueWidget


# --- CLASSE AUXILIAR: WIDGET CLICÁVEL (Para o Card do Usuário) ---
class WidgetClicavel(QWidget):
    clicked = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# --- CONFIGURAÇÃO DE TEMA (CORRIGIDO PARA LINUX) ---
def aplicar_tema_calmo(app):
    """
    Aplica o tema Fusion e força cores escuras para o texto,
    evitando bugs visuais no Linux em modo Dark.
    """
    app.setStyle("Fusion") 
    paleta = QPalette()
    
    COR_JANELA = QColor("#F9F7F3")
    COR_BASE = QColor("#FFFFFF")
    COR_TEXTO = QColor("#333333")
    COR_DESTAQUE = QColor("#007bff")
    
    paleta.setColor(QPalette.ColorRole.Window, COR_JANELA)
    paleta.setColor(QPalette.ColorRole.WindowText, COR_TEXTO)
    paleta.setColor(QPalette.ColorRole.Base, COR_BASE)
    paleta.setColor(QPalette.ColorRole.AlternateBase, COR_JANELA)
    paleta.setColor(QPalette.ColorRole.ToolTipBase, COR_TEXTO)
    paleta.setColor(QPalette.ColorRole.ToolTipText, COR_BASE)
    paleta.setColor(QPalette.ColorRole.Text, COR_TEXTO)
    paleta.setColor(QPalette.ColorRole.Button, COR_JANELA)
    paleta.setColor(QPalette.ColorRole.ButtonText, COR_TEXTO)
    paleta.setColor(QPalette.ColorRole.Link, COR_DESTAQUE)
    paleta.setColor(QPalette.ColorRole.Highlight, COR_DESTAQUE)
    paleta.setColor(QPalette.ColorRole.HighlightedText, COR_BASE)
    
    app.setPalette(paleta)

    # Força CSS global
    app.setStyleSheet("""
        QWidget { color: #333333; }
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {
            background-color: #FFFFFF; color: #333333; border: 1px solid #CCCCCC;
            border-radius: 4px; padding: 4px;
        }
        QTableWidget, QTreeWidget, QListWidget {
            background-color: #FFFFFF; color: #333333; alternate-background-color: #F9F7F3;
        }
        QHeaderView::section {
            background-color: #E0E0E0; color: #333333; padding: 4px; border: 1px solid #d0d0d0;
        }
        QLabel, QPushButton { color: #333333; }
    """)

class MainAppUnificado(QMainWindow):
    logout_realizado = pyqtSignal()

    def __init__(self, usuario_logado=None):
        super().__init__()
        self.sessao = Session(engine)
        self.usuario_atual = usuario_logado
        
        # Inicializa Lógica Comercial
        self.sistema_comercial = ComercialSistema(self.sessao)

        self.setWindowTitle("Sistema ERP Integrado")
        self.setGeometry(100, 100, 1280, 720)

        # Container Principal
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        self.layout_principal = QHBoxLayout(widget_central)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        # 1. BARRA LATERAL (Esquerda)
        self.setup_sidebar()

        # 2. ÁREA DE CONTEÚDO (Direita)
        self.widget_conteudo = QWidget()
        self.widget_conteudo.setStyleSheet("background-color: #FFFFFF;")
        self.layout_conteudo = QVBoxLayout(self.widget_conteudo)
        self.layout_conteudo.setContentsMargins(20, 20, 20, 20)
        
        self.layout_principal.addWidget(self.widget_conteudo)

        # Inicializa Widgets
        self.init_widgets()

        # Tela Inicial
        self.trocar_widget(self.widget_dashboard_produtos, "Dashboard Geral")

    def setup_sidebar(self):
        self.frame_lateral = QFrame()
        self.frame_lateral.setFixedWidth(260)
        self.frame_lateral.setStyleSheet("background-color: #F9F7F3; border-right: 1px solid #dcdcdc;")
        
        # DEFINIÇÃO CORRETA DO LAYOUT
        layout_lateral = QVBoxLayout(self.frame_lateral)
        layout_lateral.setContentsMargins(10, 20, 10, 20)
        layout_lateral.setSpacing(5)

        # --- A. CARD DO USUÁRIO ---
        if self.usuario_atual:
            self.card_usuario = WidgetClicavel()
            self.card_usuario.setFixedHeight(80)
            self.card_usuario.setCursor(Qt.CursorShape.PointingHandCursor)
            self.card_usuario.setStyleSheet("""
                WidgetClicavel { background-color: #FFFFFF; border-radius: 10px; border: 1px solid #E0E0E0; }
                WidgetClicavel:hover { background-color: #F0F0F0; border: 1px solid #B0B0B0; }
            """)
            self.card_usuario.clicked.connect(self.abrir_configuracoes)

            layout_card = QHBoxLayout(self.card_usuario)
            layout_card.setContentsMargins(10, 10, 10, 10)
            
            # 1. Pega o Nome Corretamente
            nome_display = self.usuario_atual.nome if self.usuario_atual.nome else "Usuário"
            
            # Avatar (Iniciais)
            iniciais = nome_display[:2].upper()
            lbl_avatar = QLabel(iniciais)
            lbl_avatar.setFixedSize(40, 40)
            lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_avatar.setStyleSheet("background-color: #007bff; color: white; border-radius: 20px; font-weight: bold;")
            layout_card.addWidget(lbl_avatar)

            # Texto
            layout_texto = QVBoxLayout()
            layout_texto.setSpacing(2)
            
            lbl_nome = QLabel(f"Olá, {nome_display}")
            lbl_nome.setStyleSheet("font-weight: bold; font-size: 13px; color: #333333;")
            
            # 2. Pega o Cargo Corretamente (via Perfil)
            cargo_txt = "Acesso Padrão"
            try:
                if self.usuario_atual.perfil:
                    # Pega o valor do Enum (ex: 'ADMINISTRADOR')
                    cargo_enum = self.usuario_atual.perfil.cargo
                    cargo_txt = cargo_enum.name if hasattr(cargo_enum, 'name') else str(cargo_enum)
            except Exception:
                pass
            
            lbl_cargo = QLabel(cargo_txt)
            lbl_cargo.setStyleSheet("font-size: 11px; color: #666666;")
            
            layout_texto.addWidget(lbl_nome)
            layout_texto.addWidget(lbl_cargo)
            layout_card.addLayout(layout_texto)
            # Ícone de Configuração (Engrenagem) - AJUSTADO
            lbl_config = QLabel("⚙")
            lbl_config.setFixedSize(30, 30) # Define um tamanho fixo para o "quadrado" do ícone
            lbl_config.setAlignment(Qt.AlignmentFlag.AlignCenter) # Centraliza o desenho no meio do quadrado
            # Aumentei a fonte para 22px e coloquei uma cor cinza elegante
            lbl_config.setStyleSheet("font-size: 22px; color: #6c757d; font-weight: bold;")
            
            # Adiciona ao layout alinhado verticalmente ao centro
            layout_card.addWidget(lbl_config, 0, Qt.AlignmentFlag.AlignVCenter) 

            layout_lateral.addWidget(self.card_usuario)
            layout_lateral.addSpacing(15)

        # --- SEÇÃO ADMIN (Correção Lógica) ---
        is_admin = False
        try:
            if self.usuario_atual.perfil:
                cargo = self.usuario_atual.perfil.cargo
                # Verifica se é ADMINISTRADOR (compatível com Enum ou String)
                if str(cargo) == 'ADMINISTRADOR' or getattr(cargo, 'name', '') == 'ADMINISTRADOR':
                    is_admin = True
        except Exception as e:
            print(f"Erro ao verificar permissão admin: {e}")

        if is_admin:
            self.add_section_label(layout_lateral, "ADMINISTRAÇÃO")
            
            self.botao_novo_usuario = QPushButton(" ➕  Novo Usuário")
            self.botao_novo_usuario.setCursor(Qt.CursorShape.PointingHandCursor)
            self.botao_novo_usuario.setFixedHeight(40)
            self.botao_novo_usuario.setStyleSheet("""
                QPushButton { 
                    padding-left: 15px; text-align: left; border: 1px solid #f8d7da; border-radius: 4px; 
                    background-color: #fff5f5; color: #dc3545; font-weight: bold; font-size: 13px;
                } 
                QPushButton:hover { background-color: #f8d7da; }
            """)
            self.botao_novo_usuario.clicked.connect(self.abrir_cadastro_usuario)
            layout_lateral.addWidget(self.botao_novo_usuario)
            layout_lateral.addSpacing(10)

        # --- MENUS DE NAVEGAÇÃO ---
        
        # Grupo 1
        self.add_section_label(layout_lateral, "GESTÃO & PRODUTOS")
        self.btn_dash_prod = self.create_nav_button("Dashboard Produtos", layout_lateral)
        self.btn_cad_prod = self.create_nav_button("Cadastrar Produtos", layout_lateral)
        self.btn_cad_pess = self.create_nav_button("Gerenciar Pessoas", layout_lateral)

        layout_lateral.addSpacing(10)
        
        # Grupo 2
        self.add_section_label(layout_lateral, "COMERCIAL & VENDAS")
        self.btn_venda = self.create_nav_button("Nova Venda", layout_lateral)
        self.btn_compra = self.create_nav_button("Nova Compra", layout_lateral)
        self.btn_hist = self.create_nav_button("Histórico Vendas", layout_lateral)

        layout_lateral.addSpacing(10)
        
        # Grupo 3
        self.add_section_label(layout_lateral, "FINANCEIRO & ESTOQUE")
        self.btn_dash_fin = self.create_nav_button("Dash. Financeiro", layout_lateral)
        self.btn_cad_fin = self.create_nav_button("Lançamentos Fin.", layout_lateral)
        self.btn_dash_est = self.create_nav_button("Dash. Estoque", layout_lateral)
        self.btn_cad_est = self.create_nav_button("Gerenciar Estoque", layout_lateral)

        layout_lateral.addStretch()

        # Botão Sair
        btn_sair = QPushButton("Sair do Sistema")
        btn_sair.setStyleSheet("""
            QPushButton { background-color: #ffebee; color: #c62828; border: 1px solid #ffcdd2; border-radius: 6px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #ffcdd2; }
        """)
        btn_sair.clicked.connect(self.processar_logout)
        layout_lateral.addWidget(btn_sair)

        self.layout_principal.addWidget(self.frame_lateral)

    def init_widgets(self):
        # Grupo 1
        self.widget_dashboard_produtos = DashboardProdutosWidget(self.sessao)
        self.widget_cadastro_produtos = CadastroProdutosWidget(self.sessao)
        self.widget_cadastro_pessoas = CadastroPessoasWidget(self.sessao)
        # Grupo 2
        self.widget_venda = TelaVenda(sessao=self.sessao, sistema=self.sistema_comercial)
        self.widget_compra = TelaCompra(sessao=self.sessao, sistema=self.sistema_comercial)
        self.widget_historico = HistoricoVendasWidget(self.sessao)
        # Grupo 3
        self.widget_dashboard_financeiro = DashboardFinanceiroWidget(self.sessao)
        self.widget_cadastro_financeiro = CadastroFinanceiroWidget(self.sessao)
        self.widget_dashboard_estoque = DashboardEstoqueWidget(self.sessao)
        self.widget_cadastro_estoque = CadastroEstoqueWidget(self.sessao)

        # Conexões
        self.btn_dash_prod.clicked.connect(lambda: self.trocar_widget(self.widget_dashboard_produtos, "Dashboard Produtos"))
        self.btn_cad_prod.clicked.connect(lambda: self.trocar_widget(self.widget_cadastro_produtos, "Cadastro Produtos"))
        self.btn_cad_pess.clicked.connect(lambda: self.trocar_widget(self.widget_cadastro_pessoas, "Cadastro Pessoas"))
        self.btn_venda.clicked.connect(lambda: self.trocar_widget(self.widget_venda, "Vendas"))
        self.btn_compra.clicked.connect(lambda: self.trocar_widget(self.widget_compra, "Compras"))
        self.btn_hist.clicked.connect(lambda: self.trocar_widget(self.widget_historico, "Histórico"))
        self.btn_dash_fin.clicked.connect(lambda: self.trocar_widget(self.widget_dashboard_financeiro, "Dash Financeiro"))
        self.btn_cad_fin.clicked.connect(lambda: self.trocar_widget(self.widget_cadastro_financeiro, "Cad. Financeiro"))
        self.btn_dash_est.clicked.connect(lambda: self.trocar_widget(self.widget_dashboard_estoque, "Dash Estoque"))
        self.btn_cad_est.clicked.connect(lambda: self.trocar_widget(self.widget_cadastro_estoque, "Cad. Estoque"))

    def create_nav_button(self, text, layout):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(40)
        btn.setStyleSheet("""
            QPushButton { padding-left: 15px; text-align: left; border: none; border-radius: 4px; background-color: transparent; color: #424242; font-size: 14px; } 
            QPushButton:hover { background-color: #e3f2fd; color: #004085; }
        """)
        layout.addWidget(btn)
        return btn

    def add_section_label(self, layout, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #9e9e9e; font-size: 11px; font-weight: bold; margin-top: 5px; margin-left: 5px;")
        layout.addWidget(lbl)

    def trocar_widget(self, widget, titulo):
        if self.layout_conteudo.count() > 0:
            item = self.layout_conteudo.itemAt(0)
            if item.widget():
                item.widget().setParent(None)
        if widget:
            self.layout_conteudo.addWidget(widget)
            if hasattr(widget, 'load_data'):
                try: widget.load_data()
                except: pass
        self.setWindowTitle(f"Sistema ERP Integrado - {titulo}")
        self.atualizar_estilo_botoes(widget)

    def atualizar_estilo_botoes(self, widget_atual):
        estilo_padrao = """
            QPushButton { padding-left: 15px; text-align: left; border: none; border-radius: 4px; 
            background-color: transparent; color: #424242; font-size: 14px; } 
            QPushButton:hover { background-color: #e3f2fd; color: #004085; }
        """
        estilo_ativo = """
            QPushButton { padding-left: 15px; text-align: left; border: none; border-radius: 4px;
            background-color: #cce0ff; font-weight: bold; color: #004085; font-size: 14px; }
        """
        mapa = [
            (self.btn_dash_prod, self.widget_dashboard_produtos),
            (self.btn_cad_prod, self.widget_cadastro_produtos),
            (self.btn_cad_pess, self.widget_cadastro_pessoas),
            (self.btn_venda, self.widget_venda),
            (self.btn_compra, self.widget_compra),
            (self.btn_hist, self.widget_historico),
            (self.btn_dash_fin, self.widget_dashboard_financeiro),
            (self.btn_cad_fin, self.widget_cadastro_financeiro),
            (self.btn_dash_est, self.widget_dashboard_estoque),
            (self.btn_cad_est, self.widget_cadastro_estoque),
        ]
        for btn, widget_ref in mapa:
            btn.setStyleSheet(estilo_ativo if widget_ref == widget_atual else estilo_padrao)

    def abrir_configuracoes(self):
        if not self.usuario_atual: return
        dialog = ConfiguracoesDialog(self.sessao, self.usuario_atual, parent=self)
        dialog.logout_solicitado.connect(self.processar_logout)
        dialog.exec()

    def abrir_cadastro_usuario(self):
        try:
            dialog = CadastroUsuarioDialog(self.sessao, parent=self)
            dialog.exec()
        except Exception as e:
            print(f"Erro ao abrir cadastro de usuário: {e}")
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir o cadastro: {e}")

    def processar_logout(self):
        self.logout_realizado.emit()
        self.close()