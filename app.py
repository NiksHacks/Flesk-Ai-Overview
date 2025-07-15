#!/usr/bin/env python3
"""
Ai Analyzer - Flask App
Interfaccia ultra-moderna per analisi AI Overview e Content Gap
Powered by Nicolas Micolani
"""

from flask import Flask, render_template, request, jsonify, send_file, session
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
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'ai_analyzer_secret_key_2025'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Crea cartella uploads se non esiste
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Configurazione API Key AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDXB8Lj2gamg7SEYmxvZ_uEs7JX3RKZ9yY')

# Download dati NLTK necessari (solo al primo avvio)
try:
    import nltk
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

# Inizializzazione session state
def init_session():
    if 'extraction_count' not in session:
        session['extraction_count'] = 0
    if 'analysis_count' not in session:
        session['analysis_count'] = 0
    if 'ai_overview_data' not in session:
        session['ai_overview_data'] = None
    if 'content_gap_data' not in session:
        session['content_gap_data'] = None
    if 'chat_history' not in session:
        session['chat_history'] = []
    if 'semantic_analyzer' not in session:
        session['semantic_analyzer'] = None

@app.route('/')
def index():
    init_session()
    return render_template('index.html')

@app.route('/extract_ai_overview', methods=['POST'])
def extract_ai_overview():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'Query non fornita'})
        
        # Estrazione AI Overview
        extractor = AIOverviewExtractor(headless=True)
        result = extractor.extract_ai_overview_from_query(query)
        
        if result and result.get('found', False) and result.get('full_content', ''):
            # Crea oggetto compatibile
            ai_overview_data = {
                'query': query,
                'ai_overview': result.get('full_content', ''),
                'found': True,
                'extraction_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'sources': result.get('sources', [])
            }
            
            session['ai_overview_data'] = ai_overview_data
            session['extraction_count'] = session.get('extraction_count', 0) + 1
            
            return jsonify({
                'success': True,
                'data': ai_overview_data,
                'message': 'AI Overview estratto con successo!'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Nessun AI Overview trovato per questa query'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Errore durante l\'estrazione: {str(e)}'
        })
    finally:
        try:
            extractor.close()
        except:
            pass

@app.route('/clear_ai_overview', methods=['POST'])
def clear_ai_overview():
    session['ai_overview_data'] = None
    return jsonify({'success': True, 'message': 'AI Overview cancellato'})

