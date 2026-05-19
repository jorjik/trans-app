import { Progress, Stack, Text } from '@mantine/core';

import { t } from '../i18n';

interface QuotaBarProps {
  used: number;
  limit: number;
  uiLang?: string;
}

export function QuotaBar({ used, limit, uiLang = 'en' }: QuotaBarProps) {
  const percent = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;

  return (
    <Stack gap={6}>
      <Text size="sm" fw={500}>
        {t('quota.title', uiLang)}
      </Text>
      <Progress value={percent} radius="xl" size="lg" />
      <Text size="xs" c="dimmed">
        {t('quota.used', uiLang, { used: used.toLocaleString(), limit: limit.toLocaleString() })}
      </Text>
    </Stack>
  );
}
