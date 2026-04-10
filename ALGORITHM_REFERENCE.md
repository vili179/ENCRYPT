# ENCRYPT: Algorithm and Encryption Reference

> **Version**: 3.0.0  
> **Architecture**: Dual-layer security (XOR encryption + LSB steganography)  
> **Last Updated**: April 2026

---

## 1. Executive Overview

ENCRYPT is a dual-layer steganography and encryption suite that conceals encrypted messages within digital images. The system employs two complementary security layers. The first layer uses XOR cipher encryption to transform plaintext into ciphertext, ensuring the message content is unreadable without the correct password. The second layer uses Least Significant Bit (LSB) steganography to embed the encrypted bits into the pixel channels of a carrier image, concealing the very existence of the message.

The core principle follows an **encrypt-then-embed** workflow for hiding and an **extract-then-decrypt** workflow for revealing. By encrypting before embedding, the system ensures that even if an adversary detects the presence of hidden data, the content remains protected by the encryption layer.

The application is implemented in TypeScript and runs on Node.js with Express.js for web delivery. Image processing is handled by the Sharp library, which provides high-performance access to raw pixel data across multiple image formats including PNG, JPEG, and HEIC/HEIF.

---

## 2. Encryption Layer: XOR Cipher

**Source**: `src/services/crypto.ts` (lines 1-13)

### 2.1 Algorithm Description

The encryption layer implements a symmetric XOR cipher with a custom key derivation step. The same function handles both encryption and decryption, since the XOR operation is its own inverse.

### 2.2 Key Derivation

The password string is converted to a single-byte encryption key through the following process:

1. Initialize an accumulator `keySum = 0`
2. For each character in the password, add its Unicode code point value to `keySum`
3. Reduce the sum to a single byte via `key = keySum % 256`

```typescript
// src/services/crypto.ts:2-6
let keySum = 0;
for (let i = 0; i < password.length; i++) {
  keySum += password.charCodeAt(i);
}
const key = keySum % 256;
```

This produces a key value in the range [0, 255]. The key derivation is deterministic: the same password always produces the same key.

### 2.3 Encryption and Decryption Operation

Each character of the input text is XOR-ed with the derived single-byte key:

```typescript
// src/services/crypto.ts:8-11
let result = "";
for (let i = 0; i < text.length; i++) {
  result += String.fromCharCode(text.charCodeAt(i) ^ key);
}
return result;
```

### 2.4 Mathematical Formalization

Let `P` denote the plaintext string, `C` the ciphertext, `pw` the password, and `K` the derived key.

**Key Derivation**:

```
K = ( Σ charCode(pw[i]) for i = 0..len(pw)-1 ) mod 256
```

**Encryption**:

```
C[i] = P[i] ⊕ K    for all i in [0, len(P))
```

**Decryption** (identical operation due to XOR involution):

```
P[i] = C[i] ⊕ K    for all i in [0, len(C))
```

**Proof of correctness**: XOR satisfies the involution property: `(A ⊕ K) ⊕ K = A` for any values `A` and `K`. This guarantees that encrypting and then decrypting with the same key recovers the original plaintext.

### 2.5 Key Derivation Examples

| Password | Char Codes | Sum | Key (mod 256) |
|----------|-----------|-----|---------------|
| `"abc"` | 97 + 98 + 99 | 294 | 38 |
| `"test"` | 116 + 101 + 115 + 116 | 448 | 192 |
| `"A"` | 65 | 65 | 65 |
| `"password123"` | 112+97+115+115+119+111+114+100+49+50+51 | 1033 | 9 |

### 2.6 XOR Encryption Example

For password `"abc"` (key = 38) and plaintext `"Hi"`:

