import os
import re
import requests
from tqdm import tqdm

def download_image(url, path):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(path, 'wb') as f:
            f.write(response.content)
    except Exception as e:
        print(f"Failed to download image {url}: {e}")

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

def download_chapter_images(chapter, manga_title, base_download_path="../manga-downloads"):
    chapter_id = chapter['id']
    chapter_num = chapter['attributes'].get('chapter', 'unknown')
    chapter_title = chapter['attributes'].get('title', '')

    try:
        chapter_label = f"Ch. {int(float(chapter_num)):03}"
    except (ValueError, TypeError):
        chapter_label = f"Ch. {chapter_num or 'unknown'}"

    if chapter_title:
        chapter_label += f" - {chapter_title}"

    safe_manga_title = sanitize_filename(manga_title)
    safe_chapter_label = sanitize_filename(chapter_label)
    folder = os.path.join(base_download_path, safe_manga_title, safe_chapter_label)

    try:
        os.makedirs(folder, exist_ok=True)

        server_url = f"https://api.mangadex.org/at-home/server/{chapter_id}"
        response = requests.get(server_url, timeout=10)
        response.raise_for_status()
        server_info = response.json()

        chapter_info = server_info.get("chapter", {})
        hash_id = chapter_info.get("hash")
        page_filenames = chapter_info.get("data", [])

        if not hash_id or not page_filenames:
            raise ValueError("Invalid server response or no pages found.")

        if os.path.isdir(folder) and len(os.listdir(folder)) >= len(page_filenames):
            print(f"Chapter already fully downloaded: {safe_chapter_label}")
            return folder

        for filename in tqdm(page_filenames, desc=safe_chapter_label):
            img_url = f"{server_info['baseUrl']}/data/{hash_id}/{filename}"
            img_path = os.path.join(folder, filename)

            if os.path.exists(img_path):
                continue  # Skip already downloaded images

            download_image(img_url, img_path)

        return folder
    except Exception as e:
        print(f"Failed to download chapter {chapter_id} ({safe_chapter_label}): {e}")
        return None
