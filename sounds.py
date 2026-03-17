import array
import math
import random

import numpy as np
import pygame
from scipy.signal import butter, sosfilt, fftconvolve

SAMPLE_RATE = 44100


# ─── Core helpers ──────────────────────────────────────────────────────


def _make_sound(samples):
    buf = array.array("h", samples)
    sound = pygame.mixer.Sound(buffer=buf)
    return sound


def _make_sound_stereo(np_stereo):
    """Create a pygame Sound from a (2, N) float64 stereo numpy array.

    Interleaves L/R channels into int16 buffer expected by pygame mixer
    in stereo mode (channels=2).
    """
    stereo = np.clip(np_stereo, -1.0, 1.0)
    left = (stereo[0] * 32767).astype(np.int16)
    right = (stereo[1] * 32767).astype(np.int16)
    interleaved = np.empty(left.size + right.size, dtype=np.int16)
    interleaved[0::2] = left
    interleaved[1::2] = right
    return pygame.mixer.Sound(buffer=interleaved.tobytes())


def _mono_to_stereo(mono_sound):
    """Convert a mono pygame.mixer.Sound to stereo by duplicating the channel."""
    raw = mono_sound.get_raw()
    mono = np.frombuffer(raw, dtype=np.int16)
    stereo = np.empty(mono.size * 2, dtype=np.int16)
    stereo[0::2] = mono
    stereo[1::2] = mono
    return pygame.mixer.Sound(buffer=stereo.tobytes())


# ─── Original mono synthesis primitives (kept for SFX) ────────────────


def _square_wave(frequency, duration_ms, volume=0.4):
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    period = SAMPLE_RATE / frequency
    peak = int(32767 * volume)
    samples = []
    for i in range(num_samples):
        samples.append(peak if (i % period) < (period / 2) else -peak)
    return samples


def _noise_burst(duration_ms, volume=0.3):
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(32767 * volume)
    samples = []
    for i in range(num_samples):
        fade = 1.0 - i / num_samples
        samples.append(int(random.randint(-peak, peak) * fade))
    return samples


def _descending_tone(start_freq, end_freq, duration_ms, volume=0.35):
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(32767 * volume)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        progress = i / num_samples
        freq = start_freq + (end_freq - start_freq) * progress
        fade = 1.0 - progress
        samples.append(int(peak * fade * math.sin(2 * math.pi * freq * t)))
    return samples


def _ascending_tone(start_freq, end_freq, duration_ms, volume=0.35):
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(32767 * volume)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        progress = i / num_samples
        freq = start_freq + (end_freq - start_freq) * progress
        fade = 1.0 - progress
        samples.append(int(peak * fade * math.sin(2 * math.pi * freq * t)))
    return samples


def _silence(duration_ms):
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    return [0] * num_samples


def _note(frequency, duration_ms, volume=0.25):
    """Square wave note with a quick fade-out envelope for punchy 8-bit feel."""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    period = SAMPLE_RATE / frequency
    peak = int(32767 * volume)
    attack = int(SAMPLE_RATE * 5 / 1000)
    release = int(num_samples * 0.3)
    samples = []
    for i in range(num_samples):
        wave = peak if (i % period) < (period / 2) else -peak
        if i < attack:
            env = i / attack
        elif i > num_samples - release:
            env = (num_samples - i) / release
        else:
            env = 1.0
        samples.append(int(wave * env))
    return samples


def _bass_note(frequency, duration_ms, volume=0.12):
    """Lower-volume triangle-ish wave for bass line."""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    period = SAMPLE_RATE / frequency
    peak = int(32767 * volume)
    samples = []
    for i in range(num_samples):
        phase = (i % period) / period
        if phase < 0.5:
            wave = int(peak * (4 * phase - 1))
        else:
            wave = int(peak * (3 - 4 * phase))
        release_start = num_samples - int(num_samples * 0.2)
        if i > release_start:
            wave = int(wave * (num_samples - i) / (num_samples - release_start))
        samples.append(wave)
    return samples


def _arp(frequencies, note_ms, volume=0.15):
    """Quick arpeggio across a list of frequencies."""
    out = []
    gap = _silence(15)
    for freq in frequencies:
        out += _note(freq, note_ms, volume) + gap
    return out


def _mix(*tracks):
    """Mix multiple sample lists together (sum, clamped)."""
    length = max(len(t) for t in tracks)
    out = []
    for i in range(length):
        total = 0
        for t in tracks:
            total += t[i] if i < len(t) else 0
        out.append(max(-32767, min(32767, total)))
    return out


def _haunting_note(frequency, duration_ms, volume=0.18):
    """Sine wave with slow attack and long release — eerie, sustained feel."""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(32767 * volume)
    attack = int(num_samples * 0.15)
    release = int(num_samples * 0.4)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        wave = math.sin(2 * math.pi * frequency * t)
        # Add slight vibrato for warmth
        vibrato = 1.0 + 0.003 * math.sin(2 * math.pi * 4.5 * t)
        wave = math.sin(2 * math.pi * frequency * vibrato * t)
        if i < attack:
            env = i / attack
        elif i > num_samples - release:
            env = (num_samples - i) / release
        else:
            env = 1.0
        samples.append(int(peak * wave * env))
    return samples


def _drone(frequency, duration_ms, volume=0.06):
    """Low continuous drone — triangle wave, very slow fade in/out."""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    period = SAMPLE_RATE / frequency
    peak = int(32767 * volume)
    attack = int(num_samples * 0.2)
    release = int(num_samples * 0.2)
    samples = []
    for i in range(num_samples):
        phase = (i % period) / period
        if phase < 0.5:
            wave = 4 * phase - 1
        else:
            wave = 3 - 4 * phase
        if i < attack:
            env = i / attack
        elif i > num_samples - release:
            env = (num_samples - i) / release
        else:
            env = 1.0
        samples.append(int(peak * wave * env))
    return samples


