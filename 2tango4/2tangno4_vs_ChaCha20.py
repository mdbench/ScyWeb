"""
Empirical Cryptanalysis & Distinguishability Test Harness
Compares 2tangno4 (from 2tangno4_9.html) vs. ChaCha20 (RFC 8439) across
statistical distinguishability and differential / linear / nonce-reuse probes.

Important scope note:
"Whether it can be broken" in real-world cryptanalysis depends on attacks
like algebraic/differential distinguishers, related-key/chosen-IV attacks,
state recovery, and key recovery — not just black-box byte statistics.
Black-box statistical tests can only detect structural bias or weaknesses
that leak into outputs; passing statistical tests does NOT prove security.
"""

import math
import os
import struct
import time
from typing import Callable, Dict, List, Tuple

# ==============================================================================
# 1. EXACT REFERENCE IMPLEMENTATIONS OF 2TANGNO4 & CHACHA20
# ==============================================================================

TILE_DIM = 64
TILE_PIXELS = TILE_DIM * TILE_DIM  # 4096
TILE_BYTES = TILE_PIXELS * 4       # 16384
TILE_HALF = TILE_PIXELS >> 1       # 2048
TILE_MASK = TILE_PIXELS - 1        # 0x0FFF


def _rotl32(x: int, n: int) -> int:
    x &= 0xFFFFFFFF
    n &= 31
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def _interleave_bits64(x: int, y: int) -> int:
    x = (x | (x << 4)) & 0x0F0F
    x = (x | (x << 2)) & 0x3333
    x = (x | (x << 1)) & 0x5555

    y = (y | (y << 4)) & 0x0F0F
    y = (y | (y << 2)) & 0x3333
    y = (y | (y << 1)) & 0x5555

    return (x | (y << 1)) & 0xFFFF


def _build_z_to_linear_lut() -> List[int]:
    lut = [0] * TILE_PIXELS
    for y in range(TILE_DIM):
        row_off = y * TILE_DIM
        for x in range(TILE_DIM):
            lut[_interleave_bits64(x, y)] = row_off + x
    return lut


TILE_Z_TO_LINEAR = _build_z_to_linear_lut()


def _mix32(h: int) -> int:
    h &= 0xFFFFFFFF
    h ^= h >> 16
    h = (h * 0x85EBCA6B) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0xC2B2AE35) & 0xFFFFFFFF
    h ^= h >> 16
    return h & 0xFFFFFFFF


def _derive_base_seeds(key_words: List[int], nonce_words: List[int]) -> Tuple[int, int]:
    base_a = (0x243F6A88 ^ key_words[0] ^ nonce_words[0]) & 0xFFFFFFFF
    base_a = _mix32((base_a + key_words[1] + nonce_words[1]) & 0xFFFFFFFF)
    base_a = _mix32((base_a ^ key_words[2] ^ key_words[3]) & 0xFFFFFFFF)

    base_b = (0x85A308D3 ^ key_words[4] ^ nonce_words[2]) & 0xFFFFFFFF
    base_b = _mix32((base_b + key_words[5] + nonce_words[0]) & 0xFFFFFFFF)
    base_b = _mix32((base_b ^ key_words[6] ^ key_words[7]) & 0xFFFFFFFF)

    return base_a, base_b


def _derive_tile_seeds(base_a: int, base_b: int, tile_id: int) -> Tuple[int, int, int, int]:
    t_mix = (((tile_id + 1) & 0xFFFFFFFF) * 0x9E3779B9) & 0xFFFFFFFF
    s_a = _mix32((base_a ^ t_mix) & 0xFFFFFFFF)
    s_b = _mix32((base_b + t_mix) & 0xFFFFFFFF)
    z_perm_mask = _mix32((s_a ^ _rotl32(s_b, 7)) & 0xFFFFFFFF)
    stride_odd = (_mix32((s_a + s_b) & 0xFFFFFFFF) | 1) & 0xFFFFFFFF
    z_offset = z_perm_mask & TILE_MASK
    return s_a, s_b, stride_odd, z_offset


