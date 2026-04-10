# Post-Quantum Key Exchange Feasibility Study for ENCRYPT

> **Scope**: Evaluating the feasibility of integrating ML-KEM (FIPS 203) into the ENCRYPT Steganography Suite for Render.com deployment with mobile phone compatibility  
> **Last Updated**: April 2026

---

## 1. Executive Summary

**Verdict: Fully feasible.** Pure TypeScript ML-KEM implementations exist with zero native dependencies, run in both Node.js and mobile browsers, produce a bundle overhead of only 16 KB gzipped, and deliver thousands of key exchange operations per second on modern hardware. The ENCRYPT project can integrate post-quantum key exchange without changing its deployment platform (Render.com) or sacrificing mobile compatibility.

---

## 2. Post-Quantum Key Exchange Methods Compared

### 2.1 The NIST-Standardized Landscape

NIST has standardized one KEM algorithm (ML-KEM, FIPS 203) and selected one backup (HQC), while other candidates were considered during the standardization process. We compare the four most relevant algorithms below.

| Algorithm | Math Foundation | NIST Status | Public Key | Ciphertext | Shared Secret |
|-----------|----------------|-------------|-----------|------------|---------------|
| **ML-KEM-512** | Module lattices (MLWE) | FIPS 203 (standardized) | 800 B | 768 B | 32 B |
| **ML-KEM-768** | Module lattices (MLWE) | FIPS 203 (standardized) | 1,184 B | 1,088 B | 32 B |
| **ML-KEM-1024** | Module lattices (MLWE) | FIPS 203 (standardized) | 1,568 B | 1,568 B | 32 B |
| **HQC-128** | Error-correcting codes | Selected (draft ~2027) | ~2,249 B | ~4,481 B | 32 B |
| **HQC-192** | Error-correcting codes | Selected (draft ~2027) | ~4,522 B | ~9,026 B | 32 B |
| **HQC-256** | Error-correcting codes | Selected (draft ~2027) | ~7,245 B | ~14,469 B | 32 B |
| **FrodoKEM-976** | Unstructured lattices (LWE) | Not selected | 15,632 B | 15,744 B | 32 B |
| **NTRU-HRSS** | NTRU lattices | Not selected | 1,230 B | 1,230 B | 32 B |

### 2.2 ML-KEM Is the Clear Winner

ML-KEM outperforms all alternatives on every practical metric. NIST expects ML-KEM to provide the foundation for most deployments of post-quantum cryptography [1].

**ML-KEM vs. HQC**: HQC performs significantly worse than ML-KEM on every metric. HQC-128 requires approximately 7 KB on the wire, nearly double the 3 KB required for ML-KEM-1024 (the highest ML-KEM security level). The gap widens at higher security levels: HQC-256 requires 21 KB of combined key and ciphertext, compared to ML-KEM-1024's approximately 3.1 KB. CPU performance follows a similar pattern, with HQC scaling worse with security level [2].

**ML-KEM vs. FrodoKEM**: FrodoKEM uses unstructured lattices, which provide a more conservative security assumption but at the cost of dramatically larger key sizes (15+ KB). NIST concluded that FrodoKEM has generally worse performance than the structured lattice alternatives and did not select it for standardization [3].

**ML-KEM vs. NTRU**: NTRU-HRSS has comparable key sizes to ML-KEM but is computationally more expensive on the client side. NTRU was also not selected by NIST for the final standard [3].

### 2.3 Recommended Parameter Set for ENCRYPT

**ML-KEM-768** provides the optimal balance for ENCRYPT's use case:

| Property | ML-KEM-768 Value |
|----------|-----------------|
| Security level | NIST Level 3 (~AES-192 equivalent) |
| Public key | 1,184 bytes |
| Secret key | 2,400 bytes |
| Ciphertext | 1,088 bytes |
| Shared secret | 32 bytes (256 bits) |
| Combined wire size | ~2,272 bytes |

The 32-byte shared secret can directly serve as an AES-256 key, eliminating the need for a separate key derivation step (though adding KDF is still recommended for defense in depth). The combined wire size of approximately 2.2 KB is negligible compared to the image files ENCRYPT already processes (10 MB maximum).

---

## 3. Available JavaScript/TypeScript Implementations

### 3.1 Library Comparison

