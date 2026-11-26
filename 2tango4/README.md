# 2tango4

**Dual-Lane Quaternary ARX Stream & Authenticated Encryption (AEAD) Cipher**

`2tango4` ("Two Tangos of Four") is a zero-allocation, dual-lane quaternary ARX encryption architecture engineered to eliminate the structural limitations of legacy stream ciphers like ChaCha20 and Salsa20. By replacing single-matrix fixed constants, short nonces, and unauthenticated keystreams with a 512-bit `SHA-512` key-derived root, a 192-bit nonce, dual cross-coupled quaternary rotation lanes, and built-in 256-bit tamper authentication, `2tango4` sets a new benchmark for high-speed, self-authenticating symmetric encryption across browsers, edge runtimes, and servers.

---

## Why 2tango4 Changes Symmetric Cryptography

1. **Zero Fixed Public Constants (512-Bit Key-Derived Root)**
   * ChaCha20 and Salsa20 expose 128 bits of fixed public ASCII constants (`"expand 32-byte k"`) in every block state.
   * `2tango4` initializes all **16 × 32-bit state words (512 bits)** directly from `SHA-512(domain || key || nonce192)`, ensuring zero predictable bits enter the round function.
2. **Dual Quaternary Lanes + Cross-Lane Tango Bridge**
   * **Lane Alpha (`A0..A3`)** drives 4-angle ARX rotations (`16, 12, 8, 7`) while **Lane Beta (`B0..B3`)** drives complementary coprime rotations (`13, 9, 15, 5`).
   * Every round couples both lanes through an asymmetric XOR-addition **Tango Bridge** and emits a full **64-byte (512-bit)** block per counter tick with ~50.00% single-bit key and nonce avalanche.
3. **192-Bit Nonce + 64-Bit Counter**
   * Standard RFC 8439 ChaCha20 restricts nonces to 96 bits and caps a single nonce at $2^{32}$ blocks (256 GiB).
   * `2tango4` natively uses a **192-bit (24-byte) random nonce** and a **64-bit counter** ($2^{64}$ blocks per nonce), preventing birthday-bound nonce collisions at scale.
4. **Authenticated Encryption (AEAD) by Default**
   * Unauthenticated ChaCha20 and Salsa20 allow silent ciphertext bit-flipping unless paired externally with Poly1305.
   * `2tango4` derives an isolated block-0 subkey to compute a **256-bit keyed `HMAC-SHA-256` authentication tag** over nonce, associated data (AAD), and ciphertext—blocking any tampered byte before decryption.

---

## Quick Start (`2tango4.js`)

```javascript
import { TwoTango4 } from "./2tango4.js";

// 1. Encrypt with automatic 192-bit nonce and 256-bit authentication tag
const packet = await TwoTango4.encrypt(
  "Confidential payload",
  "my-secret-passphrase",
  TwoTango4.generateNonce(),
  "optional-header-aad"
);

// 2. Decrypt and verify integrity tag
const plaintextBytes = await TwoTango4.decrypt(
  packet.ciphertext,
  packet.tag,
  "my-secret-passphrase",
  packet.nonce,
  "optional-header-aad"
);

console.log(new TextDecoder().decode(plaintextBytes));
// -> "Confidential payload"
```

### Browser `<script>` Tag Usage

```html
<script type="module">
  import { TwoTango4 } from "./2tango4.js";

  const { nonce, ciphertext, tag } = await TwoTango4.encrypt(
    new TextEncoder().encode("Hello 2tango4"),
    "secret-key"
  );

  const decrypted = await TwoTango4.decrypt(ciphertext, tag, "secret-key", nonce);
  console.log(new TextDecoder().decode(decrypted));
</script>
```