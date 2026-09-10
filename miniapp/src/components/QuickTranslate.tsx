import { Badge, Button, Card, CopyButton, Group, Select, Stack, Text, Textarea, Title } from '@mantine/core';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { translateText } from '../api/client';
import { LANGUAGE_OPTIONS } from '../api/langs';
import { hapticImpact } from '../haptics';
import { t } from '../i18n';
import { useStore } from '../store/useStore';
import type { TranslationEngine } from '../types';

export function QuickTranslate() {
  const queryClient = useQueryClient();
  const token = useStore((state) => state.token);
  const user = useStore((state) => state.user);
  const quickText = useStore((state) => state.quickText);
  const quickResult = useStore((state) => state.quickResult);
  const setQuickText = useStore((state) => state.setQuickText);
  const setQuickResult = useStore((state) => state.setQuickResult);
  const uiLang = user?.ui_language ?? 'en';

  const defaultTarget = user?.target_language ?? (uiLang === 'ru' ? 'ru' : 'en');
  const [targetLang, setTargetLang] = useState(defaultTarget);
  const [engine, setEngine] = useState<TranslationEngine>('auto');
  const [sourceLang, setSourceLang] = useState('auto');

  const mutation = useMutation({
    mutationFn: () =>
      translateText(token as string, {
        text: quickText.trim(),
        source_lang: sourceLang,
        target_lang: targetLang,
        engine,
      }),
    onSuccess: (data) => {
      setQuickResult(data.translated_text);
      void queryClient.invalidateQueries({ queryKey: ['me', token] });
      void queryClient.invalidateQueries({ queryKey: ['stats', token] });
    },
  });

  const run = () => {
    setQuickResult(null);
    mutation.mutate();
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if ((event.key === 'Enter' || event.key === 'NumpadEnter') && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      if (quickText.trim() && !mutation.isPending) run();
    }
  };

  return (
    <Card withBorder radius="md" p="md">
      <Stack gap="sm">
        <div>
<Title order={4}>{t('qt.title', uiLang)}</Title>
         </div>

        <Textarea
          label={t('qt.text_label', uiLang)}
          placeholder={t('qt.text_placeholder', uiLang)}
          minRows={3}
          value={quickText}
          onChange={(e) => setQuickText(e.currentTarget.value)}
          onKeyDown={handleKeyDown}
        />

        <Group grow>
          <Select
            label={t('qt.source', uiLang)}
            data={LANGUAGE_OPTIONS}
            value={sourceLang}
            onChange={(value) => value && setSourceLang(value)}
          />
          <Select
            label={t('qt.target', uiLang)}
            data={LANGUAGE_OPTIONS.filter((item) => item.value !== 'auto')}
            value={targetLang}
            onChange={(value) => value && setTargetLang(value)}
          />
        </Group>

        <Select
          label={t('qt.engine', uiLang)}
          data={[
            { value: 'auto', label: t('settings.engine_auto', uiLang) },
            { value: 'google_free', label: t('settings.engine_google', uiLang) },
            { value: 'deepl', label: t('settings.engine_deepl', uiLang) },
          ]}
          value={engine}
          onChange={(value) => value && setEngine(value as TranslationEngine)}
        />

        <Group justify="space-between">
          <Button
            loading={mutation.isPending}
            disabled={!quickText.trim()}
            onClick={() => {
              hapticImpact('light');
              run();
            }}
          >
            {t('qt.translate_btn', uiLang)}
          </Button>
          {quickText.trim() ? (
            <Text size="sm" c="dimmed">
              {quickText.trim().length.toLocaleString()} {t('qt.chars', uiLang)}
            </Text>
          ) : null}
        </Group>

        {mutation.isError ? (
          <Text size="sm" c="red">
            {mutation.error instanceof Error ? mutation.error.message : t('qt.failed', uiLang)}
          </Text>
        ) : null}

        {quickResult ? (
          <Stack gap={8}>
            <Group justify="space-between" align="center">
              <Group gap="xs">
                <Text size="sm" fw={600}>
                  {t('qt.result', uiLang)}
                </Text>
                {mutation.data?.cached ? (
                  <Badge variant="light" color="grape" size="sm">
                    {t('qt.from_cache', uiLang)}
                  </Badge>
                ) : null}
              </Group>
              <CopyButton value={quickResult}>
                {({ copied, copy }) => (
                  <Button
                    size="compact-sm"
                    variant="light"
                    color={copied ? 'teal' : 'gray'}
                    onClick={() => {
                      copy();
                      hapticImpact('soft');
                    }}
                  >
                    {copied ? t('qt.copied', uiLang) : t('qt.copy', uiLang)}
                  </Button>
                )}
              </CopyButton>
            </Group>
            <Text size="sm">{quickResult}</Text>
            {mutation.data ? (
              <Text size="xs" c="dimmed">
                {t('qt.provider', uiLang, { provider: mutation.data.provider, lang: mutation.data.source_lang_detected })}
                {' · '}
                {t('qt.chars_left', uiLang, { n: mutation.data.chars_remaining.toLocaleString() })}
              </Text>
            ) : null}
          </Stack>
        ) : null}
      </Stack>
    </Card>
  );
}
