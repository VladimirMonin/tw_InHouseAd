import asyncio
import re
import requests
from bs4 import BeautifulSoup
import aiohttp
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


async def bfs(start, end):
    """Поиск в ширину от start до end на википедии"""
    visited = set()  # создаем множество посещенных страниц

    async def get_links_and_extend_path(path):
        """Получение списка ссылок на странице и расширение текущих путей"""
        node = path[-1]  # получаем последнюю страницу в пути
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(node) as response:
                    text = await response.text()
                    # Поиск ссылок на странице с помощью регулярного выражения
                    links = re.findall(r'<a\s+(?:[^>]*?\s+)?href=(["\'])(.*?)\1', text)
                    links = [link[1] for link in links if
                             link[1].startswith('/wiki/') and not link[1].startswith('/wiki/Special:')]
                    links = ['https://ru.wikipedia.org' + link for link in links]
                    # расширяем текущие пути новыми ссылками
                    new_paths = [path + [link] for link in links]
                    return new_paths
        except aiohttp.ClientError as e:
            logger.error(f"Error getting links from {node}: {str(e)}")
            return []

    queue = [[start]]  # создаем очередь путей, начинаем с пути из стартовой страницы

    while queue:
        path = queue.pop(0)  # извлекаем первый путь из очереди
        node = path[-1]  # получаем последнюю страницу в пути

        if node == end:
            return path  # возвращаем найденный путь

        elif node not in visited:  # если страница не была посещена
            visited.add(node)  # добавляем страницу в посещенные

            # получаем список ссылок со страницы и расширяем текущие пути
            new_paths = await asyncio.create_task(get_links_and_extend_path(path))

            queue.extend(new_paths)  # добавляем расширенные пути в конец очереди

            logger.debug(
                f"Visited page: {node} at {datetime.datetime.now().strftime('%H:%M:%S')}")  # выводим информацию о посещенной странице

    return None  # если путь не найден, возвращаем None


def print_paragraph_with_link(path):
    """Вывод на экран результатов работы. Ищет абзац текста в котором есть ссылка на следующую страницу"""
    print(f'Полный путь: {path}\n\n')
    for idx, link in enumerate(path):
        next_idx = (idx + 1) % len(path)  # индекс следующей ссылки
        next_link = path[next_idx]  # следующая ссылка
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            if next_link.replace('https://ru.wikipedia.org', '') in str(p):
                print(f'{idx + 1}) Ссылка:\n{link}\nНайдена в тексте:\n{p.text.strip()}'
                      f'\n__________________________________________________\n')
                break
        else:
            print(f'{idx + 1}) Текст не найден. Вероятно это последняя ссылка в пути:\n{link}'
                  f'\n__________________________________________________\n')


async def main():
    start = input("Введите ссылку...\nНапример https://ru.wikipedia.org/wiki/Xbox_360_S :")
    end = input("Введите ссылку...\nНапример https://ru.wikipedia.org/wiki/Nintendo_3DS. :")

    print(f'Запущено в {datetime.datetime.now().strftime("%H:%M:%S")}')
    asyncio.get_running_loop()
    path = await bfs(start, end)
    print_paragraph_with_link(path)
    print(f'Завершено в {datetime.datetime.now().strftime("%H:%M:%S")}')


if __name__ == '__main__':
    asyncio.run(main())


