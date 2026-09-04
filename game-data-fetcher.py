"""
RAWG.io Game Data Fetcher (simple version)
Get a free API key at https://rawg.io/apidocs
"""

import os
import requests

API_KEY = ""  # <-- paste your RAWG API key here
BASE_URL = "https://api.rawg.io/api"
IMAGE_DIR = "media"


def search_game(query):
    """Search RAWG for a game name and return the first match."""
    response = requests.get(
        f"{BASE_URL}/games",
        params={"key": API_KEY, "search": query, "page_size": 1},
        timeout=10,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    return results[0] if results else None


def get_description(game_id):
    """Fetch the full description for a game by its RAWG id."""
    response = requests.get(
        f"{BASE_URL}/games/{game_id}",
        params={"key": API_KEY},
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("description_raw", "")


def get_screenshot_urls(game_id):
    """Fetch a list of screenshot image URLs for a game."""
    response = requests.get(
        f"{BASE_URL}/games/{game_id}/screenshots",
        params={"key": API_KEY},
        timeout=10,
    )
    response.raise_for_status()
    return [shot["image"] for shot in response.json().get("results", [])]


def get_trailer_urls(game_id):
    """Fetch a list of trailer video URLs for a game."""
    response = requests.get(
        f"{BASE_URL}/games/{game_id}/movies",
        params={"key": API_KEY},
        timeout=10,
    )
    response.raise_for_status()
    return [movie["data"]["max"] for movie in response.json().get("results", [])]


def download_file(url, filename, game, retries=3):
    """Download a single file (image or video) to IMAGE_DIR/filename."""
    os.makedirs(os.path.join(IMAGE_DIR, game), exist_ok=True)
    path = os.path.join(IMAGE_DIR, game,  filename)

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            with open(path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return path
        except requests.exceptions.RequestException as e:
            print(f"  Attempt {attempt}/{retries} failed for {filename}: {e}")
            if attempt == retries:
                raise    

def write_readme(name, release_year, description, game):
    """Write the game's release year and description to README.md in IMAGE_DIR."""
    os.makedirs(os.path.join(IMAGE_DIR, game), exist_ok=True)
    path = os.path.join(IMAGE_DIR, game,  "README.md")
    with open(path, "w") as f:
        f.write(f"# {name} ({release_year})\n\n{description}\n")

def main(query):
    game = search_game(query)

    if not game:
        print(f"No results found for '{query}'.")
        return

    release_year = (game.get("released") or "Unknown")[:4]
    description = get_description(game["id"])

    write_readme(game["name"], release_year, description, query)

    # Cover art
    if game.get("background_image"):
        cover_path = download_file(game["background_image"], f"{query}_cover.jpg", query)
        print(f"\nSaved cover art to {cover_path}")

    # Screenshots
    screenshot_urls = get_screenshot_urls(game["id"])
    for i, url in enumerate(screenshot_urls, start=1):
        path = download_file(url, f"{query}_screenshot_{i}.jpg", query)
        print(f"Saved screenshot to {path}")

    # Trailers
    trailer_urls = get_trailer_urls(game["id"])
    for i, url in enumerate(trailer_urls, start=1):
        path = download_file(url, f"{query}_trailer_{i}.mp4", query)
        print(f"Saved trailer to {path}")


with open("game-list.txt", 'r') as f:
    for line in f:
        main(line.rstrip('\n'))
