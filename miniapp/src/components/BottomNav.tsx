import { Text, UnstyledButton } from '@mantine/core';
import type { TablerIcon } from '@tabler/icons-react';

interface NavItem {
  key: string;
  label: string;
  icon: TablerIcon;
}

interface BottomNavProps {
  items: readonly NavItem[];
  active: string;
  onTabClick: (key: string) => void;
}

export function BottomNav({ items, active, onTabClick }: BottomNavProps) {
  return (
    <nav
      style={{
        display: 'flex',
        height: '100%',
        alignItems: 'stretch',
      }}
    >
      {items.map((item) => {
        const isActive = active === item.key;
        return (
          <UnstyledButton
            key={item.key}
            onClick={() => onTabClick(item.key)}
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 1,
              paddingBottom: 4,
              color: isActive
                ? 'var(--mantine-color-blue-4)'
                : 'var(--mantine-color-gray-5)',
              borderTop: isActive ? '2px solid var(--mantine-color-blue-4)' : '2px solid transparent',
              transition: 'color 0.15s ease, border-color 0.15s ease',
            }}
          >
            <item.icon size={22} stroke={isActive ? 2.5 : 1.8} />
            <Text size="xs" fw={isActive ? 600 : 400}>
              {item.label}
            </Text>
          </UnstyledButton>
        );
      })}
    </nav>
  );
}