| Library | Type | Dependencies | Environments | FIPS 203 | Audit Status |
|---------|------|-------------|-------------|----------|-------------|
| **`mlkem`** (dajiaji) | Pure TypeScript | Zero | Node.js, Browser, Deno, Cloudflare Workers, Bun | Yes | NIST test vectors passed |
| **`@noble/post-quantum`** (paulmillr) | Pure JavaScript | 2 (noble-hashes, noble-curves) | Node.js, Browser, React Native | Yes | Self-audited (v0.6.0) |
| **`@openpgp/crystals-kyber-js`** | Pure TypeScript | Zero | Node.js, Browser | Yes (draft) | Used in OpenPGP.js |
| **`pqc-crypto`** (QUXTech) | Pure TypeScript | Minimal | Node.js, Browser | Yes | Community |
| **`liboqs-node`** (TapuCosmo) | Native C (N-API) | liboqs C library | Node.js only | Yes | OQS project |
| **`@openforge-sh/liboqs`** | WebAssembly | liboqs WASM | Node.js, Browser | Yes | OQS project |

### 3.2 Recommended Library: `mlkem`

The `mlkem` package (npm: `mlkem`, JSR: `@dajiaji/mlkem`) is the strongest candidate for ENCRYPT:

- **Pure TypeScript**: zero native dependencies, no C compilation, no WebAssembly, no platform restrictions
- **FIPS 203 compliant**: implements the final ML-KEM standard (not the draft Kyber variant)
- **Multi-platform**: tested on Node.js, Deno, Cloudflare Workers, Bun, and all major browsers
- **Performance**: approximately 5x faster than the original reference implementation [4]
- **Test coverage**: passed all NIST KAT (Known Answer Test) vectors and C2SP/CCTV test suites [4]
- **Zero dependencies**: no supply chain risk from transitive packages

**Installation**:
```bash
npm install mlkem
```

**Usage** (from the library documentation):
```typescript
import { MlKem768 } from "mlkem";

const recipient = new MlKem768();
const [publicKey, secretKey] = await recipient.generateKeyPair();

const sender = new MlKem768();
const [ciphertext, sharedSecretSender] = await sender.encap(publicKey);

const sharedSecretRecipient = await recipient.decap(ciphertext, secretKey);
// sharedSecretSender === sharedSecretRecipient (32 bytes)
```

### 3.3 Alternative: `@noble/post-quantum`

If a broader PQC toolkit is needed (signatures via ML-DSA, hash-based signatures via SLH-DSA), `@noble/post-quantum` provides all NIST PQC algorithms in a single 16 KB gzipped bundle [5]:

- **Bundle size**: 16 KB gzipped for the entire library (ML-KEM + ML-DSA + SLH-DSA)
- **Performance**: ML-KEM-768 at approximately 3,750 ops/sec on Apple M4 [5]
- **React Native support**: confirmed with `getRandomValues` polyfill [5]
- **Dependencies**: only `@noble/hashes` and `@noble/curves` (both well-audited)
- **Audit**: self-audited as of v0.6.0 (March 2026); not yet independently audited [5]

### 3.4 Why NOT liboqs-node

The `liboqs-node` package provides Node.js bindings to the Open Quantum Safe C library. While this offers the most thoroughly audited implementation, it has critical drawbacks for ENCRYPT's use case:

- **Native C compilation**: requires a C compiler and liboqs build on the deployment platform
- **No browser support**: cannot run on mobile phones accessing the web interface
- **Render.com complexity**: native modules require Linux-compatible binaries, complicating deployment
- **Experimental status**: the liboqs project itself notes that its algorithms "should not be used in production" [6]

---

## 4. Render.com Deployment Feasibility

### 4.1 Pure TypeScript Advantage

Because `mlkem` and `@noble/post-quantum` are pure TypeScript/JavaScript with zero native dependencies, they deploy on Render.com identically to any other npm package. No changes to `render.yaml`, no additional build steps, no native compilation.

ENCRYPT's current `render.yaml`:
```yaml
services:
  - type: web
    name: encrypt-app
    runtime: node
    buildCommand: npm install && npm run build
    startCommand: node dist/index.js
    envVars:
      - key: NODE_VERSION
        value: 20
```

This configuration works without modification. The `npm install` step installs the pure TypeScript ML-KEM package alongside existing dependencies (Express, Sharp, etc.). No additional system libraries or build tools are needed.

### 4.2 Render Free Tier Constraints

| Constraint | Value | Impact on ML-KEM |
|-----------|-------|-----------------|
| Instance hours | 750/month | No additional impact (ML-KEM adds microseconds per request) |
| Outbound bandwidth | 100 GB/month | Negligible (ML-KEM adds ~2.2 KB per key exchange) |
| Memory | 512 MB (free tier) | ML-KEM requires as little as 4 KB per operation [7] |
| Sleep after inactivity | 15 minutes | No impact (ML-KEM has no persistent state) |
| CPU | Shared | ML-KEM keygen runs at thousands of ops/sec even on shared CPU |

