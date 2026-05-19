import { Button, Card, CopyButton, Group, Select, Stack, Text, Textarea, Title } from '@mantine/core';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { translateText } from '../api/client';
import { LANGUAGE_OPTIONS } from '../api/langs';
import { t } from '../i18n';
import { useStore } from '../store/useStore';
import type { TranslationEngine } from '../types';

export function QuickTranslate() {
  const queryClient = useQueryClient();
  const token = useStore((state) => state.token);
  const user = useStore((state) => state.user);
  const uiLang = user?.ui_language ?? 'en';

  const [text, setText] = useState('');
  const [sourceLang, setSourceLang] = useState('auto');
  const defaultTarget = user?.target_language ?? (uiLang === 'ru' ? 'ru' : 'en');
  const [targetLang, setTargetLang] = useState(defaultTarget);
  const [engine, setEngine] = useState<TranslationEngine>('auto');
  const [result, setResult] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      translateText(token as string, {
        text: text.trim(),
        source_lang: sourceLang,
        target_lang: targetLang,
        engine,
      }),
    onSuccess: (data) => {
      setResult(data.translated_text);
      void queryClient.invalidateQueries({ queryKey: ['me', token] });
      void queryClient.invalidateQueries({ queryKey: ['stats', token] });
    },
  });

  return (
    <Card withBorder radius="md" p="md">
      <Stack gap="sm">
        <div>
          <Title order={4}>{t('qt.title', uiLang)}</Title>
          <Text size="sm" c="dimmed">
            {t('qt.desc', uiLang)}
          </Text>
        </div>

        <Textarea
          label={t('qt.text_label', uiLang)}
          placeholder={t('qt.text_placeholder', uiLang)}
          minRows={3}
          value={text}
          onChange={(e) => setText(e.currentTarget.value)}
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
            disabled={!text.trim()}
            onClick={() => {
              setResult(null);
              mutation.mutate();
            }}
          >
            {t('qt.translate_btn', uiLang)}
          </Button>
          {mutation.data ? (
            <Text size="sm" c="dimmed">
              {mutation.data.cached ? t('qt.from_cache', uiLang) : null}
              {t('qt.chars_left', uiLang, { n: mutation.data.chars_remaining.toLocaleString() })}
            </Text>
          ) : null}
        </Group>

        {mutation.isError ? (
          <Text size="sm" c="red">
            {mutation.error instanceof Error ? mutation.error.message : t('qt.failed', uiLang)}
          </Text>
        ) : null}

        {result ? (
          <Stack gap={8}>
            <Group justify="space-between" align="center">
              <Text size="sm" fw={600}>
                {t('qt.result', uiLang)}
              </Text>
              <CopyButton value={result}>
                {({ copied, copy }) => (
                  <Button
                    size="compact-sm"
                    variant="light"
                    color={copied ? 'teal' : 'gray'}
                    onClick={copy}
                  >
                    {copied ? t('qt.copied', uiLang) : t('qt.copy', uiLang)}
                  </Button>
                )}
              </CopyButton>
            </Group>
            <Text size="sm">{result}</Text>
            {mutation.data ? (
              <Text size="xs" c="dimmed">
                {t('qt.provider', uiLang, { provider: mutation.data.provider, lang: mutation.data.source_lang_detected })}
              </Text>
            ) : null}
          </Stack>
        ) : null}
      </Stack>
    </Card>
  );
}
