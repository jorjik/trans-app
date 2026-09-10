import { Card, Grid, Skeleton, Stack, Text, Title } from '@mantine/core';

import { getLangLabel } from '../api/langs';
import { QuotaBar } from '../components/QuotaBar';
import { QuickTranslate } from '../components/QuickTranslate';
import { StatsChart } from '../components/StatsChart';
import { t } from '../i18n';
import type { StatsResponse, User } from '../types';

interface DashboardProps {
  user: User;
  stats?: StatsResponse;
  isLoadingStats?: boolean;
}

export function Dashboard({ user, stats, isLoadingStats }: DashboardProps) {
  const lang = user.ui_language ?? 'en';

  return (
    <Stack gap="md">
      <div>
        <Title order={2}>{t('dashboard.title', lang)}</Title>
        <Text c="dimmed" size="sm">
          {t('dashboard.desc', lang)}
        </Text>
      </div>

      <Card withBorder radius="md" p="md">
        <QuotaBar used={user.chars_used} limit={user.chars_limit} uiLang={lang} />
      </Card>

      <QuickTranslate />

      {isLoadingStats ? (
        <Grid>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Card withBorder radius="md" p="md">
              <Skeleton height={12} radius="xl" width="55%" />
              <Skeleton height={24} radius="sm" width="40%" my={10} />
              <Skeleton height={12} radius="xl" width="35%" />
              <Skeleton height={12} radius="xl" width="70%" mt={12} />
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 8 }}>
            <Card withBorder radius="md" p="md">
              <Skeleton height={160} radius="md" />
            </Card>
          </Grid.Col>
        </Grid>
      ) : stats ? (
        <Grid>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Card withBorder radius="md" p="md">
              <Text size="sm" c="dimmed" mb="xs">
                {t('dashboard.default_lang', lang)}
              </Text>
              <Title order={4} mb="md">{getLangLabel(user.target_language, lang)}</Title>
              <Text fw={600} mb="sm">
                {t('dashboard.totals', lang)}
              </Text>
              <Stack gap={8}>
                <Text size="sm">{t('dashboard.requests', lang, { n: stats.total_requests.toLocaleString() })}</Text>
                <Text size="sm">{t('dashboard.chars', lang, { n: stats.total_chars.toLocaleString() })}</Text>
              </Stack>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 8 }}>
            <StatsChart data={stats.chars_by_day} uiLang={lang} />
          </Grid.Col>
        </Grid>
      ) : (
        <Card withBorder radius="md" p="md">
          <Text size="sm" c="dimmed" mb="xs">
            {t('dashboard.default_lang', lang)}
          </Text>
          <Title order={4}>{getLangLabel(user.target_language, lang)}</Title>
        </Card>
      )}
    </Stack>
  );
}