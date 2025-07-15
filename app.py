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
import google.generativeai as genai

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
    extractor = None
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'Query non fornita'})
        
        # Prova prima con Playwright
        try:
            print("🚀 Tentativo estrazione con Playwright...")
            extractor = AIOverviewExtractor(headless=True)
            result = extractor.extract_ai_overview_from_query(query)
            
            if result and result.get('found', False) and result.get('full_content', ''):
                method_used = result.get('method', 'playwright')
                print(f"✅ Estrazione riuscita con metodo: {method_used}")
            else:
                result = None
                
        except Exception as playwright_error:
            print(f"❌ Errore Playwright: {playwright_error}")
            print("🔄 Passaggio al metodo fallback...")
            
            # Chiudi extractor precedente se esiste
            if extractor:
                try:
                    extractor.close()
                except:
                    pass
            
            # Prova con metodo fallback
            try:
                extractor = AIOverviewExtractor(use_fallback=True)
                result = extractor.extract_ai_overview_from_query(query)
                
                if result and result.get('found', False) and result.get('full_content', ''):
                    method_used = result.get('method', 'requests_fallback')
                    print(f"✅ Estrazione fallback riuscita con metodo: {method_used}")
                else:
                    result = None
                    
            except Exception as fallback_error:
                print(f"❌ Errore anche con fallback: {fallback_error}")
                result = None
        
        # Processa il risultato se trovato
        if result and result.get('found', False) and result.get('full_content', ''):
            # Crea oggetto compatibile
            ai_overview_data = {
                'query': query,
                'ai_overview': result.get('full_content', ''),
                'found': True,
                'extraction_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'sources': result.get('sources', []),
                'method': result.get('method', 'unknown')
            }
            
            session['ai_overview_data'] = ai_overview_data
            session['extraction_count'] = session.get('extraction_count', 0) + 1
            
            return jsonify({
                'success': True,
                'data': ai_overview_data,
                'message': f'AI Overview estratto con successo! (Metodo: {result.get("method", "unknown")})'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Nessun AI Overview trovato per questa query. Prova con una query diversa o più specifica.'
            })
            
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        return jsonify({
            'success': False,
            'error': f'Errore durante l\'estrazione: {str(e)}'
        })
    finally:
        if extractor:
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
    semantic_analyzer = None
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': 'Domanda non fornita'})
        
        print(f"🤖 Elaborazione domanda: {question[:100]}...")
        
        # Inizializza semantic analyzer con gestione memoria ottimizzata
        try:
            semantic_analyzer = SemanticAnalyzer(GEMINI_API_KEY)
        except Exception as e:
            print(f"❌ Errore inizializzazione SemanticAnalyzer: {e}")
            return jsonify({
                'success': False, 
                'error': 'Servizio di analisi temporaneamente non disponibile. Riprova tra qualche minuto.'
            })
        
        # Aggiungi domanda alla chat history (limitata per memoria)
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        # Mantieni solo le ultime 5 conversazioni per ridurre memoria
        if len(session['chat_history']) >= 10:
            session['chat_history'] = session['chat_history'][-8:]
        
        session['chat_history'].append({'role': 'user', 'content': question})
        
        # Prepara contesto completo
        context = ""
        if session.get('ai_overview_data'):
            ai_content = session['ai_overview_data'].get('ai_overview', session['ai_overview_data'].get('full_content', ''))
            # Usa il contesto completo per analisi dettagliate
            context += f"\n\nAI OVERVIEW:\n{ai_content}"
        
        # Prompt SEO ottimizzato per Content Gap Analysis
        full_prompt = f"""Sei un ESPERTO SEO specializzato in Content Gap Analysis.

## CONTESTO:{context}

## DOMANDA:
{question}

## ANALISI RICHIESTA:

🔍 **CONTENT GAP**: Identifica lacune di contenuto e argomenti mancanti
🎯 **KEYWORD GAP**: Parole chiave semanticamente correlate non coperte  
💡 **OPPORTUNITÀ**: 3-4 azioni concrete e prioritarie
📊 **STRATEGIA**: Raccomandazioni per migliorare autorità tematica
⚡ **QUICK WINS**: Modifiche rapide ad alto impatto

Rispondi in italiano con analisi professionale e actionable completa (max 15000 caratteri):"""
        
        # Genera risposta con timeout ridotto
        try:
            print(f"🔍 Debug - Prompt inviato: {full_prompt[:200]}...")
            response = semantic_analyzer.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=4096,  # Aumentato significativamente per evitare MAX_TOKENS
                    temperature=0.7
                )
            )
            
            print(f"🔍 Debug - Risposta ricevuta: {response}")
            print(f"🔍 Debug - Candidates: {response.candidates if hasattr(response, 'candidates') else 'N/A'}")
            
            # Prova ad accedere alla risposta con metodi diversi
            response_text = None
            
            # Metodo 1: Prova response.text diretto
            try:
                if response and hasattr(response, 'text') and response.text:
                    response_text = response.text.strip()
                    print(f"🔍 Debug - Metodo 1 successo: {len(response_text)} caratteri")
            except Exception as e:
                print(f"🔍 Debug - Metodo 1 fallito: {e}")
                pass
            
            # Metodo 2: Prova tramite candidates se il primo fallisce
            if not response_text and response.candidates and len(response.candidates) > 0:
                try:
                    candidate = response.candidates[0]
                    print(f"🔍 Debug - Candidate: {candidate}")
                    
                    # Gestisci il caso MAX_TOKENS
                    if candidate.finish_reason == 3:  # MAX_TOKENS
                        print("🔍 Debug - Rilevato MAX_TOKENS, provo a estrarre contenuto parziale")
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    response_text = part.text.strip() + "\n\n[Risposta troncata - riprova con una domanda più specifica]"
                                    print(f"🔍 Debug - Metodo 2 MAX_TOKENS successo: {len(response_text)} caratteri")
                                    break
                    elif hasattr(candidate.content, 'parts') and candidate.content.parts:
                        response_text = candidate.content.parts[0].text.strip()
                        print(f"🔍 Debug - Metodo 2 successo: {len(response_text)} caratteri")
                except Exception as e:
                    print(f"🔍 Debug - Metodo 2 fallito: {e}")
                    pass
            
            print(f"🔍 Debug - Response_text finale: {response_text}")
            
            if response_text:
                # Aggiungi alla chat history con limite di memoria
                if len(session['chat_history']) >= 20:
                    session['chat_history'] = session['chat_history'][-15:]
                
                session['chat_history'].append({'role': 'assistant', 'content': response_text})
                session['analysis_count'] = session.get('analysis_count', 0) + 1
                
                print(f"✅ Risposta generata: {len(response_text)} caratteri")
                
                result = {
                    'success': True,
                    'response': response_text,
                    'chat_history': session['chat_history'][-10:]  # Restituisci solo le ultime 10 conversazioni
                }
                print(f"🔍 Debug - JSON restituito: {result}")
                return jsonify(result)
            else:
                error_result = {'success': False, 'error': 'Nessuna risposta valida generata dall\'AI. Prova a riformulare la domanda.'}
                print(f"🔍 Debug - Errore restituito: {error_result}")
                return jsonify(error_result)
                
        except Exception as ai_error:
            print(f"❌ Errore AI: {ai_error}")
            return jsonify({
                'success': False, 
                'error': 'Servizio AI temporaneamente sovraccarico. Riprova tra qualche minuto.'
            })
            
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
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)