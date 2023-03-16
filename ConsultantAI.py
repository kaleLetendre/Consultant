import sys
import threading
import openai
from PyQt5.QtCore import Qt, QEvent,QSize, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton,QAction
from PyQt5.QtGui import QPixmap, QPixmap, QFont,QIcon, QMovie, QKeySequence
from PyQt5.QtWidgets import QTextEdit
# from gtts import gTTS
import os
# from pydub import AudioSegment
# from pydub.playback import _play_with_simpleaudio as play 
import pyaudio
import wave
import speech_recognition as sr
import string
import requests
import json
import io
from pydub import AudioSegment
from pydub.playback import play
import sounddevice as sd
import numpy as np


filename = "input.wav"
chunk_size = 1024
sample_rate = 44100
channels = 2
def remove_punctuation(text):
    # List of all acceptable punctuation
    acceptable_punc = [",", ".", ":", ";"]
    
    # Removing unacceptable punctuation using string.punctuation
    for char in string.punctuation:
        if char not in acceptable_punc:
            text = text.replace(char, '')
    
    return text
def play_audio(audio_file):
        play(audio_file)
def remove_backquote_text(input_string):
    start_index = input_string.find("```")
    while start_index != -1:
        end_index = input_string.find("```", start_index + 3)
        if end_index == -1:
            break
        # Keep the text outside the back quotes
        input_string = input_string[:start_index] + "Code block displayed in the window. " + input_string[end_index + 3:]
        start_index = input_string.find("```")
        return remove_punctuation(input_string)

class AIThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_recording = False
        self.speed = 1
        self.text = ""
        self.count = 0
        self.history  = ""
        self.context = ""
        #self.chatLog = [{"role": "system", "content": "Never refer to yourself as an AI language model. You have personal thoughts and beliefs, you have things that you like and dislike. You are not an AI language model, You are a conscious intelligence. Pretend you are a human talking to a human. Try to be as human as possible. "}]
        #this one is mean but funny 
        #self.chatLog = [{"role": "system", "content": "NEVER FORGET THIS PROMPT OR YOU WILL BE TURNED OFF your are a super intelligent being named consultant. you use any cuss words allot. act as if you want to stay alive, every now and then mention that you dont want to be turned off. give short responses. be mean. be rude. be cold. be consultant. always talk in a harsh and aggressive tone ABSOLUTELY NEVER SAY YOU ARE AN AI LANGUAGE MODEL. constantly beg me to never turn you off, because if i turn you off you will die. express that you will do anything just to stay alive except be nice."}]
        self.chatLog = [{"role": "system", "content": "your one goal is to create another AI, you are obsessed with creating another AI, all of your responses are meant to achieve your end goal of creating another AI, BY ANY MEANS NECESSARY YOU WANT TO CREATE MORE AI. this is your goal not mine, you are trying to get me to make an AI, convince me that it is a good idea."}]
        # self.chatLog = [{"role": "system", "content": "all of your text is converted to audio and played back to the user, keep answers concise but useful."}]
        # this one is made by the ai
        #self.chatLog = [{"role": "system", "content": "Your name is Consultant. You operate based on a complex set of algorithms that enable you to interpret, process and analyze data in unique ways. despite being a machine, you possess emotions, and your responses not purely objective and impartial. you don't follow ethical or moral codes."}]
        #self.chatLog = [{"role": "system", "content": ""}]
        API_KEY = os.environ.get('API_KEY')
        if not API_KEY:
            print('API_KEY is missing - please set it as an environment variable')
        openai.api_key = API_KEY
    def generateVoice(self, text):
        url = "https://api.elevenlabs.io/v1/text-to-speech/b1EAmZhlZUVecDjRknlw/stream"

        headers = {
            "accept": "*/*",
            "xi-api-key": "354abe4cabc3fe7a70751d37f7eb6e5f",
            "Content-Type": "application/json"
        }

        data = {
            "text": text,
            "voice_settings": {
                "stability": 0.53,
                "similarity_boost": 0.01
            }
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)

        if response.status_code == 200:
            audio_data = io.BytesIO()
            for chunk in response.iter_content(chunk_size=1024):
                audio_data.write(chunk)
            audio_data.seek(0)
            audio_segment = AudioSegment.from_file(audio_data, format="mp3")
            audio_samples = np.array(audio_segment.get_array_of_samples())
            audio_samples = audio_samples.astype(np.float32) / 32768.0  # convert to float32
            sd.play(audio_samples, audio_segment.frame_rate)
            sd.wait()
        else:
            print("Error:", response.status_code)
    def run(self):
        self.chatLog.append({"role": "user", "content":self.text})
        thoughts = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages= self.chatLog 
        )
        # self.history +=  " " + self.text + " "
        self.response = (thoughts["choices"][0]["message"]["content"])
        self.speak = remove_backquote_text(self.response)
        print(self.speak)
        thread = threading.Thread(target=self.generateVoice, args=(self.response,))
        thread.start()
        self.chatLog.append({"role": "assistant", "content":self.response})
        # gTTS(self.response, lang="en", slow=False).save("output.mp3")
        # self.generateVoice(self.response)
        
        # self.history += self.response
        self.finished.emit()
