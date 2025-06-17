import requests

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

def get_chapters(manga_id, limit=5, offset=0): #offseet for beyond than 5 chapters mate
    url = f"https://api.mangadex.org/chapter?manga={manga_id}&translatedLanguage[]=en&order[chapter]=asc&limit={limit}&offset={offset}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()['data']
    except requests.exceptions.Timeout:
        print("Request timed out while fetching chapters.")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except KeyError:
        print("Unexpected response format when fetching chapters.")
    return []
