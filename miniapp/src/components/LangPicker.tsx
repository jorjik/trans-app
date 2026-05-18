import { Modal, Select } from '@mantine/core';

import { LANGUAGE_OPTIONS } from '../api/langs';

interface LangPickerProps {
  opened: boolean;
  title: string;
  value: string;
  onClose: () => void;
  onChange: (value: string) => void;
  includeAuto?: boolean;
}

export function LangPicker({
  opened,
  title,
  value,
  onClose,
  onChange,
  includeAuto = false,
}: LangPickerProps) {
  const options = includeAuto
    ? LANGUAGE_OPTIONS
    : LANGUAGE_OPTIONS.filter((item) => item.value !== 'auto');

  return (
    <Modal opened={opened} onClose={onClose} title={title} centered>
      <Select
        searchable
        data={options}
        value={value}
        onChange={(next) => {
          if (next) {
            onChange(next);
            onClose();
          }
        }}
        nothingFoundMessage="No languages found"
      />
    </Modal>
  );
}
