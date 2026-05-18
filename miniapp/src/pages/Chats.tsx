import { ActionIcon, Button, Card, Group, Select, Stack, Switch, Table, Text, TextInput, Title } from '@mantine/core';
import { IconTrash } from '@tabler/icons-react';
import { useState } from 'react';

import { LANGUAGE_OPTIONS, getLangLabel } from '../api/langs';
import type { ChatConfig } from '../types';

interface ChatsProps {
  chats: ChatConfig[];
  limitReached: boolean;
  onCreate: (payload: { chat_username: string; source_lang: string; target_lang: string }) => Promise<void>;
  onToggle: (chat: ChatConfig) => Promise<void>;
  onDelete: (chatId: number) => Promise<void>;
  isBusy: boolean;
}

export function Chats({ chats, limitReached, onCreate, onToggle, onDelete, isBusy }: ChatsProps) {
  const [chatUsername, setChatUsername] = useState('');
  const [sourceLang, setSourceLang] = useState('auto');
  const [targetLang, setTargetLang] = useState('en');

  return (
    <Stack gap="md">
      <div>
        <Title order={2}>Chats</Title>
        <Text c="dimmed" size="sm">
          Manage auto-translation rules for Telegram chats.
        </Text>
      </div>

      <Card withBorder radius="md" p="md">
        <Stack>
          <TextInput
            label="Chat username"
            placeholder="devs_world"
            value={chatUsername}
            onChange={(event) => setChatUsername(event.currentTarget.value)}
          />
          <Group grow>
            <Select
              label="Source"
              data={LANGUAGE_OPTIONS}
              value={sourceLang}
              onChange={(value) => value && setSourceLang(value)}
            />
            <Select
              label="Target"
              data={LANGUAGE_OPTIONS.filter((item) => item.value !== 'auto')}
              value={targetLang}
              onChange={(value) => value && setTargetLang(value)}
            />
          </Group>
          <Group justify="space-between">
            <Text size="sm" c={limitReached ? 'red' : 'dimmed'}>
              {limitReached ? 'Chat limit reached for your plan.' : 'You can add a new auto-translation chat.'}
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
              Add chat
            </Button>
          </Group>
        </Stack>
      </Card>

      <Card withBorder radius="md" p="md">
        <Table.ScrollContainer minWidth={640}>
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Chat</Table.Th>
                <Table.Th>Languages</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {chats.length === 0 ? (
                <Table.Tr>
                  <Table.Td colSpan={4}>
                    <Text size="sm" c="dimmed">
                      No auto-translate chats yet. Add one above (public username without @).
                    </Text>
                  </Table.Td>
                </Table.Tr>
              ) : (
                chats.map((chat) => (
                  <Table.Tr key={chat.id}>
                    <Table.Td>{chat.chat_title ?? `@${chat.chat_username ?? 'unknown'}`}</Table.Td>
                    <Table.Td>
                      {getLangLabel(chat.source_lang)} {'->'} {getLangLabel(chat.target_lang)}
                    </Table.Td>
                    <Table.Td>
                      <Switch checked={chat.is_active} onChange={() => onToggle(chat)} />
                    </Table.Td>
                    <Table.Td>
                      <ActionIcon color="red" variant="light" onClick={() => onDelete(chat.id)}>
                        <IconTrash size={16} />
                      </ActionIcon>
                    </Table.Td>
                  </Table.Tr>
                ))
              )}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      </Card>
    </Stack>
  );
}
