# Second Pass

A small Streamlit app that turns what I study into a verified, searchable reference log.

It is built around the "second pass" study technique: the first pass is reading or watching something, the second pass is writing it out from memory. The app supports that second pass. It asks me a couple of questions about what I studied, I answer away from the screen (on paper, on a tablet, or typed), and it turns my answers into a clean entry in a running study log, checked for accuracy before anything is saved.

I built it for my own use while learning business analysis, and it works for any topic.

## How it works

1. **Paste what I studied.** Notes, an article excerpt, or a short description. Optionally add the link to the resource, which becomes the reference the answers are checked against.
2. **Get 2 short prompts.** One plain recall question and one small step past recall ("why does this matter?"). Deliberately basic, so the habit stays easy to keep.
3. **Answer from memory.** Type directly, or upload a photo or PDF export of handwritten or tablet-sketched notes. Handwriting is transcribed with Claude's vision and shown to me to review before saving.
4. **Save.** The answers are organized into a titled entry under a subject in `study_log.md`. Existing subjects are reused instead of creating near-duplicates.
5. **Fact-check before it is written.** The entry is checked against the source link (or the model's own knowledge if no link was given), and anything flagged is corrected before it reaches the log. The result is shown so I can see what was confirmed and what changed.

## Design decisions worth calling out

- **Verify before write.** The log is meant to be a reference I can trust, so entries are fact-checked and corrected before they are saved, not after.
- **Source of truth, with honest limits.** When a link is provided, the checker treats it as ground truth and quotes what the source says when something contradicts it. A claim the source simply doesn't cover is not called wrong. Video links, PDFs, JavaScript-only pages, and pages behind a login can't be read, and the app says so instead of pretending a check happened against them. The fetched page is passed to the model as data, not instructions.
- **No duplicate entries.** Studying the same material again enriches the existing entry instead of adding a second one. Similar-but-differently-worded entries are caught too, by the same call that classifies the subject, so it adds no extra API cost on a normal save.
- **Nothing lost mid-answer.** In-progress notes and answers autosave to a local draft file and are restored if the tab is closed. The draft is cleared once the entry is saved.
- **Deliberately small.** One page, a few single-purpose model calls, one Markdown file as the system of record. No database, no accounts, no multi-page navigation.

## Limits

- The fact-check is AI-generated. It is a strong second pair of eyes, not a guarantee, and the UI labels it that way.
- Autosave fires when a box loses focus, not on every keystroke, so text typed right before closing the tab without clicking elsewhere can still be lost.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
# then put your Anthropic API key in .env
streamlit run app.py
```

On Windows, `run.bat` starts the app once the virtual environment exists.

## Project layout

```
app.py                          Streamlit UI and the save / verify / enrich flow
src/orchestration/client.py     Anthropic API wrapper (truncation-aware retry, handwriting transcription)
src/orchestration/prompts.py    Prompts for questions, organizing, fact-checking, revising, enriching
src/orchestration/source.py     Fetches and cleans the linked source page
study_log.md                    The running log the app writes to (my real study notes)
```

Built with Python, Streamlit, and the Anthropic API.
