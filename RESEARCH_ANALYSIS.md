# ENCRYPT: Comparative Security Analysis and Future Directions

> **Scope**: Deep research comparing ENCRYPT's current algorithms against modern cybersecurity standards, quantum-era cryptography, and emerging steganographic techniques  
> **Last Updated**: April 2026

---

## 1. Introduction

This document presents a comprehensive analysis of the ENCRYPT Steganography Suite's current cryptographic and steganographic algorithms in the context of the broader cybersecurity landscape. We examine the system's XOR cipher and LSB steganography against industry-standard encryption, post-quantum cryptography, quantum key distribution, and neural network steganography. We identify concrete limitations and propose actionable directions for strengthening the system.

The ENCRYPT suite currently employs two security layers:

- **Encryption**: XOR cipher with sum-mod-256 key derivation (single-byte key, 256 possible values)
- **Steganography**: Sequential LSB embedding across RGB pixel channels with null-byte termination

Both layers represent foundational approaches that prioritize simplicity and educational clarity. The analysis that follows contextualizes these choices within the current state of cryptographic and steganographic research.

---

## 2. Encryption: Current Implementation vs. Modern Standards

### 2.1 ENCRYPT's XOR Cipher

The system derives a single-byte key by summing all character codes of the password and reducing modulo 256. Each plaintext character is then XOR-ed with this key. While XOR forms the mathematical basis of many strong ciphers (including AES and ChaCha20), the security of any XOR-based scheme depends entirely on the key's randomness and length.

| Property | ENCRYPT (XOR) | Minimum Modern Standard |
|----------|---------------|------------------------|
| Key size | 1 byte (8 bits) | 128-256 bits |
| Effective keyspace | 256 values | 2^128 to 2^256 values |
| Key derivation | `sum(charCodes) % 256` | PBKDF2, bcrypt, or Argon2 |
| Salt | None | Random per encryption |
| IV/Nonce | None | Random per encryption |
| Authentication | None (heuristic only) | HMAC or GCM tag |

### 2.2 AES (Advanced Encryption Standard)

AES remains the dominant symmetric cipher in 2026. Operating on 128-bit blocks with key sizes of 128, 192, or 256 bits, AES provides a keyspace of 2^256 in its strongest configuration, approximately 1.16 x 10^77 possible keys, compared to ENCRYPT's 256. AES-256-GCM achieves approximately 3 to 4 GB/s per core on modern Intel processors with AES-NI hardware acceleration (with higher aggregate throughput possible across multiple cores), demonstrating that strong encryption imposes minimal performance overhead on modern hardware [1].

A 2025 panoramic survey of AES architecture confirms that no practical attack has reduced AES security below its theoretical margin in over two decades of cryptanalysis [2]. AES with Galois Counter Mode (GCM) provides authenticated encryption, combining confidentiality and integrity verification in a single primitive.

### 2.3 ChaCha20-Poly1305

ChaCha20 is a stream cipher designed by Daniel Bernstein (published 2008) that uses Add-Rotate-XOR (ARX) operations, making it computationally cheaper than AES on devices without hardware acceleration. On platforms that lack dedicated AES instructions (such as older ARM boards and certain IoT devices), ChaCha20-Poly1305 outperforms AES-GCM by a significant margin. However, on modern processors with AES hardware acceleration (including Apple M-series chips with ARM Cryptographic Extensions and Intel/AMD with AES-NI), AES-256-GCM is typically faster than ChaCha20 [1]. ChaCha20-Poly1305 is an Authenticated Encryption with Associated Data (AEAD) algorithm that combines the ChaCha20 stream cipher with the Poly1305 message authentication code, providing both confidentiality and integrity in a single operation [3].

Implementations of ChaCha20-Poly1305 are less vulnerable to timing attacks than AES implementations, since ChaCha20 operates exclusively with constant-time ARX operations that do not use data-dependent table lookups [4]. This makes it particularly suitable for environments where side-channel resistance matters, even when AES is faster in throughput.

### 2.4 Authenticated Encryption (AEAD)

ENCRYPT's current design has no mechanism to verify whether decryption produced the correct output. The 70% printable-character heuristic is a probabilistic guess, not a cryptographic guarantee. Modern AEAD constructions (AES-GCM, ChaCha20-Poly1305) solve this by appending a Message Authentication Code (MAC) to the ciphertext. The MAC is a keyed hash of the ciphertext and any associated metadata, allowing the receiver to verify both that the ciphertext has not been tampered with and that the correct key was used [5].

