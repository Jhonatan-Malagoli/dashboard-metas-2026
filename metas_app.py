import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Metas 2026 - Jhonatan", layout="wide", page_icon="🎯")

# --- CONEXÃO COM GOOGLE SHEETS ---
def get_connection():
    # Carrega as credenciais direto dos Segredos do Streamlit
    try:
        # Tenta pegar do formato TOML padrão ou do JSON string
        if "json_key" in st.secrets["gcp_service_account"]:
            creds_dict = json.loads(st.secrets["gcp_service_account"]["json_key"])
        else:
            creds_dict = st.secrets["gcp_service_account"]
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # Abre a planilha pelo NOME (Tem que ser idêntico ao que você criou)
        return client.open("Banco de Dados - Metas 2026")
    except Exception as e:
        st.error(f"Erro ao conectar no Google Sheets: {e}")
        st.stop()

# --- FUNÇÕES DE DADOS (AGORA NA NUVEM) ---
def load_data():
    sh = get_connection()
    try:
        worksheet = sh.worksheet("Dados")
    except:
        # Se não existir, cria a aba e cabeçalhos
        worksheet = sh.add_worksheet(title="Dados", rows=1000, cols=10)
        worksheet.append_row(["Data", "Categoria", "Item", "Valor", "Obs"])
        # Adiciona dados iniciais se estiver vazia
        worksheet.append_row([datetime.now().strftime("%Y-%m-%d"), "Saúde", "Peso (Kg)", 145.0, "Peso Inicial"])
        worksheet.append_row([datetime.now().strftime("%Y-%m-%d"), "Finanças", "Saldo Total", 50000.0, "Saldo Inicial"])
        worksheet.append_row([datetime.now().strftime("%Y-%m-%d"), "Finanças", "Carro (Parcelas)", 12.0, "Faltam 12"])

    data = worksheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=["Data", "Categoria", "Item", "Valor", "Obs"])
    return pd.DataFrame(data)

def save_data(date, category, item, value, obs):
    sh = get_connection()
    worksheet = sh.worksheet("Dados")
    # Formata a data para string antes de enviar
    date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
    worksheet.append_row([date_str, category, item, value, obs])

# --- FUNÇÕES BUSINESS (NA NUVEM - ABA 2) ---
def load_business_plan():
    sh = get_connection()
    try:
        ws = sh.worksheet("Business")
    except:
        ws = sh.add_worksheet(title="Business", rows=100, cols=2)
        ws.append_row(["Chave", "Valor"])
    
    records = ws.get_all_records()
    # Converte lista de dicionários para um dicionário único
    plan = {}
    for row in records:
        plan[row["Chave"]] = row["Valor"]
    return plan

def save_business_plan(data_dict):
    sh = get_connection()
    ws = sh.worksheet("Business")
    ws.clear() # Limpa tudo para reescrever atualizado
    ws.append_row(["Chave", "Valor"]) # Repõe cabeçalho
    for k, v in data_dict.items():
        ws.append_row([k, v])

# --- FUNÇÃO GRÁFICA ---
def plot_donut(valor_atual, meta_total, titulo, cor_check="green"):
    restante = max(0, meta_total - valor_atual)
    labels = ['Concluído', 'Falta']
    values = [valor_atual, restante]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker_colors=[cor_check, '#e0e0e0'], sort=False)])
    fig.update_layout(title_text=titulo, showlegend=False, margin=dict(t=40, b=0, l=0, r=0), height=220, title_font_size=18)
    percent = (valor_atual / meta_total) * 100
    fig.add_annotation(text=f"{int(percent)}%", x=0.5, y=0.5, font_size=20, showarrow=False)
    return fig

# --- INTERFACE (SIDEBAR) ---
st.sidebar.header("📝 Painel de Controle (Nuvem)")
tipo_lancamento = st.sidebar.radio("Menu Rápido:", ["Medições (Numérico)", "Check-in Diário (Sim/Não)"])
st.sidebar.markdown("---")
data_input = st.sidebar.date_input("Data do Registro", datetime.now())

if tipo_lancamento == "Medições (Numérico)":
    categoria = st.sidebar.selectbox("Categoria", ["Saúde", "Estudo", "Finanças"])
    options = {
        "Saúde": ["Treino (Dia)", "Peso (Kg)"],
        "Estudo": ["Inglês (Horas)", "Elétrica (Horas)", "Livro Lido (Qtd)"],
        "Finanças": ["Aporte Financeiro (R$)", "Parcela Carro Paga (Qtd)"]
    }
    item = st.sidebar.selectbox("Item", options[categoria])
    valor = st.sidebar.number_input("Valor / Quantidade", min_value=0.0, step=0.5)
    obs = st.sidebar.text_input("Obs (Opcional)")
    
    if st.sidebar.button("💾 Salvar Medição"):
        save_data(data_input, categoria, item, valor, obs)
        st.success("Salvo no Google Sheets!")
        st.rerun()
    
