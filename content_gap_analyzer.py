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
    
    def __init__(self, gemini_api_key: Optional[str] = None, use_semantic_analysis: bool = False):
        """
        Inizializza l'analizzatore
        
        Args:
            gemini_api_key: Chiave API Google Gemini (usa chiave integrata se None)
            use_semantic_analysis: Se utilizzare l'analisi semantica avanzata (default: False per performance)
        """
        self.ai_overview_content = ""
        self.ai_overview_topics = []
        # Disabilita l'analisi semantica per evitare timeout di memoria
        self.use_semantic_analysis = False
        self.semantic_analyzer = None
        print("ℹ️ Utilizzo analisi base ottimizzata per performance")
        
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
        Trova gli argomenti dell'AI Overview che mancano nell'articolo (analisi base)
        
        Args:
            article_content (str): Contenuto dell'articolo
            
        Returns:
            dict: Analisi dei gap di contenuto
        """
        if not self.ai_overview_content:
            return {'error': 'AI Overview non caricato'}
        
        article_topics = self.extract_topics(article_content)
        
        print("📊 Utilizzo analisi base...")
        return self._analyze_with_basic_method(article_content, article_topics)
    
    def analyze_content_gaps(self, articles_data):
        """
        Analizza i gap di contenuto tra gli articoli e l'AI Overview (versione semplificata)
        
        Args:
            articles_data (list): Lista di dati degli articoli estratti
            
        Returns:
            dict: Risultati dell'analisi dei gap
        """
        if not self.ai_overview_content:
            return {
                'error': 'AI Overview non caricato. Usa load_ai_overview() prima di analizzare.'
            }
        
        results = []
        
        for article in articles_data:
            if not article.get('success', False):
                results.append({
                    'url': article.get('url', ''),
                    'error': article.get('error', 'Errore sconosciuto'),
                    'success': False
                })
                continue
            
            # Estrai argomenti dall'articolo
            article_topics = self.extract_topics(article['content'])
            
            # Usa solo analisi base
            gap_analysis = self._analyze_with_basic_method(article['content'], article_topics)
            
            # Aggiungi informazioni dell'articolo
            gap_analysis.update({
                'url': article['url'],
                'title': article['title'],
                'word_count': article['word_count'],
                'success': True
            })
            
            results.append(gap_analysis)
        
        return {
            'ai_overview_summary': {
                'content_length': len(self.ai_overview_content),
                'total_topics': len(self.ai_overview_topics),
                'topics_preview': self.ai_overview_topics[:5]
            },
            'articles_analysis': results,
            'total_articles': len(articles_data),
            'successful_analyses': len([r for r in results if r.get('success', False)])
        }
    

    

    
    def _generate_basic_recommendations(self, missing_topics):
        """
        Genera raccomandazioni base senza API esterne
        """
        recommendations = []
        
        for topic in missing_topics[:5]:  # Limita a 5 raccomandazioni
            topic_str = topic if isinstance(topic, str) else topic.get('topic', str(topic))
            recommendations.append({
                'type': 'generale',
                'priority': 'media',
                'title': f'Aggiungi contenuto su: {topic_str}',
                'description': f'Includi una sezione dedicata a {topic_str}',
                'impact': 'Migliora la completezza del contenuto'
            })
        
        return recommendations
    
    def _analyze_with_basic_method(self, article_content: str, article_topics: List[str]) -> Dict[str, Any]:
        """
        Analisi base semplificata per performance ottimali
        """
        missing_topics = []
        covered_topics = []
        
        # Converti tutto in lowercase per confronti case-insensitive
        article_content_lower = article_content.lower()
        
        # Limita il numero di topic AI da analizzare per performance
        limited_ai_topics = self.ai_overview_topics[:10] if len(self.ai_overview_topics) > 10 else self.ai_overview_topics
        
        for ai_topic in limited_ai_topics:
            ai_topic_str = ai_topic if isinstance(ai_topic, str) else str(ai_topic)
            ai_topic_lower = ai_topic_str.lower()
            
            # Solo controllo esatto per performance
            if ai_topic_lower in article_content_lower:
                covered_topics.append({
                    'topic': ai_topic,
                    'match_type': 'exact',
                    'confidence': 1.0
                })
            else:
                missing_topics.append({
                    'topic': ai_topic,
                    'priority': 'media',
                    'category': 'generale'
                })
        
        # Calcola statistiche base
        total_ai_topics = len(limited_ai_topics)
        coverage_percentage = (len(covered_topics) / total_ai_topics * 100) if total_ai_topics > 0 else 0
        
        # Genera raccomandazioni base
        recommendations = self._generate_basic_recommendations(missing_topics)
        
        return {
            'total_ai_topics': total_ai_topics,
            'covered_topics': covered_topics,
            'missing_topics': missing_topics,
            'coverage_percentage': round(coverage_percentage, 2),
            'article_topics': article_topics[:5],  # Limita per performance
            'recommendations': recommendations,
            'analysis_method': 'basic_simplified'
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
    

    

    
    def _generate_basic_recommendations(self, missing_topics):
        """
        Genera raccomandazioni base senza API esterne
        """
        recommendations = []
        
        for topic in missing_topics[:5]:  # Limita a 5 raccomandazioni
            topic_str = topic if isinstance(topic, str) else topic.get('topic', str(topic))
            recommendations.append({
                'type': 'generale',
                'priority': 'media',
                'title': f'Aggiungi contenuto su: {topic_str}',
                'description': f'Includi una sezione dedicata a {topic_str}',
                'impact': 'Migliora la completezza del contenuto'
            })
        
        return recommendations
    

    
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