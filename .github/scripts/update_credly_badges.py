#!/usr/bin/env python3
"""Refresh the Credly badge section in the profile README.

Credly's /size/WxH image URLs redirect to the original asset, often
600x600. GitHub renders markdown images at that intrinsic size, so the
profile shows huge badges. HTML img width and height are honored.
"""

from __future__ import annotations

import html
import json
import urllib.request
from pathlib import Path

USER = "christian-brandlehner"
START = "<!--START_SECTION:badges-->"
END = "<!--END_SECTION:badges-->"
SIZE = 120
README = Path(__file__).resolve().parents[2] / "README.md"
API = f"https://www.credly.com/users/{USER}/badges.json"


def fetch_badges() -> list[dict]:
    badges: list[dict] = []
    url: str | None = API
    while url:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "cbrandlehner-profile-readme",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
        badges.extend(payload.get("data") or [])
        url = (payload.get("metadata") or {}).get("next_page_url")
    return badges


def badge_line(badge: dict) -> str | None:
    if badge.get("is_private_badge") or badge.get("state") != "accepted":
        return None
    template = badge.get("badge_template") or {}
    name = template.get("name") or "Credly badge"
    image = badge.get("image_url") or (badge.get("image") or {}).get("url")
    badge_id = badge.get("id")
    if not image or not badge_id:
        return None
    alt = html.escape(name, quote=True)
    src = html.escape(image, quote=True)
    href = html.escape(f"https://www.credly.com/badges/{badge_id}", quote=True)
    return (
        f'<a href="{href}"><img src="{src}" alt="{alt}" '
        f'width="{SIZE}" height="{SIZE}"></a>'
    )


def render(badges: list[dict]) -> str:
    # Credly's default listing is the order already shown on the profile.
    lines = [line for badge in badges if (line := badge_line(badge))]
    if not lines:
        raise SystemExit("Credly returned no badges; leaving README unchanged")
    return "\n".join(lines)


def replace_section(readme: str, body: str) -> str:
    start = readme.find(START)
    end = readme.find(END)
    if start < 0 or end < 0 or end < start:
        raise SystemExit("badge markers not found in README.md")
    prefix = readme[: start + len(START)]
    suffix = readme[end:]
    return f"{prefix}\n{body}\n{suffix}"


def main() -> None:
    body = render(fetch_badges())
    original = README.read_text(encoding="utf-8")
    updated = replace_section(original, body)
    if updated == original:
        print("Badges unchanged")
        return
    README.write_text(updated, encoding="utf-8")
    print(f"Updated {body.count(chr(10)) + 1} badges")


if __name__ == "__main__":
    main()
