import { Stack } from 'expo-router';
import { colors } from '../src/theme/tokens';

export default function RootLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: colors.surface },
        headerTintColor: colors.ink,
        contentStyle: { backgroundColor: colors.background },
      }}>
      <Stack.Screen name="index" options={{ title: 'Eigen' }} />
      <Stack.Screen name="capture" options={{ title: 'Capture' }} />
      <Stack.Screen name="recognize" options={{ title: 'Recognize' }} />
      <Stack.Screen name="review" options={{ title: 'Review expression' }} />
      <Stack.Screen name="result" options={{ title: 'Result' }} />
      <Stack.Screen name="history" options={{ title: 'History' }} />
    </Stack>
  );
}