```
'H' = 72  → 72 ⊕ 38 = 01001000 ⊕ 00100110 = 01101110 = 110 = 'n'
'i' = 105 → 105 ⊕ 38 = 01101001 ⊕ 00100110 = 01001111 = 79  = 'O'

Ciphertext: "nO"

Decryption: 'n' ⊕ 38 = 110 ⊕ 38 = 72 = 'H'  ✓
            'O' ⊕ 38 = 79 ⊕ 38 = 105 = 'i'  ✓
```

---

## 3. Steganography Layer: LSB Embedding

**Source**: `src/services/steganography.ts`

### 3.1 Concept

Least Significant Bit steganography exploits the fact that human vision cannot distinguish between pixel values that differ by only 1 unit (e.g., RGB(128, 64, 32) vs RGB(129, 64, 33)). By modifying only the least significant bit of each pixel channel byte, we embed one bit of secret data per channel with no perceptible visual change.

### 3.2 Hiding Process (Embedding)

**Function**: `hideMessage(imageBuffer, secretText, password)` (lines 6-49)

The embedding process follows these steps:

**Step 1: Encrypt the message** (line 11)

```typescript
const encrypted = xorCrypt(secretText, password);
```

The plaintext secret is encrypted using the XOR cipher, producing a ciphertext string of identical length.

**Step 2: Convert to bit array** (line 12)

```typescript
const messageBits = textToBits(encrypted);
```

Each character of the encrypted text is decomposed into 8 individual bits in MSB-first order. A 10-character message produces 80 bits.

**Step 3: Append null terminator** (line 14)

```typescript
const secretBits = new Uint8Array(messageBits.length + 8);
secretBits.set(messageBits);
```

A `Uint8Array` is allocated with 8 extra positions (initialized to 0 by default). This appends a null byte (00000000) to the end of the message bits, which serves as the end-of-message marker during extraction.

**Step 4: Decode carrier image** (lines 17-21)

```typescript
const { data: pixels, info } = await sharp(imageBuffer)
  .removeAlpha()
  .toColourspace("srgb")
  .raw()
  .toBuffer({ resolveWithObject: true });
```

The Sharp library processes the carrier image through three transformations:
- **Remove alpha**: strips the transparency channel to ensure consistent 3-channel (RGB) processing
- **Convert to sRGB**: normalizes the colorspace so pixel values are consistently interpreted
- **Raw buffer**: extracts the pixel data as a flat `Buffer` of unsigned bytes in R, G, B, R, G, B... order

**Step 5: Capacity check** (lines 23-29)

```typescript
const totalChannels = info.width * info.height * info.channels;
if (secretBits.length > totalChannels) {
  throw new Error(`Message too long for this image. Max capacity: ${Math.floor(totalChannels / 8)} characters.`);
}
```

Each pixel channel can carry one bit. If the total number of secret bits exceeds the total number of available channels, the image is too small.

**Step 6: LSB embedding** (lines 31-34)

```typescript
const modified = Buffer.from(pixels);
for (let i = 0; i < secretBits.length; i++) {
  modified[i] = (modified[i] & 0xfe) | secretBits[i];
}
```

This is the core embedding operation. For each bit of the secret:

1. `modified[i] & 0xFE` clears the least significant bit of the pixel channel byte. The bitmask `0xFE` is `11111110` in binary, preserving the upper 7 bits.
2. `| secretBits[i]` sets the LSB to the secret bit value (0 or 1).

**Worked example**: Embedding bit `1` into pixel channel value `200`:

```
200 in binary: 11001000
200 & 0xFE:    11001000  (LSB was already 0, unchanged)
               | 1:      11001001 = 201

The pixel channel changes from 200 to 201, an imperceptible difference.
```

**Step 7: Re-encode as PNG** (lines 36-40)

```typescript
const outputBuffer = await sharp(modified, {
  raw: { width: info.width, height: info.height, channels: 3 },
}).png().toBuffer();
```

The modified pixel data is encoded back into PNG format. PNG is critical because it uses lossless compression, preserving the exact LSB values. Using JPEG would apply lossy compression that destroys the embedded data.

**Step 8: Return result** (lines 42-48)

