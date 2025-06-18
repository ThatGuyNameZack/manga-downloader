import requests
from config import LIMIT, OFFSET

def search_manga(title, limit=10):
    url = f"https://api.mangadex.org/manga?title={title}&limit={limit}&includes[]=cover_art"
    print(f"Searching for manga: {title}")
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        results = []
        for manga in data['data']:
            manga_id = manga['id']
            attributes = manga['attributes']
            title = attributes['title'].get('en', list(attributes['title'].values())[0])  # fallback

            # Get cover filename
            cover_filename = None
            for rel in manga['relationships']:
                if rel['type'] == 'cover_art':
                    cover_filename = rel['attributes']['fileName']
                    break

            cover_url = f"https://uploads.mangadex.org/covers/{manga_id}/{cover_filename}" if cover_filename else None
            results.append({
                'id': manga_id,
                'title': title,
                'cover_url': cover_url
            })

        return results

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except KeyError:
        print("error response")
        return []

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