Without AEAD, ENCRYPT is vulnerable to:
- **Bit-flipping attacks**: an adversary who knows the plaintext structure can XOR specific ciphertext bytes to alter the decrypted message without detection
- **Silent decryption failure**: messages that happen to contain >70% printable characters after wrong-key decryption will be accepted as valid

### 2.5 Key Derivation Functions

ENCRYPT's key derivation, `sum(charCodes) % 256`, collapses all password entropy into a single byte. Modern key derivation functions are designed to be deliberately slow, memory-intensive, and resistant to parallelization on specialized hardware.

| KDF | Memory Hardness | GPU/ASIC Resistance | OWASP Recommendation (2025) |
|-----|----------------|---------------------|-----------------------------|
| **Argon2id** | Configurable (19+ MiB) | Strong | First choice for new systems |
| **bcrypt** | Fixed (4 KB) | Moderate | Acceptable for existing systems |
| **scrypt** | Configurable | Strong | Good alternative |
| **PBKDF2** | None | Weak | FIPS-140 compliance only |
| **sum % 256** | None | None | Not recommended |

Argon2id, the winner of the 2015 Password Hashing Competition, is considered the most future-proof option for new systems. OWASP recommends Argon2id with a minimum configuration of 19 MiB of memory, an iteration count of 2, and 1 degree of parallelism [6]. By comparison, ENCRYPT's key derivation executes in nanoseconds with zero memory overhead, offering no resistance to brute-force attacks.

---

## 3. Steganography: Current Implementation vs. State of the Art

### 3.1 ENCRYPT's LSB Embedding

The system replaces the least significant bit of each RGB pixel channel byte with one bit of the encrypted message, proceeding sequentially from the first pixel. This approach is straightforward to implement and produces visually imperceptible changes (maximum pixel value change of 1 unit per channel).

However, sequential LSB embedding introduces detectable statistical artifacts. Research demonstrates that over 90% of basic LSB methods are detectable via deep learning steganalysis, with reported detection rates ranging from 91% to 99% depending on payload size, image type, and the specific classifier used [7]. The sequential embedding pattern creates clustering artifacts in the early portion of the image, leaving the remainder statistically untouched, a signature that modern steganalyzers exploit.

### 3.2 Detection Methods (Steganalysis)

Modern steganalysis employs multiple statistical and machine-learning techniques to detect LSB embedding:

**Chi-Square Analysis**: In natural images, adjacent even-odd pixel value pairs follow predictable frequency distributions. LSB embedding equalizes these pairs, producing a detectable deviation that chi-square tests quantify with high reliability [8].

**RS Analysis (Regular-Singular)**: This technique classifies pixel groups by smoothness. LSB embedding disrupts the ratio of "regular" to "singular" groups in a mathematically predictable way, enabling detection even at low embedding rates [8].

**CNN-Based Steganalysis**: Convolutional neural networks trained on cover/stego image pairs can detect LSB embedding with high accuracy. Recent work shows that if attackers exploit the least significant bits, detection ability with advanced CNN models remains reliable across diverse image types [7].

### 3.3 Content-Adaptive LSB Steganography

A 2025 content-adaptive LSB steganography framework from Scientific Reports integrates saliency-guided embedding with Ant Colony Optimization (ACO) mechanisms to distribute embedding indices spatially across images [9]. Rather than embedding sequentially from the first pixel, this approach:

1. Uses Canny edge detection to identify texture-rich regions where modifications are least perceptible
2. Allocates higher payload capacities to complex, edge-rich blocks
3. Uses ACO to disperse embedding positions, preventing clustering artifacts

