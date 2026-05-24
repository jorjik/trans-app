"""Generate locale files for all 7 new languages using deep-translator."""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

api_dir = os.path.join(os.path.dirname(__file__), '..', 'api')
sys.path.insert(0, api_dir)

from deep_translator import GoogleTranslator

LOCALES_DIR = os.path.join(os.path.dirname(__file__), '..', 'bot', 'locales')

with open(os.path.join(LOCALES_DIR, 'en.json'), encoding='utf-8') as f:
    en_data = json.load(f)

LANGUAGES = {
    'de': 'German',
    'fr': 'French',
    'es': 'Spanish',
    'it': 'Italian',
    'pt': 'Portuguese',
    'pl': 'Polish',
    'tr': 'Turkish',
}

def translate_text(text: str, target_lang: str) -> str:
    try:
        return GoogleTranslator(source='en', target=target_lang).translate(text)
    except Exception as e:
        print('  ERROR: ' + str(e))
        return text

for lang_code, lang_name in LANGUAGES.items():
    print()
    print('=== ' + lang_name + ' (' + lang_code + ') ===')
    out_file = os.path.join(LOCALES_DIR, lang_code + '.json')
    
    existing = {}
    if os.path.exists(out_file):
        print('  File exists, loading...')
        with open(out_file, encoding='utf-8') as f:
            existing = json.load(f)
    
    result = existing.copy()
    
    for i, (key, value) in enumerate(en_data.items()):
        if key in result and result[key]:
            continue
        if key == 'start_friend' or not value:
            result[key] = value
            continue
        print('  [' + str(i+1) + '/' + str(len(en_data)) + '] ' + key)
        translated = translate_text(value, lang_code)
        result[key] = translated
    
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print('  [OK] Saved ' + str(len(result)) + ' keys')

print()
print('=== All done! ===')