### 4.3 Performance Budget

The current ENCRYPT workflow processes images up to 10 MB through Sharp (decode, raw pixel extraction, LSB manipulation, PNG encode). This image processing dominates request latency. Adding ML-KEM key exchange adds less than 1 millisecond to the total request time, which is negligible compared to the image processing overhead.

---

## 5. Mobile Phone Feasibility

### 5.1 Browser-Based ML-KEM

The ENCRYPT web interface runs in mobile browsers. Since `mlkem` is pure TypeScript that compiles to standard JavaScript, it executes directly in mobile browser JavaScript engines without any special platform support.

**Confirmed mobile browser compatibility**:
- Chrome for Android (JavaScript engine: V8)
- Safari for iOS (JavaScript engine: JavaScriptCore)
- Firefox for Android (JavaScript engine: SpiderMonkey)
- Samsung Internet (JavaScript engine: V8)

The WebAssembly approach (used by `@openforge-sh/liboqs`) provides approximately 4x better performance than pure JavaScript [7], but pure JavaScript already delivers thousands of operations per second, far exceeding ENCRYPT's needs (one key exchange per message hide/reveal operation).

### 5.2 Mobile Performance

Research on Kyber implementations for mobile devices demonstrates that ML-KEM is well-suited for resource-constrained environments [7]:

- **Memory**: as little as 4 KB is sufficient for ML-KEM cryptographic operations
- **ARM optimization**: ARM NEON instructions provide hardware-accelerated polynomial arithmetic on modern phone processors
- **Real-world overhead**: replacing ECDH with Kyber in a chat encryption scenario increased runtime by a factor of approximately 2.3x [8], but the absolute time remains under 5 milliseconds

### 5.3 Bundle Size Impact

Adding ML-KEM to ENCRYPT's client-side bundle:

| Library | Gzipped Size | Impact on Load Time (3G) |
|---------|-------------|-------------------------|
| `mlkem` (ML-KEM only) | ~8 KB | ~0.02 seconds |
| `@noble/post-quantum` (full suite) | ~16 KB | ~0.04 seconds |

For comparison, ENCRYPT's current `theme.css` is approximately 12 KB unminified. The ML-KEM library is comparable in size to a single stylesheet.

### 5.4 Browser-Native PQC (TLS Layer)

Major browsers have already deployed ML-KEM at the TLS layer for HTTPS connections [9]:

| Browser | ML-KEM TLS Support | Version | Default |
|---------|--------------------|---------|---------|
| Chrome | X25519MLKEM768 | 131+ (Nov 2024) | Yes |
| Firefox | X25519MLKEM768 | 135+ (Feb 2025) | Yes |
| Safari | Expected in macOS/iOS 26 | Fall 2025 | TBD |

By March 2025, approximately 38% of human HTTPS traffic on Cloudflare's network used hybrid post-quantum TLS handshakes [10]. This means the transport layer between mobile phones and ENCRYPT's Render server already benefits from ML-KEM in most cases, providing quantum-resistant encryption of the HTTP requests themselves.

However, application-layer ML-KEM (what Direction 6.6 proposes) provides a distinct benefit: it enables end-to-end quantum-resistant key agreement for the steganographic payload, independent of the transport layer. Even if the TLS connection is compromised, the embedded message remains protected by its own ML-KEM key exchange.

---

## 6. Proposed Architecture for ENCRYPT

### 6.1 Current Flow (Shared Password)

```
Sender                                    Receiver
  │                                          │
  ├── knows password ──────────────────── knows password
  │                                          │
  ├── XOR encrypt with password              │
  ├── LSB embed into image                   │
  ├── send image ──────────────────────> receive image
  │                                          ├── LSB extract
  │                                          ├── XOR decrypt with password
  │                                          └── read message
```

### 6.2 Proposed Flow (ML-KEM Key Exchange)

```
Sender                                    Receiver
  │                                          │
  │                                          ├── generateKeyPair()
  │                                          ├── publish publicKey
  │     ┌────────────────────────────────────┤
  │     │ publicKey (1,184 bytes)            │
  │     ▼                                    │
  ├── encap(publicKey)                       │
  │     → ciphertext (1,088 bytes)           │
  │     → sharedSecret (32 bytes)            │
  │                                          │
  ├── AES-256-GCM encrypt with sharedSecret  │
  ├── LSB embed: ciphertext + encrypted msg  │
  ├── send stego image ────────────────> receive stego image
  │                                          ├── LSB extract: ciphertext + encrypted msg
  │                                          ├── decap(ciphertext, secretKey)
  │                                          │     → sharedSecret (32 bytes)
  │                                          ├── AES-256-GCM decrypt with sharedSecret
  │                                          └── read message
```

