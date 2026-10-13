/**
 * LaTeX renderer for Android + iOS (Expo Go compatible).
 *
 * Strategy: `katex.renderToString` (pure JS, no native modules) produces
 * static HTML, displayed in `react-native-webview` with JavaScript DISABLED
 * and no remote resources — untrusted model output can therefore never
 * execute code or exfiltrate data. The pinned KaTeX stylesheet is bundled
 * verbatim (`./katexCss.ts`) so fractions/roots/spacing lay out correctly;
 * KaTeX webfonts are NOT bundled (offline WebView cannot resolve them), so
 * glyphs fall back to system serif — visually UNVERIFIED on device (Phase 3).
 * Invalid/unsupported LaTeX falls back to
 * a monospace source view with an explanatory note (never a crash).
 */

import React, { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { WebView } from 'react-native-webview';
import katex from 'katex';

import { colors, layout, spacing, typography } from '../theme/tokens';
import { KATEX_CSS } from './katexCss';

const INLINE_CSS = `
  body { margin:0; padding:12px; font-family: Georgia, 'Times New Roman', serif;
         color:#1B2430; font-size:19px; }
  .katex { font-size: 1.15em; }
  .katex-display { margin: 0; overflow-x: auto; }
  .eq-fallback { font-family: monospace; font-size: 15px; word-break: break-all; }
`;

function buildHtml(rendered: string): string {
  // KaTeX layout stylesheet first (verbatim from pinned dep), then small
  // app overrides. @font-face URLs inside KATEX_CSS resolve to nothing in
  // this offline WebView by design — glyphs fall back to system serif.
  return `<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>${KATEX_CSS}</style><style>${INLINE_CSS}</style></head><body>${rendered}</body></html>`;
}

export function LatexView({ latex }: { latex: string }) {
  const { html, failed } = useMemo(() => {
    const trimmed = latex.trim();
    if (!trimmed) return { html: null as string | null, failed: true };
    try {
      const rendered = katex.renderToString(trimmed, {
        throwOnError: true,
        displayMode: true,
        strict: true,
        trust: false,
      });
      return { html: buildHtml(rendered), failed: false };
    } catch {
      return { html: null as string | null, failed: true };
    }
  }, [latex]);

  if (failed || !html) {
    return (
      <View style={styles.fallback}>
        <Text style={styles.source} selectable>
          {latex}
        </Text>
        <Text style={styles.note}>
          Preview unavailable — this LaTeX uses unsupported syntax. The source above is exact; you
          can still edit and calculate with it.
        </Text>
      </View>
    );
  }
  return (
    <View style={styles.frame}>
      <WebView
        originWhitelist={['about:blank']}
        source={{ html, baseUrl: 'about:blank' }}
        javaScriptEnabled={false}
        domStorageEnabled={false}
        allowFileAccess={false}
        allowUniversalAccessFromFileURLs={false}
        mixedContentMode="never"
        style={styles.web}
        scrollEnabled={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  frame: {
    minHeight: 84,
    height: 120,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: layout.radius,
    overflow: 'hidden',
  },
  web: { flex: 1, backgroundColor: 'transparent' },
  fallback: { padding: spacing.md, gap: spacing.sm },
  source: { fontSize: typography.mono, color: colors.ink, fontFamily: 'monospace' },
  note: { fontSize: typography.small, color: colors.inkMuted },
});
