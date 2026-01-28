# src/Components/Comercial/tela_venda.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QComboBox, QMessageBox,
    QAbstractItemView, QDoubleSpinBox, QGroupBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from sqlalchemy import select
from datetime import datetime

# MODELS
from src.Models.models import (
    Item,
    PedidoVenda,
    PedidoVendaItem,
    Entidade,
    MovimentoEstoque,
    Financeiro,
    EnumStatus
)


class TelaVenda(QWidget):
    def __init__(self, sessao=None, sistema=None, parent=None):
        super().__init__(parent)

        self.sessao = sessao
        self.sistema = sistema

        self.itens_venda = []
        self.total_venda = 0.0

        self.setup_ui()
        self.carregar_dados_iniciais()

    # ======================================================
    # UI
    # ======================================================
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel("Comercial - Venda")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(titulo)

        # ---------------- DADOS DA VENDA ----------------
        grupo_dados = QGroupBox("Dados da Venda")
        layout_dados = QHBoxLayout(grupo_dados)

        layout_dados.addWidget(QLabel("Cliente:"))
        self.combo_cliente = QComboBox()
        self.combo_cliente.setMinimumWidth(300)
        layout_dados.addWidget(self.combo_cliente)

        layout_dados.addWidget(QLabel("Data:"))
        self.data_emissao = QDateEdit()
        self.data_emissao.setCalendarPopup(True)
        self.data_emissao.setDate(QDate.currentDate())
        layout_dados.addWidget(self.data_emissao)

        layout_dados.addStretch()
        layout.addWidget(grupo_dados)

        # ---------------- PRODUTOS ----------------
        grupo_prod = QGroupBox("Adicionar Produtos")
        layout_prod = QHBoxLayout(grupo_prod)

        layout_prod.addWidget(QLabel("Produto:"))
        self.combo_produto = QComboBox()
        self.combo_produto.setMinimumWidth(250)
        self.combo_produto.currentIndexChanged.connect(self.atualizar_preco_produto)
        layout_prod.addWidget(self.combo_produto)

        layout_prod.addWidget(QLabel("Qtd:"))
        self.spin_qtd = QDoubleSpinBox()
        self.spin_qtd.setDecimals(0)
        self.spin_qtd.setRange(1, 9999)
        self.spin_qtd.setValue(1)
        layout_prod.addWidget(self.spin_qtd)

        layout_prod.addWidget(QLabel("Preço:"))
        self.spin_preco = QDoubleSpinBox()
        self.spin_preco.setPrefix("R$ ")
        self.spin_preco.setRange(0, 999999)
        layout_prod.addWidget(self.spin_preco)

        btn_add = QPushButton("Adicionar")
        btn_add.clicked.connect(self.adicionar_item)
        layout_prod.addWidget(btn_add)

        layout_prod.addStretch()
        layout.addWidget(grupo_prod)

        # ---------------- TABELA ----------------
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Produto", "Qtd", "Preço", "Subtotal", "Ação"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # ---------------- RODAPÉ ----------------
        rodape = QHBoxLayout()

        self.lbl_total = QLabel("Total: R$ 0,00")
        self.lbl_total.setStyleSheet("font-size: 18px; font-weight: bold;")
        rodape.addWidget(self.lbl_total)

        rodape.addStretch()

        btn_finalizar = QPushButton("FINALIZAR VENDA")
        btn_finalizar.setMinimumHeight(40)
        btn_finalizar.clicked.connect(self.finalizar_venda)
        rodape.addWidget(btn_finalizar)

        layout.addLayout(rodape)

    # ======================================================
    # DADOS
    # ======================================================
    def carregar_dados_iniciais(self):
        try:
            # -------- CLIENTES (CORREÇÃO CRÍTICA) --------
            clientes = self.sessao.execute(
                select(Entidade).where(
                    Entidade.tipo_entidade.ilike("%CLIENTE%"),
                    Entidade.esta_bloqueado == False
                ).order_by(Entidade.razao_social)
            ).scalars().all()

            self.combo_cliente.clear()
            self.combo_cliente.addItem("Selecione o Cliente", None)

            for c in clientes:
                nome = c.nome_fantasia or c.razao_social
                self.combo_cliente.addItem(nome, c.id)

            # -------- PRODUTOS --------
            produtos = self.sessao.execute(
                select(Item).where(
                    Item.tipo_item == "PRODUTO",
                    Item.ativo == True,
                    Item.estoque > 0
                ).order_by(Item.nome)
            ).scalars().all()

            self.combo_produto.clear()
            self.combo_produto.addItem("Selecione o Produto", None)

            for p in produtos:
                self.combo_produto.addItem(p.nome, p.id)

        except Exception as e:
            print("Erro ao carregar dados da venda:", e)

    def atualizar_preco_produto(self):
        produto_id = self.combo_produto.currentData()
        if not produto_id:
            self.spin_preco.setValue(0)
            return

        produto = self.sessao.get(Item, produto_id)
        if produto:
            self.spin_preco.setValue(float(produto.preco_venda or 0))

    # ======================================================
    # ITENS
    # ======================================================
    def adicionar_item(self):
        produto_id = self.combo_produto.currentData()
        if not produto_id:
            QMessageBox.warning(self, "Aviso", "Selecione um produto.")
            return

        qtd = int(self.spin_qtd.value())
        preco = float(self.spin_preco.value())
        produto = self.sessao.get(Item, produto_id)

        subtotal = qtd * preco

        self.itens_venda.append({
            "id": produto.id,
            "nome": produto.nome,
            "quantidade": qtd,
            "preco": preco,
            "subtotal": subtotal
        })

        self.atualizar_tabela()

    def atualizar_tabela(self):
        self.table.setRowCount(len(self.itens_venda))
        total = 0

        for i, item in enumerate(self.itens_venda):
            self.table.setItem(i, 0, QTableWidgetItem(str(item["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(item["nome"]))
            self.table.setItem(i, 2, QTableWidgetItem(str(item["quantidade"])))
            self.table.setItem(i, 3, QTableWidgetItem(f"R$ {item['preco']:.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"R$ {item['subtotal']:.2f}"))

            btn = QPushButton("❌")
            btn.clicked.connect(lambda _, r=i: self.remover_item(r))
            self.table.setCellWidget(i, 5, btn)

            total += item["subtotal"]

        self.lbl_total.setText(
            f"Total: R$ {total:,.2f}".replace(".", "#").replace(",", ".").replace("#", ",")
        )

    def remover_item(self, index):
        self.itens_venda.pop(index)
        self.atualizar_tabela()

    # ======================================================
    # FINALIZAR
    # ======================================================
    def finalizar_venda(self):
        if not self.itens_venda:
            QMessageBox.warning(self, "Aviso", "Nenhum produto adicionado.")
            return

        cliente_id = self.combo_cliente.currentData()
        if not cliente_id:
            QMessageBox.warning(self, "Aviso", "Selecione um cliente.")
            return

        data = self.data_emissao.date().toPyDate()
        total = sum(i["subtotal"] for i in self.itens_venda)

        try:
            pedido = PedidoVenda(
                cliente_id=cliente_id,
                preco_total=total,
                data_emissao=data,
                status="FINALIZADO"
            )
            self.sessao.add(pedido)
            self.sessao.flush()

            for item in self.itens_venda:
                self.sessao.add(PedidoVendaItem(
                    pedido_id=pedido.id,
                    produto=item["nome"],
                    quantidade=item["quantidade"],
                    preco_unitario=item["preco"],
                    preco_total=item["subtotal"]
                ))

                prod = self.sessao.get(Item, item["id"])
                prod.estoque -= item["quantidade"]

                self.sessao.add(MovimentoEstoque(
                    item_id=prod.id,
                    quantidade=item["quantidade"],
                    tipo_movimento="saida",
                    data_ultima_mov=datetime.now(),
                    observacao=f"Venda #{pedido.id}",
                    preco_venda=item["preco"],
                    preco_compra=prod.custo_unitario or 0,
                    fornecedor_id=prod.fornecedor_id
                ))

            self.sessao.add(Financeiro(
                descricao=f"Venda #{pedido.id}",
                tipo_lancamento="R",
                origem="V",
                valor_nota=total,
                data_emissao=data,
                vencimento=data,
                status=EnumStatus.PAGA,
                pedido_venda_id=pedido.id,
                cliente_id=cliente_id
            ))

            self.sessao.commit()
            QMessageBox.information(self, "Sucesso", "Venda realizada com sucesso!")
            self.itens_venda.clear()
            self.atualizar_tabela()

        except Exception as e:
            self.sessao.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao salvar venda:\n{e}")
