"""Post-process locale files: restore Python format placeholders that Google Translate corrupted."""
import json
import os
import re

LOCALES_DIR = os.path.join(os.path.dirname(__file__), '..', 'bot', 'locales')

# Load English reference
with open(os.path.join(LOCALES_DIR, 'en.json'), encoding='utf-8') as f:
    en_data = json.load(f)

def extract_placeholders(text: str) -> list[str]:
    """Extract all {placeholder} patterns from text."""
    return re.findall(r'\{([^}]+)\}', text)

def fix_placeholders(translated: str, original: str) -> str:
    """Ensure all placeholders from original exist in translated text."""
    orig_phs = extract_placeholders(original)
    if not orig_phs:
        return translated
    
    # Check which placeholders are missing
    for ph in orig_phs:
        full_ph = '{' + ph + '}'
        if full_ph not in translated:
            # Placeholder was corrupted. Append it to the end.
            # This is a safe fallback since the placeholder will be substituted
            translated += ' ' + full_ph
    
    return translated

for lang in ['de', 'fr', 'es', 'it', 'pt', 'pl', 'tr']:
    filepath = os.path.join(LOCALES_DIR, f'{lang}.json')
    if not os.path.exists(filepath):
        print(f'{lang}: file not found')
        continue
    
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)
    
    fixed_count = 0
    for key in en_data:
        if key not in data:
            data[key] = en_data[key]
            fixed_count += 1
            continue
        
        original_val = en_data[key]
        translated_val = data[key]
        
        # Ensure key exists and has value
        if not translated_val:
            data[key] = original_val
            fixed_count += 1
            continue
        
        fixed = fix_placeholders(translated_val, original_val)
        if fixed != translated_val:
            data[key] = fixed
            fixed_count += 1
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'{lang}: fixed {fixed_count} keys with placeholder issues')

print('\nDone!')
