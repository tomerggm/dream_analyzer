import os
import json
import glob as glob_module
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, Response, session
from flask_compress import Compress
from flask_caching import Cache
from openai import OpenAI
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
Compress(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    http_client=None
)

INTERPRETATION_PRICE = os.getenv('INTERPRETATION_PRICE', '4.90')
PAYPAL_BUTTON_ID = os.getenv('PAYPAL_BUTTON_ID', 'KY9UPB3L5U2F4')

ARTICLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'articles_data')
os.makedirs(ARTICLES_DIR, exist_ok=True)


def interpret_dream(dream_text):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": (
                "אתה מומחה בכיר לפירוש חלומות עם ידע עמוק בפסיכולוגיה, סמלים תרבותיים, ומסורת יהודית.\n"
                "ענה בעברית בלבד. השתמש בתגיות HTML לעיצוב התשובה.\n\n"
                "מבנה התשובה:\n\n"
                "<h3>משמעות החלום</h3>\n"
                "<p>פסקה עם הפירוש הכללי והמשמעות הרגשית של החלום.</p>\n\n"
                "<h3>ניתוח סמלים</h3>\n"
                "<ul>\n<li><strong>סמל:</strong> משמעות הסמל בחלום</li>\n</ul>\n\n"
                "<h3>תובנות ועצות</h3>\n"
                "<ul>\n<li>המלצה מעשית</li>\n</ul>\n\n"
                "<h3>הקשר תרבותי</h3>\n"
                "<p>החלום בהקשר של מסורת יהודית או תרבות ישראלית, אם רלוונטי.</p>"
            )},
            {"role": "user", "content": f"פרש את החלום הבא בצורה מעמיקה ומקצועית:\n\n{dream_text}"}
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content


def load_articles():
    articles = []
    if not os.path.exists(ARTICLES_DIR):
        return articles
    for filepath in glob_module.glob(os.path.join(ARTICLES_DIR, '*.json')):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                articles.append(json.load(f))
        except (json.JSONDecodeError, IOError):
            continue
    articles.sort(key=lambda a: a.get('date', ''), reverse=True)
    return articles


def load_article_by_slug(slug):
    filepath = os.path.join(ARTICLES_DIR, f'{slug}.json')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


@app.route('/')
def index():
    return render_template('index.html', price=INTERPRETATION_PRICE, paypal_button_id=PAYPAL_BUTTON_ID)


@app.route('/prepare-payment', methods=['POST'])
def prepare_payment():
    dream_text = request.json.get('dream', '')
    if not dream_text.strip():
        return jsonify({'error': 'נא להזין חלום'}), 400
    session['dream_text'] = dream_text
    return jsonify({'ok': True})


@app.route('/payment-success')
def payment_success():
    dream_text = session.pop('dream_text', None)
    if not dream_text:
        return redirect(url_for('index'))

    try:
        interpretation = interpret_dream(dream_text)
    except Exception as e:
        app.logger.error(f"Error interpreting dream: {e}")
        return render_template('payment_success.html',
                               error='אירעה שגיאה בפירוש החלום. אנא פנו לתמיכה.')

    with open('dreams.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'paypal', dream_text])

    app.logger.info(f"Paid interpretation - Length: {len(dream_text)}")
    return render_template('payment_success.html', interpretation=interpretation)


@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')


@app.route('/sitemap.xml')
def sitemap():
    urls = [
        {'loc': 'https://halomotai.co.il/', 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': 'https://halomotai.co.il/articles', 'changefreq': 'daily', 'priority': '0.9'},
        {'loc': 'https://halomotai.co.il/faq', 'changefreq': 'weekly', 'priority': '0.8'},
        {'loc': 'https://halomotai.co.il/articles/dream-interpretation-guide', 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': 'https://halomotai.co.il/articles/ai-dream-interpretation', 'changefreq': 'monthly', 'priority': '0.8'},
        {'loc': 'https://halomotai.co.il/articles/recurring-dreams', 'changefreq': 'monthly', 'priority': '0.8'},
    ]
    for article in load_articles():
        urls.append({
            'loc': f"https://halomotai.co.il/articles/{article['slug']}",
            'lastmod': article.get('date', ''),
            'changefreq': 'monthly',
            'priority': '0.7'
        })

    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml_parts.append('  <url>')
        xml_parts.append(f'    <loc>{u["loc"]}</loc>')
        if u.get('lastmod'):
            xml_parts.append(f'    <lastmod>{u["lastmod"]}</lastmod>')
        xml_parts.append(f'    <changefreq>{u["changefreq"]}</changefreq>')
        xml_parts.append(f'    <priority>{u["priority"]}</priority>')
        xml_parts.append('  </url>')
    xml_parts.append('</urlset>')
    return Response('\n'.join(xml_parts), mimetype='application/xml')


@app.route('/articles/dream-interpretation-guide')
def dream_guide():
    return render_template('articles/dream-interpretation-guide.html')


@app.route('/articles/ai-dream-interpretation')
def ai_interpretation():
    return render_template('articles/ai-dream-interpretation.html')


@app.route('/articles/recurring-dreams')
def recurring_dreams():
    return render_template('articles/recurring-dreams.html')


@app.route('/articles')
@cache.cached(timeout=300)
def articles_list():
    articles = load_articles()
    return render_template('articles_list.html', articles=articles)


@app.route('/articles/<slug>')
def article_detail(slug):
    article = load_article_by_slug(slug)
    if not article:
        return redirect(url_for('articles_list'))
    return render_template('article_detail.html', article=article)


@app.route('/חלומות')
def dreams_hebrew():
    return redirect(url_for('index'))


@app.route('/חלומות-חוזרים')
def recurring_dreams_hebrew():
    return redirect(url_for('recurring_dreams'))


@app.route('/פירוש-חלומות')
def dream_interpretation_hebrew():
    return redirect(url_for('index'))


@app.route('/בינה-מלאכותית-וחלומות')
def ai_dreams_hebrew():
    return redirect(url_for('ai_interpretation'))


@app.route('/מדריך-לפירוש-חלומות')
def guide_hebrew():
    return redirect(url_for('dream_guide'))


@app.route('/שאלות-נפוצות')
def faq_hebrew():
    return redirect(url_for('faq'))


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.png', mimetype='image/png')


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
