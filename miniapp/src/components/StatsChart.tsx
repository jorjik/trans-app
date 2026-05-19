import { Card, Text } from '@mantine/core';
import { AreaChart } from '@mantine/charts';

import { t } from '../i18n';
import type { StatsPoint } from '../types';

interface StatsChartProps {
  data: StatsPoint[];
  uiLang?: string;
}

export function StatsChart({ data, uiLang = 'en' }: StatsChartProps) {
  return (
    <Card withBorder radius="md" p="md">
      <Text fw={600} mb="sm">
        {t('stats.chars', uiLang)}
      </Text>
      <AreaChart
        h={220}
        data={data}
        dataKey="date"
        series={[{ name: 'chars', color: 'blue.6' }]}
        curveType="natural"
      />
    </Card>
  );
}
