from flask import Flask, render_template, request, send_file
from PIL import Image
import numpy as np
import os
import uuid

app = Flask(__name__)
os.makedirs('uploads', exist_ok=True)

def text_to_bits(text):
    result = ''
    for char in text:
        result += format(ord(char), '08b')
    return result

def xor_crypt(text, password):
    key = sum(ord(c) for c in password) % 256
    return ''.join(chr(ord(c) ^ key) for c in text)

def hide_encrypted(image_data, secret_text, password):
    encrypted = xor_crypt(secret_text, password)
    secret_bits = text_to_bits(encrypted) + '00000000'
    img = Image.open(image_data).convert('RGB')
    pixels = np.array(img)
    height, width, _ = pixels.shape
    if len(secret_bits) > height * width * 3:
        raise Exception(f"Message too long for this image.")
    idx = 0
    for i in range(height):
        for j in range(width):
            for k in range(3):
                if idx < len(secret_bits):
                    pixels[i][j][k] = (pixels[i][j][k] & 0xFE) | int(secret_bits[idx])
                    idx += 1
    output_path = os.path.join('uploads', f"stego_{uuid.uuid4().hex}.png")
    Image.fromarray(pixels).save(output_path)
    return output_path

def reveal_encrypted(image_data, password):
    img = Image.open(image_data).convert('RGB')
    pixels = np.array(img)
    height, width, _ = pixels.shape
    bits = ''
    for i in range(height):
        for j in range(width):
            for k in range(3):
                bits += str(pixels[i][j][k] & 1)
    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) == 8:
            if byte == '00000000':
                break
            chars.append(chr(int(byte, 2)))
    return xor_crypt(''.join(chars), password)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hide', methods=['GET', 'POST'])
def hide_page():
    if request.method == 'POST':
        try:
            image = request.files['image']
            secret = request.form['secret']
            password = request.form['password']
            if not image or not secret or not password:
                return render_template('hide.html', error="Please fill in all fields.")
            output_path = hide_encrypted(image, secret, password)
            return send_file(output_path, as_attachment=True, download_name='hidden_image.png', mimetype='image/png')
        except Exception as e:
            return render_template('hide.html', error=str(e))
    return render_template('hide.html')

@app.route('/extract', methods=['GET', 'POST'])
def extract_page():
    if request.method == 'POST':
        try:
            image = request.files['image']
            password = request.form['password']
            if not image or not password:
                return render_template('extract.html', error="Please fill in all fields.")
            message = reveal_encrypted(image, password)
            return render_template('extract.html', result=message)
        except Exception as e:
            return render_template('extract.html', error=str(e))
    return render_template('extract.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
