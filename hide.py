from PIL import Image
import numpy as np

def text_to_bits(text):
    result = ''
    for char in text:
        bits = format(ord(char), '08b')
        result += bits
    return result

def xor_crypt(text, password):
    key = sum(ord(c) for c in password) % 256
    result = ''.join(chr(ord(c) ^ key) for c in text)
    return result

def hide_encrypted(image_path, secret_text, password, output_path):
    # 加密
    encrypted = xor_crypt(secret_text, password)
    
    # 转二进制
    secret_bits = text_to_bits(encrypted)
    secret_bits += '00000000'
    
    # 嵌入图片
    img = Image.open(image_path).convert('RGB')
    pixels = np.array(img)
    height, width, _ = pixels.shape
    
    idx = 0
    for i in range(height):
        for j in range(width):
            for k in range(3):
                if idx < len(secret_bits):
                    pixels[i][j][k] = (pixels[i][j][k] & 0xFE) | int(secret_bits[idx])
                    idx += 1
    
    Image.fromarray(pixels).save(output_path)
    print(f"✅ 嵌入完成！共 {len(secret_bits)} 位")
    print(f"✅ 输出: {output_path}")

# 使用示例
hide_encrypted("sg-bunnies.jpg", "I actually like sanrio better...", "hello123", "secret_photo.png")