```typescript
return {
  buffer: outputBuffer,
  width: info.width,
  height: info.height,
  capacity: Math.floor(totalChannels / 8),
  bitsUsed: secretBits.length,
};
```

### 3.3 Revealing Process (Extraction)

**Function**: `revealMessage(imageBuffer, password)` (lines 51-96)

**Step 1: Decode stego image** (lines 55-59)

```typescript
const { data: pixels, info } = await sharp(imageBuffer)
  .removeAlpha()
  .toColourspace("srgb")
  .raw()
  .toBuffer({ resolveWithObject: true });
```

The same image processing pipeline is applied to ensure byte-level consistency with the embedding process.

**Step 2: Extract LSBs** (lines 61-65)

```typescript
const totalChannels = info.width * info.height * info.channels;
const bits = new Uint8Array(totalChannels);
for (let i = 0; i < totalChannels; i++) {
  bits[i] = pixels[i] & 1;
}
```

The operation `pixels[i] & 1` isolates the least significant bit of each pixel channel byte. The bitmask `1` is `00000001` in binary, extracting only the last bit.

**Step 3: Convert bits to text** (line 67)

```typescript
const encryptedText = bitsToText(bits);
```

Groups of 8 consecutive bits are reassembled into characters. The process stops when a null byte (all 8 bits are 0) is encountered.

**Step 4: Decrypt** (line 73)

```typescript
const decrypted = xorCrypt(encryptedText, password);
```

The extracted ciphertext is decrypted using the same XOR operation with the provided password.

**Step 5: Password validation** (lines 81-93)

```typescript
let printableCount = 0;
for (let i = 0; i < decrypted.length; i++) {
  const code = decrypted.charCodeAt(i);
  if ((code >= 32 && code <= 126) || code === 10 || code === 13 || code === 9) {
    printableCount++;
  }
}
if (printableCount / decrypted.length < 0.7) {
  throw new Error("Incorrect password. Please try again with the correct decryption key.");
}
```

This validation heuristic checks whether the decrypted output contains meaningful text. If fewer than 70% of characters fall within the printable ASCII range (32-126) or common whitespace characters (tab, line feed, carriage return), the system concludes the password is incorrect and reports an error.

---

## 4. Bit Conversion Utilities

**Source**: `src/utils/bits.ts` (lines 1-23)

### 4.1 Text to Bits (`textToBits`)

```typescript
// src/utils/bits.ts:1-10
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
```

Each character is decomposed into 8 bits in **MSB-first** (most significant bit first) order. The expression `(code >> (7 - b)) & 1` right-shifts the character code by `(7 - b)` positions and isolates the lowest bit.

**Worked example** for character `'A'` (code 65 = `01000001`):

| Bit index `b` | Shift `(7-b)` | `65 >> shift` | `& 1` | Result |
|---------------|---------------|---------------|-------|--------|
| 0 | 7 | `0` | 0 | **0** |
| 1 | 6 | `1` | 1 | **1** |
| 2 | 5 | `2` | 0 | **0** |
| 3 | 4 | `4` | 0 | **0** |
| 4 | 3 | `8` | 0 | **0** |
| 5 | 2 | `16` | 0 | **0** |
| 6 | 1 | `32` | 0 | **0** |
| 7 | 0 | `65` | 1 | **1** |

Output: `[0, 1, 0, 0, 0, 0, 0, 1]` which is the binary representation `01000001` = 65 = `'A'`.

### 4.2 Bits to Text (`bitsToText`)

```typescript
// src/utils/bits.ts:12-23
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
```

Groups of 8 consecutive bits are reassembled into characters. The expression `byte = (byte << 1) | bits[i + b]` left-shifts the accumulator by 1 and appends the next bit, building the byte from MSB to LSB.

The `if (byte === 0) break` statement provides the null-byte termination. When 8 consecutive zero bits are encountered, the function knows the message has ended and stops reading.

---

