from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import speech_recognition as sr
import io
from pydub import AudioSegment
from mtranslate import translate
import mysql.connector
import base64
from werkzeug.utils import secure_filename
import tempfile
import os
import librosa
import soundfile as sf
from speech_recognition import AudioData
import time
import requests
from datetime import datetime


app = Flask(__name__)
CORS(app)

# Initialize SpeechRecognition
recognizer = sr.Recognizer()

# Connect to MySQL server
try:
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="Education_system",  # Updated database name
        )
    cursor = db_connection.cursor()
except Exception as e:
    print(e)
@app.route('/')
def index():
    return send_from_directory('static', 'translate.html')

@app.route('/get_lectures')
def get_lectures():
    class_name = request.args.get('class')
    day  = request.args.get('day')

    # Fetch lectures based on class name
    query = "SELECT lecture_name FROM Class_lectures WHERE class_id = (SELECT id FROM Classes WHERE class_name = %s) AND day=%s"
    cursor.execute(query, (class_name,day))
    lectures = [row[0] for row in cursor.fetchall()]
    return jsonify(lectures)

@app.route('/get_classes')
def get_classes():
    # Fetch class names
    cursor.execute("SELECT class_name FROM Classes")
    classes = [row[0] for row in cursor.fetchall()]
    return jsonify(classes)

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        audio_data = request.files['audio'].read()
        class_name = request.form['class']
        lecture_name = request.form['lecture']
        date = request.form['date']

        # byte_audio_data = base64.b64encode(audio_data).decode('utf-8')
        # Convert audio to WAV format
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
        wav_data = io.BytesIO()
        audio.export(wav_data, format="wav")

        # wav_binary_data = wav_data.getvalue()
        # Transcribe audio using SpeechRecognition
        wav_data.seek(0)  # Move to the start of the BytesIO object
        
        with sr.AudioFile(wav_data) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        
        if text:
            # Translate text to Hindi and Gujarati
            translation_hindi = translate(text, 'hi')
            translation_gujarati = translate(text, 'gu')

            # Store data in the database
            query = "INSERT INTO Lecture_data (class_id, lecture_name, date, audio, english_transcript, hindi_translation, gujarati_translation) VALUES ((SELECT id FROM Classes WHERE class_name = %s), %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (class_name, lecture_name, date, audio_data, text, translation_hindi, translation_gujarati))
            db_connection.commit()

            return jsonify({'transcript': text, 'translation_hindi': translation_hindi, 'translation_gujarati': translation_gujarati})
        else:
            return jsonify({'error': 'Transcription failed or returned empty text'}), 500
    except Exception as e:
        print("Error processing audio:", e)
        return jsonify({'error': 'Internal server error'}), 500
    
