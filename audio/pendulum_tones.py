"""Extra warm, mallet/plucked instruments for the Bright Lights pendulum twists (BL0075+).

Same rules as the rest of the channel's sound (owner: no 1-5 kHz click, no saturation): soft rounded
attacks, few upper partials, everything low-passed under ~3 kHz. Registered in engine/audio.py as
`marimba`, `kalimba`, `harp` and `glass`.
"""
import numpy as np

from .synth import SR, _lp, t_axis


def _attack(sig, ms):
    a = max(2, int(ms / 1000 * SR))
    sig[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    return sig


def marimba(f, dur=1.6):
    """Felt-mallet wooden bar: strong fundamental, the bar's 4th partial (3.93x) quiet and quick,
    higher notes ring shorter. No knock - the pendulum 'taps' the bar."""
    tt = t_axis(dur)
    dec = 3.2 * (f / 440.0) ** 0.5
    sig = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * dec)
           + 0.12 * np.sin(2 * np.pi * 3.93 * f * tt) * np.exp(-tt * dec * 6)
           + 0.06 * np.sin(2 * np.pi * 2.0 * f * tt) * np.exp(-tt * dec * 2))
    return _lp(_attack(sig, 4), 2800)


def kalimba(f, dur=2.0):
    """Thumb piano tine: round fundamental with the tine's soft inharmonic overtone (~5.4x) that
    dies in a few tens of ms, and a little 'buzz' octave."""
    tt = t_axis(dur)
    sig = (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 2.4)
           + 0.18 * np.sin(2 * np.pi * 2.0 * f * tt) * np.exp(-tt * 5.0)
           + 0.07 * np.sin(2 * np.pi * 5.4 * f * tt) * np.exp(-tt * 30))
    return _lp(_attack(sig, 3), 3000)


def harp(f, dur=2.4):
    """Plucked nylon string (Karplus-Strong with a soft, low-passed excitation)."""
    n = int(dur * SR)
    period = max(2, int(round(SR / f)))
    rng = np.random.default_rng(int(f * 100) + 7)
    buf = _lp(rng.uniform(-1, 1, period), min(0.45 * SR, 6 * f))
    out = np.zeros(n)
    loss = 0.996 ** (440.0 / f) ** 0.3          # low strings ring a bit longer
    ring = buf.copy()
    pos = 0
    for i in range(n):
        j = pos % period
        nxt = ring[(pos + 1) % period]
        out[i] = ring[j]
        ring[j] = loss * 0.5 * (ring[j] + nxt)
        pos += 1
    out /= np.max(np.abs(out)) + 1e-9
    return _lp(_attack(out, 3), 2600)


def glass(f, dur=3.2):
    """Wet-finger glass: pure tone with a slow 40 ms swell and a long, soft tail."""
    tt = t_axis(dur)
    env = (1 - np.exp(-tt * 25)) * np.exp(-tt * 1.1)
    sig = (np.sin(2 * np.pi * f * tt) + 0.08 * np.sin(2 * np.pi * 2.0 * f * tt)
           + 0.03 * np.sin(2 * np.pi * 3.0 * f * tt)) * env
    return _lp(sig, 2400)


INSTRUMENTS = {"marimba": marimba, "kalimba": kalimba, "harp": harp, "glass": glass}
