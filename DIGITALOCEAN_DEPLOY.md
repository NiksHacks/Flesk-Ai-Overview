# Deploy su DigitalOcean App Platform

Questa guida spiega come deployare l'applicazione Flesk AI Overview su DigitalOcean App Platform.

## Prerequisiti

1. Account DigitalOcean
2. Repository GitHub con il codice dell'applicazione
3. API Key di Google Gemini

## Configurazione

### 1. Preparazione del Repository

Assicurati che il repository contenga:
- `Dockerfile` - Configurazione del container
- `.do/app.yaml` - Configurazione dell'app DigitalOcean
- `.dockerignore` - File da escludere dal build
- `requirements.txt` - Dipendenze Python

### 2. Deployment

#### Opzione A: Deploy tramite GitHub (Raccomandato)

1. Vai su [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Clicca "Create App"
3. Seleziona "GitHub" come source
4. Autorizza DigitalOcean ad accedere al tuo repository
5. Seleziona il repository `Flesk-Ai-Overview`
6. Seleziona il branch `main`
7. DigitalOcean rileverà automaticamente il `Dockerfile`
8. Configura le variabili d'ambiente (vedi sotto)
9. Clicca "Create Resources"

#### Opzione B: Deploy tramite doctl CLI

```bash
# Installa doctl
brew install doctl  # macOS
# oppure scarica da https://github.com/digitalocean/doctl/releases

# Autentica
doctl auth init

# Deploy l'app
doctl apps create .do/app.yaml
```

### 3. Configurazione Variabili d'Ambiente

Nella dashboard di DigitalOcean, configura:

- `GEMINI_API_KEY`: La tua API key di Google Gemini (tipo: SECRET)

### 4. Configurazione Dominio (Opzionale)

1. Vai nella sezione "Settings" dell'app
2. Clicca "Domains"
3. Aggiungi il tuo dominio personalizzato
4. Configura i record DNS come indicato

## Caratteristiche del Deployment

- **Runtime**: Docker con Python 3.11.7
- **Playwright**: Chromium installato e configurato
- **NLTK**: Dati scaricati automaticamente
- **Xvfb**: Display virtuale per browser headless
- **Auto-scaling**: Configurato per basic-xxs instance
- **Health Check**: Endpoint `/` monitorato

## Troubleshooting

### Build Fallisce
- Verifica che il `Dockerfile` sia presente nella root
- Controlla i log di build nella dashboard DigitalOcean
- Assicurati che `requirements.txt` sia valido

### Playwright Non Funziona
- Il `Dockerfile` include tutte le dipendenze necessarie
- Xvfb è configurato per il display virtuale
- Chromium è installato con `playwright install`

### Variabili d'Ambiente
- Verifica che `GEMINI_API_KEY` sia configurata come SECRET
- Controlla che non ci siano spazi extra nei valori

## Costi Stimati

- **basic-xxs**: $5/mese per 512MB RAM, 1 vCPU
- **Bandwidth**: 100GB inclusi
- **Build time**: Gratuito fino a 400 minuti/mese

## Monitoraggio

- **Logs**: Disponibili nella dashboard DigitalOcean
- **Metrics**: CPU, memoria, richieste monitorate automaticamente
- **Alerts**: Configurabili per downtime o errori

## Aggiornamenti

L'app si aggiorna automaticamente ad ogni push su `main` grazie a `deploy_on_push: true`.

Per aggiornamenti manuali:
```bash
doctl apps create-deployment <app-id>
```