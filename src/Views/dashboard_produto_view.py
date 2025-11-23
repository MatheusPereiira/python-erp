from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QGroupBox, QFormLayout, QLineEdit, QRadioButton, QScrollArea, QGridLayout,
    QPushButton
)
from PyQt6.QtGui import QDoubleValidator, QIntValidator
from sqlalchemy import select, func
from decimal import Decimal

from src.Models.models import Item, Fornecedor
from src.Utils.correcaoDeValores import Converter_decimal, Converter_inteiro


class DashboardProdutosWidget(QWidget):
    def __init__(self, sessao):
        super().__init__()
        self.sessao = sessao
        layout_principal = QVBoxLayout(self)

        self.rotulo_titulo = QLabel("Dashboard de Produtos")
        self.rotulo_titulo.setStyleSheet("font-size: 20pt; font-weight: bold; margin-bottom: 10px; color: #424242;")
        layout_principal.addWidget(self.rotulo_titulo)

        self.filtros_atuais = {'ativo': None, 'preco_min': None, 'preco_max': None, 'estoque_max': None}

        grupo_filtros = QGroupBox("Filtros do Dashboard")
        grupo_filtros.setStyleSheet("QGroupBox { border: 1px solid #ccc; margin-top: 10px; padding: 10px; }")

        layout_vbox = QVBoxLayout()
        layout_form = QFormLayout()

        validador_decimal = QDoubleValidator(0.0, 9999999.99, 2)
        validador_inteiro = QIntValidator(0, 9999999)

        grupo_status = QGroupBox("Status do Produto")
        layout_status = QHBoxLayout(grupo_status)
        self.radio_ativo = QRadioButton("Ativo")
        self.radio_inativo = QRadioButton("Inativo")
        self.radio_todos = QRadioButton("Todos")
        self.radio_todos.setChecked(True)
        layout_status.addWidget(self.radio_ativo)
        layout_status.addWidget(self.radio_inativo)
        layout_status.addWidget(self.radio_todos)
        layout_form.addRow(grupo_status)

        self.campo_preco_min = QLineEdit()
        self.campo_preco_min.setValidator(validador_decimal)
        self.campo_preco_min.setPlaceholderText("R$ 0,00")
        layout_form.addRow("Preço Mínimo:", self.campo_preco_min)

        self.campo_preco_max = QLineEdit()
        self.campo_preco_max.setValidator(validador_decimal)
        self.campo_preco_max.setPlaceholderText("R$ 0,00")
        layout_form.addRow("Preço Máximo:", self.campo_preco_max)

        self.campo_estoque_max = QLineEdit()
        self.campo_estoque_max.setValidator(validador_inteiro)
        self.campo_estoque_max.setPlaceholderText("0")
        layout_form.addRow("Estoque Máximo:", self.campo_estoque_max)

        layout_acoes = QHBoxLayout()
        self.botao_limpar = QPushButton("🧹 Limpar Filtros")
        self.botao_aplicar = QPushButton("⚙️ Aplicar Filtros")
        self.botao_aplicar.setFixedWidth(200)
        self.botao_aplicar.setStyleSheet("background-color: #E0E0E0; color: #424242; padding: 10px; border-radius: 5px; border: 1px solid #CCCCCC;")

        layout_acoes.addWidget(self.botao_limpar)
        layout_acoes.addStretch()
        layout_acoes.addWidget(self.botao_aplicar)

        layout_vbox.addLayout(layout_form)
        layout_vbox.addLayout(layout_acoes)
        grupo_filtros.setLayout(layout_vbox)

        layout_principal.addWidget(grupo_filtros)

        area_scroll = QScrollArea()
        area_scroll.setWidgetResizable(True)
        widget_conteudo = QWidget()
        self.layout_kpi = QGridLayout(widget_conteudo)

        area_scroll.setWidget(widget_conteudo)
        layout_principal.addWidget(area_scroll)

        self.rotulos_kpi = {}
        self.configurar_cartoes_kpi()

        # Conexões dos botões
        self.botao_limpar.clicked.connect(self.limpar_filtros)
        self.botao_aplicar.clicked.connect(self.atualizar_filtros)
        self.radio_ativo.clicked.connect(self.atualizar_filtros)
        self.radio_inativo.clicked.connect(self.atualizar_filtros)
        self.radio_todos.clicked.connect(self.atualizar_filtros)

        self.carregar_dados()

    #  FUNÇÕES PRINCIPAIS

    def limpar_filtros(self):
        self.radio_todos.setChecked(True)
        self.campo_preco_min.clear()
        self.campo_preco_max.clear()
        self.campo_estoque_max.clear()
        self.atualizar_filtros()

    def atualizar_filtros(self):
        if self.radio_ativo.isChecked():
            self.filtros_atuais['ativo'] = True
        elif self.radio_inativo.isChecked():
            self.filtros_atuais['ativo'] = False
        else:
            self.filtros_atuais['ativo'] = None

        self.filtros_atuais['preco_min'] = Converter_decimal(self.campo_preco_min.text()) or None
        self.filtros_atuais['preco_max'] = Converter_decimal(self.campo_preco_max.text()) or None
        self.filtros_atuais['estoque_max'] = Converter_inteiro(self.campo_estoque_max.text()) or None

        self.carregar_dados()

    def criar_cartao_kpi(self, titulo, icone, cor):
        grupo = QGroupBox()
        grupo.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {cor};
                border-radius: 8px;
                margin-top: 10px;
                background-color: #FFFFFF;
            }}
        """)

        layout = QVBoxLayout(grupo)
        rotulo_titulo = QLabel(f"<b>{icone} {titulo}</b>")
        rotulo_titulo.setStyleSheet("font-size: 10pt; color: #555;")

        rotulo_valor = QLabel("Carregando...")
        rotulo_valor.setStyleSheet(f"font-size: 22pt; font-weight: bold; color: {cor}; margin-top: 5px;")

        layout.addWidget(rotulo_titulo)
        layout.addWidget(rotulo_valor)
        layout.addStretch()

        return grupo, rotulo_valor

    def configurar_cartoes_kpi(self):
        cor_neutra = "#6c757d"
        cor_positiva = "#20c997"
        cor_financeira = "#495057"
        cor_alerta = "#dc3545"
        cor_media = "#007bff"

        cartao1, self.rotulos_kpi['total'] = self.criar_cartao_kpi("Total de Produtos", "📦", cor_neutra)
        self.layout_kpi.addWidget(cartao1, 0, 0)

        cartao2, self.rotulos_kpi['ativos'] = self.criar_cartao_kpi("Produtos Ativos", "✅", cor_positiva)
        self.layout_kpi.addWidget(cartao2, 0, 1)

        cartao3, self.rotulos_kpi['inativos'] = self.criar_cartao_kpi("Produtos Inativos", "🛑", cor_neutra)
        self.layout_kpi.addWidget(cartao3, 0, 2)

        cartao4, self.rotulos_kpi['valor_estoque'] = self.criar_cartao_kpi("Valor Total do Estoque", "💰", cor_financeira)
        self.layout_kpi.addWidget(cartao4, 1, 0)

        cartao5, self.rotulos_kpi['estoque_critico'] = self.criar_cartao_kpi("Itens com Estoque Crítico", "🚨", cor_alerta)
        self.layout_kpi.addWidget(cartao5, 1, 1)

        cartao6, self.rotulos_kpi['preco_medio'] = self.criar_cartao_kpi("Preço Médio de Venda", "⚖️", cor_media)
        self.layout_kpi.addWidget(cartao6, 1, 2)

    def carregar_dados(self):
        try:
            filtro_ativo = self.filtros_atuais.get('ativo')
            preco_min = self.filtros_atuais.get('preco_min')
            preco_max = self.filtros_atuais.get('preco_max')
            estoque_max = self.filtros_atuais.get('estoque_max')

            consulta_base = select(Item).join(Fornecedor, Item.fornecedor_id == Fornecedor.id, isouter=True)

            if filtro_ativo is not None:
                consulta_base = consulta_base.where(Item.ativo == filtro_ativo)
            if preco_min is not None:
                consulta_base = consulta_base.where(Item.preco_venda >= preco_min)
            if preco_max is not None:
                consulta_base = consulta_base.where(Item.preco_venda <= preco_max)
            if estoque_max is not None:
                consulta_base = consulta_base.where(Item.estoque <= estoque_max)

            subquery = consulta_base.subquery()

            total_produtos = self.sessao.execute(select(func.count()).select_from(subquery)).scalar_one()

            produtos_ativos = self.sessao.execute(
                select(func.count()).select_from(subquery).where(subquery.c.ativo == True)
            ).scalar_one()

            produtos_inativos = self.sessao.execute(
                select(func.count()).select_from(subquery).where(subquery.c.ativo == False)
            ).scalar_one()

            valor_estoque = self.sessao.execute(
                select(func.sum(subquery.c.custo_unitario * subquery.c.estoque))
            ).scalar_one_or_none() or Decimal(0)

            estoque_critico = self.sessao.execute(
                select(func.count()).select_from(subquery).where(subquery.c.estoque < subquery.c.estoque_minimo)
            ).scalar_one()

            preco_medio = self.sessao.execute(
                select(func.avg(subquery.c.preco_venda))
            ).scalar_one_or_none() or Decimal(0)

            # Atualiza rótulos
            self.rotulos_kpi['total'].setText(f"{total_produtos:,}".replace(",", "."))
            self.rotulos_kpi['ativos'].setText(f"{produtos_ativos:,}".replace(",", "."))
            self.rotulos_kpi['inativos'].setText(f"{produtos_inativos:,}".replace(",", "."))
            self.rotulos_kpi['estoque_critico'].setText(f"{estoque_critico:,}".replace(",", "."))

            self.rotulos_kpi['valor_estoque'].setText(f"R$ {valor_estoque:,.2f}".replace(".", "#").replace(",", ".").replace("#", ","))
            self.rotulos_kpi['preco_medio'].setText(f"R$ {preco_medio:,.2f}".replace(".", "#").replace(",", ".").replace("#", ","))

        except Exception as e:
            QMessageBox.critical(self, "Erro no Dashboard", f"Não foi possível carregar os dados.\nErro: {e}")
            for label in self.rotulos_kpi.values():
                label.setText("ERRO")
