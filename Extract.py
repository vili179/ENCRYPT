from PIL import Image
import numpy as np


def xor_crypt(text: str, password: str) -> str:
    key = sum(ord(c) for c in password) % 256
    return ''.join(chr(ord(c) ^ key) for c in text)


def reveal_encrypted(image_path: str, password: str) -> str:
    img = Image.open(image_path).convert('RGB')
    pixels = np.array(img)
    height, width, _ = pixels.shape

    bits = ''
    for i in range(height):
        for j in range(width):
            for k in range(3):
                bits += str(pixels[i][j][k] & 1)
    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]
        if len(byte) < 8:
            break
        if byte == '00000000':
            break
        chars.append(chr(int(byte, 2)))

    encrypted_text = ''.join(chars)
    return xor_crypt(encrypted_text, password)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: python Extract.py <image.png> <password>")
        sys.exit(1)
    result = reveal_encrypted(sys.argv[1], sys.argv[2])
    print(f"Secret Message: {result}")
