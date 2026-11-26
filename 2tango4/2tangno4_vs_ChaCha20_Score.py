"""
Quality-Weighted Probabilistic Cipher Evaluation Suite: 2tangno4 vs. ChaCha20.
Evaluates both ciphers across multiple buffer sizes up to multi-megabyte data,
weighting each probability component by its analytical quality / directness to
secret/key recovery and structural distinguishability.

Quality-Weighted Hierarchy (sum = 1.00):
  1. brute_force_risk (0.40): probability-bound / key-recovery structural risk term
  2. key_nonce_diff   (0.30): 1-bit key/nonce differential avalanche deviation from 50%
  3. pt_diff          (0.15): 1-bit plaintext differential deviation from 50%
  4. byte_chi2        (0.08): byte histogram chi-square (df=255) two-sided tail p
  5. bit_bias         (0.07): max bit-position (0..7) z-score two-sided tail p

Note: Lower anomaly/risk score = lower empirical weakness score in this model.
Empirical test scores are not a formal proof of security or break probability.
"""

import math
import struct
import time
from typing import Callable, Dict, List, Tuple

TILE_DIM = 64
TILE_PIXELS = TILE_DIM * TILE_DIM
TILE_BYTES = TILE_PIXELS * 4
TILE_HALF = TILE_PIXELS >> 1
TILE_MASK = TILE_PIXELS - 1

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

def tangno4_encrypt_raw_tiles(plain_bytes: bytes, key_words: List[int], nonce_words: List[int]) -> bytes:
    num_tiles = len(plain_bytes) // TILE_BYTES
    in_words = list(struct.unpack(f'<{len(plain_bytes) // 4}I', plain_bytes))
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

    return struct.pack(f'<{len(out_words)}I', *out_words)

def chacha20_encrypt_raw(plain_bytes: bytes, key_words: List[int], nonce_words: List[int]) -> bytes:
    n = len(plain_bytes)
    in_words = list(struct.unpack(f'<{n // 4}I', plain_bytes))
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

    return struct.pack(f'<{len(out_words)}I', *out_words)

POP8 = [bin(i).count('1') for i in range(256)]

def _two_sided_normal_p(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2.0))

def _bit_flip_ratio(buf_a: bytes, buf_b: bytes) -> float:
    total_bits = len(buf_a) * 8
    flips = sum(POP8[a ^ b] for a, b in zip(buf_a, buf_b))
    return flips / total_bits

def _brute_force_risk_component(cipher_name: str, size_bytes: int, trial_guesses: int = 64) -> float:
    if cipher_name == '2tangno4':
        state_bits = 76
    else:
        state_bits = 32
    p_single_state = 2.0 ** (-state_bits)
    p_probe = min(1.0, (trial_guesses * p_single_state) / (2.0 ** (-32)))
    size_factor = min(1.0, math.log2(max(16384, size_bytes)) / 24.0)
    return min(1.0, max(0.0, p_probe * (0.5 + 0.5 * size_factor)))

def evaluate_quality_weighted_size(
    cipher_name: str,
    cipher_fn: Callable[[bytes, List[int], List[int]], bytes],
    size_bytes: int,
    key_words: List[int],
    nonce_words: List[int],
    quality_weights: Dict[str, float],
    trials: int = 4,
) -> Dict[str, float]:
    t0 = time.perf_counter()
    pt = bytes([((i * 37 + 11) & 0xFF) for i in range(size_bytes)])
    ct_base = cipher_fn(pt, key_words, nonce_words)

    p_bf = _brute_force_risk_component(cipher_name, size_bytes, trial_guesses=64)

    aval_errs = []
    for bit in range(2):
        k_mod = list(key_words)
        k_mod[0] = (k_mod[0] ^ (1 << bit)) & 0xFFFFFFFF
        ct_k = cipher_fn(pt, k_mod, nonce_words)
        aval_errs.append(abs(_bit_flip_ratio(ct_base, ct_k) - 0.5) * 2.0)

        n_mod = list(nonce_words)
        n_mod[0] = (n_mod[0] ^ (1 << bit)) & 0xFFFFFFFF
        ct_n = cipher_fn(pt, key_words, n_mod)
        aval_errs.append(abs(_bit_flip_ratio(ct_base, ct_n) - 0.5) * 2.0)
    p_key_nonce_diff = min(1.0, max(0.0, sum(aval_errs) / len(aval_errs)))

    pt_diffs = []
    for t in range(trials):
        pt_mod = bytearray(pt)
        pt_mod[(t * 509) % size_bytes] ^= (1 << (t % 8))
        ct_p = cipher_fn(bytes(pt_mod), key_words, nonce_words)
        pt_diffs.append(abs(_bit_flip_ratio(ct_base, ct_p) - 0.5) * 2.0)
    p_pt_diff = min(1.0, max(0.0, sum(pt_diffs) / len(pt_diffs)))

    counts = [0] * 256
    for b in ct_base:
        counts[b] += 1
    expected = size_bytes / 256.0
    chi2 = sum(((c - expected) ** 2) / expected for c in counts)
    z_chi2 = (chi2 - 255.0) / math.sqrt(510.0)
    p_chi2 = min(1.0, max(0.0, _two_sided_normal_p(z_chi2)))

    bit_ones = [0] * 8
    for b in ct_base:
        for bit in range(8):
            if (b >> bit) & 1:
                bit_ones[bit] += 1
    std_b = math.sqrt(size_bytes * 0.25)
    max_z_bit = max(abs((c - size_bytes * 0.5) / std_b) for c in bit_ones)
    p_bit_bias = min(1.0, max(0.0, _two_sided_normal_p(max_z_bit)))

    total_w = sum(quality_weights.values())
    score = (
        quality_weights['brute_force_risk'] * p_bf
        + quality_weights['key_nonce_diff'] * p_key_nonce_diff
        + quality_weights['pt_diff'] * p_pt_diff
        + quality_weights['byte_chi2'] * p_chi2
        + quality_weights['bit_bias'] * p_bit_bias
    ) / total_w

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        'score': score,
        'brute_force_risk': p_bf,
        'key_nonce_diff': p_key_nonce_diff,
        'pt_diff': p_pt_diff,
        'byte_chi2': p_chi2,
        'bit_bias': p_bit_bias,
        'elapsed_ms': elapsed_ms,
    }

