export const LANG_NAMES: Record<string, string> = {
  auto: 'Auto detect',
  en: 'English',
  ru: 'Russian',
  uk: 'Ukrainian',
  de: 'German',
  fr: 'French',
  es: 'Spanish',
  it: 'Italian',
  pl: 'Polish',
  tr: 'Turkish',
  zh: 'Chinese',
  ja: 'Japanese',
};

export const LANG_FLAGS: Record<string, string> = {
  auto: '🌐',
  en: '🇬🇧',
  ru: '🇷🇺',
  uk: '🇺🇦',
  de: '🇩🇪',
  fr: '🇫🇷',
  es: '🇪🇸',
  it: '🇮🇹',
  pl: '🇵🇱',
  tr: '🇹🇷',
  zh: '🇨🇳',
  ja: '🇯🇵',
};

export const LANGUAGE_OPTIONS = Object.keys(LANG_NAMES).map((code) => ({
  value: code,
  label: `${LANG_FLAGS[code] ?? '🌐'} ${LANG_NAMES[code]}`,
}));

import { LANG_NAMES_LOCALIZED } from '../i18n';

export function getLangLabel(code: string, locale?: string) {
  const localizedNames = locale ? LANG_NAMES_LOCALIZED[locale] : undefined;
  const name = localizedNames?.[code] ?? LANG_NAMES[code] ?? code.toUpperCase();
  return `${LANG_FLAGS[code] ?? '🌐'} ${name}`;
}
