from pathlib import Path

p = Path('android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java')
s = p.read_text(encoding='utf-8')

s = s.replace(
    'import android.app.Activity;\n',
    'import android.app.Activity;\nimport android.content.ActivityNotFoundException;\nimport android.content.Intent;\n',
    1
)
s = s.replace(
    'import java.util.UUID;\n',
    'import java.util.UUID;\n\nimport org.json.JSONObject;\n',
    1
)

s = s.replace(
    '    private final List<PendingSpeech> pendingSpeech = new ArrayList<>();\n',
    '    private final List<PendingSpeech> pendingSpeech = new ArrayList<>();\n    private static final int REQ_KEYBOX = 7311;\n',
    1
)

s = s.replace(
    '        webView.addJavascriptInterface(new NativeUiBridge(), "GeoVisionNativeUI");\n',
    '        webView.addJavascriptInterface(new NativeUiBridge(), "GeoVisionNativeUI");\n        webView.addJavascriptInterface(new KeyBoxBridge(), "GeoVisionKeyBox");\n',
    1
)

anchor = """    private class NativeTtsBridge {
        @JavascriptInterface public void speak(String text, boolean append) { speakNative(text, append); }
        @JavascriptInterface public void stop() { stopNative(); }
        @JavascriptInterface public boolean isReady() { return ttsReady; }
    }

    @Override
    public void onBackPressed() {"""

replacement = """    private void notifyKeyBoxError(String message) {
        main.post(() -> {
            if (webView != null) {
                webView.evaluateJavascript(
                        "window.gvKeyBoxError&&window.gvKeyBoxError(" + JSONObject.quote(message) + ")", null);
            }
        });
    }

    private class KeyBoxBridge {
        @JavascriptInterface
        public void importKeys() {
            main.post(() -> {
                Intent intent = new Intent("it.geovision.keybox.EXPORT_KEYS");
                intent.setPackage("it.geovision.keybox");
                try {
                    startActivityForResult(intent, REQ_KEYBOX);
                } catch (ActivityNotFoundException e) {
                    notifyKeyBoxError("Installa GeoVision KeyBox");
                } catch (SecurityException e) {
                    notifyKeyBoxError("KeyBox non autorizzato: verifica la firma GeoVision");
                }
            });
        }
    }

    private class NativeTtsBridge {
        @JavascriptInterface public void speak(String text, boolean append) { speakNative(text, append); }
        @JavascriptInterface public void stop() { stopNative(); }
        @JavascriptInterface public boolean isReady() { return ttsReady; }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQ_KEYBOX) return;
        if (resultCode != RESULT_OK || data == null) {
            notifyKeyBoxError("KeyBox non ha restituito le chiavi");
            return;
        }
        try {
            JSONObject keys = new JSONObject();
            keys.put("google1", data.getStringExtra("google1"));
            keys.put("google2", data.getStringExtra("google2"));
            keys.put("google3", data.getStringExtra("google3"));
            keys.put("ai", data.getStringExtra("ai"));
            keys.put("youtube", data.getStringExtra("youtube"));
            keys.put("count", data.getIntExtra("count", 0));
            final String payload = keys.toString();
            main.post(() -> {
                if (webView != null) {
                    webView.evaluateJavascript(
                            "window.gvReceiveKeyBox&&window.gvReceiveKeyBox(" + payload + ")", null);
                }
            });
        } catch (Exception e) {
            notifyKeyBoxError("Errore nella lettura del KeyBox");
        }
    }

    @Override
    public void onBackPressed() {"""

if anchor not in s:
    raise SystemExit('MainActivity insertion anchor not found')
s = s.replace(anchor, replacement, 1)

assert 'GeoVisionKeyBox' in s
assert 'it.geovision.keybox.EXPORT_KEYS' in s
assert 'REQ_KEYBOX' in s
assert 'gvReceiveKeyBox' in s

p.write_text(s, encoding='utf-8')
print('MainActivity KeyBox bridge patched')