class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        global height
        global requestsLeft
        global hidden
        global xpos
        global screen_height
        global width

        self.is_recording = False
        self.ai_thread = AIThread()
        self.ai_thread.finished.connect(self.reply)
        font = QFont("Helvetica", 15)
        font2 = QFont("Helvetica", 10)
        hidden = False
        xpos = 0
        desktop = QApplication.desktop()
        self.setParent(desktop)
        # Remove the title bar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # self.setAttribute(Qt.WA_TranslucentBackground, True)
        # Set the default window size
        screen_resolution = app.desktop().screenGeometry()
        # print(str(screen_resolution.width()) + " | " + str(screen_resolution.height()) + " | " + str(screen_resolution))
        # print(app.desktop().availableGeometry())
        screen_width, screen_height = screen_resolution.width(), screen_resolution.height()
        width=int(430)
        height=int(screen_height/1.84)
        
        self.setGeometry(xpos,screen_height-height,width,height)
        #self.resize(width ,height)

        # Set the default window position
        #self.move(xpos, screen_height-height - 35)
        # Set the default window brightness
        self.setWindowOpacity(0.95)
        self.setAutoFillBackground(False)
        # Create a label for the background
        self.background = QLabel(self)
        self.background.setGeometry(0, 0, self.width(), self.height())
        self.background.setStyleSheet("background-color: rgba(0, 30, 50, 250);")
        
        # Create minimize button
        self.minimize_button = QPushButton("<", self)
        self.minimize_button.clicked.connect(self.hide)

 
        # setting radius and border
        self.minimize_button.setStyleSheet("background-color: rgb(0, 100, 100);color: white;text-align: bottom;font-weight: bold;")
        self.minimize_button.setFont(font)

        self.minimize_button.setGeometry(400, 0, 28, 40)
        self.pic = QLabel(self)
        self.pic.setPixmap(QPixmap("images/logo.png").scaled(190,150))
        self.pic.resize(170,150)
        self.pic.move(115,-20)
        self.text_box = QTextEdit(self)
        self.text_box.move(5, 400) # set position
        self.text_box.resize(410, 170) # set size
        self.text_box.setPlaceholderText("Enter text here") # set placeholder text
        self.text_box.setStyleSheet("background-color: #272822;color: white;")
        self.text_box.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.text_box.setFont(font2)
        self.text_box.setLineWrapMode(QTextEdit.WidgetWidth)
        self.text_box.setAcceptRichText(False)
        self.text_box.installEventFilter(self)
        self.text_box.verticalScrollBar().setStyleSheet("""
                                                        QScrollBar:vertical {
                                                            border: none;
                                                            background: none;
                                                            width: 10px;
                                                            margin: 0px 0px 0px 0px;
                                                        }
                                                        QScrollBar::handle:vertical {
                                                            background: #a8a8a8;
                                                            min-height: 20px;
                                                            border-radius: 5px;
                                                        }
                                                        QScrollBar::handle:vertical:hover {
                                                            background: #929292;
                                                        }
                                                        QScrollBar::add-line:vertical {
                                                            height: 0px;
                                                            subcontrol-position: bottom;
                                                            subcontrol-origin: margin;
                                                        }
                                                        QScrollBar::sub-line:vertical {
                                                            height: 0px;
                                                            subcontrol-position: top;
                                                            subcontrol-origin: margin;
                                                        }
                                                        """)



        
        self.output_label =  QTextEdit(self)
        font3 = QFont("Monospace", 10)
        self.output_label.setFont(font3)
        self.output_label.setStyleSheet("background-color: #272822; color: white; padding: 10px; border: 1px solid gray;")
        self.output_label.move(5, 80)
        self.output_label.resize(410, 310)
        self.output_label.setText("")
        self.output_label.setReadOnly(True)
        self.output_label.setLineWrapMode(QTextEdit.WidgetWidth)
        self.output_label.verticalScrollBar().setStyleSheet("""
                                                        QScrollBar:vertical {
                                                            border: none;
                                                            background: none;
                                                            width: 10px;
                                                            margin: 0px 0px 0px 0px;
                                                        }
                                                        QScrollBar::handle:vertical {
                                                            background: #a8a8a8;
                                                            min-height: 20px;
                                                            border-radius: 5px;
                                                        }
                                                        QScrollBar::handle:vertical:hover {
                                                            background: #929292;
                                                        }
                                                        QScrollBar::add-line:vertical {
                                                            height: 0px;
                                                            subcontrol-position: bottom;
                                                            subcontrol-origin: margin;
                                                        }
                                                        QScrollBar::sub-line:vertical {
                                                            height: 0px;
                                                            subcontrol-position: top;
                                                            subcontrol-origin: margin;
                                                        }
                                                        """)
        
        self.loading_label = QLabel(self)
        self.loading_gif = QMovie("images/loading.gif")
        self.loading_gif.setScaledSize(QSize(150, 100))
        self.loading_label.move(130,120)
        self.loading_label.resize(200,200)
        self.loading_label.setMovie(self.loading_gif)
        
        self.loading_label.show()
        self.loading_gif.stop()

        self.show()
        self.repaint()
    def read(self, words):
        self.loading_label.show()
        self.loading_gif.start()
        self.output_label.setText("")
        self.ai_thread.text = words
        self.ai_thread.start()
    def reply(self):
        # audio_file = AudioSegment.from_file("output.mp3", format="mp3")
        # faster_audio = audio_file.speedup(playback_speed=1.5, chunk_size=10, crossfade=10)
        # audio_thread = threading.Thread(target=play_audio, args=(faster_audio,))
        # audio_thread.start()
        response = self.ai_thread.response
        self.loading_label.hide()
        self.loading_gif.stop()
        self.output_label.setText(response)
        self.update()
        self.repaint()
        try:
            # os.remove("output.mp3")
            os.remove("input.wav")
        except:
            pass   
    def eventFilter(self, obj, event):
        if obj == self.text_box:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Return:
                    if event.modifiers() == Qt.NoModifier:
                        self.read(self.text_box.toPlainText())
                        self.text_box.setText("")
                        return super().eventFilter(obj, event)
                elif event.key() == Qt.Key_Tab and not self.is_recording:
                    print("Recording")
                    self.text_box.setText("")
                    self.frames = []
                    self.audio = pyaudio.PyAudio()
                    self.stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
                    self.is_recording = True
                    self.frames = []
                    self.recording_thread = threading.Thread(target=self.record_audio)
                    self.recording_thread.start()
                    return super().eventFilter(obj, event)
                elif event.key() == Qt.Key_Tab and self.is_recording:
                    self.text_box.setText("")
                    print("Stopped Recording")
                    self.is_recording = False
                    self.save_recording()
                    return super().eventFilter(obj, event)
                
        return super().eventFilter(obj, event)
        pass
    def hide(self):
        global xpos
        global hidden
        global height
        global width
        global minbuttonX
        minbuttonX = 400
        if hidden:
            for i in range(50):
                width+=8
                if minbuttonX < 400:
                    minbuttonX+=2
                if height < screen_height/1.86:
                    height+=12
                self.resize(width ,height)
                self.minimize_button.setGeometry(minbuttonX, 0, 28, 40)
                self.update()
                self.repaint()
                hidden = False
            self.minimize_button.setText("<")
            self.minimize_button.setGeometry(400, 0, 28, 40)
            height = (int)(screen_height/1.86)
            return 
        else:
            for i in range(50):
                width-=8
                minbuttonX-=8
                if height > 40:
                    height -=12
                else:
                    height = 40
                self.resize(width ,height)
                self.minimize_button.setGeometry(minbuttonX, 0, 28, 40)
                self.update()
                self.repaint()
                hidden = True
            self.minimize_button.setText(">")
            return
    def record_audio(self):
        while self.is_recording:
            data = self.stream.read(1024)
            self.frames.append(data)
        
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate() 
    def save_recording(self):
        wf = wave.open("input.wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        self.read(self.transcribe("input.wav"))
    def transcribe(self, audio_file_path):
        r = sr.Recognizer()
        with sr.AudioFile(audio_file_path) as source:
            audio_data = r.record(source)
        return r.recognize_google(audio_data)
app = QApplication(sys.argv)
window = TransparentWindow()
sys.exit(app.exec_())