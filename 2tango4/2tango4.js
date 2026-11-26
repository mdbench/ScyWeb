// 2tango4.js — Zero-Allocation Dual-Lane Quaternary ARX Stream & AEAD Cipher
export class TwoTango4 {
    static async initState(keyBytes, nonce24) {
      if (!(keyBytes instanceof Uint8Array)) keyBytes = new TextEncoder().encode(String(keyBytes));
      if (!(nonce24 instanceof Uint8Array) || nonce24.length !== 24) {
        throw new Error("2tango4 requires a 24-byte (192-bit) nonce.");
      }
      const domain = new TextEncoder().encode("2tango4-v2-root");
      const payload = new Uint8Array(domain.length + keyBytes.length + nonce24.length);
      payload.set(domain, 0);
      payload.set(keyBytes, domain.length);
      payload.set(nonce24, domain.length + keyBytes.length);
      const digest = await globalThis.crypto.subtle.digest("SHA-512", payload);
      return new Uint32Array(digest); // 16 x 32-bit words (512 bits)
    }
  
    static generateNonce() {
      return globalThis.crypto.getRandomValues(new Uint8Array(24));
    }
  
    static keystream(r, byteLength, startCounter = 1n, rounds = 8) {
      const out = new Uint8Array(byteLength);
      const alignedWords = byteLength >>> 2;
      const out32 = new Uint32Array(out.buffer, 0, alignedWords);
  
      const r0 = r[0], r1 = r[1], r2 = r[2], r3 = r[3];
      const r4 = r[4], r5 = r[5], r6 = r[6], r7 = r[7];
      const r8 = r[8], r9 = r[9], r10 = r[10], r11 = r[11];
      const r12 = r[12], r13 = r[13], r14 = r[14], r15 = r[15];
  
      let cLo = Number(startCounter & 0xffffffffn) >>> 0;
      let cHi = Number((startCounter >> 32n) & 0xffffffffn) >>> 0;
  
      let wIdx = 0;
      while (wIdx + 16 <= alignedWords) {
        let a0 = (r0 ^ cLo) >>> 0, a1 = (r1 ^ cHi) >>> 0, a2 = r2, a3 = r3;
        let b0 = (r4 ^ cHi) >>> 0, b1 = (r5 ^ cLo) >>> 0, b2 = r6, b3 = r7;
  
        for (let round = 0; round < rounds; round++) {
          // Lane Alpha (16, 12, 8, 7)
          a0 = (a0 + a1) | 0; a3 ^= a0; a3 = (a3 << 16) | (a3 >>> 16);
          a2 = (a2 + a3) | 0; a1 ^= a2; a1 = (a1 << 12) | (a1 >>> 20);
          a0 = (a0 + a1) | 0; a3 ^= a0; a3 = (a3 << 8)  | (a3 >>> 24);
          a2 = (a2 + a3) | 0; a1 ^= a2; a1 = (a1 << 7)  | (a1 >>> 25);
  
          // Lane Beta (13, 9, 15, 5)
          b0 = (b0 + b1) | 0; b3 ^= b0; b3 = (b3 << 13) | (b3 >>> 19);
          b2 = (b2 + b3) | 0; b1 ^= b2; b1 = (b1 << 9)  | (b1 >>> 23);
          b0 = (b0 + b1) | 0; b3 ^= b0; b3 = (b3 << 15) | (b3 >>> 17);
          b2 = (b2 + b3) | 0; b1 ^= b2; b1 = (b1 << 5)  | (b1 >>> 27);
  
          // Cross-lane Tango Bridge
          a0 = (a0 + b2) | 0; b1 ^= a1;
          a2 = (a2 + b0) | 0; b3 ^= a3;
        }
  
        out32[wIdx]      = (a0 + r0)  >>> 0;
        out32[wIdx + 1]  = (a1 + r1)  >>> 0;
        out32[wIdx + 2]  = (a2 + r2)  >>> 0;
        out32[wIdx + 3]  = (a3 + r3)  >>> 0;
        out32[wIdx + 4]  = (b0 + r4)  >>> 0;
        out32[wIdx + 5]  = (b1 + r5)  >>> 0;
        out32[wIdx + 6]  = (b2 + r6)  >>> 0;
        out32[wIdx + 7]  = (b3 + r7)  >>> 0;
        out32[wIdx + 8]  = ((a0 ^ b1) + r8)  >>> 0;
        out32[wIdx + 9]  = ((a1 ^ b2) + r9)  >>> 0;
        out32[wIdx + 10] = ((a2 ^ b3) + r10) >>> 0;
        out32[wIdx + 11] = ((a3 ^ b0) + r11) >>> 0;
        out32[wIdx + 12] = ((b0 + a1) ^ r12) >>> 0;
        out32[wIdx + 13] = ((b1 + a2) ^ r13) >>> 0;
        out32[wIdx + 14] = ((b2 + a3) ^ r14) >>> 0;
        out32[wIdx + 15] = ((b3 + a0) ^ r15) >>> 0;
  
        wIdx += 16;
        cLo = (cLo + 1) >>> 0;
        if (cLo === 0) cHi = (cHi + 1) >>> 0;
      }
  
      const remStart = wIdx << 2;
      if (remStart < byteLength) {
        const tailCtr = (BigInt(cHi >>> 0) << 32n) | BigInt(cLo >>> 0);
        const tailBlk = TwoTango4.keystream(r, 64, tailCtr, rounds);
        out.set(tailBlk.subarray(0, byteLength - remStart), remStart);
      }
  
      return out;
    }
  
