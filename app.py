import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from financial_logic import calcular_fluxo_mensal, converter_taxa_anual_para_mensal
from report_generator import gerar_pdf

# ==============================================================================
# 1. CONFIGURAÇÕES INICIAIS
# ==============================================================================
st.set_page_config(page_title="Simulador Fluxo de Caixa Mensal", layout="wide", page_icon="📈")

# Estilo CSS para melhorar a visualização dos números
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #0068C9;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. FUNÇÕES AUXILIARES DE UI
# ==============================================================================
def formatar_brl(valor):
    """Formata float para R$ 1.000,00"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==============================================================================
# 3. INTERFACE DO USUÁRIO
# ==============================================================================
st.title("📊 Planejamento Financeiro - Fluxo Mensal Detalhado")

with st.sidebar:
    st.header("1. Parâmetros Gerais")
    anos_projecao = st.number_input("Anos de Projeção", value=30, min_value=1, step=1)
    meses_total = anos_projecao * 12
    
    st.header("2. Patrimônio & Entradas")
    st.info("Considere aqui o dinheiro que já está na conta (incluindo os 2MM de entrada).")
    patrimonio_ini = st.number_input("Liquidez Atual (R$)", value=2000000.0, step=10000.0, format="%.2f")
    
    st.subheader("Recebíveis da Venda")
    col_v1, col_v2 = st.columns(2)
    valor_parcela = col_v1.number_input("Valor Parcela (R$)", value=373000.0)
    qtd_parcelas = col_v2.number_input("Qtd. Meses", value=42)
    corrigir_parcela = st.checkbox("Corrigir parcelas pela inflação?", value=False, help="Se marcado, o valor da parcela aumentará mensalmente conforme o IPCA.")
    
    st.subheader("Renda Recorrente")
    valor_aluguel = st.number_input("Aluguel Mensal (R$)", value=36000.0)
    
    st.header("3. Despesas & Inflação")
    custo_vida = st.number_input("Custo de Vida Mensal (Hoje)", value=80000.0)
    ipca_anual = st.number_input("IPCA Estimado (% a.a.)", value=4.5, step=0.1)
    
    st.header("4. Investimentos")
    st.caption("Taxa média de retorno da carteira (já líquida de IR idealmente)")
    rentabilidade_anual = st.number_input("Rentabilidade (% a.a.)", value=10.0, step=0.1)
    
    btn_calcular = st.button("🔄 CALCULAR CENÁRIO", type="primary", use_container_width=True)

# ==============================================================================
# 4. EXIBIÇÃO DOS RESULTADOS
# ==============================================================================
if btn_calcular:
    # Chama o motor de cálculo (agora importado)
    df, zerou, mes_z = calcular_fluxo_mensal(
        patrimonio_liquido_inicial=patrimonio_ini,
        meses_simulacao=meses_total,
        valor_parcela_imovel=valor_parcela,
        qtd_parcelas_imovel=qtd_parcelas,
        corrigir_parcela_imovel=corrigir_parcela,
        valor_aluguel_inicial=valor_aluguel,
        custo_vida_inicial=custo_vida,
        taxa_rentabilidade_anual=rentabilidade_anual,
        taxa_ipca_anual=ipca_anual
    )
    
    # --- KPIs Principais ---
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    pat_final_nominal = df.iloc[-1]['Patrimônio Final (Nominal)']
    pat_final_real = df.iloc[-1]['Patrimônio Final (Real)']
    renda_passiva_media = df['Rendimento Investimentos'].mean()
    
    col1.metric("Patrimônio Nominal (Fim)", formatar_brl(pat_final_nominal), delta="Em 30 anos" if not zerou else "Zerado")
    col2.metric("Patrimônio Real (Hoje)", formatar_brl(pat_final_real), help="Valor ajustado pelo poder de compra de hoje (deflacionado).", delta_color="off")
    col3.metric("Rendimento Médio", formatar_brl(renda_passiva_media))
    
    if zerou:
        anos_duracao = mes_z / 12
        col4.error(f"🚨 Esgota em: {anos_duracao:.1f} anos (Mês {mes_z})")
    else:
        col4.success("✅ Patrimônio Preservado")

    # --- GRÁFICOS AVANÇADOS ---
    st.subheader("📈 Evolução Visual")
    
    # Criar figura com eixo secundário
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4],
        subplot_titles=("Evolução do Patrimônio Líquido", "Fluxo de Caixa Mensal (Entradas vs Saídas)")
    )
    
    # 1. Gráfico de Área (Patrimônio)
    fig.add_trace(
        go.Scatter(
            x=df['Mês'], y=df['Patrimônio Final (Nominal)'],
            name="Patrimônio Nominal",
            mode='lines',
            fill='tozeroy',
            line=dict(color='#0068C9', width=2),
            hovertemplate='Nominal: %{y:,.2f}<extra></extra>'
        ), row=1, col=1
    )
    
    # Linha do Patrimônio Real
    fig.add_trace(
        go.Scatter(
            x=df['Mês'], y=df['Patrimônio Final (Real)'],
            name="Patrimônio Real (Poder de Compra)",
            mode='lines',
            line=dict(color='#FF8C00', width=2, dash='dot'),
            hovertemplate='Real: %{y:,.2f}<extra></extra>'
        ), row=1, col=1
    )
    
    # 2. Gráfico de Barras (Fluxo de Caixa)
    # Entradas
    fig.add_trace(
        go.Bar(
            x=df['Mês'], y=df['Total Entradas'],
            name="Entradas Totais",
            marker_color='#28a745',
            opacity=0.6,
            hovertemplate='Entradas: %{y:,.2f}<extra></extra>'
        ), row=2, col=1
    )
    
    # Saídas (Custo de Vida)
    fig.add_trace(
        go.Bar(
            x=df['Mês'], y=df['Custo de Vida'],
            name="Custo de Vida",
            marker_color='#dc3545',
            opacity=0.6,
            hovertemplate='Despesas: %{y:,.2f}<extra></extra>'
        ), row=2, col=1
    )
    
    # Linha de Saldo Líquido
    fig.add_trace(
        go.Scatter(
            x=df['Mês'], y=df['Fluxo Líquido (Operacional)'],
            name="Saldo Líquido Mensal",
            mode='lines',
            line=dict(color='black', width=1),
            hovertemplate='Liq: %{y:,.2f}<extra></extra>'
        ), row=2, col=1
    )
    
    # Linha vertical marcando o fim das parcelas
    fig.add_vline(x=qtd_parcelas, line_dash="dash", line_color="gray", annotation_text="Fim Parcelas Venda", row=2, col=1)
    fig.add_vline(x=qtd_parcelas, line_dash="dash", line_color="gray", row=1, col=1)

    fig.update_layout(height=800, hovermode="x unified", template="plotly_white", barmode='group')
    fig.update_yaxes(title_text="R$", row=1, col=1)
    fig.update_yaxes(title_text="Fluxo Mensal (R$)", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # --- TABELA DE DADOS & DOWNLOAD ---
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        st.subheader("📂 Tabela Detalhada")
    with col_d2:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name='simulacao_financeira.csv',
            mime='text/csv',
        )

    with st.expander("Ver Tabela Completa"):
        # Formatar colunas para exibição
        df_display = df.copy()
        cols_float = [c for c in df_display.columns if "Mês" not in c and "Ano" not in c]
        for c in cols_float:
            df_display[c] = df_display[c].apply(formatar_brl)
        
        st.dataframe(df_display, use_container_width=True, height=400)

    # --- RELATÓRIO PDF ---
    st.divider()
    st.subheader("📄 Relatório Competo")
    
    col_pdf1, col_pdf2 = st.columns([3, 1])
    with col_pdf1:
        comentarios = st.text_area("Adicione comentários para a página 3 do relatório:", 
                                   value="O planejamento financeiro apresenta solidez no longo prazo...", height=100)
    
    with col_pdf2:
        st.write("") # Espaçamento
        st.write("") 
        
        # Botão para GERAR o PDF (Processamento)
        if st.button("Gerar PDF 🖨️"):
            with st.spinner("Gerando PDF..."):
                st.session_state['pdf_bytes'] = gerar_pdf(df, fig, comentarios)
                
        # Botão para BAIXAR (Aparece se o PDF já foi gerado na sessão)
        if 'pdf_bytes' in st.session_state:
            st.success("PDF Gerado com Sucesso!")
            st.download_button(
                label="⬇️ Baixar PDF Agora",
                data=st.session_state['pdf_bytes'],
                file_name="relatorio_financeiro.pdf",
                mime="application/pdf",
                type="primary"
            )

else:
    st.info("👈 Configure os valores na barra lateral e clique em CALCULAR CENÁRIO.")