### 6.3 Hybrid Mode (Backward Compatible)

ENCRYPT could support both modes through a payload header:

| Mode | Header Byte | Key Exchange | Encryption | Use Case |
|------|------------|-------------|------------|----------|
| `0x01` | Legacy | Shared password | XOR | Backward compatibility |
| `0x02` | Standard | Shared password | AES-256-GCM | Upgraded symmetric |
| `0x03` | PQC | ML-KEM-768 | AES-256-GCM | Quantum-resistant |

The mode byte is the first byte of the embedded payload. The extraction function reads this byte first and dispatches to the appropriate decryption pipeline.

### 6.4 Capacity Impact

Adding ML-KEM key exchange data to the steganographic payload:

| Component | Size | Cumulative |
|-----------|------|-----------|
| Mode header | 1 byte | 1 B |
| ML-KEM ciphertext | 1,088 bytes | 1,089 B |
| AES-GCM IV | 12 bytes | 1,101 B |
| AES-GCM auth tag | 16 bytes | 1,117 B |
| Message payload | Variable | 1,117 B + message |

For a 1920x1080 image with 777,600 bytes of LSB capacity, the ML-KEM overhead of 1,117 bytes consumes only 0.14% of the total capacity, leaving 776,483 bytes (approximately 758 KB) available for the encrypted message.

---

## 7. Implementation Roadmap

### Phase 1: Add ML-KEM Library (Minimal Change)

```bash
npm install mlkem
```

Add to `package.json` dependencies. No build configuration changes needed.

**Files modified**: `package.json` only.

### Phase 2: Create PQC Key Exchange Service

Create `src/services/pqc.ts` with functions for:
- `generateKeyPair()`: returns `{ publicKey, secretKey }` as `Uint8Array`
- `encapsulate(publicKey)`: returns `{ ciphertext, sharedSecret }`
- `decapsulate(ciphertext, secretKey)`: returns `sharedSecret`

**Files created**: `src/services/pqc.ts`

### Phase 3: Upgrade Encryption Service

Replace or augment `src/services/crypto.ts` with AES-256-GCM using the shared secret from ML-KEM:

```typescript
import { createCipheriv, createDecipheriv, randomBytes } from "crypto";

export function aesEncrypt(plaintext: string, key: Uint8Array): Buffer {
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  const encrypted = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([iv, tag, encrypted]);
}

export function aesDecrypt(data: Buffer, key: Uint8Array): string {
  const iv = data.subarray(0, 12);
  const tag = data.subarray(12, 28);
  const encrypted = data.subarray(28);
  const decipher = createDecipheriv("aes-256-gcm", key, iv);
  decipher.setAuthTag(tag);
  return decipher.update(encrypted) + decipher.final("utf8");
}
```

**Files modified**: `src/services/crypto.ts`

### Phase 4: Update Steganography Service

Modify `src/services/steganography.ts` to embed the mode byte, ML-KEM ciphertext, and AES-encrypted message:

**Files modified**: `src/services/steganography.ts`, `src/types.ts`

### Phase 5: Add Key Management UI

Add a receiver key generation page where users can generate and download their ML-KEM key pair. The sender uploads the receiver's public key alongside the carrier image and secret message.

**Files created/modified**: `views/keys.ejs`, `src/routes/keys.ts`, `public/ts/keys.ts`

### Phase 6: Client-Side ML-KEM (Optional)

For end-to-end encryption where the server never sees the plaintext:
- Include `mlkem` in the client-side esbuild bundle
- Perform key exchange and AES encryption entirely in the browser
- Server only handles the steganography layer (LSB embedding of already-encrypted data)

**Files modified**: `build.mjs`, `public/ts/hide.ts`, `public/ts/extract.ts`

---

## 8. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| ML-KEM cryptanalysis breakthrough | Low | ML-KEM security is based on the Module-LWE problem, studied for decades; HQC provides algorithm diversity as NIST backup |
| Pure JS performance insufficient | Very Low | Benchmarks show thousands of ops/sec; ENCRYPT needs one operation per request |
| Library abandoned/unmaintained | Low | `mlkem` and `@noble/post-quantum` are actively maintained; `@noble` ecosystem has strong track record |
| No independent audit | Medium | `mlkem` passes all NIST KAT vectors; `@noble/post-quantum` has undergone self-audit; independent audit recommended before production deployment |
| Increased payload size | Very Low | ML-KEM overhead is 1,117 bytes, consuming 0.14% of a 1080p image's capacity |
| Key management complexity | Medium | Users must generate, store, and exchange public keys; UX design must make this intuitive |
| Backward compatibility | Low | Mode header byte in payload enables version detection and graceful fallback |

