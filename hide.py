from PIL import Image
import numpy as np


def xor_crypt(text: str, password: str) -> str:
    key = sum(ord(c) for c in password) % 256
    return ''.join(chr(ord(c) ^ key) for c in text)


def text_to_bits(text: str) -> str:
    return ''.join(format(ord(c), '08b') for c in text)


def hide_encrypted(image_path: str, secret_text: str, password: str, output_path: str) -> None:
    encrypted = xor_crypt(secret_text, password)
    secret_bits = text_to_bits(encrypted) + '00000000'

    img = Image.open(image_path).convert('RGB')
    pixels = np.array(img)
    height, width, _ = pixels.shape

    capacity = height * width * 3
    if len(secret_bits) > capacity:
        raise ValueError(
            f"Message too large: needs {len(secret_bits)} bits, "
            f"image capacity is {capacity} bits "
            f"({capacity // 8 - 1} chars max)."
        )

    idx = 0
    for i in range(height):
        for j in range(width):
            for k in range(3):
                if idx < len(secret_bits):
                    pixels[i][j][k] = (pixels[i][j][k] & 0xFE) | int(secret_bits[idx])
                    idx += 1

    Image.fromarray(pixels).save(output_path)
    print(f"Done — {len(secret_bits)} bits written.")
    print(f"Output: {output_path}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 5:
        print("Usage: python hide.py <input.png> <secret_message> <password> <output.png>")
        sys.exit(1)
    hide_encrypted(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
