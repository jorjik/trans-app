import { Button, Card, Group, SimpleGrid, Stack, Text, Title } from '@mantine/core';

import { t } from '../i18n';
import type { BillingPlan } from '../types';

interface BillingProps {
  plans: BillingPlan[];
  currentPlan: string;
  onCheckout: (planId: string) => Promise<void>;
  isLoading: boolean;
  uiLang?: string;
}

export function Billing({ plans, currentPlan, onCheckout, isLoading, uiLang = 'en' }: BillingProps) {
  return (
    <Stack gap="md">
      <div>
        <Title order={2}>{t('billing.title', uiLang)}</Title>
        <Text c="dimmed" size="sm">
          {t('billing.desc', uiLang)}
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
                    {t('billing.chars_month', uiLang, { n: plan.chars_per_month.toLocaleString() })}
                  </Text>
                </div>

                <Text fw={700}>{t('billing.stars', uiLang, { n: plan.price_stars })}</Text>

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
                    {isCurrent ? t('billing.current_plan', uiLang) : t('billing.pay_stars', uiLang)}
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