def _pad(frequency, duration_ms, volume=0.08):
    """Soft pad — two detuned sine waves for a wide, spacious sound."""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(32767 * volume)
    detune = 1.5
    attack = int(num_samples * 0.25)
    release = int(num_samples * 0.35)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        wave = (
            math.sin(2 * math.pi * frequency * t)
            + 0.7 * math.sin(2 * math.pi * (frequency + detune) * t)
            + 0.3 * math.sin(2 * math.pi * (frequency * 2.001) * t)
        )
        if i < attack:
            env = i / attack
        elif i > num_samples - release:
            env = (num_samples - i) / release
        else:
            env = 1.0
        samples.append(int(peak * wave * env / 2.0))
    return samples


# ─── New synthesis primitives for realistic SFX ──────────────────────────


def _filtered_noise(duration_ms, volume=0.4, cutoff_start=1.0, cutoff_end=0.1):
    """Noise burst with simple low-pass filter that closes over time."""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(32767 * volume)
    samples = []
    prev = 0.0
    for i in range(num_samples):
        progress = i / num_samples
        fade = 1.0 - progress * 0.8
        cutoff = cutoff_start + (cutoff_end - cutoff_start) * progress
        raw = random.randint(-peak, peak) * fade
        prev = prev + cutoff * (raw - prev)
        samples.append(int(prev))
    return samples


def _sine_tone(frequency, duration_ms, volume=0.3):
    """Pure sine wave with ADSR envelope."""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(32767 * volume)
    attack = int(num_samples * 0.05)
    decay = int(num_samples * 0.1)
    release = int(num_samples * 0.3)
    sustain_level = 0.7
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        wave = math.sin(2 * math.pi * frequency * t)
        if i < attack:
            env = i / attack
        elif i < attack + decay:
            env = 1.0 - (1.0 - sustain_level) * (i - attack) / decay
        elif i > num_samples - release:
            env = sustain_level * (num_samples - i) / release
        else:
            env = sustain_level
        samples.append(int(peak * wave * env))
    return samples


def _rumble(duration_ms, volume=0.4):
    """Low-frequency rumble for heavy impacts and rocket engines."""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(32767 * volume)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        progress = i / num_samples
        fade = 1.0 - progress * 0.7
        wave = (
            math.sin(2 * math.pi * 40 * t)
            + 0.5 * math.sin(2 * math.pi * 65 * t)
            + 0.3 * math.sin(2 * math.pi * 30 * t + 0.5)
        )
        samples.append(int(peak * wave * fade / 1.8))
    return samples


def _laser_zap(start_freq, end_freq, duration_ms, volume=0.35):
    """Layered laser sound — two detuned oscillators + harmonics."""
    num_samples = int(SAMPLE_RATE * duration_ms / 1000)
    peak = int(32767 * volume)
    attack = min(int(SAMPLE_RATE * 3 / 1000), num_samples)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        progress = i / num_samples
        freq = start_freq * ((end_freq / start_freq) ** progress)
        fade = (1.0 - progress) ** 1.5
        if i < attack:
            fade *= i / attack
        wave = (
            0.6 * math.sin(2 * math.pi * freq * t)
            + 0.25 * math.sin(2 * math.pi * freq * 2.01 * t)
            + 0.15 * math.sin(2 * math.pi * freq * 3.0 * t)
        )
        samples.append(int(peak * wave * fade))
    return samples


# ─── Improved sound effects ──────────────────────────────────────────────


def _make_shoot():
    """Realistic laser blaster — sharp zap with resonant tail."""
    zap = _laser_zap(1800, 400, 100, volume=0.30)
    click = _sine_tone(3000, 8, volume=0.20)
    body = _sine_tone(600, 60, volume=0.12)
    return _mix(click + _silence(92), zap, _silence(10) + body)


def _make_explosion():
    """Alien explosion — filtered noise with low rumble undertone."""
    noise = _filtered_noise(350, volume=0.45, cutoff_start=0.8, cutoff_end=0.05)
    low = _rumble(300, volume=0.20)
    crack = _noise_burst(30, volume=0.5)
    return _mix(crack + _silence(320), noise, low)


def _make_rocket_fire():
    """Rocket launch — ignition burst, ascending whoosh, engine rumble."""
    ignition = _filtered_noise(80, volume=0.45, cutoff_start=1.0, cutoff_end=0.3)
    whoosh = _ascending_tone(100, 500, 250, volume=0.30)
    engine = _rumble(400, volume=0.35)
    hiss = _filtered_noise(350, volume=0.20, cutoff_start=0.3, cutoff_end=0.05)
    return _mix(
        ignition + _silence(320),
        _silence(40) + whoosh + _silence(110),
        engine,
        _silence(50) + hiss,
    )


def _make_rocket_explosion():
    """Massive rocket detonation — deep boom with debris scatter."""
    boom = _rumble(600, volume=0.50)
    blast = _filtered_noise(500, volume=0.60, cutoff_start=1.0, cutoff_end=0.03)
    crack = _noise_burst(40, volume=0.7)
    debris = _filtered_noise(400, volume=0.20, cutoff_start=0.15, cutoff_end=0.02)
    sub = _sine_tone(35, 500, volume=0.25)
    return _mix(
        crack + _silence(560),
        blast,
        boom,
        _silence(200) + debris,
        sub,
    )


def _make_boss_hit():
    """Metallic impact on boss armor."""
    impact = _sine_tone(800, 40, volume=0.30)
    ring = _descending_tone(1200, 600, 80, volume=0.20)
    clang = _noise_burst(25, volume=0.25)
    return _mix(clang + _silence(95), impact + _silence(80), ring)


def _make_boss_shoot():
    """Heavy boss weapon — deep energy discharge."""
    charge = _ascending_tone(80, 200, 100, volume=0.30)
    blast = _laser_zap(600, 150, 200, volume=0.35)
    bass = _rumble(150, volume=0.20)
    return _mix(charge + _silence(200), _silence(80) + blast + _silence(20), bass)


