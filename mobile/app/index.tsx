/**
 * Home — branding, scan/import actions, recent calculations, history access.
 * History reads are local SQLite: this screen works fully offline.
 */

import { useFocusEffect, useRouter } from 'expo-router';
import React, { useCallback, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { Card, EigenButton, EmptyState, LoadingState } from '../src/components/ui';
import { listCalculations, type HistoryRecord } from '../src/storage/history';
import { resetSession } from '../src/state/session';
import { colors, layout, spacing, typography } from '../src/theme/tokens';

export default function HomeScreen() {
  const router = useRouter();
  const [recent, setRecent] = useState<HistoryRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setRecent(await listCalculations(5));
    } catch {
      setError('Could not load local history.');
      setRecent([]);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.brand}>
        <Text style={styles.brandMark}>∑ Eigen</Text>
        <Text style={styles.tagline}>Photograph handwritten math — check it — calculate.</Text>
      </View>

      <EigenButton
        title="Scan with camera"
        onPress={() => {
          resetSession();
          router.push('/capture?pick=camera');
        }}
      />
      <EigenButton
        title="Import image"
        variant="secondary"
        onPress={() => {
          resetSession();
          router.push('/capture?pick=gallery');
        }}
      />

      <View style={styles.row}>
        <Text style={styles.section}>Recent calculations</Text>
        <TouchableOpacity
          accessibilityRole="button"
          onPress={() => router.push('/history')}
          style={styles.linkHit}>
          <Text style={styles.link}>History</Text>
        </TouchableOpacity>
      </View>

      {recent === null ? (
        <LoadingState message="Loading local history…" />
      ) : error ? (
        <Text style={styles.error}>{error}</Text>
      ) : recent.length === 0 ? (
        <Card>
          <EmptyState message="No saved calculations yet. Scan or import an equation to begin — it will appear here." />
        </Card>
      ) : (
        recent.map((r) => (
          <TouchableOpacity
            key={r.id}
            accessibilityRole="button"
            onPress={() => router.push(`/history?open=${encodeURIComponent(r.id)}`)}>
            <Card>
              <Text style={styles.op}>{r.operation}</Text>
              <Text style={styles.expr} numberOfLines={1}>
                {r.correctedExpression}
              </Text>
              <Text style={styles.result} numberOfLines={2}>
                = {r.result}
              </Text>
            </Card>
          </TouchableOpacity>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.md, maxWidth: layout.maxContentWidth, alignSelf: 'center', width: '100%' },
  brand: { paddingVertical: spacing.lg, alignItems: 'center' },
  brandMark: { fontSize: typography.brand, fontWeight: '800', color: colors.ink },
  tagline: { fontSize: typography.small, color: colors.inkMuted, textAlign: 'center', marginTop: spacing.xs },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: spacing.lg },
  section: { fontSize: typography.heading, fontWeight: '700', color: colors.ink },
  linkHit: { minHeight: layout.touchTarget, justifyContent: 'center', paddingHorizontal: spacing.sm },
  link: { color: colors.accent, fontSize: typography.body, fontWeight: '600' },
  op: { fontSize: typography.small, color: colors.inkMuted },
  expr: { fontSize: typography.body, color: colors.ink, fontFamily: 'monospace', marginTop: spacing.xs },
  result: { fontSize: typography.body, color: colors.success, fontWeight: '600', marginTop: spacing.xs },
  error: { color: colors.danger, fontSize: typography.body, textAlign: 'center' },
});
