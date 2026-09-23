# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-script lecture "secretary": `sec.py` transcribes a lecture recording with Whisper on Apple Silicon (MLX), then pipes the transcript to the `claude` CLI to produce class notes.

## Running

The project root **is** the Python 3.14 venv (`bin/`, `lib/`, `pyvenv.cfg` live here; `.gitignore` ignores everything). Use its interpreter:

```
bin/python sec.py <path-to-audio>      # e.g. bin/python sec.py Prog-Lang.m4a
```

There are no tests, linter, or build step.

## Pipeline (sec.py)

1. **Transcribe**: `mlx_whisper.transcribe` with the HF model `mlx-community/whisper-large-v3-mlx` (downloaded to the HF cache; the local `whisper-large-v3/` folder holds only config/README and is not used by the script). Decoding options (`condition_on_previous_text=False`, `hallucination_silence_threshold`, etc.) are tuned to suppress Whisper hallucinations.
2. **Filter**: `is_junk` drops empty/punctuation-only segments and short "Thank you."-style hallucinations (high `no_speech_prob`, low `compression_ratio`); consecutive duplicate segments are collapsed.
3. **Write transcript**: `<audio>.txt` next to the audio, one line per segment as `[MM:SS] text`.
4. **Notes**: runs `claude -p <prompt> --model opus --tools ""` with the transcript on stdin and writes the output to `~/Desktop/brain2/<audio stem> notes.md`. The note title is `<audio stem> <audio file mtime as MM/DD/YY>`.

The notes prompt embedded in `sec.py` encodes the format from `noteFormat.md` (four sections: homework `- <when> > <task>`, topics list, detailed notes with tab-indented `= ` lines, topic timestamps). If you change the note format, update both `noteFormat.md` and the prompt in `sec.py` so they stay in sync.

## Files in the root

`*.m4a` / `*.aifc` are source recordings (large); matching `*.txt` files are transcript outputs. Some `.txt` files (e.g. `TCA.txt`) come from other transcription tools and don't follow the `[MM:SS]` format.
