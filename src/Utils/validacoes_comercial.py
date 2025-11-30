# sistemacomercial/src/Utils/validacoes_comercial.py

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select
from PyQt6.QtWidgets import QMessageBox

class ValidadorComercial:
    def __init__(self, sessao):
        self.sessao = sessao
        self.erros = []
    
    def limpar_erros(self):
        self.erros = []
    
    def adicionar_erro(self, mensagem):
        self.erros.append(mensagem)
    
    def tem_erros(self):
        return len(self.erros) > 0
    
    def obter_erros(self):
        return self.erros
    
    def mostrar_erros(self, parent=None):
        if self.tem_erros():
            mensagem = "\n".join([f"• {erro}" for erro in self.erros])
            QMessageBox.warning(parent, "Validação de Venda", mensagem)
            return False
        return True

    def _executar_consulta_segura(self, consulta):
        """Executa uma consulta de forma segura, tratando transações abortadas"""
        try:
            return self.sessao.execute(consulta)
        except Exception as e:
            # Se houver erro de transação abortada, faz rollback e tenta novamente
            if "transaction" in str(e).lower() and "aborted" in str(e).lower():
                print("⚠️  Transação abortada detectada - fazendo rollback...")
                try:
                    self.sessao.rollback()
                    print("✅ Rollback realizado com sucesso")
                    return self.sessao.execute(consulta)
                except Exception as rollback_error:
                    print(f"❌ Erro no rollback: {rollback_error}")
                    raise rollback_error
            else:
                print(f"❌ Erro na consulta: {e}")
                raise e

    # 1. Validação de Cliente Obrigatório - CORRIGIDA
    def validar_cliente(self, cliente_id, cliente_nome):
        """Valida se o cliente foi selecionado"""
        if not cliente_id and not cliente_nome:
            self.adicionar_erro("Cliente é obrigatório para a venda")
            return False
        
        # Se tem ID, verifica se existe no banco
        if cliente_id:
            from src.Models.models import Entidade
            try:
                print(f"🔍 Validando cliente ID: {cliente_id}")
                cliente = self._executar_consulta_segura(
                    select(Entidade).where(Entidade.id == cliente_id)
                ).scalar_one_or_none()
                
                if not cliente:
                    self.adicionar_erro("Cliente não encontrado no cadastro")
                    return False
                
                if cliente.esta_bloqueado:
                    self.adicionar_erro("Cliente está bloqueado para novas vendas")
                    return False
                    
                print("✅ Cliente validado com sucesso")
                return True
                    
            except Exception as e:
                error_msg = f"Erro ao validar cliente: {str(e)}"
                print(f"❌ {error_msg}")
                self.adicionar_erro(error_msg)
                return False
        
        return True

    # 2. Validação de Dados do Vendedor - CORRIGIDA
    def validar_vendedor(self, vendedor_id, vendedor_nome):
        """Valida se o vendedor foi selecionado"""
        if not vendedor_id and not vendedor_nome:
            self.adicionar_erro("Vendedor é obrigatório para a venda")
            return False
        
        # Verifica se o vendedor existe e está ativo
        if vendedor_id:
            from src.Models.models import Usuario, Perfil
            try:
                print(f"🔍 Validando vendedor ID: {vendedor_id}")
                vendedor = self._executar_consulta_segura(
                    select(Usuario).where(Usuario.id == vendedor_id)
                ).scalar_one_or_none()
                
                if not vendedor:
                    self.adicionar_erro("Vendedor não encontrado no sistema")
                    return False
                
                # Verifica se o vendedor tem perfil de vendas
                perfil_valido = vendedor.perfil.cargo.value in ['vendas', 'administrador']
                if not perfil_valido:
                    self.adicionar_erro("Vendedor não tem permissão para realizar vendas")
                    return False
                
                print("✅ Vendedor validado com sucesso")
                return True
                    
            except Exception as e:
                error_msg = f"Erro ao validar vendedor: {str(e)}"
                print(f"❌ {error_msg}")
                self.adicionar_erro(error_msg)
                return False
        
        return True

    # 3. Validação de Limite de Crédito do Cliente - CORRIGIDA
    def validar_limite_credito(self, cliente_id, valor_total_venda):
        """Valida se o cliente tem limite de crédito disponível"""
        if not cliente_id:
            return True  # Venda para cliente balcão não precisa de limite
        
        from src.Models.models import Entidade, Financeiro
        from sqlalchemy import func
        
        try:
            print(f"💰 Validando limite de crédito para cliente: {cliente_id}")
            # Buscar limite do cliente
            LIMITE_PADRAO = Decimal('5000.00')  # Limite padrão de R$ 5.000,00
            
            # Calcular vendas em aberto do cliente
            total_em_aberto = self._executar_consulta_segura(
                select(func.coalesce(func.sum(Financeiro.valor_nota), 0))
                .where(
                    Financeiro.cliente_id == cliente_id,
                    Financeiro.status == 'ABERTA',
                    Financeiro.tipo_lancamento == 'R'  # Receber
                )
            ).scalar()
            
            limite_disponivel = LIMITE_PADRAO - total_em_aberto
            
            if valor_total_venda > limite_disponivel:
                self.adicionar_erro(
                    f"Limite de crédito insuficiente\n"
                    f"Limite disponível: R$ {limite_disponivel:,.2f}\n"
                    f"Valor da venda: R$ {valor_total_venda:,.2f}"
                )
                return False
                
            print("✅ Limite de crédito validado com sucesso")
            return True
                
        except Exception as e:
            error_msg = f"Erro ao validar limite de crédito: {str(e)}"
            print(f"❌ {error_msg}")
            self.adicionar_erro(error_msg)
            return False

    # 4. Validação de Preços Mínimos - CORRIGIDA
    def validar_preco_minimo(self, itens_venda):
        """Valida se os preços estão acima do mínimo permitido"""
        from src.Models.models import Item
        
        for item in itens_venda:
            produto_id = item.get('produto_id')
            preco_venda = item.get('preco_unitario')
            quantidade = item.get('quantidade', 1)
            
            if produto_id and preco_venda:
                try:
                    print(f"📊 Validando preço mínimo para produto: {produto_id}")
                    produto = self._executar_consulta_segura(
                        select(Item).where(Item.id == produto_id)
                    ).scalar_one_or_none()
                    
                    if produto:
                        # Calcular preço mínimo (custo + 10% de margem)
                        preco_minimo = produto.custo_unitario * Decimal('1.10')
                        
                        if preco_venda < preco_minimo:
                            self.adicionar_erro(
                                f"Preço abaixo do mínimo para {produto.nome}\n"
                                f"Preço mínimo: R$ {preco_minimo:,.2f}\n"
                                f"Preço informado: R$ {preco_venda:,.2f}"
                            )
                            return False
                    print("✅ Preço mínimo validado com sucesso")
                except Exception as e:
                    error_msg = f"Erro ao validar preço do produto: {str(e)}"
                    print(f"❌ {error_msg}")
                    self.adicionar_erro(error_msg)
                    return False
        
        return True

    # 5. Validação de Data de Validade (para produtos perecíveis) - CORRIGIDA
    def validar_validade_produtos(self, itens_venda):
        """Valida a validade de produtos perecíveis"""
        from src.Models.models import Item
        
        hoje = date.today()
        
        for item in itens_venda:
            produto_id = item.get('produto_id')
            data_validade = item.get('data_validade')
            
            if produto_id and data_validade:
                try:
                    print(f"📅 Validando validade para produto: {produto_id}")
                    produto = self._executar_consulta_segura(
                        select(Item).where(Item.id == produto_id)
                    ).scalar_one_or_none()
                    
                    if produto:
                        # Verificar se é produto perecível (baseado no tipo ou nome)
                        is_perecivel = self.is_produto_perecivel(produto)
                        
                        if is_perecivel and data_validade < hoje:
                            self.adicionar_erro(
                                f"Produto {produto.nome} está vencido\n"
                                f"Data de validade: {data_validade.strftime('%d/%m/%Y')}"
                            )
                            return False
                    print("✅ Validade validada com sucesso")
                except Exception as e:
                    error_msg = f"Erro ao validar validade do produto: {str(e)}"
                    print(f"❌ {error_msg}")
                    self.adicionar_erro(error_msg)
                    return False
        
        return True

    def is_produto_perecivel(self, produto):
        """Verifica se o produto é perecível baseado no nome ou categoria"""
        palavras_chave = ['leite', 'iogurte', 'queijo', 'carne', 'frango', 'peixe', 
                         'presunto', 'salame', 'manteiga', 'ovo', 'fruta', 'verdura',
                         'legume', 'pão', 'bolo', 'torta']
        
        nome_produto = produto.nome.lower() if produto.nome else ""
        
        return any(palavra in nome_produto for palavra in palavras_chave)

    # 6. Validação de Estoque - CORRIGIDA
    def validar_estoque(self, itens_venda):
        """Valida se há estoque suficiente para todos os itens"""
        from src.Models.models import Item
        
        for item in itens_venda:
            produto_id = item.get('produto_id')
            quantidade = item.get('quantidade', 0)
            
            if produto_id:
                try:
                    print(f"📦 Validando estoque para produto: {produto_id}")
                    produto = self._executar_consulta_segura(
                        select(Item).where(Item.id == produto_id)
                    ).scalar_one_or_none()
                    
                    if produto:
                        if produto.estoque < quantidade:
                            self.adicionar_erro(
                                f"Estoque insuficiente para {produto.nome}\n"
                                f"Estoque disponível: {produto.estoque}\n"
                                f"Quantidade solicitada: {quantidade}"
                            )
                            return False
                        
                        # Verificar estoque mínimo
                        if produto.estoque - quantidade < produto.estoque_minimo:
                            self.adicionar_erro(
                                f"Atenção: Venda deixará estoque abaixo do mínimo para {produto.nome}\n"
                                f"Estoque após venda: {produto.estoque - quantidade}\n"
                                f"Estoque mínimo: {produto.estoque_minimo}"
                            )
                            # Não bloqueia a venda, apenas alerta
                    print("✅ Estoque validado com sucesso")
                except Exception as e:
                    error_msg = f"Erro ao validar estoque do produto: {str(e)}"
                    print(f"❌ {error_msg}")
                    self.adicionar_erro(error_msg)
                    return False
        
        return True

    # 7. Validação de Dados Obrigatórios da Venda
    def validar_dados_obrigatorios(self, dados_venda):
        """Valida dados obrigatórios da venda"""
        if not dados_venda.get('itens') or len(dados_venda['itens']) == 0:
            self.adicionar_erro("A venda deve conter pelo menos um item")
            return False
        
        if not dados_venda.get('valor_total') or dados_venda['valor_total'] <= 0:
            self.adicionar_erro("Valor total da venda deve ser maior que zero")
            return False
        
        # Validação de desconto máximo
        subtotal = dados_venda.get('subtotal', 0)
        desconto_valor = dados_venda.get('desconto_valor', 0)
        
        if desconto_valor > subtotal:
            self.adicionar_erro("Desconto não pode ser maior que o subtotal da venda")
            return False
        
        return True

    # 8. Validação Completa Integrada - CORRIGIDA
    def validar_venda_completa(self, dados_venda, parent=None):
        """Executa todas as validações da venda"""
        print("🚀 Iniciando validação completa da venda...")
        self.limpar_erros()
        
        # Dados básicos
        cliente_id = dados_venda.get('cliente_id')
        cliente_nome = dados_venda.get('cliente_nome')
        vendedor_id = dados_venda.get('vendedor_id')
        vendedor_nome = dados_venda.get('vendedor_nome')
        valor_total = dados_venda.get('valor_total', 0)
        itens = dados_venda.get('itens', [])
        
        try:
            # Executar validações
            validacoes = [
                lambda: self.validar_dados_obrigatorios(dados_venda),
                lambda: self.validar_cliente(cliente_id, cliente_nome),
                lambda: self.validar_vendedor(vendedor_id, vendedor_nome),
                lambda: self.validar_limite_credito(cliente_id, valor_total),
                lambda: self.validar_estoque(itens),
                lambda: self.validar_preco_minimo(itens),
                lambda: self.validar_validade_produtos(itens)
            ]
            
            for i, validacao in enumerate(validacoes):
                print(f"🔍 Executando validação {i+1}...")
                if not validacao():
                    print(f"❌ Validação {i+1} falhou")
                    break  # Para na primeira validação que falhar
                else:
                    print(f"✅ Validação {i+1} passou")
                    
        except Exception as e:
            error_msg = f"Erro inesperado durante a validação: {str(e)}"
            print(f"❌ {error_msg}")
            self.adicionar_erro(error_msg)
        
        print(f"🎯 Validação concluída. Erros encontrados: {len(self.erros)}")
        return self.mostrar_erros(parent)

# Classe para representar itens da venda
class ItemVenda:
    def __init__(self, produto_id, produto_nome, quantidade, preco_unitario, data_validade=None):
        self.produto_id = produto_id
        self.produto_nome = produto_nome
        self.quantidade = quantidade
        self.preco_unitario = preco_unitario
        self.data_validade = data_validade
    
    def to_dict(self):
        return {
            'produto_id': self.produto_id,
            'produto_nome': self.produto_nome,
            'quantidade': self.quantidade,
            'preco_unitario': self.preco_unitario,
            'data_validade': self.data_validade
        }