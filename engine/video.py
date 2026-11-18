"""ffmpeg I/O: stream raw frames to H.264, mux the soundtrack."""
import json
import subprocess
import sys


class VideoWriter:
    def __init__(self, path, fmt, crf=16, preset="medium", x264_params=None):
        """x264_params: e.g. "aq-mode=3" (Deep Sky: more bits for dark flat areas, against banding)."""
        self.path = path
        extra = ["-x264-params", x264_params] if x264_params else []
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{fmt.width}x{fmt.height}",
            "-r", str(fmt.fps), "-i", "-",
            "-c:v", "libx264", "-preset", preset, "-crf", str(crf), *extra,
            "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-movflags", "+faststart", path,
        ]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write(self, frame):
        try:
            self.proc.stdin.write(frame if isinstance(frame, bytes) else frame.tobytes())
        except (BrokenPipeError, OSError):  # Windows also reports a dead pipe as EINVAL
            if self.proc.poll() is None and not isinstance(sys.exc_info()[1], BrokenPipeError):
                raise
            # the encoder quit under us; say how (KS0010 lost it silently twice on the main PC)
            try:
                code = self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                code = None
            raise RuntimeError(f"ffmpeg encoder quit mid-render (exit code {code}"
                               f"{'' if code is None else f', 0x{code & 0xFFFFFFFF:08X}'})") from None

    def close(self):
        self.proc.stdin.close()
        if self.proc.wait() != 0:
            raise RuntimeError("ffmpeg video encode failed")


def _loudnorm_linear(wav_path, lufs):
    """Two-pass loudnorm: measure, then one constant gain (no dynamic pumping on soft textures)."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", wav_path, "-af",
                          f"loudnorm=I={lufs:g}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True, check=True).stderr
    m = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    return (f"loudnorm=I={lufs:g}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
            f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
            f"linear=true")


def measure_lufs(path):
    """Integrated loudness (LUFS) and sample peak (dBFS) of an audio file, via ffmpeg's ebur128."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=sample",
                          "-f", "null", "-"], capture_output=True, text=True, check=True).stderr
    summary = err[err.rindex("Summary:"):]
    lufs = float(summary.split("I:")[1].split("LUFS")[0])
    peak = float(summary.split("Peak:")[1].split("dBFS")[0])
    return lufs, peak


def mux(video_path, wav_path, out_path, lufs=-14, linear=False, premastered=False):
    """lufs/linear: Sandglass masters quieter with a single constant gain; defaults = every other engine.
    premastered: the audio is already at its final level (Deep Sky loops) - no filter, no resampling."""
    if premastered:
        af = []
    else:
        af = ["-af", _loudnorm_linear(wav_path, lufs) if linear else f"loudnorm=I={lufs:g}:TP=-1.5:LRA=11",
              "-ar", "48000"]
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", video_path, "-i", wav_path,
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", *af,
        "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out_path,
    ], check=True)
