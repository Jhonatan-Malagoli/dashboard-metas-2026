import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Metas 2026 - Jhonatan", layout="wide", page_icon="🎯")

# --- ARQUIVOS DE DADOS ---
FILE_DATA = "meus_dados_2026.csv"
FILE_BUSINESS = "meus_negocios_2026.json"

# --- FUNÇÕES ---
def load_data():
    if not os.path.exists(FILE_DATA):
        columns = ["Data", "Categoria", "Item", "Valor", "Obs"]
        initial_data = [
            [datetime.now().strftime("%Y-%m-%d"), "Saúde", "Peso (Kg)", 145.0, "Peso Inicial"],
            [datetime.now().strftime("%Y-%m-%d"), "Finanças", "Saldo Total", 50000.0, "Saldo Inicial"],
            [datetime.now().strftime("%Y-%m-%d"), "Finanças", "Carro (Parcelas)", 12.0, "Faltam 12"]
        ]
        df = pd.DataFrame(initial_data, columns=columns)
        df.to_csv(FILE_DATA, index=False)
    return pd.read_csv(FILE_DATA)

def save_data(date, category, item, value, obs):
    df = load_data()
    # Converte valor para string se for texto (caso do diário) ou float se for número
    new_row = pd.DataFrame([[date, category, item, value, obs]], columns=["Data", "Categoria", "Item", "Valor", "Obs"])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(FILE_DATA, index=False)

def load_business_plan():
    if not os.path.exists(FILE_BUSINESS):
        return {}
    with open(FILE_BUSINESS, "r") as f:
        return json.load(f)

def save_business_plan(data_dict):
    with open(FILE_BUSINESS, "w") as f:
        json.dump(data_dict, f)

def plot_donut(valor_atual, meta_total, titulo, cor_check="green"):
    restante = max(0, meta_total - valor_atual)
    labels = ['Concluído', 'Falta']
    values = [valor_atual, restante]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker_colors=[cor_check, '#e0e0e0'], sort=False)])
    fig.update_layout(title_text=titulo, showlegend=False, margin=dict(t=40, b=0, l=0, r=0), height=220, title_font_size=18)
    percent = (valor_atual / meta_total) * 100
    fig.add_annotation(text=f"{int(percent)}%", x=0.5, y=0.5, font_size=20, showarrow=False)
    return fig

# --- SIDEBAR ---
st.sidebar.header("📝 Painel de Controle")
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
        st.success("Salvo!")
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
        st.success("Hábitos Salvos!")
        st.rerun()

# --- DADOS ---
df = load_data()
business_data = load_business_plan()

st.title("🎯 Metas Pessoais 2026")
st.markdown("---")

