import datetime
import hashlib
import json
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.orchestration.client import LogLLM
from src.orchestration.source import fetch_source
from src.orchestration.prompts import (
    check_understanding_prompt,
    enrich_entry_prompt,
    organize_entry_prompt,
    retrieval_prompts_prompt,
    revise_entry_prompt,
    transcribe_prompt,
)

load_dotenv()

LOG_PATH = Path(__file__).parent / "study_log.md"
DRAFT_PATH = Path(__file__).parent / ".second_pass_draft.json"
INDEX_PATH = Path(__file__).parent / ".study_log_index.json"

SEED_CONTENT = (
    "# Study Log\n\n"
    "Running reference built from real study sessions, across whatever you're "
    "currently curious about. Newest entry is on top within each subject.\n"
)

HEADER_RE = re.compile(r"^## (.+)$", re.MULTILINE)
TITLE_RE = re.compile(r"^\*\*(.+?)\*\*", re.MULTILINE)


def load_log() -> str:
    if not LOG_PATH.exists():
        LOG_PATH.write_text(SEED_CONTENT, encoding="utf-8")
    return LOG_PATH.read_text(encoding="utf-8")


def existing_subjects() -> list[str]:
    return HEADER_RE.findall(load_log())


def existing_titles() -> list[str]:
    return TITLE_RE.findall(load_log())


def find_entry(title: str) -> dict | None:
    """Locate an existing entry by its exact title, regardless of whether it's
    tracked in the merge index - covers legacy entries saved before that index
    existed, or ones a semantic (not exact-notes) duplicate check flagged."""
    content = load_log()
    for section in re.split(r"\n(?=## )", content):
        header_match = re.match(r"## (.+)", section)
        if not header_match:
            continue
        pattern = re.compile(
            r"\n\*\*" + re.escape(title) + r"\*\*(?: _(?P<tag>.+?)_)? &mdash; \d{4}-\d{2}-\d{2}\n\n(?P<bullets>.*?)\n(?=\n\*\*|\Z)",
            re.DOTALL,
        )
        m = pattern.search(section)
        if m:
            return {
                "subject": header_match.group(1).strip(),
                "tag": m.group("tag") or "",
                "bullets": m.group("bullets"),
                "entry_text": m.group(0),
            }
    return None


def append_entry(subject: str, tag: str, title: str, bullets: str) -> str:
    content = load_log()
    date = datetime.date.today().isoformat()
    tag_part = f" _{tag}_" if tag else ""
    entry = f"\n**{title}**{tag_part} &mdash; {date}\n\n{bullets}\n"
    header = f"## {subject}"
    if header not in content:
        content += f"\n{header}\n{entry}"
    else:
        idx = content.index(header) + len(header)
        content = content[:idx] + entry + content[idx:]
    LOG_PATH.write_text(content, encoding="utf-8")
    return entry


def replace_entry(old_entry_text: str, new_bullets: str) -> str:
    """Swap just the bullets of an already-saved entry, keeping its title/tag/date line."""
    content = load_log()
    if old_entry_text not in content:
        raise ValueError("Could not find the original entry to revise - it may have been edited outside the app.")
    header_line = old_entry_text.split("\n\n", 1)[0]
    new_entry_text = f"{header_line}\n\n{new_bullets}\n"
    content = content.replace(old_entry_text, new_entry_text, 1)
    LOG_PATH.write_text(content, encoding="utf-8")
    return new_entry_text