## 5. Image Processing Pipeline

**Source**: `src/services/steganography.ts` (Sharp operations at lines 17-21, 36-40, 55-59)

### 5.1 Pipeline Stages

The image processing pipeline applies three transformations in sequence:

```
Input Image → removeAlpha() → toColourspace("srgb") → raw() → Pixel Buffer
```

**Alpha channel removal** (`removeAlpha()`): Images with transparency (PNG with alpha, HEIC) have a 4th channel per pixel. By removing it, the system standardizes to exactly 3 channels (RGB), simplifying the embedding logic and preventing the alpha channel from interfering with visual appearance when modified.

**sRGB colorspace conversion** (`toColourspace("srgb")`): Different image formats may store colors in different colorspaces (e.g., Adobe RGB, Display P3). By normalizing to sRGB, the system ensures pixel values are interpreted consistently regardless of the source format.

**Raw buffer extraction** (`raw()`): Converts the decoded image into a flat byte array where bytes appear in sequential R, G, B, R, G, B... order. This provides direct, index-based access to individual pixel channels for LSB manipulation.

### 5.2 Output Format

The modified pixels are always encoded as **PNG** using `sharp().png().toBuffer()`. PNG uses lossless compression (DEFLATE algorithm), which preserves every bit of the pixel data exactly as written. This is essential because the secret message is encoded in the least significant bits, and any alteration to those bits would corrupt the message.

### 5.3 Input Format Support

The system accepts five input formats as defined in `src/utils/validation.ts`:

| Format | Compression | LSB Survival |
|--------|-------------|--------------|
| PNG | Lossless | Yes (ideal carrier) |
| JPEG/JPG | Lossy (DCT) | N/A (converted to PNG on output) |
| HEIC/HEIF | Lossy (HEVC) | N/A (converted to PNG on output) |

JPEG and HEIC images can be used as **input carriers** because Sharp decodes them to raw pixel data before embedding. However, the output is always PNG. If a user were to re-compress the stego image as JPEG after receiving it, the lossy compression would alter LSB values and destroy the hidden message.

### 5.4 Pixel Buffer Layout

For an image of dimensions W x H, the raw buffer contains:

```
Total bytes = W × H × 3
Layout: [R0, G0, B0, R1, G1, B1, R2, G2, B2, ..., R(n-1), G(n-1), B(n-1)]
```

Where pixel indices proceed left to right, top to bottom (row-major order). The embedding loop writes secret bits into bytes starting from index 0 (`R0`), proceeding sequentially through all channels.

---

## 6. Password Validation Mechanism

**Source**: `src/services/steganography.ts` (lines 81-93)

### 6.1 Validation Logic

After decryption, the system checks whether the output resembles meaningful text:

```typescript
let printableCount = 0;
for (let i = 0; i < decrypted.length; i++) {
  const code = decrypted.charCodeAt(i);
  if ((code >= 32 && code <= 126) || code === 10 || code === 13 || code === 9) {
    printableCount++;
  }
}
if (printableCount / decrypted.length < 0.7) {
  throw new Error("Incorrect password.");
}
```

### 6.2 Character Ranges

| Range | Characters | Description |
|-------|-----------|-------------|
| 32-126 | Space through `~` | Standard printable ASCII |
| 9 | `\t` | Horizontal tab |
| 10 | `\n` | Line feed |
| 13 | `\r` | Carriage return |

### 6.3 Rationale

When a wrong password is used, the XOR decryption produces a pseudorandom byte sequence. For uniformly distributed random bytes, the probability of any byte falling in the printable range is approximately `(126 - 32 + 1 + 3) / 256 = 98/256 ≈ 38.3%`. This falls well below the 70% threshold, causing the system to correctly identify the wrong password in most cases.

When the correct password is used, natural language text contains overwhelmingly printable characters (typically 95%+), passing the threshold easily.

### 6.4 Limitations

