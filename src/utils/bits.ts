export function textToBits(text: string): Uint8Array {
  const bits = new Uint8Array(text.length * 8);
  for (let i = 0; i < text.length; i++) {
    const code = text.charCodeAt(i);
    for (let b = 0; b < 8; b++) {
      bits[i * 8 + b] = (code >> (7 - b)) & 1;
    }
  }
  return bits;
}

export function bitsToText(bits: Uint8Array): string {
  const chars: string[] = [];
  for (let i = 0; i + 7 < bits.length; i += 8) {
    let byte = 0;
    for (let b = 0; b < 8; b++) {
      byte = (byte << 1) | bits[i + b];
    }
    if (byte === 0) break;
    chars.push(String.fromCharCode(byte));
  }
  return chars.join("");
}