def _make_boss_death():
    """Epic boss destruction — cascading explosions."""
    boom1 = _rumble(500, volume=0.45)
    boom2 = _filtered_noise(400, volume=0.50, cutoff_start=0.9, cutoff_end=0.05)
    boom3 = _filtered_noise(600, volume=0.40, cutoff_start=0.7, cutoff_end=0.02)
    crumble = _descending_tone(400, 30, 800, volume=0.30)
    sub = _sine_tone(25, 1000, volume=0.20)
    crack1 = _noise_burst(50, volume=0.6)
    crack2 = _noise_burst(40, volume=0.5)
    return _mix(
        crack1 + _silence(950),
        boom1 + _silence(500),
        _silence(200) + boom2 + _silence(200),
        _silence(400) + crack2 + _silence(560),
        _silence(400) + boom3,
        crumble + _silence(200),
        sub,
    )


# ─── Numpy FM synthesis primitives for cinematic music ─────────────────


def _np_adsr(n, a, d, s, r):
    """Exponential-curve ADSR envelope, returns float64 array of length n."""
    env = np.ones(n, dtype=np.float64)
    a_samp = int(n * a)
    d_samp = int(n * d)
    r_samp = int(n * r)
    s_level = s

    # Attack — exponential rise
    if a_samp > 0:
        env[:a_samp] = np.linspace(0, 1, a_samp) ** 0.5

    # Decay — exponential fall to sustain
    if d_samp > 0:
        start = a_samp
        end = min(a_samp + d_samp, n)
        t = np.linspace(0, 1, end - start)
        env[start:end] = 1.0 - (1.0 - s_level) * (1.0 - np.exp(-3 * t))

    # Sustain
    sus_start = a_samp + d_samp
    sus_end = max(n - r_samp, sus_start)
    env[sus_start:sus_end] = s_level

    # Release — exponential fall to zero
    if r_samp > 0:
        start = max(n - r_samp, 0)
        t = np.linspace(0, 1, n - start)
        env[start:] = env[start] * np.exp(-4 * t)

    return env


def _np_fm_brass(freq, dur, vol=0.22):
    """FM synthesis brass — bright attack, warm sustain (mod index decays).

    Carrier: freq, Modulator: freq*1 (1:1 ratio for brassy timbre).
    Modulation index starts high (bright attack) and decays (warm sustain).
    """
    n = int(SAMPLE_RATE * dur)
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE

    # ADSR: fast attack, quick decay, high sustain, moderate release
    env = _np_adsr(n, 0.06, 0.1, 0.75, 0.15)

    # Modulation index: starts at 6 (bright), decays to 2 (warm)
    mod_env = 2.0 + 4.0 * np.exp(-6.0 * t / dur)

    # FM synthesis
    mod_freq = freq * 1.0  # 1:1 ratio
    modulator = mod_env * np.sin(2.0 * np.pi * mod_freq * t)
    carrier = np.sin(2.0 * np.pi * freq * t + modulator)

    # Add a second partial for thickness (octave + fifth, lower level)
    mod2 = (mod_env * 0.3) * np.sin(2.0 * np.pi * freq * 3.0 * t)
    carrier2 = 0.2 * np.sin(2.0 * np.pi * freq * 2.0 * t + mod2)

    return vol * env * (carrier + carrier2) / 1.2


def _np_fm_strings(freq, dur, vol=0.12, voices=4):
    """Detuned multi-voice FM strings with vibrato — ensemble sound."""
    n = int(SAMPLE_RATE * dur)
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE

    # Slow attack, long sustain, gentle release (string-like)
    env = _np_adsr(n, 0.25, 0.1, 0.8, 0.2)

    # Vibrato (shared across voices)
    vibrato = 1.0 + 0.003 * np.sin(2.0 * np.pi * 5.0 * t)

    out = np.zeros(n, dtype=np.float64)
    rng = np.random.default_rng(int(freq * 1000) % (2**31))
    detune_cents = np.linspace(-8, 8, voices)

    for i in range(voices):
        detune = 2.0 ** (detune_cents[i] / 1200.0)
        f = freq * detune * vibrato
        # Light FM for string richness (mod index ~1)
        phase_offset = rng.uniform(0, 2 * np.pi)
        mod = 0.8 * np.sin(2.0 * np.pi * f * 2.0 * t + phase_offset)
        voice = np.sin(2.0 * np.pi * f * t + mod)
        out += voice

    out /= voices
    return vol * env * out


def _np_timpani(freq, dur, vol=0.22):
    """Inharmonic partials at real timpani mode ratios, exponential decay."""
    n = int(SAMPLE_RATE * dur)
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE

    # Real timpani mode ratios (relative to fundamental)
    ratios = [1.0, 1.504, 1.741, 2.0, 2.296, 2.654]
    amps = [1.0, 0.6, 0.4, 0.3, 0.15, 0.1]

    # Pitch drop on attack
    pitch_env = 1.0 + 0.3 * np.exp(-20.0 * t)

    # Exponential decay, faster for higher partials
    out = np.zeros(n, dtype=np.float64)
    for ratio, amp in zip(ratios, amps):
        decay = np.exp(-ratio * 4.0 * t / dur)
        partial_freq = freq * ratio * pitch_env
        phase = 2.0 * np.pi * np.cumsum(partial_freq) / SAMPLE_RATE
        out += amp * decay * np.sin(phase)

    # Noise attack for the stick hit
    noise = np.random.default_rng(42).normal(0, 1, n)
    noise_env = np.exp(-40.0 * t)
    out += 0.15 * noise * noise_env

    out /= np.max(np.abs(out) + 1e-10)
    return vol * out


def _np_snare(dur, vol=0.12):
    """Bandpass-filtered noise + sine body."""
    n = int(SAMPLE_RATE * dur)
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE

    # Body — sine at ~200Hz
    body = np.sin(2.0 * np.pi * 200 * t)

    # Noise component
    noise = np.random.default_rng(99).normal(0, 1, n)
    # Simple bandpass via cascaded high/low pass
    sos_hi = butter(2, 1000, btype="high", fs=SAMPLE_RATE, output="sos")
    sos_lo = butter(2, 8000, btype="low", fs=SAMPLE_RATE, output="sos")
    noise = sosfilt(sos_hi, noise)
    noise = sosfilt(sos_lo, noise)

    env = np.exp(-8.0 * t / dur)
    out = env * (0.3 * body + 0.7 * noise / (np.max(np.abs(noise)) + 1e-10))
    return vol * out