    static async computeTag(root16, nonce24, aadBytes, ciphertext) {
      const authKeyBytes = TwoTango4.keystream(root16, 32, 0n, 8);
      const cryptoKey = await globalThis.crypto.subtle.importKey(
        "raw",
        authKeyBytes,
        { name: "HMAC", hash: "SHA-256" },
        false,
        ["sign"]
      );
      const msg = new Uint8Array(nonce24.length + aadBytes.length + ciphertext.length + 16);
      msg.set(nonce24, 0);
      msg.set(aadBytes, nonce24.length);
      msg.set(ciphertext, nonce24.length + aadBytes.length);
      const view = new DataView(msg.buffer);
      view.setUint32(msg.length - 16, aadBytes.length, true);
      view.setUint32(msg.length - 8, ciphertext.length, true);
      const sig = await globalThis.crypto.subtle.sign("HMAC", cryptoKey, msg);
      return new Uint8Array(sig);
    }
  
    static async encrypt(plaintext, key, nonce24 = TwoTango4.generateNonce(), aad = new Uint8Array(0)) {
      const ptBytes = plaintext instanceof Uint8Array ? plaintext : new TextEncoder().encode(String(plaintext));
      const keyBytes = key instanceof Uint8Array ? key : new TextEncoder().encode(String(key));
      const aadBytes = aad instanceof Uint8Array ? aad : new TextEncoder().encode(String(aad));
  
      const root16 = await TwoTango4.initState(keyBytes, nonce24);
      const ks = TwoTango4.keystream(root16, ptBytes.length, 1n, 8);
      const ciphertext = new Uint8Array(ptBytes.length);
      for (let i = 0; i < ptBytes.length; i++) {
        ciphertext[i] = ptBytes[i] ^ ks[i];
      }
      const tag = await TwoTango4.computeTag(root16, nonce24, aadBytes, ciphertext);
      return { nonce: nonce24, ciphertext, tag };
    }
  
    static async decrypt(ciphertextBytes, tagBytes, key, nonce24, aad = new Uint8Array(0)) {
      const keyBytes = key instanceof Uint8Array ? key : new TextEncoder().encode(String(key));
      const aadBytes = aad instanceof Uint8Array ? aad : new TextEncoder().encode(String(aad));
  
      const root16 = await TwoTango4.initState(keyBytes, nonce24);
      const expectedTag = await TwoTango4.computeTag(root16, nonce24, aadBytes, ciphertextBytes);
      let diff = 0;
      for (let i = 0; i < 32; i++) diff |= (expectedTag[i] ^ tagBytes[i]);
      if (diff !== 0) {
        throw new Error("2tango4 authentication failed: invalid key, nonce, AAD, or tampered ciphertext.");
      }
      const ks = TwoTango4.keystream(root16, ciphertextBytes.length, 1n, 8);
      const plaintext = new Uint8Array(ciphertextBytes.length);
      for (let i = 0; i < ciphertextBytes.length; i++) {
        plaintext[i] = ciphertextBytes[i] ^ ks[i];
      }
      return plaintext;
    }
  }
  
  if (typeof window !== "undefined") window.TwoTango4 = TwoTango4;
  export default TwoTango4;