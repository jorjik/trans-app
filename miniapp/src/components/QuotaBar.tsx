import { Badge, Group, Progress, Stack, Text } from '@mantine/core';

import { t } from '../i18n';

interface QuotaBarProps {
  used: number;
  limit: number;
  uiLang?: string;
}

export function QuotaBar({ used, limit, uiLang = 'en' }: QuotaBarProps) {
  const percent = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const remaining = Math.max(0, limit - used);
  const color = percent >= 90 ? 'red' : percent >= 60 ? 'yellow' : 'grape';

  return (
    <Stack gap={6}>
      <Group justify="space-between" align="center" gap="sm" wrap="nowrap">
        <Text size="sm" fw={500}>
          {t('quota.title', uiLang)}
        </Text>
        <Badge
          color={color}
          variant="light"
          size="sm"
          styles={{ label: { minWidth: 44, textAlign: 'center' } }}
        >
          {percent}%
        </Badge>
      </Group>
      <Progress value={percent} radius="xl" size="lg" color={color} />
      <Text size="xs" c="dimmed">
        {t('quota.used', uiLang, { used: used.toLocaleString(), limit: limit.toLocaleString() })}
        {' · '}
        {t('quota.remaining', uiLang, { n: remaining.toLocaleString() })}
      </Text>
    </Stack>
  );
}
