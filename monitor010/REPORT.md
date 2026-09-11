# GeoVision — KEYBOX 007 Monitor / LAB 010 Monitor Sync

Base KeyBox: `d655a782c54acb6197aa327bcc75a9fb289f188b` (KEYBOX 005).
Base GeoVision: `1d3933b2578883ef46261981515b0833092f9501` (MADRE ORIGINALE 2).
HTML Madre ricostruito: SHA256 `42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b`.
La Madre e il suo ramo non vengono modificati. Il confronto automatico verifica l'identità dell'intero HTML al di fuori del sottosistema chiavi/pannello.

## Diagnosi prima dell'intervento

1. KEYBOX 005 usa archivio e alias Keystore stabili; la versione 006 aggiunge stato attivo globale.
2. Il LAB 009 cerca `openKeysDiagnostics`, assente dalla Madre: il comando reale è `runGoogleDiagnostics`.
3. Il LAB 009 cerca `keysDiagnosticsPanel`; l'elemento della Madre è `googleDiagPanel`.
4. La decorazione del LAB usa un collegamento `keysDiagnosticsOpen` assente dalla Madre.
5. Il bootstrap LAB 009 usa stringhe raw con `\n` letterali da verificare come JavaScript generato, non solo come Python valido.
6. `gvDiagApplySelectedKey` cambia la variabile Google dopo il caricamento del SDK: le due chiavi possono divergere.
7. L'import manuale LAB 009 chiama sia il nuovo apply sia il vecchio receive: applicazione doppia e reload storico ancora attivo.
8. La finestra fissa di 300 ms non garantisce che il broadcast arrivi prima dell'avvio della pagina.
9. Il ricevitore dinamico LAB 009 è esportato senza imporre il permesso al mittente nella registrazione.
10. La vecchia importazione può rimuovere chiavi locali da payload incompleti; AI/YouTube vuoti non sono trattati uniformemente.
11. Il vecchio failover torna sulle chiavi già fallite senza ricordare il cooldown.
12. Il vecchio `get` del vault converte anche un errore di decifratura in chiave vuota.
13. Cinque `put` separati possono produrre un salvataggio parziale.
14. Un indicatore verde per mera presenza della chiave non dimostra il funzionamento del servizio.

Questi sono difetti verificati nel sorgente. L'effettiva causa di ogni malfunzionamento sul telefono non è deducibile dai soli sorgenti.

## Confronto con le richieste

| Richiesta | Implementazione e controllo |
|---|---|
| Partire da KEYBOX 005 | Conservati formato cifrato, archivio `geovision_keybox_v1`, alias `GeoVisionKeyBoxMasterV1`, export manuale e firma |
| Madre 2 intatta | Ricostruzione con SHA256 esatto; file e ramo Madre non modificati |
| KeyBox `it.geovision.keybox` | VersionCode 2007, firma originale verificata sull'APK |
| GeoVision di prova separata | `it.geovision.lab.monitor010`, versionCode 2010 |
| Monitor con 5 chiavi | Google 1/2/3, AI, YouTube, campi password e indicatori |
| Separare pannello app da KeyBox | KeyBox conserva le chiavi; Monitor GeoVision modifica solo la propria copia e verifica i servizi |
| Sync stabile | Ricezione firmata, nonce per richiesta, payload completo, revisione, nessuna apertura automatica di Activity |
| Schede stabili | Sync riceve un aggiornamento in attesa; attivazione al prossimo avvio o con Applica esplicito, nessuna modifica a caldo del SDK |
| Chiave in uso preservata | L'import mantiene la stessa chiave se ancora presente, anche se cambia slot |
| Nessuna rotazione continua | Errori di rete non ruotano; cooldown per chiavi fallite e arresto quando esaurite; riprova successiva dopo cooldown |
| Non consegnare per sola compilazione | Workflow con sintassi, regressione integrale, stato JS, browser reale, build/lint APK e test Android 11; artefatto finale pubblicato solo dopo tutti i gate |

Il Sync è attivabile nel Monitor. KEYBOX 005 resta compatibile con Importa manuale. Una risposta vuota, corrotta o obsoleta conserva le chiavi in uso. KeyBox non impone un indice Google globale alle app: ogni SDK mantiene la propria chiave durante la sessione.

## Verifiche e limiti

Test di stato: 19 scenari automatizzati (slot, errori, import, revisioni, rollback, failover e cooldown).
Regressione: confronto completo di tutti i byte esterni al comparto chiavi, oltre alla sintassi di ogni script.
Browser: apertura dal vero pulsante, cinque campi mascherati, nessuna chiamata al solo aprire il pannello, cinque test espliciti, indicatori, import ritardato, nessun doppio pannello, overflow mobile, applicazione singola e scheda/menu originali.
Android 11: archivio cifrato compatibile 005, roundtrip, salvataggio atomico, cancellazione singola, corruzione, conteggio errato e permessi firma. Due test aggiuntivi del bridge eseguono uno scambio reale KeyBox/GeoVision su WebView e rifiutano una risposta non richiesta.
Build: APK, lint, certificato, applicationId e identità dell'HTML impacchettato.

I test dei servizi nel browser usano risposte simulate e chiavi sintetiche: non certificano quote o autorizzazioni delle chiavi personali. Il Monitor esegue le verifiche reali su richiesta dal telefono. Il verde per Gemini verifica l'accesso all'API modelli, non una narrazione generata; YouTube verifica l'accesso alla Data API; Google verifica Places REST, mentre il pulsante diagnostica separato verifica il SDK/schede/foto. Nessuna modifica ai servizi AI/video della Madre.

Fonti tecniche: https://developer.android.com/develop/background-work/background-tasks/broadcasts e https://developer.android.com/reference/android/webkit/WebView.

Installazione: aggiornare KeyBox sopra la versione esistente senza disinstallarla; LAB 010 si installa accanto alla Madre. Non installare APK di test strumentali: non fanno parte della consegna.
