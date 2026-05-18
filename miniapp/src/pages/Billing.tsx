import { Button, Card, Group, SimpleGrid, Stack, Text, Title } from '@mantine/core';

import type { BillingPlan } from '../types';

interface BillingProps {
  plans: BillingPlan[];
  currentPlan: string;
  onCheckout: (planId: string) => Promise<void>;
  isLoading: boolean;
}

export function Billing({ plans, currentPlan, onCheckout, isLoading }: BillingProps) {
  return (
    <Stack gap="md">
      <div>
        <Title order={2}>Billing</Title>
        <Text c="dimmed" size="sm">
          Upgrade your monthly quota with Telegram Stars.
        </Text>
      </div>

      <SimpleGrid cols={{ base: 1, md: 3 }}>
        {plans.map((plan) => {
          const isCurrent = currentPlan === plan.id;

          return (
            <Card key={plan.id} withBorder radius="md" p="md">
              <Stack gap="sm">
                <div>
                  <Title order={3}>{plan.name}</Title>
                  <Text c="dimmed" size="sm">
                    {plan.chars_per_month.toLocaleString()} chars / month
                  </Text>
                </div>

                <Text fw={700}>{plan.price_stars} Stars</Text>

                <Stack gap={4}>
                  {plan.features.map((feature) => (
                    <Text key={feature} size="sm">
                      • {feature}
                    </Text>
                  ))}
                </Stack>

                <Group justify="flex-end" mt="sm">
                  <Button
                    variant={isCurrent ? 'default' : 'filled'}
                    disabled={isCurrent}
                    loading={isLoading}
                    onClick={() => onCheckout(plan.id)}
                  >
                    {isCurrent ? 'Current plan' : 'Pay with Stars'}
                  </Button>
                </Group>
              </Stack>
            </Card>
          );
        })}
      </SimpleGrid>
    </Stack>
  );
}
