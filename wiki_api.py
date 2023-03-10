from multiprocessing import Lock, Process, Queue, Manager
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




# Создание объекта блокировки
lock = Lock()

# Создание экземпляра Wikipedia API
wiki = wikipediaapi.Wikipedia('ru')


def get_links(title):
    page = wiki.page(title)
    if not page.exists():
        return None
    links = page.links.keys()
    return {title: [link for link in links]}


def bfs_worker(start_title, end_title, visited, result_queue):
    # Создание пустой очереди
    queue = Queue()
    # Помещение стартового заголовка в очередь
    queue.put(([start_title], start_title))

    while not queue.empty():
        # Извлечение следующего пути и последнего заголовка из очереди
        path, last_title = queue.get()

        # Использование блокировки для синхронизации доступа к общей переменной visited
        with visited.get_lock():
            if last_title in visited:
                continue
            visited.add(last_title)

        if last_title == end_title:
            # Если достигнут конечный заголовок, помещаем путь в очередь результатов
            result_queue.put(path)
            break

        links = get_links(last_title)
        if links is None:
            continue

        for link_title in links[last_title]:
            if link_title not in visited:
                new_path = path + [link_title]
                queue.put((new_path, link_title))


def bfs(start_title, end_title, num_processes=10):
    # Создание множества, в которое будут добавляться уже посещенные страницы
    visited = Manager().list()

    # Создание очереди результатов
    result_queue = Queue()

    # Создание списка процессов
    processes = []
    for i in range(num_processes):
        p = Process(target=bfs_worker, args=(start_title, end_title, visited, result_queue))
        p.start()
        processes.append(p)

    # Ожидание завершения всех процессов
    for p in processes:
        p.join()

    # Извлечение первого найденного пути из очереди результатов
    if not result_queue.empty():
        return result_queue.get()

    return None


starttime = datetime.datetime.now()
print(f'Запущено в {starttime}')
start_links = 'Xbox_360_S'
end_links = 'Nintendo_3DS'
path = bfs(start_links, end_links)
print(path)
print(f'Потрачено минут на обработку: {(datetime.datetime.now() - starttime) // 60}')
