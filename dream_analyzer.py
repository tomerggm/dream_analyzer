import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Move API key to environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/interpret', methods=['POST'])
def interpret():
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
        return jsonify({'interpretation': interpretation})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
