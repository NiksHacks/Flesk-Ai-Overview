# AI Overview & Content Gap Analyzer

Sistema automatizzato per l'estrazione di contenuti dall'AI Overview di Google e l'analisi del content gap degli articoli.

## 🎯 Funzionalità

Il progetto si divide in **due funzioni principali**:

### 1. **Automazione Browser & Estrazione AI Overview**
- Automatizza la navigazione su Google Search
- Estrae automaticamente i contenuti dall'AI Overview
- Clicca il pulsante "Mostra altro" per ottenere il contenuto completo
- Utilizza selettori CSS avanzati per identificare l'AI Overview
- Salva i risultati in formato JSON

### 2. **Content Gap Analysis**
- Analizza articoli tramite URL
- Confronta il contenuto degli articoli con l'AI Overview estratto
- Identifica argomenti mancanti negli articoli
- Genera raccomandazioni per migliorare il contenuto
- Calcola percentuali di copertura degli argomenti
- Supporta analisi di articoli singoli o multipli

### 3. **🤖 Analisi Semantica Avanzata (Nuovo!)**
- **Analisi Base**: Utilizza algoritmi di similarità testuale tradizionali
- **Analisi Avanzata**: Integra Google Gemini API per analisi semantica di precisione superiore
- **Embedding Semantici**: Calcola similarità semantica profonda tra contenuti
- **Raccomandazioni Intelligenti**: Genera suggerimenti contestuali basati su AI
- **Categorizzazione Automatica**: Classifica automaticamente i topic mancanti
- **Analisi di Rilevanza**: Valuta l'importanza semantica di ogni argomento

## 🚀 Installazione

### Prerequisiti
- Python 3.8 o superiore
- Google Chrome o Chromium
- Connessione internet

### 1. Clona o scarica il progetto
```bash
cd "Ai Overview+Content GAP"
```

### 2. Installa le dipendenze
```bash
pip install -r requirements.txt
```

### 3. Installa Chrome (se non già presente)
**macOS:**
```bash
brew install --cask google-chrome
```

**Ubuntu/Debian:**
```bash
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable
```

### 4. Configurazione Analisi Semantica Avanzata (Opzionale)
Per utilizzare l'analisi semantica avanzata, è necessaria una API key di Google Gemini:

1. **Ottieni una API key Google Gemini**:
   - Vai su [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Crea un account o accedi
   - Genera una nuova API key

2. **Configura la API key**:
   - Nell'interfaccia Streamlit: inserisci la key nella sidebar
   - Oppure imposta la variabile d'ambiente: `export GEMINI_API_KEY="your-key-here"`

3. **Abilita l'analisi avanzata**:
   - Spunta la checkbox "Abilita analisi semantica avanzata" nella sidebar
   - Il sistema utilizzerà automaticamente Google Gemini 2.5 Pro per analisi più precise

> **Nota**: L'analisi base funziona senza API key, ma l'analisi avanzata offre precisione significativamente superiore.

## 📖 Utilizzo

### Modalità Interattiva (Consigliata)
```bash
python main.py
```

Il sistema presenta un menu interattivo con le seguenti opzioni:

1. **Estrai AI Overview da Google** - Automatizza la ricerca e l'estrazione
2. **Analizza Content Gap di un articolo** - Analizza un singolo URL
3. **Analizza Content Gap di più articoli** - Analisi batch di più URL
4. **Workflow completo** - Estrazione + Analisi in sequenza
5. **Visualizza AI Overview salvato** - Mostra il contenuto estratto

### Utilizzo Programmatico

#### Estrazione AI Overview
```python
from ai_overview_extractor import AIOverviewExtractor

# Inizializza l'estrattore
extractor = AIOverviewExtractor(headless=True)

# Estrai AI Overview
result = extractor.extract_ai_overview_from_query("intelligenza artificiale")

# Salva il risultato
extractor.save_to_file(result, "ai_overview.json")
extractor.close()

if result["found"]:
    print("AI Overview estratto:", result["full_content"])
```

#### Analisi Content Gap
```python
from content_gap_analyzer import ContentGapAnalyzer

# Analisi Base
analyzer = ContentGapAnalyzer()

# Analisi Semantica Avanzata (con Google Gemini API)
analyzer_advanced = ContentGapAnalyzer(
    gemini_api_key="your-gemini-api-key",
    use_semantic_analysis=True
)

# Carica l'AI Overview precedentemente estratto
analyzer.load_ai_overview_from_file("ai_overview.json")

# Analizza un articolo
result = analyzer.analyze_article_gap("https://esempio.com/articolo")

if result['success']:
    gap = result['gap_analysis']
    print(f"Copertura: {gap['coverage_percentage']}%")
    print(f"Metodo: {gap['analysis_method']}")
    print(f"Argomenti mancanti: {gap['missing_topics']}")
    print(f"Raccomandazioni: {gap['recommendations']}")
```

## 🔧 Configurazione Avanzata

### Selettori CSS Personalizzati
Per adattare il sistema a cambiamenti nell'interfaccia di Google, modifica i selettori in `ai_overview_extractor.py`:

```python
ai_overview_selectors = [
    "[data-attrid='wa:/description']",
    "[data-attrid*='overview']",
    ".kp-blk",
    # Aggiungi nuovi selettori qui
]
```

### Modalità Headless
Per eseguire il browser in background (senza interfaccia grafica):
```python
extractor = AIOverviewExtractor(headless=True)
```

### Timeout Personalizzati
Modifica i timeout in base alla velocità della connessione:
```python
# In ai_overview_extractor.py
WebDriverWait(self.driver, 15)  # Aumenta da 10 a 15 secondi
```

## 📁 Struttura File

```
Ai Overview+Content GAP/
├── main.py                     # Script principale con menu interattivo
├── ai_overview_extractor.py    # Funzione 1: Estrazione AI Overview
├── content_gap_analyzer.py     # Funzione 2: Analisi Content Gap
├── requirements.txt            # Dipendenze Python
├── README.md                   # Documentazione
├── ai_overview_result.json     # AI Overview estratto (generato)
└── *_gap_analysis.json         # Report analisi (generati)
```

## 📊 Output e Report

### AI Overview Result (JSON)
```json
{
  "found": true,
  "text": "Testo base dell'AI Overview",
  "expanded_text": "Testo dopo aver cliccato 'Mostra altro'",
  "full_content": "Contenuto completo estratto"
}
```

### Content Gap Analysis (JSON)
```json
{
  "url": "https://esempio.com/articolo",
  "title": "Titolo dell'articolo",
  "word_count": 1500,
  "gap_analysis": {
    "coverage_percentage": 75.5,
    "covered_topics": ["intelligenza artificiale", "machine learning"],
    "missing_topics": ["deep learning", "etica AI"],
    "recommendations": ["Aggiungi sezione su deep learning"]
  }
}
```

## 🛠️ Risoluzione Problemi

### Chrome non trovato
```bash
# Verifica installazione Chrome
which google-chrome
# o
which chromium-browser
```

### Errori di timeout
- Aumenta i timeout nel codice
- Verifica la connessione internet
- Prova con modalità non-headless per debug

### AI Overview non trovato
- Google potrebbe aver cambiato i selettori CSS
- Prova con query diverse
- Verifica che l'AI Overview sia disponibile per quella query

### Errori di parsing articoli
- Alcuni siti potrebbero bloccare il web scraping
- Verifica che l'URL sia accessibile
- Alcuni siti richiedono JavaScript (considera Selenium per questi casi)

## 🔄 Aggiornamenti

Google aggiorna frequentemente la sua interfaccia. Se il sistema smette di funzionare:

1. Ispeziona la pagina di Google per nuovi selettori CSS
2. Aggiorna i selettori in `ai_overview_extractor.py`
3. Testa con diverse query
4. Considera l'uso di selettori più generici

## 📝 Note Tecniche

- **Browser Engine**: Selenium WebDriver con Chrome
- **NLP**: NLTK per elaborazione testo
- **Web Scraping**: BeautifulSoup + Requests
- **Compatibilità**: Python 3.8+, macOS/Linux/Windows
- **Performance**: ~10-30 secondi per estrazione AI Overview, ~5-15 secondi per analisi articolo

## 🤝 Contributi

Per migliorare il sistema:
1. Testa con diverse query e siti web
2. Aggiorna i selettori CSS quando necessario
3. Migliora gli algoritmi di analisi del testo
4. Aggiungi supporto per nuovi formati di contenuto

## ⚖️ Disclaimer

Questo strumento è per scopi educativi e di ricerca. Rispetta sempre i termini di servizio dei siti web e le politiche di rate limiting.