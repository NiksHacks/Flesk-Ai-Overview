# 🚀 Deploy su Railway - AI Overview Analyzer

## 📋 Configurazione Completata

Tutti i file sono stati ottimizzati per il deploy su Railway con **Gemini 2.0 Flash**:

### ✅ File Aggiornati:
- `requirements.txt` - Dipendenze aggiornate con Gemini 2.0 Flash
- `runtime.txt` - Python 3.12.1 per prestazioni ottimali
- `Procfile` - Gunicorn ottimizzato con 2 worker e timeout 120s
- `railway.json` - Configurazione completa con health check
- `.railwayignore` - Esclude file non necessari dal deploy

### 🔧 Configurazioni Railway:

#### 1. Variabili d'Ambiente Richieste:
```
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

#### 2. Impostazioni Deploy:
- **Runtime**: Python 3.12.1
- **Builder**: NIXPACKS (automatico)
- **Workers**: 2 processi Gunicorn
- **Timeout**: 120 secondi
- **Health Check**: Attivo su `/`

### 🚀 Passi per il Deploy:

1. **Connetti Repository**:
   - Vai su [railway.app](https://railway.app)
   - Crea nuovo progetto
   - Connetti questo repository GitHub

2. **Configura Variabili**:
   - Vai in Settings > Variables
   - Aggiungi `GEMINI_API_KEY` con la tua chiave API
   - Le altre variabili sono già configurate in `railway.json`

3. **Deploy Automatico**:
   - Railway rileverà automaticamente i file di configurazione
   - Il deploy partirà automaticamente
   - L'app sarà disponibile su `https://your-app.railway.app`

### ⚡ Ottimizzazioni Implementate:

- **Gemini 2.0 Flash**: Modello più veloce per ridurre timeout
- **Gunicorn Multi-Worker**: 2 processi per gestire più richieste
- **Timeout Esteso**: 120s per analisi SEO complesse
- **Health Check**: Monitoraggio automatico dello stato
- **Cache Ottimizzata**: Gestione memoria migliorata
- **File Ignore**: Deploy più veloce escludendo file inutili

### 🔍 Monitoraggio:

- **Logs**: Visibili nella dashboard Railway
- **Metriche**: CPU, memoria e traffico in tempo reale
- **Health Check**: Verifica automatica ogni 5 minuti
- **Auto-Restart**: Riavvio automatico in caso di errori

### 🛠️ Troubleshooting:

1. **Deploy Fallisce**:
   - Verifica che `GEMINI_API_KEY` sia impostata
   - Controlla i logs per errori specifici

2. **Timeout Errori**:
   - Il timeout è già impostato a 120s
   - Gemini 2.0 Flash dovrebbe essere più veloce

3. **Memoria Insufficiente**:
   - Railway offre 512MB di base
   - L'app è ottimizzata per questo limite

### 📊 Prestazioni Attese:

- **Avvio**: ~30-60 secondi
- **Risposta AI**: ~5-15 secondi (vs 30-60s con Gemini 2.5 Pro)
- **Estrazione AI Overview**: ~10-30 secondi
- **Uptime**: 99.9% con auto-restart

---

**✅ Pronto per il Deploy!** 
Tutti i file sono configurati e ottimizzati per Railway.