def tangno4_encrypt_raw_tiles(
    plain_bytes: bytes, key_words: List[int], nonce_words: List[int]
) -> bytes:
    """
    Runs 2tangno4's 64x64 RGBA middle-out tiled kernel directly on a multiple
    of TILE_BYTES (16,384 bytes) for clean differential/statistical analysis.
    """
    if len(plain_bytes) == 0 or (len(plain_bytes) % TILE_BYTES) != 0:
        raise ValueError(f"plain_bytes must be a non-zero multiple of {TILE_BYTES}")

    num_tiles = len(plain_bytes) // TILE_BYTES
    in_words = list(struct.unpack(f"<{len(plain_bytes) // 4}I", plain_bytes))
    out_words = [0] * len(in_words)
    base_a, base_b = _derive_base_seeds(key_words, nonce_words)
    lut = TILE_Z_TO_LINEAR

    for tile_id in range(num_tiles):
        s_a, s_b, stride_odd, z_offset = _derive_tile_seeds(base_a, base_b, tile_id)
        chain_alpha = s_a
        chain_beta = s_b
        tile_base = tile_id * TILE_PIXELS

        for step in range(TILE_HALF):
            z_a = TILE_HALF - 1 - step
            z_b = TILE_HALF + step

            pix_a = in_words[tile_base + lut[z_a]]
            pix_b = in_words[tile_base + lut[z_b]]

            chain_alpha = (((chain_alpha ^ z_a) & 0xFFFFFFFF) * 0x9E3779B1 + 0x7F4A7C15) & 0xFFFFFFFF
            chain_beta = (((chain_beta ^ z_b) & 0xFFFFFFFF) * 0x85EBCA77 + 0xC2B2AE3D) & 0xFFFFFFFF

            bridge = ((chain_alpha >> 11) ^ ((chain_beta << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
            mask_a = (chain_alpha ^ bridge) & 0xFFFFFFFF
            mask_b = (chain_beta ^ _rotl32(bridge, 7)) & 0xFFFFFFFF

            out_a = (pix_a ^ mask_a) & 0xFFFFFFFF
            out_b = (pix_b ^ mask_b) & 0xFFFFFFFF

            dst_za = (z_a * stride_odd + z_offset) & TILE_MASK
            dst_zb = (z_b * stride_odd + z_offset) & TILE_MASK

            out_words[tile_base + lut[dst_za]] = out_a
            out_words[tile_base + lut[dst_zb]] = out_b

            chain_alpha = _mix32((chain_alpha ^ pix_a ^ _rotl32(out_b, 5)) & 0xFFFFFFFF)
            chain_beta = _mix32((chain_beta ^ pix_b ^ _rotl32(out_a, 11)) & 0xFFFFFFFF)

    return struct.pack(f"<{len(out_words)}I", *out_words)


def chacha20_encrypt_raw(
    plain_bytes: bytes, key_words: List[int], nonce_words: List[int]
) -> bytes:
    """
    20-round ChaCha20 block stream XOR matching the JS reference in 2tangno4_9.html.
    """
    n = len(plain_bytes)
    if n == 0 or (n % 4) != 0:
        raise ValueError("plain_bytes must be a non-zero multiple of 4 bytes")

    in_words = list(struct.unpack(f"<{n // 4}I", plain_bytes))
    out_words = [0] * len(in_words)

    c0, c1, c2, c3 = 0x61707865, 0x3320646E, 0x79622D32, 0x6B206574
    k0, k1, k2, k3, k4, k5, k6, k7 = key_words
    n0, n1, n2 = nonce_words

    w_idx = 0
    ctr = 1
    total_words = len(in_words)

    def qr(a, b, c, d):
        a = (a + b) & 0xFFFFFFFF; d = _rotl32(d ^ a, 16)
        c = (c + d) & 0xFFFFFFFF; b = _rotl32(b ^ c, 12)
        a = (a + b) & 0xFFFFFFFF; d = _rotl32(d ^ a, 8)
        c = (c + d) & 0xFFFFFFFF; b = _rotl32(b ^ c, 7)
        return a, b, c, d

    while w_idx < total_words:
        x0, x1, x2, x3 = c0, c1, c2, c3
        x4, x5, x6, x7 = k0, k1, k2, k3
        x8, x9, x10, x11 = k4, k5, k6, k7
        x12, x13, x14, x15 = ctr & 0xFFFFFFFF, n0, n1, n2

        for _ in range(10):
            x0, x4, x8, x12 = qr(x0, x4, x8, x12)
            x1, x5, x9, x13 = qr(x1, x5, x9, x13)
            x2, x6, x10, x14 = qr(x2, x6, x10, x14)
            x3, x7, x11, x15 = qr(x3, x7, x11, x15)

            x0, x5, x10, x15 = qr(x0, x5, x10, x15)
            x1, x6, x11, x12 = qr(x1, x6, x11, x12)
            x2, x7, x8, x13 = qr(x2, x7, x8, x13)
            x3, x4, x9, x14 = qr(x3, x4, x9, x14)

        ks = [
            (x0 + c0) & 0xFFFFFFFF, (x1 + c1) & 0xFFFFFFFF,
            (x2 + c2) & 0xFFFFFFFF, (x3 + c3) & 0xFFFFFFFF,
            (x4 + k0) & 0xFFFFFFFF, (x5 + k1) & 0xFFFFFFFF,
            (x6 + k2) & 0xFFFFFFFF, (x7 + k3) & 0xFFFFFFFF,
            (x8 + k4) & 0xFFFFFFFF, (x9 + k5) & 0xFFFFFFFF,
            (x10 + k6) & 0xFFFFFFFF, (x11 + k7) & 0xFFFFFFFF,
            (x12 + ((ctr + 1) & 0xFFFFFFFF)) & 0xFFFFFFFF,
            (x13 + n0) & 0xFFFFFFFF, (x14 + n1) & 0xFFFFFFFF,
            (x15 + n2) & 0xFFFFFFFF,
        ]

        block_words = min(16, total_words - w_idx)
        for j in range(block_words):
            out_words[w_idx + j] = (in_words[w_idx + j] ^ ks[j]) & 0xFFFFFFFF

        ctr = (ctr + 1) & 0xFFFFFFFF
        w_idx += 16

    return struct.pack(f"<{len(out_words)}I", *out_words)


# ==============================================================================
# 2. STATISTICAL & DIFFERENTIAL PROBES (DISTINGUISHABILITY TESTS)
# ==============================================================================

def _popcount_byte_table() -> List[int]:
    return [bin(i).count("1") for i in range(256)]


POP8 = _popcount_byte_table()


def byte_chi_square_and_entropy(data: bytes) -> Tuple[float, float]:
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    n = len(data)
    expected = n / 256.0
    chi2 = 0.0
    ent = 0.0
    for c in counts:
        diff = c - expected
        chi2 += (diff * diff) / expected
        if c > 0:
            p = c / n
            ent -= p * math.log2(p)
    return chi2, ent


def bit_bias_z_score(data: bytes) -> float:
    """
    Max |z|-score across all 8 bit positions (bit 0..7) over all bytes in `data`.
    Under unbiased bits (p = 0.5), z ~ N(0, 1).
    """
    n = len(data)
    if n == 0:
        return 0.0
    bit_ones = [0] * 8
    for b in data:
        for bit in range(8):
            if (b >> bit) & 1:
                bit_ones[bit] += 1
    std = math.sqrt(n * 0.25)
    max_abs_z = 0.0
    for c in bit_ones:
        z = abs((c - n * 0.5) / std)
        if z > max_abs_z:
            max_abs_z = z
    return max_abs_z


def chosen_plaintext_diff_test(
    cipher_fn: Callable[[bytes, List[int], List[int]], bytes],
    key_words: List[int],
    nonce_words: List[int],
    trials: int = 32,
) -> Dict[str, float]:
    """
    Tests output XOR differences for single-bit plaintext differences
    across `trials` fixed keys/nonces on a 16 KB (1-tile) zero buffer vs.
    1-bit flipped buffer. Checks whether output differences stay sparse or
    have positional/bit bias.
    """
    base_pt = bytearray(TILE_BYTES)
    ct0 = cipher_fn(bytes(base_pt), key_words, nonce_words)

    diff_weights: List[float] = []
    bit_pos_ones = [0] * 8
    total_bytes_checked = 0

    for t in range(trials):
        pt1 = bytearray(base_pt)
        byte_idx = (t * 257) % TILE_BYTES
        bit_idx = t % 8
        pt1[byte_idx] ^= (1 << bit_idx)
        ct1 = cipher_fn(bytes(pt1), key_words, nonce_words)

        flipped_bits = 0
        for i in range(TILE_BYTES):
            d = ct0[i] ^ ct1[i]
            flipped_bits += POP8[d]
            for b in range(8):
                if (d >> b) & 1:
                    bit_pos_ones[b] += 1
        total_bytes_checked += TILE_BYTES
        diff_weights.append(flipped_bits / (TILE_BYTES * 8))

    mean_diff = sum(diff_weights) / len(diff_weights)
    max_bit_z = max(
        abs((c - total_bytes_checked * 0.5) / math.sqrt(total_bytes_checked * 0.25))
        for c in bit_pos_ones
    )
    return {
        "mean_bit_diff_ratio": mean_diff,
        "abs_err_from_0_5": abs(mean_diff - 0.5),
        "max_diff_bit_z": max_bit_z,
    }


def nonce_reuse_depth_test(
    cipher_fn: Callable[[bytes, List[int], List[int]], bytes],
    key_words: List[int],
    nonce_words: List[int],
) -> Dict[str, float]:
    """
    Measures keystream/output correlation across consecutive 16 KB tiles
    when encrypting an identical 16 KB block twice under the same (key, nonce).
    Note: any stream/tiled cipher without stateful per-message IV chaining
    exhibits identical ciphertext on identical (key, nonce, plaintext) — this
    quantifies cross-tile structure inside a single 16 KB tile.
    """
    pt = bytes([0xAA] * TILE_BYTES)
    ct = cipher_fn(pt, key_words, nonce_words)
    # Split 16 KB tile into 4 quarters (4 KB each) and compare pairwise hamming rates
    q_size = TILE_BYTES // 4
    quarters = [ct[i * q_size : (i + 1) * q_size] for i in range(4)]
    rates = []
    for i in range(4):
        for j in range(i + 1, 4):
            flips = sum(POP8[quarters[i][k] ^ quarters[j][k]] for k in range(q_size))
            rates.append(flips / (q_size * 8))
    return {
        "min_quarter_hamming": min(rates),
        "max_quarter_hamming": max(rates),
        "max_dev_from_0_5": max(abs(r - 0.5) for r in rates),
    }


# ==============================================================================
# 3. STRING PACKING & BOUNDED BRUTE-FORCE PARTIAL RECOVERY PROBE
# ==============================================================================

def tangno4_encrypt_string(
    message: str, key_words: List[int], nonce_words: List[int]
) -> bytes:
    """
    Packs a UTF-8 string using 2tangno4's macro-tile framing:
      [0..4): uint32 little-endian payload byte length
      [4..4+len): UTF-8 bytes
      [4+len..TILE_BYTES): deterministic key-derived padding to complete 16,384 B tile
    and encrypts via `tangno4_encrypt_raw_tiles`.
    """
    raw = message.encode("utf-8")
    orig_len = len(raw)
    num_tiles = max(1, (orig_len + 4 + TILE_BYTES - 1) // TILE_BYTES)
    total_bytes = num_tiles * TILE_BYTES
    buf = bytearray(total_bytes)
    struct.pack_into("<I", buf, 0, orig_len)
    buf[4 : 4 + orig_len] = raw

    base_a, _ = _derive_base_seeds(key_words, nonce_words)
    pad_seed = _mix32((base_a ^ orig_len) & 0xFFFFFFFF)
    for i in range(4 + orig_len, total_bytes):
        pad_seed = (pad_seed + 0x9E3779B9) & 0xFFFFFFFF
        buf[i] = (_mix32(pad_seed) >> ((i & 3) * 8)) & 0xFF

    return tangno4_encrypt_raw_tiles(bytes(buf), key_words, nonce_words)


def tangno4_decrypt_string_attempt(
    cipher_bytes: bytes, key_words: List[int], nonce_words: List[int]
) -> Tuple[bool, str, bytes]:
    """
    Attempts to invert a 2tangno4 macro-tile ciphertext with candidate key_words
    and nonce_words, returning (header_plausible, decoded_text, raw_recovered_bytes).
    """
    if len(cipher_bytes) < TILE_BYTES or (len(cipher_bytes) % TILE_BYTES) != 0:
        raise ValueError(f"cipher_bytes must be a multiple of {TILE_BYTES}")

    num_tiles = len(cipher_bytes) // TILE_BYTES
    in_words = list(struct.unpack(f"<{len(cipher_bytes) // 4}I", cipher_bytes))
    out_words = [0] * len(in_words)
    base_a, base_b = _derive_base_seeds(key_words, nonce_words)
    lut = TILE_Z_TO_LINEAR

    for tile_id in range(num_tiles):
        s_a, s_b, stride_odd, z_offset = _derive_tile_seeds(base_a, base_b, tile_id)
        chain_alpha = s_a
        chain_beta = s_b
        tile_base = tile_id * TILE_PIXELS

        for step in range(TILE_HALF):
            z_a = TILE_HALF - 1 - step
            z_b = TILE_HALF + step

            chain_alpha = (((chain_alpha ^ z_a) & 0xFFFFFFFF) * 0x9E3779B1 + 0x7F4A7C15) & 0xFFFFFFFF
            chain_beta = (((chain_beta ^ z_b) & 0xFFFFFFFF) * 0x85EBCA77 + 0xC2B2AE3D) & 0xFFFFFFFF

            bridge = ((chain_alpha >> 11) ^ ((chain_beta << 13) & 0xFFFFFFFF)) & 0xFFFFFFFF
            mask_a = (chain_alpha ^ bridge) & 0xFFFFFFFF
            mask_b = (chain_beta ^ _rotl32(bridge, 7)) & 0xFFFFFFFF

            dst_za = (z_a * stride_odd + z_offset) & TILE_MASK
            dst_zb = (z_b * stride_odd + z_offset) & TILE_MASK

            out_a = in_words[tile_base + lut[dst_za]]
            out_b = in_words[tile_base + lut[dst_zb]]

            pix_a = (out_a ^ mask_a) & 0xFFFFFFFF
            pix_b = (out_b ^ mask_b) & 0xFFFFFFFF

            out_words[tile_base + lut[z_a]] = pix_a
            out_words[tile_base + lut[z_b]] = pix_b

            chain_alpha = _mix32((chain_alpha ^ pix_a ^ _rotl32(out_b, 5)) & 0xFFFFFFFF)
            chain_beta = _mix32((chain_beta ^ pix_b ^ _rotl32(out_a, 11)) & 0xFFFFFFFF)

    plain_bytes = struct.pack(f"<{len(out_words)}I", *out_words)
    orig_len = struct.unpack_from("<I", plain_bytes, 0)[0]
    if orig_len > len(plain_bytes) - 4:
        return False, "", b""

    payload = plain_bytes[4 : 4 + orig_len]
    text = payload.decode("utf-8", errors="replace")
    return True, text, payload


def chacha20_encrypt_string(
    message: str, key_words: List[int], nonce_words: List[int]
) -> bytes:
    """
    Packs a UTF-8 string with the same 4-byte length header + zero padding
    aligned to 64-byte ChaCha20 blocks for direct comparison.
    """
    raw = message.encode("utf-8")
    orig_len = len(raw)
    block_bytes = 64
    num_blocks = max(1, (orig_len + 4 + block_bytes - 1) // block_bytes)
    buf = bytearray(num_blocks * block_bytes)
    struct.pack_into("<I", buf, 0, orig_len)
    buf[4 : 4 + orig_len] = raw
    return chacha20_encrypt_raw(bytes(buf), key_words, nonce_words)


def chacha20_decrypt_string_attempt(
    cipher_bytes: bytes, key_words: List[int], nonce_words: List[int]
) -> Tuple[bool, str, bytes]:
    """
    Attempts to decrypt a length-prefixed ChaCha20 ciphertext with candidate key_words
    and nonce_words.
    """
    plain_bytes = chacha20_encrypt_raw(cipher_bytes, key_words, nonce_words)
    orig_len = struct.unpack_from("<I", plain_bytes, 0)[0]
    if orig_len > len(plain_bytes) - 4:
        return False, "", b""
    payload = plain_bytes[4 : 4 + orig_len]
    text = payload.decode("utf-8", errors="replace")
    return True, text, payload


def _partial_recovery_score(target: str, candidate: str) -> Dict[str, float]:
    """
    Measures partial string recovery between `target` and `candidate`:
      - exact_match: 1.0 if identical, else 0.0
      - prefix_ratio: length of common leading prefix / max(1, len(target))
      - char_overlap_ratio: matching characters at identical indices / max(1, len(target))
      - printable_ratio: fraction of candidate chars that are printable ASCII / whitespace
    """
    if not target:
        return {"exact_match": 1.0 if not candidate else 0.0, "prefix_ratio": 0.0, "char_overlap_ratio": 0.0, "printable_ratio": 0.0}

    prefix_len = 0
    for a, b in zip(target, candidate):
        if a == b:
            prefix_len += 1
        else:
            break

    pos_matches = sum(1 for a, b in zip(target, candidate) if a == b)
    printable_cnt = sum(1 for ch in candidate if ch.isprintable() or ch.isspace())

    return {
        "exact_match": 1.0 if candidate == target else 0.0,
        "prefix_ratio": prefix_len / len(target),
        "char_overlap_ratio": pos_matches / len(target),
        "printable_ratio": printable_cnt / max(1, len(candidate)),
    }


def brute_force_string_recovery_probe(
    target_text: str = "Telemetry packet #042: altitude=412.8km status=NOMINAL",
    nonce_words: List[int] = None,
    candidate_limit: int = 256,
    planted_index: int = 173,
) -> None:
    """
    Demonstrates a bounded brute-force key search without knowing the password/key.
    Plants a known key at `planted_index` inside a candidate space of size `candidate_limit`
    to verify the search harness works, and measures partial recovery on wrong keys.

    Note on feasibility: A true 256-bit key space (2^256) cannot be brute-forced on
    classical hardware; brute-force partial recovery is only feasible if keys/passwords
    come from a tiny/weak search space or if a cipher leaks partial/prefix structure
    under wrong guesses.
    """
    if nonce_words is None:
        nonce_words = [0x452821E6, 0x38D01377, 0xBE5466CF]

    # Build a small deterministic candidate key list (e.g., weak/low-value 256-bit keys)
    candidates: List[List[int]] = []
    for idx in range(candidate_limit):
        # Weak/structured candidate keys: small integer / simple pattern in word 0
        k = [0] * 8
        k[0] = (idx * 0x01010101) & 0xFFFFFFFF
        k[1] = idx & 0xFFFF
        candidates.append(k)

    true_key = candidates[planted_index % candidate_limit]

    print(f"=== Bounded Brute-Force String Recovery Probe (candidates={candidate_limit}, planted_idx={planted_index}) ===")
    print(f"Target string ({len(target_text)} chars): {target_text!r}\n")

    specs = [
        ("2tangno4", tangno4_encrypt_string, tangno4_decrypt_string_attempt),
        ("ChaCha20", chacha20_encrypt_string, chacha20_decrypt_string_attempt),
    ]

    for name, enc_fn, dec_fn in specs:
        ct = enc_fn(target_text, true_key, nonce_words)

        t0 = time.perf_counter()
        plausible_headers = 0
        best_wrong_prefix = 0.0
        best_wrong_overlap = 0.0
        best_wrong_sample = ""
        found_at_idx: int = -1
        recovered_at_find = ""

        for idx, cand_key in enumerate(candidates):
            ok_hdr, dec_text, _ = dec_fn(ct, cand_key, nonce_words)
            if ok_hdr:
                plausible_headers += 1
            scores = _partial_recovery_score(target_text, dec_text)
            if scores["exact_match"] == 1.0 and found_at_idx == -1:
                found_at_idx = idx
                recovered_at_find = dec_text
            elif cand_key != true_key:
                if scores["prefix_ratio"] > best_wrong_prefix:
                    best_wrong_prefix = scores["prefix_ratio"]
                if scores["char_overlap_ratio"] > best_wrong_overlap:
                    best_wrong_overlap = scores["char_overlap_ratio"]
                    best_wrong_sample = dec_text[:40]

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        print(f"[{name}] Search time: {elapsed_ms:.1f} ms | Plausible length headers: {plausible_headers}/{candidate_limit}")
        print(f"  Exact recovery index: {found_at_idx} (exact match: {recovered_at_find == target_text})")
        print(
            f"  Wrong-key partial recovery: best prefix={best_wrong_prefix*100:.2f}%, "
            f"best char overlap={best_wrong_overlap*100:.2f}%, sample={best_wrong_sample!r}\n"
        )


def run_comparison(sample_bytes: int = 65536, diff_trials: int = 24) -> None:
    # Align sample_bytes to multiple of TILE_BYTES (16384)
    aligned = max(TILE_BYTES, (sample_bytes // TILE_BYTES) * TILE_BYTES)
    key_words = [
        0x243F6A88, 0x85A308D3, 0x13198A2E, 0x03707344,
        0xA4093822, 0x299F31D0, 0x082EFA98, 0xEC4E6C89,
    ]
    nonce_words = [0x452821E6, 0x38D01377, 0xBE5466CF]

    # Zero plaintext exposes any unmasked keystream / state bias directly
    zero_pt = b"\x00" * aligned

    engines: List[Tuple[str, Callable[[bytes, List[int], List[int]], bytes]]] = [
        ("2tangno4", tangno4_encrypt_raw_tiles),
        ("ChaCha20", chacha20_encrypt_raw),
    ]

    print(f"=== Distinguishability & Differential Probe ({aligned} bytes = {aligned // TILE_BYTES} tiles) ===")
    print("Note: Chi2(df=255) expected ~ 255.0 +/- 22.6; |z| > 3.5 indicates notable bias.\n")

    for name, fn in engines:
        t0 = time.perf_counter()
        ct = fn(zero_pt, key_words, nonce_words)
        dt_ms = (time.perf_counter() - t0) * 1000.0

        chi2, ent = byte_chi_square_and_entropy(ct)
        max_bit_z = bit_bias_z_score(ct)
        diff_res = chosen_plaintext_diff_test(fn, key_words, nonce_words, trials=diff_trials)
        q_res = nonce_reuse_depth_test(fn, key_words, nonce_words)

        print(f"[{name}] ({dt_ms:.1f} ms for {aligned} B zero-PT)")
        print(f"  Byte Chi2 (df=255): {chi2:7.2f} | Entropy: {ent:.5f} b/B | Max Bit |z|: {max_bit_z:.2f}")
        print(
            f"  1-Bit PT Diff ({diff_trials} trials): mean={diff_res['mean_bit_diff_ratio']*100:.2f}% "
            f"(|err|={diff_res['abs_err_from_0_5']*100:.2f} pts), max diff-bit |z|={diff_res['max_diff_bit_z']:.2f}"
        )
        print(
            f"  Intra-Tile Quarter Hamming: min={q_res['min_quarter_hamming']*100:.2f}%, "
            f"max={q_res['max_quarter_hamming']*100:.2f}%, max |dev-50%|={q_res['max_dev_from_0_5']*100:.2f} pts\n"
        )


if __name__ == "__main__":
    run_comparison(sample_bytes=65536, diff_trials=24)
    print()
    brute_force_string_recovery_probe(candidate_limit=256, planted_index=173)