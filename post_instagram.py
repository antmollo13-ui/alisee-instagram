#!/usr/bin/env python3
"""
Posta un'immagine su Instagram via Graph API ufficiale (2 step: crea container -> pubblica).

Uso locale (per testare PRIMA di automatizzare):
  set IG_USER_ID=1784xxxxxxxxx           (Windows PowerShell: $env:IG_USER_ID="...")
  set IG_ACCESS_TOKEN=EAAG...            (token long-lived)
  python post_instagram.py --image-url "https://.../snap.png" --caption "testo"

Requisiti: pip install requests
"""
import os
import sys
import time
import argparse
import requests

# Percorso "Instagram API con login di Instagram" -> base graph.instagram.com.
# Se invece usi il percorso con login Facebook (via Pagina), imposta:
#   IG_API_BASE=https://graph.facebook.com/v21.0
API = os.environ.get("IG_API_BASE", "https://graph.instagram.com/v21.0")


def create_container(ig_id, token, image_url, caption):
    r = requests.post(
        f"{API}/{ig_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token},
        timeout=60,
    )
    if not r.ok:
        sys.exit(f"[ERRORE create container] {r.status_code}: {r.text}")
    return r.json()["id"]


def wait_ready(cid, token, tries=10, delay=3):
    # Per le immagini è quasi sempre pronto subito; questa poll evita il raro race condition.
    for _ in range(tries):
        r = requests.get(
            f"{API}/{cid}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        if r.ok and r.json().get("status_code") == "FINISHED":
            return
        if r.ok and r.json().get("status_code") == "ERROR":
            sys.exit(f"[ERRORE container] {r.text}")
        time.sleep(delay)


def publish(ig_id, token, cid):
    r = requests.post(
        f"{API}/{ig_id}/media_publish",
        data={"creation_id": cid, "access_token": token},
        timeout=60,
    )
    if not r.ok:
        sys.exit(f"[ERRORE publish] {r.status_code}: {r.text}")
    return r.json()["id"]


def get_user_id(token):
    r = requests.get(
        f"{API}/me",
        params={"fields": "user_id", "access_token": token},
        timeout=30,
    )
    if not r.ok:
        sys.exit(f"[ERRORE lettura account] {r.status_code}: {r.text}")
    j = r.json()
    return j.get("user_id") or j.get("id")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image-url", required=True, help="URL PUBBLICO dell'immagine")
    p.add_argument("--caption", default="", help="testo del post")
    p.add_argument("--caption-file", help="in alternativa, file .txt con la caption")
    a = p.parse_args()

    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token:
        sys.exit("Manca IG_ACCESS_TOKEN nelle variabili d'ambiente.")
    # se non passi IG_USER_ID, lo ricava da solo dal token
    ig_id = os.environ.get("IG_USER_ID") or get_user_id(token)

    caption = a.caption
    if a.caption_file:
        with open(a.caption_file, encoding="utf-8") as f:
            caption = f.read().strip()

    cid = create_container(ig_id, token, a.image_url, caption)
    print("Container creato:", cid)
    wait_ready(cid, token)
    post_id = publish(ig_id, token, cid)
    print("PUBBLICATO! Post ID:", post_id)


if __name__ == "__main__":
    main()
