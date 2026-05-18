import { Progress, Stack, Text } from '@mantine/core';

interface QuotaBarProps {
  used: number;
  limit: number;
}

export function QuotaBar({ used, limit }: QuotaBarProps) {
  const percent = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;

  return (
    <Stack gap={6}>
      <Text size="sm" fw={500}>
        Monthly quota
      </Text>
      <Progress value={percent} radius="xl" size="lg" />
      <Text size="xs" c="dimmed">
        {used.toLocaleString()} / {limit.toLocaleString()} chars used
      </Text>
    </Stack>
  );
}
