import json
import os
import requests
from dotenv import load_dotenv

# Файлы из env.
load_dotenv()

# Достаем апишку
API_KEY = os.getenv("API_KEY")

# Проверка с ключом
if API_KEY is None:
    print("Ошибка: добавьте апи ключ в файл .env")
    exit()

BASE_URL = "https://kinopoiskapiunofficial.tech"
COOKIE_FILE = "cookies.json"

GENRES = {
    "триллер": 1,
    "драма": 2,
    "криминал": 3,
    "мелодрама": 4,
    "детектив": 5,
    "фантастика": 6,
    "приключения": 7,
    "биография": 8,
    "фильм-нуар": 9,
    "вестерн": 10,
    "боевик": 11,
    "фэнтези": 12,
    "комедия": 13,
    "военный": 14,
    "история": 15,
    "музыка": 16,
    "ужасы": 17,
    "мультфильм": 18,
    "семейный": 19,
    "мюзикл": 20,
    "спорт": 21,
    "документальный": 22,
    "короткометражка": 23,
    "аниме": 24,
}


def load_cookies():
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {
        "genre_name": None,
        "genre_id": None,
        "liked_ids": [],
        "seen_ids": [],
    }


def save_cookies(data):
    with open(COOKIE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def fetch_api(endpoint, params=None):
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers={"X-API-KEY": API_KEY},
            params=params,
            timeout=5,
        )
    except requests.exceptions.RequestException as e:
        print(f"Сбой сети при подключении к серверу: {e}")
        return None

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка API: сервер вернул код {response.status_code}")
        return None


def choose_genre(cookies):
    # Проверяем, сохранен ли жанр
    if cookies.get("genre_id") is not None:
        saved_name = cookies["genre_name"]
        choice = (
            input(
                f"У вас сохранен жанр «{saved_name}». Продолжить с ним? (да/нет): "
            )
            # обработка чтобы принимал текст типа дА Да НеТ нЕт и тд
            .strip()
            .lower()
        )

        if choice in ("да", "д", "yes", "y", ""):
            print(f"Отлично, продолжаем подборку в жанре «{saved_name}»!")
            return

    # Если жанр не сохранен или пользователь захотел выбрать новый
    print("\nДоступные жанры:", ", ".join(GENRES.keys()))

    while True:
        genre_input = (
            input("Введите название жанра из списка: ").strip().lower()
        )
        if genre_input in GENRES:
            cookies["genre_name"] = genre_input
            cookies["genre_id"] = GENRES[genre_input]
            save_cookies(cookies)
            print(f"Выбран и сохранен жанр: «{genre_input}»")
            break
        else:
            print(
                "Такого жанра нет в списке. Попробуйте еще раз (например: комедия, драма)."
            )


# --- Стартуем
cookies = load_cookies()
choose_genre(cookies)

# --- Пагинашка
page = 1
while True:
    params = {"genres": cookies["genre_id"], "page": page}
    data = fetch_api("/api/v2.2/films", params=params)

    if not data or not data.get("items"):
        print("Подборки по этому жанру закончились.")
        break

    print(f"\n--- Страница {page} ---")
    for film in data["items"]:
        film_id = film["kinopoiskId"]
        if film_id not in cookies["seen_ids"]:
            name = film.get("nameRu") or film.get("nameEn") or "Без названия"
            year = film.get("year") or "н/д"
            rating = film.get("ratingKinopoisk") or "нет"
            print(f"[ID: {film_id}] {name} ({year}) — Рейтинг: {rating}")
            cookies["seen_ids"].append(film_id)

    next_page = input("\nПоказать следующую страницу? (да/нет): ").strip().lower()
    if next_page in ("да", "д", "yes", "y"):
        page += 1
    else:
        break

#похожие фильмы и по лайку
fav = input("\nВведите ID понравившегося фильма (или Enter, чтобы пропустить): ").strip()
if fav.isdigit():
    cookies["liked_ids"].append(int(fav))
    print("Фильм добавлен в понравившиеся!")

if cookies["liked_ids"]:
    last_id = cookies["liked_ids"][-1]
    similars = fetch_api(f"/api/v2.2/films/{last_id}/similars")
    if similars and similars.get("items"):
        print("\nПохожие фильмы:")
        for item in similars["items"][:3]:
            sim_name = item.get("nameRu") or item.get("nameEn") or "Без названия"
            print(f"- {sim_name} (ID: {item['filmId']})")

save_cookies(cookies)
print("\nДанные сохранены в cookies.json!")
