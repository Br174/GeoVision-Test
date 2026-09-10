from pathlib import Path

p = Path('android-youtube-test/app/src/main/java/it/geovision/test/MainActivity.java')
s = p.read_text(encoding='utf-8')

# This patch runs AFTER patch_mainactivity_keybox.py, so Intent and
# ActivityNotFoundException are already imported. Keep the HTML social URLs
# unchanged: only teach the Android WebView host how to hand non-web schemes
# to Android instead of rendering ERR_UNKNOWN_URL_SCHEME.

method_anchor = """    private void initTts() {
"""
method = r"""    private boolean openExternalDeepLink(String url) {
        if (url == null || url.trim().isEmpty()) return false;
        try {
            android.net.Uri uri = android.net.Uri.parse(url);
            String scheme = uri.getScheme();
            if (scheme == null) return false;

            // Normal web pages keep the existing GeoVision/WebView behaviour.
            if ("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme)) {
                return false;
            }

            if (url.startsWith("intent://") || "intent".equalsIgnoreCase(scheme)) {
                Intent intent = Intent.parseUri(url, Intent.URI_INTENT_SCHEME);
                intent.addCategory(Intent.CATEGORY_BROWSABLE);
                intent.setComponent(null);
                intent.setSelector(null);
                try {
                    startActivity(intent);
                    return true;
                } catch (ActivityNotFoundException e) {
                    String fallback = intent.getStringExtra("browser_fallback_url");
                    if (fallback != null && !fallback.trim().isEmpty()) {
                        try {
                            startActivity(new Intent(Intent.ACTION_VIEW, android.net.Uri.parse(fallback)));
                        } catch (Exception ignored) { }
                    }
                    return true;
                }
            }

            // Covers instagram://search?... and any other explicit app scheme.
            Intent intent = new Intent(Intent.ACTION_VIEW, uri);
            intent.addCategory(Intent.CATEGORY_BROWSABLE);
            try {
                startActivity(intent);
            } catch (ActivityNotFoundException e) {
                // Consume the navigation so WebView never shows the ugly
                // ERR_UNKNOWN_URL_SCHEME page if the target app is absent.
                android.util.Log.w("GeoVisionLink", "No app for deep link: " + url);
            }
            return true;
        } catch (Exception e) {
            android.util.Log.e("GeoVisionLink", "Deep link error: " + url, e);
            // Non-web schemes must never be rendered inside WebView.
            return true;
        }
    }

    private void initTts() {
"""
if method_anchor not in s:
    raise SystemExit('initTts anchor not found')
s = s.replace(method_anchor, method, 1)

client_anchor = """            @Override
            @SuppressWarnings(\"deprecation\")
            public android.webkit.WebResourceResponse shouldInterceptRequest(
                    WebView view, String url) {
                return assetLoader.shouldInterceptRequest(android.net.Uri.parse(url));
            }
        });
"""
client_replacement = """            @Override
            @SuppressWarnings(\"deprecation\")
            public android.webkit.WebResourceResponse shouldInterceptRequest(
                    WebView view, String url) {
                return assetLoader.shouldInterceptRequest(android.net.Uri.parse(url));
            }

            @Override
            public boolean shouldOverrideUrlLoading(
                    WebView view, android.webkit.WebResourceRequest request) {
                String url = request != null && request.getUrl() != null
                        ? request.getUrl().toString() : null;
                return MainActivity.this.openExternalDeepLink(url);
            }

            @Override
            @SuppressWarnings(\"deprecation\")
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return MainActivity.this.openExternalDeepLink(url);
            }
        });
"""
if client_anchor not in s:
    raise SystemExit('WebViewClient anchor not found')
s = s.replace(client_anchor, client_replacement, 1)

assert 'shouldOverrideUrlLoading' in s
assert 'Intent.parseUri(url, Intent.URI_INTENT_SCHEME)' in s
assert 'openExternalDeepLink' in s
assert 'ERR_UNKNOWN_URL_SCHEME' in s

p.write_text(s, encoding='utf-8')
print('native social deep-link handling patched')
