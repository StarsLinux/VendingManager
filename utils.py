import requests
from datetime import datetime, UTC, timezone, timedelta
from bs4 import BeautifulSoup

def get_first_image_url(url):
    # Проверяем, является ли url кортежем и извлекаем значение
    if isinstance(url, tuple):
        url = url[0]
    
    # Убедимся, что URL не пустой и имеет правильный формат
    if not url or not isinstance(url, str):
        return ''
    
    try:
        # Добавляем схему, если она отсутствует
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.ya.ru/',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        response = requests.get(url,headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.select('img.img-with-alt')
        correct_imgs = []
        
        for img in img_tags:
            alt = img.get('alt', '').strip()
            if img and 'src' in img.attrs and alt != "Логотип":
                correct_imgs.append(img.get('src', '').strip())
        
        # Проверяем корректность URL для изображений
        for i in range(len(correct_imgs)):
            img_url = correct_imgs[i]
            if not img_url.startswith(('http://', 'https://')):
                from urllib.parse import urljoin
                correct_imgs[i] = urljoin(url, img_url)

        if len(correct_imgs) == 0:
            return ''
            
        return correct_imgs[0]
        
    except (requests.RequestException, AttributeError) as e:
        print(f"Ошибка при получении изображения: {e}")
        return ''

def gen_activity_date(date):
    now = datetime.now(UTC)
    diff = now - date.astimezone(timezone.utc)
    seconds = diff.total_seconds()
    def pluralize(n, forms):
        n = abs(n)
        if n % 10 == 1 and n % 100 != 11:
            return forms[0]
        elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
            return forms[1]
        else:
            return forms[2]

    # Склонения для русского языка
    units = [
        (365*24*3600, ('год', 'года', 'лет')),
        (30*24*3600, ('месяц', 'месяца', 'месяцев')),
        (7*24*3600, ('неделя', 'недели', 'недель')),
        (24*3600, ('день', 'дня', 'дней')),
        (3600, ('час', 'часа', 'часов')),
        (60, ('минуту', 'минуты', 'минут')),
        (1, ('секунду', 'секунды', 'секунд'))
    ]

    for duration, names in units:
        if seconds >= duration:
            count = int(seconds // duration)
            return f"{count} {pluralize(count, names)} назад"
    
    return 'недавно'