def _np_silence(dur):
    """Return numpy array of zeros for given duration in seconds."""
    return np.zeros(int(SAMPLE_RATE * dur), dtype=np.float64)


def _np_mix(*tracks):
    """Mix numpy tracks (sum), padding shorter ones with zeros."""
    length = max(len(t) for t in tracks)
    out = np.zeros(length, dtype=np.float64)
    for t in tracks:
        out[: len(t)] += t
    return out


def _np_concat(*segments):
    """Concatenate numpy segments."""
    return np.concatenate(segments)


# ─── Post-processing chain ─────────────────────────────────────────────


def _post_process(stereo, lowpass_freq=6000, reverb_wet=0.22, reverb_dur=1.5):
    """Apply low-pass filter, convolution reverb, soft compression.

    stereo: (2, N) numpy array
    Returns: (2, N') numpy array, normalized.
    """
    processed = np.copy(stereo)

    # 1. Low-pass filter — remove harsh digital bite
    sos = butter(4, lowpass_freq, btype="low", fs=SAMPLE_RATE, output="sos")
    for ch in range(2):
        processed[ch] = sosfilt(sos, processed[ch])

    # 2. Convolution reverb — synthetic impulse response
    ir_len = int(SAMPLE_RATE * reverb_dur)
    rng = np.random.default_rng(777)
    ir = rng.normal(0, 1, ir_len)
    # Exponential decay
    ir *= np.exp(-4.0 * np.arange(ir_len) / ir_len)
    # Filter the IR itself for a smooth tail
    ir_sos = butter(2, 3000, btype="low", fs=SAMPLE_RATE, output="sos")
    ir = sosfilt(ir_sos, ir)
    ir /= np.max(np.abs(ir) + 1e-10)

    for ch in range(2):
        wet = fftconvolve(processed[ch], ir, mode="full")[: processed.shape[1]]
        processed[ch] = (1.0 - reverb_wet) * processed[ch] + reverb_wet * wet

    # 3. Soft compression — tanh clipper for warmth
    peak = np.max(np.abs(processed) + 1e-10)
    processed = processed / peak  # normalize to [-1, 1]
    processed = np.tanh(1.5 * processed) / np.tanh(1.5)  # soft clip

    # 4. Normalize to 0.7 peak
    processed *= 0.7

    return processed


def _crossfade_loop(stereo, fade_ms=80):
    """Apply crossfade at boundaries for seamless looping."""
    fade_samples = int(SAMPLE_RATE * fade_ms / 1000)
    if stereo.shape[1] < fade_samples * 2:
        return stereo

    result = np.copy(stereo)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)

    # Crossfade: blend the end into the beginning
    for ch in range(2):
        result[ch, :fade_samples] = (
            result[ch, :fade_samples] * fade_in + result[ch, -fade_samples:] * fade_out
        )
        result[ch, -fade_samples:] *= fade_out

    return result


# ─── Stereo panning helper ─────────────────────────────────────────────


def _pan_to_stereo(mono, pan=0.0):
    """Place a mono numpy signal in the stereo field.

    pan: -1.0 = full left, 0.0 = center, 1.0 = full right
    Returns: (2, N) array.
    """
    # Constant-power panning
    angle = (pan + 1.0) * np.pi / 4.0  # 0 to pi/2
    left_gain = np.cos(angle)
    right_gain = np.sin(angle)
    stereo = np.zeros((2, len(mono)), dtype=np.float64)
    stereo[0] = mono * left_gain
    stereo[1] = mono * right_gain
    return stereo


# ─── Star Wars-vibe level music (FM synthesis) ────────────────────────