@app.route('/upload_audio', methods=['POST'])  
def upload_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        class_name = request.form['class']
        lecture_name = request.form['lecture']
        date = request.form['date']
        date += datetime.now().strftime(' %H:%M:%S')
        faculty ="hms"
        audio_file_name = class_name + "_" + lecture_name + "_" + request.form['date'] + ".mp3"
        english = "English"
        hindi = "Hindi"
        gujarati = "Gujarati"

        if audio_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Save audio file to temporary location
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, secure_filename(audio_file_name))
        audio_file.save(temp_file_path)

        # files = {'audio': open(temp_file_path, 'rb')}
        # response = requests.post("http://localhost:6000/receive_audio", files=files)

        # Split audio file into 1-minute segments
        segments = split_audio(temp_file_path)

        transcriptions = []
        hindi_translations = []
        gujarati_translations = []

        for segment in segments:
            
        # Convert audio segment to WAV format
            wav_data = convert_to_wav(segment)
            try:
                # Transcribe audio using SpeechRecognition
                text = transcribe_audio(wav_data)
                try:
                    response = requests.post("http://localhost:6000/enhance-text", json={'text': text})
                    enhanced_text = response.json().get('enhanced_text', '')
                    # enhanced_text = gemini_api.enhance_text(text, api_key=gemini_api_key)
                except Exception as e:
                    print(f"Error enhancing text: {e}")
                    enhanced_text = ""
                # enhanced_text = gemini_api.enhance_text(text, api_key=gemini_api_key)
            except:
                text=""
                enhanced_text=""
            time.sleep(30)

            if text:
                transcriptions.append(enhanced_text)
                print("transcribe done")

                # Translate text to Hindi and Gujarati
                hindi_translation = translate(enhanced_text, 'hi')
                gujarati_translation = translate(enhanced_text, 'gu')
                print("Translate done")
                hindi_translations.append(hindi_translation)
                gujarati_translations.append(gujarati_translation)
            else:
                transcriptions.append("")
                hindi_translations.append("")
                gujarati_translations.append("")
            

        # Combine transcriptions from all segments
        combined_transcription = " ".join(transcriptions)
        combined_hindi_translation = " ".join(hindi_translations)
        combined_gujarati_translation = " ".join(gujarati_translations)
        
        send_data_to_endpoint(date, datetime.now().year, class_name[0], class_name, lecture_name, faculty, audio_file_name, english, combined_transcription)
        send_data_to_endpoint(date, datetime.now().year, class_name[0], class_name, lecture_name, faculty, audio_file_name, hindi, combined_hindi_translation)
        send_data_to_endpoint(date, datetime.now().year, class_name[0], class_name, lecture_name, faculty, audio_file_name, gujarati, combined_gujarati_translation)
        # Store data in the database
        # query = "INSERT INTO Lecture_data (class_id, lecture_name, date, english_transcript, hindi_translation, gujarati_translation) VALUES ((SELECT id FROM Classes WHERE class_name = %s), %s, %s, %s, %s, %s)"
        # cursor.execute(query, (class_name, lecture_name, date, combined_transcription, combined_hindi_translation, combined_gujarati_translation))
        # db_connection.commit()

        return jsonify({'transcript': combined_transcription, 'translation_hindi': combined_hindi_translation, 'translation_gujarati': combined_gujarati_translation})
        # return jsonify({'transcript': combined_transcription})

    except Exception as e:
        print("Error processing uploaded audio:", e)
        return jsonify({'error': 'Internal server error'}), 500
    

def send_data_to_endpoint(date_time, academic_year, semester, class_name, subject, faculty, audio_file_name, language, audio_to_text):
    endpoint_url = "https://guni-student-info-chat-bot.onrender.com/store_audio_data"

    data = {
        "Date_Time": date_time,
        "Academic_Year": academic_year,
        "Semester": semester,
        "Class": class_name,
        "Subject": subject,
        "Faculty": faculty,
        "Audio_File_name": audio_file_name,
        "Language": language,
        "Audio_To_Text": audio_to_text
    }

    response = requests.post(endpoint_url, json=data)

    if response.status_code == 200:
        print("Data sent successfully to the endpoint")
    else:
        print("Failed to send data to the endpoint. Status code:", response.status_code)

# Example usage:
# send_data_to_endpoint('date_Time', 2024, 6, 'IT', 'AI', 'hms', 'audio_file.mp3', 'english', 'english text')



def split_audio(audio_file_path, segment_length=60000):  # 1 minute = 60000 milliseconds
    audio = AudioSegment.from_file(audio_file_path)
    num_segments = len(audio) // segment_length + 1
    segments = []
    for i in range(num_segments):
        start_time = i * segment_length
        end_time = min((i + 1) * segment_length, len(audio))
        segment = audio[start_time:end_time]
        segments.append(segment)
    return segments

def convert_to_wav(audio_segment):
    wav_data = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    wav_data_path = wav_data.name
    audio_segment.export(wav_data_path, format="wav")
    wav_data.close()
    return wav_data_path

def transcribe_audio(wav_data_path):
    with sr.AudioFile(wav_data_path) as source:
        audio_data = recognizer.record(source)
    text = recognizer.recognize_google(audio_data)
    return text
    
if __name__ == '__main__':
    app.run(debug=True, port=5000)