@app.route('/chat_analyze', methods=['POST'])
def chat_analyze():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': 'Domanda non fornita'})
        
        # Inizializza semantic analyzer se necessario
        if not session.get('semantic_analyzer'):
            semantic_analyzer = SemanticAnalyzer(GEMINI_API_KEY)
            session['semantic_analyzer'] = True  # Flag per indicare che è inizializzato
        else:
            semantic_analyzer = SemanticAnalyzer(GEMINI_API_KEY)
        
        # Aggiungi domanda alla chat history
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        session['chat_history'].append({'role': 'user', 'content': question})
        
        # Prepara contesto
        context = ""
        if session.get('ai_overview_data'):
            ai_content = session['ai_overview_data'].get('ai_overview', session['ai_overview_data'].get('full_content', ''))
            context += f"\n\nAI OVERVIEW:\n{ai_content[:1500]}..."
        
        full_prompt = f"""Sei un esperto SEO e content strategist con oltre 10 anni di esperienza. Il tuo compito è fornire analisi precise, actionable e basate su dati concreti.

## RUOLO E COMPETENZE:
- Specialista in ottimizzazione per motori di ricerca
- Esperto in content strategy e gap analysis
- Analista di performance e metriche SEO
- Consulente per miglioramento della visibilità online

## CONTESTO DISPONIBILE:{context}

## DOMANDA DELL'UTENTE:
{question}

## ISTRUZIONI PER LA RISPOSTA:
1. **ANALISI**: Inizia con un'analisi chiara del problema/richiesta
2. **STRATEGIA**: Fornisci una strategia specifica e dettagliata
3. **AZIONI CONCRETE**: Elenca azioni precise e misurabili
4. **METRICHE**: Suggerisci KPI per monitorare i risultati
5. **TEMPISTICHE**: Indica quando possibile le tempistiche di implementazione

## FORMATO RISPOSTA:
- Usa un linguaggio professionale ma accessibile
- Struttura la risposta con titoli e sottotitoli chiari
- Fornisci esempi concreti quando possibile
- Includi riferimenti al contesto AI Overview quando rilevante
- Mantieni focus su risultati misurabili e ROI

## VINCOLI:
- Rispondi SEMPRE in italiano
- Basa le raccomandazioni sui dati del contesto fornito
- Se mancano informazioni, specifica cosa serve per un'analisi più precisa
- Evita consigli generici, sii sempre specifico

Fornisci una risposta completa, strutturata e immediatamente implementabile:"""
        
        # Controlla se l'utente richiede grafici o tabelle
        chart_keywords = ['grafico', 'grafica', 'chart', 'plot', 'visualizza', 'diagramma', 'istogramma', 'barre', 'linee', 'torta']
        table_keywords = ['tabella', 'table', 'elenco', 'lista strutturata', 'confronto', 'comparazione']
        
        wants_chart = any(keyword in question.lower() for keyword in chart_keywords)
        wants_table = any(keyword in question.lower() for keyword in table_keywords)
        
        if wants_chart or wants_table:
            # Genera prompt specifico per dati strutturati
            if wants_chart:
                structured_prompt = f"""{full_prompt}

## RICHIESTA VISUALIZZAZIONE DATI:
L'utente ha richiesto un grafico. Dopo la tua risposta testuale completa, DEVI includere OBBLIGATORIAMENTE i dati per la visualizzazione.

## FORMATO JSON RICHIESTO (OBBLIGATORIO):
Includi ESATTAMENTE questo formato JSON alla fine della tua risposta:

{{"chart": {{"type": "TIPO_GRAFICO", "title": "TITOLO_SPECIFICO", "data": DATI_STRUTTURATI}}}}

## TIPI DI GRAFICO SUPPORTATI:
- **bar**: Per confronti tra categorie
- **line**: Per trend temporali
- **pie**: Per distribuzioni percentuali

## STRUTTURE DATI SPECIFICHE:

**Per grafici a barre (bar):**
{{"chart": {{"type": "bar", "title": "Titolo Descrittivo", "data": {{"x": ["Categoria1", "Categoria2", "Categoria3"], "y": [valore1, valore2, valore3]}}}}}}

**Per grafici a linee (line):**
{{"chart": {{"type": "line", "title": "Titolo Descrittivo", "data": {{"x": ["Gen", "Feb", "Mar"], "y": [valore1, valore2, valore3]}}}}}}

**Per grafici a torta (pie):**
{{"chart": {{"type": "pie", "title": "Titolo Descrittivo", "data": {{"labels": ["Categoria1", "Categoria2", "Categoria3"], "values": [percentuale1, percentuale2, percentuale3]}}}}}}

## REGOLE OBBLIGATORIE:
1. I valori numerici devono essere SEMPRE numeri, mai stringhe
2. Le etichette devono essere descrittive e specifiche
3. Per grafici a torta, i valori devono sommare a 100
4. Massimo 8 elementi per grafico per leggibilità
5. Il JSON deve essere valido e ben formattato
6. Posiziona il JSON DOPO la risposta testuale, su una nuova riga

## ESEMPIO COMPLETO:
[La tua risposta testuale qui]

{{"chart": {{"type": "bar", "title": "Performance Keyword Top 5", "data": {{"x": ["keyword seo", "content marketing", "digital strategy", "web analytics", "social media"], "y": [85, 72, 68, 61, 45]}}}}}}

RICORDA: Il JSON è OBBLIGATORIO per visualizzare il grafico!"""
            else:
                structured_prompt = f"""{full_prompt}

## RICHIESTA VISUALIZZAZIONE TABELLA:
L'utente ha richiesto una tabella. Dopo la tua risposta testuale completa, DEVI includere OBBLIGATORIAMENTE i dati tabulari.

## FORMATO JSON RICHIESTO (OBBLIGATORIO):
Includi ESATTAMENTE questo formato JSON alla fine della tua risposta:

{{"table": {{"title": "TITOLO_DESCRITTIVO", "headers": ["Colonna1", "Colonna2", "Colonna3"], "rows": [["dato1", "dato2", "dato3"], ["dato4", "dato5", "dato6"]]}}}}

## REGOLE PER LA STRUTTURA TABELLA:
1. **Title**: Deve essere descrittivo e specifico
2. **Headers**: Massimo 6 colonne per leggibilità
3. **Rows**: Massimo 10 righe per performance
4. **Dati**: Devono essere coerenti con il tipo di colonna
5. **Formattazione**: Usa stringhe per tutti i valori nelle celle

## TIPI DI TABELLE CONSIGLIATE:
- **Analisi Competitor**: [Nome, DA, Traffico, Ranking]
- **Performance Keyword**: [Keyword, Volume, Difficoltà, Posizione]
- **Content Gap**: [Argomento, Priorità, Difficoltà, Impatto]
- **Metriche SEO**: [Metrica, Valore Attuale, Target, Status]
- **Timeline Azioni**: [Azione, Priorità, Tempistica, Responsabile]

## ESEMPI SPECIFICI:

**Analisi Competitor:**
{{"table": {{"title": "Top 5 Competitor Analysis", "headers": ["Competitor", "Domain Authority", "Traffico Mensile", "Top Keyword"], "rows": [["competitor1.com", "85", "2.5M", "digital marketing"], ["competitor2.com", "72", "1.8M", "seo tools"]]}}}}

**Performance Keyword:**
{{"table": {{"title": "Keyword Performance Report", "headers": ["Keyword", "Volume Ricerca", "Difficoltà SEO", "Posizione Attuale"], "rows": [["content marketing", "12,000", "65", "#8"], ["seo strategy", "8,500", "72", "#12"]]}}}}

## REGOLE OBBLIGATORIE:
1. Tutti i valori nelle celle devono essere stringhe (anche i numeri)
2. Le intestazioni devono essere chiare e specifiche
3. I dati devono essere realistici e coerenti
4. Ordina i dati per rilevanza/importanza
5. Il JSON deve essere valido e ben formattato
6. Posiziona il JSON DOPO la risposta testuale, su una nuova riga

## ESEMPIO COMPLETO:
[La tua risposta testuale qui]

{{"table": {{"title": "Content Gap Analysis - Top Priority", "headers": ["Argomento Mancante", "Priorità", "Difficoltà", "Impatto Stimato"], "rows": [["Tutorial SEO avanzato", "Alta", "Media", "85%"], ["Case study settore", "Alta", "Bassa", "70%"], ["Tools comparison", "Media", "Bassa", "60%"]]}}}}

RICORDA: Il JSON è OBBLIGATORIO per visualizzare la tabella!"""
        else:
            structured_prompt = full_prompt
        
        # Genera risposta
        response = semantic_analyzer.model.generate_content(structured_prompt)
        
        if response and response.text:
            response_text = response.text
            
            # Cerca dati JSON per grafici o tabelle nella risposta
            chart_data = None
            table_data = None
            
            # Estrai JSON dalla risposta se presente
            import re
            json_pattern = r'\{"(chart|table)":[^}]+\}\}'
            json_matches = re.findall(json_pattern, response_text)
            
            if json_matches:
                try:
                    # Trova l'intero blocco JSON
                    json_start = response_text.find('{"')
                    if json_start != -1:
                        # Trova la fine del JSON
                        brace_count = 0
                        json_end = json_start
                        for i, char in enumerate(response_text[json_start:]):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = json_start + i + 1
                                    break
                        
                        json_str = response_text[json_start:json_end]
                        visual_data = json.loads(json_str)
                        
                        if 'chart' in visual_data:
                            chart_data = visual_data['chart']
                        elif 'table' in visual_data:
                            table_data = visual_data['table']
                        
                        # Rimuovi il JSON dalla risposta testuale
                        response_text = response_text[:json_start].strip()
                        
                except (json.JSONDecodeError, ValueError):
                    pass  # Continua con la risposta normale se il JSON non è valido
            
            # Prepara la risposta finale
            final_response = response_text
            
            if chart_data:
                final_response = {
                    'text': response_text,
                    'chart': chart_data
                }
            elif table_data:
                final_response = {
                    'text': response_text,
                    'table': table_data
                }
            
            session['chat_history'].append({'role': 'assistant', 'content': final_response})
            session['analysis_count'] = session.get('analysis_count', 0) + 1
            
            return jsonify({
                'success': True,
                'response': final_response,
                'chat_history': session['chat_history']
            })
        else:
            return jsonify({'success': False, 'error': 'Errore nella risposta AI'})
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Errore nell\'analisi: {str(e)}'
        })

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session['chat_history'] = []
    return jsonify({'success': True, 'message': 'Chat cancellata'})

