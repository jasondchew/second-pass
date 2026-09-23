"""Fetch a link to the resource the notes are about, so the accuracy check has a real source
of truth instead of relying on the model's memory alone.

Deliberately dependency-light (requests + stdlib HTMLParser). It handles ordinary text/HTML
pages. It does NOT handle YouTube (no transcript access), PDFs, or pages that only render via
JavaScript or sit behind a login/paywall - for those it returns a clear error rather than
pretending it has a source, so the app never labels something "checked against your source"
when it wasn't.
"""
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests

MAX_BYTES = 2_000_000
MAX_CHARS = 30_000  # what gets handed to the model; enough for a long article
MIN_USABLE_CHARS = 400  # below this the page almost certainly didn't render real content
TIMEOUT_SECONDS = 15
USER_AGENT = "Mozilla/5.0 (compatible; SecondPass/1.0; personal study tool)"

SKIP_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form", "svg", "iframe"}
BLOCK_TAGS = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section", "article", "pre", "blockquote"}
VIDEO_HOSTS = ("youtube.com", "youtu.be", "vimeo.com")


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self._skip_depth += 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip_depth and data.strip():
            self.parts.append(data)


def _html_to_text(html: str) -> str:
    extractor = _TextExtractor()
    extractor.feed(html)
    lines = (" ".join(line.split()) for line in "".join(extractor.parts).splitlines())
    return "\n".join(line for line in lines if line)


def fetch_source(url: str) -> tuple[str | None, str | None]:
    """Returns (text, error). Exactly one is None."""
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None, "That doesn't look like a web link (it needs to start with http:// or https://)."
    if any(parsed.netloc.lower().endswith(h) for h in VIDEO_HOSTS):
        return None, (
            "Video links can't be read (no transcript access), so this link can't act as a source. "
            "If there's a transcript or written version of it, link that instead."
        )
    try:
        response = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS, stream=True
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        if "html" not in content_type and "text/plain" not in content_type:
            return None, f"That link isn't a web page or plain text (it's {content_type or 'unknown type'}), so it can't be read as a source."
        raw = response.raw.read(MAX_BYTES, decode_content=True)
        response.encoding = response.encoding or "utf-8"
        body = raw.decode(response.encoding, errors="replace")
    except requests.RequestException as e:
        return None, f"Couldn't open that link ({type(e).__name__}). Check it loads in your browser, or that it isn't behind a login."

    text = _html_to_text(body) if "html" in content_type else body.strip()
    if len(text) < MIN_USABLE_CHARS:
        return None, (
            "The page came back with almost no readable text - it probably needs JavaScript to "
            "load, or it's behind a login/paywall. It can't act as a source."
        )
    return text[:MAX_CHARS], None
