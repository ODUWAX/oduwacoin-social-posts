#!/usr/bin/env python3
"""Post a generated day's image or Reel to X using the xurl CLI.

Usage: python3 x_post.py --date YYYY-MM-DD --only image|reel
Requires an authenticated xurl. Uses the same posted.json log to avoid double posting.
"""
import argparse, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "posted.json")
TAGS = "#OduwaCoin #OWC"
# X charges far more for posts that contain a URL, so links are left out unless X_LINKS=1.
X_LINKS = os.environ.get("X_LINKS", "0") == "1"
DOMAIN = re.compile(r"\b(?:https?://)?(?:www\.)?[\w-]+(?:\.[\w-]+)*\.(?:com|io|org|net)\b[\w/#?=&.-]*")


def x_text(caption):
    """Fit the caption to X: hook + main message (+ link if X_LINKS=1) + 2 hashtags, <=280 chars."""
    import content as C
    paras = [p.strip() for p in caption.split("\n\n") if p.strip()]
    hooks = {h for hs in C.HOOKS.values() for h in hs}
    has_hook = any(paras[0].startswith(h) for h in hooks) and len(paras) > 1
    hook = paras[0] if has_hook else ""
    rest = paras[1:] if has_hook else paras
    body = rest[0]
    link = next((p for p in rest[1:] if re.search(r"\b[\w-]+\.(com|io)\b", p)), "")
    link = link.splitlines()[-1].replace(" (link in bio)", "") if link else ""
    if link and link in body:
        link = ""
    if not X_LINKS:
        link = ""
        body = DOMAIN.sub(lambda m: "the link in our bio" + "." * (len(m.group()) - len(m.group().rstrip("."))), body)
    head = f"{hook}\n\n{body}" if hook else body
    budget = 280 - len(TAGS) - (len(link) + 2 if link else 0) - 2
    if len(head) > budget:
        head = head[: budget - 1].rsplit(" ", 1)[0].rstrip(",.;:") + "\u2026"
    return "\n\n".join([p for p in (head, link, TAGS) if p])


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
    """Return the last JSON object in xurl output (it may print status lines after the JSON)."""
    out = re.sub(r"\x1b\[[0-9;]*m", "", out)
    dec = json.JSONDecoder()
    for start in [m.start() for m in re.finditer(r"^\{", out, re.M)][::-1]:
        try:
            return dec.raw_decode(out[start:])[0]
        except Exception:
            continue
    return json.loads(out)


def wait_processed(media_id, timeout=300):
    """X processes videos after upload; posting before it finishes gives "media IDs are invalid"."""
    import time
    end = time.time() + timeout
    while time.time() < end:
        info = find(last_json(run(["xurl", "media", "status", media_id])), "processing_info") or {}
        state = info.get("state")
        if state == "succeeded" or not info:
            return
        if state == "failed":
            raise RuntimeError(f"X video processing failed: {info}")
        time.sleep(max(2, int(info.get("check_after_secs", 3))))
    raise RuntimeError("X video processing timed out")


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
    if a.only == "reel":
        wait_processed(str(media_id))
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
