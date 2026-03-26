from flask import Flask, render_template, request, send_file
from PIL import Image
import numpy as np
import os
import uuid

# Create Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# Create uploads folder if it doesn't exist
os.makedirs('uploads', exist_ok=True)

# ========== HELPER FUNCTIONS ==========

def text_to_bits(text):
    """Convert text to binary (8 bits per character)"""
    result = ''
    for char in text:
        bits = format(ord(char), '08b')
        result += bits
    return result

def xor_crypt(text, password):
    """XOR encryption/decryption using password"""
    # Calculate key from password
    key = sum(ord(c) for c in password) % 256
    # XOR each character
    result = ''.join(chr(ord(c) ^ key) for c in text)
    return result

def hide_encrypted(image_data, secret_text, password):
    """
    Step 1: Encrypt the message with password
    Step 2: Convert encrypted message to binary
    Step 3: Hide binary data in image pixels (LSB method)
    """
    
    # STEP 1: Encrypt the secret message
    encrypted = xor_crypt(secret_text, password)
    
    # STEP 2: Convert encrypted text to binary
    secret_bits = text_to_bits(encrypted)
    # Add 8 zeros as "end marker" so we know when to stop reading
    secret_bits += '00000000'
    
    # STEP 3: Open the image and get pixel data
    img = Image.open(image_data).convert('RGB')
    pixels = np.array(img)
    height, width, _ = pixels.shape
    
    # Check if image is big enough
    max_capacity = height * width * 3
    if len(secret_bits) > max_capacity:
        raise Exception(f"Message too long! Image can only hold {max_capacity} bits")
    
    # STEP 4: Hide data in Least Significant Bits (LSB)
    idx = 0
    for i in range(height):
        for j in range(width):
            for k in range(3):  # R, G, B channels
                if idx < len(secret_bits):
                    # Clear the last bit (set to 0) then OR with secret bit
                    pixels[i][j][k] = (pixels[i][j][k] & 0xFE) | int(secret_bits[idx])
                    idx += 1
    
    # STEP 5: Save the modified image
    output_filename = f"stego_{uuid.uuid4().hex}.png"
    output_path = os.path.join('uploads', output_filename)
    Image.fromarray(pixels).save(output_path)
    
    return output_path

def reveal_encrypted(image_data, password):
    """
    Step 1: Extract binary data from image pixels
    Step 2: Convert binary back to text
    Step 3: Decrypt using password
    """
    
    # STEP 1: Open image and get pixel data
    img = Image.open(image_data).convert('RGB')
    pixels = np.array(img)
    height, width, _ = pixels.shape
    
    # STEP 2: Extract all Least Significant Bits
    bits = ''
    for i in range(height):
        for j in range(width):
            for k in range(3):
                # Get the last bit (LSB) of each pixel channel
                bits += str(pixels[i][j][k] & 1)
    
    # STEP 3: Group bits into bytes (8 bits each)
    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) == 8:
            # Stop when we find the end marker (8 zeros)
            if byte == '00000000':
                break
            # Convert binary byte to character
            chars.append(chr(int(byte, 2)))
    
    encrypted_text = ''.join(chars)
    
    # STEP 4: Decrypt using password
    decrypted = xor_crypt(encrypted_text, password)
    
    return decrypted

# ========== WEB PAGES ==========

@app.route('/')
def index():
    """Homepage - shows both options"""
    return render_template('index.html')

@app.route('/hide', methods=['GET', 'POST'])
def hide_page():
    """
    Hide Page:
    - GET: Show the form
    - POST: Process the form (hide message and return image)
    """
    
    if request.method == 'POST':
        try:
            # Get data from the form
            image = request.files['image']      # The uploaded image
            secret = request.form['secret']     # The secret message
            password = request.form['password'] # The password
            
            # Check if all fields are filled
            if not image or not secret or not password:
                return render_template('hide.html', error="Please fill in all fields")
            
            # Hide the message in the image
            output_path = hide_encrypted(image, secret, password)
            
            # Send the image back to user for download
            return send_file(
                output_path,
                as_attachment=True,
                download_name='hidden_image.png',
                mimetype='image/png'
            )
        
        except Exception as e:
            # Show error if something went wrong
            return render_template('hide.html', error=str(e))
    
    # GET request: just show the form
    return render_template('hide.html')

@app.route('/extract', methods=['GET', 'POST'])
def extract_page():
    """
    Extract Page:
    - GET: Show the form
    - POST: Process the form (extract and reveal message)
    """
    
    if request.method == 'POST':
        try:
            # Get data from the form
            image = request.files['image']      # The hidden image
            password = request.form['password'] # The password
            
            # Check if all fields are filled
            if not image or not password:
                return render_template('extract.html', error="Please fill in all fields")
            
            # Extract and decrypt the message
            message = reveal_encrypted(image, password)
            
            # Show the result
            return render_template('extract.html', result=message)
        
        except Exception as e:
            # Show error if something went wrong
            return render_template('extract.html', error=str(e))
    
    # GET request: just show the form
    return render_template('extract.html')

# ========== RUN THE APP ==========

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)