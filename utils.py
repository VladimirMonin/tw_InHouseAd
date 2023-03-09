import requests
from bs4 import BeautifulSoup
import logging

# Создание логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Создание обработчика файлового логгера
file_handler = logging.FileHandler('log.txt')
file_handler.setLevel(logging.DEBUG)

# Создание форматтера
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger.addHandler(file_handler)


def get_links(url):
    """Получение списка ссылок на странице"""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith('/wiki/') and not href.startswith('/wiki/Special:'):
                links.append('https://ru.wikipedia.org' + href)
        return links
    except Exception as e:
        logger.error(f"Error getting links from {url}: {str(e)}")
        return []


def find_path(start_url, end_url):
    """Поиск пути между двумя страницами"""
    visited_pages = set()
    queue = [[start_url]]
    while queue:
        path = queue.pop(0)
        current_page = path[-1]
        logger.debug(f"Visiting page {current_page}")
        if current_page == end_url:
            return path
        elif current_page not in visited_pages:
            visited_pages.add(current_page)
            for link in get_links(current_page):
                new_path = list(path)
                new_path.append(link)
                queue.append(new_path)
    logger.warning("Path not found")
    return []


def main():
    start_url = input("Введите ссылку на стартовую страницу: ")
    end_url = input("Введите ссылку на конечную страницу: ")
    if not start_url.startswith('https://ru.wikipedia.org') or not end_url.startswith('https://ru.wikipedia.org'):
        print("Ссылки должны быть из wikipedia")
        return

    path = find_path(start_url, end_url)
    if not path:
        print("Путь не найден")
        return

    print("Результат работы:")
    for i, page in enumerate(path):
        print(f"{i + 1}------------------------")
        try:
            response = requests.get(page)
            soup = BeautifulSoup(response.content, 'html.parser')
            for p in soup.find_all('p'):
                if page in str(p):
                    print(p.text.strip())
                    for link in get_links(page):
                        if link in str(p):
                            print(f"Ссылка: {link}")
                    if i < len(path) - 1:
                        print(f"Следующая страница: {path[i + 1]}\n")
                    else:
                        print()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting page {page}: {str(e)}")

