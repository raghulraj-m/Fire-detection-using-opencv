from flask import Flask, render_template, request, redirect, url_for, Response
import cv2
import threading
import pygame
import numpy as np
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

Alarm_Status = False
Fire_Reported = False

# Email configuration
sender_email = "raghulraj17042003@gmail.com"
receiver_email = "raghulraj17042003@gmail.com"
subject = "FIRE ALERT!..."
body = "IT'S GOT FIRE ON YOUR LOCATION!..."

# SMTP server configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587  # Use 465 for SSL/TLS

# Your email credentials
username = "raghulraj17042003@gmail.com"
password = "ftav rhwv kmpp kgiv"

# Create message
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject
message.attach(MIMEText(body, "plain"))

pygame.mixer.init()

# Connect to the SMTP server
def mail():
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        # Start TLS for security (if required)
        server.starttls()

        # Login to your email account
        server.login(username, password)

        # Send email
        server.sendmail(sender_email, receiver_email, message.as_string())

def play_alarm_sound_function():
    pygame.mixer.music.load('emergency-alarm-with-reverb-29431.mp3')
    pygame.mixer.music.play()
    mail()

cooldown_duration = 10  # Set the cooldown duration in seconds
cooldown_start_time = 0

def perform_fire_detection(camera):
    global Alarm_Status
    global Fire_Reported
    global cooldown_start_time

    while True:
        grabbed, frame = camera.read()
        if not grabbed:
            break

        frame = cv2.resize(frame, (960, 540))

        blur = cv2.GaussianBlur(frame, (21, 21), 0)
        hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

        lower = [18, 50, 50]
        upper = [35, 255, 255]
        lower = np.array(lower, dtype="uint8")
        upper = np.array(upper, dtype="uint8")

        mask = cv2.inRange(hsv, lower, upper)

        no_red = cv2.countNonZero(mask)

        if int(no_red) > 15000:
            Fire_Reported = True
        else:
            Fire_Reported = False

        if Fire_Reported and not Alarm_Status and time.time() - cooldown_start_time > cooldown_duration:
            threading.Thread(target=play_alarm_sound_function).start()
            Alarm_Status = True
            cooldown_start_time = time.time()  # Update cooldown start time

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        return redirect(url_for('process_video', video_file=filename))

@app.route('/process/<video_file>')
def process_video(video_file):
    global Alarm_Status
    Alarm_Status = False
    return render_template('video.html', video_file=video_file)

@app.route('/video_feed/<video_source>')
def video_feed(video_source):
    if video_source == 'webcam':
        camera = cv2.VideoCapture(0)  # 0 corresponds to the default webcam
    else:
        camera = cv2.VideoCapture(video_source)

    return Response(perform_fire_detection(camera), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
