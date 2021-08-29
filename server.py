"""Основной код приложения."""
import base64
import json
import re
from io import BytesIO
from math import ceil

import pymorphy2
from PIL import Image, ImageDraw
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel


class ParseBody(BaseModel):
    """Тело запроса на парсинг с текстом."""

    text: str


def load_colors():
    """Функция загрузки цветов из файла."""
    with open('colors.json', 'r') as f:
        codenames, rgb = {}, {}
        for color in json.loads(f.read()):
            codenames.update({color['name']: color['color']})
            rgb.update({color['name']: tuple(int(el) for el in color['rgb'])})
    return codenames, rgb


colors_codenames, colors_rgb = load_colors()
app = FastAPI()
morph = pymorphy2.MorphAnalyzer(lang='ru')


@app.get('/', response_class=HTMLResponse)
def index():
    """
    Обработчик индекстовой страницы.

    Отдает сразу файл с index.html, потому что ради одного файла
    шаблонизатор не стал подключать.
    """
    with open('index.html', 'r') as tmpl:
        return tmpl.read()


@app.post('/parse')
def parse(body: ParseBody):
    """Обработчик запроса на парсинг текста."""
    text_colors = []
    for word in re.findall(r'[a-zA-Zа-яА-Я-]+', body.text.lower()):
        norm = parse_word(word)
        if not norm:
            continue
        text_colors.append({'word': word, 'norm': norm,
                            'color': colors_codenames[norm]})
    body, status = draw_image(text_colors)
    body.update({'colors': text_colors})
    return JSONResponse(body, status_code=status)


def parse_word(word):
    """
    Парсинг слова в цвет, если это цвет.

    Рекурсивно вызывает себя для каждой части, если в тексте есть '-'.
    """
    parsed = [p for p in morph.parse(word) if 'ADJF' in p.tag]
    if not parsed:
        return
    parsed = parsed[0]
    norm = parsed.normal_form.replace('ё', 'е')

    inner_words = []
    if '-' in norm:
        for inner_word in norm.split('-'):
            inner_words.append(parse_word(inner_word))
    inner_words = list(filter(lambda el: el in colors_codenames.keys(),
                              inner_words))

    if norm not in colors_codenames.keys() and not inner_words:
        return

    if norm in colors_codenames.keys():
        return norm

    if inner_words:
        return inner_words[0]


def draw_image(text_colors):
    """Функция рисования картинки по переданным цветам."""
    if len(text_colors) < 1:
        return {'error': 'Цвета в тексте не найдено!'}, 400

    block_size = 40
    length = 1000

    row_size = length / block_size
    rows = ceil(len(text_colors) / row_size)
    height = block_size * (rows + 1)

    image = Image.new('RGBA', (length, height))
    draw = ImageDraw.Draw(image)

    start_x, start_y = 0, 0
    end_y = block_size
    for color in text_colors:
        end_x = start_x + block_size
        draw.rectangle(((start_x, start_y), (end_x, end_y)),
                       fill=colors_rgb[color['norm']])
        draw.line(((end_x, 0), (end_x, end_y)), fill=(0, 0, 0), width=3)
        start_x = end_x
        if start_x > length:
            start_x = 0
            start_y = start_y + block_size
            end_y = end_y + block_size

    buffered = BytesIO()
    image.save(buffered, format='PNG')
    code = base64.b64encode(buffered.getvalue()).decode('utf-8')

    pic = f'<img style = "width:100%;" src="data:image/png;base64, {code}" />'
    return {'pic': pic}, 200
