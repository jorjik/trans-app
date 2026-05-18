import { Button, Card, Group, MultiSelect, Select, Stack, Text, Title } from '@mantine/core';
import { useEffect, useState } from 'react';

import { LANGUAGE_OPTIONS } from '../api/langs';
import type { TranslationEngine, User } from '../types';

interface SettingsProps {
  user: User;
  onSave: (payload: {
    target_language: string;
    favorite_langs: string[];
    preferred_engine: TranslationEngine;
  }) => Promise<void>;
  isSaving: boolean;
}

export function Settings({ user, onSave, isSaving }: SettingsProps) {
  const [targetLanguage, setTargetLanguage] = useState(user.target_language);
  const [favoriteLangs, setFavoriteLangs] = useState(user.favorite_langs);
  const [engine, setEngine] = useState<TranslationEngine>(user.preferred_engine);

  useEffect(() => {
    setTargetLanguage(user.target_language);
    setFavoriteLangs(user.favorite_langs);
    setEngine(user.preferred_engine);
  }, [user.target_language, user.favorite_langs, user.preferred_engine, user.id]);

  return (
    <Stack gap="md">
      <div>
        <Title order={2}>Settings</Title>
        <Text c="dimmed" size="sm">
          Configure your default translation preferences.
        </Text>
      </div>

      <Card withBorder radius="md" p="md">
        <Stack>
          <Select
            label="Target language"
            data={LANGUAGE_OPTIONS.filter((item) => item.value !== 'auto')}
            value={targetLanguage}
            onChange={(value) => value && setTargetLanguage(value)}
          />
          <MultiSelect
            label="Favorite languages"
            data={LANGUAGE_OPTIONS.filter((item) => item.value !== 'auto')}
            value={favoriteLangs}
            onChange={setFavoriteLangs}
          />
          <Select
            label="Translation engine"
            data={[
              { value: 'auto', label: 'Auto' },
              { value: 'google_free', label: 'Google Free' },
              { value: 'deepl', label: 'DeepL' },
            ]}
            value={engine}
            onChange={(value) => value && setEngine(value as TranslationEngine)}
          />
          <Group justify="flex-end">
            <Button
              loading={isSaving}
              onClick={() =>
                onSave({
                  target_language: targetLanguage,
                  favorite_langs: favoriteLangs,
                  preferred_engine: engine,
                })
              }
            >
              Save changes
            </Button>
          </Group>
        </Stack>
      </Card>
    </Stack>
  );
}
