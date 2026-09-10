/** Helpers for Telegram haptic feedback. All calls are safe outside Telegram. */

type TgWebApp = NonNullable<NonNullable<typeof window.Telegram>['WebApp']>;
type TgHaptic = TgWebApp['HapticFeedback'];

function haptic(): TgHaptic | undefined {
  return window.Telegram?.WebApp?.HapticFeedback;
}

export function hapticImpact(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'): void {
  try {
    haptic()?.impactOccurred(style);
  } catch {
    // unsupported
  }
}

export function hapticNotification(type: 'error' | 'success' | 'warning'): void {
  try {
    haptic()?.notificationOccurred(type);
  } catch {
    // unsupported
  }
}

export function hapticSelection(): void {
  try {
    haptic()?.selectionChanged();
  } catch {
    // unsupported
  }
}