def _make_level_music():
    """Heroic, adventurous theme — FM brass fanfares, sweeping FM strings,
    string ostinato, timpani. ~20 seconds, loops during regular levels.
    Natively stereo with post-processing."""

    # Notes
    G3, A3, Bb3, C4 = 196, 220, 233, 262
    D4, Eb4, F4, G4, A4, Bb4 = 294, 311, 349, 392, 440, 466
    C5, D5, Eb5, F5, G5 = 523, 587, 622, 698, 784
    G2, C3, D3, F3 = 98, 131, 147, 175

    # BPM ~130, beat in seconds
    b = 0.460
    hb = b / 2
    qb = b / 4

    brass_parts = []  # (offset_sec, numpy_array)
    string_parts = []
    bass_parts = []
    perc_parts = []
    ostinato_parts = []

    def seconds(beats):
        return beats * b

    # Helper to build a track from timed parts
    def _build_sequential(parts_list):
        """Build a mono track by concatenating (signal) segments."""
        if not parts_list:
            return np.zeros(1, dtype=np.float64)
        return np.concatenate(parts_list)

    # ===== Build brass melody =====
    brass_seq = []

    # Section A: Heroic fanfare (0-5 beats * b)
    brass_seq.append(_np_fm_brass(G4, hb, 0.22))
    brass_seq.append(_np_silence(qb))
    brass_seq.append(_np_fm_brass(G4, hb, 0.22))
    brass_seq.append(_np_silence(qb))
    brass_seq.append(_np_fm_brass(G4, hb, 0.22))
    brass_seq.append(_np_silence(qb))
    brass_seq.append(_np_fm_brass(Eb5, b + hb, 0.24))
    brass_seq.append(_np_silence(qb))
    brass_seq.append(_np_fm_brass(D5, hb, 0.20))
    brass_seq.append(_np_fm_brass(C5, qb, 0.18))
    brass_seq.append(_np_fm_brass(Bb4, qb, 0.18))
    brass_seq.append(_np_fm_brass(A4, b + hb, 0.22))
    brass_seq.append(_np_silence(hb))

    # Section B: Adventure theme
    brass_seq.append(_np_fm_brass(G4, hb, 0.20))
    brass_seq.append(_np_silence(qb))
    brass_seq.append(_np_fm_brass(A4, hb, 0.20))
    brass_seq.append(_np_silence(qb))
    brass_seq.append(_np_fm_brass(Bb4, b, 0.22))
    brass_seq.append(_np_fm_brass(D5, hb, 0.24))
    brass_seq.append(_np_silence(qb))
    brass_seq.append(_np_fm_brass(C5, hb, 0.22))
    brass_seq.append(_np_silence(qb))
    brass_seq.append(_np_fm_brass(Bb4, hb, 0.20))
    brass_seq.append(_np_fm_brass(A4, qb, 0.18))
    brass_seq.append(_np_fm_brass(G4, b + hb, 0.22))
    brass_seq.append(_np_silence(hb))

    # Section C: Soaring climax
    brass_seq.append(_np_fm_brass(D5, b, 0.26))
    brass_seq.append(_np_fm_brass(Eb5, hb, 0.24))
    brass_seq.append(_np_fm_brass(D5, hb, 0.22))
    brass_seq.append(_np_fm_brass(C5, b, 0.24))
    brass_seq.append(_np_fm_brass(Bb4, hb, 0.20))
    brass_seq.append(_np_fm_brass(A4, hb, 0.20))
    brass_seq.append(_np_fm_brass(G4, b, 0.22))
    brass_seq.append(_np_fm_brass(A4, hb, 0.20))
    brass_seq.append(_np_fm_brass(Bb4, b + hb, 0.24))

    # Section D: Resolution
    brass_seq.append(_np_fm_brass(G5, b + hb, 0.26))
    brass_seq.append(_np_silence(hb))
    brass_seq.append(_np_fm_brass(F5, hb, 0.22))
    brass_seq.append(_np_fm_brass(Eb5, hb, 0.22))
    brass_seq.append(_np_fm_brass(D5, b, 0.24))
    brass_seq.append(_np_fm_brass(C5, hb, 0.20))
    brass_seq.append(_np_fm_brass(Bb4, hb, 0.20))
    brass_seq.append(_np_fm_brass(G4, b + hb, 0.24))
    brass_seq.append(_np_silence(hb))

    brass_mono = _build_sequential(brass_seq)

    # ===== Build strings =====
    strings_seq = []

    # Section A
    strings_seq.append(_np_fm_strings(G3, b * 2, 0.10))
    strings_seq.append(_np_fm_strings(Eb4, b * 2, 0.10))
    strings_seq.append(_np_fm_strings(Bb3, b, 0.09))

    # Section B
    strings_seq.append(_np_fm_strings(C4, b * 2, 0.11))
    strings_seq.append(_np_fm_strings(Bb3, b * 2, 0.11))
    strings_seq.append(_np_fm_strings(G3, b, 0.10))

    # Section C
    strings_seq.append(_np_fm_strings(D4, b * 2, 0.12))
    strings_seq.append(_np_fm_strings(C4, b * 2, 0.12))
    strings_seq.append(_np_fm_strings(G3, b, 0.11))

    # Section D
    strings_seq.append(_np_fm_strings(G3, b * 2, 0.11))
    strings_seq.append(_np_fm_strings(Eb4, b * 2, 0.11))
    strings_seq.append(_np_fm_strings(G3, b, 0.10))

    strings_mono = _build_sequential(strings_seq)

    # ===== Build bass =====
    bass_seq = []
    bass_notes_a = [G2, G2, C3, C3, F3]
    bass_notes_b = [C3, C3, Bb3, Bb3, G2]
    bass_notes_c = [D3, D3, C3, C3, G2]
    bass_notes_d = [G2, G2, C3, C3, G2]

    for note_list in [bass_notes_a, bass_notes_b, bass_notes_c, bass_notes_d]:
        for freq in note_list:
            n = int(SAMPLE_RATE * b)
            t_arr = np.arange(n, dtype=np.float64) / SAMPLE_RATE
            env = _np_adsr(n, 0.02, 0.1, 0.6, 0.15)
            # FM bass — warm, round
            mod = 0.5 * np.sin(2.0 * np.pi * freq * t_arr)
            wave = np.sin(2.0 * np.pi * freq * t_arr + mod)
            bass_seq.append(0.16 * env * wave)

    bass_mono = _build_sequential(bass_seq)

    # ===== Build percussion =====
    perc_seq = []

    # Section A: timpani on beats
    for _ in range(5):
        perc_seq.append(_np_timpani(G2, b, 0.16))

    # Section B: timpani + snare
    for _ in range(5):
        perc_seq.append(_np_timpani(C3, hb, 0.14))
        snare = _np_snare(0.06, 0.09)
        perc_seq.append(snare)
        perc_seq.append(_np_silence(hb - 0.06))

    # Section C: heavier timpani
    for _ in range(5):
        perc_seq.append(_np_timpani(D3, b, 0.17))

    # Section D: timpani + snare
    for _ in range(4):
        perc_seq.append(_np_timpani(G2, hb, 0.15))
        snare = _np_snare(0.06, 0.08)
        perc_seq.append(snare)
        perc_seq.append(_np_silence(hb - 0.06))
    perc_seq.append(_np_timpani(G2, b, 0.18))

    perc_mono = _build_sequential(perc_seq)

    # ===== String ostinato — rapid 16th notes (Star Wars action style) =====
    ostinato_notes = [G3, Bb3, C4, Bb3, G3, Bb3, C4, D4]
    ost_seq = []
    note_dur = qb * 0.85  # slightly shorter than a 16th for articulation
    gap_dur = qb * 0.15
    total_ost_dur = 0
    target_dur = len(brass_mono) / SAMPLE_RATE

    while total_ost_dur < target_dur:
        for freq in ostinato_notes:
            if total_ost_dur >= target_dur:
                break
            ost_seq.append(_np_fm_strings(freq, note_dur, 0.06, voices=2))
            ost_seq.append(_np_silence(gap_dur))
            total_ost_dur += qb

    ostinato_mono = _build_sequential(ost_seq)

    # ===== Mix to stereo =====
    total_len = max(
        len(brass_mono),
        len(strings_mono),
        len(bass_mono),
        len(perc_mono),
        len(ostinato_mono),
    )

    def _pad_to(arr, length):
        if len(arr) >= length:
            return arr[:length]
        return np.concatenate([arr, np.zeros(length - len(arr))])

    brass_mono = _pad_to(brass_mono, total_len)
    strings_mono = _pad_to(strings_mono, total_len)
    bass_mono = _pad_to(bass_mono, total_len)
    perc_mono = _pad_to(perc_mono, total_len)
    ostinato_mono = _pad_to(ostinato_mono, total_len)

    # Pan: brass slightly left, strings slightly right, bass center,
    # perc center, ostinato slightly right
    stereo = np.zeros((2, total_len), dtype=np.float64)
    stereo += _pan_to_stereo(brass_mono, -0.3)
    stereo += _pan_to_stereo(strings_mono, 0.35)
    stereo += _pan_to_stereo(bass_mono, 0.0)
    stereo += _pan_to_stereo(perc_mono, 0.0)
    stereo += _pan_to_stereo(ostinato_mono, 0.25)

    # Post-process
    stereo = _post_process(stereo, lowpass_freq=6000, reverb_wet=0.22, reverb_dur=1.5)
    stereo = _crossfade_loop(stereo, fade_ms=80)

    return _make_sound_stereo(stereo)


