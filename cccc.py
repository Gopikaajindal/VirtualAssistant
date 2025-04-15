import httpx
import yaml
import speech_recognition as sr
import pyttsx3
from pydub import AudioSegment 
import soundfile as sf
import numpy as np
import tempfile
import os
import simpleaudio as sa
import datetime
import wikipedia
import pyjokes
import pywhatkit



# Manually set the path to ffmpeg and ffprobe if needed
os.environ["PATH"] += os.pathsep + r"D:\documents\ffmpeg-master-latest-win64-gpl\bin" # Adjust the path as necessary

# Now proceed with your script
AudioSegment.converter = r"D:\documents\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\\ffmpeg\\bin\\ffprobe.exe"

# Your code

# Load configuration from YAML file
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

def fetch_error_audio_url():
    url = 'https://eva-replica.hellojio.jio.com/jiointeract/api/v2/bot/config/botsettings'
    params = {
        "botId": config['chatbot']['botid'],
        "botName": config['chatbot']['botName'],
        "clientKey": config['chatbot']['clientKey'],
        "context": "default"
    }
    response = httpx.get(url, params=params)
    if response.is_success:
        data = response.json()
        for setting in data.get('botSettings', []):
            if setting.get('key') == 'user_input_error_audios':
                return setting.get('setting', [])[0]  # Assuming the URL is the first item in the list
    else:
        print(f"Failed to fetch bot settings. Status code: {response.status_code}, Response: {response.text}")
    return None

def download_and_convert_audio(url):
    response = httpx.get(url)
    if response.status_code == 200:
        temp_mp3_path = tempfile.mktemp(suffix=".mp3")
        with open(temp_mp3_path, 'wb') as mp3_file:
            mp3_file.write(response.content)
        
        # Use pydub to convert MP3 to WAV
        temp_wav_path = tempfile.mktemp(suffix=".wav")
        audio = AudioSegment.from_mp3(temp_mp3_path)
        audio.export(temp_wav_path, format="wav")
        
        os.remove(temp_mp3_path)  # Clean up the temporary MP3 file
        return temp_wav_path
    else:
        print("Failed to download audio.")
        return None


def play_error_audio(file_path):
    try:
        wave_obj = sa.WaveObject.from_wave_file(file_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()  # Wait until the audio file finishes playing
    except Exception as e:
        print(f"Error playing audio: {e}")

def modified_listen(error_audio_path):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            print("You said:", text)
            return text
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio.")
            if error_audio_path:
                play_error_audio(error_audio_path)
            return ""
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return ""

# Initializing the speech engine and setting properties
listener = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
engine.setProperty('rate', 150)

def talk(text):
    engine.say(text)
    engine.runAndWait()

def take_command():
    command = ''
    try:
        with sr.Microphone() as source:
            print('listening...')
            voice = listener.listen(source)
            command = listener.recognize_google(voice)
            command = command.lower()
            if 'assistant' in command:
                command = command.replace('assistant', '')
                print(command)
    except Exception as e:
        print("An error occurred:", e)
    return command

def run_assistant():
    command = take_command()
    if command:
        print(command)
        if 'play' in command:
            song = command.replace('play', '')
            talk('playing ' + song)
            pywhatkit.playonyt(song)
        elif 'time' in command:
            time = datetime.datetime.now().strftime('%I:%M %p')
            talk('Current time is ' + time)
        elif 'who the heck is' in command:
            person = command.replace('who the heck is', '')
            info = wikipedia.summary(person, 1)
            print(info)
            talk(info)
        elif 'date' in command:
            talk('sorry, I have a headache')
        elif 'are you single' in command:
            talk('I am in a relationship with wifi')
        elif 'joke' in command:
            talk(pyjokes.get_joke())
        elif 'talk to chatbot' in command:
            interact_with_chatbot()
        else:
            talk('Please say the command again.')
    else:
        talk("I didn't catch that. Please try again.")

def interact_with_chatbot():
    # Placeholder for chatbot interaction logic
    session_id = create_session()
    if session_id:
        error_audio_url = fetch_error_audio_url()
        error_audio_path = None
        if error_audio_url:
            error_audio_path = download_and_convert_audio(error_audio_url)
        welcome_message = "welcome"
        welcome_response = send_message(session_id, welcome_message, error_audio_path)
        talk(welcome_response)
        user_input = modified_listen(error_audio_path)
        if user_input.lower() != 'exit':
            response_text = send_message(session_id, user_input, error_audio_path)
            talk(response_text)

# Defining chatbot functions (create_session, send_message, speak) with actual logic
def create_session():
    url = 'https://eva-replica.hellojio.jio.com/jiointeract/api/v1/session/create'
    payload = {
        "botName": "EVA Alexa POC",
        "botid": "bo-f907773e-9730-4167-88ff-4079014f40e8",
        "clientKey": "s-ea0e0c08-2dd3-4152-bc58-175c5f32603f",
        "context": "default",
        "botResponseType": "Text | Audio",
        "language": "en",
        "user": {
            "ani": "user_mobile_number",  # Replace with actual mobile number of the user.
            "uld": "user_unique_identifier"  # Replace with actual unique identifier of the user.can a comment goin two lines
            
        }
    }
    response = httpx.post(url, json=payload)
    if response.is_success:
        session_id = response.json().get('sessionId')
        print("Session ID:", session_id)
        return session_id
    else:
        print(f"Failed to create session. Status code: {response.status_code}, Response: {response.text}")
        return None

def send_message(session_id, message, error_audio_path):
    url = f'{config["chatbot"]["url_send_message"]}?sessionId={session_id}'
    payload = {
        "query": message,
        "lang": "en",
        "mode": "Text | Audio",
        "responseType": "All",
        "botId": config['chatbot']['botid']
    }
    response = httpx.post(url, json=payload)
    if response.is_success:
        response_data = response.json()
        print("Chatbot says:", response_data)
        
        speech_text = ''
        if 'action' in response_data and 'modes' in response_data['action']:
            for mode in response_data['action']['modes']:
                if mode['type'] == 'Text' and 'data' in mode:
                    if mode['data'] is None:  # If data is None, play error audio and return
                        play_error_audio(error_audio_path)
                        return "I did not understand that."
                    for data in mode['data']:
                        if 'textData' in data and data['textData']:
                            speech_text += data['textData'] + ' '
        if not speech_text:  # Handling null or empty textData
            play_error_audio(error_audio_path)
            return "This query is not recognized by the chatbot."
        return speech_text.strip()
    else:
        print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")
        play_error_audio(error_audio_path)
        return "Failed to communicate with the chatbot."

def speak(text):
    talk(text)

if __name__ == '__main__':
    run_assistant()
#welcome where do you live who is prime minister of India how many states are in India

