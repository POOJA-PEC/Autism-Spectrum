from flask import Flask, render_template, request, jsonify,redirect
from flask_cors import CORS  # Import CORS
import sys
import os
import glob
import re
import numpy as np
from keras.applications.imagenet_utils import preprocess_input, decode_predictions
from keras.models import load_model
from keras.preprocessing import image
from tensorflow.keras.models import Model, load_model
import numpy as np
import cv2
import os
from glob import glob
from PIL import Image 
from skimage import transform
from flask import Flask, redirect, url_for, request, render_template, jsonify
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer
import sqlite3
from datetime import datetime
import base64
import smtplib
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
from email.utils import formataddr
app = Flask(__name__)
CORS(app)  
final_score = 0
MODEL_VGG16_PATH = 'model_vgg16.h5'
MODEL_VGG16 = load_model(MODEL_VGG16_PATH)
MODEL_VGG16.make_predict_function()




def load(filename):
   np_image = Image.open(filename)
   np_image = np.array(np_image).astype('float32')/255
   np_image = transform.resize(np_image, (224, 224, 3))
   np_image = np.expand_dims(np_image, axis=0)
   return np_image

def model_predict(img_path, model):
    image = load(img_path)
    preds = model.predict(image,batch_size=32)
    return preds






database = "database1.db"
conn = sqlite3.connect(database)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS register (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT, user_id TEXT, age int,password TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS score (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, score TEXT,result text
    )
''')
conn.commit()

@app.route('/')
def index():
    return render_template('register.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user_name = request.form['user_name']   
        user_id = request.form['user_id']
        age = request.form['age']
        password = request.form['password']
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO register (user_name, user_id,age, password) VALUES (?, ?, ?,?)",
                       (user_name, user_id,age, password))
        conn.commit()
        return render_template('register.html')

    return render_template('register.html')

u=[]
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        user_id = request.form['user_id']
        u.append(user_id)
        password = request.form['password']
        cursor.execute("SELECT * FROM register WHERE user_id=? AND password=?", (user_id, password))
        user = cursor.fetchone()
        if user:
            if user[3]<10:
                return render_template('game5.html')
            else:
                return render_template('form.html')
        else:
            return "password mismatch"
    return render_template('register.html')


@app.route('/admin', methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        user_id = request.form['user_id']
        password = request.form['password']
        if user_id=="admin" and password=="admin":
            conn = sqlite3.connect(database)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM score")
            data=cursor.fetchall()
            return render_template("admin.html",data=data)
                
        else:
            return "password mismatch"


score=[]
new1=[]
@app.route('/submit-score', methods=['POST'])
def submit_score():
    global final_score
    if request.method == 'POST':
        data = request.json
        final_score = data['finalScore']
        user_id=u[-1]
        score.append(final_score)
        return "finish"
    

@app.route('/submit', methods=['POST'])
def submit():
    user_id=u[-1]
    data = request.form.to_dict()
    converted_data = {key: 0 if value == 'a' else 1 for key, value in data.items()}
    total_marks = sum(converted_data.values())
    score.append(total_marks)
    return "finish"




@app.route('/new')
def new():
        s=score[-1]
        new1.append(s)
        return render_template('upload_chest.html')


@app.route('/uploaded_chest', methods=['POST', 'GET'])
def uploaded_chest():
    if request.method == 'POST':
        f = request.files['file']
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(basepath, "static/upload_img.png")
        f.save(file_path)
        lst = ["Affected","Not affected"]
        preds_VGG16 = model_predict(file_path, MODEL_VGG16)
        pred_class_VGG16 = np.argmax(preds_VGG16)            
        result_VGG16 = str(lst[pred_class_VGG16])
        user_id=u[-1]
        score=new1[-1]
        if score<5:
           result="Affected"
        else:
              result="Not Affected"
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO score (user_id, score,result) VALUES (?,?,?)",
                       (user_id, score,result))
        conn.commit()
        return render_template('result.html',score=score,result=result)


    

if __name__ == '__main__':
    app.run(debug=False, port=800)