- **False negatives**: Messages containing a high proportion of non-ASCII characters (e.g., Unicode, binary data) may fail validation even with the correct password.
- **No cryptographic verification**: This is a heuristic, not a cryptographic integrity check (such as HMAC). It cannot guarantee correctness, only estimate it.

---

## 7. End-to-End Data Flow Diagrams

### 7.1 Hide Workflow (Encrypt and Embed)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HIDE WORKFLOW                                │
│                                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────┐               │
│  │ Password │───>│ Key Derive   │───>│ Key (0-255) │               │
│  │ "abc"    │    │ sum % 256    │    │ K = 38      │               │
│  └──────────┘    └──────────────┘    └──────┬──────┘               │
│                                             │                       │
│  ┌──────────┐    ┌──────────────┐    ┌──────▼──────┐               │
│  │ Secret   │───>│ XOR Encrypt  │<───│             │               │
│  │ "Hi"     │    │ P[i] ⊕ K    │    │             │               │
│  └──────────┘    └──────┬───────┘    └─────────────┘               │
│                         │                                           │
│                  ┌──────▼───────┐                                   │
│                  │ Ciphertext   │                                   │
│                  │ "nO"         │                                   │
│                  └──────┬───────┘                                   │
│                         │                                           │
│                  ┌──────▼───────┐                                   │
│                  │ textToBits   │                                   │
│                  │ char → 8bit  │                                   │
│                  └──────┬───────┘                                   │
│                         │                                           │
│                  ┌──────▼───────────────┐                           │
│                  │ Bit Array + Null Term │                           │
│                  │ [0,1,1,0,1,1,1,0,    │                           │
│                  │  0,1,0,0,1,1,1,1,    │                           │
│                  │  0,0,0,0,0,0,0,0]    │  ← 8 zero bits (null)   │
│                  └──────┬───────────────┘                           │
│                         │                                           │
│  ┌──────────┐    ┌──────▼───────┐    ┌─────────────┐               │
│  │ Carrier  │───>│ Sharp Decode │───>│ Raw Pixels  │               │
│  │ Image    │    │ removeAlpha  │    │ [R,G,B,...] │               │
│  │ (PNG/    │    │ sRGB, raw()  │    │             │               │
│  │  JPEG/   │    └──────────────┘    └──────┬──────┘               │
│  │  HEIC)   │                               │                      │
│  └──────────┘                        ┌──────▼──────┐               │
│                                      │ LSB Embed   │               │
│                                      │ (p & 0xFE)  │               │
│                                      │   | bit     │               │
│                                      └──────┬──────┘               │
│                                             │                       │
│                                      ┌──────▼──────┐               │
│                                      │ Sharp PNG   │               │
│                                      │ Encode      │               │
│                                      └──────┬──────┘               │
│                                             │                       │
│                                      ┌──────▼──────┐               │
│                                      │ Stego Image │               │
│                                      │ (PNG)       │               │
│                                      └─────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Extract Workflow (Extract and Decrypt)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      EXTRACT WORKFLOW                               │
│                                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────┐               │
│  │ Stego    │───>│ Sharp Decode │───>│ Raw Pixels  │               │
│  │ Image    │    │ removeAlpha  │    │ [R,G,B,...] │               │
│  │ (PNG)    │    │ sRGB, raw()  │    └──────┬──────┘               │
│  └──────────┘    └──────────────┘           │                       │
│                                      ┌──────▼──────┐               │
│                                      │ LSB Extract │               │
│                                      │ p[i] & 1    │               │
│                                      └──────┬──────┘               │
│                                             │                       │
│                                      ┌──────▼──────┐               │
│                                      │ Bit Array   │               │
│                                      │ [0,1,1,...] │               │
│                                      └──────┬──────┘               │
│                                             │                       │
│                                      ┌──────▼──────┐               │
│                                      │ bitsToText  │               │
│                                      │ 8bit → char │               │
│                                      │ stop @ null │               │
│                                      └──────┬──────┘               │
│                                             │                       │
│                                      ┌──────▼──────┐               │
│                                      │ Ciphertext  │               │
│                                      │ "nO"        │               │
│                                      └──────┬──────┘               │
│                                             │                       │
│  ┌──────────┐    ┌──────────────┐    ┌──────▼──────┐               │
│  │ Password │───>│ Key Derive   │───>│ XOR Decrypt │               │
│  │ "abc"    │    │ sum % 256    │    │ C[i] ⊕ K   │               │
│  └──────────┘    └──────┬───────┘    └──────┬──────┘               │
│                         │                   │                       │
│                  ┌──────▼───────┐    ┌──────▼──────┐               │
│                  │ K = 38       │    │ Plaintext   │               │
│                  └──────────────┘    │ "Hi"        │               │
│                                      └──────┬──────┘               │
│                                             │                       │
│                                      ┌──────▼──────┐               │
│                                      │ Validate    │               │
│                                      │ ≥70% print  │               │
│                                      │ able chars? │               │
│                                      └──────┬──────┘               │
│                                        ┌────┴────┐                  │
│                                     Yes│         │No                │
│                                 ┌──────▼──┐ ┌───▼────────┐         │
│                                 │ Return  │ │ Error:     │         │
│                                 │ message │ │ Wrong pwd  │         │
│                                 └─────────┘ └────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 File-Level Data Flow

