from pathlib import Path

import ffmpeg  # pip install ffmpeg-python


def get_audio_duration(audio_path: Path) -> float:
    probe = ffmpeg.probe(audio_path)
    duration = float(probe["format"]["duration"])
    return duration


def trim_audio_from_end(audio_path: Path, opath: Path, start: int, from_end: int) -> None:
    """Trim audio 'from_end' seconds from the end."""
    audio_stream = ffmpeg.input(audio_path)

    duration = get_audio_duration(audio_path)
    end = duration - from_end
    trimmed_stream = audio_stream.filter("atrim", start=start, end=end)

    if audio_path != opath:
        output_stream = ffmpeg.output(trimmed_stream, str(opath))
        output_stream.run()
    else:
        # ffmpeg does not support edit in-place. Make a tmp file.
        tmp_opath = audio_path.with_name(f"temp_{audio_path.name}")
        output_stream = ffmpeg.output(trimmed_stream, str(tmp_opath))
        output_stream.run()
        # Delete the original file and rename the temp file
        audio_path.unlink()
        tmp_opath.rename(audio_path)

    # Safety check
    delta = abs(get_audio_duration(opath) + start - end)
    # print(duration)
    # print(get_audio_duration(opath))
    # print(delta)
    assert delta < 0.1


if __name__ == "__main__":
    audios_path = Path("book/audios")
    for audio_path in audios_path.iterdir():
        trim_audio_from_end(
            audio_path=audio_path,
            opath=audio_path,
            start=19,
            from_end=65,
        )
