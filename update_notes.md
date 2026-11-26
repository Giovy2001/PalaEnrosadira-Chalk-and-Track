# FIX - CSS della bottom nav e dell'archivio mancanti

    [x] Ripristinato `static/css/bottom-nav.css` (linkato da base.html ma assente):
        nav fissa in basso, voci allineate, stato attivo e safe-area iOS
    [x] Ripristinato `static/css/home/archive.css` (_linked_ ma assente)
    [x] Test che verifica che tutti i CSS linkati dalle pagine pubbliche siano serviti

---

# FIX - Creazione blocco bloccata al passaggio prese → nome

    [x] `auth.restore_from_request()` non riscrive più la sessione quando il token
        inviato dal form è già quello autenticato: non cancella più
        `pending_image_url` e `pending_holds` durante il flusso di creazione
    [x] `login()` conserva lo stato temporaneo quando l'identità resta la stessa;
        lo ripulisce solo in caso di cambio utente
    [x] Test end-to-end: upload → prese → finalizza → salvataggio → archivio

---

# UPDATE #11 - Fase 3: profilo e statistiche reali ✅

Completata sul branch `unstable`. La logica dati era già presente; sono stati ripristinati gli asset mancanti e aggiunti test di accettazione.

    [x] Grado salvato in creazione/modifica e mostrato nel profilo (mappa gradi
        condivisa dal server tramite `window.GRADES`)
    [x] Blocchi completati e "I miei blocchi" letti dal DB, con stati vuoti espliciti
    [x] Punti assegnati una sola volta per completamento e `last_seen_date` aggiornato
    [x] Ripristinato `static/css/palette.css` (linkato ma assente): ciclo colore 0→7→0
        con swatch, avatar, favicon, icone PWA e manifest per colore sincronizzati
    [x] Generate icone mancanti (PWA + 8 profili) via `scripts/generate_icons.py`
    [x] Manifest completo (`name`, `start_url`, `scope`, display standalone)
    [x] Zero immagini esterne Stitch nelle pagine del profilo
    [x] Test pytest: asset/PWA, punteggio una sola volta, gradi, limiti colore,
        profilo da dati server (33 test totali)

---

# UPDATE #10 - Fase 2: identità e autorizzazione server-side ✅

Completata sul branch `unstable`, con verifica delle difese già presenti e chiusura dei residui lato UI/validazione.

    [x] Sessione Flask firmata + token opaco firmato; localStorage solo preferenza UI/cache
    [x] Identità del server injectata in `window.APP_USER`: nav e profilo non leggono più
        il nome utente da localStorage come fonte di verità; il profilo attende il
        ripristino asincrono della sessione prima di decidere se redirectare
    [x] Token non accettato più nella query string (solo header, form e sessione)
    [x] require_author su /route_<id> POST, /edit_route_<id> e /edit_holds_<id>
    [x] Verifica esistenza utente nel DB a ogni richiesta autenticata
    [x] Username non vuoto, unico, max 40 caratteri e senza caratteri di controllo;
        errori visibili nelle pagine di creazione/aggiornamento profilo
    [x] Nessun auto-submit del nome a ogni tasto; invio solo tramite pulsante
    [x] Whitelist color_id (0-7); get_profile risponde JSON anche per utente assente
    [x] Test pytest: token in query ignorato, sessione senza token, autorizzazione
        su prese, colore altrui bloccato, username lungo rifiutato (28 test totali)

---

# UPDATE #9 - Fase 1: fondamenta dati affidabili ✅

Completata sul branch `unstable`. Il grosso della fase era già presente; sono stati chiusi i gap rimasti e aggiunti i test di accettazione.

    [x] Migrazioni versionate e idempotenti (schema_migrations, ora alla versione 4)
    [x] PRAGMA foreign_keys=ON e ON DELETE CASCADE su holds/betas, con ricostruzione
        delle tabelle esistenti senza perdita di dati (migrazione 4)
    [x] Indici su routes.author, routes.creation_date, holds.route_id, betas.route_id
    [x] Transazioni con rollback su add_route, add_holds, edit_holds, del_route
    [x] del_route rimuove anche le bete; immagine eliminata solo dopo il commit
    [x] Date ISO 8601, whitelist degli UPDATE dinamici, 404 per route inesistente
    [x] JSON di prese/immagine passato via POST body e sessione, non più in query string
    [x] Test pytest: ordinamento cronologico, cascade delle FK, rollback, idempotenza
        delle migrazioni e upgrade da schema storico (22 test totali)

---

# UPDATE #8 - Deploy, sicurezza e completamento funzionalità ✅