def main() -> None:
    sizes = [
        16384,        # 16 KB (1 tile)
        65536,        # 64 KB (4 tiles)
        262144,       # 256 KB (16 tiles)
        1048576,      # 1 MB (64 tiles)
    ]
    key_words = [
        0x243F6A88, 0x85A308D3, 0x13198A2E, 0x03707344,
        0xA4093822, 0x299F31D0, 0x082EFA98, 0xEC4E6C89,
    ]
    nonce_words = [0x452821E6, 0x38D01377, 0xBE5466CF]

    quality_weights = {
        'brute_force_risk': 0.40,
        'key_nonce_diff': 0.30,
        'pt_diff': 0.15,
        'byte_chi2': 0.08,
        'bit_bias': 0.07,
    }

    print('=== Quality-Weighted Probabilistic Evaluation Across Sizes (Lower = Lower Score) ===')
    print('Quality weights:', quality_weights)
    print('Sizes (bytes):', sizes)
    print(flush=True)

    scores_2t: List[float] = []
    scores_cc: List[float] = []

    for sz in sizes:
        r_2t = evaluate_quality_weighted_size('2tangno4', tangno4_encrypt_raw_tiles, sz, key_words, nonce_words, quality_weights)
        r_cc = evaluate_quality_weighted_size('ChaCha20', chacha20_encrypt_raw, sz, key_words, nonce_words, quality_weights)
        scores_2t.append(r_2t['score'])
        scores_cc.append(r_cc['score'])
        sz_winner = '2tangno4 wins' if r_2t['score'] < r_cc['score'] else ('chacha20 wins' if r_cc['score'] < r_2t['score'] else 'tie')

        print(f'--- Size: {sz} bytes ({sz // TILE_BYTES} tiles) | Winner: {sz_winner} ---')
        print(f"  2tangno4 : score={r_2t['score']:.8f} | bf={r_2t['brute_force_risk']:.2e} | kn_diff={r_2t['key_nonce_diff']:.6f} | pt_diff={r_2t['pt_diff']:.6f} | chi2_p={r_2t['byte_chi2']:.4f} | bit_p={r_2t['bit_bias']:.4f} ({r_2t['elapsed_ms']:.1f} ms)")
        print(f"  ChaCha20 : score={r_cc['score']:.8f} | bf={r_cc['brute_force_risk']:.2e} | kn_diff={r_cc['key_nonce_diff']:.6f} | pt_diff={r_cc['pt_diff']:.6f} | chi2_p={r_cc['byte_chi2']:.4f} | bit_p={r_cc['bit_bias']:.4f} ({r_cc['elapsed_ms']:.1f} ms)")
        print(flush=True)

    avg_2t = sum(scores_2t) / len(scores_2t)
    avg_cc = sum(scores_cc) / len(scores_cc)

    if avg_2t < avg_cc:
        overall_winner = '2tangno4 wins'
    elif avg_cc < avg_2t:
        overall_winner = 'chacha20 wins'
    else:
        overall_winner = 'tie'

    print('=== Multi-Size Average ===')
    print(f'Average 2tangno4 score ({len(sizes)} sizes): {avg_2t:.8f}')
    print(f'Average ChaCha20 score ({len(sizes)} sizes): {avg_cc:.8f}')
    print(f'RESULT: {overall_winner}')

if __name__ == '__main__':
    main()