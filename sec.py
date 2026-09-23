import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import mlx_whisper

audio = Path(sys.argv[1]).expanduser().resolve()
out = audio.with_suffix(".txt")

result = mlx_whisper.transcribe(
    str(audio),
    path_or_hf_repo="mlx-community/whisper-large-v3-mlx",
    language="en",                      # skips language detection
    condition_on_previous_text=False,   # stops errors from carrying forward
    initial_prompt=(
        "A university lecture"
    ),
    word_timestamps=True,
    hallucination_silence_threshold=2.0,  # skips hallucinations over long silences
    no_speech_threshold=0.6,
    compression_ratio_threshold=2.4,
)



def is_junk(seg):
    text = seg["text"].strip()
    if not re.search(r"\w", text):  # empty or punctuation-only
        return True
    # "Thank you."-style hallucinations: a few words in a window Whisper itself rates as silence
    return seg["no_speech_prob"] > 0.8 and seg["compression_ratio"] < 1.0 and len(text.split()) <= 3

lines, prev = [], None
for seg in result["segments"]:
    text = seg["text"].strip()
    if is_junk(seg) or text == prev:  # text == prev collapses repetition loops
        continue
    prev = text
    lines.append(f"[{int(seg['start']//60):02d}:{int(seg['start']%60):02d}] {text}")
out.write_text("\n".join(lines) + "\n")
print(f"Wrote {out}")

# Class notes, formatted per noteFormat.md
title = f"{audio.stem} {datetime.fromtimestamp(audio.stat().st_mtime):%m/%d/%y}"
notes_prompt = f"""You are given a timestamped transcript of a university lecture on stdin.
The transcript was made by speech recognition, so expect misheard words; use context to recover the intended terms.
Write class notes in Markdown. Output only the notes, following this format exactly:

The first line is exactly: {title}

Then these four sections, with these exact headings, in this order:

# Section 1: Homework/required next steps
Every piece of homework, reading, deadline, exam, or other next step mentioned in the lecture.
One bullet per task, formatted as "- <when> > <task>". Put the date or timeframe first: an exact date as MM/DD/YY, or the wording used in class (e.g. "By next class", "Next few weeks").
If nothing was assigned, write "- None mentioned".

# Section 2: Topics covered in class today
One short bullet per topic, in the order they were covered. No explanations here.

# Section 3: Detailed topic notes
For every topic in Section 2, in the same order and with the same name, a bullet with the topic name,
followed by tab-indented detail lines that each start with "= ". Include definitions, formulas, examples, and how the topic relates to the others.

# Section 4: timestamps of topics
For every topic in Section 2, a bullet "- <topic>: <MM:SS>" giving the transcript timestamp(s) where it was covered; use a range like 12:30-18:05 when it spans a stretch.
"""
notes = subprocess.run(
    ["claude", "-p", notes_prompt, "--model", "opus", "--tools", ""],
    input=out.read_text(), capture_output=True, text=True, check=True,
).stdout
notes_path = Path.home() / "Desktop/brain2" / f"{audio.stem} notes.md"
notes_path.write_text(notes)
print(f"Wrote {notes_path}")
