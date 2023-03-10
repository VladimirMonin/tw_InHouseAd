import asyncio
import re

from lxml import html
import aiohttp
import multiprocessing
import datetime
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


async def get_links_async(url):
    """Получение списка ссылок на странице"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                text = await response.text()
                # Поиск ссылок на странице с помощью регулярного выражения
                links = re.findall(r'<a\s+(?:[^>]*?\s+)?href=(["\'])(.*?)\1', text)
                links = [link[1] for link in links if
                         link[1].startswith('/wiki/') and not link[1].startswith('/wiki/Special:')]
                links = ['https://ru.wikipedia.org' + link for link in links]
                return links
    except aiohttp.ClientError as e:
        logger.error(f"Error getting links from {url}: {str(e)}")
        return []


def extend_path(path, link):
    """Добавляет новую ссылку в конец пути"""
    return path + [link]


def bfs(start, end):
    """Поиск в ширину от start до end на википедии"""
    queue = [[start]]  # создаем очередь путей, начинаем с пути из стартовой страницы
    visited = set()  # создаем множество посещенных страниц
    lock = multiprocessing.Lock()  # создаем блокировку для безопасности многопоточности

    pool = multiprocessing.Pool()  # создаем пул процессов

    while queue:
        path = queue.pop(0)  # извлекаем первый путь из очереди
        node = path[-1]  # получаем последнюю страницу в пути

        if node == end:
            pool.close()  # закрываем пул процессов
            pool.join()  # ждем завершения всех процессов
            return path  # возвращаем найденный путь

        elif node not in visited:  # если страница не была посещена
            with lock:
                visited.add(node)  # добавляем страницу в посещенные

            links = asyncio.run(get_links_async(node))  # получаем список ссылок со страницы
            new_paths = pool.starmap(extend_path,
                                     [(path, link) for link in links])  # расширяем текущие пути новыми ссылками

            queue.extend(new_paths)  # добавляем расширенные пути в конец очереди

            logger.debug(
                f"Visited page: {node} at {datetime.datetime.now()}")  # выводим информацию о посещенной странице

    pool.close()  # закрываем пул процессов
    pool.join()  # ждем завершения всех процессов
    return None  # если путь не найден, возвращаем None


start = "https://ru.wikipedia.org/wiki/Xbox_360_S"
end = "https://ru.wikipedia.org/wiki/Nintendo_3DS"

starttime = datetime.datetime.now()
print(f'Запущено в {datetime.datetime.now().strftime("%H:%M:%S")}')

# Рабочее время ~10 минут и 900 пройденных ссылок
path = bfs(start, end)
print(path)
print(f'Завершено в {datetime.datetime.now().strftime("%H:%M:%S")}')
print(f'Потрачено минут на обработку: {(datetime.datetime.now() - starttime) // 60}')

