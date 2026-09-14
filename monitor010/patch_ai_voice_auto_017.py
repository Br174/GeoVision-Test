from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'android-youtube-test/app/src/main/assets/geovision.html'
OUT=ROOT/'out/LAB_012_FAILOVER.html'


def patch(path):
    s=path.read_text(encoding='utf-8')

    # Guardie minime: preserviamo l'AI e l'avvio automatico gia presenti nella base.
    assert 'async function aiNarration(' in s
    assert 'void enrichNarration(p);' in s
    assert "function speak(text, append = false) { if (!('speechSynthesis' in window))" in s
    assert 'function stopSpeech() { speechToken++;' in s

    # Il TTS usato da enrichNarration e' una funzione lessicale del <script type=module>.
    # LAB016 intercettava window.speak, che non e' la stessa funzione. Qui patchiamo
    # direttamente il percorso realmente chiamato all'apertura della scheda.
    s=s.replace(
        'function stopSpeech() { speechToken++;',
        "function stopSpeech() { try { if (window.GeoVisionTTS && typeof window.GeoVisionTTS.stop === 'function') window.GeoVisionTTS.stop(); } catch {} speechToken++;",
        1
    )

    s=s.replace(
        "function speak(text, append = false) { if (!('speechSynthesis' in window))",
        """function speak(text, append = false) {
    try {
        if (window.GeoVisionTTS && typeof window.GeoVisionTTS.speak === 'function') {
            const parts = speechParts(text);
            if (!parts.length) return;
            if (!append && typeof window.GeoVisionTTS.stop === 'function') window.GeoVisionTTS.stop();
            speaking = true;
            $('#voice')?.classList.add('active');
            $('#nativeVoice')?.classList.add('active');
            parts.forEach((part, i) => window.GeoVisionTTS.speak(part, !!append || i > 0));
            return;
        }
    } catch {}
    if (!('speechSynthesis' in window))""",
        1
    )

    hook=r'''
<script id="gv-ai-voice-auto-017">
window.gvNativeTtsState=function(state){
  try{
    const active=state==='start';
    const done=state==='done'||state==='error';
    if(active||done){
      const a=document.getElementById('voice');
      const b=document.getElementById('nativeVoice');
      if(a)a.classList.toggle('active',active);
      if(b)b.classList.toggle('active',active);
    }
  }catch(_){}
};
</script>
'''
    assert 'gv-ai-voice-auto-017' not in s
    s=s.replace('</body>',hook+'</body>',1)
    path.write_text(s,encoding='utf-8')

patch(HTML)
if OUT.exists(): patch(OUT)
print('LAB017: automatic native TTS patched into module narration path; existing Gemini flow preserved')
