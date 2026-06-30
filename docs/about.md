# About & Methodology

This is an **unofficial fan companion** to the *History of Philosophy Without Any Gaps* India series (Peter Adamson & Jonardon Ganeri) — a transparency-first set of read-along notes and transcripts. Here's exactly how it was made.

!!! warning "Read this first"
    The transcripts and notes are **machine-generated** (speech-to-text + an AI language model). They are a study aid, **not** an authoritative record — especially for the spelling of Sanskrit names and terms. When something matters, **trust the audio**, not this site.

## 1. Transcription — OpenAI Whisper (distil-large-v3)

Each episode's audio was transcribed locally with the open-source **Whisper** model — `distil-large-v3` via `faster-whisper` (int8, CPU, ~4x real-time). The series is dense with **Sanskrit proper nouns** that stress speech-to-text, so each episode was **seeded** with the key terms from its own title to prime the decoder, and the terms were then normalized to standard transliteration when the notes were written.

- Timestamps (`[hh:mm:ss]`) are Whisper-generated and approximate.
- Whisper still mishears Sanskrit terms; these were normalized to standard transliteration when the notes were written.

## 2. Notes — Anthropic's Claude (Opus)

The episode notes were written by **Claude (Opus)** from **one input only: the Whisper transcript of that episode**. The model worked to a fixed format spec:

- Follow the episode's **narration order**, not reordered chronology.
- Anchor points to the audio with `[hh:mm:ss]`.
- Preserve the **argument** — positions, objections, examples, jokes.
- **Don't invent facts.** Everything traces to the transcript. Sanskrit terms are normalized to standard transliteration.
- End each note with a glossary of the **thinkers, texts & terms** the episode introduces.

**No outside sources were used** — unlike some companions, there is no external bibliography. Every note reflects only what that episode itself says, so treat it as a *high-quality summary that can still be wrong*.

## 3. How this site is built & published

Notes and transcripts are compiled locally by a small Python script into a static site with **[MkDocs](https://www.mkdocs.org/) + the Material theme**, published free on **GitHub Pages**. No server, database, tracking, or ads. The site is `noindex` — meant to be shared by link, not found in search.

## 4. Credit & contact

All scholarship belongs to **Peter Adamson, Jonardon Ganeri, and their guest contributors**. Please **support the podcast** at **[historyofphilosophy.net](https://historyofphilosophy.net)** (and the accompanying OUP books). If you're affiliated with the show and would like this changed or taken down, that request will be honored via the repository it's published from.
