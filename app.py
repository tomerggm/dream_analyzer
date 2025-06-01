import os
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, send_file, make_response
from openai import OpenAI
import csv
import requests
from datetime import datetime

app = Flask(__name__)

# Initialize OpenAI client without proxies
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    http_client=None  # This will use the default client without proxies
)

# Bit configuration
BIT_API_KEY = 'your_bit_api_key'  # החלף את זה במפתח האמיתי שלך מביט
BIT_API_URL = 'https://api.bit.co.il/v1'  # URL של ה-API של ביט

# Store dreams in memory (you might want to use a database in production)
dreams = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/interpret', methods=['GET', 'POST'])
def interpret():
    if request.method == 'GET':
        return redirect(url_for('index'))

    dream_text = request.form.get('dream')
    email = request.form.get('email')
    if not dream_text:
        return jsonify({'error': 'מצטער, אינני יכול לפרש חלום מבלי שתזין או תזיני חלום :)'}), 400
    # Save email and dream to CSV
    with open('dreams.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), email, dream_text])

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "אתה מומחה לפירוש חלומות"},
                {"role": "user", "content": f"פירש לי את החלום הבא בארבעה משפטים שלמים וברורים בלבד: {dream_text}"}
            ],
            max_tokens=300
        )
        interpretation = response.choices[0].message.content
        # Log dream themes for analytics
        app.logger.info(f"Dream interpretation request - Length: {len(dream_text)}")
        return jsonify({'interpretation': interpretation})
    except Exception as e:
        app.logger.error(f"Error in dream interpretation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/articles/dream-interpretation-guide')
def dream_guide():
    return render_template('articles/dream-interpretation-guide.html')

@app.route('/articles/ai-dream-interpretation')
def ai_interpretation():
    return render_template('articles/ai-dream-interpretation.html')

@app.route('/articles/recurring-dreams')
def recurring_dreams():
    return render_template('articles/recurring-dreams.html')

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

@app.route('/create-payment', methods=['POST'])
def create_payment():
    try:
        # יצירת עסקה חדשה בביט
        payment_data = {
            'amount': 19.90,
            'currency': 'ILS',
            'description': 'פירוש חלום מורחב ומעמיק',
            'success_url': f"{request.host_url}premium-interpretation",
            'cancel_url': f"{request.host_url}",
            'metadata': {
                'dream': request.form.get('dream', ''),
                'email': request.form.get('email', '')
            }
        }
        
        response = requests.post(
            f"{BIT_API_URL}/payments",
            json=payment_data,
            headers={'Authorization': f'Bearer {BIT_API_KEY}'}
        )
        
        if response.status_code == 200:
            payment_url = response.json()['payment_url']
            return jsonify({'payment_url': payment_url})
        else:
            return jsonify({'error': 'שגיאה ביצירת התשלום'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/premium-interpretation', methods=['GET', 'POST'])
def premium_interpretation():
    # בדיקת סטטוס התשלום
    payment_id = request.args.get('payment_id')
    if not payment_id:
        return redirect(url_for('index'))
        
    try:
        response = requests.get(
            f"{BIT_API_URL}/payments/{payment_id}",
            headers={'Authorization': f'Bearer {BIT_API_KEY}'}
        )
        
        if response.status_code == 200 and response.json()['status'] == 'completed':
            # התשלום הצליח, נחזיר את הפירוש המורחב
            dream = response.json()['metadata']['dream']
            email = response.json()['metadata']['email']
            
            # כאן תוכל להוסיף את הלוגיקה של הפירוש המורחב
            premium_interpretation = f"פירוש מורחב ומעמיק לחלום: {dream}\n\n" + \
                                  "ניתוח מעמיק של סמלים ומוטיבים:\n" + \
                                  "המלצות מעשיות להתמודדות:\n" + \
                                  "פירוש בהקשר אישי:\n" + \
                                  "תובנות נוספות:"
            
            return render_template('premium_result.html', interpretation=premium_interpretation)
        else:
            return redirect(url_for('index'))
            
    except Exception as e:
        return redirect(url_for('index'))

@app.route('/premium-interpretation-success')
def premium_interpretation_success():
    # כאן אפשר להוסיף לוגיקה כלשהי אם צריך
    # למשל, שמירה ב-CSV אחר שהתשלום עבר
    # או שליחת אימייל אוטומטית עם אישור

    # מכיוון שהפירוש המורחב נשלח ידנית לאחר 24 שעות,
    # מספיק להציג דף תודה.
    return render_template('premium_success.html')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
