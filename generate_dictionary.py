import os
import json
from datetime import datetime
from openai import OpenAI

DICTIONARY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dictionary_data')
USED_FILE = os.path.join(DICTIONARY_DIR, 'used_symbols.json')

DREAM_SYMBOLS = [
    "מים", "טיסה", "נחש", "נפילה", "שיניים", "מוות", "רדיפה", "בית",
    "אש", "ים", "תינוק", "חתונה", "מכונית", "כלב", "חתול", "גשם",
    "ירח", "שמש", "פרחים", "מפתח", "דלת", "מדרגות", "מראה", "שעון",
    "כסף", "ציפור", "דג", "עכביש", "חושך", "אור", "הר", "גשר",
    "רכבת", "עץ", "גן", "מערה", "שלג", "רוח", "ברק", "ספינה",
]


def get_used_symbols():
    if os.path.exists(USED_FILE):
        with open(USED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_used_symbol(symbol):
    used = get_used_symbols()
    used.append(symbol)
    with open(USED_FILE, 'w', encoding='utf-8') as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def get_next_symbol():
    used = get_used_symbols()
    for symbol in DREAM_SYMBOLS:
        if symbol not in used:
            return symbol
    with open(USED_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)
    return DREAM_SYMBOLS[0]


def generate_entry(symbol):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": (
                "אתה מומחה לפירוש חלומות וסמלים בחלומות.\n"
                "כתוב ערך מילוני מקיף בעברית על סמל בחלומות.\n"
                "הערך צריך להיות ~500 מילים, כתוב ב-HTML, וכולל:\n"
                "- פסקת פתיחה על המשמעות הכללית של הסמל בחלומות\n"
                "- כותרת <h2> עם תרחישים נפוצים (לפחות 4) כרשימה <ul>\n"
                "- כותרת <h2> עם פירוש פסיכולוגי\n"
                "- כותרת <h2> עם הקשר תרבותי/יהודי\n"
                "- כותרת <h2> עם טיפים מעשיים\n\n"
                "ענה בפורמט JSON בלבד:\n"
                '{\n'
                '  "title": "חלום על [סמל] - פירוש ומשמעות",\n'
                '  "meta_description": "תיאור מטא קצר עד 150 תווים",\n'
                '  "content": "<p>תוכן HTML</p>"\n'
                '}'
            )},
            {"role": "user", "content": f"כתוב ערך מילוני מקיף על הסמל: {symbol}"}
        ],
        max_tokens=2000,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


def main():
    os.makedirs(DICTIONARY_DIR, exist_ok=True)

    symbol = get_next_symbol()
    print(f"Generating dictionary entry for: {symbol}")

    entry_data = generate_entry(symbol)

    entry = {
        'symbol': symbol,
        'title': entry_data['title'],
        'meta_description': entry_data['meta_description'],
        'content': entry_data['content'],
        'date': datetime.now().strftime('%Y-%m-%d')
    }

    filepath = os.path.join(DICTIONARY_DIR, f'{symbol}.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)

    save_used_symbol(symbol)
    print(f"Entry saved: {filepath}")


if __name__ == '__main__':
    main()
