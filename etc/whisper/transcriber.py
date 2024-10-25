from pathlib import Path
from typing import Any

import faster_whisper  # type: ignore
from tqdm import tqdm


class Transcriber:
    def __init__(self, wav_path: Path, srt_path: Path, model_name: str) -> None:
        self.wav_path = wav_path
        self.srt_path = srt_path
        self.model = faster_whisper.WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
            cpu_threads=16,
        )

    def transcribe(self, entry: Any) -> None:
        segments, _info = self.model.transcribe(self.wav_path, beam_size=5)  # type: ignore

        pbar = tqdm(total=entry["duration"], desc="Transcribing")

        with self.srt_path.open("w", encoding="utf-8") as srt:
            for chunk, segment in enumerate(segments, start=1):
                srt.write(
                    f"{chunk}\n"
                    f"{format_timestamp(segment.start, always_include_hours=True)} --> "
                    f"{format_timestamp(segment.end, always_include_hours=True)}\n"
                    f"{segment.text.strip().replace('-->', '->')}\n\n"
                )

                delta = round(segment.end - segment.start)
                pbar.update(delta)

        pbar.close()


def format_timestamp(seconds: float, always_include_hours: bool = False) -> str:
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds = milliseconds // 1_000
    milliseconds -= seconds * 1_000

    hours_marker = f"{hours:02d}:" if always_include_hours or hours > 0 else ""
    return f"{hours_marker}{minutes:02d}:{seconds:02d},{milliseconds:03d}"