```
src/routes/hide.ts          src/services/steganography.ts     src/services/crypto.ts
──────────────────          ─────────────────────────────     ─────────────────────
POST /hide                  hideMessage()                     xorCrypt()
  │                           │                                 │
  ├─ validate file            ├─ calls xorCrypt() ────────────>│ encrypt
  ├─ validate inputs          ├─ calls textToBits()             │
  ├─ calls hideMessage() ───>│  ├─ append null terminator      │
  │                           ├─ Sharp decode image             │
  │                           ├─ capacity check                 │
  │                           ├─ LSB embed loop                 │
  │                           ├─ Sharp PNG encode               │
  │<── StegoResult ──────────├─ return StegoResult             │
  ├─ send PNG attachment      │                                 │
  │                           │                                 │

src/routes/extract.ts       src/services/steganography.ts     src/services/crypto.ts
─────────────────────       ─────────────────────────────     ─────────────────────
POST /extract               revealMessage()                   xorCrypt()
  │                           │                                 │
  ├─ validate file            ├─ Sharp decode image             │
  ├─ validate password        ├─ LSB extract loop               │
  ├─ calls revealMessage() ─>│  ├─ calls bitsToText()          │
  │                           ├─ calls xorCrypt() ────────────>│ decrypt
  │                           ├─ validate printable chars       │
  │<── decrypted string ─────├─ return message                 │
  ├─ render result            │                                 │
```

---

## 8. Security Analysis

### 8.1 XOR Cipher Weaknesses

**Keyspace**: The derived key is a single byte, meaning there are only **256 possible keys**. An attacker can brute-force all keys in microseconds and check each result against the printable character heuristic.

**Key collisions**: Different passwords may produce the same key. For example, `"ab"` (97+98=195) and `"ba"` (98+97=195) produce identical keys. Any passwords whose character code sums are congruent modulo 256 are equivalent.

**Frequency analysis**: Since every plaintext character is XOR-ed with the same single-byte key, character frequency distributions are preserved in the ciphertext. An attacker familiar with the language of the plaintext can use frequency analysis to recover the key.

**Known-plaintext attack**: If an attacker knows any single character of the plaintext and its position, the key is immediately revealed: `K = P[i] ⊕ C[i]`.

### 8.2 LSB Steganography Detectability

**Chi-square analysis**: LSB embedding alters the statistical distribution of pixel values. In natural images, adjacent even-odd pixel pairs (e.g., 100 and 101) follow predictable frequency patterns. After LSB embedding, these pairs become more uniform, which chi-square tests can detect.

