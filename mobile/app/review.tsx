/**
 * Expression review — rendered LaTeX is shown SEPARATELY from the editable
 * expression. The original prediction is preserved for comparison; the
 * user must be able to correct before any calculation happens.
 */

import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput } from 'react-native';

import { LatexView } from '../src/components/LatexView';
import { Card, EigenButton, Notice } from '../src/components/ui';
import { getSession, setSession } from '../src/state/session';
import { colors, layout, spacing, typography } from '../src/theme/tokens';

export default function ReviewScreen() {
  const router = useRouter();
  const session = getSession();
  const [draft, setDraft] = useState(session.corrected);
  // Edited-state = draft differs from the expression the user was given to
  // edit. (Comparing against originalLatex too would flag untouched drafts,
  // because `corrected` is usually the ASCII conversion, not the raw LaTeX.)
  const changed = draft !== session.corrected;

  if (!session.imageUri || (session.originalLatex === null && !session.reopenedId)) {
    return (
      <ScrollView contentContainerStyle={styles.container}>
        <Notice kind="info" text="Nothing to review yet — recognize an image or reopen a saved calculation first." />
        <EigenButton title="Back home" onPress={() => router.replace('/')} />
      </ScrollView>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      {session.originalLatex !== null ? (
        <Card>
          <Text style={styles.label}>Original prediction (kept for comparison)</Text>
          <Text style={styles.mono} selectable>
            {session.originalLatex || '(empty prediction)'}
          </Text>
        </Card>
      ) : null}

      <Card>
        <Text style={styles.label}>Rendered preview (best effort)</Text>
        {draft.trim() ? (
          <LatexView latex={draft} />
        ) : (
          <Notice kind="info" text="Type your corrected expression below to preview it." />
        )}
      </Card>

      <Card>
        <Text style={styles.label}>Editable expression</Text>
        <TextInput
          accessibilityLabel="Corrected mathematical expression"
          value={draft}
          onChangeText={setDraft}
          multiline
          autoCapitalize="none"
          autoCorrect={false}
          style={styles.input}
          placeholder="e.g. 2*x + sqrt(16)"
        />
        <Text style={styles.hint}>
          Grammar: numbers, + - * / ^, parentheses, sqrt(), variables x y z t, one = for equations.
          LaTeX subset: \frac, \cdot, \times, \div.
        </Text>
      </Card>

      {changed ? (
        <Notice kind="info" text="You edited the expression. The original prediction above is unchanged." />
      ) : null}

      <EigenButton
        title="Continue to calculate"
        disabled={!draft.trim()}
        onPress={() => {
          setSession({ corrected: draft.trim() });
          router.push('/result');
        }}
      />
      <EigenButton title="Retry recognition" variant="secondary" onPress={() => router.push('/recognize')} />
      <EigenButton title="Back to image" variant="secondary" onPress={() => router.push('/capture')} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.md, maxWidth: layout.maxContentWidth, alignSelf: 'center', width: '100%' },
  label: { fontSize: typography.heading, fontWeight: '700', color: colors.ink, marginBottom: spacing.sm },
  mono: { fontSize: typography.mono, fontFamily: 'monospace', color: colors.ink },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: layout.radius,
    padding: spacing.md,
    fontSize: typography.mono,
    fontFamily: 'monospace',
    color: colors.ink,
    backgroundColor: colors.background,
    minHeight: 88,
    textAlignVertical: 'top',
  },
  hint: { fontSize: typography.small, color: colors.inkMuted, marginTop: spacing.sm },
});
