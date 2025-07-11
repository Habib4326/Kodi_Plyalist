#!/usr/bin/env python3
# kodi_movies_xml_clean.py
# ------------------------
# ২০২৫→২০০০ পর্যন্ত স্ক্যান করে শুধুই  "Title (Year)" ফরম্যাট দেয়

import re, sys, os, urllib.parse as up, requests, xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

ROOT_URL        = "http://10.1.1.1/data/Animation%20Movies/"
OUT_FILE        = "Animation-Movies.xml"
FALLBACK_IMAGE  = "https://example.com/fallback/animation.png"
ALLOWED_VIDEO   = (".mkv", ".mp4", ".avi", ".ts", ".webm")
IMAGE_EXT       = (".jpg", ".jpeg", ".png", ".webp")

# ---------- HELPER ----------
def get_links(url):
    html = requests.get(url, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.select("a"):
        href = a.get("href")
        if href and href not in ("../", "./"):
            yield href, a.text.strip()

def first_image(url):
    for href, _ in get_links(url):
        if href.lower().endswith(IMAGE_EXT):
            return up.urljoin(url, href)
    return None

def is_video(name): return name.lower().endswith(ALLOWED_VIDEO)

def clean_title(raw_name: str) -> str:
    """
    ফাইল/ফোল্ডার নাম থেকে  
    • এক্সটেনশন/ব্র্যাকেট/ব্রেস/রেজল্যুশন/এনকোডিং সরিয়ে  
    • শুধু মুভির নাম + (Year) রিটার্ন করে
    """
    # path/extension বাদ
    base = os.path.splitext(os.path.basename(raw_name))[0]

    # সেপারেটরগুলোকে স্পেস বানাই
    base = re.sub(r"[._\-]+", " ", base)

    # প্রথম 4-digit year ধরব
    m_year = re.search(r"(19|20)\d{2}", base)
    year = m_year.group(0) if m_year else ""

    # বছরসহ অংশের আগে পর্যন্তই শিরোনাম
    title_part = base[:m_year.start()].strip() if m_year else base.strip()

    # বাড়তি টোকেন/ব্র্যাকেট সরাই
    title_part = re.sub(r"\[.*?\]|\(.*?\)|\{.*?\}", "", title_part).strip()

    # ফরমান করে রিটার্ন
    return f"{title_part} ({year})" if year else title_part

# ---------- XML বিল্ড ----------
def build_xml():
    root_xml = ET.Element("library")

    for year in range(2025, 1999, -1):
        year_folder = f"({year})"
        year_block  = ET.SubElement(root_xml, "movies", year=str(year))
        year_url    = up.urljoin(ROOT_URL, year_folder + "/")

        try:
            links = list(get_links(year_url))
        except Exception:
            continue          # ওই বছরের ফোল্ডার নেই

        for href, human in links:
            if "1080" in human:
                continue

            full_url = up.urljoin(year_url, href)

            # ---------------- সাব-ফোল্ডার ----------------
            if href.endswith("/"):
                thumb = first_image(full_url) or FALLBACK_IMAGE

                video_url, raw_title = None, human
                for ihref, iname in get_links(full_url):
                    if is_video(ihref) and "1080" not in iname:
                        video_url  = up.urljoin(full_url, ihref)
                        raw_title  = iname
                        break
                if not video_url:
                    continue
            # ---------------- সরাসরি ফাইল ----------------
            else:
                if not is_video(href):
                    continue
                video_url = full_url
                raw_title = human
                thumb     = FALLBACK_IMAGE

            # শিরোনাম ক্লিন করি
            video_title = clean_title(raw_title)

            # XML <movie>
            mv = ET.SubElement(year_block, "movie")
            ET.SubElement(mv, "title").text      = video_title
            ET.SubElement(mv, "link").text       = video_url
            ET.SubElement(mv, "thumbnail").text  = thumb
            ET.SubElement(mv, "fanart").text     = thumb

    return ET.ElementTree(root_xml)

# ---------- main ----------
def main():
    print("[+] Kodi XML build শুরু …")
    tree = build_xml()
    tree.write(OUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"✅  {OUT_FILE} তৈরি হয়েছে!")

if __name__ == "__main__":
    try:
        import bs4
    except ImportError:
        sys.exit("pip install requests beautifulsoup4")

    main()