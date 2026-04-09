from flask import Flask, render_template, request, send_file
from PIL import Image
import pillow_heif
pillow_heif.register_heif_opener()
import numpy as np
import os
import uuid

print(">_ SYSTEM READY. AWAITING CARRIER...")

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'heic', 'heif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

app = Flask(__name__)

# Create uploads folder if it doesn't exist
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
        raise Exception(f"Message too long for this image. Max capacity: {(height * width * 3)//8} characters.")
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
    """
    Step 1: Extract binary data from image pixels
    Step 2: Convert binary back to text
    Step 3: Decrypt using password
    Step 4: Detect if password was wrong
    """

    # STEP 1: Open image and get pixel data
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

    encrypted_text = ''.join(chars)

    if len(encrypted_text) == 0:
        raise Exception("No hidden message found in this image")

    # Decrypt
    decrypted = xor_crypt(encrypted_text, password)

    # Validate password (detect gibberish)
    if len(decrypted) == 0:
        raise Exception("No hidden message found. The image may not contain a steganographic payload.")
    
    # Check if decrypted text looks like readable text
    printable_count = sum(1 for c in decrypted if 32 <= ord(c) <= 126 or c in '\n\r\t')
    printable_ratio = printable_count / len(decrypted) if len(decrypted) > 0 else 0
    
    # If less than 70% printable characters, likely wrong password
    if printable_ratio < 0.7:
        raise Exception("Incorrect password. Please try again with the correct decryption key.")
    
    return decrypted


# ========== WEB PAGES ==========

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

            if not image or not allowed_file(image.filename):
                return render_template('hide.html', error="Unsupported file type. Use PNG, JPG, JPEG, HEIC, HEIF.")
           
            if not image or not secret or not password:
                return render_template('hide.html', error="Please fill in all fields.")

            output_path = hide_encrypted(image, secret, password)
            return send_file(output_path, as_attachment=True,
                             download_name='hidden_image.png', mimetype='image/png')

        except Exception as e:
            return render_template('hide.html', error=str(e))

    return render_template('hide.html')


@app.route('/extract', methods=['GET', 'POST'])
def extract_page():
    if request.method == 'POST':
        try:
            image = request.files['image']
            password = request.form['password']

            if not image or not allowed_file(image.filename):
                return render_template('extract.html', error="Unsupported file type. Use PNG, JPG, JPEG, HEIC, HEIF.")
            if not password:
                return render_template('extract.html', error="Please enter the decryption password.")
            
            message = reveal_encrypted(image, password)
            return render_template('extract.html', result=message)

        except Exception as e:
            # Show error if something went wrong (including wrong password)
            error_msg = str(e)
            # Make sure password error is clear
            if "Incorrect password" in error_msg:
                return render_template('extract.html', error="❌ Incorrect password. Please try again with the correct key.")
            return render_template('extract.html', error=error_msg)

    return render_template('extract.html')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9000))  
    print(f">_ SERVER RUNNING AT: http://0.0.0.0:{port}")
    print(">_ NULL STATIC GATE ACTIVE")
    app.run(host="0.0.0.0", port=port)