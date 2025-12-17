import pandas as pd
import numpy as np

def converter_taxa_anual_para_mensal(taxa_anual):
    """Converte 10% a.a. em taxa mensal equivalente"""
    if taxa_anual is None:
        return 0.0
    return (1 + taxa_anual / 100)**(1/12) - 1

def calcular_fluxo_mensal(
    patrimonio_liquido_inicial,
    meses_simulacao,
    valor_parcela_imovel,
    qtd_parcelas_imovel,
    corrigir_parcela_imovel,
    valor_aluguel_inicial,
    custo_vida_inicial,
    taxa_rentabilidade_anual,
    taxa_ipca_anual
):
    # Conversão das taxas
    juros_mensal = converter_taxa_anual_para_mensal(taxa_rentabilidade_anual)
    ipca_mensal = converter_taxa_anual_para_mensal(taxa_ipca_anual)
    
    # Variáveis de Estado
    saldo_atual = patrimonio_liquido_inicial
    custo_vida_atual = custo_vida_inicial
    aluguel_atual = valor_aluguel_inicial
    
    # Parcela da venda também pode ser corrigida (ex: INCC/IGP-M simulado pelo IPCA ou outro índice)
    # Se o usuário optou por corrigir, iniciamos o valor base.
    parcela_venda_atual = valor_parcela_imovel
    
    dados_mensais = []
    patrimonio_zerou = False
    mes_zerou = None
    
    cum_inflation_factor = 1.0 # Para calcular o valor real (deflacionado)
    
    # Loop Mês a Mês
    for mes in range(1, meses_simulacao + 1):
        
        # 0. Atualizar fator de inflação acumulada (para trazer a valor presente)
        # O IPCA do mês corrige os valores para o MÊS SEGUINTE normalmente, 
        # mas aqui usamos para deflacionar o saldo atual aos preços de hoje (Mês 0).
        # Assumindo inflação constante mensal.
        cum_inflation_factor *= (1 + ipca_mensal)
        
        # 1. Entradas do Mês (Cash In)
        if mes <= qtd_parcelas_imovel:
            entrada_venda = parcela_venda_atual
        else:
            entrada_venda = 0
            
        entrada_aluguel = aluguel_atual
        total_entradas = entrada_venda + entrada_aluguel
        
        # 2. Saídas do Mês (Cash Out)
        total_saidas = custo_vida_atual
        
        # 3. Resultado Operacional (Sobra ou Falta dinheiro no mês?)
        fluxo_liquido = total_entradas - total_saidas
        
        # 4. Rendimento do Patrimônio (Juros sobre o saldo que já existia)
        rendimento_financeiro = saldo_atual * juros_mensal
        
        # 5. Atualização do Patrimônio Final
        saldo_anterior = saldo_atual
        saldo_atual = saldo_anterior + rendimento_financeiro + fluxo_liquido
        
        # Valor Real (Deflacionado) = Saldo Nominal / Acumulado Inflação
        saldo_real = saldo_atual / cum_inflation_factor
        
        # Verifica se o dinheiro acabou
        if saldo_atual < 0:
            saldo_atual = 0
            saldo_real = 0
            if not patrimonio_zerou:
                patrimonio_zerou = True
                mes_zerou = mes
        
        # 6. Gravar Dados
        dados_mensais.append({
            "Mês": mes,
            "Ano": (mes // 12),
            "Patrimônio Inicial": saldo_anterior,
            "Rendimento Investimentos": rendimento_financeiro,
            "Recebível Venda": entrada_venda,
            "Recebível Aluguel": entrada_aluguel,
            "Total Entradas": total_entradas,
            "Custo de Vida": total_saidas,
            "Fluxo Líquido (Operacional)": fluxo_liquido,
            "Patrimônio Final (Nominal)": saldo_atual,
            "Patrimônio Final (Real)": saldo_real
        })
        
        # 7. Correção Monetária para o PRÓXIMO mês
        custo_vida_atual = custo_vida_atual * (1 + ipca_mensal)
        aluguel_atual = aluguel_atual * (1 + ipca_mensal)
        
        if corrigir_parcela_imovel:
            parcela_venda_atual = parcela_venda_atual * (1 + ipca_mensal)
        
    return pd.DataFrame(dados_mensais), patrimonio_zerou, mes_zerou