# ─── Dark, menacing boss theme (FM synthesis) ──────────────────────────


def _make_boss_music():
    """Dark, menacing boss theme — heavy FM brass, pounding timpani, ominous drone.
    ~16 seconds, loops during boss fight. Natively stereo with post-processing."""

    # Notes — dark minor key (C minor / Eb)
    C2, Eb2, G2, Ab2, Bb2 = 65, 78, 98, 104, 117
    C3, Eb3, F3, G3, Ab3, Bb3 = 131, 156, 175, 196, 208, 233
    C4, D4, Eb4, F4, G4, Ab4, Bb4 = 262, 294, 311, 349, 392, 415, 466
    C5, Eb5 = 523, 622

    # BPM ~100, beat in seconds
    b = 0.600
    hb = b / 2
    qb = b / 4

    def _build_sequential(parts_list):
        if not parts_list:
            return np.zeros(1, dtype=np.float64)
        return np.concatenate(parts_list)

    # ===== Build brass =====
    brass_seq = []

    # Section A: Menacing march — short, stabbing notes
    brass_seq.append(_np_fm_brass(C4, hb - 0.05, 0.24))
    brass_seq.append(_np_silence(0.05))
    brass_seq.append(_np_fm_brass(C4, hb - 0.05, 0.24))
    brass_seq.append(_np_silence(0.05))
    brass_seq.append(_np_fm_brass(C4, hb - 0.05, 0.24))
    brass_seq.append(_np_silence(0.05))
    brass_seq.append(_np_fm_brass(Eb4, b, 0.26))
    brass_seq.append(_np_silence(qb))
    brass_seq.append(_np_fm_brass(Bb3, hb, 0.22))
    brass_seq.append(_np_fm_brass(Ab3, qb, 0.20))
    brass_seq.append(_np_fm_brass(G3, qb + hb, 0.24))
    brass_seq.append(_np_silence(hb))

    # Section B: Intensifying
    brass_seq.append(_np_fm_brass(G4, hb, 0.26))
    brass_seq.append(_np_silence(qb))
    brass_seq.append(_np_fm_brass(G4, qb, 0.22))
    brass_seq.append(_np_fm_brass(Ab4, b, 0.26))
    brass_seq.append(_np_fm_brass(G4, hb, 0.24))
    brass_seq.append(_np_fm_brass(F4, hb, 0.22))
    brass_seq.append(_np_fm_brass(Eb4, hb, 0.24))
    brass_seq.append(_np_fm_brass(D4, qb, 0.20))
    brass_seq.append(_np_fm_brass(C4, b + qb, 0.26))
    brass_seq.append(_np_silence(qb))

    # Section C: Climax — threatening peak
    brass_seq.append(_np_fm_brass(C5, b, 0.28))
    brass_seq.append(_np_fm_brass(Bb4, hb, 0.24))
    brass_seq.append(_np_fm_brass(Ab4, hb, 0.24))
    brass_seq.append(_np_fm_brass(G4, b, 0.26))
    brass_seq.append(_np_fm_brass(F4, hb, 0.22))
    brass_seq.append(_np_fm_brass(Eb4, hb, 0.24))
    brass_seq.append(_np_fm_brass(C4, hb, 0.24))
    brass_seq.append(_np_fm_brass(Eb4, hb, 0.24))
    brass_seq.append(_np_fm_brass(G4, b, 0.26))

    # Section D: Transition back to loop
    brass_seq.append(_np_fm_brass(Eb5, b + hb, 0.28))
    brass_seq.append(_np_silence(hb))
    brass_seq.append(_np_fm_brass(C5, hb, 0.24))
    brass_seq.append(_np_fm_brass(G4, hb, 0.22))
    brass_seq.append(_np_fm_brass(C4, b, 0.26))

    brass_mono = _build_sequential(brass_seq)

    # ===== Build strings — ominous sustain =====
    strings_seq = []

    strings_seq.append(_np_fm_strings(C3, b * 2, 0.13))
    strings_seq.append(_np_fm_strings(Ab3, b * 2, 0.12))
    # Section B
    strings_seq.append(_np_fm_strings(Eb3, b * 2, 0.13))
    strings_seq.append(_np_fm_strings(Ab3, b * 2, 0.13))
    # Section C
    strings_seq.append(_np_fm_strings(C3, b * 2, 0.14))
    strings_seq.append(_np_fm_strings(G3, b * 2, 0.14))
    # Section D
    strings_seq.append(_np_fm_strings(C3, b * 2, 0.13))

    strings_mono = _build_sequential(strings_seq)

    # ===== Ominous low drone (continuous) =====
    total_dur = len(brass_mono) / SAMPLE_RATE
    n_drone = int(SAMPLE_RATE * total_dur)
    t_drone = np.arange(n_drone, dtype=np.float64) / SAMPLE_RATE
    drone_env = _np_adsr(n_drone, 0.15, 0.1, 0.9, 0.1)
    # Two detuned low sines for menacing rumble
    drone_mono = (
        0.08
        * drone_env
        * (
            np.sin(2.0 * np.pi * C2 * t_drone)
            + 0.5 * np.sin(2.0 * np.pi * (C2 * 1.5) * t_drone)
            + 0.3 * np.sin(2.0 * np.pi * (C2 * 0.5) * t_drone)
        )
    )

    # ===== Build bass =====
    bass_seq = []
    bass_a = [C2, C2, C2, Eb2, Ab2, G2, C2, C2]
    bass_b = [Eb2, Eb2, Ab2, Ab2, Eb2, G2, C2, C2]
    bass_c = [C2, Ab2, G2, Eb2, G2, C2]
    bass_d = [C2, G2, C2, C2]

    for note_list, dur_mult in [(bass_a, hb), (bass_b, hb), (bass_c, b), (bass_d, b)]:
        for freq in note_list:
            n = int(SAMPLE_RATE * dur_mult)
            t_arr = np.arange(n, dtype=np.float64) / SAMPLE_RATE
            env = _np_adsr(n, 0.02, 0.1, 0.7, 0.1)
            mod = 0.6 * np.sin(2.0 * np.pi * freq * t_arr)
            wave = np.sin(2.0 * np.pi * freq * t_arr + mod)
            bass_seq.append(0.18 * env * wave)

    bass_mono = _build_sequential(bass_seq)

    # ===== Build percussion — heavier than level =====
    perc_seq = []

    # Section A
    for _ in range(4):
        perc_seq.append(_np_timpani(C2, hb, 0.20))
        perc_seq.append(_np_timpani(C2, hb, 0.14))

    # Section B
    for _ in range(4):
        perc_seq.append(_np_timpani(G2, qb + qb, 0.18))
        perc_seq.append(_np_snare(0.08, 0.11))
        perc_seq.append(_np_silence(hb - 0.08))

    # Section C
    for _ in range(4):
        perc_seq.append(_np_timpani(C2, hb, 0.22))
        perc_seq.append(_np_snare(0.06, 0.11))
        perc_seq.append(_np_silence(qb - 0.06))
        perc_seq.append(_np_timpani(G2, qb, 0.16))

    # Section D
    for _ in range(2):
        perc_seq.append(_np_timpani(C2, b, 0.20))
        perc_seq.append(_np_timpani(G2, b, 0.16))

    perc_mono = _build_sequential(perc_seq)

    # ===== Mix to stereo =====
    total_len = max(
        len(brass_mono),
        len(strings_mono),
        len(bass_mono),
        len(perc_mono),
        len(drone_mono),
    )

    def _pad_to(arr, length):
        if len(arr) >= length:
            return arr[:length]
        return np.concatenate([arr, np.zeros(length - len(arr))])

    brass_mono = _pad_to(brass_mono, total_len)
    strings_mono = _pad_to(strings_mono, total_len)
    bass_mono = _pad_to(bass_mono, total_len)
    perc_mono = _pad_to(perc_mono, total_len)
    drone_mono = _pad_to(drone_mono, total_len)

    stereo = np.zeros((2, total_len), dtype=np.float64)
    stereo += _pan_to_stereo(brass_mono, -0.25)
    stereo += _pan_to_stereo(strings_mono, 0.3)
    stereo += _pan_to_stereo(bass_mono, 0.0)
    stereo += _pan_to_stereo(perc_mono, 0.0)
    stereo += _pan_to_stereo(drone_mono, 0.0)

    # Post-process — less reverb for boss (more aggressive, in-your-face)
    stereo = _post_process(stereo, lowpass_freq=5500, reverb_wet=0.15, reverb_dur=1.0)
    stereo = _crossfade_loop(stereo, fade_ms=80)

    return _make_sound_stereo(stereo)


