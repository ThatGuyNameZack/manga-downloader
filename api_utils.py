import requests
from config import LIMIT, OFFSET

def search_manga(title):
    url = f"https://api.mangadex.org/manga?title={title}&limit=1"
    print(f"Searching for manga: {title}")
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data['data'][0]['id']
    except requests.exceptions.Timeout:
        print("Request timed out. Please check your internet connection.")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except (KeyError, IndexError):
        print("Manga not found or unexpected response format.")
    return None

def get_chapters(manga_id, limit=LIMIT, offset=OFFSET, chapter_from=None, chapter_to=None): #offset for beyond than 5 chapters mate
    url = f"https://api.mangadex.org/chapter?manga={manga_id}&translatedLanguage[]=en&order[chapter]=asc&limit={limit}&offset={offset}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        chapters = res.json()['data']
    
        if chapter_from is not None:
                        filtered = []
                        for chapter in chapters:
                            chap_num = chapter['attributes'].get('chapter', '')
                            try:
                                chap_float = float(chap_num)
                                if chapter_to is not None:
                                    if float(chapter_from) <= chap_float <= float(chapter_to):
                                        filtered.append(chapter)
                                else:
                                    if chap_float == float(chapter_from):
                                        filtered.append(chapter)
                            except (ValueError, TypeError):
                                continue
                        return filtered

        return chapters

    except requests.exceptions.Timeout:
        print("Request timed out while fetching chapters.")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except KeyError:
        print("Unexpected response format when fetching chapters.")
    return []