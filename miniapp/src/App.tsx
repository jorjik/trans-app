import {
  AppShell,
  Avatar,
  Center,
  Group,
  Loader,
  NavLink,
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
      } catch (bootstrapError) {
        setError(bootstrapError instanceof Error ? bootstrapError.message : 'Failed to initialize app.');
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

  const saveSettingsMutation = useMutation({
    mutationFn: (payload: Parameters<typeof updateMe>[1]) => updateMe(token as string, payload),
    onSuccess: (nextUser) => {
      setUser(nextUser);
      void queryClient.invalidateQueries({ queryKey: ['me', token] });
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to save settings.');
    },
  });

  const createChatMutation = useMutation({
    mutationFn: (payload: { chat_username: string; source_lang: string; target_lang: string }) =>
      createChat(token as string, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['chats', token] });
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to create chat.');
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
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to update chat.');
    },
  });

  const deleteChatMutation = useMutation({
    mutationFn: (chatId: number) => deleteChat(token as string, chatId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['chats', token] });
    },
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to delete chat.');
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
            setError('Payment failed. Please try again.');
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
      setError(mutationError instanceof Error ? mutationError.message : 'Failed to create checkout.');
    },
  });

  const navItems = useMemo(
    () => [
      { key: 'dashboard', label: 'Dashboard', icon: IconDashboard },
      { key: 'chats', label: 'Chats', icon: IconMessages },
      { key: 'billing', label: 'Billing', icon: IconCreditCard },
      { key: 'settings', label: 'Settings', icon: IconSettings },
    ] as const,
    [],
  );

  if (!isReady) {
    return (
      <Center mih="100vh">
        <Stack align="center" gap="sm">
          <Loader />
          <Text size="sm" c="dimmed">
            Initializing TransApp...
          </Text>
        </Stack>
      </Center>
    );
  }

  if (!token || !user) {
    return (
      <Center mih="100vh" px="md">
        <Stack align="center" gap="sm" maw={420}>
          <Title order={3}>TransApp Mini App</Title>
          <Text ta="center" c="dimmed">
            {error ?? 'Authorization failed.'}
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
            onCreate={async (payload) => {
              await createChatMutation.mutateAsync(payload);
            }}
            onToggle={async (chat) => {
              await toggleChatMutation.mutateAsync(chat);
            }}
            onDelete={(chatId) => deleteChatMutation.mutateAsync(chatId)}
            isBusy={
              createChatMutation.isPending ||
              toggleChatMutation.isPending ||
              deleteChatMutation.isPending
            }
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
    <AppShell padding="md" navbar={{ width: 280, breakpoint: 'sm' }}>
      <AppShell.Navbar p="sm">
        <Stack justify="space-between" h="100%">
          <Stack gap="sm">
            <Group>
              <Avatar radius="xl">T</Avatar>
              <div>
                <Text fw={600}>TransApp</Text>
                <Text size="xs" c="dimmed">
                  @{user.username ?? 'telegram_user'}
                </Text>
              </div>
            </Group>

            {navItems.map((item) => (
              <NavLink
                key={item.key}
                active={activeTab === item.key}
                label={item.label}
                leftSection={<item.icon size={18} />}
                onClick={() => setActiveTab(item.key)}
              />
            ))}
          </Stack>

          <Text size="xs" c="dimmed">
            Plan: {user.plan} · Remaining: {user.chars_remaining.toLocaleString()}
          </Text>
        </Stack>
      </AppShell.Navbar>
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
    </AppShell>
  );
}
