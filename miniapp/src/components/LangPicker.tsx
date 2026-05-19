import { Modal, Select } from '@mantine/core';

import { LANGUAGE_OPTIONS } from '../api/langs';
import { t } from '../i18n';

interface LangPickerProps {
  opened: boolean;
  title: string;
  value: string;
  onClose: () => void;
  onChange: (value: string) => void;
  includeAuto?: boolean;
  uiLang?: string;
}

export function LangPicker({
  opened,
  title,
  value,
  onClose,
  onChange,
  includeAuto = false,
  uiLang = 'en',
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
        nothingFoundMessage={t('lang.not_found', uiLang)}
      />
    </Modal>
  );
}
