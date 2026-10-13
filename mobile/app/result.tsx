/**
 * Mathematical results — Evaluate / Simplify / Solve against the real
 * backend. Only applicable operations are offered; results show exact
 * values plus decimals where the backend provides them. Successful
 * operations auto-save to local history. Failures preserve the
 * expression so the user corrects it in place.
 */

import { useRouter } from 'expo-router';
import React, { useMemo, useRef, useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import {
  ApiError,
  evaluateExpression,
  simplifyExpression,
  solveEquation,
} from '../src/api/client';
import { Card, EigenButton, ErrorState, LoadingState, Notice } from '../src/components/ui';
import { getSession } from '../src/state/session';
import { saveCalculation } from '../src/storage/history';
import { colors, layout, spacing, typography } from '../src/theme/tokens';
import { explainCode } from '../src/utils/validate';

const KNOWN_VARS = ['x', 'y', 'z', 't'];

type Outcome =
  | { kind: 'evaluate'; result: string; decimal: number | null }
  | { kind: 'simplify'; result: string }
  | { kind: 'solve'; variable: string; solutions: string[] };

/** Variables mentioned as bare identifiers (naive but honest pre-check). */
function mentionedVars(expr: string): string[] {
  return KNOWN_VARS.filter((v) => new RegExp(`(^|[^A-Za-z])${v}([^A-Za-z]|$)`).test(expr));
}

export default function ResultScreen() {
  const router = useRouter();
  const session = getSession();
  const expr = session.corrected.trim();
  const isEquation = useMemo(() => expr.includes('='), [expr]);
  const vars = useMemo(() => (isEquation ? [] : mentionedVars(expr)), [expr, isEquation]);

  const [solveVar, setSolveVar] = useState('x');
  const [varValues, setVarValues] = useState<Record<string, string>>({});
  const [working, setWorking] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [savedNote, setSavedNote] = useState(false);
  const savedKey = useRef<string | null>(null);

  async function persist(operation: string, result: string) {
    const key = `${operation}::${expr}::${result}`;
    if (savedKey.current === key) return;
    savedKey.current = key;
    try {
      await saveCalculation({
        imageUri: session.imageUri,
        originalLatex: session.originalLatex ?? '',
        correctedExpression: expr,
        operation,
        result,
        modelId: session.modelId,
      });
      setSavedNote(true);
    } catch {
      setSavedNote(false);
    }
  }

  async function run(kind: 'evaluate' | 'simplify' | 'solve') {
    if (working || !expr) return; // duplicate-calculation guard
    setWorking(kind);
    setFailure(null);
    setOutcome(null);
    setSavedNote(false);
    try {
      if (kind === 'evaluate') {
        const variables: Record<string, number> = {};
        for (const v of vars) {
          const raw = (varValues[v] ?? '').trim();
          if (raw !== '') {
            const n = Number(raw);
            if (!Number.isFinite(n)) throw new ApiError('parse_error', `Value for ${v} is not a number.`, 400);
            variables[v] = n;
          }
        }
        const res = await evaluateExpression({ expression: expr, variables });
        setOutcome({ kind, result: res.result, decimal: res.decimal });
        await persist('evaluate', res.decimal === null ? res.result : `${res.result} ≈ ${res.decimal}`);
      } else if (kind === 'simplify') {
        const res = await simplifyExpression({ expression: expr });
        setOutcome({ kind, result: res.result });
        await persist('simplify', res.result);
      } else {
        const v = solveVar.trim() || 'x';
        const res = await solveEquation({ equation: expr, variable: v });
        setOutcome({ kind, variable: res.variable, solutions: res.solutions });
        await persist(`solve:${res.variable}`, res.solutions.join(', '));
      }
    } catch (e) {
      const hint = e instanceof ApiError ? explainCode(e.code) : String(e);
      setFailure(e instanceof ApiError ? `${e.message} ${hint}` : hint);
    } finally {
      setWorking(null);
    }
  }

  if (!expr) {
    return (
      <ScrollView contentContainerStyle={styles.container}>
        <Notice kind="info" text="No expression to calculate — review one first." />
        <EigenButton title="Back to review" onPress={() => router.replace('/review')} />
      </ScrollView>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      <Card>
        <Text style={styles.label}>Expression (preserved)</Text>
        <Text style={styles.mono} selectable>
          {expr}
        </Text>
        <EigenButton title="Edit expression" variant="secondary" onPress={() => router.push('/review')} />
      </Card>

      {!isEquation ? (
        <>
          <EigenButton title={working === 'evaluate' ? 'Evaluating…' : 'Evaluate'} disabled={working !== null} onPress={() => void run('evaluate')} />
          <EigenButton title={working === 'simplify' ? 'Simplifying…' : 'Simplify'} variant="secondary" disabled={working !== null} onPress={() => void run('simplify')} />
          {vars.length > 0 ? (
            <Card>
              <Text style={styles.label}>Variable values (optional, for Evaluate)</Text>
              {vars.map((v) => (
                <View key={v} style={styles.varRow}>
                  <Text style={styles.varName}>{v} =</Text>
                  <TextInput
                    accessibilityLabel={`Value for ${v}`}
                    value={varValues[v] ?? ''}
                    onChangeText={(t) => setVarValues((s) => ({ ...s, [v]: t }))}
                    keyboardType="numbers-and-punctuation"
                    autoCapitalize="none"
                    autoCorrect={false}
                    style={styles.varInput}
                    placeholder="number"
                  />
                </View>
              ))}
            </Card>
          ) : null}
          <Notice kind="info" text="Solve needs an equation with exactly one '=' (e.g. 2*x+3=7). This input has none, so Solve is not offered." />
        </>
      ) : (
        <>
          <Card>
            <Text style={styles.label}>Solve for variable</Text>
            <View style={styles.varPick}>
              {KNOWN_VARS.map((v) => (
                <EigenButton
                  key={v}
                  title={v}
                  variant={solveVar === v ? 'primary' : 'secondary'}
                  onPress={() => setSolveVar(v)}
                />
              ))}
            </View>
          </Card>
          <EigenButton title={working === 'solve' ? 'Solving…' : `Solve for ${solveVar}`} disabled={working !== null} onPress={() => void run('solve')} />
          <Notice kind="info" text="Evaluate and Simplify need a plain expression without '='. This input is an equation, so only Solve is offered." />
        </>
      )}

      {working ? <LoadingState message="Asking the backend… your expression is preserved." /> : null}
      {failure ? <ErrorState message={failure} /> : null}

      {outcome?.kind === 'evaluate' ? (
        <Card>
          <Text style={styles.label}>Exact result</Text>
          <Text style={styles.result} selectable>
            {outcome.result}
          </Text>
          {outcome.decimal !== null ? (
            <Text style={styles.decimal} selectable>
              ≈ {outcome.decimal}
            </Text>
          ) : null}
          {savedNote ? <Notice kind="success" text="Saved to local history." /> : null}
        </Card>
      ) : null}
      {outcome?.kind === 'simplify' ? (
        <Card>
          <Text style={styles.label}>Simplified</Text>
          <Text style={styles.result} selectable>
            {outcome.result}
          </Text>
          {savedNote ? <Notice kind="success" text="Saved to local history." /> : null}
        </Card>
      ) : null}
      {outcome?.kind === 'solve' ? (
        <Card>
          <Text style={styles.label}>Solutions for {outcome.variable}</Text>
          {outcome.solutions.map((s, i) => (
            <Text key={`${i}-${s}`} style={styles.result} selectable>
              {outcome.variable} = {s}
            </Text>
          ))}
          {savedNote ? <Notice kind="success" text="Saved to local history." /> : null}
        </Card>
      ) : null}

      {outcome ? (
        <EigenButton title="View history" variant="secondary" onPress={() => router.push('/history')} />
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.md, maxWidth: layout.maxContentWidth, alignSelf: 'center', width: '100%' },
  label: { fontSize: typography.heading, fontWeight: '700', color: colors.ink, marginBottom: spacing.sm },
  mono: { fontSize: typography.mono, fontFamily: 'monospace', color: colors.ink },
  result: { fontSize: typography.title, fontWeight: '700', color: colors.success, marginTop: spacing.xs },
  decimal: { fontSize: typography.body, color: colors.inkMuted, marginTop: spacing.xs },
  varRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginVertical: spacing.xs },
  varName: { fontSize: typography.body, color: colors.ink, minWidth: 32 },
  varInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: layout.radius,
    padding: spacing.sm,
    fontSize: typography.body,
    color: colors.ink,
    backgroundColor: colors.background,
    minHeight: layout.touchTarget,
  },
  varPick: { flexDirection: 'row', gap: spacing.sm, flexWrap: 'wrap' },
});
