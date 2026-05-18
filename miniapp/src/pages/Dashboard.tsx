import { Card, Grid, SimpleGrid, Stack, Text, Title } from '@mantine/core';

import { getLangLabel } from '../api/langs';
import { QuotaBar } from '../components/QuotaBar';
import { QuickTranslate } from '../components/QuickTranslate';
import { StatsChart } from '../components/StatsChart';
import type { StatsResponse, User } from '../types';

interface DashboardProps {
  user: User;
  stats?: StatsResponse;
}

export function Dashboard({ user, stats }: DashboardProps) {
  return (
    <Stack gap="md">
      <div>
        <Title order={2}>Dashboard</Title>
        <Text c="dimmed" size="sm">
          Overview of your translation quota and activity.
        </Text>
      </div>

      <Card withBorder radius="md" p="md">
        <QuotaBar used={user.chars_used} limit={user.chars_limit} />
      </Card>

      <QuickTranslate />

      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <Card withBorder radius="md" p="md">
          <Text size="sm" c="dimmed">
            Plan
          </Text>
          <Title order={4} tt="capitalize">
            {user.plan}
          </Title>
        </Card>
        <Card withBorder radius="md" p="md">
          <Text size="sm" c="dimmed">
            Remaining
          </Text>
          <Title order={4}>{user.chars_remaining.toLocaleString()}</Title>
        </Card>
        <Card withBorder radius="md" p="md">
          <Text size="sm" c="dimmed">
            Default language
          </Text>
          <Title order={4}>{getLangLabel(user.target_language)}</Title>
        </Card>
      </SimpleGrid>

      {stats ? (
        <Grid>
          <Grid.Col span={{ base: 12, md: 8 }}>
            <StatsChart data={stats.chars_by_day} />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Card withBorder radius="md" p="md">
              <Text fw={600} mb="sm">
                Totals
              </Text>
              <Stack gap={8}>
                <Text size="sm">Requests: {stats.total_requests.toLocaleString()}</Text>
                <Text size="sm">Chars: {stats.total_chars.toLocaleString()}</Text>
              </Stack>
            </Card>
          </Grid.Col>
        </Grid>
      ) : null}
    </Stack>
  );
}
