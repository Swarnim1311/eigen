/**
 * History — persistent local calculations (SQLite, offline).
 * Reopen restores a record into the session; missing image files are
 * reported gracefully; clear-all requires confirmation.
 */

import { useLocalSearchParams, useRouter } from 'expo-router';
import { useFocusEffect } from 'expo-router';
import React, { useCallback, useState } from 'react';
import { Alert, Image, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { Card, EigenButton, EmptyState, LoadingState, Notice } from '../src/components/ui';
import {
  clearCalculations,
  deleteCalculation,
  getCalculation,
  listCalculations,
  type HistoryRecord,
} from '../src/storage/history';
import { setSession } from '../src/state/session';
import { colors, layout, spacing, typography } from '../src/theme/tokens';

export default function HistoryScreen() {
  const router = useRouter();
  const { open } = useLocalSearchParams<{ open?: string }>();
  const [items, setItems] = useState<HistoryRecord[] | null>(null);
  const [detail, setDetail] = useState<HistoryRecord | null>(null);
  const [detailImageBroken, setDetailImageBroken] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setItems(await listCalculations(100));
    } catch {
      setError('Could not read local history.');
      setItems([]);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void load();
    }, [load]),
  );

  // Deep-link from Home recent list: /history?open=<id>
  useFocusEffect(
    useCallback(() => {
      if (!open || Array.isArray(open)) return;
      void getCalculation(open)
        .then((r) => {
          if (r) {
            setDetailImageBroken(false);
            setDetail(r);
          }
        })
        .catch(() => undefined);
    }, [open]),
  );

  function reopen(r: HistoryRecord) {
    setSession({
      imageUri: r.imageUri,
      originalLatex: r.originalLatex,
      corrected: r.correctedExpression,
      beamScore: null,
      modelId: r.modelId,
      reopenedId: r.id,
    });
    router.push('/review');
  }

  async function remove(id: string) {
    await deleteCalculation(id);
    if (detail?.id === id) setDetail(null);
    await load();
  }

  function confirmClear() {
    Alert.alert(
      'Clear all history?',
      'This permanently deletes every saved calculation on this device.',
      [
        { text: 'Keep', style: 'cancel' },
        {
          text: 'Delete all',
          style: 'destructive',
          onPress: () => {
            void clearCalculations()
              .then(() => {
                setDetail(null);
                return load();
              })
              .catch(() => setError('Could not clear history.'));
          },
        },
      ],
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {detail ? (
        <Card>
          <Text style={styles.label}>Saved calculation</Text>
          {detail.imageUri && !detailImageBroken ? (
            <Image
              source={{ uri: detail.imageUri }}
              style={styles.thumb}
              resizeMode="cover"
              onError={() => setDetailImageBroken(true)}
            />
          ) : (
            <Notice
              kind="info"
              text={
                detail.imageUri
                  ? 'The original image file is no longer on this device. The saved expression and result below are intact.'
                  : 'No image was stored with this record.'
              }
            />
          )}
          <Text style={styles.meta}>
            {detail.operation} · {new Date(detail.createdAt).toLocaleString()}
            {detail.modelId ? ` · ${detail.modelId}` : ''}
          </Text>
          <Text style={styles.sectionTitle}>Original LaTeX</Text>
          <Text style={styles.mono} selectable>
            {detail.originalLatex || '(none)'}
          </Text>
          <Text style={styles.sectionTitle}>Expression used</Text>
          <Text style={styles.mono} selectable>
            {detail.correctedExpression}
          </Text>
          <Text style={styles.sectionTitle}>Result</Text>
          <Text style={styles.result} selectable>
            {detail.result}
          </Text>
          <EigenButton title="Reopen and edit" onPress={() => reopen(detail)} />
          <EigenButton title="Back to list" variant="secondary" onPress={() => setDetail(null)} />
        </Card>
      ) : null}

      {items === null ? (
        <LoadingState message="Reading local history…" />
      ) : error ? (
        <Notice kind="info" text={error} />
      ) : items.length === 0 ? (
        <Card>
          <EmptyState message="History is empty. Successful calculations save here automatically and stay on this device." />
        </Card>
      ) : (
        <>
          {!detail ? (
            <Text style={styles.count}>
              {items.length} saved calculation{items.length === 1 ? '' : 's'} (this device only)
            </Text>
          ) : null}
          {items.map((r) => (
            <Card key={r.id}>
              <TouchableOpacity
                accessibilityRole="button"
                onPress={() => {
                  setDetailImageBroken(false);
                  setDetail(r);
                }}>
                <View style={styles.row}>
                  {r.imageUri ? (
                    <Image source={{ uri: r.imageUri }} style={styles.rowThumb} resizeMode="cover" />
                  ) : (
                    <View style={[styles.rowThumb, styles.rowThumbEmpty]} />
                  )}
                  <View style={styles.rowBody}>
                    <Text style={styles.op}>{r.operation}</Text>
                    <Text style={styles.expr} numberOfLines={1}>
                      {r.correctedExpression}
                    </Text>
                    <Text style={styles.resultSmall} numberOfLines={1}>
                      = {r.result}
                    </Text>
                    <Text style={styles.meta}>{new Date(r.createdAt).toLocaleString()}</Text>
                  </View>
                </View>
              </TouchableOpacity>
              <View style={styles.actions}>
                <EigenButton title="Reopen" variant="secondary" onPress={() => reopen(r)} />
                <EigenButton
                  title="Delete"
                  variant="danger"
                  onPress={() =>
                    Alert.alert('Delete this calculation?', 'This cannot be undone.', [
                      { text: 'Keep', style: 'cancel' },
                      { text: 'Delete', style: 'destructive', onPress: () => void remove(r.id) },
                    ])
                  }
                />
              </View>
            </Card>
          ))}
          <EigenButton title="Clear all history" variant="danger" onPress={confirmClear} />
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.md, maxWidth: layout.maxContentWidth, alignSelf: 'center', width: '100%' },
  count: { fontSize: typography.small, color: colors.inkMuted, marginBottom: spacing.sm },
  label: { fontSize: typography.heading, fontWeight: '700', color: colors.ink, marginBottom: spacing.sm },
  sectionTitle: { fontSize: typography.small, color: colors.inkMuted, marginTop: spacing.md },
  mono: { fontSize: typography.mono, fontFamily: 'monospace', color: colors.ink },
  result: { fontSize: typography.title, fontWeight: '700', color: colors.success },
  op: { fontSize: typography.small, color: colors.inkMuted },
  expr: { fontSize: typography.body, fontFamily: 'monospace', color: colors.ink },
  resultSmall: { fontSize: typography.body, color: colors.success, fontWeight: '600' },
  meta: { fontSize: typography.small, color: colors.inkMuted, marginTop: spacing.xs },
  thumb: { width: '100%', height: 180, borderRadius: layout.radius, backgroundColor: colors.surfaceMuted },
  row: { flexDirection: 'row', gap: spacing.md },
  rowThumb: { width: 72, height: 72, borderRadius: layout.radius, backgroundColor: colors.surfaceMuted },
  rowThumbEmpty: { borderWidth: 1, borderColor: colors.border },
  rowBody: { flex: 1 },
  actions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
});