else: 
    st.sidebar.markdown("**Rotina Diária:**")
    c1 = st.sidebar.checkbox("Zero Álcool")
    c2 = st.sidebar.checkbox("Dormiu 23h-06h")
    c3 = st.sidebar.checkbox("Manteve Dieta")
    c4 = st.sidebar.checkbox("Terapia em dia")
    c5 = st.sidebar.checkbox("Controlou Ansiedade")
    c6 = st.sidebar.checkbox("Contas em dia")
    obs = st.sidebar.text_input("Resumo rápido do dia")
    
    val_list = [c1, c2, c3, c4, c5, c6]
    item_list = ["Zero Álcool", "Sono", "Dieta", "Terapia", "Ansiedade", "Contas em Dia"]

    if st.sidebar.button("💾 Salvar Check-in"):
        for v, i in zip(val_list, item_list):
            save_data(data_input, "Hábitos", i, 1 if v else 0, obs)
        st.success("Hábitos Salvos na Nuvem!")
        st.rerun()

# --- CARREGAR DADOS ---
# Adicionei um spinner para mostrar que está carregando da internet
with st.spinner('Conectando ao Google Sheets...'):
    df = load_data()
    business_data = load_business_plan()

st.title("🎯 Metas Pessoais 2026 (Online)")
st.markdown("---")