This framework achieves PSNR values in the range of 55 dB to 64.5 dB depending on secret image size and embedding rate (compared to basic LSB's typical 51 dB at moderate payloads) and demonstrates random-level detectability against modern CNN-based steganalyzers [9].

### 3.4 DCT-Domain Steganography

Unlike spatial-domain methods (LSB), DCT-domain steganography operates on the frequency coefficients produced by the Discrete Cosine Transform, the same transform used in JPEG compression. A recent study (submitted 2025, published February 2026) demonstrates adaptive DCT-based steganography that selects mid-frequency coefficients in 8x8 blocks, achieving a 58.5% improvement in embedding efficiency over standard binary techniques while maintaining robustness against JPEG compression, with PSNR values ranging from 48 dB to 62 dB [10].

Key advantages over spatial-domain LSB:
- **JPEG survival**: embedded data persists through lossy compression
- **Perceptual masking**: modifications concentrate in frequency bands where human vision is least sensitive
- **Compression alignment**: works with rather than against the image compression pipeline

### 3.5 Deep Learning Steganography

The most significant recent advance in steganography is the application of Generative Adversarial Networks (GANs) and neural network architectures:

**GAN-Based Approaches**: AGASI (2025) uses an encoder as the GAN generator alongside a discriminator, achieving an 84.73% misclassification rate against neural network steganalyzers under adversarial perturbation [11]. The adversarial training process inherently optimizes for undetectability.

**Invertible Neural Networks (INNs)**: Hybrid INN-GAN architectures combine the information-preserving properties of invertible networks with the visual quality enhancement of adversarial training, achieving extraction accuracy close to 100% across multiple network structures [12].

**StegNet Performance**: State-of-the-art deep learning steganography achieves a decoding rate of 98.2% with a capacity of 23.57 bits per pixel (bpp), while modifying only 0.76% of the cover image [13]. For comparison, ENCRYPT's LSB method modifies exactly 1 bit per channel (effectively 3 bpp at full capacity) with sequential placement.

**Multi-Layered Approaches**: A 2025 Scientific Reports paper presents a deep learning-driven multi-layered steganographic approach that addresses limitations of single-method systems, providing enhanced robustness against both conventional steganalysis and deep learning-based detection [14].

---

## 4. Quantum Cryptography and Post-Quantum Security

### 4.1 The Quantum Threat

The Global Risk Institute's 2026 Quantum Threat Timeline estimates a cryptographically relevant quantum computer is "quite possible" within 10 years and "likely" within 15 [15]. The primary threats are:

**Shor's Algorithm**: breaks RSA, ECC, and Diffie-Hellman key exchange by efficiently factoring large integers and computing discrete logarithms. This threatens all asymmetric cryptography used for key exchange and digital signatures.

**Grover's Algorithm**: provides a quadratic speedup for brute-force search, effectively halving the security of symmetric ciphers. AES-256 retains 128-bit security post-quantum, while AES-128 drops to 64-bit security. ENCRYPT's XOR cipher with 8-bit key would be reduced from 256 possible keys to effectively instantaneous cracking, though it is already trivially breakable without quantum computers.

**"Harvest Now, Decrypt Later"**: Nation-states and advanced adversaries are already stockpiling encrypted communications with the intent to decrypt them once quantum computers become available [15]. This makes current encryption choices consequential even for data that appears secure today.

### 4.2 NIST Post-Quantum Cryptography Standards

NIST finalized its first three post-quantum cryptography standards on August 13, 2024, marking a watershed moment in the transition to quantum-resistant cryptography [16]:

**FIPS 203 (ML-KEM)**: Based on the CRYSTALS-Kyber algorithm, renamed Module-Lattice-Based Key-Encapsulation Mechanism. ML-KEM is the primary standard for key encapsulation and is designed to replace Diffie-Hellman and ECDH key exchange. Security is based on the hardness of the Module Learning with Errors (MLWE) problem, which is believed to resist both classical and quantum attacks [16].

**FIPS 204 (ML-DSA)**: Based on the CRYSTALS-Dilithium algorithm, renamed Module-Lattice-Based Digital Signature Algorithm. Provides quantum-resistant digital signatures for authentication and integrity verification [16].

**FIPS 205 (SLH-DSA)**: Based on the SPHINCS+ algorithm, renamed Stateless Hash-Based Digital Signature Algorithm. Provides an alternative signature scheme based solely on hash function security, offering a different mathematical foundation than lattice-based approaches [16].

**HQC (March 2025)**: NIST selected the Hamming Quasi-Cyclic algorithm as an additional KEM, providing a code-based alternative to the lattice-based ML-KEM. Standardization is expected by 2026-2027 [17].

**FALCON/FN-DSA**: Currently progressing through the standardization pipeline as FIPS 206, offering compact signatures based on NTRU lattices [17].

### 4.3 Quantum Key Distribution (QKD)

QKD represents a fundamentally different approach to secure communication. Rather than relying on computational hardness assumptions (which quantum computers may break), QKD derives its security from the laws of quantum mechanics, specifically the no-cloning theorem and the measurement-disturbance principle [18].

**How QKD Works**: Two parties exchange quantum states (typically photon polarizations) over a quantum channel. Any eavesdropping attempt disturbs the quantum states in a detectable way, allowing the parties to verify that their shared key has not been intercepted. The resulting key can then be used with a one-time pad or symmetric cipher for provably secure communication.

**Recent Breakthroughs (2025)**:
- Toshiba and KDDI Research demonstrated QKD multiplexing, allowing QKD and data signals to share existing fiber optic networks at 33.4 Tbps over 80 km [19]
- QNu Labs demonstrated India's first QKD network spanning over 500 kilometers over existing optical fiber infrastructure [19]

**Current Limitations**:
- Distance constraints: QKD requires direct optical fiber or free-space optical links, limiting range until quantum repeaters mature [18]
- Infrastructure requirements: dedicated quantum channels or specialized multiplexing hardware
- Incompatibility with radio networks: wireless QKD currently exists only with free-space optics [18]
- Cost: specialized photon detectors and sources remain expensive
- The NSA has expressed skepticism about QKD as a general-purpose solution, noting it "does not provide a means to authenticate the QKD source" without additional classical cryptographic mechanisms [20]

**Complementary Strategy**: Organizations are adopting a dual approach, using post-quantum cryptography (PQC) for broad deployment and QKD for high-security use cases where the additional infrastructure investment is justified [19]. Canada has set federal deadlines requiring PQC migration plans by April 2026, with critical systems prioritized by 2031 and full migration by 2035 [15].

### 4.4 Relevance to ENCRYPT

ENCRYPT's symmetric XOR cipher is not directly threatened by Shor's algorithm (which targets asymmetric cryptography), but this is only because its keyspace is already trivially small. Grover's algorithm would reduce an 8-bit keyspace to approximately 4-bit equivalent security, reducing the brute-force search from 256 to 16 operations, but the cipher is already breakable in microseconds on classical hardware.

If ENCRYPT were upgraded to AES-256, the system would retain 128-bit post-quantum security against Grover's algorithm, sufficient for the foreseeable future. The steganography layer is not directly affected by quantum computing, as steganalysis relies on statistical analysis rather than key recovery.

---

## 5. Comprehensive Limitation Analysis

### 5.1 Encryption Layer Limitations

| Limitation | Severity | Detail |
|-----------|----------|--------|
| **Trivial keyspace** | Critical | 256 possible keys, brute-forced in microseconds |
| **Key collisions** | Critical | Passwords "ab" and "ba" produce identical keys; any anagram or sum-equivalent password is interchangeable |
| **No key stretching** | Critical | Modern KDFs (Argon2) deliberately consume time and memory; ENCRYPT's derivation is instantaneous |
| **No salt** | High | Same password always produces same key, enabling precomputation attacks |
| **No IV/nonce** | High | Same plaintext + password always produces identical ciphertext, enabling replay and comparison attacks |
| **No authentication** | High | No HMAC or GCM tag; 70% printable heuristic is unreliable for binary payloads and can silently accept wrong-key results |
| **Single-byte key reuse** | High | Every character is XOR-ed with the same byte, preserving frequency distributions and enabling frequency analysis |
| **No forward secrecy** | Medium | Compromising the password exposes all past and future messages encrypted with it |

### 5.2 Steganography Layer Limitations

| Limitation | Severity | Detail |
|-----------|----------|--------|
| **Sequential embedding** | High | Bits embed from pixel 0 onward; early channels are modified while later channels are untouched, creating a detectable boundary |
| **No content adaptation** | High | Embeds equally in flat regions (sky, walls) and textured regions (foliage, fabric); flat-region modifications are more detectable |
| **Chi-square vulnerability** | High | Even-odd pixel pair distributions are equalized by LSB replacement, detectable by standard steganalysis tools |
| **No JPEG survival** | Medium | Output must be PNG; any lossy recompression destroys the payload |
| **No capacity signaling** | Medium | The null-byte terminator is the only end-of-message signal; no header indicates payload length, complicating error recovery |
| **Full-image extraction** | Low | All pixel LSBs are read during extraction, regardless of payload size; large images incur unnecessary processing |

### 5.3 Architectural Limitations

| Limitation | Severity | Detail |
|-----------|----------|--------|
| **No message integrity** | High | No checksum or hash verifies that the extracted message is complete and uncorrupted |
| **No payload metadata** | Medium | No embedded header indicates encryption algorithm, payload length, or format version |
| **No multi-format output** | Low | Always outputs PNG; cannot produce WebP or other modern lossless formats |
| **Single-message capacity** | Low | Cannot embed multiple independent messages in different image regions |

---

## 6. Future Directions

### 6.1 Direction 1: Modern Authenticated Encryption

**Replace XOR cipher with AES-256-GCM or ChaCha20-Poly1305.**

This is the highest-impact improvement. AES-256-GCM provides:
- 256-bit key (2^256 keyspace, quantum-resistant at 128-bit equivalent)
- Random 96-bit nonce per encryption (prevents ciphertext repetition)
- 128-bit authentication tag (cryptographic proof of correct decryption)
- Native support in Node.js `crypto` module (no additional dependencies)

ChaCha20-Poly1305 is an equivalent alternative that performs better on devices without AES hardware acceleration and is also available in Node.js's `crypto` module.

**Implementation path**: Replace `xorCrypt()` with Node.js `crypto.createCipheriv("aes-256-gcm", key, iv)`, derive the key using Argon2 or PBKDF2 from the password, and prepend the salt, IV, and auth tag to the ciphertext before embedding.

### 6.2 Direction 2: Proper Key Derivation

**Replace `sum(charCodes) % 256` with Argon2id.**

Using the `argon2` npm package or Node.js's built-in `crypto.scrypt()`:
- Derive a 256-bit key from the password
- Include a random salt (stored as part of the embedded payload header)
- Configure memory and iteration parameters to resist GPU/ASIC attacks
- Salt ensures different ciphertext for the same password + plaintext combination

### 6.3 Direction 3: Content-Adaptive Embedding

**Replace sequential LSB embedding with saliency-guided adaptive placement.**

Following the 2025 content-adaptive framework [9]:
1. Analyze the carrier image for texture complexity using edge detection
2. Prioritize embedding in high-texture regions where modifications are least perceptible
3. Use pseudorandom index generation (seeded by the encryption key) to scatter embedding positions
4. This prevents the sequential embedding artifact and makes statistical detection significantly harder

### 6.4 Direction 4: DCT-Domain Steganography

**Embed data in frequency-domain coefficients rather than spatial-domain pixels.**

Operating in the DCT domain provides JPEG survival, meaning the hidden message can persist through lossy compression. This would allow ENCRYPT to output JPEG or WebP stego images, which appear less suspicious than PNG files (which are less common for photographs). The 2025 adaptive DCT framework achieves 58.5% better embedding efficiency than binary spatial methods [10].

### 6.5 Direction 5: Payload Metadata Header

**Embed a structured header before the message payload.**

A header could include:
- Magic bytes (to verify a message exists before attempting full extraction)
- Payload length (to avoid reading unnecessary pixels)
- Encryption algorithm identifier (to support multiple ciphers)
- Format version (to maintain backward compatibility)
- HMAC of the payload (integrity verification independent of AEAD)

### 6.6 Direction 6: Post-Quantum Key Exchange

**For multi-party scenarios, integrate ML-KEM (FIPS 203) for key agreement.**

While ENCRYPT currently uses a shared-password model (both parties know the password), a future version could support asymmetric key exchange where the sender encrypts with the receiver's public key. Using ML-KEM would make this key exchange quantum-resistant. The `liboqs` library and its Node.js bindings provide implementations of all NIST PQC algorithms.

### 6.7 Direction 7: Deep Learning Steganography

**Explore neural network encoders/decoders for embedding.**

GAN-based steganography represents the research frontier, achieving 84.73% evasion rates against neural network steganalyzers [11] and extraction accuracy near 100% [12]. While computationally expensive (requiring trained models), this approach could be offered as a "high-security" mode for users willing to accept slower processing in exchange for stronger undetectability.

### 6.8 Direction 8: Spread Spectrum Embedding

**Distribute each secret bit across multiple pixel channels using a pseudorandom spreading code.**

Rather than placing one secret bit in one pixel channel, spread spectrum steganography distributes each bit across many channels using a code sequence derived from the encryption key. This provides:
- Robustness against partial image modification
- Resistance to statistical detection (energy is distributed broadly)
- Graceful degradation (minor image alterations cause proportional rather than catastrophic errors)

---

## 7. Prioritized Upgrade Roadmap

Based on the analysis above, we recommend the following upgrade priorities ordered by security impact relative to implementation effort:

| Priority | Direction | Impact | Effort | Rationale |
|----------|-----------|--------|--------|-----------|
| **P0** | AES-256-GCM encryption | Critical | Low | Node.js `crypto` module provides native support; eliminates the most severe vulnerability (trivial keyspace) |
| **P0** | Argon2/scrypt key derivation | Critical | Low | `crypto.scrypt()` is built into Node.js; transforms password entropy into proper key material |
| **P1** | Payload metadata header | High | Low | Small structural change that enables integrity verification, version detection, and efficient extraction |
| **P1** | Pseudorandom embedding order | High | Medium | Seed a PRNG with the derived key to scatter embedding positions; eliminates sequential clustering artifact |
| **P2** | Content-adaptive embedding | Medium | Medium | Requires image analysis (edge detection) before embedding; significantly improves steganalytic resistance |
| **P3** | DCT-domain steganography | Medium | High | Requires understanding of DCT coefficients and quantization; enables JPEG-compatible output |
| **P4** | Deep learning steganography | Low-Medium | Very High | Requires trained models and GPU inference; research-grade improvement |
| **P5** | Post-quantum key exchange | Low | High | ML-KEM adds quantum resistance for asymmetric scenarios; current shared-password model is symmetric and less affected |

---

## 8. Summary

The ENCRYPT Steganography Suite implements a clean, educational dual-layer architecture that successfully demonstrates the core principles of cryptographic concealment. The XOR cipher illustrates how bitwise operations transform plaintext, while LSB embedding shows how information can hide in perceptually insignificant bits. These foundations are sound.

However, in the context of modern cybersecurity, the implementation sits at a significant distance from production-grade security. The single-byte XOR keyspace is trivially exhaustible, the sequential LSB embedding is detectable by standard steganalysis tools, and the absence of authenticated encryption leaves the system vulnerable to both incorrect-key acceptance and active tampering.

The most impactful upgrade path involves replacing the XOR cipher with AES-256-GCM (available natively in Node.js), introducing Argon2 or scrypt for key derivation, and randomizing the embedding order using a PRNG seeded by the derived key. These three changes would transform ENCRYPT from an educational tool into a system with meaningful cryptographic resistance, while preserving the architectural simplicity that makes the codebase accessible.

On the quantum frontier, ENCRYPT's symmetric approach is not directly threatened by Shor's algorithm, but the trivial keyspace offers no security regardless. Upgrading to AES-256 provides 128-bit post-quantum security against Grover's algorithm. For scenarios requiring key exchange, the NIST-standardized ML-KEM (FIPS 203) offers quantum-resistant key encapsulation with mature implementations already available.

The steganography frontier is advancing rapidly, with GAN-based and deep learning approaches achieving near-perfect undetectability. While these methods are computationally expensive, content-adaptive LSB embedding and pseudorandom embedding order represent practical intermediate steps that substantially improve resistance to steganalysis without requiring neural network infrastructure.

---

## Sources

1. [Encryption Algorithm Comparison: Performance, Security, and Use Cases (StealthCloud)](https://stealthcloud.ai/data/encryption-algorithm-comparison/)
2. [A Panoramic Survey of AES: Architecture to Security Analysis (Springer, 2025)](https://link.springer.com/article/10.1007/s10207-025-01116-x)
3. [ChaCha20-Poly1305 (Wikipedia)](https://en.wikipedia.org/wiki/ChaCha20-Poly1305)
4. [AES & ChaCha: A Case for Simplicity in Cryptography (Phase Blog)](https://phase.dev/blog/chacha-and-aes-simplicity-in-cryptography/)
5. [Authenticated Encryption: Why You Need It and How It Works (Andrea Corbellini)](https://andrea.corbellini.name/2023/03/09/authenticated-encryption/)
6. [Password Hashing Guide 2025: Argon2 vs Bcrypt vs Scrypt vs PBKDF2 (Deepak Gupta)](https://guptadeepak.com/the-complete-guide-to-password-hashing-argon2-vs-bcrypt-vs-scrypt-vs-pbkdf2-2026/)
7. [Steganalysis of AI Models LSB Attacks (IEEE Xplore)](https://ieeexplore.ieee.org/document/10486976/)
8. [Reliable Detection of LSB Steganography in Color and Grayscale Images (ACM)](https://dl.acm.org/doi/10.1145/1232454.1232466)
9. [Content-Adaptive LSB Steganography with Saliency Fusion, ACO Dispersion, and Hybrid Encryption (Scientific Reports, 2025)](https://www.nature.com/articles/s41598-025-33920-9)
10. [Novel Adaptive DCT-Based Steganography Algorithm (UKSCIP, 2025)](https://ojs.ukscip.com/index.php/jic/article/view/1570)
11. [AGASI: A GAN-Based Approach to Strengthening Adversarial Image Steganography (MDPI Entropy, 2025)](https://www.mdpi.com/1099-4300/27/3/282)
12. [High-Accuracy Image Steganography with Invertible Neural Network and GAN (Signal Processing, 2025)](https://www.sciencedirect.com/science/article/abs/pii/S0165168425001021)
13. [Deep Learning-Based Image Steganography with Latent Space Embedding (MDPI Entropy, 2025)](https://www.mdpi.com/1099-4300/27/12/1223)
14. [A Deep Learning-Driven Multi-Layered Steganographic Approach (Scientific Reports, 2025)](https://www.nature.com/articles/s41598-025-89189-5)
15. [Quantum-Safe Cryptography: Companies and Players Across the Landscape 2026 (The Quantum Insider)](https://thequantuminsider.com/2026/03/25/25-companies-building-the-quantum-cryptography-communications-markets/)
16. [NIST Releases First 3 Finalized Post-Quantum Encryption Standards (NIST, 2024)](https://www.nist.gov/news-events/news/2024/08/nist-releases-first-3-finalized-post-quantum-encryption-standards)
17. [Post-Quantum Cryptography PQC Standardization: 2025 Update (PostQuantum)](https://postquantum.com/post-quantum/cryptography-pqc-nist/)
18. [Quantum Key Distribution (Wikipedia)](https://en.wikipedia.org/wiki/Quantum_key_distribution)
19. [QKD in 2025: Innovations, Challenges, and the Path to Adoption (Juniper Research)](https://www.juniperresearch.com/resources/blog/qkd-in-2025-innovations-challenges-and-the-path-to-adoption/)
20. [NSA: Quantum Key Distribution and Quantum Cryptography (NSA)](https://www.nsa.gov/Cybersecurity/Quantum-Key-Distribution-QKD-and-Quantum-Cryptography-QC/)
21. [Post-Quantum Cryptography: NIST Standards 2026 Complete Guide (CalmOps)](https://calmops.com/technology/post-quantum-cryptography-nist-standards-2026/)
22. [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
23. [XOR Cipher Brute Force: Automated Cryptanalysis and Key Recovery (Inventive HQ)](https://inventivehq.com/blog/xor-brute-force-cryptanalysis-automated)
24. [XOR Known-Plaintext Attacks (NVISO Labs)](https://blog.nviso.eu/2023/10/12/xor-known-plaintext-attacks/)
25. [A Hybrid Steganography Framework Using DCT and GAN (Scientific Reports, 2025)](https://www.nature.com/articles/s41598-025-01054-7)
26. [How to Choose Cryptographic Algorithms: A Decision Framework for 2025 (Axis Intelligence)](https://axis-intelligence.com/how-to-choose-cryptographic-algorithms-guide/)
27. [Deep Steganographic Approach for Reliable Data Hiding Using CNNs (Scientific Reports, 2025)](https://www.nature.com/articles/s41598-025-26867-4)
28. [XChaCha20-Poly1305 vs AES: Modern Encryption Comparison (2025)](https://blog.vitalvas.com/post/2025/06/01/xchacha20-poly1305-vs-aes/)
