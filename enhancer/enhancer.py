from flask import Flask, request, jsonify
from g4f.client import Client
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.config['AUDIO_FOLDER'] = 'C:/Users/mmant/OneDrive/Desktop/CP-2/student'

# def enhance_text(text):
#     # Checking if the text ends with a punctuation mark. If not, add a period to make it a complete sentence.
#     if text[-1] not in ['.', '!', '?']:
#         text += '.'

#     # Creating a prompt for the text enhancement.
#     prompt = (
#         "This is a tool designed to help improve the clarity and readability of text and enhances the text.\n"
#         "Please provide a sentence or a phrase that you'd like to enhance:\n"
#         f"User: {text}"
#     )

#     # Initializing the GPT-3.5 Turbo model.
#     client = Client()

#     # Generating an enhanced version of the text.
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "This tool helps improve text clarity, readability and enhancement."},
#             {"role": "user", "content": text},
#         ],
#         max_tokens=150,
#         n=1,
#         stop=None,
#         temperature=0.5,
#         prompt=prompt  # Passing the prompt to the completion API
#     )

#     # Extracting the enhanced text from the response.
#     enhanced_text = response.choices[0].message.content.strip()

#     return enhanced_text

def enhance_text(text):
    client = Client()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that enhances the text."},
            {"role": "user", "content": f"Please add executive-level punctuation to the following text: {text}"},
        ],
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.5,
    )
    enhanced_text = response.choices[0].message.content.strip()
    return enhanced_text

@app.route('/enhance-text', methods=['POST'])
def handle_enhance_text():
    data = request.get_json()
    text = data.get('text')

    if text is None:
        return jsonify({'error': 'Text parameter is missing or invalid'}), 400

    enhanced_text = enhance_text(text)
    return jsonify({'enhanced_text': enhanced_text})

@app.route('/receive_audio', methods=['POST'])
def receive_audio():
    print("accepted")
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Save audio file to a folder
        audio_file.save(os.path.join(app.config['AUDIO_FOLDER'], secure_filename(audio_file.filename)))

        return jsonify({'message': 'Audio file received and saved successfully'})
    
    except Exception as e:
        print("Error receiving audio file:", e)
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=6000)
