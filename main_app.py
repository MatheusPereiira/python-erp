import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QToolButton, QFrame
)
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import QSize, Qt
from sqlalchemy.orm import Session

# Imports do projeto
from src.Models.models import engine
from src.Views.cadastro_produto_view import CadastroProdutosWidget
from src.Views.dashboard_produto_view import DashboardProdutosWidget
from src.Components.Comercial.comercial import ComercialSistema

# Tente importar a TelaVenda. Se der erro (arquivo não existir), cria um placeholder.
try:
    from src.Components.Comercial.tela_venda import TelaVenda
except ImportError:
    # Classe temporária caso o arquivo ainda não esteja criado
    class TelaVenda(QWidget):
        def __init__(self, sessao=None, sistema=None):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Tela de Vendas (Em construção)"))

# Substitui o bloco anterior por um que loga o erro ao importar TelaCompra
try:
    from src.Components.Comercial.tela_compra import TelaCompra
except ImportError as e:
    print(f"Erro ao importar TelaCompra: {e}")
    # Classe temporária caso o arquivo ainda não esteja criado
    class TelaCompra(QWidget):
        def __init__(self, sessao=None, sistema=None):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Tela de Compras (Em construção)"))

def aplicar_tema_calmo(app):
    """Aplica um tema visual suave à aplicação."""
    app.setStyle("Fusion") 
    paleta = QPalette()

    COR_JANELA = QColor("#F9F7F3") 
    COR_BASE = QColor("#FFFFFF") 
    COR_TEXTO = QColor("#424242") 
    COR_DESTAQUE = QColor("#007bff")
    
    paleta.setColor(QPalette.ColorRole.Window, COR_JANELA)
    paleta.setColor(QPalette.ColorRole.WindowText, COR_TEXTO)
    paleta.setColor(QPalette.ColorRole.Base, COR_BASE)
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor("#E8E5DF"))
    paleta.setColor(QPalette.ColorRole.Text, COR_TEXTO)
    paleta.setColor(QPalette.ColorRole.Button, COR_JANELA)
    paleta.setColor(QPalette.ColorRole.ButtonText, COR_TEXTO)
    paleta.setColor(QPalette.ColorRole.Link, COR_DESTAQUE)
    paleta.setColor(QPalette.ColorRole.Highlight, COR_DESTAQUE)
    paleta.setColor(QPalette.ColorRole.HighlightedText, COR_BASE)

    app.setPalette(paleta)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestão - PyQt6")
        self.setMinimumSize(QSize(1100, 700))
        
        # Inicializa Banco de Dados e Controladores
        self.sessao = Session(engine)
        self.comercial_sistema = ComercialSistema(self.sessao)

        # --- Layout Principal ---
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_horizontal = QHBoxLayout(widget_central)
        layout_horizontal.setContentsMargins(0, 0, 0, 0)
        layout_horizontal.setSpacing(0)

        # --- Barra Lateral ---
        barra_lateral = QWidget()
        barra_lateral.setFixedWidth(240)
        barra_lateral.setStyleSheet("""
            QWidget {
                background-color: #E6F0FF;
                border-right: 1px solid #c0d4f0;
            }
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                font-size: 14px;
            }
        """)
        layout_barra = QVBoxLayout(barra_lateral)
        layout_barra.setContentsMargins(0, 0, 0, 0)
        layout_barra.setSpacing(5)

        # Título do Menu
        layout_barra.addWidget(QLabel("  Módulos do Sistema"))
        
        # Divisor
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #c0d4f0;")
        layout_barra.addWidget(line)

        # =====================================================
        # MÓDULO: CADASTRO
        # =====================================================
        self.botao_nav_cadastro = self.criar_botao_menu("Cadastro")
        layout_barra.addWidget(self.botao_nav_cadastro)

        self.widget_nav_cadastro = QWidget()
        self.layout_nav_cadastro = QVBoxLayout(self.widget_nav_cadastro)
        self.layout_nav_cadastro.setContentsMargins(20, 0, 10, 10)
        self.layout_nav_cadastro.setSpacing(5)

        self.botao_cadastro_produtos = self.criar_sub_botao("Cadastro de Produtos")
        self.botao_dashboard_produtos = self.criar_sub_botao("Dashboard de Produtos")
        self.botao_tabela_precos = self.criar_sub_botao("Tabela de Preços")
        self.botao_tabela_precos.setEnabled(False)

        self.layout_nav_cadastro.addWidget(self.botao_cadastro_produtos)
        self.layout_nav_cadastro.addWidget(self.botao_dashboard_produtos)
        self.layout_nav_cadastro.addWidget(self.botao_tabela_precos)
        self.widget_nav_cadastro.setVisible(False)
        layout_barra.addWidget(self.widget_nav_cadastro)

        # =====================================================
        # MÓDULO: COMERCIAL
        # =====================================================
        self.botao_nav_comercial = self.criar_botao_menu("Comercial")
        layout_barra.addWidget(self.botao_nav_comercial)

        self.widget_nav_comercial = QWidget()
        self.layout_nav_comercial = QVBoxLayout(self.widget_nav_comercial)
        self.layout_nav_comercial.setContentsMargins(20, 0, 10, 10)
        self.layout_nav_comercial.setSpacing(5)

        self.botao_cadastro_venda = self.criar_sub_botao("Venda de Produtos")
        self.botao_cadastro_compra = self.criar_sub_botao("Entrada de Nota (Compra)")

        self.layout_nav_comercial.addWidget(self.botao_cadastro_venda)
        self.layout_nav_comercial.addWidget(self.botao_cadastro_compra)
        self.widget_nav_comercial.setVisible(False)
        layout_barra.addWidget(self.widget_nav_comercial)

        # Espaçador para empurrar tudo para cima
        layout_barra.addStretch()

        # Rodapé da barra
        self.rotulo_status = QLabel("  Status: Aguardando...")
        self.rotulo_status.setStyleSheet("font-size: 11px; color: #666;")
        layout_barra.addWidget(self.rotulo_status)

        # Adiciona a barra ao layout principal
        layout_horizontal.addWidget(barra_lateral)

        # --- Área de Conteúdo ---
        self.area_conteudo = QWidget()
        self.area_conteudo.setStyleSheet("background-color: #FFFFFF;")
        self.layout_conteudo = QVBoxLayout(self.area_conteudo)
        self.layout_conteudo.setContentsMargins(20, 20, 20, 20)
        layout_horizontal.addWidget(self.area_conteudo)

        # --- Instância das Telas ---
        # Cadastro
        self.tela_cadastro_produtos = CadastroProdutosWidget(self.sessao)
        self.tela_dashboard_produtos = DashboardProdutosWidget(self.sessao)
        
        # Comercial (Instancia dinamicamente ou aqui)
        # Passamos a sessão e o sistema comercial para a tela de venda
        self.tela_venda = TelaVenda(sessao=self.sessao, sistema=self.comercial_sistema)
        self.tela_compra = TelaCompra(sessao=self.sessao, sistema=self.comercial_sistema)  # ADICIONADO/AFIRMADO

        # --- Conexões de Eventos ---
        # Menus Expansíveis
        self.botao_nav_cadastro.clicked.connect(self.alternar_menu_cadastro)
        self.botao_nav_comercial.clicked.connect(self.alternar_menu_comercial)

        # Navegação Cadastro
        self.botao_cadastro_produtos.clicked.connect(
            lambda: self.definir_conteudo(self.tela_cadastro_produtos, "Cadastro de Produtos")
        )
        self.botao_dashboard_produtos.clicked.connect(
            lambda: self.definir_conteudo(self.tela_dashboard_produtos, "Dashboard de Produtos")
        )

        # Navegação Comercial
        self.botao_cadastro_venda.clicked.connect(
            lambda: self.definir_conteudo(self.tela_venda, "Venda de Produtos")
        )
        self.botao_cadastro_compra.clicked.connect(
            lambda: self.definir_conteudo(self.tela_compra, "Entrada de Nota (Compra)")  # MODIFICADO/AFIRMADO
        )

        # Tela inicial
        self.definir_conteudo(self.tela_dashboard_produtos, "Home")

    # --- Métodos Auxiliares de UI ---
    
    def criar_botao_menu(self, texto):
        btn = QToolButton()
        btn.setText(f" {texto}")
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        btn.setCheckable(True)
        btn.setChecked(False)
        btn.setArrowType(Qt.ArrowType.RightArrow)
        btn.setStyleSheet("""
            QToolButton {
                font-weight: bold;
                text-align: left;
                border: none;
                padding: 10px;
                background-color: transparent;
                color: #333;
            }
            QToolButton:hover {
                background-color: #d6e4ff;
                border-radius: 5px;
            }
            QToolButton:checked {
                color: #0056b3;
            }
        """)
        return btn

    def criar_sub_botao(self, texto):
        btn = QPushButton(texto)
        btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                text-align: left;
                border: none;
                border-radius: 4px;
                background-color: transparent;
                color: #555;
            }
            QPushButton:hover {
                background-color: #cce0ff;
                color: #000;
            }
        """)
        return btn

    def alternar_menu_cadastro(self):
        visivel = self.botao_nav_cadastro.isChecked()
        self.widget_nav_cadastro.setVisible(visivel)
        self.botao_nav_cadastro.setArrowType(Qt.ArrowType.DownArrow if visivel else Qt.ArrowType.RightArrow)
        # Fecha o outro menu para manter limpo
        if visivel:
            self.botao_nav_comercial.setChecked(False)
            self.alternar_menu_comercial()

    def alternar_menu_comercial(self):
        visivel = self.botao_nav_comercial.isChecked()
        self.widget_nav_comercial.setVisible(visivel)
        self.botao_nav_comercial.setArrowType(Qt.ArrowType.DownArrow if visivel else Qt.ArrowType.RightArrow)
        if visivel:
            self.botao_nav_cadastro.setChecked(False)
            self.alternar_menu_cadastro()

    def definir_conteudo(self, widget, titulo_status=""):
        # Limpa o conteúdo atual
        for i in reversed(range(self.layout_conteudo.count())):
            item = self.layout_conteudo.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        # Reseta estilos dos botões
        estilo_padrao = self.botao_cadastro_produtos.styleSheet().replace("background-color: #b3d7ff;", "background-color: transparent;")
        estilo_ativo = estilo_padrao.replace("background-color: transparent;", "background-color: #b3d7ff; font-weight: bold; color: #004085;")
        
        for btn in [self.botao_cadastro_produtos, self.botao_dashboard_produtos, self.botao_cadastro_venda, self.botao_cadastro_compra]:
            btn.setStyleSheet(estilo_padrao)

        # Adiciona o novo widget
        if widget:
            self.layout_conteudo.addWidget(widget)
            # Recarrega dados se a tela tiver esse método
            if hasattr(widget, 'load_data'):
                widget.load_data()
        else:
            self.layout_conteudo.addWidget(QLabel(f"Módulo: {titulo_status}"))

        # Atualiza Status e Estilo do Botão Ativo
        self.rotulo_status.setText(f"  Status: {titulo_status}")
        
        if widget == self.tela_cadastro_produtos:
            self.botao_cadastro_produtos.setStyleSheet(estilo_ativo)
        elif widget == self.tela_dashboard_produtos:
            self.botao_dashboard_produtos.setStyleSheet(estilo_ativo)
        elif widget == self.tela_venda:
            self.botao_cadastro_venda.setStyleSheet(estilo_ativo)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    aplicar_tema_calmo(app)
    janela = MainWindow()
    janela.show()
    sys.exit(app.exec())