# --- ABAS ---
abas = ["📊 Progresso", "✅ Hábitos", "🧘 Propósito", "🙏 Gratidão", "💼 Business IA", "📋 Panorama"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# ================= TAB 1: GRÁFICOS =================
with tab1:
    st.subheader("Progresso Quantitativo")
    # Tratamento de erro caso o DF esteja vazio
    if not df.empty:
        dias_treino = len(df[(df["Categoria"]=="Saúde") & (df["Item"]=="Treino (Dia)")])
        dias_sem_alcool = df[df["Item"] == "Zero Álcool"]["Valor"].sum()
        aportes = df[(df["Categoria"]=="Finanças") & (df["Item"]=="Aporte Financeiro (R$)")]["Valor"].sum()
        saldo_inicial = df[(df["Categoria"]=="Finanças") & (df["Item"]=="Saldo Total")]["Valor"].sum()
        saldo_atual = saldo_inicial + aportes
        h_eletrica = df[df["Item"]=="Elétrica (Horas)"]["Valor"].sum()
        h_ingles = df[df["Item"]=="Inglês (Horas)"]["Valor"].sum()
        livros = df[df["Item"]=="Livro Lido (Qtd)"]["Valor"].sum()
    else:
        dias_treino = dias_sem_alcool = saldo_atual = h_eletrica = h_ingles = livros = 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(plot_donut(dias_treino, 250, "💪 Dias de Treino", "blue"), use_container_width=True)
        st.plotly_chart(plot_donut(h_eletrica, 200, "⚡ Elétrica (Horas)", "orange"), use_container_width=True)
    with c2:
        st.plotly_chart(plot_donut(dias_sem_alcool, 365, "🚫🍺 Dias Sem Álcool", "green"), use_container_width=True)
        st.plotly_chart(plot_donut(h_ingles, 300, "🌎 Inglês (Horas)", "purple"), use_container_width=True)
    with c3:
        st.plotly_chart(plot_donut(saldo_atual, 100000, "💰 Juntar 100k", "gold"), use_container_width=True)
        st.plotly_chart(plot_donut(livros, 12, "📚 Livros Lidos", "teal"), use_container_width=True)

# ================= TAB 2: HÁBITOS =================
with tab2:
    st.subheader("Rotina Diária")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        habitos = ["Sono", "Dieta", "Terapia", "Ansiedade", "Contas em Dia"]
        for h in habitos:
            if not df.empty:
                df_h = df[df["Item"] == h]
                total = len(df_h)
                sucesso = df_h["Valor"].sum()
            else:
                total = sucesso = 0
            
            if total > 0:
                perc = int((sucesso / total) * 100)
                st.write(f"**{h}:** {perc}%")
                st.progress(perc/100)
            else:
                st.write(f"**{h}:** --")
                st.progress(0)
    with col_b:
        st.write("### 🚗 Meta Carro")
        if not df.empty:
            pagas = df[df["Item"]=="Parcela Carro Paga (Qtd)"]["Valor"].sum()
        else: pagas = 0
        restantes = 12 - pagas
        st.metric("Parcelas Restantes", f"{int(restantes)}", delta=f"-{int(pagas)} pagas")

# ================= TAB 3: PROPÓSITO =================
with tab3:
    st.header("🧘 Reafirmação de Propósito")
    with st.form("form_proposito"):
        p1 = st.text_area("1. Porque dormir cedo ONTEM e acordar CEDO HOJE foi valioso?")
        p2 = st.text_area("2. Porque HOJE não beber foi importante?")
        p3 = st.text_area("3. Porque foi importante HOJE treinar e manter a dieta?")
        p4 = st.text_area("4. Valeu a pena estudar HOJE? O que aprendi?")
        p5 = st.text_area("5. Valeu a pena ler HOJE? O que aprendi?")
        p6 = st.text_area("6. Porque a terapia HOJE foi importante?")
        p7 = st.text_area("7. Porque manter a saúde financeira HOJE foi importante?")
        
        if st.form_submit_button("💾 Salvar Reflexão"):
            respostas = [p1, p2, p3, p4, p5, p6, p7]
            perguntas = ["Propósito-Sono", "Propósito-Álcool", "Propósito-Saúde", "Propósito-Estudo", "Propósito-Leitura", "Propósito-Terapia", "Propósito-Finanças"]
            for p, r in zip(perguntas, respostas):
                if r: save_data(data_input, "Reflexão", p, 1, r)
            st.success("Salvo no Sheets!")
            st.rerun()
            
    with st.expander("Ver Histórico"):
        if not df.empty:
            df_ref = df[df["Categoria"] == "Reflexão"].sort_values("Data", ascending=False)
            st.dataframe(df_ref[["Data", "Item", "Obs"]], use_container_width=True)

# ================= TAB 4: GRATIDÃO =================
with tab4:
    st.header("🙏 Diário de Gratidão")
    col_g1, col_g2 = st.columns([1, 1])
    with col_g1:
        with st.form("form_gratidao"):
            g1 = st.text_input("1. Sou grato por uma PESSOA:")
            g2 = st.text_input("2. Sou grato por uma OPORTUNIDADE/COISA:")
            g3 = st.text_input("3. Uma pequena VITÓRIA de hoje:")
            if st.form_submit_button("❤️ Enviar"):
                if g1: save_data(data_input, "Gratidão", "Pessoa", 1, g1)
                if g2: save_data(data_input, "Gratidão", "Coisa", 1, g2)
                if g3: save_data(data_input, "Gratidão", "Vitória", 1, g3)
                st.balloons()
                st.success("Salvo!")
                st.rerun()
    with col_g2:
        st.subheader("🌸 Mural")
        if not df.empty:
            df_grat = df[df["Categoria"] == "Gratidão"].sort_values("Data", ascending=False)
            if not df_grat.empty:
                for i, r in df_grat.head(5).iterrows():
                    st.info(f"📅 {r['Data']} ({r['Item']}): {r['Obs']}")

# ================= TAB 5: BUSINESS =================
with tab5:
    st.header("🚀 Incubadora de Negócios")
    with st.form("business_canvas"):
        st.subheader("Canvas")
        ideia = st.text_area("Ideia", value=business_data.get("Ideia", ""))
        mercado = st.text_area("Mercado", value=business_data.get("Mercado", ""))
        mvp = st.text_area("MVP", value=business_data.get("MVP", ""))
        custos = st.text_area("Custos", value=business_data.get("Custos", ""))
        acao = st.text_area("Ação", value=business_data.get("Ação", ""))
        
        if st.form_submit_button("Salvar Plano"):
            save_business_plan({"Ideia": ideia, "Mercado": mercado, "MVP": mvp, "Custos": custos, "Ação": acao})
            st.success("Plano salvo na Nuvem!")
            st.rerun()

# ================= TAB 6: PANORAMA =================
with tab6:
    st.header("📋 Panorama Geral")
    col_x, col_y, col_z = st.columns(3)
    with col_x:
        st.markdown("### 🏥 Saúde\n* 1 ano sem álcool\n* Manter dieta\n* 250 dias treino\n* Perder 45 kg\n* Terapia")
    with col_y:
        st.markdown("### 📚 Estudo\n* 200h Elétrica\n* 300h Inglês\n* 12 Livros\n* Sono (23h-06h)\n* Menos Ansiedade")
    with col_z:
        st.markdown("### 💰 Finanças\n* Contas em dia\n* Quitar carro\n* Juntar 100k\n* Negócio Online")
