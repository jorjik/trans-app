import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Collapse,
  Group,
  Modal,
  Select,
  Stack,
  Switch,
  Table,
  Text,
  TextInput,
  Title,
  Tooltip,
} from '@mantine/core';
import { useDisclosure, useMediaQuery } from '@mantine/hooks';
import {
  IconEdit,
  IconMessagePlus,
  IconSearch,
  IconSearchOff,
  IconTrash,
} from '@tabler/icons-react';
import { useMemo, useState } from 'react';

import { LANG_FLAGS, LANGUAGE_OPTIONS, getLangLabel } from '../api/langs';
import { t } from '../i18n';
import type { ChatConfig } from '../types';

interface ChatsProps {
  chats: ChatConfig[];
  limitReached: boolean;
  maxChats: number;
  onCreate: (payload: { chat_username: string; source_lang: string; target_lang: string }) => Promise<void>;
  onToggle: (chat: ChatConfig) => Promise<void>;
  onUpdate: (chat: ChatConfig, payload: { source_lang: string; target_lang: string }) => Promise<void>;
  onDelete: (chatId: number) => Promise<void>;
  isBusy: boolean;
  uiLang?: string;
}

export function Chats({ chats, limitReached, maxChats, onCreate, onToggle, onUpdate, onDelete, isBusy, uiLang = 'en' }: ChatsProps) {
  const [chatUsername, setChatUsername] = useState('');
  const [sourceLang, setSourceLang] = useState('auto');
  const [targetLang, setTargetLang] = useState('en');
  const [searchQuery, setSearchQuery] = useState('');

  // Edit modal state
  const [editOpened, { open: openEdit, close: closeEdit }] = useDisclosure(false);
  const [editingChat, setEditingChat] = useState<ChatConfig | null>(null);
  const [editSource, setEditSource] = useState('auto');
  const [editTarget, setEditTarget] = useState('en');

  // Form expand
  const [formOpened, { toggle: toggleForm }] = useDisclosure(true);

  const isMobile = useMediaQuery('(max-width: 640px)');

  // Filter chats by search query
  const filteredChats = useMemo(() => {
    if (!searchQuery.trim()) return chats;
    const q = searchQuery.toLowerCase();
    return chats.filter((chat) => {
      const title = (chat.chat_title ?? '').toLowerCase();
      const username = (chat.chat_username ?? '').toLowerCase();
      return title.includes(q) || username.includes(q);
    });
  }, [chats, searchQuery]);

  const activeCount = chats.filter((c) => c.is_active).length;

  // Open edit modal
  const handleOpenEdit = (chat: ChatConfig) => {
    setEditingChat(chat);
    setEditSource(chat.source_lang);
    setEditTarget(chat.target_lang);
    openEdit();
  };

  // Save edit
  const handleSaveEdit = async () => {
    if (!editingChat) return;
    await onUpdate(editingChat, { source_lang: editSource, target_lang: editTarget });
    closeEdit();
    setEditingChat(null);
  };

  return (
    <Stack gap="md">
      {/* Header */}
      <div>
        <Group justify="space-between" align="flex-end">
          <div>
            <Title order={2}>{t('chats.title', uiLang)}</Title>
            <Text c="dimmed" size="sm">
              {t('chats.desc', uiLang)}
            </Text>
          </div>
          {chats.length > 0 && (
            <Badge
              variant="light"
              color="blue"
              size="lg"
              styles={{ root: { flexShrink: 0 } }}
            >
              {t('chats.stats', uiLang, { active: activeCount, total: chats.length })}
            </Badge>
          )}
        </Group>
      </div>

      {/* Add chat form (collapsible) */}
      <Card
        withBorder
        radius="md"
        p="md"
        style={{
          borderColor: limitReached ? 'var(--mantine-color-red-3)' : undefined,
          transition: 'border-color 0.2s ease',
        }}
      >
        <Stack gap="sm">
          <Group justify="space-between" onClick={toggleForm} style={{ cursor: 'pointer' }}>
            <Text fw={600} size="sm">
              {t('chats.add_new', uiLang)}
            </Text>
            <IconMessagePlus size={18} style={{ opacity: 0.5 }} />
          </Group>

          <Collapse in={formOpened}>
            <Stack gap="sm" pt="xs">
              <TextInput
                label={t('chats.username_label', uiLang)}
                placeholder={t('chats.username_placeholder', uiLang)}
                value={chatUsername}
                onChange={(event) => setChatUsername(event.currentTarget.value)}
                leftSection={<Text size="xs" c="dimmed">@</Text>}
              />
              <Group grow>
                <Select
                  label={t('chats.source', uiLang)}
                  data={LANGUAGE_OPTIONS}
                  value={sourceLang}
                  onChange={(value) => value && setSourceLang(value)}
                  searchable
                />
                <Select
                  label={t('chats.target', uiLang)}
                  data={LANGUAGE_OPTIONS.filter((item) => item.value !== 'auto')}
                  value={targetLang}
                  onChange={(value) => value && setTargetLang(value)}
                  searchable
                />
              </Group>
              <Group justify="space-between">
                <Text size="sm" c={limitReached ? 'red' : 'dimmed'}>
                  {limitReached
                    ? t('chats.limit_reached', uiLang)
                    : t('chats.can_add', uiLang, { max: maxChats, current: chats.length })
                  }
                </Text>
                <Button
                  disabled={limitReached || !chatUsername.trim()}
                  loading={isBusy}
                  onClick={async () => {
                    await onCreate({
                      chat_username: chatUsername.trim(),
                      source_lang: sourceLang,
                      target_lang: targetLang,
                    });
                    setChatUsername('');
                  }}
                >
                  {t('chats.add_btn', uiLang)}
                </Button>
              </Group>
            </Stack>
          </Collapse>
        </Stack>
      </Card>

      {/* Search bar */}
      {chats.length > 0 && (
        <TextInput
          placeholder={t('chats.search_placeholder', uiLang)}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.currentTarget.value)}
          leftSection={<IconSearch size={16} />}
          rightSection={
            searchQuery ? (
              <ActionIcon variant="subtle" size="sm" onClick={() => setSearchQuery('')}>
                <IconSearchOff size={14} />
              </ActionIcon>
            ) : null
          }
        />
      )}

      {/* Chat list */}
      {filteredChats.length === 0 ? (
        <Card withBorder radius="md" p="xl">
          <Stack align="center" gap="sm" py="lg">
            <Text fz={48} style={{ opacity: 0.3 }}>
              {searchQuery ? '🔍' : '💬'}
            </Text>
            <Text size="sm" c="dimmed" ta="center">
              {searchQuery
                ? t('chats.search_empty', uiLang, { query: searchQuery })
                : t('chats.empty', uiLang)
              }
            </Text>
            {!searchQuery && (
              <Button
                variant="light"
                size="xs"
                onClick={toggleForm}
                leftSection={<IconMessagePlus size={14} />}
              >
                {t('chats.add_first', uiLang)}
              </Button>
            )}
          </Stack>
        </Card>
      ) : isMobile ? (
        /* Mobile: card layout */
        <Stack gap="sm">
          {filteredChats.map((chat) => (
            <Card
              key={chat.id}
              withBorder
              radius="md"
              p="sm"
              className="chat-card"
              style={{
                opacity: chat.is_active ? 1 : 0.6,
                transition: 'opacity 0.2s ease, box-shadow 0.2s ease',
              }}
            >
              <Group justify="space-between" mb={4}>
                <Group gap="xs">
                  <Text fw={500} size="sm">
                    {chat.chat_title ?? `@${chat.chat_username ?? 'unknown'}`}
                  </Text>
                  <Badge
                    size="xs"
                    color={chat.is_active ? 'green' : 'gray'}
                    variant="dot"
                  >
                    {chat.is_active ? t('chats.status_on', uiLang) : t('chats.status_off', uiLang)}
                  </Badge>
                </Group>
                <Group gap={4}>
                  <ActionIcon variant="subtle" color="blue" size="sm" onClick={() => handleOpenEdit(chat)}>
                    <IconEdit size={14} />
                  </ActionIcon>
                  <ActionIcon variant="subtle" color="red" size="sm" onClick={() => onDelete(chat.id)}>
                    <IconTrash size={14} />
                  </ActionIcon>
                </Group>
              </Group>
              <Group gap={4} mb={6}>
                <Text size="xs" span c="dimmed">
                  {getLangLabel(chat.source_lang, uiLang)}
                </Text>
                <Text size="xs" span c="dimmed">→</Text>
                <Text size="xs" span c="dimmed">
                  {getLangLabel(chat.target_lang, uiLang)}
                </Text>
              </Group>
              <Switch
                size="xs"
                checked={chat.is_active}
                onChange={() => onToggle(chat)}
                label={chat.is_active ? t('chats.active', uiLang) : t('chats.inactive', uiLang)}
                styles={{ label: { fontSize: '11px', color: 'var(--mantine-color-dimmed)' } }}
              />
            </Card>
          ))}
        </Stack>
      ) : (
        /* Desktop: table layout */
        <Card withBorder radius="md" p="md">
          <Table.ScrollContainer minWidth={500}>
            <Table highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>{t('chats.table_chat', uiLang)}</Table.Th>
                  <Table.Th>{t('chats.table_langs', uiLang)}</Table.Th>
                  <Table.Th>{t('chats.table_status', uiLang)}</Table.Th>
                  <Table.Th w={100} />
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {filteredChats.map((chat) => (
                  <Table.Tr
                    className="chat-row"
                    style={{
                      opacity: chat.is_active ? 1 : 0.55,
                      transition: 'opacity 0.2s ease, background-color 0.15s ease',
                    }}
                  >
                        <Table.Td>
                          <Group gap="xs">
                            <Text size="sm" fw={500}>
                              {chat.chat_title ?? `@${chat.chat_username ?? 'unknown'}`}
                            </Text>
                            {chat.chat_username && chat.chat_title && (
                              <Text size="xs" c="dimmed" span>
                                @{chat.chat_username}
                              </Text>
                            )}
                          </Group>
                        </Table.Td>
                        <Table.Td>
                          <Group gap={4}>
                            <Badge
                              size="sm"
                              variant="light"
                              color="grape"
                              styles={{ label: { textTransform: 'none' } }}
                            >
                              {LANG_FLAGS[chat.source_lang] ?? '🌐'} {chat.source_lang.toUpperCase()}
                            </Badge>
                            <Text size="xs" c="dimmed">→</Text>
                            <Badge
                              size="sm"
                              variant="light"
                              color="blue"
                              styles={{ label: { textTransform: 'none' } }}
                            >
                              {LANG_FLAGS[chat.target_lang] ?? '🌐'} {chat.target_lang.toUpperCase()}
                            </Badge>
                          </Group>
                        </Table.Td>
                        <Table.Td>
                          <Group gap="xs">
                            <Switch
                              checked={chat.is_active}
                              onChange={() => onToggle(chat)}
                              size="xs"
                            />
                            <Badge
                              size="sm"
                              color={chat.is_active ? 'green' : 'gray'}
                              variant="dot"
                            >
                              {chat.is_active ? t('chats.status_on', uiLang) : t('chats.status_off', uiLang)}
                            </Badge>
                          </Group>
                        </Table.Td>
                        <Table.Td>
                          <Group gap={4} justify="flex-end">
                            <Tooltip label={t('chats.edit_tooltip', uiLang)}>
                              <ActionIcon variant="subtle" color="blue" size="sm" onClick={() => handleOpenEdit(chat)}>
                                <IconEdit size={15} />
                              </ActionIcon>
                            </Tooltip>
                            <Tooltip label={t('chats.delete_tooltip', uiLang)}>
                              <ActionIcon variant="subtle" color="red" size="sm" onClick={() => onDelete(chat.id)}>
                                <IconTrash size={15} />
                              </ActionIcon>
                            </Tooltip>
                          </Group>
                        </Table.Td>
                      </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        </Card>
      )}

      {/* Edit Modal */}
      <Modal
        opened={editOpened}
        onClose={closeEdit}
        title={t('chats.edit_title', uiLang)}
        size="sm"
        centered
      >
        {editingChat && (
          <Stack gap="md">
            <div>
              <Text size="sm" fw={500} mb={2}>
                {editingChat.chat_title ?? `@${editingChat.chat_username ?? ''}`}
              </Text>
              <Text size="xs" c="dimmed">
                {t('chats.edit_desc', uiLang)}
              </Text>
            </div>
            <Select
              label={t('chats.source', uiLang)}
              data={LANGUAGE_OPTIONS}
              value={editSource}
              onChange={(value) => value && setEditSource(value)}
              searchable
            />
            <Select
              label={t('chats.target', uiLang)}
              data={LANGUAGE_OPTIONS.filter((item) => item.value !== 'auto')}
              value={editTarget}
              onChange={(value) => value && setEditTarget(value)}
              searchable
            />
            <Group justify="flex-end" mt="sm">
              <Button variant="default" onClick={closeEdit}>
                {t('chats.edit_cancel', uiLang)}
              </Button>
              <Button onClick={handleSaveEdit} loading={isBusy}>
                {t('chats.edit_save', uiLang)}
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>
    </Stack>
  );
}
