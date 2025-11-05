import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.utils import ImageReader
import os

# ---------- CONFIGURAÇÕES ----------
st.set_page_config(page_title="AutoDD v1.7 — Financial Health Dashboard", layout="wide")

st.title("📊 AutoDD — Financial Health Dashboard")
st.subheader("Análise Automatizada de Due Diligence Financeira")

st.markdown("""
O **AutoDD** calcula KPIs financeiros, compara com benchmarks de mercado e gera um relatório PDF completo,
com explicações acessíveis sobre cada indicador e diagnóstico automático da empresa.
""")

# ---------- FORMULÁRIO ----------
with st.form("financial_form"):
    company_name = st.text_input("Nome da Empresa", placeholder="Ex: Alpargatas S.A.")
    
    st.markdown("### 🧾 Demonstração do Resultado (DRE)")
    receita = st.number_input("Receita Líquida", min_value=0.0, step=1000.0)
    lucro_bruto = st.number_input("Lucro Bruto", min_value=0.0, step=1000.0)
    ebitda = st.number_input("EBITDA", min_value=0.0, step=1000.0)
    lucro_liquido = st.number_input("Lucro Líquido", min_value=0.0, step=1000.0)

    st.markdown("### 💰 Balanço Patrimonial")
    ativo_total = st.number_input("Ativo Total", min_value=0.0, step=1000.0)
    passivo_total = st.number_input("Passivo Total", min_value=0.0, step=1000.0)
    patrimonio_liquido = st.number_input("Patrimônio Líquido", min_value=0.0, step=1000.0)
    divida_liquida = st.number_input("Dívida Líquida", min_value=0.0, step=1000.0)

    st.markdown("### 🔄 Estrutura de Liquidez (opcional)")
    ativo_circ = st.number_input("Ativo Circulante", min_value=0.0, step=1000.0)
    passivo_circ = st.number_input("Passivo Circulante", min_value=0.0, step=1000.0)

    submitted = st.form_submit_button("Calcular KPIs e Gerar Dashboard")

