from PIL import Image
import numpy as np

def xor_crypt(text, password):
    key = sum(ord(c) for c in password) % 256
    result = ''.join(chr(ord(c) ^ key) for c in text)
    return result

def reveal_encrypted(image_path, password):
    # 读取图片
    img = Image.open(image_path).convert('RGB')
    pixels = np.array(img)
    height, width, _ = pixels.shape
    
    # 提取所有最低有效位
    bits = ''
    for i in range(height):
        for j in range(width):
            for k in range(3):
                bits += str(pixels[i][j][k] & 1)
    
    # 找到结束标志
    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) == 8:
            if byte == '00000000':
                break
            chars.append(chr(int(byte, 2)))
    
    encrypted_text = ''.join(chars)
    
    # 解密
    decrypted = xor_crypt(encrypted_text, password)
    return decrypted

# 使用示例
result = reveal_encrypted("secret_photo.png", "hello123")
print(f"Secret Message: {result}")
