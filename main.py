import os
import json
from tqdm import tqdm
from api_utils import search_manga, get_chapters
from download_utils import download_chapter_images
from page_order import rename_images_in_folder
from config import LIMIT, OFFSET


limit = LIMIT  # How many chapters to download at once

LOG_PATH = "log.json"  # so it won't download the same chapter like a fool

def load_log():
    if not os.path.exists(LOG_PATH):
        return {"downloaded_chapters": []}
    with open(LOG_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"downloaded_chapters": []}

def save_log(log):
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=4)

def main():
    title = input("Enter the manga title: ").strip()
    if not title:
        print("No title provided.")
        return

    range_input = input("which chapters do you want to donwload?").strip()

    chapter_from = None
    chapter_to = None

    if "-" in range_input:
        chapter_from, chapter_to = map(float, range_input.split("-"))
    elif range_input:
        chapter_from = float(range_input)

    manga_id = search_manga(title)
    if not manga_id:
        print("Could not get manga info.")
        return

    log = load_log()


    offset = OFFSET # Reset offset for each run
    
    while True:
        chapters = get_chapters(manga_id, limit=LIMIT, offset=OFFSET, chapter_from=chapter_from, chapter_to=chapter_to)
        if not chapters:
            print("No more chapters found.")
            break

        print(f"Found {len(chapters)} chapters (offset={OFFSET}). Starting download...\n")


        for chapter in tqdm(chapters, desc="Chapters Downloaded", unit="chapter"):
            chapter_id = chapter["id"]

            if chapter_id in log["downloaded_chapters"]:
                print(f"Skipping already downloaded chapter {chapter_id}")
                continue

            chapter_folder = download_chapter_images(chapter, title)
            rename_images_in_folder(chapter_folder)

            log["downloaded_chapters"].append(chapter_id)
            save_log(log)

            new_chapters_downloaded = True

        # Always increment offset to move to next batch
        offset += limit

        # Only break if we got fewer chapters than the limit (meaning we've reached the end)
        if len(chapters) < limit:
            print("Reached the end of available chapters.")
            break

if __name__ == "__main__":
    main()