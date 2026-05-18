import { Button, Card, Group, Select, Stack, Text, Textarea, Title } from '@mantine/core';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { translateText } from '../api/client';
import { LANGUAGE_OPTIONS } from '../api/langs';
import { useStore } from '../store/useStore';
import type { TranslationEngine } from '../types';

export function QuickTranslate() {
  const queryClient = useQueryClient();
  const token = useStore((state) => state.token);

  const [text, setText] = useState('');
  const [sourceLang, setSourceLang] = useState('auto');
  const [targetLang, setTargetLang] = useState('en');
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
          <Title order={4}>Quick translate</Title>
          <Text size="sm" c="dimmed">
            Calls the same API as the bot. Cached hits do not spend quota.
          </Text>
        </div>

        <Textarea
          label="Text"
          placeholder="Type something to translate..."
          minRows={3}
          value={text}
          onChange={(e) => setText(e.currentTarget.value)}
        />

        <Group grow>
          <Select
            label="Source"
            data={LANGUAGE_OPTIONS}
            value={sourceLang}
            onChange={(value) => value && setSourceLang(value)}
          />
          <Select
            label="Target"
            data={LANGUAGE_OPTIONS.filter((item) => item.value !== 'auto')}
            value={targetLang}
            onChange={(value) => value && setTargetLang(value)}
          />
        </Group>

        <Select
          label="Engine"
          data={[
            { value: 'auto', label: 'Auto' },
            { value: 'google_free', label: 'Google Free' },
            { value: 'deepl', label: 'DeepL' },
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
            Translate
          </Button>
          {mutation.data ? (
            <Text size="sm" c="dimmed">
              {mutation.data.cached ? 'From cache · ' : null}
              {mutation.data.chars_remaining.toLocaleString()} chars left
            </Text>
          ) : null}
        </Group>

        {mutation.isError ? (
          <Text size="sm" c="red">
            {mutation.error instanceof Error ? mutation.error.message : 'Translation failed.'}
          </Text>
        ) : null}

        {result ? (
          <Stack gap={4}>
            <Text size="sm" fw={600}>
              Result
            </Text>
            <Text size="sm">{result}</Text>
            {mutation.data ? (
              <Text size="xs" c="dimmed">
                {mutation.data.provider} · detected {mutation.data.source_lang_detected}
              </Text>
            ) : null}
          </Stack>
        ) : null}
      </Stack>
    </Card>
  );
}