# ---------- LÓGICA ----------
if submitted:
    try:
        # KPIs calculados
        kpis = {}
        kpis['Margem Bruta'] = lucro_bruto / receita if receita else None
        kpis['Margem EBITDA'] = ebitda / receita if receita else None
        kpis['Margem Líquida'] = lucro_liquido / receita if receita else None
        kpis['ROE'] = lucro_liquido / patrimonio_liquido if patrimonio_liquido else None
        kpis['ROA'] = lucro_liquido / ativo_total if ativo_total else None
        kpis['Dívida/PL'] = divida_liquida / patrimonio_liquido if patrimonio_liquido else None
        kpis['Liquidez Corrente'] = ativo_circ / passivo_circ if ativo_circ and passivo_circ else None

        # Benchmarks
        benchmarks = {
            'Margem Bruta': 0.40,
            'Margem EBITDA': 0.20,
            'Margem Líquida': 0.10,
            'ROE': 0.15,
            'ROA': 0.07,
            'Dívida/PL': 1.0,
            'Liquidez Corrente': 1.5
        }

        # DataFrame principal
        df = pd.DataFrame.from_dict(kpis, orient='index', columns=['Valor'])
        df['Benchmark'] = df.index.map(benchmarks)
        df['Desvio (%)'] = ((df['Valor'] - df['Benchmark']) / df['Benchmark']) * 100
        df['Valor (%)'] = df['Valor'] * 100

        st.success(f"📈 Dashboard Financeiro — {company_name if company_name else 'Empresa Analisada'}")
        st.markdown("### 📊 Indicadores e Comparação com Benchmark")
        st.dataframe(df.style.format({
            "Valor": "{:.2f}",
            "Valor (%)": "{:.2f}%",
            "Benchmark": "{:.2f}",
            "Desvio (%)": "{:+.1f}%"
        }))

        # ---------- Gráfico Radar ----------
        labels = list(kpis.keys())
        values = [v if v is not None else 0 for v in kpis.values()]
        benchmark_values = [benchmarks.get(k, 0) for k in labels]
        values += values[:1]
        benchmark_values += benchmark_values[:1]
        angles = [n / float(len(labels)) * 2 * 3.14159 for n in range(len(labels))]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6,6), subplot_kw=dict(polar=True))
        ax.plot(angles, values, linewidth=2, linestyle='solid', label='Empresa')
        ax.fill(angles, values, alpha=0.25)
        ax.plot(angles, benchmark_values, linewidth=2, linestyle='dashed', color='red', label='Benchmark')
        ax.fill(angles, benchmark_values, alpha=0.1, color='red')
        ax.set_yticklabels([])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        radar_buffer = BytesIO()
        plt.savefig(radar_buffer, format='png')
        radar_buffer.seek(0)
        st.pyplot(fig)

        # ---------- Cálculo do Índice de Saúde Financeira ----------
        def normalize(v, ideal, max_val):
            if v is None:
                return 0
            return min(v / ideal, 1.0) if ideal != 0 else 0
        
        score = (
            0.25 * normalize(kpis['Margem EBITDA'], 0.2, 0.4) +
            0.2  * normalize(kpis['Margem Líquida'], 0.1, 0.2) +
            0.25 * normalize(kpis['ROE'], 0.15, 0.3) +
            0.2  * (1 - normalize(kpis['Dívida/PL'], 1, 3)) +
            0.1  * normalize(kpis['Liquidez Corrente'], 1.5, 3)
        ) * 100

        st.markdown("### 🧮 Como é calculado o Índice de Saúde Financeira")
        st.info("""
O índice é calculado com base em uma média ponderada dos principais KPIs:
- **Margem EBITDA (25%)** — mede a eficiência operacional;
- **Margem Líquida (20%)** — mede a rentabilidade final;
- **ROE (25%)** — mede o retorno ao acionista;
- **Dívida/PL (20%)** — avalia o risco financeiro;
- **Liquidez Corrente (10%)** — mede a capacidade de pagamento.

O resultado vai de 0 a 100, onde valores acima de 80 indicam excelente saúde financeira.
""")

        # Diagnóstico textual
        if score >= 80:
            diagnosis = "Excelente condição financeira. Estrutura de capital sólida e margens saudáveis."
            recommendation = "A empresa apresenta perfil atrativo para investidores institucionais e estratégicos."
        elif score >= 60:
            diagnosis = "Boa condição financeira, com pontos de atenção em margens ou alavancagem."
            recommendation = "Pode ser considerada para investimento, desde que haja monitoramento de eficiência operacional."
        elif score >= 40:
            diagnosis = "Situação moderada, com fragilidades em rentabilidade ou endividamento."
            recommendation = "Investimento requer análise aprofundada e possível reestruturação de capital."
        else:
            diagnosis = "Condição financeira fraca. Elevado risco operacional e financeiro."
            recommendation = "Não recomendada para investimento no estágio atual."

        # Comparações automáticas
        comparisons = []
        for i, row in df.iterrows():
            if pd.notnull(row['Desvio (%)']):
                if row['Desvio (%)'] > 10:
                    comparisons.append(f"{i} acima do benchmark (+{row['Desvio (%)']:.1f}%)")
                elif row['Desvio (%)'] < -10:
                    comparisons.append(f"{i} abaixo do benchmark ({row['Desvio (%)']:.1f}%)")

        insights = "• " + "\n• ".join(comparisons) if comparisons else "Os indicadores estão próximos das médias de mercado."

        # ---------- PDF ----------
        st.markdown("### 📤 Exportar Relatório em PDF")

        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        normal = styles['Normal']
        elements = []

        # LOGO
        logo_path = "/workspaces/AutoDD/logo.png"
        if os.path.exists(logo_path):
            try:
                logo_img = ImageReader(logo_path)
                logo = Image(logo_img, width=160, height=70)
                logo.hAlign = 'CENTER'
                elements.append(logo)
            except:
                elements.append(Paragraph("<b>AutoDD — Financial Health Dashboard</b>", styles['Title']))
        else:
            elements.append(Paragraph("<b>AutoDD — Financial Health Dashboard</b>", styles['Title']))

        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"<b>Empresa:</b> {company_name}", normal))
        elements.append(Paragraph(f"<b>Índice de Saúde Financeira:</b> {score:.1f}/100", normal))
        elements.append(Spacer(1, 12))

        # TABELA
        data = [["Indicador", "Valor", "Benchmark", "Desvio (%)"]]
        for i, row in df.iterrows():
            data.append([i, f"{row['Valor']:.2f}", f"{row['Benchmark']:.2f}", f"{row['Desvio (%)']:+.1f}%"])
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (1,1), (-1,-1), 'CENTER')
        ]))
        elements.append(table)
        elements.append(Spacer(1, 18))
        elements.append(Paragraph(f"<b>Diagnóstico:</b> {diagnosis}", normal))
        elements.append(Paragraph(f"<b>Recomendação:</b> {recommendation}", normal))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("<b>Comparativo com Benchmarks:</b>", normal))
        elements.append(Paragraph(insights.replace("\n", "<br/>"), normal))
        elements.append(Spacer(1, 18))
        radar_img = Image(radar_buffer, width=300, height=300)
        radar_img.hAlign = 'CENTER'
        elements.append(radar_img)
        elements.append(PageBreak())

        # SEGUNDA PÁGINA (educativa)
        leigo_text = """
<b>O que são Indicadores Financeiros (KPIs)?</b><br/>
Indicadores financeiros — conhecidos como KPIs — ajudam a entender como anda a saúde da empresa. Eles funcionam como sinais de trânsito: mostram se tudo está indo bem, se existe espaço para melhorar ou se é preciso tomar cuidado.<br/><br/>
<b>KPIs de Margem</b><br/>
Margem Bruta: Mostra quanto do dinheiro das vendas sobra para a empresa depois de pagar o custo dos produtos ou serviços. Uma margem alta é sinal de que a empresa consegue criar valor e tem espaço para lidar com despesas.<br/>
Margem Líquida: Indica quanto da receita se transforma em lucro de verdade, já descontadas todas as despesas. Se a margem líquida é alta, significa que a empresa é eficiente e lucrativa.<br/><br/>
<b>Por que isso importa?</b> Margens ajudam a analisar se a empresa está conseguindo transformar vendas em resultados. Comparar com a média do mercado (benchmark) mostra se está indo melhor ou pior do que outras empresas do mesmo ramo.<br/><br/>
<b>Receita</b><br/>
É o total de dinheiro que entra na empresa pelas vendas de produtos ou serviços.<br/><br/>
<b>Lucro</b><br/>
É o dinheiro que realmente sobra para a empresa depois de pagar todos os custos e despesas.<br/><br/>
<b>EBITDA</b><br/>
Mostra o resultado operacional da empresa, sem considerar juros, impostos e depreciação. Ajuda a entender a capacidade de gerar caixa com suas atividades principais.<br/><br/>
<b>Endividamento</b><br/>
Mede o quanto a empresa deve para bancos ou credores, avaliando se está se financiando de forma saudável.<br/><br/>
<b>Liquidez</b><br/>
Avalia a facilidade de pagar contas de curto prazo. Uma liquidez alta significa tranquilidade para honrar compromissos.<br/><br/>
<b>Retorno sobre Investimento (ROI)</b><br/>
Mostra quanto os investimentos feitos estão voltando em ganhos, indicando se valeu a pena aplicar dinheiro no negócio.<br/><br/>
<b>Comparação com o Mercado (Benchmark)</b><br/>
Comparar indicadores com a média do mercado ajuda a entender se a empresa está competitiva, acima ou abaixo dos concorrentes.
"""
        elements.append(Paragraph(leigo_text, normal))
        elements.append(Spacer(1, 24))
        elements.append(Paragraph("<b>Como é calculado o índice:</b> O índice combina 5 KPIs ponderados: Margem EBITDA (25%), Margem Líquida (20%), ROE (25%), Dívida/PL (20%) e Liquidez Corrente (10%). O resultado varia de 0 a 100 e reflete o equilíbrio entre rentabilidade, risco e liquidez.", normal))
        elements.append(Spacer(1, 24))
        elements.append(Paragraph("AutoDD — Due Diligence Automatizada v1.7", styles['Italic']))

        doc.build(elements)
        pdf_value = pdf_buffer.getvalue()

        # DOWNLOAD
        b64 = base64.b64encode(pdf_value).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="AutoDD_{company_name or "empresa"}.pdf">📄 Baixar Relatório em PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro ao gerar dashboard: {e}")