**RS analysis (Regular-Singular)**: This technique examines pixel groups and classifies them as "regular" or "singular" based on smoothness. In natural images, the ratio of regular to singular groups is stable. LSB embedding disrupts this ratio in a predictable way.

**Histogram anomalies**: Natural images have smooth, bell-curve-like histograms for pixel intensity. LSB embedding flattens pairs of adjacent histogram bins, creating detectable artifacts.

**Visual inspection**: While individual pixel changes are imperceptible, large embedded payloads (approaching capacity) may produce subtle patterns visible in difference images (subtracting the original from the stego image).

### 8.3 Missing Security Properties

| Property | Status | Impact |
|----------|--------|--------|
| Key stretching (PBKDF2, bcrypt, Argon2) | Absent | Brute-force is trivial |
| Salt | Absent | Same password always produces same key |
| Initialization vector (IV) | Absent | Same plaintext + password always produces same ciphertext |
| Message authentication (HMAC) | Absent | No way to verify message integrity |
| Authenticated encryption (AES-GCM) | Absent | No confidentiality or integrity guarantees |

### 8.4 Comparison to Industry Standards

| Feature | ENCRYPT (current) | Industry Standard |
|---------|-------------------|-------------------|
| Cipher | XOR (single byte) | AES-256 (256-bit key) |
| Key derivation | sum(charCodes) % 256 | PBKDF2, bcrypt, or Argon2 |
| Keyspace | 256 keys | 2^256 keys |
| Salt | None | Random per message |
| IV/Nonce | None | Random per encryption |
| Authentication | Heuristic (70% printable) | HMAC-SHA256 or GCM tag |
| Steganography | LSB (1 bit/channel) | Spread spectrum, DCT domain, or adaptive LSB |

### 8.5 Threat Model

The system provides protection against:
- **Casual observation**: the stego image looks identical to the original
- **Non-technical recipients**: without knowledge of the hidden data, there is nothing to find

The system does **not** protect against:
- **Targeted statistical analysis**: standard steganalysis tools can detect LSB embedding
- **Key recovery**: 256-key brute force is trivial
- **Active adversaries**: no integrity protection means an attacker could modify the hidden message

---

## 9. Technical Specifications

### 9.1 System Specifications

| Parameter | Value |
|-----------|-------|
| Steganography method | LSB (Least Significant Bit) |
| Encryption algorithm | XOR cipher with sum-mod-256 key derivation |
| Supported input formats | PNG, JPEG, JPG, HEIC, HEIF |
| Output format | PNG (lossless) |
| Max upload size | 10 MB |
| Pixel channels used | 3 (RGB, alpha removed) |
| Bits per channel | 1 (LSB only) |
| Bit ordering | MSB-first per character |
| Message terminator | Null byte (8 zero bits) |
| Password validation | 70% printable ASCII threshold |

### 9.2 Capacity Formula

```
capacity_bits    = width × height × 3
capacity_bytes   = floor(capacity_bits / 8)
capacity_chars   = capacity_bytes - 1    (subtract null terminator)
```

### 9.3 Capacity Examples

| Image Dimensions | Total Channels | Capacity (bytes) | Capacity (approx.) |
|-----------------|----------------|------------------|---------------------|
| 640 x 480 | 921,600 | 115,200 | ~112 KB |
| 1280 x 720 | 2,764,800 | 345,600 | ~337 KB |
| 1920 x 1080 | 6,220,800 | 777,600 | ~759 KB |
| 3840 x 2160 | 24,883,200 | 3,110,400 | ~2.96 MB |

### 9.4 Server Configuration

| Parameter | Value |
|-----------|-------|
| Runtime | Node.js >= 20 |
| Port | 9000 (configurable via `PORT` env var) |
| Compression | gzip (via `compression` middleware) |
| Security headers | Helmet with CSP |
| Static file cache | 1 year, immutable |
| File upload storage | Memory (not disk) |
