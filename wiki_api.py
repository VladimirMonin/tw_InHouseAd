import wikipediaapi
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


wiki = wikipediaapi.Wikipedia('ru')


def get_links(title):
    page = wiki.page(title)
    if not page.exists():
        return None
    links = page.links.keys()
    return {title: [link for link in links]}


def bfs(start_title, end_title):
    start_links = get_links(start_title)

    visited = set()
    queue = [(start_links, [start_title])]

    while queue:
        (links, path) = queue.pop(0)
        last_title = path[-1]

        if last_title in visited:
            continue
        visited.add(last_title)

        if last_title == end_title:
            return path

        for link_title in links[last_title]:
            if link_title not in visited:
                new_links = links.copy()
                link_links = get_links(link_title)
                if link_links is not None:
                    new_links[last_title] += link_links
                    new_path = path + [link_title]
                    queue.append((new_links, new_path))
                    logger.debug(f'Processed page: {link_title}')

    return None


starttime = datetime.datetime.now()
print(f'Запущено в {starttime}')
start_links = 'Xbox_360_S'
end_links = 'Nintendo_3DS'
path = bfs(start_links, end_links)
print(path)
print(f'Потрачено минут на обработку: {(datetime.datetime.now() - starttime) // 60}')
