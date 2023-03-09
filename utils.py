import threading
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
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting links from {url}: {str(e)}")
        return []


def process_page(queue, visited_pages, current_page, end_url):
    logger.debug(f"Visiting page {current_page}")
    if current_page not in visited_pages:
        visited_pages.add(current_page)
        for link in get_links(current_page):
            if link == end_url:
                return [current_page, link]
            if link not in visited_pages:
                queue.append(link)
    return None

def find_path(start_url, end_url):
    """Поиск пути между двумя страницами"""
    visited_pages = set()
    queue = [start_url]
    threads = []
    while queue:
        current_page = queue.pop(0)
        if current_page == end_url:
            return [current_page]
        threads = [t for t in threads if t.is_alive()]
        if len(threads) < 25:
            t = threading.Thread(target=process_page, args=(queue, visited_pages, current_page, end_url))
            t.start()
            threads.append(t)
    logger.warning("Path not found")
    return []


def find_paragraph(start_url, end_url):
    """Поиск первого абзаца текста на странице start_url, в котором встречается ссылка на страницу end_url"""
    end_url = end_url.replace('https://ru.wikipedia.org', '')
    try:
        response = requests.get(start_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        for p in soup.find_all('p'):
            if end_url in str(p):
                return p.text.strip()
        return "Url not found"
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting page {start_url}: {str(e)}")
        return "Error. Url not found"


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
            paragraph = find_paragraph(page, end_url)
            if not paragraph:
                print(f"Абзац с ссылкой на {end_url} не найден")
            else:
                print(paragraph)
                print(f"Ссылка на {end_url}: {page}\n")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting page {page}: {str(e)}")
