import os
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, send_file, make_response
from openai import OpenAI

app = Flask(__name__)

# Initialize OpenAI client without proxies
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    http_client=None  # This will use the default client without proxies
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/interpret', methods=['GET', 'POST'])
def interpret():
    if request.method == 'GET':
        return redirect(url_for('index'))

    dream_text = request.form.get('dream')
    if not dream_text:
        return jsonify({'error': 'נא להזין חלום'}), 400

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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
