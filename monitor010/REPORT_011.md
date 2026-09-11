# GeoVision — KEYBOX 008 + LAB 011 FAILOVER

## Obiettivo
Correggere il comparto chiavi senza modificare la MADRE ORIGINALE 2, aggiungendo:

- interruttori manuali ON/OFF indipendenti per Google 1 / Google 2 / Google 3;
- OFF con priorità assoluta: una chiave OFF non viene usata, testata o scelta dal failover;
- cambio immediato della chiave attiva quando quella corrente viene spenta;
- failover automatico immediato sui veri errori quota/chiave (`RESOURCE_EXHAUSTED`, 429, `OVER_QUERY_LIMIT`, `REQUEST_DENIED`, chiave invalida, API disabilitata, billing/referer/auth failure);
- retry trasparente della stessa chiamata Places con la chiave successiva abilitata;
- nessun reload della WebView per i normali errori Places;
- stop dopo l'esaurimento delle alternative, senza rotazione infinita;
- sincronizzazione degli stati ON/OFF con KeyBox tramite broadcast protetto da firma;
- conservazione di SharedPreferences `geovision_keybox_v1` e alias AndroidKeyStore `GeoVisionKeyBoxMasterV1`.

## Identità
- KEYBOX 008 MONITOR: package `it.geovision.keybox`, versionCode 2008, update del KeyBox singleton.
- LAB 011 FAILOVER: package isolato `it.geovision.lab.failover011`, versionCode 2011.
- Firma attesa: `716c1a8a139ad956ef8a00f85f153eb0028d109c75b1b938bdf3bb3eb23c22b5`.

## Strategia tecnica
La Maps JavaScript API caricata inizialmente non può cambiare credenziale in-place. Per non perdere la scheda aperta quando una richiesta Places incontra una quota esaurita, LAB 011 mantiene la mappa già caricata e instrada SearchText, Nearby, Place Details e media foto attraverso Places REST v1 usando la nuova chiave, ripetendo la richiesta fallita senza ricaricare l'app. Solo `gm_authFailure` della Maps JavaScript SDK è trattato come eccezione tecnica: in quel caso viene effettuato un singolo reload controllato dopo aver selezionato la chiave successiva.

## Verifiche automatiche richieste prima della consegna
1. Hash esatto della Madre 2: `42aead77c8cac5c36d3eb9ec7cf81b9efb69f8fd5979ebd52a5e4ca01c28cb9b`.
2. Diff confinato al comparto chiavi/diagnostica/failover.
3. Sintassi JavaScript di tutti gli script.
4. Unit test dello stato chiavi: switch manuali, OFF assoluto, all-OFF, cooldown, duplicati, revisioni e rollback storage.
5. Browser test mobile: pannello con 3 switch, G1 quota -> G2 retry immediato, chiave OFF saltata, all-OFF blocca le richieste, nessun reload Places, markup scheda Google/social invariato.
6. Build + lint Android per KeyBox e LAB.
7. Test Android API 30 del vault cifrato, persistenza degli switch, permission signature e bridge.
8. Firma APK, package, versionCode, label e byte equality dell'HTML nell'APK.
9. Screenshot automatici di KeyBox e Monitor GeoVision.

## Limite della CI
La CI usa credenziali sintetiche/mocking per testare il motore di failover e non usa le chiavi private reali dell'utente. La prova finale con le quote reali del progetto Google resta una verifica sul telefono dell'utente. Una build non viene consegnata se la suite automatizzata non è completamente verde.
