#!/usr/bin/env python3
"""Post a generated day's image or Reel to X using the xurl CLI.

Usage: python3 x_post.py --date YYYY-MM-DD --only image|reel
Requires an authenticated xurl. Uses the same posted.json log to avoid double posting.
"""
import argparse, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "posted.json")
TAGS = "#OduwaCoin #OWC"


def x_text(caption):
    """Shorten the Instagram caption to fit X: first paragraph + link line + 2 hashtags (<=280)."""
    paras = [p.strip() for p in caption.split("\n\n") if p.strip()]
    body = paras[0]
    link = next((p for p in paras[1:] if re.search(r"\b[\w-]+\.(com|io)\b", p)), "")
    link = link.splitlines()[-1].replace(" (link in bio)", "") if link else ""
    if link and link in body:
        link = ""
    budget = 280 - len(TAGS) - (len(link) + 2 if link else 0) - 2
    if len(body) > budget:
        body = body[: budget - 1].rsplit(" ", 1)[0].rstrip(",.;:") + "\u2026"
    return "\n\n".join([p for p in (body, link, TAGS) if p])


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:3])}: {r.stderr.strip() or r.stdout.strip()}"[:600])
    return r.stdout


def find(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            f = find(v, key)
            if f:
                return f
    if isinstance(obj, list):
        for v in obj:
            f = find(v, key)
            if f:
                return f
    return None


def last_json(out):
    for start in [m.start() for m in re.finditer(r"^\{", out, re.M)][::-1]:
        try:
            return json.loads(out[start:])
        except Exception:
            continue
    return json.loads(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--only", choices=["image", "reel"], required=True)
    a = ap.parse_args()
    key = f"x_{a.only}"
    meta = json.load(open(os.path.join(HERE, "media", a.date, "meta.json")))
    log = json.load(open(LOG)) if os.path.exists(LOG) else {}
    day = log.setdefault(a.date, {})
    if key in day:
        print(f"x {a.only}: already posted {day[key].get('permalink')}")
        return
    path = os.path.join(HERE, "media", a.date, "image.jpg" if a.only == "image" else "reel.mp4")
    if a.only == "image":
        up = run(["xurl", "media", "upload", "--category", "tweet_image", "--media-type", "image/jpeg", path])
    else:
        up = run(["xurl", "media", "upload", "--category", "tweet_video", "--media-type", "video/mp4", path])
    media_id = find(last_json(up), "id") or find(last_json(up), "media_id_string") or find(last_json(up), "media_id")
    if not media_id:
        raise RuntimeError(f"No media id in upload response: {up[:300]}")
    text = x_text(meta[a.only]["caption"])
    out = run(["xurl", "post", text, "--media-id", str(media_id)])
    tid = find(last_json(out), "id")
    me = find(json.loads(run(["xurl", "whoami"])), "username") or "i"
    day[key] = dict(id=tid, permalink=f"https://x.com/{me}/status/{tid}", theme=meta[a.only]["theme"])
    json.dump(log, open(LOG, "w"), indent=2)
    print(f"x {a.only}: posted {day[key]['permalink']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"x: FAILED {e}", file=sys.stderr)
        sys.exit(1)
