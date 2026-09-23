"""Веб-интерфейс генератора карточек размеров для Ozon.

Запуск:
    python app.py
Затем открыть http://127.0.0.1:5000
"""

import io
import os
import zipfile

from flask import Flask, abort, redirect, render_template, send_file, url_for
from PIL import Image

import generate_kaprolon_listy as kaprolon_sheets
import generate_kaprolon_sterzhni as kaprolon_rods
import generate_poliuretan_list as polyurethane_sheets
import generate_poliuretan_sterzhen as polyurethane_rods

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PREVIEW_WIDTH = 420

app = Flask(__name__)


def sheets_line(module, filename_template):
    """Линейка с одним изменяемым размером — толщиной листа."""

    def rows():
        return [(value,) for value in module.load_thicknesses(module.DATA_FILE)]

    def generate():
        os.makedirs(module.OUTPUT_DIR, exist_ok=True)
        names = []
        for (thickness,) in rows():
            filename = filename_template.format(thickness=thickness)
            module.generate_card(
                module.TEMPLATE, module.FONT_PATH, thickness,
                os.path.join(module.OUTPUT_DIR, filename),
            )
            names.append(filename)
        return names

    return rows, generate


def rods_line(module, filename_template):
    """Линейка с двумя изменяемыми размерами — диаметром и длиной стержня."""

    def rows():
        return list(module.load_sizes(module.DATA_FILE))

    def generate():
        os.makedirs(module.OUTPUT_DIR, exist_ok=True)
        names = []
        for diameter, length in rows():
            filename = filename_template.format(diameter=diameter, length=length)
            module.generate_card(
                module.TEMPLATE, module.FONT_PATH, diameter, length,
                os.path.join(module.OUTPUT_DIR, filename),
            )
            names.append(filename)
        return names

    return rows, generate


def build_line(key, title, material, substitutes, columns, module, rows, generate):
    return {
        'key': key,
        'title': title,
        'material': material,
        'substitutes': substitutes,
        'columns': columns,
        'layout': os.path.relpath(module.TEMPLATE, BASE_DIR).replace('\\', '/'),
        'data_file': os.path.relpath(module.DATA_FILE, BASE_DIR).replace('\\', '/'),
        'output_dir': module.OUTPUT_DIR,
        'rows': rows,
        'generate': generate,
    }


LINES = {}

for _key, _title, _material, _subs, _cols, _module, _factory, _pattern in [
    (
        'kaprolon-sheets', 'Капролон листовой', 'Капролон ПА-6',
        'толщина', ('Толщина, мм',), kaprolon_sheets, sheets_line,
        '{thickness}мм_капролон_листовой_ПА6.png',
    ),
    (
        'kaprolon-rods', 'Капролон стержневой', 'Капролон ПА-6',
        'диаметр и длина', ('Диаметр, мм', 'Длина, мм'), kaprolon_rods, rods_line,
        '{diameter}мм_капролон_стержневой_ПА6.png',
    ),
    (
        'polyurethane-sheets', 'Полиуретан листовой', 'Полиуретан',
        'толщина', ('Толщина, мм',), polyurethane_sheets, sheets_line,
        '{thickness}мм_полиуретан_листовой.png',
    ),
    (
        'polyurethane-rods', 'Полиуретан стержневой', 'Полиуретан',
        'диаметр и длина', ('Диаметр, мм', 'Длина, мм'), polyurethane_rods, rods_line,
        '{diameter}мм_{length}мм_полиуретан_стержень.png',
    ),
]:
    _rows, _generate = _factory(_module, _pattern)
    LINES[_key] = build_line(
        _key, _title, _material, _subs, _cols, _module, _rows, _generate,
    )


def get_line(key):
    line = LINES.get(key)
    if line is None:
        abort(404)
    return line


def ready_files(line):
    """Список уже сгенерированных карточек линейки."""
    output_dir = line['output_dir']
    if not os.path.isdir(output_dir):
        return []
    return sorted(f for f in os.listdir(output_dir) if f.lower().endswith('.png'))


@app.route('/')
def index():
    cards = []
    for line in LINES.values():
        try:
            sizes_count = len(line['rows']())
            error = None
        except OSError as exc:
            sizes_count, error = 0, str(exc)
        cards.append({
            'line': line,
            'sizes_count': sizes_count,
            'ready_count': len(ready_files(line)),
            'error': error,
        })
    return render_template('index.html', cards=cards)


@app.route('/line/<key>')
def line_detail(key):
    line = get_line(key)
    return render_template(
        'line.html',
        line=line,
        rows=line['rows'](),
        files=ready_files(line),
        generated=False,
    )


@app.route('/line/<key>/generate', methods=['POST'])
def line_generate(key):
    line = get_line(key)
    line['generate']()
    return redirect(url_for('line_result', key=key))


@app.route('/line/<key>/result')
def line_result(key):
    line = get_line(key)
    return render_template(
        'line.html',
        line=line,
        rows=line['rows'](),
        files=ready_files(line),
        generated=True,
    )


@app.route('/preview/<key>/<path:filename>')
def preview(key, filename):
    line = get_line(key)
    if filename not in ready_files(line):
        abort(404)
    image = Image.open(os.path.join(line['output_dir'], filename))
    ratio = PREVIEW_WIDTH / image.width
    image = image.resize(
        (PREVIEW_WIDTH, int(image.height * ratio)), Image.Resampling.LANCZOS,
    )
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')


@app.route('/download/<key>')
def download(key):
    line = get_line(key)
    files = ready_files(line)
    if not files:
        abort(404)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for filename in files:
            archive.write(os.path.join(line['output_dir'], filename), filename)
    buffer.seek(0)
    return send_file(
        buffer, mimetype='application/zip',
        as_attachment=True, download_name=f'{key}.zip',
    )


if __name__ == '__main__':
    app.run(debug=True)
