#!/usr/bin/env python3
"""Publish a generated day's image and/or Reel to Instagram via the Graph API.

Set IG_ACCESS_TOKEN to the Instagram Page token (or run behind an authenticating proxy):
  python3 publish.py --date YYYY-MM-DD [--only image|reel]

Media must already be live on GitHub Pages (BASE_URL). A log in posted.json prevents double posting.
"""
import content as C
import argparse, functools, json, os, sys, time
print = functools.partial(print, flush=True)
import requests

IG_USER = "17841407053927946"  # @oduwacoin, linked to Oduwa Blockchain Solutions Page
FB_PAGE = "154546045188430"  # Oduwa Blockchain Solutions Facebook Page
GRAPH = "https://graph.facebook.com/v21.0"
BASE_URL = "https://oduwax.github.io/oduwacoin-social-posts"
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "posted.json")


def call(method, path, params=None):
    url = f"{GRAPH}/{path}"
    params = dict(params or {})
    if os.environ.get("IG_ACCESS_TOKEN"):
        params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    if method == "GET":
        r = requests.get(url, params=params, timeout=90)
    else:
        r = requests.post(url, data=params, timeout=90)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:600]}")
    return r.json()


def wait_public(url, tries=40):
    for _ in range(tries):
        try:
            # bypass the credential proxy, which only allows graph.facebook.com
            r = requests.head(url, timeout=30, proxies={"https": None, "http": None})
            if r.status_code == 200:
                return r.headers.get("Content-Type")
        except Exception:
            pass
        time.sleep(15)
    raise RuntimeError(f"Media not publicly reachable: {url}")


def wait_container(cid, tries=60):
    for _ in range(tries):
        st = call("GET", cid, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Container {cid} failed: {st}")
        time.sleep(10)
    raise RuntimeError(f"Container {cid} not ready in time")


def publish(kind, date, meta):
    rel = f"media/{date}/" + ("image.jpg" if kind == "image" else "reel.mp4")
    url = f"{BASE_URL}/{rel}"
    ctype = wait_public(url)
    caption = meta[kind]["caption"]
    if kind == "image":
        c = call("POST", f"{IG_USER}/media", {"image_url": url, "caption": caption})
    else:
        c = call("POST", f"{IG_USER}/media", {"media_type": "REELS", "video_url": url, "caption": caption,
                                               "share_to_feed": "true"})
    cid = c["id"]
    wait_container(cid)
    p = call("POST", f"{IG_USER}/media_publish", {"creation_id": cid})
    info = call("GET", p["id"], {"fields": "permalink,timestamp"})
    return dict(media_id=p["id"], permalink=info.get("permalink"), timestamp=info.get("timestamp"),
                theme=meta[kind]["theme"], url=url, content_type=ctype)


def publish_fb(kind, date, meta):
    rel = f"media/{date}/" + ("image.jpg" if kind == "image" else "reel.mp4")
    url = f"{BASE_URL}/{rel}"
    wait_public(url)
    caption = C.facebook_caption(meta[kind]["caption"])
    if kind == "image":
        r = call("POST", f"{FB_PAGE}/photos", {"url": url, "caption": caption, "published": "true"})
        pid = r.get("post_id") or r["id"]
    else:
        r = call("POST", f"{FB_PAGE}/videos", {"file_url": url, "description": caption, "published": "true"})
        pid = r["id"]
    link = None
    try:
        link = call("GET", pid, {"fields": "permalink_url"}).get("permalink_url")
    except Exception:
        pass
    if link and link.startswith("/"):
        link = "https://www.facebook.com" + link
    return dict(id=pid, permalink=link or f"https://www.facebook.com/{pid}", theme=meta[kind]["theme"], url=url)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--only", choices=["image", "reel"])
    ap.add_argument("--platforms", default="instagram,facebook")
    a = ap.parse_args()
    meta = json.load(open(os.path.join(HERE, "media", a.date, "meta.json")))
    log = json.load(open(LOG)) if os.path.exists(LOG) else {}
    day = log.setdefault(a.date, {})
    kinds = [a.only] if a.only else ["image", "reel"]
    plats = a.platforms.split(",")
    ok = True
    for k in kinds:
        jobs = []
        if "instagram" in plats:
            jobs.append((k, "instagram", publish))
        if "facebook" in plats:
            jobs.append((f"fb_{k}", "facebook", publish_fb))
        for key, name, fn in jobs:
            if key in day:
                print(f"{name} {k}: already posted {day[key].get('permalink')}")
                continue
            try:
                day[key] = fn(k, a.date, meta)
                print(f"{name} {k}: posted {day[key]['permalink']}")
            except Exception as e:
                ok = False
                print(f"{name} {k}: FAILED {e}", file=sys.stderr)
            json.dump(log, open(LOG, "w"), indent=2)
    if "instagram" in plats:
        lim = call("GET", f"{IG_USER}/content_publishing_limit", {"fields": "quota_usage,config"})
        print("instagram quota:", json.dumps(lim.get("data")))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
