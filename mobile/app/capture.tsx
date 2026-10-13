/**
 * Capture + image review.
 *
 * Uses `expo-image-picker` only (no custom camera): `launchCameraAsync`
 * for capture, `launchImageLibraryAsync` for gallery, both with the
 * reliable system crop UI (`allowsEditing`). Rotation beyond the system
 * editor is deliberately out of scope — no dependable cross-platform
 * Expo Go library exists for it in this SDK.
 */

import { useLocalSearchParams, useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import React, { useEffect, useRef, useState } from 'react';
import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Card, EigenButton, ErrorState, Notice } from '../src/components/ui';
import { setSession } from '../src/state/session';
import { colors, layout, spacing, typography } from '../src/theme/tokens';
import { validateLocalImage } from '../src/utils/validate';

export default function CaptureScreen() {
  const router = useRouter();
  const { pick } = useLocalSearchParams<{ pick?: string }>();
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const autoRun = useRef(pick === 'camera' || pick === 'gallery');

  async function pickImage(kind: 'camera' | 'gallery') {
    setProblem(null);
    setBusy(true);
    try {
      const options: ImagePicker.ImagePickerOptions = {
        allowsEditing: true,
        quality: 0.9,
        mediaTypes: ['images'],
      };
      const result =
        kind === 'camera'
          ? await ImagePicker.launchCameraAsync({ ...options, cameraType: ImagePicker.CameraType.back })
          : await ImagePicker.launchImageLibraryAsync(options);
      if (result.canceled) return;
      const uri = result.assets?.[0]?.uri ?? null;
      const err = validateLocalImage(uri);
      if (err) {
        setProblem(err);
        return;
      }
      setImageUri(uri);
    } catch {
      setProblem(
        kind === 'camera'
          ? 'Camera unavailable or permission denied. Grant camera access in system settings, or import from the gallery instead.'
          : 'Gallery unavailable or permission denied. Grant photo access in system settings, or use the camera instead.',
      );
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (autoRun.current) {
      autoRun.current = false;
      void pickImage(pick === 'gallery' ? 'gallery' : 'camera');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Capture the equation</Text>
      <Text style={styles.hint}>
        Fill the frame with one handwritten expression. Good light and a flat page read best —
        recognition is experimental either way.
      </Text>

      <EigenButton title={busy ? 'Opening…' : 'Take photo'} disabled={busy} onPress={() => void pickImage('camera')} />
      <EigenButton title={busy ? 'Opening…' : 'Choose from gallery'} variant="secondary" disabled={busy} onPress={() => void pickImage('gallery')} />

      {problem ? <ErrorState message={problem} /> : null}

      {imageUri ? (
        <Card>
          <Text style={styles.label}>Image review</Text>
          <Image source={{ uri: imageUri }} style={styles.preview} resizeMode="contain" />
          <Notice kind="info" text="Check that the equation is sharp and complete. Use Retake/Replace to crop again with the system editor." />
          <EigenButton title="Retake / replace" variant="secondary" onPress={() => void pickImage('camera')} />
          <EigenButton
            title="Continue to recognition"
            onPress={() => {
              setSession({ imageUri, originalLatex: null, corrected: '', reopenedId: null });
              router.push('/recognize');
            }}
          />
        </Card>
      ) : (
        <View style={styles.placeholder}>
          <Text style={styles.placeholderText}>No image yet — take a photo or import one.</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.md, maxWidth: layout.maxContentWidth, alignSelf: 'center', width: '100%' },
  title: { fontSize: typography.title, fontWeight: '800', color: colors.ink },
  hint: { fontSize: typography.small, color: colors.inkMuted, marginVertical: spacing.sm },
  label: { fontSize: typography.heading, fontWeight: '700', color: colors.ink, marginBottom: spacing.sm },
  preview: { width: '100%', height: 300, backgroundColor: colors.surfaceMuted, borderRadius: layout.radius },
  placeholder: { padding: spacing.lg, alignItems: 'center' },
  placeholderText: { color: colors.inkMuted, fontSize: typography.body },
});