def load_draft() -> dict | None:
    if not DRAFT_PATH.exists():
        return None
    try:
        return json.loads(DRAFT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_draft(material: str, prompts: list[str] | None, answer: str, source_url: str = "") -> None:
    if not material.strip() and not answer.strip():
        clear_draft()
        return
    DRAFT_PATH.write_text(
        json.dumps({"material": material, "prompts": prompts, "answer": answer, "source_url": source_url}),
        encoding="utf-8",
    )


def clear_draft() -> None:
    DRAFT_PATH.unlink(missing_ok=True)


def material_key(material: str) -> str:
    return hashlib.sha256(material.strip().encode("utf-8")).hexdigest()


def load_index() -> dict:
    if not INDEX_PATH.exists():
        return {}
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def upsert_index(material: str, subject: str, tag: str, title: str, bullets: str, entry_text: str) -> None:
    """Remember which saved entry a given set of study notes produced, so a future
    save with the exact same notes enriches that entry instead of duplicating it.
    Called after every write to the log (fresh save, revise, or enrich) so this
    always points at the entry's current text, never a stale pre-revise version."""
    index = load_index()
    index[material_key(material)] = {
        "subject": subject,
        "tag": tag,
        "title": title,
        "bullets": bullets,
        "entry_text": entry_text,
    }
    INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")


def find_prior_entry(material: str) -> dict | None:
    prior = load_index().get(material_key(material))
    if prior and prior.get("entry_text", "") in load_log():
        return prior
    return None


def persist_draft() -> None:
    """on_change callback for the material/answer boxes - fires when a box loses
    focus after being edited, so closing the tab shortly after typing (without
    ever clicking away) can still lose the very last unblurred keystrokes."""
    save_draft(
        st.session_state.get("material_box", ""),
        st.session_state.get("prompts"),
        st.session_state.get("answer_box", ""),
        st.session_state.get("source_url_box", ""),
    )


def get_source(url: str) -> tuple[str | None, str | None]:
    """Fetch the linked source once per URL per session (cached), so re-runs and both the
    prompt-generation and fact-check steps reuse it instead of re-downloading the page."""
    url = url.strip()
    if not url:
        return None, None
    cache = st.session_state.setdefault("source_cache", {})
    if url not in cache:
        cache[url] = fetch_source(url)
    return cache[url]


st.set_page_config(page_title="Second Pass", page_icon="🎓")

st.title("Second Pass")
st.caption(
    "Read/watch something → handwrite your own summary on paper (or sketch it on "
    "a tablet) → bring it back here and it gets organized into your running "
    "reference log below. Works for any topic, not just one subject."
)

if "prompts" not in st.session_state:
    st.session_state["prompts"] = None

if "draft_loaded" not in st.session_state:
    draft = load_draft()
    if draft:
        st.session_state["material_box"] = draft.get("material", "")
        if draft.get("prompts"):
            st.session_state["prompts"] = draft["prompts"]
        st.session_state["answer_box"] = draft.get("answer", "")
        st.session_state["source_url_box"] = draft.get("source_url", "")
        st.session_state["draft_restored"] = True
    st.session_state["draft_loaded"] = True

if st.session_state.pop("draft_restored", False):
    st.info("Restored your in-progress notes and answers from where you left off.")

st.header("1. What did you just study?")
material = st.text_area(
    "Paste raw notes, an article excerpt, or just describe what you read/watched",
    height=120,
    placeholder="e.g. Watched a 10-min explainer on BPMN swimlanes and gateway types...",
    key="material_box",
    on_change=persist_draft,
)
source_url = st.text_input(
    "Link to the resource you're studying from (optional)",
    placeholder="https://...",
    key="source_url_box",
    on_change=persist_draft,
    help="If it's a readable web page, it becomes the reference for the fact-check, so your notes are checked against what it actually says instead of the AI's memory. Video links (YouTube etc.) and pages behind a login can't be read.",
)
source_text, source_error = get_source(source_url)
if source_text:
    st.caption(f"Source loaded ({len(source_text):,} characters read). The fact-check will use it as the reference.")
elif source_error:
    st.warning(f"{source_error} The fact-check will fall back to the AI's own knowledge and say so.")
    if st.button("Retry loading the link"):
        st.session_state.get("source_cache", {}).pop(source_url.strip(), None)
        st.rerun()

if st.button("Generate handwriting prompts", disabled=not material.strip()):
    llm = LogLLM()
    system, user = retrieval_prompts_prompt(material, source_text)
    with st.spinner("Thinking of what to ask you..."):
        result = llm.complete_json(system, user)
    st.session_state["prompts"] = result.get("prompts", [])
    persist_draft()

if st.session_state["prompts"]:
    st.success("Close this tab. Handwrite (or sketch) your answers to these on paper/tablet. Come back when you're done.")
    for i, p in enumerate(st.session_state["prompts"], 1):
        st.markdown(f"**{i}.** {p}")

st.divider()

st.header("2. Bring back your answers")
st.caption(
    "Type your answers directly below, or upload a photo/export of a handwritten "
    "or sketched page (from an iPad app like Notability/GoodNotes, or a phone "
    "photo) and have it transcribed into the box instead."
)
upload = st.file_uploader(
    "Upload a photo/export of a handwritten page (optional)",
    type=["png", "jpg", "jpeg", "pdf"],
)
if upload is not None and st.button("Transcribe upload"):
    llm = LogLLM()
    extension = upload.name.rsplit(".", 1)[-1]
    with st.spinner("Reading your handwriting..."):
        text = llm.transcribe(upload.getvalue(), extension, transcribe_prompt())
    st.session_state["answer_box"] = text
    persist_draft()

raw_summary = st.text_area(
    "Your answers, in your own words (type here, or review/fix the transcription above)",
    height=150,
    placeholder="Type your answers to the prompts above here...",
    key="answer_box",
    on_change=persist_draft,
)

subjects = existing_subjects()
subject_hint = st.selectbox("Subject hint (optional, AI will still double-check)", ["Let AI decide"] + subjects)

def verify_and_correct(llm, material_text, prompts, bullets, raw_answer, source_text=None, max_revisions=2):
    """Fact-check the bullets BEFORE they're written to the log. If the check
    flags anything, revise just the flagged points and re-check, up to
    max_revisions times. When a source link was loaded, both the check and the
    revision use it as the reference. Returns (bullets, final_check, was_revised)."""
    revised = False
    for attempt in range(max_revisions + 1):
        check_system, check_user = check_understanding_prompt(material_text, prompts, bullets, source_text)
        check = llm.complete_json(check_system, check_user)
        if not check.get("flags") or attempt == max_revisions:
            break
        rev_system, rev_user = revise_entry_prompt(
            material_text, prompts, raw_answer, bullets, check["flags"], source_text
        )
        bullets = llm.complete_json(rev_system, rev_user)["markdown_bullets"]
        revised = True
    return bullets, check, revised


if st.button("Save to log & check answers", disabled=not raw_summary.strip()):
    llm = LogLLM()
    prior = find_prior_entry(material)
    prompts_given = st.session_state["prompts"] or []
    target = None  # existing entry to overwrite, if enriching
    result = {}

    if prior:
        st.info("Same notes as an existing entry - enriching it instead of creating a duplicate.")
        target = prior
    else:
        hint = "" if subject_hint == "Let AI decide" else subject_hint
        system, user = organize_entry_prompt(raw_summary, subjects, existing_titles(), hint)
        with st.spinner("Organizing into your study log..."):
            result = llm.complete_json(system, user)

        dup_title = (result.get("duplicate_of_title") or "").strip()
        same_topic = find_entry(dup_title) if dup_title else None
        if same_topic:
            st.info(f'Looks like the same topic as an existing entry ("{dup_title}") - enriching it instead of creating a duplicate.')
            target = {**same_topic, "title": dup_title}

    if target:
        enrich_system, enrich_user = enrich_entry_prompt(target["bullets"], raw_summary)
        with st.spinner("Merging into your existing entry..."):
            bullets = llm.complete_json(enrich_system, enrich_user)["markdown_bullets"]
        subject, tag, title = target["subject"], target["tag"], target["title"]
    else:
        subject, tag, title = result["subject"], result.get("tag", ""), result["title"]
        bullets = result["markdown_bullets"]

    with st.spinner("Fact-checking your notes before saving..."):
        bullets, check, was_revised = verify_and_correct(
            llm, material, prompts_given, bullets, raw_summary, source_text
        )
    if was_revised:
        st.info("The fact-check flagged something in your notes, so the saved entry has been corrected (your original wording is kept everywhere else).")

    if target:
        entry_text = replace_entry(target["entry_text"], bullets)
    else:
        entry_text = append_entry(subject, tag, title, bullets)

    upsert_index(material, subject, tag, title, bullets, entry_text)
    st.session_state["last_entry"] = {
        "subject": subject,
        "tag": tag,
        "title": title,
        "bullets": bullets,
        "entry_text": entry_text,
    }
    st.session_state["last_material"] = material
    st.session_state["last_prompts"] = prompts_given
    st.session_state["last_answer"] = raw_summary
    st.session_state["last_check"] = check
    st.session_state["last_source_text"] = source_text
    clear_draft()

if st.session_state.get("last_entry"):
    entry = st.session_state["last_entry"]
    check = st.session_state.get("last_check") or {}

    st.success(f'Saved under "{entry["subject"]}" as "{entry["title"]}".')
    st.markdown(f"**{entry['title']}**" + (f" _{entry['tag']}_" if entry["tag"] else ""))
    st.markdown(entry["bullets"])
    st.caption("Copy this into Google Docs (or wherever else) too, if you want it there as well.")

    if st.session_state.get("last_source_text"):
        st.markdown("**Fact-check of the saved entry** _(checked against your source link; still AI-generated, so verify anything that surprises you)_")
    else:
        st.markdown("**Fact-check of the saved entry** _(no source link was loaded, so this is the AI's own knowledge only, not a guarantee — verify anything that surprises you)_")
    for c in check.get("confirmed", []):
        st.markdown(f"✅ {c}")
    for f in check.get("flags", []):
        st.warning(f)
    if not check.get("confirmed") and not check.get("flags"):
        st.caption("Nothing specific to confirm or flag - the notes were saved as-is either way.")

    if check.get("flags"):
        if st.button("Revise flagged answers"):
            llm = LogLLM()
            rev_system, rev_user = revise_entry_prompt(
                st.session_state.get("last_material", ""),
                st.session_state.get("last_prompts", []),
                st.session_state.get("last_answer", ""),
                entry["bullets"],
                check["flags"],
                st.session_state.get("last_source_text"),
            )
            with st.spinner("Revising based on the flags..."):
                revised = llm.complete_json(rev_system, rev_user)
            new_bullets = revised["markdown_bullets"]
            new_entry_text = replace_entry(entry["entry_text"], new_bullets)
            entry["bullets"] = new_bullets
            entry["entry_text"] = new_entry_text
            st.session_state["last_entry"] = entry
            upsert_index(
                st.session_state.get("last_material", ""),
                entry["subject"],
                entry["tag"],
                entry["title"],
                new_bullets,
                new_entry_text,
            )

            recheck_system, recheck_user = check_understanding_prompt(
                st.session_state.get("last_material", ""),
                st.session_state.get("last_prompts", []),
                new_bullets,
                st.session_state.get("last_source_text"),
            )
            with st.spinner("Re-checking the revised notes..."):
                st.session_state["last_check"] = llm.complete_json(recheck_system, recheck_user)
            st.rerun()

st.divider()

st.header("Your study log")
with st.expander("View full log", expanded=False):
    st.markdown(load_log())
