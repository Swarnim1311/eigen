/**
 * Reusable UI primitives: buttons, cards, and loading/error/empty/success
 * states. One small file keeps the visual language consistent.
 */

import React from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { colors, layout, spacing, typography } from '../theme/tokens';

export function EigenButton({
  title,
  onPress,
  disabled,
  variant = 'primary',
}: {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'danger';
}) {
  return (
    <TouchableOpacity
      accessibilityRole="button"
      onPress={onPress}
      disabled={disabled}
      style={[
        styles.button,
        variant === 'primary' && styles.buttonPrimary,
        variant === 'secondary' && styles.buttonSecondary,
        variant === 'danger' && styles.buttonDanger,
        disabled && styles.buttonDisabled,
      ]}>
      <Text
        style={[
          styles.buttonText,
          variant === 'secondary' && styles.buttonTextSecondary,
          disabled && styles.buttonTextDisabled,
        ]}>
        {title}
      </Text>
    </TouchableOpacity>
  );
}

export function Card({ children }: { children: React.ReactNode }) {
  return <View style={styles.card}>{children}</View>;
}

export function LoadingState({ message }: { message: string }) {
  return (
    <View style={styles.state} accessibilityLiveRegion="polite">
      <ActivityIndicator size="large" color={colors.accent} />
      <Text style={styles.stateText}>{message}</Text>
    </View>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <View style={[styles.state, styles.errorBox]}>
      <Text style={styles.errorTitle}>Something needs attention</Text>
      <Text style={styles.stateText}>{message}</Text>
      {onRetry ? <EigenButton title="Try again" onPress={onRetry} variant="secondary" /> : null}
    </View>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <View style={styles.state}>
      <Text style={styles.emptyGlyph}>∅</Text>
      <Text style={styles.stateText}>{message}</Text>
    </View>
  );
}

export function Notice({ kind, text }: { kind: 'warning' | 'success' | 'info'; text: string }) {
  return (
    <View
      style={[
        styles.notice,
        kind === 'warning' && styles.noticeWarning,
        kind === 'success' && styles.noticeSuccess,
        kind === 'info' && styles.noticeInfo,
      ]}>
      <Text style={styles.noticeText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: layout.touchTarget,
    borderRadius: layout.radius,
    paddingHorizontal: spacing.lg,
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: spacing.xs,
  },
  buttonPrimary: { backgroundColor: colors.accent },
  buttonSecondary: { backgroundColor: colors.surfaceMuted, borderWidth: 1, borderColor: colors.border },
  buttonDanger: { backgroundColor: colors.danger },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { color: colors.accentInk, fontSize: typography.body, fontWeight: '600' },
  buttonTextSecondary: { color: colors.ink },
  buttonTextDisabled: {},
  card: {
    backgroundColor: colors.surface,
    borderRadius: layout.radius,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginVertical: spacing.sm,
  },
  state: { alignItems: 'center', padding: spacing.lg, gap: spacing.sm },
  stateText: { color: colors.inkMuted, fontSize: typography.body, textAlign: 'center' },
  errorBox: {
    backgroundColor: colors.dangerBg,
    borderRadius: layout.radius,
    marginVertical: spacing.sm,
  },
  errorTitle: { color: colors.danger, fontSize: typography.heading, fontWeight: '700' },
  emptyGlyph: { fontSize: 40, color: colors.border },
  notice: { borderRadius: layout.radius, padding: spacing.md, marginVertical: spacing.sm },
  noticeWarning: { backgroundColor: colors.warningBg },
  noticeSuccess: { backgroundColor: colors.successBg },
  noticeInfo: { backgroundColor: colors.surfaceMuted },
  noticeText: { fontSize: typography.small, color: colors.ink },
});
