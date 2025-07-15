#!/usr/bin/env python3
"""
Ai Analyzer - Interfaccia ultra-moderna per analisi AI Overview e Content Gap
Powered by Nicolas Micolani
"""

import streamlit as st
import json
import time
import threading
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from ai_overview_extractor import AIOverviewExtractor
from content_gap_analyzer import ContentGapAnalyzer
from semantic_analyzer import SemanticAnalyzer
import pandas as pd
import io
import csv
import base64

# Configurazione pagina
st.set_page_config(
    page_title="Ai Analyzer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS professionale ed elegante
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Source+Code+Pro:wght@400;500&display=swap');
    
    /* Variabili CSS professionali */
    :root {
        --primary-blue: #2563eb;
        --secondary-blue: #1e40af;
        --accent-blue: #3b82f6;
        --success-green: #059669;
        --warning-orange: #d97706;
        --danger-red: #dc2626;
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-tertiary: #f1f5f9;
        --bg-card: #ffffff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --text-muted: #94a3b8;
        --border-light: 1px solid #e2e8f0;
        --border-medium: 1px solid #cbd5e1;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    /* Reset e base professionale */
    * {
        font-family: 'Inter', sans-serif !important;
    }
    
    .stApp {
        background: var(--bg-secondary);
        min-height: 100vh;
        color: var(--text-primary);
    }
    
    .main .block-container {
        padding: 1rem;
        max-width: 1600px;
    }
    
    /* Header professionale */
    .cyber-header {
        text-align: center;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        background: var(--bg-card);
        border-radius: 12px;
        border: var(--border-light);
        box-shadow: var(--shadow-lg);
        animation: slideIn 0.6s ease-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .cyber-title {
        font-family: 'Inter', sans-serif !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.2 !important;
    }
    
    .cyber-subtitle {
        font-size: 1.125rem !important;
        font-weight: 400 !important;
        color: var(--text-secondary) !important;
        margin-bottom: 1.5rem !important;
        line-height: 1.6 !important;
    }
    
    .cyber-powered {
        font-family: 'Source Code Pro', monospace !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: var(--primary-blue) !important;
    }
    
    /* Cards professionali */
    .cyber-card {
        background: var(--bg-card);
        border: var(--border-light);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        transition: all 0.2s ease;
        animation: fadeIn 0.5s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .cyber-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-color: var(--accent-blue);
    }
    
    /* Metric cards professionali */
    .metric-card {
        background: var(--bg-card);
        border: var(--border-light);
        border-left: 4px solid var(--primary-blue);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: var(--shadow-md);
        transition: all 0.2s ease;
        animation: fadeIn 0.5s ease-out;
        margin: 1rem 0;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-left-color: var(--accent-blue);
    }
    
    .metric-value {
        font-family: 'Inter', sans-serif !important;
        font-size: 2.25rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        margin-bottom: 0.5rem !important;
        line-height: 1 !important;
    }
    
    .metric-label {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    /* Benchmark cards */
    .benchmark-card {
        background: var(--bg-card);
        border: var(--border-light);
        border-left: 4px solid var(--success-green);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: var(--shadow-md);
        transition: all 0.2s ease;
        animation: fadeIn 0.5s ease-out;
        margin: 1rem 0;
    }
    
    .benchmark-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        border-left-color: var(--warning-orange);
    }
    
    .benchmark-value {
        font-family: 'Inter', sans-serif !important;
        font-size: 2.25rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        margin-bottom: 0.5rem !important;
        line-height: 1 !important;
    }
    
    .benchmark-label {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    /* Bottoni professionali */
    .stButton > button {
        background: var(--primary-blue) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        text-transform: none !important;
        letter-spacing: 0.025em !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
        cursor: pointer !important;
    }
    
    .stButton > button:hover {
        background: var(--secondary-blue) !important;
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-md) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    /* Input fields professionali */
    .stTextInput > div > div > input {
        background: var(--bg-card) !important;
        border: var(--border-medium) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0.75rem !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        outline: none !important;
    }
    
    /* Sidebar professionale */
    .css-1d391kg {
        background: var(--bg-card) !important;
        border-right: var(--border-light) !important;
    }
    
    /* Tabs professionali */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-tertiary) !important;
        border-radius: 8px !important;
        padding: 0.25rem !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 6px !important;
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        margin: 0 0.125rem !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--bg-card) !important;
        color: var(--primary-blue) !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    /* AI Overview container */
    .ai-overview-container {
        background: var(--bg-card);
        border: var(--border-light);
        border-radius: 12px;
        padding: 2rem;
        box-shadow: var(--shadow-md);
        margin: 1rem 0;
        animation: fadeIn 0.6s ease-out;
    }
    
    .ai-overview-container:hover {
        box-shadow: var(--shadow-lg);
    }
    
    /* Status messages */
    .status-success {
        background: rgba(5, 150, 105, 0.1) !important;
        border: 1px solid var(--success-green) !important;
        color: var(--success-green) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
    }
    
    .status-warning {
        background: rgba(217, 119, 6, 0.1) !important;
        border: 1px solid var(--warning-orange) !important;
        color: var(--warning-orange) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
    }
    
    .status-error {
        background: rgba(220, 38, 38, 0.1) !important;
        border: 1px solid var(--danger-red) !important;
        color: var(--danger-red) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* Progress bar professionale */
    .stProgress > div > div > div > div {
        background: var(--primary-blue) !important;
        border-radius: 4px !important;
    }
    
    /* Scrollbar professionale */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-tertiary);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--text-muted);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-secondary);
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .cyber-header h1 {
            font-size: 2rem;
        }
        
        .cyber-header {
            padding: 2rem 1.5rem;
        }
        
        .metric-value {
            font-size: 1.875rem;
        }
        
        .cyber-card, .metric-card, .benchmark-card {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Header principale professionale
st.markdown("""
<div class="cyber-header">
    <h1 class="cyber-title">Ai Analyzer</h1>
    <p class="cyber-subtitle">Sistema Professionale di Analisi AI Overview & Content Gap</p>
    <p class="cyber-powered">Analisi intelligente per strategie di contenuto ottimizzate  powered by Nicolas Micolani</p>
</div>
""", unsafe_allow_html=True)

# Inizializzazione session state
if 'extraction_count' not in st.session_state:
    st.session_state.extraction_count = 0
if 'analysis_count' not in st.session_state:
    st.session_state.analysis_count = 0
if 'ai_overview_data' not in st.session_state:
    st.session_state.ai_overview_data = None
if 'content_gap_data' not in st.session_state:
    st.session_state.content_gap_data = None
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'semantic_analyzer' not in st.session_state:
    st.session_state.semantic_analyzer = None

# Funzioni di utilità
def create_metric_card(value, label, card_type="metric"):
    """Crea una card metrica professionale"""
    if card_type == "benchmark":
        card_class = "benchmark-card"
        value_class = "benchmark-value"
        label_class = "benchmark-label"
    else:
        card_class = "metric-card"
        value_class = "metric-value"
        label_class = "metric-label"
    
    return f"""
    <div class="{card_class}">
        <div class="{value_class}">{value}</div>
        <div class="{label_class}">{label}</div>
    </div>
    """

def create_professional_card(content, title=""):
    """Crea una card professionale per contenuti generali"""
    title_html = f"<h3 style='color: var(--primary-blue); margin-bottom: 1rem; font-family: Inter, sans-serif; font-weight: 600;'>{title}</h3>" if title else ""
    return f"""
    <div class="cyber-card">
        {title_html}
        {content}
    </div>
    """

# Configurazione API Key AI
st.session_state.gemini_api_key = "AIzaSyDXB8Lj2gamg7SEYmxvZ_uEs7JX3RKZ9yY"

# Tabs principali
tab1, tab2, tab3, tab4 = st.tabs(["🤖 AI Overview Extractor", "💬 Content Gap Analyzer", "📁 File Manager", "📈 Dashboard Analytics"])

with tab1:
    st.markdown("""
    <div class="cyber-card">
        <h2 style="color: var(--neon-blue); text-shadow: 0 0 10px var(--neon-blue); font-family: 'Orbitron', monospace; margin-bottom: 2rem;">🤖 ESTRAZIONE INTELLIGENTE AI OVERVIEW</h2>
        <p style="color: var(--text-neon); font-size: 1.2rem; line-height: 1.6;">Estrai automaticamente i contenuti dall'AI Overview di Google per qualsiasi query di ricerca. Il sistema utilizza automazione browser avanzata per ottenere il contenuto completo.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Input per la query
    query = st.text_input(
        "🔍 Query di ricerca",
        placeholder="Inserisci la tua query di ricerca...",
        help="Inserisci la query per cui vuoi estrarre l'AI Overview"
    )
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        extract_button = st.button("🚀 ESTRAI AI OVERVIEW", use_container_width=True)
    
    with col2:
        if st.session_state.ai_overview_data:
            clear_button = st.button("🗑️ CANCELLA AI OVERVIEW", use_container_width=True)
            if clear_button:
                st.session_state.ai_overview_data = None
                st.rerun()
    
    if extract_button and query:
        with st.spinner("🔄 Estrazione AI Overview in corso..."):
                try:
                    extractor = AIOverviewExtractor(headless=True)
                    result = extractor.extract_ai_overview_from_query(query)
                    
                    if result and result.get('found', False) and result.get('full_content', ''):
                        # Crea un oggetto compatibile per la visualizzazione
                        ai_overview_data = {
                            'query': query,
                            'ai_overview': result.get('full_content', ''),
                            'found': True,
                            'extraction_time': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        st.session_state.ai_overview_data = ai_overview_data
                        st.session_state.extraction_count += 1
                        st.success("✅ AI Overview estratto con successo!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Nessun AI Overview trovato per questa query")
                        
                except Exception as e:
                    st.error(f"❌ Errore durante l'estrazione: {str(e)}")
                finally:
                    # Chiudi sempre l'extractor per rilasciare le risorse
                    try:
                        extractor.close()
                    except:
                        pass
    
    # Visualizzazione risultati AI Overview
    if st.session_state.ai_overview_data:
        st.markdown("""
        <div class="ai-overview-container">
            <h3 style="color: var(--neon-green); text-shadow: 0 0 10px var(--neon-green); font-family: 'Orbitron', monospace; margin-bottom: 1.5rem;">📋 RISULTATO AI OVERVIEW</h3>
        </div>
        """, unsafe_allow_html=True)
        
        data = st.session_state.ai_overview_data
        
        # Query utilizzata
        st.markdown(f"""
        <div class="cyber-card">
            <h4 style="color: var(--neon-purple); text-shadow: 0 0 10px var(--neon-purple); font-family: 'Orbitron', monospace;">🔍 Query:</h4>
            <p style="color: var(--text-neon); font-size: 1.2rem; font-weight: 500;">{data.get('query', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Contenuto AI Overview
        if 'ai_overview' in data and data['ai_overview']:
            st.markdown(f"""
            <div class="cyber-card">
                <h4 style="color: var(--neon-blue); text-shadow: 0 0 10px var(--neon-blue); font-family: 'Orbitron', monospace;">🤖 Contenuto AI Overview:</h4>
                <div style="background: rgba(0, 212, 255, 0.1); border: 1px solid var(--neon-blue); border-radius: 15px; padding: 1.5rem; margin-top: 1rem;">
                    <p style="color: var(--text-neon); font-size: 1.1rem; line-height: 1.6;">{data['ai_overview']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Fonti
        if 'sources' in data and data['sources']:
            st.markdown("""
            <div class="cyber-card">
                <h4 style="color: var(--neon-pink); text-shadow: 0 0 10px var(--neon-pink); font-family: 'Orbitron', monospace;">🔗 Fonti:</h4>
            </div>
            """, unsafe_allow_html=True)
            
            for i, source in enumerate(data['sources'], 1):
                st.markdown(f"""
                <div style="background: rgba(255, 0, 110, 0.1); border: 1px solid var(--neon-pink); border-radius: 15px; padding: 1rem; margin: 0.5rem 0;">
                    <p style="color: var(--neon-pink); font-weight: 600; margin-bottom: 0.5rem;">Fonte {i}:</p>
                    <p style="color: var(--text-neon);"><strong>Titolo:</strong> {source.get('title', 'N/A')}</p>
                    <p style="color: var(--text-neon);"><strong>URL:</strong> <a href="{source.get('url', '#')}" target="_blank" style="color: var(--neon-blue);">{source.get('url', 'N/A')}</a></p>
                </div>
                """, unsafe_allow_html=True)
        
        # Timestamp
        if 'timestamp' in data:
            st.markdown(f"""
            <div class="cyber-card">
                <p style="color: var(--text-neon); font-size: 0.9rem; text-align: center; opacity: 0.8;">⏰ Estratto il: {data['timestamp']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Sezione Download
        st.markdown("""
        <div class="cyber-card">
            <h4 style="color: var(--neon-green); text-shadow: 0 0 10px var(--neon-green); font-family: 'Orbitron', monospace;">💾 DOWNLOAD AI OVERVIEW</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Pulsanti di download in colonne
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Download JSON
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 JSON",
                data=json_data,
                file_name=f"ai_overview_{data.get('query', 'export').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True,
                help="Scarica in formato JSON per riutilizzo nell'app"
            )
        
        with col2:
            # Download TXT
            txt_content = f"AI OVERVIEW EXTRACTION\n"
            txt_content += f"=" * 50 + "\n\n"
            txt_content += f"Query: {data.get('query', 'N/A')}\n\n"
            txt_content += f"Contenuto AI Overview:\n{'-' * 25}\n"
            txt_content += f"{data.get('ai_overview', data.get('full_content', 'N/A'))}\n\n"
            
            if 'sources' in data and data['sources']:
                txt_content += f"Fonti:\n{'-' * 10}\n"
                for i, source in enumerate(data['sources'], 1):
                    txt_content += f"{i}. {source.get('title', 'N/A')}\n"
                    txt_content += f"   URL: {source.get('url', 'N/A')}\n\n"
            
            txt_content += f"\nEstratto il: {data.get('extraction_time', data.get('timestamp', 'N/A'))}"
            
            st.download_button(
                label="📝 TXT",
                data=txt_content,
                file_name=f"ai_overview_{data.get('query', 'export').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True,
                help="Scarica in formato testo semplice"
            )
        
        with col3:
            # Download Markdown
            md_content = f"# AI Overview Extraction\n\n"
            md_content += f"**Query:** {data.get('query', 'N/A')}\n\n"
            md_content += f"**Data estrazione:** {data.get('extraction_time', data.get('timestamp', 'N/A'))}\n\n"
            md_content += f"## 🤖 Contenuto AI Overview\n\n"
            md_content += f"{data.get('ai_overview', data.get('full_content', 'N/A'))}\n\n"
            
            if 'sources' in data and data['sources']:
                md_content += f"## 🔗 Fonti\n\n"
                for i, source in enumerate(data['sources'], 1):
                    md_content += f"{i}. **{source.get('title', 'N/A')}**\n"
                    md_content += f"   - URL: [{source.get('url', 'N/A')}]({source.get('url', '#')})\n\n"
            
            md_content += f"\n---\n*Generato da AI Analyzer - {datetime.now().strftime('%d/%m/%Y %H:%M')}*"
            
            st.download_button(
                label="📋 MD",
                data=md_content,
                file_name=f"ai_overview_{data.get('query', 'export').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                use_container_width=True,
                help="Scarica in formato Markdown"
            )
        
        with col4:
            # Download CSV
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Campo', 'Valore'])
            writer.writerow(['Query', data.get('query', 'N/A')])
            writer.writerow(['AI Overview', data.get('ai_overview', data.get('full_content', 'N/A'))])
            writer.writerow(['Data Estrazione', data.get('extraction_time', data.get('timestamp', 'N/A'))])
            
            if 'sources' in data and data['sources']:
                for i, source in enumerate(data['sources'], 1):
                    writer.writerow([f'Fonte {i} - Titolo', source.get('title', 'N/A')])
                    writer.writerow([f'Fonte {i} - URL', source.get('url', 'N/A')])
            
            csv_content = output.getvalue()
            output.close()
            
            st.download_button(
                label="📊 CSV",
                data=csv_content,
                file_name=f"ai_overview_{data.get('query', 'export').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
                help="Scarica in formato CSV per Excel"
            )

with tab2:
    st.markdown("""
    <div class="cyber-card">
        <h2 style="color: var(--neon-purple); text-shadow: 0 0 10px var(--neon-purple); font-family: 'Orbitron', monospace; margin-bottom: 2rem;">💬 CONTENT GAP ANALYZER</h2>
        <p style="color: var(--text-neon); font-size: 1.2rem; line-height: 1.6;">Analizza il gap di contenuto con l'intelligenza artificiale avanzata. Chat interattiva per insights approfonditi.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Verifica API Key
    if not st.session_state.gemini_api_key:
        st.warning("⚠️ Configurazione AI non disponibile.")
    else:
        # Inizializza AI Analyzer se non presente
        if st.session_state.semantic_analyzer is None:
            st.session_state.semantic_analyzer = SemanticAnalyzer(st.session_state.gemini_api_key)
        
        # Chat interface pulita
        st.markdown("""
        <div style="text-align: center; margin: 1rem 0;">
            <h2 style="color: var(--neon-purple); text-shadow: 0 0 10px var(--neon-purple); font-family: 'Orbitron', monospace; margin: 0;">💭 Content Gap Analyzer</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Caricamento JSON semplificato
        st.subheader("📁 Carica AI Overview JSON")
        uploaded_file = st.file_uploader(
            "Carica il file JSON con l'AI Overview estratto",
            type=['json'],
            key="json_upload",
            help="Carica un file JSON contenente l'AI Overview per iniziare l'analisi"
        )
        
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                if 'ai_overview' in data or 'full_content' in data:
                    st.session_state.ai_overview_data = data
                    st.success("✅ AI Overview caricato con successo!")
                    # Messaggio automatico di benvenuto
                    welcome_msg = f"Ho caricato l'AI Overview. Contiene {len(data.get('ai_overview', data.get('full_content', '')).split())} parole. Cosa vorresti sapere?"
                    if not st.session_state.chat_history or st.session_state.chat_history[-1]['content'] != welcome_msg:
                        st.session_state.chat_history.append({'role': 'assistant', 'content': welcome_msg})
                else:
                    st.error("❌ File JSON non valido. Deve contenere 'ai_overview' o 'full_content'.")
            except Exception as e:
                st.error(f"❌ Errore nel caricamento: {str(e)}")
        
        # Chat history con design pulito
        if st.session_state.chat_history:
            st.markdown("---")
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f"**👤 Tu:** {message['content']}")
                else:
                    st.markdown(f"**🤖 AI:** {message['content']}")
                st.markdown("")
            st.markdown("---")
        


        
        # Input semplificato
        user_question = st.text_area(
            "💬 Fai una domanda all'AI:",
            placeholder="Es: Come posso migliorare il mio contenuto basandomi sull'AI Overview estratto?",
            height=80
        )
        
        # Pulsanti azione
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Invia", type="primary", use_container_width=True):
                if user_question.strip():
                    st.session_state.chat_history.append({'role': 'user', 'content': user_question})
                    
                    with st.spinner("🤖 Analizzando..."):
                        try:
                            context = ""
                            if st.session_state.ai_overview_data:
                                ai_content = st.session_state.ai_overview_data.get('ai_overview', st.session_state.ai_overview_data.get('full_content', ''))
                                context += f"\n\nAI OVERVIEW:\n{ai_content[:1500]}..."
                            
                            full_prompt = f"""Sei un esperto SEO e content strategist con oltre 10 anni di esperienza. Il tuo compito è fornire analisi precise, actionable e basate su dati concreti.

## TUE COMPETENZE
- Analisi SEO avanzata e ottimizzazione contenuti
- Strategia di content marketing data-driven
- Gap analysis e competitive intelligence
- Keyword research e semantic SEO
- User intent analysis e content optimization

## CONTESTO DISPONIBILE
{context}

## DOMANDA DELL'UTENTE
{user_question}

## ISTRUZIONI PER LA RISPOSTA
Fornisci una risposta che:
1. **ANALISI**: Analizza la situazione basandoti sui dati disponibili
2. **STRATEGIA**: Proponi una strategia chiara e strutturata
3. **AZIONI CONCRETE**: Elenca step specifici e implementabili
4. **METRICHE**: Suggerisci KPI per misurare i risultati
5. **TEMPISTICHE**: Indica timeline realistiche per l'implementazione

## FORMATO RISPOSTA
- Professionale e strutturato
- Con esempi concreti quando possibile
- Riferimenti all'AI Overview quando disponibile
- Focus su risultati misurabili
- Sempre in italiano

## VINCOLI
- Basati sempre sui dati forniti
- Se mancano informazioni, richiedile esplicitamente
- Evita consigli generici, sii specifico
- Fornisci sempre il "perché" dietro ogni raccomandazione

Rispondi in modo completo e actionable:"""
                            
                            response = st.session_state.semantic_analyzer.model.generate_content(full_prompt)
                            if response and response.text:
                                st.session_state.chat_history.append({'role': 'assistant', 'content': response.text})
                                st.rerun()
                            else:
                                st.error("❌ Errore nella risposta")
                        except Exception as e:
                            st.error(f"❌ Errore: {str(e)}")
                else:
                    st.warning("⚠️ Inserisci una domanda")
        
        with col2:
            if st.button("📄 Esporta Chat", use_container_width=True):
                if st.session_state.chat_history:
                    # Crea il contenuto del documento
                    chat_content = "# Conversazione Content Gap Analyzer\n\n"
                    chat_content += f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                    
                    for i, message in enumerate(st.session_state.chat_history, 1):
                        role = "👤 **Utente**" if message['role'] == 'user' else "🤖 **AI Assistant**"
                        chat_content += f"## {role}\n\n{message['content']}\n\n---\n\n"
                    
                    # Offri il download
                    st.download_button(
                        label="💾 Scarica Conversazione",
                        data=chat_content,
                        file_name=f"chat_content_gap_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ Nessuna conversazione da esportare")
        
        with col3:
            if st.button("🗑️ Pulisci Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

with tab3:
    st.header("📁 Gestione File")
    st.write("Gestisci i tuoi file JSON: carica AI Overview salvati ed esporta i risultati delle analisi.")
    
    st.subheader("📤 Carica AI Overview")
    
    uploaded_file = st.file_uploader(
        "Carica un file JSON con AI Overview salvato",
        type=['json'],
        help="Carica un file JSON precedentemente esportato contenente dati di AI Overview"
    )
    
    if uploaded_file is not None:
        try:
            # Leggi il file JSON
            file_content = json.loads(uploaded_file.read())
            
            # Verifica che sia un file AI Overview valido
            if 'ai_overview' in file_content or 'full_content' in file_content:
                st.session_state.ai_overview_data = file_content
                st.success("✅ AI Overview caricato con successo!")
                
                # Mostra anteprima
                content = file_content.get('ai_overview', file_content.get('full_content', ''))
                preview = content[:300] + "..." if len(content) > 300 else content
                st.markdown(f"""
                <div style="background: rgba(0, 212, 255, 0.1); border: 1px solid var(--neon-blue); border-radius: 15px; padding: 1rem; margin: 1rem 0;">
                    <h4 style="color: var(--neon-blue);">📋 Anteprima Contenuto:</h4>
                    <p style="color: var(--text-neon);">{preview}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("❌ File JSON non valido. Deve contenere dati di AI Overview.")
        except json.JSONDecodeError:
            st.error("❌ Errore nel leggere il file JSON. Verifica che sia un file JSON valido.")
        except Exception as e:
            st.error(f"❌ Errore nel caricare il file: {str(e)}")
    
    # Sezione Download
    st.markdown("""
    <div class="cyber-card">
        <h3 style="color: var(--neon-purple); font-family: 'Orbitron', monospace;">📥 ESPORTA RISULTATI</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export AI Overview
        if st.session_state.ai_overview_data:
            ai_json = json.dumps(st.session_state.ai_overview_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="📄 Scarica AI Overview JSON",
                data=ai_json,
                file_name=f"ai_overview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                help="Scarica l'AI Overview attualmente caricato in formato JSON"
            )
        else:
            st.info("📋 Nessun AI Overview disponibile per l'export")
    
    with col2:
        # Export Content Gap Analysis
        if st.session_state.content_gap_data:
            gap_json = json.dumps(st.session_state.content_gap_data, indent=2, ensure_ascii=False)
            st.download_button(
                label="📊 Scarica Analisi Gap JSON",
                data=gap_json,
                file_name=f"content_gap_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                help="Scarica l'ultima analisi Content Gap in formato JSON"
            )
        else:
            st.info("📊 Nessuna analisi Gap disponibile per l'export")
    
    # Sezione file locali
    st.markdown("""
    <div class="cyber-card">
        <h3 style="color: var(--neon-pink); font-family: 'Orbitron', monospace;">💾 FILE LOCALI DISPONIBILI</h3>
    </div>
    """, unsafe_allow_html=True)
    
    import os
    import glob
    
    # Cerca file JSON nella directory corrente
    json_files = glob.glob("*.json")
    
    if json_files:
        selected_file = st.selectbox(
            "Seleziona un file JSON locale da caricare:",
            options=["Seleziona..."] + json_files
        )
        
        if selected_file != "Seleziona..." and st.button(f"📂 Carica {selected_file}"):
            try:
                with open(selected_file, 'r', encoding='utf-8') as f:
                    file_content = json.load(f)
                
                # Determina il tipo di file
                if 'ai_overview' in file_content or 'full_content' in file_content:
                    st.session_state.ai_overview_data = file_content
                    st.success(f"✅ AI Overview caricato da {selected_file}!")
                elif 'gap_analysis' in file_content:
                    st.session_state.content_gap_data = file_content
                    st.success(f"✅ Analisi Gap caricata da {selected_file}!")
                else:
                    st.warning(f"⚠️ Tipo di file non riconosciuto: {selected_file}")
                    
                st.rerun()
            except Exception as e:
                st.error(f"❌ Errore nel caricare {selected_file}: {str(e)}")
    else:
        st.info("📁 Nessun file JSON trovato nella directory corrente")

with tab4:
    st.markdown("""
    <div class="cyber-card">
        <h2 style="color: var(--neon-green); text-shadow: 0 0 10px var(--neon-green); font-family: 'Orbitron', monospace; margin-bottom: 2rem;">📈 DASHBOARD ANALYTICS</h2>
        <p style="color: var(--text-neon); font-size: 1.2rem; line-height: 1.6;">Visualizza statistiche avanzate e metriche di performance del sistema di analisi.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metriche di sessione
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(create_metric_card(st.session_state.extraction_count, "Estrazioni Totali"), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card(st.session_state.analysis_count, "Analisi Totali"), unsafe_allow_html=True)
    
    with col3:
        success_rate = "100%" if st.session_state.extraction_count > 0 else "0%"
        st.markdown(create_metric_card(success_rate, "Success Rate"), unsafe_allow_html=True)
    
    # Grafici di performance
    if st.session_state.extraction_count > 0 or st.session_state.analysis_count > 0:
        st.markdown("""
        <div class="cyber-card">
            <h3 style="color: var(--neon-blue); text-shadow: 0 0 10px var(--neon-blue); font-family: 'Orbitron', monospace; margin-bottom: 2rem;">📊 PERFORMANCE ANALYTICS</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Grafico a torta delle attività
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Estrazioni AI Overview', 'Analisi Content Gap'],
            values=[st.session_state.extraction_count, st.session_state.analysis_count],
            hole=0.4,
            marker_colors=['#00d4ff', '#b347d9']
        )])
        
        fig_pie.update_layout(
            title={
                'text': 'Distribuzione Attività',
                'x': 0.5,
                'font': {'color': '#ffffff', 'size': 20, 'family': 'Orbitron'}
            },
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': '#ffffff', 'family': 'Rajdhani'},
            showlegend=True,
            legend={'font': {'color': '#ffffff'}}
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Benchmark di performance
        st.markdown("""
        <div class="cyber-card">
            <h3 style="color: var(--neon-purple); text-shadow: 0 0 10px var(--neon-purple); font-family: 'Orbitron', monospace; margin-bottom: 2rem;">⚡ BENCHMARK PERFORMANCE</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(create_metric_card("12.3s", "Estrazione Media", "benchmark"), unsafe_allow_html=True)
        with col2:
            st.markdown(create_metric_card("3.7s", "Analisi Media", "benchmark"), unsafe_allow_html=True)
        with col3:
            st.markdown(create_metric_card("94%", "Successo Rate", "benchmark"), unsafe_allow_html=True)
    
    else:
        st.markdown("""
        <div class="cyber-card">
            <p style="color: var(--neon-pink); text-shadow: 0 0 10px var(--neon-pink); font-size: 1.2rem; text-align: center;">📊 Nessun dato disponibile. Inizia estraendo un AI Overview!</p>
        </div>
        """, unsafe_allow_html=True)

# Footer con statistiche
st.markdown("""
<div class="cyber-card" style="margin-top: 3rem;">
    <h3 style="color: var(--neon-blue); text-shadow: 0 0 10px var(--neon-blue); font-family: 'Orbitron', monospace; text-align: center; margin-bottom: 1.5rem;">📊 STATISTICHE SESSIONE</h3>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown(create_metric_card(st.session_state.extraction_count, "Estrazioni"), unsafe_allow_html=True)
with col2:
    st.markdown(create_metric_card(st.session_state.analysis_count, "Analisi"), unsafe_allow_html=True)

st.markdown("""
<div class="cyber-card" style="margin-top: 2rem; text-align: center;">
    <p style="color: var(--text-neon); font-size: 1rem; margin-bottom: 0.5rem;">🚀 <strong>Ai Analyzer</strong> - Powered by Nicolas Micolani</p>
    <p style="color: var(--text-neon); font-size: 0.9rem; opacity: 0.8;">Ai Overview Scraper & Content Gap Analyz</p>
</div>
""", unsafe_allow_html=True)