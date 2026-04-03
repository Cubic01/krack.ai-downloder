import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def load_cookies_from_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cookies = {}

    if isinstance(data, list):
        for item in data:
            if "name" in item and "value" in item:
                cookies[item["name"]] = item["value"]
    elif isinstance(data, dict):
        cookies = data

    return cookies


cookies = load_cookies_from_json("cookies.txt")

headers = {
    "User-Agent": "Mozilla/5.0"
}


COURSE_URL = "https://krack.ai/courses/learn-ukulele/"
DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_file(url, folder):
    filename = url.split("/")[-1].split("?")[0]
    filepath = os.path.join(folder, filename)

    if os.path.exists(filepath):
        print(f"Skipping: {filename}")
        return

    print(f"Downloading: {filename}")

    r = requests.get(url, headers=headers, cookies=cookies, stream=True)

    with open(filepath, "wb") as f:
        for chunk in r.iter_content(1024):
            if chunk:
                f.write(chunk)

def get_lessons(course_url):
    print("Fetching lessons...")

    r = requests.get(course_url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(r.text, "html.parser")

    lessons = []
    current_group = "Unknown"

    # iterate in order
    for el in soup.find_all(["h3", "h4", "a"]):

        # group titles (sections)
        if el.name in ["h3", "h4"]:
            text = el.text.strip()
            if text:
                current_group = text

        # lesson links
        if el.name == "a" and el.get("href"):
            href = el["href"]
            if "/lesson/" in href:
                lessons.append({
                    "url": href,
                    "group": current_group
                })

    return lessons

def process_lesson(lesson):
    url = lesson["url"]
    group_name = lesson["group"]

    print(f"\nVisiting: {url}")
    print(f"Saving to: {group_name}")

    r = requests.get(url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(r.text, "html.parser")

    group_folder = os.path.join(DOWNLOAD_DIR, group_name)
    os.makedirs(group_folder, exist_ok=True)

    # videos
    for tag in soup.find_all(["video", "source"]):
        src = tag.get("src")
        if src and ".mp4" in src:
            download_file(urljoin(url, src), group_folder)

    # pdfs
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href:
            download_file(urljoin(url, href), group_folder)

lessons = get_lessons(COURSE_URL)

print(f"Found {len(lessons)} lessons")

for lesson in lessons:
    process_lesson(lesson)

print("Done")