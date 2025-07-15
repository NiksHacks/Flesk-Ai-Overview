#!/usr/bin/env python3
"""
Funzione 1: Automatizzazione del browser per estrarre contenuti dall'AI Overview di Google

Questo script utilizza Playwright (2025) per automatizzare il browser, navigare su Google,
eseguire una ricerca e estrarre il contenuto dell'AI Overview incluso il testo
espanso dopo aver cliccato "Mostra altro".

Playwright è stato scelto come migliore soluzione per il 2025 rispetto a Selenium/Puppeteer
per la sua robustezza nella gestione dei popup e migliori performance.
"""

import time
import json
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

class AIOverviewExtractor:
    def __init__(self, headless=False):
        """
        Inizializza l'estrattore AI Overview con Playwright (2025)
        
        Args:
            headless (bool): Se True, esegue il browser in modalità headless
        """
        self.browser = None
        self.page = None
        self.headless = headless
        self.playwright = None
        self.setup_browser()
    
    def setup_browser(self):
        """Configura Playwright con le migliori opzioni per gestire popup Google (2025)"""
        try:
            print("🚀 Inizializzando Playwright (2025)...")
            self.playwright = sync_playwright().start()
            
            # Opzioni browser ottimizzate per gestire popup di consenso Google
            browser_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-default-apps',
                '--disable-sync',
                '--disable-translate',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-field-trial-config',
                '--disable-back-forward-cache',
                '--disable-ipc-flooding-protection',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-popup-blocking',  # Importante per gestire popup
                '--disable-notifications',   # Disabilita notifiche
                '--disable-infobars',        # Disabilita barre info
                '--disable-save-password-bubble',  # Disabilita popup password
            ]
            
            # Avvia browser Chromium
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # Crea contesto con impostazioni anti-rilevamento
            context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='it-IT',
                timezone_id='Europe/Rome',
                permissions=['geolocation'],  # Gestisce permessi automaticamente
                extra_http_headers={
                    'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8'
                }
            )
            
            # Crea pagina
            self.page = context.new_page()
            
            # Script anti-rilevamento
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['it-IT', 'it', 'en']});
                window.chrome = {runtime: {}};
            """)
            
            print("✅ Playwright configurato con successo")
            
        except Exception as e:
            print(f"❌ Errore nell'inizializzazione Playwright: {e}")
            raise Exception(f"Impossibile inizializzare Playwright: {e}")
    
    def handle_popups_and_captcha(self):
        """Gestisce popup di consenso Google con strategie avanzate 2025"""
        try:
            print("🔍 Ricerca popup di consenso Google...")
            
            # Attendi caricamento popup
            self.page.wait_for_timeout(3000)
            
            # Selettori aggiornati per popup Google 2025
            consent_selectors = [
                # Selettori principali Google 2025
                "button[id='L2AGLb']",  # "Accetta tutto" principale
                "button[aria-label*='Accept all']",
                "button[aria-label*='Accetta tutto']",
                "button[aria-label*='Accept']",
                "button[aria-label*='Accetta']",
                "div[role='button'][aria-label*='Accept']",
                "div[role='button'][aria-label*='Accetta']",
                
                # Selettori alternativi
                "button[data-ved]",
                "button:has-text('Accept all')",
                "button:has-text('Accetta tutto')",
                "button:has-text('I agree')",
                "button:has-text('Accetto')",
                "button:has-text('OK')",
                
                # Selettori per iframe di consenso
                "iframe[src*='consent'] button",
                "iframe[src*='cookiechoices'] button",
                
                # Selettori generici
                "[data-testid*='accept']",
                "[data-testid*='consent']",
                "button[class*='consent']",
                "button[class*='accept']"
            ]
            
            popup_closed = False
            
            # Prova ogni selettore
            for selector in consent_selectors:
                try:
                    # Controlla se l'elemento esiste ed è visibile
                    if self.page.locator(selector).count() > 0:
                        element = self.page.locator(selector).first
                        if element.is_visible():
                            element.click()
                            print(f"✅ Popup chiuso con: {selector}")
                            popup_closed = True
                            break
                except Exception as e:
                    continue
            
            # Gestione iframe di consenso
            if not popup_closed:
                try:
                    # Cerca iframe di consenso
                    iframe_selectors = [
                        "iframe[src*='consent']",
                        "iframe[src*='cookiechoices']",
                        "iframe[name*='consent']"
                    ]
                    
                    for iframe_selector in iframe_selectors:
                        if self.page.locator(iframe_selector).count() > 0:
                            frame = self.page.frame_locator(iframe_selector)
                            # Cerca pulsanti nell'iframe
                            for btn_selector in ["button:has-text('Accept')", "button:has-text('OK')", "button[aria-label*='Accept']"]:  
                                try:
                                    if frame.locator(btn_selector).count() > 0:
                                        frame.locator(btn_selector).first.click()
                                        print(f"✅ Popup iframe chiuso con: {btn_selector}")
                                        popup_closed = True
                                        break
                                except:
                                    continue
                            if popup_closed:
                                break
                except Exception as e:
                    print(f"Errore gestione iframe: {e}")
            
            # Gestione overlay/modal generici
            if not popup_closed:
                try:
                    overlay_selectors = [
                        "div[role='dialog'] button",
                        "div[class*='modal'] button",
                        "div[class*='overlay'] button",
                        "div[class*='popup'] button"
                    ]
                    
                    for overlay_sel in overlay_selectors:
                        if self.page.locator(overlay_sel).count() > 0:
                            buttons = self.page.locator(overlay_sel)
                            for i in range(buttons.count()):
                                btn = buttons.nth(i)
                                if btn.is_visible():
                                    text = btn.inner_text().lower()
                                    if any(word in text for word in ['accept', 'accetta', 'ok', 'agree']):
                                        btn.click()
                                        print(f"✅ Overlay chiuso: {text}")
                                        popup_closed = True
                                        break
                            if popup_closed:
                                break
                except Exception as e:
                    print(f"Errore gestione overlay: {e}")
            
            if popup_closed:
                self.page.wait_for_timeout(2000)  # Attendi chiusura
                print("✅ Popup di consenso gestito con successo")
            else:
                print("ℹ️ Nessun popup di consenso rilevato")
            
            # Gestione captcha
            try:
                if self.page.locator("iframe[src*='recaptcha']").count() > 0:
                    print("⚠️ Captcha rilevato. Attesa 10 secondi...")
                    self.page.wait_for_timeout(10000)
            except:
                pass
                
        except Exception as e:
            print(f"❌ Errore gestione popup: {e}")
    
    def search_google(self, query):
        """Esegue una ricerca su Google con Playwright"""
        try:
            print(f"🔍 Ricerca: {query}")
            
            # Naviga a Google
            self.page.goto("https://www.google.com", wait_until="domcontentloaded")
            
            # Gestisci popup di consenso
            self.handle_popups_and_captcha()
            
            # Trova e compila il campo di ricerca
            search_selectors = [
                "input[name='q']",
                "textarea[name='q']",
                "input[title='Cerca']",
                "input[aria-label*='Cerca']",
                "input[role='combobox']"
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        search_box = self.page.locator(selector).first
                        if search_box.is_visible():
                            break
                except:
                    continue
            
            if not search_box:
                raise Exception("Campo di ricerca non trovato")
            
            # Pulisci e inserisci la query
            search_box.clear()
            search_box.fill(query)
            search_box.press("Enter")
            
            # Attendi il caricamento dei risultati
            self.page.wait_for_selector("div[id='search']", timeout=15000)
            
            # Attendi che l'AI Overview si carichi se presente
            self.page.wait_for_timeout(3000)
            
            print("✅ Ricerca completata")
            return True
            
        except Exception as e:
            print(f"❌ Errore durante la ricerca: {e}")
            return False
    
    def extract_ai_overview(self):
        """
        Estrae il contenuto dell'AI Overview dalla pagina dei risultati con Playwright
        
        Returns:
            dict: Dizionario contenente il testo dell'AI Overview
        """
        ai_overview_content = {
            "found": False,
            "text": "",
            "expanded_text": "",
            "full_content": ""
        }
        
        try:
            print("🤖 Ricerca AI Overview...")
            
            # Selettori specifici per AI Overview aggiornati
            ai_overview_selectors = [
                ".LT6XE",
                ".QVRyCf",
                ".pyPiTc",
                ".rPeykc",
                ".EIJn2 :nth-child(1)",
                ".EIJn2 ul",
                "#m-x-content :nth-child(1)",
                "#_S7xvaILyI7Tq7_UP1_-T2A0_17+ .WaaZC .pyPiTc",
                ".RJPOee.EIJn2",
                "#m-x-content > div > div > div.RJPOee.mNfcNd > div > div > div > div:nth-child(1) > div > div > div.LT6XE > div > div:nth-child(1) > div:nth-child(22) > div > ul",
                "#m-x-content > div > div > div.RJPOee.mNfcNd > div > div > div > div:nth-child(1) > div > div > div.LT6XE > div > div:nth-child(1) > div:nth-child(21) > div > div",
                ".rPeykc.pyPiTc",
                "#m-x-content > div > div > div.RJPOee.mNfcNd > div > div > div > div:nth-child(1) > div > div > div.LT6XE > div > div:nth-child(1) > div:nth-child(1) > div > div",
                "#m-x-content > div > div > div.RJPOee.mNfcNd > div > div > div > div:nth-child(1) > div > div > div.LT6XE > div > div:nth-child(1) > div:nth-child(4) > div",
                "#m-x-content > div > div > div.RJPOee.mNfcNd > div > div > div > div:nth-child(1) > div > div > div.LT6XE > div > div:nth-child(1) > div:nth-child(3)",
                # Selettori aggiuntivi per catturare più contenuto
                "div[data-ved] p",
                "div[data-ved] span",
                "div[data-ved] div:has-text('AI')",
                "div[data-ved] div:has-text('intelligenza')",
                "[data-ved] .VwiC3b",
                "[data-ved] .hgKElc",
                "[data-ved] .LTKOO",
                "[data-ved] .sATSHe",
                "div.g div[data-ved]",
                "div.ULSxyf div[data-ved]"
            ]
            
            ai_overview_element = None
            found_selector = None
            
            # Prova diversi selettori per trovare l'AI Overview
            all_content = []
            seen_content = set()  # Per tracciare contenuto già visto
            
            def is_duplicate_content(new_text, existing_content):
                """Controlla se il nuovo testo è duplicato o contenuto in testi esistenti"""
                new_text_clean = new_text.lower().strip()
                
                # Controlla se il testo è identico
                if new_text_clean in seen_content:
                    return True
                
                # Controlla se il testo è contenuto in un testo esistente (>90% overlap)
                for existing in existing_content:
                    existing_clean = existing.lower().strip()
                    if len(new_text_clean) > 100 and len(existing_clean) > 100:
                        # Calcola sovrapposizione solo per testi molto lunghi
                        if new_text_clean in existing_clean or existing_clean in new_text_clean:
                            return True
                        
                        # Controlla similarità solo per frasi molto lunghe con soglia più alta
                        words_new = set(new_text_clean.split())
                        words_existing = set(existing_clean.split())
                        if len(words_new) > 20 and len(words_existing) > 20:
                            overlap = len(words_new.intersection(words_existing))
                            similarity = overlap / min(len(words_new), len(words_existing))
                            if similarity > 0.9:
                                return True
                
                return False
            
            for selector in ai_overview_selectors:
                try:
                    elements = self.page.locator(selector)
                    count = min(elements.count(), 10)  # Aumentato a 10 elementi per selettore
                    
                    for i in range(count):
                        element = elements.nth(i)
                        if element.is_visible():
                            text = element.inner_text().strip()
                            
                            # Raccoglie tutto il contenuto significativo con deduplicazione meno aggressiva
                            if (len(text) > 15 and 
                                not is_duplicate_content(text, all_content) and
                                # Esclude elementi di navigazione
                                not any(nav_word in text.lower() for nav_word in [
                                    'search', 'images', 'videos', 'news', 'shopping',
                                    'maps', 'more', 'tools', 'settings', 'sign in'
                                ])):
                                
                                all_content.append(text)
                                seen_content.add(text.lower().strip())
                                if not ai_overview_element:
                                    ai_overview_element = element
                                    found_selector = selector
                                
                                # Aumentato il limite per catturare più contenuto
                                if len(all_content) >= 20:
                                    break
                    
                    # Se abbiamo raggiunto il limite, usciamo dal loop principale
                    if len(all_content) >= 20:
                        break
                        
                except Exception as e:
                    continue
            
            # Se abbiamo raccolto contenuto da più elementi, lo combiniamo
            if all_content:
                combined_content = '\n\n'.join(all_content)
                print(f"✅ AI Overview trovato con {len(all_content)} elementi: {found_selector}")
                print(f"📝 Contenuto combinato: {len(combined_content)} caratteri")
                
                # Imposta il contenuto combinato ma continua per cercare espansioni
                ai_overview_content["found"] = True
                ai_overview_content["text"] = combined_content
                ai_overview_content["full_content"] = combined_content
                
                # Continua per cercare il pulsante "Mostra altro" se abbiamo un elemento principale
                if ai_overview_element:
                    print("🔍 Ricerca pulsante 'Mostra altro' per contenuto combinato...")
            
            # Ricerca alternativa per contenuti AI in iframe o shadow DOM
            if not ai_overview_element:
                try:
                    # Cerca in iframe
                    iframe_selectors = ["iframe[src*='ai']", "iframe[src*='overview']"]
                    for iframe_sel in iframe_selectors:
                        if self.page.locator(iframe_sel).count() > 0:
                            frame = self.page.frame_locator(iframe_sel)
                            frame_content = frame.locator("body").inner_text()
                            if len(frame_content) > 50:
                                ai_content = frame_content
                                found_selector = f"iframe: {iframe_sel}"
                                print(f"✅ AI Overview trovato in iframe: {iframe_sel}")
                                return ai_content
                except Exception as e:
                    print(f"Errore ricerca iframe: {e}")
                
                # Strategia di fallback: cerca elementi con molto testo
                try:
                    fallback_selectors = [
                        "div[data-ved]:has-text('AI')",
                        "div[data-ved]:has-text('intelligenza')",
                        "div[data-ved]:has-text('artificial')",
                        "div[id='search'] div"
                    ]
                    
                    for fallback_sel in fallback_selectors:
                        elements = self.page.locator(fallback_sel)
                        for i in range(min(elements.count(), 5)):  # Controlla solo i primi 5
                            element = elements.nth(i)
                            if element.is_visible():
                                text = element.inner_text().strip()
                                if len(text) > 100 and not text.startswith('http'):
                                    ai_overview_element = element
                                    found_selector = f"fallback: {fallback_sel}"
                                    print(f"✅ AI Overview trovato con fallback: {fallback_sel}")
                                    break
                        if ai_overview_element:
                            break
                except Exception as e:
                    print(f"Errore strategia fallback: {e}")
            
            if ai_overview_element:
                try:
                    # Estrai il testo dall'elemento
                    ai_text = ai_overview_element.inner_text().strip()
                    
                    if ai_text and len(ai_text) > 20:  # Verifica che ci sia contenuto significativo
                        print(f"✅ AI Overview estratto con: {found_selector}")
                        print(f"📝 Contenuto: {len(ai_text)} caratteri")
                        print(f"📄 Anteprima: {ai_text[:200]}...")
                        
                        ai_overview_content["found"] = True
                        ai_overview_content["text"] = ai_text
                    else:
                        print("⚠️ AI Overview trovato ma contenuto insufficiente")
                        
                except Exception as e:
                    print(f"❌ Errore nell'estrazione del testo: {e}")
                
                # Cerca il pulsante "Mostra altro" o "Show more" con Playwright
                try:
                    print("🔍 Ricerca pulsante 'Mostra altro'...")
                    
                    show_more_selectors = [
                        # Selettori aggiornati per "Mostra altro" (2025)
                        ".niO4u.VDgVie.SlP8xc",
                        "div.niO4u.VDgVie.SlP8xc",
                        "span.niO4u.VDgVie.SlP8xc",
                        "button.niO4u.VDgVie.SlP8xc",
                        "[class*='niO4u'][class*='VDgVie'][class*='SlP8xc']",
                        
                        # Selettori specifici per testo
                        "button:has-text('Mostra altro')",
                        "button:has-text('Show more')",
                        "span:has-text('Mostra altro')",
                        "span:has-text('Show more')",
                        "div:has-text('Mostra altro')",
                        "div:has-text('Show more')",
                        "a:has-text('Mostra altro')",
                        "a:has-text('Show more')",
                        
                        # Selettori con attributi role
                        "[role='button']:has-text('altro')",
                        "[role='button']:has-text('more')",
                        "[role='button']:has-text('Mostra')",
                        "[role='button']:has-text('Show')",
                        
                        # Selettori con aria-label
                        "button[aria-label*='Mostra']",
                        "button[aria-label*='Show']",
                        "button[aria-label*='more']",
                        "button[aria-label*='altro']",
                        "[aria-label*='Mostra altro']",
                        "[aria-label*='Show more']",
                        
                        # Selettori con data-ved
                        "[data-ved][role='button']",
                        "button[data-ved]",
                        "div[data-ved][role='button']",
                        "span[data-ved][role='button']",
                        
                        # Classi CSS specifiche Google
                        ".oHglmf",
                        ".GKS7yf",
                        ".pkphOe",
                        ".s75CSd",
                        ".CvDJxb",
                        ".RveJvd",
                        ".dmenKe",
                        ".CL9Uqc",
                        ".wHYlTd",
                        ".sATSHe",
                        
                        # Selettori generici per elementi cliccabili
                        "[onclick*='more']",
                        "[onclick*='altro']",
                        "[onclick*='expand']",
                        "[onclick*='espandi']"
                    ]
                    
                    show_more_button = None
                    
                    # Cerca il pulsante nell'elemento AI Overview
                    for selector in show_more_selectors:
                        try:
                            # Cerca prima nell'elemento AI Overview
                            buttons = ai_overview_element.locator(selector)
                            if buttons.count() > 0:
                                button = buttons.first
                                if button.is_visible():
                                    show_more_button = button
                                    print(f"✅ Pulsante 'Mostra altro' trovato: {selector}")
                                    break
                        except:
                            continue
                    
                    # Se non trovato nell'elemento, cerca nella pagina
                    if not show_more_button:
                        for selector in show_more_selectors:
                            try:
                                buttons = self.page.locator(selector)
                                if buttons.count() > 0:
                                    button = buttons.first
                                    if button.is_visible():
                                        show_more_button = button
                                        print(f"✅ Pulsante 'Mostra altro' trovato nella pagina: {selector}")
                                        break
                            except:
                                continue
                    
                    # Prova con XPath specifico se non trovato
                    if not show_more_button:
                        try:
                            xpath_selector = "//*[@id='_L5FvaJOBM43_7_UPgvGUsQ0_1']/div[1]/div/div[3]/div/div/div"
                            xpath_button = self.page.locator(f"xpath={xpath_selector}")
                            if xpath_button.count() > 0 and xpath_button.first.is_visible():
                                show_more_button = xpath_button.first
                                print(f"✅ Pulsante 'Mostra altro' trovato con XPath specifico")
                        except Exception as e:
                            print(f"⚠️ XPath specifico non funzionante: {e}")
                    
                    # Fallback: cerca qualsiasi elemento cliccabile con testo relativo
                    if not show_more_button:
                        try:
                            print("🔍 Ricerca fallback del pulsante 'Mostra altro'...")
                            fallback_selectors = [
                                "*:has-text('Mostra') >> visible=true",
                                "*:has-text('altro') >> visible=true",
                                "*:has-text('Show') >> visible=true",
                                "*:has-text('more') >> visible=true",
                                "[role='button'] >> visible=true",
                                "button >> visible=true",
                                "div[role='button'] >> visible=true",
                                "span[role='button'] >> visible=true",
                                "a >> visible=true"
                            ]
                            
                            for fallback in fallback_selectors:
                                try:
                                    elements = self.page.locator(fallback)
                                    count = elements.count()
                                    print(f"🔍 Controllando {count} elementi con selettore: {fallback}")
                                    
                                    for i in range(min(count, 5)):
                                        element = elements.nth(i)
                                        try:
                                            if element.is_visible():
                                                text = element.inner_text().lower().strip()
                                                print(f"📝 Testo elemento {i}: '{text[:50]}...'")
                                                
                                                # Controllo più preciso delle parole chiave
                                                keywords = ['mostra altro', 'show more', 'mostra', 'altro', 'show', 'more']
                                                if any(keyword in text for keyword in keywords):
                                                    # Verifica che l'elemento sia effettivamente cliccabile
                                                    if element.is_enabled():
                                                        show_more_button = element
                                                        print(f"✅ Pulsante trovato con fallback: {fallback} - Testo: '{text}'")
                                                        break
                                        except Exception as elem_e:
                                            print(f"⚠️ Errore controllo elemento {i}: {elem_e}")
                                            continue
                                    
                                    if show_more_button:
                                        break
                                except Exception as sel_e:
                                    print(f"⚠️ Errore con selettore {fallback}: {sel_e}")
                                    continue
                                    
                        except Exception as e:
                            print(f"⚠️ Fallback search failed: {e}")
                    
                    # Se trova il pulsante, cliccalo
                    if show_more_button:
                        try:
                            print("🖱️ Click su 'Mostra altro'...")
                            show_more_button.click()
                            
                            # Attendi che il contenuto si espanda
                            self.page.wait_for_timeout(3000)
                            
                            # Estrai il contenuto espanso
                            expanded_text = ai_overview_element.inner_text().strip()
                            
                            # Confronto più intelligente per verificare l'espansione
                            original_length = len(ai_text)
                            expanded_length = len(expanded_text)
                            length_increase = expanded_length - original_length
                            
                            # Considera espanso se:
                            # 1. Il testo è più lungo di almeno 50 caratteri
                            # 2. O se è aumentato di almeno il 20%
                            if length_increase > 50 or (original_length > 0 and length_increase / original_length > 0.2):
                                ai_overview_content["expanded_text"] = expanded_text
                                ai_overview_content["full_content"] = expanded_text
                                print(f"✅ Contenuto espanso estratto: {expanded_length} caratteri (+{length_increase})")
                            else:
                                ai_overview_content["full_content"] = ai_text
                                print(f"⚠️ Contenuto non espanso significativamente: {original_length} → {expanded_length} caratteri (+{length_increase})")
                                
                        except Exception as e:
                            print(f"❌ Errore nel click 'Mostra altro': {e}")
                            ai_overview_content["full_content"] = ai_text
                    else:
                        ai_overview_content["full_content"] = ai_text
                        print("ℹ️ Pulsante 'Mostra altro' non trovato")
                        
                except Exception as e:
                    print(f"❌ Errore nella gestione 'Mostra altro': {e}")
                    ai_overview_content["full_content"] = ai_text
            
            else:
                print("❌ AI Overview non trovato nella pagina")
                
        except Exception as e:
            print(f"❌ Errore durante l'estrazione dell'AI Overview: {e}")
        
        return ai_overview_content
    
    def extract_ai_overview_from_query(self, query):
        """
        Funzione principale che esegue la ricerca ed estrae l'AI Overview
        
        Args:
            query (str): La query di ricerca
            
        Returns:
            str: Contenuto dell'AI Overview estratto o None se non trovato
        """
        try:
            print(f"🔍 Ricerca di: {query}")
            
            # Esegui la ricerca
            if not self.search_google(query):
                print("❌ Ricerca fallita")
                return None
            
            print("🤖 Estrazione dell'AI Overview...")
            ai_content = self.extract_ai_overview()
            
            if ai_content:
                print("✅ AI Overview estratto con successo!")
                return ai_content
            else:
                print("❌ AI Overview non trovato")
                return None
            
        except Exception as e:
            print(f"❌ Errore durante l'estrazione: {e}")
            return None
    
    def save_to_file(self, content, filename):
        """
        Salva il contenuto estratto in un file JSON
        
        Args:
            content (dict): Contenuto da salvare
            filename (str): Nome del file
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            print(f"Contenuto salvato in: {filename}")
        except Exception as e:
            print(f"Errore nel salvare il file: {e}")
    
    def close(self):
        """
        Chiude il browser e rilascia le risorse
        """
        try:
            if hasattr(self, 'page') and self.page:
                self.page.close()
            if hasattr(self, 'browser') and self.browser:
                self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                self.playwright.stop()
            print("🔒 Browser chiuso correttamente")
        except Exception as e:
            print(f"❌ Errore durante la chiusura: {e}")


def main():
    """Funzione principale per testare l'estrattore"""
    extractor = AIOverviewExtractor(headless=False)
    
    try:
        # Query di test aggiornata per il 2025
        query = "migliori smartphone 2025"
        
        # Estrai l'AI Overview
        result = extractor.extract_ai_overview_from_query(query)
        
        # Salva il risultato
        if result:
            filename = f"ai_overview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            extractor.save_to_file(result, filename)
            print(f"📁 Risultato salvato in: {filename}")
            
            # Stampa il risultato
            print("\n=== CONTENUTO AI OVERVIEW ===")
            print(result)
        else:
            print("❌ Nessun AI Overview trovato")
        
    finally:
        extractor.close()


if __name__ == "__main__":
    main()