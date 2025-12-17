from fpdf import FPDF
import pandas as pd
import tempfile
import os

def remover_acentos(texto):
    """Remove acentos para compatibilidade com fontes padrão do FPDF"""
    substituicoes = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n',
        'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
        'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C', 'Ñ': 'N'
    }
    for original, substituto in substituicoes.items():
        texto = texto.replace(original, substituto)
    return texto

class FinancialReportPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Relatorio de Planejamento Financeiro', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, remover_acentos(title), 0, 1, 'L', 1)
        self.ln(4)

    def add_table(self, df):
        self.set_font('Arial', 'B', 9)
        
        # Defining columns to show
        cols = ["Mes", "Recebivel Venda", "Patrimonio Final (Nominal)"]
        
        # Header
        for col in cols:
            self.cell(60, 10, col, 1, 0, 'C')
        self.ln()
        
        # Rows
        self.set_font('Arial', '', 9)
        for _, row in df.iterrows():
            self.cell(60, 10, str(int(row['Mês'])), 1)
            self.cell(60, 10, f"R$ {row['Recebível Venda']:,.2f}", 1)
            self.cell(60, 10, f"R$ {row['Patrimônio Final (Nominal)']:,.2f}", 1)
            self.ln()

def gerar_pdf(df, fig, comentarios):
    pdf = FinancialReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- PÁGINA 1: TABELA DETALHADA ---
    pdf.add_page()
    pdf.chapter_title("1. Detalhamento do Fluxo (Período de Recebimento de Venda)")
    
    # Filtrar apenas meses com Recebível Venda > 0
    df_filtered = df[df['Recebível Venda'] > 0][["Mês", "Recebível Venda", "Patrimônio Final (Nominal)"]]
    
    # Limitar linhas para não quebrar layout se for muito grande (opcional)
    # df_filtered = df_filtered.head(50) 
    
    pdf.add_table(df_filtered)
    
    # --- PÁGINA 2: GRÁFICOS ---
    pdf.add_page()
    pdf.chapter_title("2. Evolução Visual do Patrimônio")
    
    # Salvar gráfico plotly como imagem temporária
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
        tmp_path = tmpfile.name
    
    # File is now closed, so Windows allows us to open it again for writing
    try:
        fig.write_image(tmp_path, width=800, height=600, scale=1.5)
        pdf.image(tmp_path, x=10, y=30, w=190)
    finally:
        # Remover arquivo temporário depois
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass


    # --- PÁGINA 3: COMENTÁRIOS ---
    pdf.add_page()
    pdf.chapter_title("3. Analise e Comentarios")
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 10, remover_acentos(comentarios))

    # fpdf2 retorna bytes diretamente, não precisa de encode
    return bytes(pdf.output())