# ─── Menu melody (unchanged, wrapped to stereo) ───────────────────────


def _make_menu_melody():
    # Atmospheric, haunting theme — D minor, slow and spacious
    # Inspired by post-apocalyptic wasteland ambience
    D3, F3, G3, A3, Bb3 = 147, 175, 196, 220, 233
    D4, E4, F4, G4, A4, Bb4, C5, D5, F5 = 294, 330, 349, 392, 440, 466, 523, 587, 698
    D2, A2 = 73, 110

    lead = []  # haunting melody
    pads = []  # atmospheric chords
    bass = []  # low drone

    # --- Continuous low drone underpinning everything ---
    bass += _drone(D2, 24000, 0.05)

    # ===== Part 1: Desolate opening (0-6s) =====

    # Slow, sparse notes emerging from silence
    pads += _pad(D3, 3000, 0.06) + _silence(200)
    pads += _pad(A3, 2800, 0.06) + _silence(200)

    lead += _silence(1000)
    lead += _haunting_note(D4, 1400, 0.16)
    lead += _silence(500)
    lead += _haunting_note(F4, 1100, 0.14)
    lead += _silence(400)
    lead += _haunting_note(E4, 900, 0.12)
    lead += _silence(300)
    lead += _haunting_note(D4, 1600, 0.16)
    lead += _silence(600)

    # ===== Part 2: Theme emerges (6-12s) =====

    # Main melody — slow, deliberate, melancholic
    pads += _pad(Bb3, 2800, 0.07) + _silence(200)
    pads += _pad(F3, 2800, 0.07) + _silence(200)

    lead += _haunting_note(A4, 1000, 0.18)
    lead += _silence(200)
    lead += _haunting_note(G4, 600, 0.15)
    lead += _silence(150)
    lead += _haunting_note(F4, 600, 0.15)
    lead += _silence(150)
    lead += _haunting_note(E4, 1200, 0.17)
    lead += _silence(400)
    lead += _haunting_note(D4, 800, 0.14)
    lead += _silence(200)
    lead += _haunting_note(A3, 1400, 0.16)
    lead += _silence(500)

    # ===== Part 3: Building tension (12-17s) =====

    # Higher register, more intensity
    pads += _pad(G3, 2500, 0.08) + _silence(200)
    pads += _pad(D3, 2500, 0.08) + _silence(200)

    lead += _haunting_note(D5, 1200, 0.20)
    lead += _silence(200)
    lead += _haunting_note(C5, 600, 0.17)
    lead += _silence(100)
    lead += _haunting_note(Bb4, 600, 0.17)
    lead += _silence(100)
    lead += _haunting_note(A4, 1100, 0.18)
    lead += _silence(250)
    lead += _haunting_note(G4, 700, 0.15)
    lead += _silence(150)
    lead += _haunting_note(F4, 900, 0.15)
    lead += _silence(350)

    # ===== Part 4: Climax and resolution (17-24s) =====

    # Peak emotional moment — highest note, then gentle descent
    pads += _pad(Bb3, 3000, 0.09) + _silence(200)
    pads += _pad(A3, 4000, 0.07) + _silence(200)

    lead += _haunting_note(F5, 1600, 0.20)
    lead += _silence(400)
    lead += _haunting_note(D5, 1100, 0.18)
    lead += _silence(250)
    lead += _haunting_note(A4, 900, 0.16)
    lead += _silence(250)
    lead += _haunting_note(F4, 1000, 0.14)
    lead += _silence(300)
    lead += _haunting_note(D4, 2000, 0.15)
    lead += _silence(600)

    return _mix(lead, pads, bass)


