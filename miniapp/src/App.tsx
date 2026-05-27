import {
  AppShell,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Notification,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import {
  IconCreditCard,
  IconDashboard,
  IconMessages,
  IconSettings,
} from '@tabler/icons-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';

import {
  authWithTelegram,
  createChat,
  createCheckout,
  deleteChat,
  getChats,
  getMe,
  getPlans,
  getStats,
  updateChat,
  updateMe,
} from './api/client';
import { BottomNav } from './components/BottomNav';
import { t } from './i18n';
import { Billing } from './pages/Billing';
import { Chats } from './pages/Chats';
import { Dashboard } from './pages/Dashboard';
import { Settings } from './pages/Settings';
import { useStore } from './store/useStore';
import type { ChatConfig } from './types';

export default function App() {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const token = useStore((state) => state.token);
  const user = useStore((state) => state.user);
  const isReady = useStore((state) => state.isReady);
  const activeTab = useStore((state) => state.activeTab);
  const setToken = useStore((state) => state.setToken);
  const setUser = useStore((state) => state.setUser);
  const setReady = useStore((state) => state.setReady);
  const setActiveTab = useStore((state) => state.setActiveTab);

  const [isNewUser, setIsNewUser] = useState(false);
  const [pickerLang, setPickerLang] = useState(() => {
    const tgLang = window.Telegram?.WebApp?.initDataUnsafe?.user?.language_code?.slice(0, 2);
    return tgLang && ['en', 'ru', 'uk'].includes(tgLang) ? tgLang : 'en';
  });

  const uiLang = user?.ui_language ?? 'en';

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const webApp = window.Telegram?.WebApp;
        const initData = webApp?.initData || import.meta.env.VITE_DEV_TOKEN;

        if (!initData) {
          throw new Error('Telegram initData is missing. Open this app from Telegram or set VITE_DEV_TOKEN.');
        }

        webApp?.ready();
        webApp?.expand();

        const auth = await authWithTelegram(initData);
        setToken(auth.access_token);
        setUser(auth.user);
        setIsNewUser(auth.is_new);
      } catch (bootstrapError) {
        setError(bootstrapError instanceof Error ? bootstrapError.message : t('app.init_error', uiLang));
      } finally {
        setReady(true);
      }
    };

    void bootstrap();
  }, [setReady, setToken, setUser]);

  const meQuery = useQuery({
    queryKey: ['me', token],
    queryFn: () => getMe(token as string),
    enabled: Boolean(token),
  });

  const statsQuery = useQuery({
    queryKey: ['stats', token],
    queryFn: () => getStats(token as string),
    enabled: Boolean(token),
  });

  const chatsQuery = useQuery({
    queryKey: ['chats', token],
    queryFn: () => getChats(token as string),
    enabled: Boolean(token),
  });

  const plansQuery = useQuery({
    queryKey: ['plans', token],
    queryFn: () => getPlans(token as string),
    enabled: Boolean(token),
  });

  useEffect(() => {
    if (meQuery.data) {
      setUser(meQuery.data);
    }
  }, [meQuery.data, setUser]);

  useEffect(() => {
    if (user?.ui_language && ['en', 'ru', 'uk'].includes(user.ui_language)) {
      setPickerLang(user.ui_language);
    }
  }, [user?.ui_language]);

  const saveSettingsMutation = useMutation({
    mutationFn: (payload: Parameters<typeof updateMe>[1]) => updateMe(token as string, payload),
    onSuccess: (nextUser) => {
      setUser(nextUser);
      void queryClient.invalidateQueries({ queryKey: ['me', token] });
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : t('app.save_error', uiLang));
    },
  });

  const createChatMutation = useMutation({
    mutationFn: (payload: { chat_username: string; source_lang: string; target_lang: string }) =>
      createChat(token as string, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['chats', token] });
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : t('app.chat_create_error', uiLang));
    },
  });

  const toggleChatMutation = useMutation({
    mutationFn: (chat: ChatConfig) =>
      updateChat(token as string, chat.id, {
        is_active: !chat.is_active,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['chats', token] });
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : t('app.chat_update_error', uiLang));
    },
  });

  const updateChatMutation = useMutation({
    mutationFn: (payload: { id: number; source_lang: string; target_lang: string }) =>
      updateChat(token as string, payload.id, {
        source_lang: payload.source_lang,
        target_lang: payload.target_lang,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['chats', token] });
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : t('app.chat_update_error', uiLang));
    },
  });

  const deleteChatMutation = useMutation({
    mutationFn: (chatId: number) => deleteChat(token as string, chatId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['chats', token] });
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : t('app.chat_update_error', uiLang));
    },
  });

  const checkoutMutation = useMutation({
    mutationFn: (planId: string) => createCheckout(token as string, planId),
    onSuccess: (data) => {
      const tg = window.Telegram?.WebApp;
      const url = data.invoice_url;

      const refreshBilling = () => {
        void queryClient.invalidateQueries({ queryKey: ['plans', token] });
        void queryClient.invalidateQueries({ queryKey: ['me', token] });
      };

      if (tg?.openInvoice) {
        tg.openInvoice(url, (status) => {
          if (status === 'paid') {
            refreshBilling();
            setError(null);
          } else if (status === 'failed') {
            setError(t('app.payment_failed', uiLang));
          }
        });
        return;
      }

      if (url.startsWith('https://t.me/') || url.startsWith('tg://')) {
        tg?.openTelegramLink(url);
      } else {
        tg?.openLink(url);
      }
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : t('app.checkout_error', uiLang));
    },
  });

  const navItems = useMemo(
    () => [
      { key: 'dashboard', label: t('nav.dashboard', uiLang), icon: IconDashboard },
      { key: 'chats', label: t('nav.chats', uiLang), icon: IconMessages },
      { key: 'billing', label: t('nav.billing', uiLang), icon: IconCreditCard },
      { key: 'settings', label: t('nav.settings', uiLang), icon: IconSettings },
    ] as const,
    [uiLang],
  );

  const handleNavClick = (key: 'dashboard' | 'chats' | 'billing' | 'settings') => {
    setActiveTab(key);
  };

  const handleLangConfirm = async () => {
    if (!token) return;
    try {
      const updated = await updateMe(token, { ui_language: pickerLang });
      setUser(updated);
    } catch {
      // fallback: keep the default user, they can change in Settings
    }
    setIsNewUser(false);
  };

  if (isNewUser && user) {
    return (
      <Center mih="100vh" px="md">
        <Card withBorder radius="lg" p="xl" maw={400} w="100%">
          <Stack align="center" gap="lg">
            <Text fz={32}>🌐</Text>
            <Stack align="center" gap="xs">
              <Title order={3}>{t('langpicker.title', pickerLang)}</Title>
              <Text ta="center" c="dimmed" size="sm">
                {t('langpicker.desc', pickerLang)}
              </Text>
            </Stack>
            <Stack w="100%" gap="xs">
              {[
                { value: 'en', label: t('langpicker.en', pickerLang), flag: '🇬🇧' },
                { value: 'ru', label: t('langpicker.ru', pickerLang), flag: '🇷🇺' },
                { value: 'uk', label: t('langpicker.uk', pickerLang), flag: '🇺🇦' },
              ].map(({ value, label, flag }) => (
                <Card
                  key={value}
                  withBorder
                  radius="md"
                  p="sm"
                  style={{
                    cursor: 'pointer',
                    borderColor: pickerLang === value ? 'var(--mantine-color-blue-6)' : undefined,
                    backgroundColor: pickerLang === value ? 'var(--mantine-color-blue-0)' : undefined,
                  }}
                  onClick={() => setPickerLang(value)}
                >
                  <Group gap="sm">
                    <Text fz={24}>{flag}</Text>
                    <Text fw={pickerLang === value ? 600 : 400}>{label}</Text>
                  </Group>
                </Card>
              ))}
            </Stack>
            <Button fullWidth size="md" onClick={handleLangConfirm}>
              {t('langpicker.continue', pickerLang)}
            </Button>
          </Stack>
        </Card>
      </Center>
    );
  }

  if (!isReady) {
    return (
      <Center mih="100vh">
        <Stack align="center" gap="sm">
          <Loader />
          <Text size="sm" c="gray.4">
            {t('app.loading', uiLang)}
          </Text>
        </Stack>
      </Center>
    );
  }

  if (!token || !user) {
    return (
      <Center mih="100vh" px="md">
        <Stack align="center" gap="sm" maw={420}>
          <Title order={3}>{t('app.error.title', uiLang)}</Title>
          <Text ta="center" c="dimmed">
            {error ?? t('app.auth_failed', uiLang)}
          </Text>
        </Stack>
      </Center>
    );
  }

  const content = (() => {
    switch (activeTab) {
      case 'chats':
        return (
          <Chats
            chats={chatsQuery.data?.items ?? []}
            limitReached={chatsQuery.data?.limit_reached ?? false}
            maxChats={chatsQuery.data?.max_chats ?? 5}
            onCreate={async (payload) => {
              await createChatMutation.mutateAsync(payload);
            }}
            onToggle={async (chat) => {
              await toggleChatMutation.mutateAsync(chat);
            }}
            onUpdate={async (chat, payload) => {
              await updateChatMutation.mutateAsync({
                id: chat.id,
                source_lang: payload.source_lang,
                target_lang: payload.target_lang,
              });
            }}
            onDelete={(chatId) => deleteChatMutation.mutateAsync(chatId)}
            isBusy={
              createChatMutation.isPending ||
              toggleChatMutation.isPending ||
              deleteChatMutation.isPending ||
              updateChatMutation.isPending
            }
            uiLang={user.ui_language}
          />
        );
      case 'billing':
        return (
          <Billing
            plans={plansQuery.data?.plans ?? []}
            currentPlan={user.plan}
            onCheckout={async (planId) => {
              await checkoutMutation.mutateAsync(planId);
            }}
            isLoading={checkoutMutation.isPending}
            uiLang={user.ui_language}
          />
        );
      case 'settings':
        return (
          <Settings
            user={user}
            onSave={async (payload) => {
              await saveSettingsMutation.mutateAsync(payload);
            }}
            isSaving={saveSettingsMutation.isPending}
          />
        );
      case 'dashboard':
      default:
        return <Dashboard user={user} stats={statsQuery.data} />;
    }
  })();

  return (
    <AppShell
      padding="md"
      header={{ height: 52 }}
      footer={{ height: 60 }}
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Text fw={600}>TransApp</Text>
          <Text size="xs" c="dimmed">
            {t('nav.plan_remaining', user.ui_language, {
              plan: user.plan,
              chars: user.chars_remaining.toLocaleString(),
            })}
          </Text>
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <Stack gap="md">
          {error ? (
            <Notification color="red" onClose={() => setError(null)}>
              {error}
            </Notification>
          ) : null}
          {content}
        </Stack>
      </AppShell.Main>
      <AppShell.Footer>
        <BottomNav items={navItems} active={activeTab} onTabClick={handleNavClick} />
      </AppShell.Footer>
    </AppShell>
  );
}
