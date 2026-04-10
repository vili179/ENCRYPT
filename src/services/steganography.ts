import sharp from "sharp";
import { xorCrypt } from "./crypto.js";
import { textToBits, bitsToText } from "../utils/bits.js";
import type { StegoResult } from "../types.js";

export async function hideMessage(
  imageBuffer: Buffer,
  secretText: string,
  password: string
): Promise<StegoResult> {
  const encrypted = xorCrypt(secretText, password);
  const messageBits = textToBits(encrypted);

  const secretBits = new Uint8Array(messageBits.length + 8);
  secretBits.set(messageBits);

  const { data: pixels, info } = await sharp(imageBuffer)
    .removeAlpha()
    .toColourspace("srgb")
    .raw()
    .toBuffer({ resolveWithObject: true });

  const totalChannels = info.width * info.height * info.channels;

  if (secretBits.length > totalChannels) {
    throw new Error(
      `Message too long for this image. Max capacity: ${Math.floor(totalChannels / 8)} characters.`
    );
  }

  const modified = Buffer.from(pixels);
  for (let i = 0; i < secretBits.length; i++) {
    modified[i] = (modified[i] & 0xfe) | secretBits[i];
  }

  const outputBuffer = await sharp(modified, {
    raw: { width: info.width, height: info.height, channels: 3 },
  })
    .png()
    .toBuffer();

  return {
    buffer: outputBuffer,
    width: info.width,
    height: info.height,
    capacity: Math.floor(totalChannels / 8),
    bitsUsed: secretBits.length,
  };
}

export async function revealMessage(
  imageBuffer: Buffer,
  password: string
): Promise<string> {
  const { data: pixels, info } = await sharp(imageBuffer)
    .removeAlpha()
    .toColourspace("srgb")
    .raw()
    .toBuffer({ resolveWithObject: true });

  const totalChannels = info.width * info.height * info.channels;
  const bits = new Uint8Array(totalChannels);
  for (let i = 0; i < totalChannels; i++) {
    bits[i] = pixels[i] & 1;
  }

  const encryptedText = bitsToText(bits);

  if (encryptedText.length === 0) {
    throw new Error("No hidden message found in this image");
  }

  const decrypted = xorCrypt(encryptedText, password);

  if (decrypted.length === 0) {
    throw new Error(
      "No hidden message found. The image may not contain a steganographic payload."
    );
  }

  let printableCount = 0;
  for (let i = 0; i < decrypted.length; i++) {
    const code = decrypted.charCodeAt(i);
    if ((code >= 32 && code <= 126) || code === 10 || code === 13 || code === 9) {
      printableCount++;
    }
  }

  if (printableCount / decrypted.length < 0.7) {
    throw new Error(
      "Incorrect password. Please try again with the correct decryption key."
    );
  }

  return decrypted;
}
