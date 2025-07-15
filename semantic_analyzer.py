import google.generativeai as genai
import requests
import json
import time
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging

class SemanticAnalyzer:
    """
    Analizzatore semantico avanzato che utilizza Google Gemini 2.5 Pro per migliorare
    l'accuratezza dell'analisi del content gap
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None, use_local_models: bool = True):
        """
        Inizializza l'analizzatore semantico con Google Gemini
        
        Args:
            gemini_api_key: Chiave API Google Gemini (opzionale, usa chiave integrata se None)
            use_local_models: Se utilizzare modelli locali per l'embedding
        """
        # Usa la chiave API integrata se non fornita
        self.gemini_api_key = gemini_api_key or "AIzaSyDXB8Lj2gamg7SEYmxvZ_uEs7JX3RKZ9yY"
        self.use_local_models = use_local_models
        
        # Configura logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Configura Google Gemini con chiave integrata
        try:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.5-pro')
            self.logger.info("✅ Google Gemini 2.5 Pro configurato")
        except Exception as e:
            self.logger.error(f"❌ Errore nella configurazione di Gemini: {e}")
            self.model = None
    
    def get_embeddings_gemini(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings usando Google Gemini
        
        Args:
            texts: Lista di testi da convertire in embeddings
            
        Returns:
            Lista di embeddings
        """
        if not self.model:
            return []
        
        try:
            embeddings = []
            for text in texts:
                # Usa Gemini per generare embedding semantico
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="semantic_similarity"
                )
                embeddings.append(result['embedding'])
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"❌ Errore nella generazione di embeddings Gemini: {e}")
            return []
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calcola la similarità semantica tra due testi usando Gemini
        
        Args:
            text1: Primo testo
            text2: Secondo testo
            
        Returns:
            Score di similarità (0-1)
        """
        if not self.model:
            return 0.0
        
        try:
            # Genera embeddings per entrambi i testi
            embeddings = self.get_embeddings_gemini([text1, text2])
            
            if len(embeddings) == 2:
                # Calcola similarità coseno
                similarity = cosine_similarity(
                    [embeddings[0]], [embeddings[1]]
                )[0][0]
                return max(0.0, min(1.0, similarity))
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"❌ Errore nel calcolo della similarità: {e}")
            return 0.0
    
    def find_semantic_matches(self, target_topics: List[str], article_content: str, 
                            threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Trova corrispondenze semantiche tra argomenti target e contenuto articolo
        
        Args:
            target_topics: Lista di argomenti da cercare
            article_content: Contenuto dell'articolo
            threshold: Soglia di similarità minima
            
        Returns:
            Lista di corrispondenze semantiche
        """
        matches = []
        
        if not self.model:
            return matches
        
        try:
            # Dividi l'articolo in paragrafi
            paragraphs = [p.strip() for p in article_content.split('\n') if p.strip()]
            
            for topic in target_topics:
                best_match = {
                    'topic': topic,
                    'similarity': 0.0,
                    'matched_content': '',
                    'match_type': 'none'
                }
                
                # Cerca la migliore corrispondenza nei paragrafi
                for paragraph in paragraphs:
                    if len(paragraph) > 50:  # Solo paragrafi significativi
                        similarity = self.calculate_semantic_similarity(topic, paragraph)
                        
                        if similarity > best_match['similarity']:
                            best_match.update({
                                'similarity': similarity,
                                'matched_content': paragraph[:200] + '...',
                                'match_type': self._classify_match_type(similarity)
                            })
                
                if best_match['similarity'] >= threshold:
                    matches.append(best_match)
            
            return matches
            
        except Exception as e:
            self.logger.error(f"❌ Errore nella ricerca di corrispondenze semantiche: {e}")
            return []
    
    def _classify_match_type(self, similarity: float) -> str:
        """
        Classifica il tipo di corrispondenza basato sulla similarità
        
        Args:
            similarity: Score di similarità
            
        Returns:
            Tipo di corrispondenza
        """
        if similarity >= 0.9:
            return 'exact'
        elif similarity >= 0.7:
            return 'high'
        elif similarity >= 0.5:
            return 'medium'
        elif similarity >= 0.3:
            return 'low'
        else:
            return 'none'
    
    def analyze_topic_relevance(self, missing_topics: List[str], article_content: str) -> List[Dict[str, Any]]:
        """
        Analizza la rilevanza dei topic mancanti rispetto al contenuto dell'articolo
        
        Args:
            missing_topics: Lista di argomenti mancanti
            article_content: Contenuto dell'articolo
            
        Returns:
            Lista di topic con score di rilevanza
        """
        if not self.model:
            return [{'topic': topic, 'relevance_score': 0.5, 'priority': 'medium'} for topic in missing_topics]
        
        try:
            # Analizza ogni topic mancante
            analyzed_topics = []
            
            for topic in missing_topics:
                # Calcola similarità semantica con il contenuto
                similarity = self.calculate_semantic_similarity(topic, article_content[:1000])
                
                # Determina priorità basata sulla similarità
                if similarity > 0.7:
                    priority = 'high'
                elif similarity > 0.4:
                    priority = 'medium'
                else:
                    priority = 'low'
                
                analyzed_topics.append({
                    'topic': topic,
                    'relevance_score': round(similarity, 3),
                    'priority': priority
                })
            
            # Ordina per rilevanza
            analyzed_topics.sort(key=lambda x: x['relevance_score'], reverse=True)
            return analyzed_topics
            
        except Exception as e:
            self.logger.error(f"❌ Errore nell'analisi di rilevanza: {e}")
            return [{'topic': topic, 'relevance_score': 0.5, 'priority': 'medium'} for topic in missing_topics]
    
    def _calculate_priority(self, relevance_score: int) -> str:
        """
        Calcola la priorità basata sul punteggio di rilevanza
        
        Args:
            relevance_score: Punteggio di rilevanza (0-100)
            
        Returns:
            Livello di priorità
        """
        if relevance_score >= 80:
            return 'high'
        elif relevance_score >= 60:
            return 'medium'
        elif relevance_score >= 40:
            return 'low'
        else:
            return 'very_low'
    
    def generate_content_suggestions(self, missing_topics: List[str], 
                                   article_content: str, ai_overview_content: str = "") -> List[Dict[str, Any]]:
        """
        Genera suggerimenti di contenuto dettagliati per i topic mancanti
        
        Args:
            missing_topics: Lista di argomenti mancanti
            article_content: Contenuto dell'articolo esistente
            ai_overview_content: Contenuto dell'AI Overview per contesto
            
        Returns:
            Lista di suggerimenti dettagliati
        """
        if not self.model:
            return self._generate_basic_suggestions(missing_topics)
        
        try:
            suggestions = []
            
            # Genera un'analisi complessiva prima
            overview_prompt = f"""
            Sei un esperto content strategist e SEO analyst. Analizza con precisione l'articolo esistente confrontandolo con l'AI Overview di riferimento per identificare gap critici di contenuto.
            
            ## ARTICOLO DA ANALIZZARE:
            {article_content[:1200]}
            
            ## AI OVERVIEW DI RIFERIMENTO (STANDARD QUALITÀ):
            {ai_overview_content[:800]}
            
            ## ARGOMENTI POTENZIALMENTE MANCANTI:
            {', '.join(missing_topics[:10])}
            
            ## COMPITO:
            Esegui un'analisi comparativa dettagliata e fornisci un'analisi strutturata in formato JSON VALIDO.
            
            ## CRITERI DI VALUTAZIONE:
            1. **Completezza**: Quanto l'articolo copre gli argomenti dell'AI Overview
            2. **Profondità**: Livello di dettaglio e approfondimento
            3. **Rilevanza**: Pertinenza degli argomenti trattati
            4. **Struttura**: Organizzazione logica del contenuto
            5. **Valore aggiunto**: Informazioni uniche rispetto all'AI Overview
            
            ## FORMATO JSON RICHIESTO (OBBLIGATORIO):
            {{
                "gap_analysis": "Analisi dettagliata dei gap più critici identificati (max 200 caratteri)",
                "content_strategy": "Strategia specifica per migliorare l'articolo con azioni concrete (max 250 caratteri)",
                "priority_topics": ["topic1", "topic2", "topic3"],
                "completeness_score": numero_da_0_a_100,
                "depth_score": numero_da_0_a_100,
                "critical_gaps": ["gap1", "gap2", "gap3"],
                "improvement_areas": ["area1", "area2", "area3"]
            }}
            
            ## REGOLE OBBLIGATORIE:
            - Fornisci SOLO il JSON valido, senza testo aggiuntivo
            - I punteggi devono essere numeri interi da 0 a 100
            - Massimo 3 elementi per ogni array
            - Usa descrizioni concise ma specifiche
            - Basa l'analisi sui contenuti forniti, non su conoscenze generali
            """
            
            overview_response = self.model.generate_content(overview_prompt)
            
            # Genera suggerimenti specifici per i topic più importanti
            for i, topic in enumerate(missing_topics[:8]):  # Aumentato a 8 topic
                prompt = f"""
                Sei un content strategist esperto. Analizza il gap specifico e genera una raccomandazione precisa e implementabile.
                
                ## CONTESTO ARTICOLO ESISTENTE:
                {article_content[:1000]}
                
                ## AI OVERVIEW STANDARD DI RIFERIMENTO:
                {ai_overview_content[:600]}
                
                ## ARGOMENTO MANCANTE DA INTEGRARE:
                "{topic}"
                
                ## COMPITO:
                Genera una raccomandazione dettagliata, specifica e immediatamente implementabile per integrare questo argomento nell'articolo esistente.
                
                ## ANALISI RICHIESTA:
                1. **COSA AGGIUNGERE**: Contenuto specifico e dettagliato da includere
                2. **DOVE POSIZIONARE**: Sezione precisa dell'articolo dove inserire il contenuto
                3. **COME SVILUPPARE**: 2-3 punti chiave concreti da trattare
                4. **VALORE STRATEGICO**: Beneficio SEO e per l'utente di questa integrazione
                
                ## FORMATO RISPOSTA OBBLIGATORIO:
                COSA: [Descrizione specifica del contenuto da aggiungere - max 40 parole]
                DOVE: [Posizione esatta nell'articolo - max 15 parole]
                COME: [2-3 punti chiave da sviluppare - max 50 parole]
                VALORE: [Beneficio SEO e utente - max 30 parole]
                
                ## VINCOLI:
                - Massimo 135 parole totali
                - Sii specifico e actionable
                - Considera la struttura esistente dell'articolo
                - Focus su implementazione pratica
                - Evita consigli generici
                """
                
                response = self.model.generate_content(prompt)
                suggestion_text = response.text.strip()
                
                # Analizza rilevanza del topic
                relevance = self.calculate_semantic_similarity(topic, article_content[:1000])
                
                # Determina priorità basata su posizione e rilevanza
                if i < 3 or relevance > 0.7:
                    priority = 'alta'
                    impact = 'Alto impatto sulla completezza del contenuto'
                elif i < 6 or relevance > 0.5:
                    priority = 'media'
                    impact = 'Medio impatto sulla qualità del contenuto'
                else:
                    priority = 'bassa'
                    impact = 'Basso impatto, contenuto opzionale'
                
                suggestions.append({
                    'topic': topic,
                    'suggestion': suggestion_text,
                    'relevance_score': round(relevance, 3),
                    'priority': priority,
                    'impact': impact,
                    'type': 'critica' if i < 3 else 'strutturale' if i < 6 else 'generale'
                })
                
                # Pausa per evitare rate limiting
                time.sleep(0.5)
            
            # Ordina per priorità e rilevanza
            suggestions.sort(key=lambda x: (x['priority'] == 'alta', x['relevance_score']), reverse=True)
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"❌ Errore nella generazione suggerimenti: {e}")
            return self._generate_basic_suggestions(missing_topics)
    
    def _generate_basic_suggestions(self, missing_topics: List[str]) -> List[Dict[str, Any]]:
        """
        Genera suggerimenti di base quando Gemini non è disponibile
        
        Args:
            missing_topics: Lista di argomenti mancanti
            
        Returns:
            Lista di suggerimenti di base
        """
        suggestions = []
        
        for topic in missing_topics:
            suggestions.append({
                'topic': topic,
                'suggestion': f"Considera di aggiungere una sezione dedicata a '{topic}' per migliorare la completezza dell'articolo.",
                'relevance_score': 0.5,
                'priority': 'medium'
            })
        
        return suggestions
    
    def _categorize_topic(self, topic: str) -> str:
        """
        Categorizza un argomento
        
        Args:
            topic: Argomento da categorizzare
            
        Returns:
            Categoria dell'argomento
        """
        # Validazione del tipo di input
        if isinstance(topic, dict):
            topic = topic.get('topic', str(topic))
        elif not isinstance(topic, str):
            topic = str(topic)
            
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['come', 'guida', 'tutorial', 'passo']):
            return 'tutorial'
        elif any(word in topic_lower for word in ['cos\'è', 'definizione', 'significato']):
            return 'definizione'
        elif any(word in topic_lower for word in ['vantaggi', 'benefici', 'pro']):
            return 'vantaggi'
        elif any(word in topic_lower for word in ['esempio', 'caso', 'pratico']):
            return 'esempi'
        elif any(word in topic_lower for word in ['problema', 'errore', 'soluzione']):
            return 'problemi'
        else:
            return 'generale'
    
    def batch_similarity_analysis(self, topics: List[str], 
                                content_chunks: List[str]) -> Dict[str, Any]:
        """
        Esegue un'analisi di similarità in batch
        
        Args:
            topics: Lista di argomenti
            content_chunks: Lista di chunk di contenuto
            
        Returns:
            Risultati dell'analisi batch
        """
        if not self.model:
            return {}
        
        try:
            # Genera embeddings per tutti i topics e chunks
            all_texts = topics + content_chunks
            embeddings = self.get_embeddings_gemini(all_texts)
            
            if len(embeddings) != len(all_texts):
                return {}
            
            topic_embeddings = embeddings[:len(topics)]
            content_embeddings = embeddings[len(topics):]
            
            # Calcola matrice di similarità
            similarity_matrix = cosine_similarity(topic_embeddings, content_embeddings)
            
            results = {
                'similarity_matrix': similarity_matrix.tolist(),
                'topics': topics,
                'content_chunks': content_chunks,
                'best_matches': []
            }
            
            # Trova le migliori corrispondenze per ogni topic
            for i, topic in enumerate(topics):
                best_chunk_idx = np.argmax(similarity_matrix[i])
                best_similarity = similarity_matrix[i][best_chunk_idx]
                
                results['best_matches'].append({
                    'topic': topic,
                    'best_chunk': content_chunks[best_chunk_idx],
                    'similarity': float(best_similarity),
                    'match_type': self._classify_match_type(best_similarity)
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Errore nell'analisi batch: {e}")
            return {}
    
    def generate_content_suggestions(self, ai_overview_content: str, article_content: str, missing_topics: List[str]) -> str:
        """
        Genera suggerimenti personalizzati per migliorare il contenuto basandosi sull'AI Overview
        e sui topic mancanti identificati
        
        Args:
            ai_overview_content: Contenuto dell'AI Overview
            article_content: Contenuto dell'articolo analizzato
            missing_topics: Lista degli argomenti mancanti
            
        Returns:
            Suggerimenti personalizzati generati da Gemini AI
        """
        if not self.model:
            return "Gemini AI non disponibile per generare suggerimenti."
        
        try:
            # Limita il numero di topic mancanti per evitare prompt troppo lunghi
            limited_topics = missing_topics[:10] if len(missing_topics) > 10 else missing_topics
            
            prompt = f"""
            Sei un esperto SEO e content strategist con oltre 10 anni di esperienza. Il tuo compito è fornire suggerimenti specifici e actionable per migliorare l'articolo basandoti sull'analisi comparativa con l'AI Overview.
            
            ## CONTESTO DELL'ANALISI
            **AI OVERVIEW (contenuto di riferimento):**
            {ai_overview_content[:2000]}...
            
            **ARTICOLO ANALIZZATO (estratto):**
            {article_content[:1500]}...
            
            **ARGOMENTI MANCANTI IDENTIFICATI:**
            {', '.join(limited_topics)}
            
            ## ISTRUZIONI DETTAGLIATE
            Analizza sistematicamente il gap tra l'articolo e l'AI Overview e fornisci suggerimenti che:
            
            1. **COLMINO I GAP SPECIFICI**: Integrano gli argomenti mancanti identificati
            2. **MIGLIORINO IL RANKING SEO**: Ottimizzano per search intent e keyword relevance
            3. **AUMENTINO IL VALORE UTENTE**: Aggiungono informazioni utili e actionable
            4. **SIANO IMPLEMENTABILI**: Forniscono step concreti e realistici
            5. **RISPETTINO L'INTENT**: Mantengono coerenza con l'obiettivo dell'articolo
            
            ## STRUTTURA RICHIESTA DELLA RISPOSTA
            
            ### 🎯 OPPORTUNITÀ PRINCIPALI
            - Identifica le 3-5 opportunità più importanti
            - Spiega il potenziale impatto di ciascuna
            
            ### 📝 SUGGERIMENTI SPECIFICI PER ARGOMENTO
            Per ogni argomento mancante:
            - **Cosa aggiungere**: Contenuto specifico da integrare
            - **Dove posizionarlo**: Sezione ottimale nell'articolo
            - **Come svilupparlo**: Approccio e struttura consigliata
            - **Parole chiave target**: Keywords correlate da includere
            
            ### 🔍 OTTIMIZZAZIONI SEO
            - Miglioramenti per title e meta description
            - Struttura heading ottimizzata
            - Internal linking opportunities
            - Featured snippet optimization
            
            ### 📊 STRATEGIE PER COLMARE I GAP
            - Priorità di implementazione (alta/media/bassa)
            - Stima effort richiesto
            - Impatto atteso su ranking e traffico
            - Timeline suggerita per l'implementazione
            
            ## VINCOLI E REQUISITI
            - Mantieni un tono professionale ma accessibile
            - Fornisci sempre esempi concreti quando possibile
            - Basa ogni suggerimento sui dati dell'analisi
            - Evita consigli generici, sii specifico e actionable
            - Rispondi sempre in italiano
            - Limita la risposta a 800-1000 parole per mantenere focus
            
            Fornisci una risposta completa e strutturata seguendo il formato richiesto.
            """
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                return "Non è stato possibile generare suggerimenti in questo momento."
                
        except Exception as e:
            self.logger.error(f"❌ Errore nella generazione di suggerimenti: {e}")
            return f"Errore nella generazione di suggerimenti: {str(e)}"