---

## 9. Conclusion

By evaluating the current landscape of post-quantum key encapsulation mechanisms, we conclude that ML-KEM-768 is the optimal choice for integrating quantum-resistant key exchange into the ENCRYPT Steganography Suite. The algorithm provides NIST Level 3 security with compact key sizes (1,184-byte public key, 1,088-byte ciphertext) and minimal computational overhead.

The implementation path is straightforward because mature, pure TypeScript libraries (`mlkem`, `@noble/post-quantum`) eliminate the need for native compilation or WebAssembly. These libraries work in both Node.js (for the Render.com server) and mobile browsers (for phone-based access), with zero changes to the deployment configuration. The ML-KEM overhead of approximately 1,117 bytes per message consumes less than 0.15% of a standard image's steganographic capacity, and the key exchange operation completes in under 1 millisecond on modern hardware.

By combining ML-KEM key exchange with AES-256-GCM authenticated encryption, ENCRYPT would transform from a system with 256 possible keys to one with 2^256 possible keys derived through quantum-resistant key agreement, an improvement of approximately 75 orders of magnitude. The proposed hybrid mode architecture preserves backward compatibility while enabling progressive adoption of post-quantum security.

---

## Sources

1. [NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard](https://csrc.nist.gov/pubs/fips/203/final)
2. [Cloudflare: State of the Post-Quantum Internet in 2025](https://blog.cloudflare.com/pq-2025/)
3. [NIST Post-Quantum Cryptography Standardization (Wikipedia)](https://en.wikipedia.org/wiki/NIST_Post-Quantum_Cryptography_Standardization)
4. [mlkem: Pure TypeScript ML-KEM Implementation (GitHub)](https://github.com/dajiaji/crystals-kyber-js)
5. [noble-post-quantum: Auditable JS Post-Quantum Cryptography (GitHub)](https://github.com/paulmillr/noble-post-quantum)
6. [liboqs-node: Node.js Bindings for liboqs (GitHub)](https://github.com/TapuCosmo/liboqs-node)
7. [Portable and Efficient Implementation of CRYSTALS-Kyber Based on WebAssembly (CSSE, 2023)](https://www.researchgate.net/publication/368417526_Portable_and_Efficient_Implementation_of_CRYSTALS-Kyber_Based_on_WebAssembly)
8. [Evaluating Kyber Post-Quantum KEM in a Mobile Application (NIST PQC Conference)](https://csrc.nist.gov/CSRC/media/Events/third-pqc-standardization-conference/documents/accepted-papers/ribeiro-evaluating-kyber-pqc2021.pdf)
9. [Post-Quantum Hybrid TLS Is Here: How ML-KEM Arrived Quietly in Your Browser](https://www.intelligentliving.co/quantum-hybrid-tls-ml-kem-browser/)
10. [Cloudflare: PQ 2025 Traffic Statistics](https://blog.cloudflare.com/pq-2025/)
11. [ML-KEM Key Sizes and Parameters (NIST FIPS 203 PDF)](https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.203.pdf)
12. [Performance Analysis of Post-Quantum Cryptography Algorithms (arXiv, 2025)](https://arxiv.org/html/2503.12952v1)
13. [Google Chrome Switches to ML-KEM for Post-Quantum Defense (The Hacker News)](https://thehackernews.com/2024/09/google-chrome-switches-to-ml-kem-for.html)
14. [Render.com Free Tier Pricing and Limits (2025)](https://www.freetiers.com/directory/render)
15. [wolfSSL Accelerated ML-KEM](https://www.wolfssl.com/accelerated-kyber-ml-kem/)
16. [Project Eleven: ML-KEM Over WebSockets in the Browser](https://blog.projecteleven.com/posts/guaranteeing-post-quantum-encryption-in-the-browser-ml-kem-over-websockets)
17. [Post-Quantum Cryptography Standardization 2025 Update](https://postquantum.com/post-quantum/cryptography-pqc-nist/)
18. [Keysight: Are Modern Networks Ready for Post-Quantum Encryption?](https://www.keysight.com/blogs/en/tech/nwvs/2025/08/05/post-quantum-handshakes)
19. [ML-KEM Mythbusting (Key Material, 2025)](https://keymaterial.net/2025/11/27/ml-kem-mythbusting/)
20. [OpenPGP crystals-kyber-js (npm)](https://www.npmjs.com/package/@openpgp/crystals-kyber-js)