# --- ABAS (AGORA 6) ---
abas = ["📊 Progresso", "✅ Hábitos", "🧘 Propósito", "🙏 Gratidão", "💼 Business IA", "📋 Panorama"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# ================= TAB 1: GRÁFICOS =================
with tab1:
    st.subheader("Progresso Quantitativo")
    # Cálculos
    dias_treino = len(df[(df["Categoria"]=="Saúde") & (df["Item"]=="Treino (Dia)")])
    dias_sem_alcool = df[df["Item"] == "Zero Álcool"]["Valor"].sum()
    aportes = df[(df["Categoria"]=="Finanças") & (df["Item"]=="Aporte Financeiro (R$)")]["Valor"].sum()
    saldo_inicial = df[(df["Categoria"]=="Finanças") & (df["Item"]=="Saldo Total")]["Valor"].sum()
    saldo_atual = saldo_inicial + aportes
    h_eletrica = df[df["Item"]=="Elétrica (Horas)"]["Valor"].sum()
    h_ingles = df[df["Item"]=="Inglês (Horas)"]["Valor"].sum()
    livros = df[df["Item"]=="Livro Lido (Qtd)"]["Valor"].sum()
    
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
            df_h = df[df["Item"] == h]
            total = len(df_h)
            sucesso = df_h["Valor"].sum()
            if total > 0:
                perc = int((sucesso / total) * 100)
                st.write(f"**{h}:** {perc}%")
                st.progress(perc/100)
            else:
                st.write(f"**{h}:** --")
                st.progress(0)
    with col_b:
        st.write("### 🚗 Meta Carro")
        pagas = df[df["Item"]=="Parcela Carro Paga (Qtd)"]["Valor"].sum()
        restantes = 12 - pagas
        st.metric("Parcelas Restantes", f"{int(restantes)}", delta=f"-{int(pagas)} pagas")

# ================= TAB 3: PROPÓSITO (NOVA) =================
with tab3:
    st.header("🧘 Reafirmação de Propósito")
    st.markdown("*Responda para lembrar ao seu cérebro o valor do seu esforço.*")
    
    with st.form("form_proposito"):
        p1 = st.text_area("1. Porque dormir cedo ONTEM e acordar CEDO HOJE foi valioso?", placeholder="Benefícios que senti...")
        p2 = st.text_area("2. Porque HOJE não beber foi importante? Como isso impacta minha vida?", placeholder="Clareza mental, saúde...")
        p3 = st.text_area("3. Porque foi importante HOJE treinar e manter a dieta?", placeholder="Sensação de dever cumprido...")
        p4 = st.text_area("4. Valeu a pena estudar HOJE? O que aprendi?", placeholder="Aprendizado do dia...")
        p5 = st.text_area("5. Valeu a pena ler HOJE? O que aprendi?", placeholder="Insight do livro...")
        p6 = st.text_area("6. Porque a terapia HOJE foi importante?", placeholder="Impacto na saúde mental...")
        p7 = st.text_area("7. Porque manter a saúde financeira HOJE foi importante?", placeholder="Paz de espírito...")
        
        if st.form_submit_button("💾 Salvar Reflexão do Dia"):
            # Salva cada resposta como um item no CSV
            respostas = [p1, p2, p3, p4, p5, p6, p7]
            perguntas = ["Propósito-Sono", "Propósito-Álcool", "Propósito-Saúde", "Propósito-Estudo", "Propósito-Leitura", "Propósito-Terapia", "Propósito-Finanças"]
            
            for p, r in zip(perguntas, respostas):
                if r: # Só salva se tiver escrito algo
                    save_data(data_input, "Reflexão", p, 1, r)
            st.success("Reflexão salva! Mantenha o foco.")
            st.rerun()
            
    with st.expander("Ver Histórico de Reflexões"):
        df_ref = df[df["Categoria"] == "Reflexão"].sort_values("Data", ascending=False)
        st.dataframe(df_ref[["Data", "Item", "Obs"]], use_container_width=True)

# ================= TAB 4: GRATIDÃO (NOVA) =================
with tab4:
    st.header("🙏 Diário de Gratidão")
    st.write("A prática da gratidão reduz a ansiedade e melhora o foco no positivo.")
    
    col_g1, col_g2 = st.columns([1, 1])
    
    with col_g1:
        st.subheader("O que houve de bom hoje?")
        with st.form("form_gratidao"):
            g1 = st.text_input("1. Sou grato por uma PESSOA:", placeholder="Quem foi importante hoje?")
            g2 = st.text_input("2. Sou grato por uma OPORTUNIDADE/COISA:", placeholder="Algo que tenho ou aconteceu...")
            g3 = st.text_input("3. Uma pequena VITÓRIA de hoje:", placeholder="Algo que deu certo, mesmo que simples.")
            
            if st.form_submit_button("❤️ Enviar ao Universo"):
                if g1: save_data(data_input, "Gratidão", "Pessoa", 1, g1)
                if g2: save_data(data_input, "Gratidão", "Coisa", 1, g2)
                if g3: save_data(data_input, "Gratidão", "Vitória", 1, g3)
                st.balloons()
                st.success("Gratidão registrada!")
                st.rerun()

    with col_g2:
        st.subheader("🌸 Mural de Coisas Boas")
        df_grat = df[df["Categoria"] == "Gratidão"].sort_values("Data", ascending=False)
        
        if not df_grat.empty:
            for index, row in df_grat.head(5).iterrows():
                st.info(f"📅 **{row['Data']}** ({row['Item']}): {row['Obs']}")
        else:
            st.write("Seu mural está vazio. Comece agradecendo hoje!")

# ================= TAB 5: BUSINESS =================
with tab5:
    st.header("🚀 Incubadora de Negócios")
    with st.form("business_canvas"):
        st.subheader("1. Conceito")
        ideia = st.text_area("Ideia", value=business_data.get("ideia", ""))
        st.subheader("2. Mercado")
        mercado = st.text_area("Mercado", value=business_data.get("mercado", ""))
        st.subheader("3. MVP")
        mvp = st.text_area("MVP", value=business_data.get("mvp", ""))
        st.subheader("4. Custos")
        custos = st.text_area("Custos", value=business_data.get("custos", ""))
        st.subheader("5. Ação")
        acao = st.text_area("Ação", value=business_data.get("acao", ""))
        
        if st.form_submit_button("Salvar Plano"):
            save_business_plan({"ideia": ideia, "mercado": mercado, "mvp": mvp, "custos": custos, "acao": acao})
            st.success("Salvo!")
            st.rerun()

# ================= TAB 6: PANORAMA =================
with tab6:
    st.header("📋 Panorama Geral 2026")
    col_x, col_y, col_z = st.columns(3)
    with col_x:
        st.markdown("### 🏥 Saúde\n* 1 ano sem álcool\n* Manter dieta\n* 250 dias treino\n* Perder 45 kg\n* Terapia")
    with col_y:
        st.markdown("### 📚 Estudo\n* 200h Elétrica\n* 300h Inglês\n* 12 Livros\n* Sono (23h-06h)\n* Menos Ansiedade")
    with col_z:
        st.markdown("### 💰 Finanças\n* Contas em dia\n* Quitar carro\n* Juntar 100k\n* Negócio Online")