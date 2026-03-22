import os
import json
import re
from datetime import datetime
from openai import OpenAI

ARTICLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'articles_data')
TOPICS_FILE = os.path.join(ARTICLES_DIR, 'used_topics.json')

DREAM_TOPICS = [
    "חלומות על טיסה ומעוף",
    "חלומות על נפילת שיניים",
    "חלומות על מים ושיטפון",
    "חלומות חוזרים ומשמעותם",
    "חלומות על בית ספר ומבחנים",
    "חלומות על מוות ומשמעותם",
    "חלומות על בעלי חיים",
    "חלומות על רדיפה ובריחה",
    "חלומות על נהיגה ותאונות",
    "חלומות על הריון ולידה",
    "חלומות על אנשים שנפטרו",
    "חלומות על נחשים",
    "חלומות על נפילה",
    "חלום צלול - מהו ואיך להגיע אליו",
    "חלומות על חתונה ואירוסין",
    "חלומות על עירום בציבור",
    "חלומות על כסף ועושר",
    "חלומות על ילדות",
    "חלומות על אובדן דרך",
    "חלומות על לילה ואפלה",
    "חלומות על אש ושריפה",
    "חלומות על ים ושחייה",
    "חלומות על גשם וסערה",
    "חלומות על מלחמה ולחימה",
    "חלומות על תינוקות",
    "סיוטים - למה הם קורים ואיך להתמודד",
    "חלומות על בגידה",
    "חלומות על מרחבים פתוחים ומקומות סגורים",
    "חלומות על מטוס ונסיעות",
    "חלומות על אכילה ומזון",
    "חלומות בתלמוד והמסורת היהודית",
    "חלומות בספרות הקבלה",
    "פרויד ופירוש חלומות",
    "יונג וארכיטיפים בחלומות",
    "חלומות מנבאים - אמת או מיתוס",
    "איך לזכור חלומות טוב יותר",
    "יומן חלומות - למה זה חשוב ואיך לכתוב",
    "חלומות של ילדים",
    "חלומות בזמן הריון",
    "חלומות והשפעת סטרס",
]


def get_used_topics():
    if os.path.exists(TOPICS_FILE):
        with open(TOPICS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_used_topic(topic):
    used = get_used_topics()
    used.append(topic)
    with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def get_next_topic():
    used = get_used_topics()
    for topic in DREAM_TOPICS:
        if topic not in used:
            return topic
    with open(TOPICS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)
    return DREAM_TOPICS[0]


def slugify(text):
    text = text.strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def generate_article(topic):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": (
                "אתה כותב תוכן מקצועי בעברית בנושא חלומות ופירוש חלומות.\n"
                "כתוב מאמר SEO-friendly בעברית. המאמר צריך להיות:\n"
                "- כ-800 מילים\n"
                "- כתוב בסגנון מקצועי ונגיש\n"
                "- מחולק לכותרות משנה עם תגיות <h2>\n"
                "- כולל רשימות (<ul>/<li>) כאשר מתאים\n"
                "- כולל פסקאות ברורות (<p>)\n"
                "- כולל טיפים מעשיים\n"
                "- כולל בסוף הפניה לפירוש חלומות באתר halomotai.co.il\n\n"
                "ענה בפורמט JSON בלבד:\n"
                '{\n'
                '  "title": "כותרת המאמר",\n'
                '  "meta_description": "תיאור מטא קצר של עד 150 תווים",\n'
                '  "content": "<p>תוכן HTML של המאמר</p>"\n'
                '}'
            )},
            {"role": "user", "content": f"כתוב מאמר מקצועי ומעמיק בנושא: {topic}"}
        ],
        max_tokens=2500,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


def main():
    os.makedirs(ARTICLES_DIR, exist_ok=True)

    topic = get_next_topic()
    print(f"Generating article about: {topic}")

    article_data = generate_article(topic)

    slug = slugify(topic)
    date = datetime.now().strftime('%Y-%m-%d')

    article = {
        'title': article_data['title'],
        'slug': slug,
        'meta_description': article_data['meta_description'],
        'content': article_data['content'],
        'date': date,
        'topic': topic
    }

    filepath = os.path.join(ARTICLES_DIR, f'{slug}.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(article, f, ensure_ascii=False, indent=2)

    save_used_topic(topic)
    print(f"Article saved: {filepath}")


if __name__ == '__main__':
    main()