@app.route('/upload_json', methods=['POST'])
def upload_json():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nessun file caricato'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nessun file selezionato'})
        
        if file and file.filename.endswith('.json'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Leggi e valida il file JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'ai_overview' in data or 'full_content' in data:
                session['ai_overview_data'] = data
                
                # Messaggio di benvenuto automatico
                welcome_msg = f"Ho caricato l'AI Overview. Contiene {len(data.get('ai_overview', data.get('full_content', '')).split())} parole. Cosa vorresti sapere?"
                
                if 'chat_history' not in session:
                    session['chat_history'] = []
                
                if not session['chat_history'] or session['chat_history'][-1]['content'] != welcome_msg:
                    session['chat_history'].append({'role': 'assistant', 'content': welcome_msg})
                
                # Rimuovi file temporaneo
                os.remove(filepath)
                
                return jsonify({
                    'success': True,
                    'message': 'AI Overview caricato con successo!',
                    'data': data,
                    'chat_history': session['chat_history']
                })
            else:
                os.remove(filepath)
                return jsonify({'success': False, 'error': 'File JSON non valido. Deve contenere \'ai_overview\' o \'full_content\'.'})
        
        return jsonify({'success': False, 'error': 'Formato file non supportato. Usa file .json'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Errore nel caricamento: {str(e)}'})



@app.route('/export_chat')
def export_chat():
    try:
        chat_history = session.get('chat_history', [])
        if not chat_history:
            return jsonify({'success': False, 'error': 'Nessuna conversazione da esportare'})
        
        # Crea contenuto chat
        chat_content = "# Conversazione Content Gap Analyzer\n\n"
        chat_content += f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        
        for i, message in enumerate(chat_history, 1):
            role = "👤 **Utente**" if message['role'] == 'user' else "🤖 **AI Assistant**"
            chat_content += f"## {role}\n\n{message['content']}\n\n---\n\n"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"chat_content_gap_{timestamp}.md"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(chat_content)
        
        return send_file(filepath, as_attachment=True, download_name=filename, mimetype='text/markdown')
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Errore nell\'esportazione: {str(e)}'})

@app.route('/get_stats')
def get_stats():
    return jsonify({
        'extraction_count': session.get('extraction_count', 0),
        'analysis_count': session.get('analysis_count', 0),
        'has_ai_overview': session.get('ai_overview_data') is not None,
        'chat_messages': len(session.get('chat_history', []))
    })

@app.route('/get_ai_overview')
def get_ai_overview():
    return jsonify({
        'data': session.get('ai_overview_data'),
        'has_data': session.get('ai_overview_data') is not None
    })

@app.route('/get_chat_history')
def get_chat_history():
    return jsonify({
        'chat_history': session.get('chat_history', [])
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)