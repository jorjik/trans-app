import { Card, Text } from '@mantine/core';
import { AreaChart } from '@mantine/charts';

import type { StatsPoint } from '../types';

interface StatsChartProps {
  data: StatsPoint[];
}

export function StatsChart({ data }: StatsChartProps) {
  return (
    <Card withBorder radius="md" p="md">
      <Text fw={600} mb="sm">
        Character usage
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