Completato sul branch `develop`. Dettagli nel piano: `~/.opencode/plan/chalk-and-track-piano-completamento.md`.

    [x] Sblocco deploy: main.py riscritto (nessun TypeError), modalità DB scelta prima della connessione
    [x] Configurazione centralizzata in settings.py + app factory in app.py
    [x] Endpoint /health
    [x] Cron /api/database_cleanup protetto con CRON_SECRET e force modalità remota
    [x] .gitignore versionato; .pyc rimossi da git; token da ruotare su Vercel
    [x] Dipendenze pinnate (requirements.txt / requirements-dev.txt)
    [x] Migrazioni versionate e idempotenti (schema_migrations): NON serve più droppare le tabelle
    [x] Transazioni con rollback; del_route rimuove anche bete e immagini
    [x] Date ISO 8601; get_route inesistente → 404
    [x] Identità server-side (sessione + token firmato); require_author su modifica/eliminazione
    [x] Whitelist color_id e username; get_profile gestisce utente inesistente
    [x] Profilo reale: punti, gradi, blocchi creati e completati dal DB
    [x] Grado aggiunto al salvataggio e alla modifica
    [x] Creazione/modifica prese robusta (submit, pointercancel, hold_id, size numerico)
    [x] Esplora e Archivio funzionanti con filtri
    [x] Betas: CRUD corretto + endpoint JSON di inserimento
    [x] Template base condiviso, nav su tutte le pagine, CSS ripulito, manifest PWA completato
    [x] Test pytest (18 test) + GitHub Actions CI
    [x] readme.md aggiornato

    [ ] Rimangono fuori dallo scope attuale:
        [ ] Ricerca fuzzy nell'archivio (per ora solo LIKE %nome%)
        [ ] Feed fullscreen stile TikTok per Esplora
        [ ] Accettazione obbligatoria delle condizioni d'uso prima della creazione utente

---

# UPDATE #2.5 - GitHub Restyling
    this will be merged to main with update #3

    [x] Create readme
    [x] Rename to PalaEnrosadira - Chalk & Track


TODO UPDATE #3 - App sections rework

    [x] IMPORTANTE: Sono state fatte molte modifiche agli script del database, bisogna controllare tutte le volte che venivano chiamate le funzioni
    [x] Aggiungere abilità di usare progression_id "zone" e constraint_id "only_hand","only_foot","foot","only_volume","no_volume","normal"


    [x] Inserire nel databse tutte le cose necessarie per la nuova app
        [x] users
            [x] creare una nuova table users
            [x] user_id, user_name, user_icon, user_color, creation_date, last_seen_date, points, serialized_completed_routes
            [x] Test delle funzionalità
        [x] betas
            [x] creare una nuova table betas
            [x] beta_id, route_id, title, body
            [x] Foreign reference alla route (come holds)
        [x] routes
            [x] aggiungere difficoltà (opzionale)
            [x] Foreign reference a user_id
        [x] holds
            [x] rinominare use e type per essere più comprensibili
            [x] valutare di aggiungere altre informazioni

    # OUT of branch unstable

    [ ] Creare palette comune
        [ ] :root{} dovrebbe funzionare (cerca su internet)

    [ ] Implementare le quattro diverse sezioni
        [ ] Esplora
            [ ] Per ora non porta a nulla
            [ ] Magari under construction page
        [ ] Crea
            [ ] Fai in modo che sia visibile solo se username è salvato nel local_storage
        [ ] Archivio
            [ ] l'attuale index
        [ ] Profilo
            [ ] Icona del profilo
            [ ] Colore del profilo
                
    [ ] Manca l'icona del sito (favicon)
    [x] Cambiare nome a salvataggio nel local storage "chalk_and_track_username" 


TODO UPDATE #4 - Rework Route creation

    [ ] Provare a vedere se è possibile processare l'immagine lato client in modo da rendere più leggero il caricamento
    
    [ ] Scrap dell'idea delle tre fasi
        [ ] Fase unica con la pagina lunga come da stitch

    [ ] Riattivare lo scroll ma non lo zoom
    [ ] Valutare possibilità di ingrandire e rimpicciolire la presa con lo zoom (gesture pizzicata)
    [ ] Valutare possibilità di cambiare tipo di presa tenendo premuto su di essa

    [ ] Copri l'immagine con un qualcosa di semitrasparente che la renda più scura/desaturata
        [ ] le prese al posto di colorare l'interno dei tre colori, all'interno hanno i colori originale della foto
        [ ] colora dei tre colori le outline dei cerchi
        [ ] le label dei constraint dovrebbero avere una targhetta in modo che siano visibili sempre
        
    [ ] Far si che una volta selezionata una presa tu possa scrollare in qualsiasi punto dello schermo per spostarla
        [ ] Valutare differenza tra de-selezione e hold-drag


TODO UPDATE #5 - Archivio
    
    [ ] Possibilità di filtrare nell'index, per autore / nome / difficoltà
        [ ] Controlla come si fa la ricerca intelligente (lettera sbagliata ma comunque simile)
        

TODO UPDATE #6 - Esplora

    [ ] Pagina per trovare blocchi in evidenza
    [ ] Filtra solo i blocchi che non hai completato
    [ ] In base alla data, quelli più recenti prima
    [ ] Con un po' di randomicità
    [ ] Fullscreen tiktok feed
    [ ] Se non ci sono blocchi in evidenza cosa succede?


TODO UPDATE #7 - pulizia del codice

    [ ] Controllare durante l'esecuzione se ci sono errori nella console 
    [ ] Mettere ordine nel codice
    [ ] Aggiungere in python le tipologie delle variabili
    [ ] Commentare tutte le funzioni
    [ ] Rimuovere commenti relativi al precedente modo di passare le variabili con i cookies in create.py
    [ ] Valutare di rinominare i file per seguire una convenzione migliore
    [ ] Rimuovere da git i file di cache di python
