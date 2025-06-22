import requests
from config import LIMIT, OFFSET
from functools import lru_cache
import time
import ssl
import urllib3

# Disable SSL warnings if we're going to disable verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Session for connection pooling
session = requests.Session()
session.headers.update({"User-Agent": "MangaDownloader/1.0"})

# Add connection pooling with SSL configuration
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=3
)

# Mount adapters
session.mount("http://", adapter)
session.mount("https://", adapter)

# Configure SSL - try different approaches
def configure_ssl_session():
    """Configure session with appropriate SSL settings"""
    try:
        # First try with default SSL context
        session.verify = True
        test_response = session.get("https://api.mangadex.org/", timeout=5)
        print("SSL verification working with default settings")
        return True
    except requests.exceptions.SSLError:
        print("Default SSL failed, trying with custom SSL context...")
        try:
            # Create a custom SSL context that's more permissive
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # This approach works with requests by disabling verification
            session.verify = False
            test_response = session.get("https://api.mangadex.org/", timeout=5)
            print("SSL verification disabled - connection working")
            return True
        except Exception as e:
            print(f"SSL configuration failed: {e}")
            return False
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

# Configure SSL on import
ssl_configured = configure_ssl_session()

def search_manga(title, limit=10):
    """Search for manga with improved error handling and caching"""
    url = f"https://api.mangadex.org/manga"
    params = {
        'title': title,
        'limit': min(limit, 20),  # Limit to prevent too many results
        'includes[]': 'cover_art',
        'order[relevance]': 'desc'
    }
    
    print(f"Searching for manga: {title}")
    try:
        # Add additional headers that might help
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = session.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' not in data:
            print("No data field in response")
            return []
            
        results = []
        for manga in data['data']:
            try:
                manga_id = manga['id']
                attributes = manga['attributes']
                
                # Get title with better fallback
                title = None
                if 'title' in attributes:
                    title_dict = attributes['title']
                    title = (title_dict.get('en') or 
                            title_dict.get('ja-ro') or 
                            title_dict.get('ja') or
                            list(title_dict.values())[0] if title_dict else None)
                
                if not title:
                    continue

                # Get cover filename
                cover_filename = None
                for rel in manga.get('relationships', []):
                    if rel['type'] == 'cover_art' and 'attributes' in rel:
                        cover_filename = rel['attributes'].get('fileName')
                        break

                cover_url = None
                if cover_filename:
                    cover_url = f"https://uploads.mangadex.org/covers/{manga_id}/{cover_filename}.256.jpg"
                
                results.append({
                    'id': manga_id,
                    'title': title,
                    'cover_url': cover_url
                })
                
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error processing manga entry: {e}")
                continue

        return results

    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
        print("Try running the script with SSL verification disabled or update your certificates")
        return []
    except requests.exceptions.Timeout:
        print("Search request timed out")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []
    except (KeyError, ValueError) as e:
        print(f"Error parsing response: {e}")
        return []

def get_chapters(manga_id, limit=LIMIT, offset=OFFSET, chapter_from=None, chapter_to=None):
    """Get chapters with improved error handling and rate limiting"""
    url = f"https://api.mangadex.org/chapter"
    params = {
        'manga': manga_id,
        'translatedLanguage[]': 'en',
        'order[chapter]': 'asc',
        'limit': min(limit, 100),  # API limit
        'offset': offset,
        'contentRating[]': ['safe', 'suggestive', 'erotica']  # Include more content
    }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
        }
        
        response = session.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if 'data' not in data:
            print("No chapters data in response")
            return []
            
        chapters = data['data']
        
        # Filter by chapter range if specified
        if chapter_from is not None:
            filtered = []
            for chapter in chapters:
                try:
                    chap_num = chapter['attributes'].get('chapter', '')
                    if not chap_num:
                        continue
                        
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

    except requests.exceptions.SSLError as e:
        print(f"SSL Error while fetching chapters: {e}")
        return []
    except requests.exceptions.Timeout:
        print("Request timed out while fetching chapters.")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []
    except (KeyError, ValueError) as e:
        print(f"Error parsing chapters response: {e}")
        return []

def get_chapter_images(chapter_id):
    """Get chapter images with better error handling"""
    url = f"https://api.mangadex.org/at-home/server/{chapter_id}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
        }
        
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        server_info = response.json()
        
        if 'chapter' not in server_info:
            raise ValueError("Invalid server response")
            
        chapter_info = server_info['chapter']
        hash_id = chapter_info.get('hash')
        page_filenames = chapter_info.get('data', [])
        
        if not hash_id or not page_filenames:
            raise ValueError("No images found for chapter")
            
        return server_info, hash_id, page_filenames
        
    except requests.exceptions.SSLError as e:
        print(f"SSL Error while getting images: {e}")
        return None, None, []
    except requests.exceptions.RequestException as e:
        print(f"Failed to get chapter images: {e}")
        return None, None, []
    except (KeyError, ValueError) as e:
        print(f"Error parsing images response: {e}")
        return None, None, []

# Clean up session on module exit
import atexit
atexit.register(lambda: session.close())