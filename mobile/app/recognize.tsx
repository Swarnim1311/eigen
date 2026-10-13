/**
 * Recognition — uploads the image to POST /api/v1/recognize.
 *
 * Real loading state, duplicate-submission guard, cancellation that keeps
 * the image, stale-response guard, honest network/server errors, and a
 * persistent experimental-model warning. No progress percentages (nothing
 * to measure them against).
 */

import { useRouter } from 'expo-router';
import React, { useEffect, useRef, useState } from 'react';
import { Image, ScrollView, StyleSheet, Text } from 'react-native';

import { ApiError, describeError, recognizeImage } from '../src/api/client';
import type { RecognizeResponse } from '../src/api/types';
import { Card, EigenButton, ErrorState, LoadingState, Notice } from '../src/components/ui';
import { getSession, setSession } from '../src/state/session';
import { colors, layout, spacing, typography } from '../src/theme/tokens';
import { explainCode } from '../src/utils/validate';

export default function RecognizeScreen() {
  const router = useRouter();
  const [phase, setPhase] = useState<'idle' | 'working' | 'done' | 'failed'>('idle');
  const [failure, setFailure] = useState<string | null>(null);
  const [response, setResponse] = useState<RecognizeResponse | null>(null);
  const inflight = useRef<AbortController | null>(null);
  const requestSeq = useRef(0);
  const imageUri = getSession().imageUri;

  function start() {
    if (!imageUri || inflight.current) return; // duplicate-submission guard
    const seq = ++requestSeq.current;
    const ctrl = new AbortController();
    inflight.current = ctrl;
    setPhase('working');
    setFailure(null);
    setResponse(null);
    void recognizeImage(imageUri, ctrl.signal)
      .then((res) => {
        if (requestSeq.current !== seq) return; // stale response: ignore
        inflight.current = null;
        setResponse(res);
        setPhase('done');
      })
      .catch((e: unknown) => {
        if (requestSeq.current !== seq) return;
        inflight.current = null;
        if (e instanceof DOMException && e.name === 'AbortError') {
          setPhase('idle'); // user-cancelled: image + session preserved
          return;
        }
        const hint = e instanceof ApiError ? explainCode(e.code) : describeError(e);
        setFailure(e instanceof ApiError ? `${e.message} ${hint}` : hint);
        setPhase('failed');
      });
  }

  function cancel() {
    requestSeq.current += 1;
    inflight.current?.abort();
    inflight.current = null;
    setPhase('idle');
  }

  useEffect(() => {
    start();
    return () => {
      requestSeq.current += 1;
      inflight.current?.abort();
      inflight.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!imageUri) {
    return (
      <ScrollView contentContainerStyle={styles.container}>
        <ErrorState
          message="No image in this session (the app may have restarted). Go back and choose an image."
          onRetry={() => router.replace('/capture')}
        />
      </ScrollView>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Notice
        kind="warning"
        text="Recognition is experimental (Phase-1 baseline: 0/30 exact matches). Always check the result on the next screen before calculating."
      />
      <Card>
        <Image source={{ uri: imageUri }} style={styles.preview} resizeMode="contain" />
      </Card>

      {phase === 'working' ? (
        <>
          <LoadingState message="Recognizing handwriting… this can take up to a minute on CPU. You can cancel — your image is kept." />
          <EigenButton title="Cancel" variant="secondary" onPress={cancel} />
        </>
      ) : null}

      {phase === 'failed' && failure ? (
        <>
          <ErrorState message={failure} onRetry={start} />
          <EigenButton title="Back to image" variant="secondary" onPress={() => router.back()} />
        </>
      ) : null}

      {phase === 'done' && response ? (
        <>
          <Card>
            <Text style={styles.label}>Predicted LaTeX (unedited model output)</Text>
            <Text style={styles.mono} selectable>
              {response.latex || '(empty prediction)'}
            </Text>
            <Text style={styles.meta}>
              Model {response.model.id} · experimental · {response.duration_s.toFixed(1)} s
              {response.math_parse.ok ? ' · parses with the v1 grammar' : ' · does NOT parse with the v1 grammar — correction needed'}
            </Text>
          </Card>
          <EigenButton
            title="Review and correct"
            onPress={() => {
              setSession({
                originalLatex: response.latex,
                corrected: response.math_parse.ascii ?? response.latex,
                beamScore: response.beam_score,
                modelId: response.model.id,
              });
              router.push('/review');
            }}
          />
          <EigenButton title="Retry (same image)" variant="secondary" onPress={start} />
          <EigenButton title="Back to image" variant="secondary" onPress={() => router.back()} />
        </>
      ) : null}

      {phase === 'idle' && !response && !failure ? (
        <EigenButton title="Start recognition" onPress={start} />
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.md, maxWidth: layout.maxContentWidth, alignSelf: 'center', width: '100%' },
  preview: { width: '100%', height: 220, backgroundColor: colors.surfaceMuted, borderRadius: layout.radius },
  label: { fontSize: typography.heading, fontWeight: '700', color: colors.ink, marginBottom: spacing.sm },
  mono: { fontSize: typography.mono, fontFamily: 'monospace', color: colors.ink },
  meta: { fontSize: typography.small, color: colors.inkMuted, marginTop: spacing.sm },
});
