import { Button, Card, Group, MultiSelect, Select, Stack, Text, Title } from '@mantine/core';
import { useEffect, useState } from 'react';

import { LANGUAGE_OPTIONS } from '../api/langs';
import { t } from '../i18n';
import type { TranslationEngine, User } from '../types';

interface SettingsProps {
  user: User;
  onSave: (payload: {
    target_language: string;
    favorite_langs: string[];
    preferred_engine: TranslationEngine;
    ui_language?: string;
  }) => Promise<void>;
  isSaving: boolean;
}

export function Settings({ user, onSave, isSaving }: SettingsProps) {
  const [targetLanguage, setTargetLanguage] = useState(user.target_language);
  const [favoriteLangs, setFavoriteLangs] = useState(user.favorite_langs);
  const [engine, setEngine] = useState<TranslationEngine>(user.preferred_engine);
  const [uiLang, setUiLang] = useState(user.ui_language ?? 'en');

  useEffect(() => {
    setTargetLanguage(user.target_language);
    setFavoriteLangs(user.favorite_langs);
    setEngine(user.preferred_engine);
    setUiLang(user.ui_language ?? 'en');
  }, [user.target_language, user.favorite_langs, user.preferred_engine, user.ui_language, user.id]);

  return (
    <Stack gap="md">
      <div>
        <Title order={2}>{t('settings.title', uiLang)}</Title>
        <Text c="dimmed" size="sm">
          {t('settings.desc', uiLang)}
        </Text>
      </div>

      <Card withBorder radius="md" p="md">
        <Stack>
          <Select
            label={t('settings.target_lang', uiLang)}
            data={LANGUAGE_OPTIONS.filter((item) => item.value !== 'auto')}
            value={targetLanguage}
            onChange={(value) => value && setTargetLanguage(value)}
          />
          <MultiSelect
            label={t('settings.favorite_langs', uiLang)}
            data={LANGUAGE_OPTIONS.filter((item) => item.value !== 'auto')}
            value={favoriteLangs}
            onChange={setFavoriteLangs}
          />
          <Select
            label={t('settings.engine', uiLang)}
            data={[
              { value: 'auto', label: t('settings.engine_auto', uiLang) },
              { value: 'google_free', label: t('settings.engine_google', uiLang) },
              { value: 'deepl', label: t('settings.engine_deepl', uiLang) },
            ]}
            value={engine}
            onChange={(value) => value && setEngine(value as TranslationEngine)}
          />
          <Select
            label={t('settings.ui_language', uiLang)}
            data={[
              { value: 'ru', label: t('settings.ui_lang_ru', uiLang) },
              { value: 'uk', label: t('settings.ui_lang_uk', uiLang) },
              { value: 'en', label: t('settings.ui_lang_en', uiLang) },
            ]}
            value={uiLang}
            onChange={(value) => value && setUiLang(value)}
          />
          <Group justify="flex-end">
            <Button
              loading={isSaving}
              onClick={() =>
                onSave({
                  target_language: targetLanguage,
                  favorite_langs: favoriteLangs,
                  preferred_engine: engine,
                  ui_language: uiLang,
                })
              }
            >
              {t('settings.save_btn', uiLang)}
            </Button>
          </Group>
        </Stack>
      </Card>
    </Stack>
  );
}
