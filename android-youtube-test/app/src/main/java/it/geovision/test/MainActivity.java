package it.geovision.test;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.webkit.ConsoleMessage;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;

import androidx.webkit.WebViewAssetLoader;
import androidx.webkit.WebViewClientCompat;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

public class MainActivity extends Activity {
    private WebView webView;
    private TextToSpeech tts;
    private boolean ttsReady = false;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final List<PendingSpeech> pendingSpeech = new ArrayList<>();

    private static class PendingSpeech {
        final String text;
        final boolean append;
        PendingSpeech(String text, boolean append) {
            this.text = text;
            this.append = append;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setGeolocationEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccess(false);
        settings.setSupportMultipleWindows(false);
        settings.setJavaScriptCanOpenWindowsAutomatically(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);

        initTts();
        webView.addJavascriptInterface(new NativeTtsBridge(), "GeoVisionTTS");

        final WebViewAssetLoader assetLoader =
                new WebViewAssetLoader.Builder()
                        .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                        .build();

        webView.setWebViewClient(new WebViewClientCompat() {
            @Override
            public android.webkit.WebResourceResponse shouldInterceptRequest(
                    WebView view, android.webkit.WebResourceRequest request) {
                return assetLoader.shouldInterceptRequest(request.getUrl());
            }

            @Override
            @SuppressWarnings("deprecation")
            public android.webkit.WebResourceResponse shouldInterceptRequest(
                    WebView view, String url) {
                return assetLoader.shouldInterceptRequest(android.net.Uri.parse(url));
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage cm) {
                android.util.Log.e("GeoVisionJS", cm.message()+" @"+cm.lineNumber()+" "+cm.sourceId());
                return true;
            }

            @Override
            public void onGeolocationPermissionsShowPrompt(
                    String origin, GeolocationPermissions.Callback callback) {
                if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                        == PackageManager.PERMISSION_GRANTED) {
                    callback.invoke(origin, true, false);
                } else {
                    requestPermissions(new String[]{
                            Manifest.permission.ACCESS_FINE_LOCATION,
                            Manifest.permission.ACCESS_COARSE_LOCATION
                    }, 44);
                    callback.invoke(origin, true, false);
                }
            }

            @Override
            public void onPermissionRequest(PermissionRequest request) {
                runOnUiThread(() -> request.grant(request.getResources()));
            }
        });

        webView.loadUrl("https://appassets.androidplatform.net/assets/geovision.html");
    }

    private void initTts() {
        tts = new TextToSpeech(this, status -> {
            if (status != TextToSpeech.SUCCESS) return;
            int lang = tts.setLanguage(Locale.ITALY);
            if (lang == TextToSpeech.LANG_MISSING_DATA || lang == TextToSpeech.LANG_NOT_SUPPORTED) {
                tts.setLanguage(Locale.ITALIAN);
            }
            tts.setSpeechRate(1.02f);
            tts.setPitch(1.0f);
            tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
                @Override public void onStart(String utteranceId) { notifyTtsState("start"); }
                @Override public void onDone(String utteranceId) {
                    if (tts != null && !tts.isSpeaking()) notifyTtsState("done");
                }
                @Override public void onError(String utteranceId) { notifyTtsState("error"); }
            });
            ttsReady = true;
            flushPendingSpeech();
        });
    }

    private void notifyTtsState(String state) {
        main.post(() -> {
            if (webView != null) {
                webView.evaluateJavascript(
                        "window.gvNativeTtsState&&window.gvNativeTtsState('" + state + "')", null);
            }
        });
    }

    private void speakNative(String text, boolean append) {
        if (text == null || text.trim().isEmpty()) return;
        main.post(() -> {
            if (!ttsReady || tts == null) {
                synchronized (pendingSpeech) {
                    if (!append) pendingSpeech.clear();
                    pendingSpeech.add(new PendingSpeech(text, append));
                }
                return;
            }
            int queueMode = append ? TextToSpeech.QUEUE_ADD : TextToSpeech.QUEUE_FLUSH;
            tts.speak(text, queueMode, null, UUID.randomUUID().toString());
        });
    }

    private void flushPendingSpeech() {
        main.post(() -> {
            List<PendingSpeech> copy;
            synchronized (pendingSpeech) {
                copy = new ArrayList<>(pendingSpeech);
                pendingSpeech.clear();
            }
            for (PendingSpeech p : copy) speakNative(p.text, p.append);
        });
    }

    private void stopNative() {
        main.post(() -> {
            synchronized (pendingSpeech) { pendingSpeech.clear(); }
            if (tts != null) tts.stop();
            notifyTtsState("done");
        });
    }

    private class NativeTtsBridge {
        @JavascriptInterface public void speak(String text, boolean append) { speakNative(text, append); }
        @JavascriptInterface public void stop() { stopNative(); }
        @JavascriptInterface public boolean isReady() { return ttsReady; }
    }

    @Override
    public void onBackPressed() {
        webView.evaluateJavascript(
                "(function(){var p=document.getElementById('youtubeInternalModal');if(p){var f=document.getElementById('ytModalFrame');if(f)f.src='';p.remove();return 'closed'};var r=document.getElementById('youtubeResultsModal');if(r){r.remove();return 'closed'};return 'none'})()",
                value -> {
                    if ("\"closed\"".equals(value)) return;
                    if (webView != null && webView.canGoBack()) webView.goBack();
                    else MainActivity.super.onBackPressed();
                });
    }

    @Override
    protected void onDestroy() {
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
        if (webView != null) webView.destroy();
        super.onDestroy();
    }
}
