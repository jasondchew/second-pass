"""Read-only Google Drive mirror of the study log.

Every save rewrites one Google Doc from study_log.md, in place, so its link never changes.
The doc is a mirror, not a second source of truth: edits made in Drive are overwritten.

Uses the narrow `drive.file` scope, which only reaches files this app created, so the app
makes the doc itself on first run. One-time setup:
  1. Put an OAuth "Desktop app" client file at ./credentials.json (gitignored).
  2. Run `python -m src.orchestration.drive_mirror` and click Allow in the browser.
That stores ./token.json and the doc id in ./.drive_mirror.json (both gitignored).
"""
import json
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[2]
CREDENTIALS = ROOT / "credentials.json"
TOKEN = ROOT / "token.json"
STATE = ROOT / ".drive_mirror.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
DOC_TITLE = "Study Journal (Data & AI)"


def render_html(log_text: str) -> str:
    """study_log.md -> HTML Drive converts to a formatted Doc: subjects as headings, each
    entry title as a subheading (both show up in the Docs outline for navigation)."""
    text = log_text.replace("# Study Log", f"# {DOC_TITLE}", 1)

    # Entry lines look like: **Title** _Tag_ &mdash; 2026-09-21  (tag optional)
    def entry(m):
        tag, date = m.group(2), m.group(3)
        return f"### {m.group(1)}\n\n" + (f"_{tag}_ · " if tag else "") + date + "\n"
    text = re.sub(r"^\*\*(.+?)\*\*(?:\s+_(.+?)_)?\s+(?:&mdash;|—)\s+(\S+)\s*$", entry, text, flags=re.M)
    # python-markdown needs blank lines before lists and 4-space nesting
    text = re.sub(r"(?m)^(?!\s*(?:[-*] |\d+[.)] ))(\S.*)\n(?=(?:[-*] |\d+[.)] ))", r"\1\n\n", text)
    text = re.sub(r"^((?:  )+)(?=[-*] |\d+[.)] )", lambda m: "    " * (len(m.group(1)) // 2), text, flags=re.M)
    # keep * literal in arithmetic like (15*1*0.7)
    text = re.sub(r"(?<=[\w)])\s?\*\s?(?=[\w(])", lambda m: m.group(0).replace("*", "\\*"), text)
    body = markdown.markdown(text, extensions=["sane_lists"])

    # No hand-built table of contents: Drive's HTML import drops the anchors, so its links
    # break ("Bookmark no longer exists"). Docs' own outline lists every heading instead.
    intro = (
        "<p><i>Read-only copy of the Second Pass study log, rewritten after every save. "
        "Edits made here will be overwritten. To jump to any entry, open the document "
        "outline: View &gt; Show outline (or the outline icon at the top left of the page).</i></p><hr>"
    )
    i = body.find("<h2")
    body = body[:i] + intro + body[i:] if i >= 0 else intro + body
    return "<html><body>" + body + "</body></html>"


def _service(interactive: bool = False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES) if TOKEN.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
    if not creds or not creds.valid:
        if not interactive:
            raise RuntimeError("Drive isn't connected yet. Run: python -m src.orchestration.drive_mirror")
        from google_auth_oauthlib.flow import InstalledAppFlow
        creds = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS), SCOPES).run_local_server(port=0)
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def is_configured() -> bool:
    return TOKEN.exists() and STATE.exists()


def push(log_path: Path, interactive: bool = False) -> str:
    """Rewrite the mirror doc from the log. Creates the doc on first run. Returns its link."""
    from googleapiclient.http import MediaInMemoryUpload

    svc = _service(interactive)
    media = MediaInMemoryUpload(render_html(log_path.read_text(encoding="utf-8")).encode("utf-8"),
                                mimetype="text/html", resumable=False)
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    if state.get("doc_id"):
        svc.files().update(fileId=state["doc_id"], media_body=media).execute()
    else:
        meta = {"name": DOC_TITLE, "mimeType": "application/vnd.google-apps.document"}
        created = svc.files().create(body=meta, media_body=media, fields="id").execute()
        state["doc_id"] = created["id"]
        STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return f"https://docs.google.com/document/d/{state['doc_id']}/edit"


if __name__ == "__main__":
    print("Mirror updated:", push(ROOT / "study_log.md", interactive=True))
