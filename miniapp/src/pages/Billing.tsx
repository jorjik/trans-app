import { Badge, Button, Card, Group, SimpleGrid, Stack, Text, Title } from '@mantine/core';

import { t } from '../i18n';
import type { BillingPlan } from '../types';

interface BillingProps {
  plans: BillingPlan[];
  currentPlan: string;
  onCheckout: (planId: string) => Promise<void>;
  /** Optional: id of the plan whose checkout is in flight. */
  payingPlanId?: string | null;
  /** Current quota limit of the user, used to compute the recommended upgrade. */
  charsLimit?: number;
  isLoading?: boolean;
  uiLang?: string;
}

export function Billing({ plans, currentPlan, onCheckout, payingPlanId, charsLimit = 0, isLoading, uiLang = 'en' }: BillingProps) {
  const recommendedPlanId = plans.find(
    (plan) => plan.chars_per_month > Math.max(0, charsLimit) && plan.price_stars > 0,
  )?.id;

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
          const isRecommended = plan.id === recommendedPlanId && !isCurrent;
          const planIsLoading = isLoading && payingPlanId === plan.id;
          const anyPlanLoading = isLoading && payingPlanId !== null;

          return (
            <Card
              key={plan.id}
              withBorder
              radius="md"
              p="md"
              className="plan-card"
              style={{
                borderColor: isRecommended ? 'var(--mantine-color-blue-4)' : undefined,
                opacity: anyPlanLoading && !planIsLoading && !isCurrent ? 0.55 : undefined,
                transition: 'opacity 0.2s ease, border-color 0.2s ease',
              }}
            >
              <Stack gap="sm">
                <div>
                  <Group justify="space-between" gap="xs" align="center" wrap="nowrap">
                    <Title order={3}>{plan.name}</Title>
                    {isRecommended && (
                      <Badge color="blue" variant="light" size="sm" styles={{ root: { flexShrink: 0 } }}>
                        {t('billing.recommended', uiLang)}
                      </Badge>
                    )}
                  </Group>
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
                    variant={isRecommended ? 'filled' : 'default'}
                    disabled={isCurrent || (anyPlanLoading && !planIsLoading)}
                    loading={planIsLoading}
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
