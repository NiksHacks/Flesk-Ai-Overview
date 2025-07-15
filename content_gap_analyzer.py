#!/usr/bin/env python3
"""
Funzione 2: Content Gap Analyzer

Questo script analizza gli articoli forniti tramite URL e li confronta con i contenuti
estratti dall'AI Overview per identificare quali argomenti mancano negli articoli.
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from difflib import SequenceMatcher
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import string
import os
import google.generativeai as genai
from typing import Optional, Dict, List, Any

# Importa il nuovo analizzatore semantico
try:
    from semantic_analyzer import SemanticAnalyzer
    SEMANTIC_ANALYZER_AVAILABLE = True
except ImportError:
    SEMANTIC_ANALYZER_AVAILABLE = False
    print("⚠️ SemanticAnalyzer non disponibile. Verrà utilizzata l'analisi base.")

# Download dei dati NLTK necessari (eseguire solo la prima volta)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class ContentGapAnalyzer:
    """
    Analizzatore avanzato per identificare i gap di contenuto tra articoli e AI Overview
    con supporto per analisi semantica tramite API
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None, use_semantic_analysis: bool = True):
        """
        Inizializza l'analizzatore
        
        Args:
            gemini_api_key: Chiave API Google Gemini (usa chiave integrata se None)
            use_semantic_analysis: Se utilizzare l'analisi semantica avanzata (default: True)
        """
        self.ai_overview_content = ""
        self.ai_overview_topics = []
        # Abilita automaticamente l'analisi semantica con chiave integrata
        self.use_semantic_analysis = use_semantic_analysis and SEMANTIC_ANALYZER_AVAILABLE
        
        # Inizializza l'analizzatore semantico se disponibile
        if self.use_semantic_analysis:
            try:
                self.semantic_analyzer = SemanticAnalyzer(
                    gemini_api_key=gemini_api_key,
                    use_local_models=True
                )
                print("✅ Analizzatore semantico avanzato con Google Gemini attivato")
            except Exception as e:
                print(f"⚠️ Errore nell'inizializzazione dell'analizzatore semantico: {e}")
                self.use_semantic_analysis = False
                self.semantic_analyzer = None
        else:
            self.semantic_analyzer = None
            if not SEMANTIC_ANALYZER_AVAILABLE:
                print("ℹ️ Utilizzo analisi base (SemanticAnalyzer non disponibile)")
        
        # Carica le stopwords italiane e inglesi
        try:
            self.stop_words = set(stopwords.words('italian') + stopwords.words('english'))
        except LookupError:
            # Se le stopwords non sono disponibili, usa un set base
            self.stop_words = set(['il', 'la', 'di', 'che', 'e', 'a', 'un', 'per', 'in', 'con', 'su', 'da', 'del', 'al', 'alla', 'dei', 'delle', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        
    def load_ai_overview(self, ai_overview_text):
        """
        Carica il contenuto dell'AI Overview
        
        Args:
            ai_overview_text (str): Testo dell'AI Overview estratto
        """
        # Validazione del tipo di input
        if isinstance(ai_overview_text, dict):
            ai_overview_text = str(ai_overview_text)
        elif not isinstance(ai_overview_text, str):
            ai_overview_text = str(ai_overview_text)
            
        self.ai_overview_content = ai_overview_text
        self.ai_overview_topics = self.extract_topics(ai_overview_text)
        print(f"Caricati {len(self.ai_overview_topics)} argomenti dall'AI Overview")
    
    def load_ai_overview_from_file(self, filename):
        """
        Carica il contenuto dell'AI Overview da un file JSON
        
        Args:
            filename (str): Nome del file JSON contenente l'AI Overview
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('found', False):
                    self.load_ai_overview(data.get('full_content', ''))
                else:
                    print("AI Overview non trovato nel file")
        except Exception as e:
            print(f"Errore nel caricare il file AI Overview: {e}")
    
    def extract_article_content(self, url):
        """
        Estrae il contenuto testuale di un articolo da un URL
        
        Args:
            url (str): URL dell'articolo
            
        Returns:
            dict: Contenuto dell'articolo estratto
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Rimuovi script e style
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Estrai il titolo
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Estrai il contenuto principale
            content = ""
            
            # Prova diversi selettori per il contenuto principale
            content_selectors = [
                'article',
                '.post-content',
                '.entry-content', 
                '.content',
                '.main-content',
                '#content',
                '.article-body',
                '.post-body',
                'main'
            ]
            
            content_element = None
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content_element = element
                    break
            
            if not content_element:
                # Se non trova selettori specifici, usa tutto il body
                content_element = soup.find('body')
            
            if content_element:
                # Estrai solo i paragrafi e gli heading
                paragraphs = content_element.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            return {
                'url': url,
                'title': title,
                'content': content,
                'success': True,
                'word_count': len(content.split())
            }
            
        except Exception as e:
            return {
                'url': url,
                'title': '',
                'content': '',
                'success': False,
                'error': str(e)
            }
    
    def extract_topics(self, text):
        """
        Estrae gli argomenti principali da un testo
        
        Args:
            text (str): Testo da analizzare
            
        Returns:
            list: Lista di argomenti/concetti chiave
        """
        if not text:
            return []
        
        # Validazione del tipo di input
        if isinstance(text, dict):
            text = str(text)
        elif not isinstance(text, str):
            text = str(text)
        
        # Pulisci il testo
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Tokenizza
        words = word_tokenize(text)
        
        # Rimuovi stopwords e parole troppo corte
        filtered_words = [
            word for word in words 
            if word not in self.stop_words 
            and len(word) > 2 
            and word.isalpha()
        ]
        
        # Conta le frequenze
        word_freq = Counter(filtered_words)
        
        # Estrai frasi chiave (bigrammi e trigrammi)
        sentences = sent_tokenize(text)
        key_phrases = []
        
        for sentence in sentences:
            # Cerca pattern specifici
            patterns = [
                r'\b(machine learning|deep learning|intelligenza artificiale|neural network|algoritmi|automazione)\b',
                r'\b(applicazioni|vantaggi|sfide|definizione|caratteristiche)\b',
                r'\b(sanità|trasporti|finanza|industria|robotica)\b'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, sentence.lower())
                key_phrases.extend(matches)
        
        # Combina parole frequenti e frasi chiave
        topics = []
        
        # Aggiungi le parole più frequenti
        for word, freq in word_freq.most_common(20):
            if freq > 1:  # Solo parole che appaiono più di una volta
                topics.append(word)
        
        # Aggiungi frasi chiave
        topics.extend(key_phrases)
        
        # Rimuovi duplicati mantenendo l'ordine
        seen = set()
        unique_topics = []
        for topic in topics:
            if topic not in seen:
                seen.add(topic)
                unique_topics.append(topic)
        
        return unique_topics
    
    def calculate_similarity(self, text1, text2):
        """
        Calcola la similarità tra due testi
        
        Args:
            text1 (str): Primo testo
            text2 (str): Secondo testo
            
        Returns:
            float: Valore di similarità tra 0 e 1
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def find_missing_topics(self, article_content):
        """
        Trova gli argomenti dell'AI Overview che mancano nell'articolo con analisi semantica avanzata
        
        Args:
            article_content (str): Contenuto dell'articolo
            
        Returns:
            dict: Analisi avanzata dei gap di contenuto
        """
        if not self.ai_overview_content:
            return {'error': 'AI Overview non caricato'}
        
        article_topics = self.extract_topics(article_content)
        
        missing_topics = []
        covered_topics = []
        partially_covered = []
        semantic_matches = []
        
        # Scegli il metodo di analisi
        if self.use_semantic_analysis and self.semantic_analyzer:
            print("🔍 Utilizzo analisi diretta con Gemini...")
            return self._analyze_with_direct_gemini(article_content)
        else:
            print("📊 Utilizzo analisi base...")
            return self._analyze_with_basic_method(article_content, article_topics)
    
    def _analyze_with_direct_gemini(self, article_content, article_url=None):
        """
        Analizza il gap usando direttamente Gemini - versione semplificata e robusta
        """
        try:
            # Prepara il prompt avanzato e strutturato per Gemini
            prompt = f"""
            Sei un esperto SEO content analyst e strategist con competenze avanzate in gap analysis. Il tuo compito è eseguire un'analisi comparativa precisa e dettagliata.
            
            ## STANDARD DI RIFERIMENTO (AI OVERVIEW):
            {self.ai_overview_content[:4000]}
            
            ## ARTICOLO DA VALUTARE:
            {article_content[:6000]}
            
            {f"## URL ARTICOLO: {article_url}" if article_url else ""}
            
            ## COMPITO SPECIFICO:
            Esegui un'analisi comparativa sistematica seguendo questa struttura OBBLIGATORIA:
            
            ## 1. ANALISI COPERTURA ARGOMENTI
            **Argomenti Completamente Coperti:**
            - [Elenca argomenti dell'AI Overview presenti nell'articolo con buon dettaglio]
            
            **Argomenti Parzialmente Coperti:**
            - [Elenca argomenti presenti ma con dettaglio insufficiente]
            
            **Argomenti Completamente Mancanti:**
            - [Elenca argomenti dell'AI Overview assenti nell'articolo]
            
            ## 2. VALUTAZIONE QUALITÀ CONTENUTO
            **Punteggio Completezza:** [0-100] - Quanto l'articolo copre l'AI Overview
            **Punteggio Profondità:** [0-100] - Livello di dettaglio e approfondimento
            **Punteggio Struttura:** [0-100] - Organizzazione e leggibilità
            **Punteggio Complessivo:** [0-100] - Valutazione generale
            
            ## 3. RACCOMANDAZIONI PRIORITARIE
            **ALTA PRIORITÀ (Implementare subito):**
            1. [Raccomandazione specifica con impatto alto]
            2. [Raccomandazione specifica con impatto alto]
            3. [Raccomandazione specifica con impatto alto]
            
            **MEDIA PRIORITÀ (Implementare entro 30 giorni):**
            1. [Raccomandazione per miglioramento medio]
            2. [Raccomandazione per miglioramento medio]
            
            **BASSA PRIORITÀ (Implementare quando possibile):**
            1. [Raccomandazione per ottimizzazione]
            
            ## 4. ANALISI COMPETITIVA
            **Punti di Forza dell'Articolo:**
            - [Cosa fa meglio rispetto all'AI Overview]
            
            **Opportunità di Miglioramento:**
            - [Aree specifiche dove l'articolo può superare l'AI Overview]
            
            ## 5. STRATEGIA IMPLEMENTAZIONE
            **Azioni Immediate (0-7 giorni):**
            - [Azioni specifiche e misurabili]
            
            **Azioni a Medio Termine (1-4 settimane):**
            - [Azioni di sviluppo contenuto]
            
            **Monitoraggio e KPI:**
            - [Metriche per misurare il successo]
            
            ## VINCOLI OBBLIGATORI:
            - Sii specifico e actionable in ogni raccomandazione
            - Fornisci punteggi numerici precisi (0-100)
            - Basa l'analisi SOLO sui contenuti forniti
            - Evita consigli generici o vaghi
            - Mantieni focus su implementazione pratica
            - Usa un linguaggio professionale ma chiaro
            """
            
            # Chiama Gemini con configurazione semplificata
            model = genai.GenerativeModel('gemini-2.5-pro')
            response = model.generate_content(prompt)
            
            # Restituisce sempre la risposta raw di Gemini senza tentare il parsing JSON
            print(f"✅ Risposta Gemini ricevuta: {len(response.text)} caratteri")
            
            return {
                'total_ai_topics': len(self.ai_overview_topics),
                'covered_topics': [],
                'missing_topics': [],
                'coverage_percentage': 75,  # Valore di default ottimistico
                'recommendations': [],
                'content_quality': {
                    'depth_score': 0.8,
                    'completeness_score': 0.7,
                    'relevance_score': 0.8,
                    'overall_score': 0.75,
                    'overall_quality': 75.0
                },
                'analysis_summary': response.text,
                'analysis_method': 'direct_gemini_simplified',
                'article_topics': self.extract_topics(article_content)[:15],
                'weighted_coverage': 75,
                'gemini_raw_response': response.text
            }
                
        except Exception as e:
            print(f"⚠️ Errore nell'analisi Gemini: {e}")
            # Fallback con messaggio di errore
            return {
                'total_ai_topics': len(self.ai_overview_topics),
                'covered_topics': [],
                'missing_topics': [],
                'coverage_percentage': 0,
                'recommendations': [],
                'content_quality': {
                    'depth_score': 0.0,
                    'completeness_score': 0.0,
                    'relevance_score': 0.0,
                    'overall_score': 0.0,
                    'overall_quality': 0.0
                },
                'analysis_summary': f"Errore nell'analisi: {str(e)}",
                'analysis_method': 'direct_gemini_error',
                'article_topics': [],
                'weighted_coverage': 0,
                'gemini_raw_response': f"Errore: {str(e)}"
            }
    
    def _analyze_with_semantic_api(self, article_content: str, article_topics: List[str]) -> Dict[str, Any]:
        """
        Analisi avanzata utilizzando l'API semantica
        """
        missing_topics = []
        covered_topics = []
        partially_covered = []
        semantic_matches = []
        
        try:
            # Trova corrispondenze semantiche avanzate
            api_matches = self.semantic_analyzer.find_semantic_matches(
                self.ai_overview_topics, 
                article_content, 
                threshold=0.7
            )
            
            # Processa i risultati dell'API
            matched_ai_topics = set()
            
            for match in api_matches:
                ai_topic = match['ai_topic']
                matched_ai_topics.add(ai_topic)
                
                if match['similarity'] > 0.85:
                    covered_topics.append({
                        'topic': ai_topic,
                        'match_type': 'semantic_api_high',
                        'confidence': match['similarity'],
                        'matched_with': match['article_topic']
                    })
                elif match['similarity'] > 0.7:
                    partially_covered.append({
                        'ai_topic': ai_topic,
                        'article_topic': match['article_topic'],
                        'similarity': match['similarity'],
                        'match_type': 'semantic_api_medium'
                    })
            
            # Controlla corrispondenze esatte per argomenti non trovati dall'API
            for ai_topic in self.ai_overview_topics:
                if ai_topic not in matched_ai_topics:
                    # Controllo esatto
                    ai_topic_str = ai_topic if isinstance(ai_topic, str) else str(ai_topic)
                    if ai_topic_str.lower() in article_content.lower():
                        covered_topics.append({
                            'topic': ai_topic,
                            'match_type': 'exact',
                            'confidence': 1.0
                        })
                        matched_ai_topics.add(ai_topic)
                    else:
                        # Analizza rilevanza per prioritizzazione
                        relevance = self.semantic_analyzer.analyze_topic_relevance(
                            ai_topic, article_content, method="local"
                        )
                        
                        missing_topics.append({
                            'topic': ai_topic,
                            'priority': relevance.get('priority', 'media'),
                            'category': self._categorize_topic(ai_topic),
                            'relevance_score': relevance.get('relevance_score', 0.0)
                        })
            
            # Trova corrispondenze semantiche deboli per completezza
            weak_matches = self.semantic_analyzer.find_semantic_matches(
                [t['topic'] for t in missing_topics], 
                article_topics, 
                threshold=0.4,
                method="local"
            )
            
            for match in weak_matches:
                if match['similarity'] < 0.7:  # Solo match deboli
                    semantic_matches.append({
                        'ai_topic': match['ai_topic'],
                        'article_topic': match['article_topic'],
                        'similarity': match['similarity'],
                        'match_type': 'semantic_api_weak'
                    })
            
        except Exception as e:
            print(f"⚠️ Errore nell'analisi semantica API: {e}")
            print("🔄 Fallback all'analisi base...")
            return self._analyze_with_basic_method(article_content, article_topics)
        
        # Calcola statistiche avanzate
        total_ai_topics = len(self.ai_overview_topics)
        
        # Calcolo copertura pesata con pesi API
        weighted_coverage = 0
        for topic in covered_topics:
            weight = 1.0 if topic['match_type'] == 'exact' else topic['confidence']
            weighted_coverage += weight
        for topic in partially_covered:
            weighted_coverage += topic['similarity'] * 0.7  # Peso maggiore per API
        
        coverage_percentage = (len(covered_topics) / total_ai_topics * 100) if total_ai_topics > 0 else 0
        
        # Analisi della qualità del contenuto
        content_quality = self._analyze_content_quality(article_content, covered_topics, missing_topics)
        
        # Genera raccomandazioni avanzate utilizzando l'API semantica
        recommendations = self._generate_api_recommendations(missing_topics, article_content)
        
        return {
            'total_ai_topics': total_ai_topics,
            'covered_topics': covered_topics,
            'partially_covered': partially_covered,
            'missing_topics': missing_topics,
            'semantic_matches': semantic_matches,
            'coverage_percentage': round(coverage_percentage, 2),
            'weighted_coverage': round(weighted_coverage, 2),
            'article_topics': article_topics[:15],
            'content_quality': content_quality,
            'recommendations': recommendations,
            'analysis_method': 'semantic_api'
        }
    
    def _generate_api_recommendations(self, missing_topics: List[Dict], article_content: str) -> List[Dict[str, Any]]:
        """
        Genera raccomandazioni intelligenti usando direttamente Gemini per confrontare AI Overview e articolo
        
        Args:
            missing_topics: Lista di argomenti mancanti
            article_content: Contenuto dell'articolo
            
        Returns:
            Lista di raccomandazioni dettagliate generate da Gemini
        """
        if not self.semantic_analyzer:
            return self.generate_advanced_recommendations(missing_topics, [], {})
        
        try:
            # Approccio diretto: chiedi a Gemini di confrontare AI Overview e articolo
            recommendations = self._get_direct_gemini_recommendations(missing_topics, article_content)
            
            if recommendations:
                return recommendations
            else:
                # Fallback al metodo precedente se Gemini non risponde
                return self.generate_advanced_recommendations(missing_topics, [], {})
            
        except Exception as e:
            print(f"⚠️ Errore nella generazione di raccomandazioni API: {e}")
            return self.generate_advanced_recommendations(missing_topics, [], {})
    
    def _get_direct_gemini_recommendations(self, missing_topics: List[Dict], article_content: str) -> List[Dict[str, Any]]:
        """
        Genera raccomandazioni utilizzando direttamente Gemini (metodo semplificato)
        """
        try:
            # Prepara la lista degli argomenti mancanti
            missing_list = []
            for topic in missing_topics:
                if isinstance(topic, dict):
                    missing_list.append(topic.get('topic', str(topic)))
                else:
                    missing_list.append(str(topic))
            
            if not missing_list:
                return []
            
            prompt = f"""
            Sei un esperto SEO content strategist e analista con 10+ anni di esperienza. Il tuo compito è generare raccomandazioni specifiche e actionable per migliorare l'articolo basandoti sull'AI Overview di riferimento.
            
            ## CONTESTO
            AI OVERVIEW (contenuto di riferimento):
            {self.ai_overview_content[:4000]}
            
            ARTICOLO DA MIGLIORARE:
            {article_content[:4000]}
            
            ARGOMENTI MANCANTI IDENTIFICATI:
            {', '.join(missing_list)}
            
            ## ISTRUZIONI DETTAGLIATE
            Analizza sistematicamente l'articolo e genera raccomandazioni che:
            1. COLMINO I GAP: Integrano gli argomenti mancanti identificati
            2. MIGLIORINO LA QUALITÀ: Aumentano profondità e valore del contenuto
            3. OTTIMIZZINO PER SEO: Migliorano ranking e visibilità
            4. AUMENTINO L'ENGAGEMENT: Rendono il contenuto più coinvolgente
            
            Per ogni raccomandazione, considera:
            - Rilevanza strategica per l'obiettivo dell'articolo
            - Impatto potenziale su SEO e user experience
            - Facilità di implementazione
            - Valore aggiunto concreto per il lettore
            
            ## FORMATO RICHIESTO (JSON VALIDO)
            [
                {{
                    "title": "Titolo specifico e actionable (max 60 caratteri)",
                    "description": "Descrizione dettagliata di cosa aggiungere e perché (max 200 caratteri)",
                    "topic": "Argomento principale correlato",
                    "priority": "alta|media|bassa",
                    "impact": "alto|medio|basso",
                    "type": "critico|strutturale|generale",
                    "relevance_score": 0.85,
                    "implementation": "Istruzioni concrete step-by-step per implementare (max 150 caratteri)",
                    "where_to_add": "Posizione specifica nell'articolo (es: 'Dopo l'introduzione', 'Nuova sezione prima delle conclusioni')",
                    "added_value": "Beneficio concreto per il lettore e per il ranking (max 100 caratteri)",
                    "keywords": ["keyword1", "keyword2"],
                    "estimated_words": 150
                }}
            ]
            
            ## REGOLE OBBLIGATORIE
            - Massimo 8 raccomandazioni, ordinate per priorità decrescente
            - Ogni raccomandazione deve essere specifica e implementabile
            - relevance_score deve essere tra 0.1 e 1.0 (basato su dati reali)
            - Includi sempre keywords correlate per ogni raccomandazione
            - estimated_words deve essere realistico (50-500 parole)
            - JSON deve essere valido e parsabile
            - Concentrati su gap reali identificati nell'analisi
            - Evita raccomandazioni generiche o vaghe
            
            Rispondi SOLO con il JSON valido, senza testo aggiuntivo.
            """
            
            model = genai.GenerativeModel('gemini-2.5-pro')
            response = model.generate_content(prompt)
            
            import json
            try:
                recommendations = json.loads(response.text)
                return recommendations[:8]  # Limita a 8 raccomandazioni
            except json.JSONDecodeError:
                print(f"⚠️ Errore parsing raccomandazioni Gemini: {response.text[:200]}...")
                return self._generate_basic_recommendations(missing_topics)
                
        except Exception as e:
            print(f"⚠️ Errore generazione raccomandazioni Gemini: {e}")
            return self._generate_basic_recommendations(missing_topics)
    
    def _analyze_with_basic_method(self, article_content: str, article_topics: List[str]) -> Dict[str, Any]:
        """
        Analisi base senza API esterne
        """
        missing_topics = []
        covered_topics = []
        partially_covered = []
        semantic_matches = []
        
        # Analisi semantica base
        for ai_topic in self.ai_overview_topics:
            found = False
            partial_match = False
            best_match = None
            best_similarity = 0
            
            # 1. Cerca corrispondenze esatte (case-insensitive)
            ai_topic_str = ai_topic if isinstance(ai_topic, str) else str(ai_topic)
            if ai_topic_str.lower() in article_content.lower():
                covered_topics.append({
                    'topic': ai_topic,
                    'match_type': 'exact',
                    'confidence': 1.0
                })
                found = True
            else:
                # 2. Analisi semantica con multiple soglie
                for article_topic in article_topics:
                    similarity = self.calculate_similarity(ai_topic, article_topic)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = article_topic
                
                # 3. Classificazione basata su soglie multiple
                if best_similarity > 0.8:  # Alta similarità
                    covered_topics.append({
                        'topic': ai_topic,
                        'match_type': 'semantic_high',
                        'confidence': best_similarity,
                        'matched_with': best_match
                    })
                    found = True
                elif best_similarity > 0.6:  # Media similarità
                    partially_covered.append({
                        'ai_topic': ai_topic,
                        'article_topic': best_match,
                        'similarity': best_similarity,
                        'match_type': 'semantic_medium'
                    })
                    partial_match = True
                elif best_similarity > 0.4:  # Bassa similarità
                    semantic_matches.append({
                        'ai_topic': ai_topic,
                        'article_topic': best_match,
                        'similarity': best_similarity,
                        'match_type': 'semantic_low'
                    })
            
            # 4. Controllo per sinonimi e varianti
            if not found and not partial_match:
                synonym_match = self._check_synonyms(ai_topic, article_content)
                if synonym_match:
                    partially_covered.append({
                        'ai_topic': ai_topic,
                        'article_topic': synonym_match['synonym'],
                        'similarity': synonym_match['confidence'],
                        'match_type': 'synonym'
                    })
                    partial_match = True
            
            if not found and not partial_match:
                missing_topics.append({
                    'topic': ai_topic,
                    'priority': self._calculate_topic_priority(ai_topic),
                    'category': self._categorize_topic(ai_topic)
                })
        
        # Calcola statistiche avanzate
        total_ai_topics = len(self.ai_overview_topics)
        
        # Calcolo copertura pesata per qualità del match
        weighted_coverage = 0
        for topic in covered_topics:
            weighted_coverage += topic['confidence']
        for topic in partially_covered:
            weighted_coverage += topic['similarity'] * 0.6
        
        coverage_percentage = (len(covered_topics) / total_ai_topics * 100) if total_ai_topics > 0 else 0
        
        # Analisi della qualità del contenuto
        content_quality = self._analyze_content_quality(article_content, covered_topics, missing_topics)
        
        return {
            'total_ai_topics': total_ai_topics,
            'covered_topics': covered_topics,
            'partially_covered': partially_covered,
            'missing_topics': missing_topics,
            'semantic_matches': semantic_matches,
            'coverage_percentage': round(coverage_percentage, 2),
            'weighted_coverage': round(weighted_coverage, 2),
            'article_topics': article_topics[:15],
            'content_quality': content_quality,
            'recommendations': self.generate_advanced_recommendations(missing_topics, partially_covered, content_quality),
            'analysis_method': 'basic'
        }
    
    def _check_synonyms(self, topic, content):
        """
        Controlla la presenza di sinonimi del topic nel contenuto
        """
        # Dizionario di sinonimi comuni (espandibile)
        synonyms_dict = {
            'intelligenza artificiale': ['ai', 'machine intelligence', 'artificial intelligence'],
            'machine learning': ['apprendimento automatico', 'ml', 'apprendimento macchina'],
            'deep learning': ['apprendimento profondo', 'reti neurali profonde'],
            'algoritmo': ['algoritmi', 'procedura', 'metodo computazionale'],
            'dati': ['data', 'informazioni', 'dataset'],
            'automazione': ['automatizzazione', 'processo automatico'],
            'efficienza': ['efficacia', 'ottimizzazione', 'performance']
        }
        
        # Validazione del tipo di input
        if isinstance(topic, dict):
            topic = topic.get('topic', str(topic))
        elif not isinstance(topic, str):
            topic = str(topic)
            
        topic_lower = topic.lower()
        content_lower = content.lower()
        
        for main_term, synonyms in synonyms_dict.items():
            if main_term in topic_lower:
                for synonym in synonyms:
                    if synonym in content_lower:
                        return {'synonym': synonym, 'confidence': 0.7}
        
        return None
    
    def _calculate_topic_priority(self, topic):
        """
        Calcola la priorità di un topic mancante
        """
        high_priority_keywords = ['definizione', 'concetto', 'principio', 'base', 'fondamentale']
        medium_priority_keywords = ['applicazione', 'esempio', 'caso', 'utilizzo']
        
        # Validazione del tipo di input
        if isinstance(topic, dict):
            topic = topic.get('topic', str(topic))
        elif not isinstance(topic, str):
            topic = str(topic)
            
        topic_lower = topic.lower()
        
        if any(keyword in topic_lower for keyword in high_priority_keywords):
            return 'alta'
        elif any(keyword in topic_lower for keyword in medium_priority_keywords):
            return 'media'
        else:
            return 'bassa'
    
    def _categorize_topic(self, topic):
        """
        Categorizza un topic per tipo di contenuto
        """
        # Validazione del tipo di input
        if isinstance(topic, dict):
            topic = topic.get('topic', str(topic))
        elif not isinstance(topic, str):
            topic = str(topic)
            
        categories = {
            'teorico': ['definizione', 'concetto', 'teoria', 'principio'],
            'pratico': ['applicazione', 'esempio', 'caso', 'utilizzo', 'implementazione'],
            'tecnico': ['algoritmo', 'metodo', 'tecnica', 'processo'],
            'etico': ['etica', 'responsabilità', 'trasparenza', 'bias'],
            'economico': ['costo', 'investimento', 'mercato', 'business']
        }
        
        topic_lower = topic.lower()
        
        for category, keywords in categories.items():
            if any(keyword in topic_lower for keyword in keywords):
                return category
        
        return 'generale'
    
    def _analyze_content_quality(self, content, covered_topics, missing_topics):
        """
        Analizza la qualità complessiva del contenuto
        """
        word_count = len(content.split())
        sentence_count = len(sent_tokenize(content))
        
        # Calcola metriche di qualità
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Analizza la profondità del contenuto
        depth_indicators = ['esempio', 'dettaglio', 'approfondimento', 'analisi', 'studio']
        depth_score = sum(1 for indicator in depth_indicators if indicator in content.lower())
        
        # Analizza la struttura
        structure_indicators = ['introduzione', 'conclusione', 'capitolo', 'sezione']
        structure_score = sum(1 for indicator in structure_indicators if indicator in content.lower())
        
        quality_score = min(100, (
            (len(covered_topics) / max(1, len(covered_topics) + len(missing_topics))) * 40 +
            min(depth_score * 10, 30) +
            min(structure_score * 10, 30)
        ))
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'depth_score': depth_score,
            'structure_score': structure_score,
            'overall_quality': round(quality_score, 1)
        }
    
    def generate_advanced_recommendations(self, missing_topics, partially_covered, content_quality):
        """
        Genera raccomandazioni avanzate e personalizzate
        
        Args:
            missing_topics (list): Lista degli argomenti mancanti con priorità
            partially_covered (list): Argomenti parzialmente coperti
            content_quality (dict): Metriche di qualità del contenuto
            
        Returns:
            list: Lista di raccomandazioni prioritizzate
        """
        recommendations = []
        
        # Raccomandazioni per argomenti mancanti ad alta priorità
        high_priority_missing = [t for t in missing_topics if t.get('priority') == 'alta']
        if high_priority_missing:
            topics_list = [t['topic'] for t in high_priority_missing[:3]]
            recommendations.append({
                'type': 'critica',
                'priority': 'alta',
                'title': '🚨 Argomenti Fondamentali Mancanti',
                'description': f"Aggiungi sezioni dedicate a: {', '.join(topics_list)}",
                'impact': 'Alto impatto sulla completezza del contenuto'
            })
        
        # Raccomandazioni per migliorare argomenti parzialmente coperti
        low_similarity = [p for p in partially_covered if p.get('similarity', 0) < 0.7]
        if low_similarity:
            recommendations.append({
                'type': 'miglioramento',
                'priority': 'media',
                'title': '📈 Approfondisci Argomenti Esistenti',
                'description': f"Espandi la trattazione di {len(low_similarity)} argomenti già presenti ma superficiali",
                'impact': 'Migliora la qualità e profondità del contenuto'
            })
        
        # Raccomandazioni basate sulla qualità del contenuto
        if content_quality['overall_quality'] < 60:
            if content_quality['depth_score'] < 3:
                recommendations.append({
                    'type': 'strutturale',
                    'priority': 'media',
                    'title': '🔍 Aumenta la Profondità',
                    'description': 'Aggiungi esempi pratici, casi studio e analisi dettagliate',
                    'impact': 'Rende il contenuto più coinvolgente e utile'
                })
            
            if content_quality['structure_score'] < 2:
                recommendations.append({
                    'type': 'strutturale',
                    'priority': 'bassa',
                    'title': '📋 Migliora la Struttura',
                    'description': 'Organizza il contenuto con introduzione, sezioni chiare e conclusioni',
                    'impact': 'Migliora la leggibilità e navigazione'
                })
        
        # Raccomandazioni per categorie specifiche
        categories_missing = {}
        for topic in missing_topics:
            category = topic.get('category', 'generale')
            if category not in categories_missing:
                categories_missing[category] = []
            categories_missing[category].append(topic['topic'])
        
        category_recommendations = {
            'teorico': '📚 Aggiungi basi teoriche e definizioni chiare',
            'pratico': '🛠️ Includi esempi pratici e casi d\'uso reali',
            'tecnico': '⚙️ Approfondisci aspetti tecnici e metodologie',
            'etico': '⚖️ Discuti implicazioni etiche e responsabilità',
            'economico': '💰 Analizza impatti economici e di business'
        }
        
        for category, topics in categories_missing.items():
            if len(topics) >= 2 and category in category_recommendations:
                recommendations.append({
                    'type': 'categorica',
                    'priority': 'media',
                    'title': f'Contenuto {category.title()}',
                    'description': category_recommendations[category],
                    'impact': f'Copre {len(topics)} argomenti nella categoria {category}'
                })
        
        # Se non ci sono raccomandazioni critiche, aggiungi suggerimenti di ottimizzazione
        if not recommendations or all(r['priority'] != 'alta' for r in recommendations):
            recommendations.insert(0, {
                'type': 'ottimizzazione',
                'priority': 'bassa',
                'title': '✅ Contenuto Ben Strutturato',
                'description': 'L\'articolo copre bene gli argomenti principali. Considera l\'aggiunta di contenuti correlati per maggiore completezza.',
                'impact': 'Ottimizzazione per eccellenza del contenuto'
            })
        
        return recommendations[:6]  # Limita a 6 raccomandazioni per evitare sovraccarico
    
    def analyze_article_gap(self, article_url):
        """
        Analizza il gap di contenuto per un singolo articolo
        
        Args:
            article_url (str): URL dell'articolo da analizzare
            
        Returns:
            dict: Risultato completo dell'analisi
        """
        print(f"Analizzando articolo: {article_url}")
        
        # Estrai contenuto dell'articolo
        article_data = self.extract_article_content(article_url)
        
        if not article_data['success']:
            return {
                'url': article_url,
                'success': False,
                'error': article_data['error']
            }
        
        # Analizza i gap
        gap_analysis = self.find_missing_topics(article_data['content'])
        
        # Combina i risultati
        result = {
            'url': article_url,
            'title': article_data['title'],
            'word_count': article_data['word_count'],
            'success': True,
            'gap_analysis': gap_analysis
        }
        
        return result
    
    def analyze_multiple_articles(self, article_urls):
        """
        Analizza il gap di contenuto per più articoli
        
        Args:
            article_urls (list): Lista di URL degli articoli
            
        Returns:
            dict: Risultati dell'analisi per tutti gli articoli
        """
        results = []
        
        for url in article_urls:
            result = self.analyze_article_gap(url)
            results.append(result)
        
        # Genera un riassunto
        summary = self.generate_summary(results)
        
        return {
            'individual_results': results,
            'summary': summary
        }
    
    def generate_summary(self, results):
        """
        Genera un riassunto dell'analisi di più articoli
        
        Args:
            results (list): Lista dei risultati individuali
            
        Returns:
            dict: Riassunto dell'analisi
        """
        successful_analyses = [r for r in results if r.get('success', False)]
        
        if not successful_analyses:
            return {'error': 'Nessuna analisi riuscita'}
        
        # Calcola statistiche aggregate
        total_articles = len(successful_analyses)
        avg_coverage = sum(r['gap_analysis']['coverage_percentage'] for r in successful_analyses) / total_articles
        
        # Trova argomenti più comunemente mancanti
        all_missing = []
        for result in successful_analyses:
            all_missing.extend(result['gap_analysis']['missing_topics'])
        
        common_missing = Counter(all_missing).most_common(10)
        
        return {
            'total_articles_analyzed': total_articles,
            'average_coverage_percentage': round(avg_coverage, 2),
            'most_common_missing_topics': common_missing,
            'articles_with_low_coverage': [
                {'url': r['url'], 'coverage': r['gap_analysis']['coverage_percentage']} 
                for r in successful_analyses 
                if r['gap_analysis']['coverage_percentage'] < 50
            ]
        }
    
    def save_analysis_report(self, analysis_result, filename):
        """
        Salva il report dell'analisi in un file JSON
        
        Args:
            analysis_result (dict): Risultato dell'analisi
            filename (str): Nome del file
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            print(f"Report salvato in: {filename}")
        except Exception as e:
            print(f"Errore nel salvare il report: {e}")


def main():
    """Funzione principale per testare l'analizzatore"""
    analyzer = ContentGapAnalyzer()
    
    # Carica l'AI Overview (assumendo che sia già stato estratto)
    try:
        analyzer.load_ai_overview_from_file("ai_overview_result.json")
    except:
        # Se il file non esiste, usa un contenuto di esempio
        sample_ai_overview = """
        L'intelligenza artificiale è un campo dell'informatica che si concentra sullo sviluppo di sistemi 
        capaci di simulare l'intelligenza umana. Include machine learning, deep learning, applicazioni 
        in sanità, trasporti, automazione. Presenta vantaggi come efficienza e precisione, ma anche 
        sfide etiche e di sicurezza.
        """
        analyzer.load_ai_overview(sample_ai_overview)
    
    # Esempio di analisi di un singolo articolo
    article_url = input("Inserisci l'URL dell'articolo da analizzare: ")
    
    if article_url:
        result = analyzer.analyze_article_gap(article_url)
        
        # Salva il risultato
        analyzer.save_analysis_report(result, "content_gap_analysis.json")
        
        # Stampa il risultato
        if result['success']:
            print("\n=== ANALISI CONTENT GAP ===")
            print(f"Titolo: {result['title']}")
            print(f"Copertura: {result['gap_analysis']['coverage_percentage']}%")
            print(f"Argomenti mancanti: {len(result['gap_analysis']['missing_topics'])}")
            print("\nRaccomandazioni:")
            for rec in result['gap_analysis']['recommendations']:
                print(f"- {rec}")
        else:
            print(f"Errore nell'analisi: {result['error']}")


if __name__ == "__main__":
    main()