import hashlib
import os
import pathlib


def _cache_dir():
    """Return the sound cache directory next to this file."""
    return pathlib.Path(__file__).parent / ".sound_cache"


def _source_hash():
    """Hash of this source file — changes when any sound code changes."""
    src = pathlib.Path(__file__).read_bytes()
    return hashlib.md5(src).hexdigest()[:12]


def _try_load_cache():
    """Try to load all sounds from cached WAV files. Returns dict or None."""
    cache = _cache_dir()
    stamp_file = cache / "stamp.txt"
    if not stamp_file.exists():
        return None
    if stamp_file.read_text().strip() != _source_hash():
        return None

    result = {}
    for wav_path in cache.glob("*.wav"):
        name = wav_path.stem
        try:
            result[name] = pygame.mixer.Sound(str(wav_path))
        except Exception:
            return None

    # Check all expected keys exist
    expected = {
        "shoot",
        "explosion",
        "game_over",
        "pickup",
        "rocket_fire",
        "rocket_explosion",
        "boss_hit",
        "boss_shoot",
        "boss_death",
        "level_up",
        "victory",
        "comm_call",
        "comm_open",
        "menu_melody",
        "level_music",
        "boss_music",
    }
    if not expected.issubset(result.keys()):
        return None
    return result


def _save_cache(sounds_dict):
    """Save all sounds as WAV files for fast loading next time."""
    cache = _cache_dir()
    cache.mkdir(exist_ok=True)

    for name, snd in sounds_dict.items():
        raw = snd.get_raw()
        wav_path = cache / f"{name}.wav"
        # Write raw PCM as WAV (16-bit stereo, 44100 Hz)
        import wave

        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(raw)

    (cache / "stamp.txt").write_text(_source_hash())


def load_sounds():
    # Try loading from cache first (instant)
    cached = _try_load_cache()
    if cached is not None:
        for key in ("menu_melody", "level_music", "boss_music"):
            if key in cached:
                cached[key].set_volume(0.5)
        return cached

    # Generate everything from scratch (slow, only on first run or after changes)
    level_music = _make_level_music()
    boss_music = _make_boss_music()

    # Menu melody and all SFX are mono — wrap to stereo
    menu_mono = _make_sound(_make_menu_melody())

    sfx_mono = {
        "shoot": _make_sound(_make_shoot()),
        "explosion": _make_sound(_make_explosion()),
        "game_over": _make_sound(_descending_tone(440, 110, 600, volume=0.4)),
        "pickup": _make_sound(_ascending_tone(400, 1200, 180, volume=0.4)),
        "rocket_fire": _make_sound(_make_rocket_fire()),
        "rocket_explosion": _make_sound(_make_rocket_explosion()),
        "boss_hit": _make_sound(_make_boss_hit()),
        "boss_shoot": _make_sound(_make_boss_shoot()),
        "boss_death": _make_sound(_make_boss_death()),
        "level_up": _make_sound(
            _square_wave(440, 100, volume=0.3)
            + _square_wave(554, 100, volume=0.3)
            + _square_wave(659, 150, volume=0.3)
        ),
        "victory": _make_sound(
            _square_wave(523, 120, volume=0.3)
            + _square_wave(659, 120, volume=0.3)
            + _square_wave(784, 120, volume=0.3)
            + _square_wave(1047, 200, volume=0.4)
        ),
        "comm_call": _make_sound(
            _square_wave(800, 80, volume=0.25)
            + _square_wave(600, 80, volume=0.25)
            + _square_wave(800, 80, volume=0.25)
            + _square_wave(600, 80, volume=0.25)
            + _square_wave(800, 80, volume=0.25)
        ),
        "comm_open": _make_sound(_ascending_tone(300, 900, 150, volume=0.2)),
    }

    result = {}
    result["menu_melody"] = _mono_to_stereo(menu_mono)
    result["level_music"] = level_music
    result["boss_music"] = boss_music
    for key, snd in sfx_mono.items():
        result[key] = _mono_to_stereo(snd)

    # Reduce music volume by 50%
    for key in ("menu_melody", "level_music", "boss_music"):
        result[key].set_volume(0.5)

    # Cache for next run
    _save_cache(result)

    return result
