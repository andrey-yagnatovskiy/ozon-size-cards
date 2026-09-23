from PIL import Image, ImageDraw, ImageFont
import argparse
import openpyxl
import os
import subprocess
import platform

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_sizes(excel_path):
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    sizes = []
    for row in ws.iter_rows(min_row=1, values_only=True):
        vals = []
        for c in row[:3]:
            if c is None:
                vals.append('')
            else:
                s = str(c).strip()
                num = ''.join(ch for ch in s if ch.isdigit())
                vals.append(num)
        if all(vals):
            sizes.append(vals)
    return sizes


def find_font_size_for_height(draw, text, font_path, target_h):
    lo, hi = 10, 200
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        f = ImageFont.truetype(font_path, mid)
        bb = draw.textbbox((0, 0), text, font=f)
        th = bb[3] - bb[1]
        if th <= target_h:
            best = f
            lo = mid + 1
        else:
            hi = mid - 1
    if best is None:
        best = ImageFont.truetype(font_path, 10)
    return best


def draw_value_with_unit(draw, font_path, digit_text, unit_text,
                         digit_left, base_y, digit_target_h, unit_target_h,
                         unit_bottom_offset=0, color=(0, 0, 0, 255), spacing=4,
                         dry_run=False):
    """
    Рисует цифру и единицу измерения рядом.
    Цифра выравнивается по нижней линии base_y.
    Единица измерения рисуется меньшим шрифтом, её нижний край
    смещён вверх на unit_bottom_offset относительно base_y.
    При dry_run=True возвращает ширину текста без рисования.
    """
    digit_font = find_font_size_for_height(draw, digit_text, font_path, digit_target_h)
    bb_digit = draw.textbbox((0, 0), digit_text, font=digit_font)
    digit_w = bb_digit[2] - bb_digit[0]
    digit_h = bb_digit[3] - bb_digit[1]
    digit_y = base_y - digit_h

    unit_font = find_font_size_for_height(draw, unit_text, font_path, unit_target_h)
    bb_unit = draw.textbbox((0, 0), unit_text, font=unit_font)
    unit_h = bb_unit[3] - bb_unit[1]
    unit_y = base_y - unit_bottom_offset - unit_h
    unit_x = digit_left + digit_w + spacing

    text_width = unit_x + (bb_unit[2] - bb_unit[0]) - digit_left

    if not dry_run:
        draw.text((digit_left, digit_y), digit_text, font=digit_font, fill=color)
        draw.text((unit_x, unit_y), unit_text, font=unit_font, fill=color)

    return text_width


def generate_image(template_path, font_path, thickness, width, length, output_path,
                   bg_color=(255, 255, 255, 255)):
    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)

    configs = [
        {
            'name': 'length',
            'clear': (150, 1050, 320, 1118),
            'digit_left': 176,
            'digit': str(length),
            'unit': 'м',
            'digit_h': 48,
            'unit_h': 25,
            'unit_offset': 10,
        },
        {
            'name': 'width',
            'clear': (410, 1050, 620, 1118),
            'digit_left': 426,
            'digit': str(width),
            'unit': 'см',
            'digit_h': 48,
            'unit_h': 25,
            'unit_offset': 10,
        },
        {
            'name': 'thickness',
            'clear': (735, 1050, 920, 1118),
            'digit_left': 760,
            'digit': str(thickness),
            'unit': 'мм',
            'digit_h': 48,
            'unit_h': 25,
            'unit_offset': 10,
        },
    ]

    for cfg in configs:
        draw.rectangle(cfg['clear'], fill=bg_color)
        draw_value_with_unit(
            draw, font_path,
            cfg['digit'], cfg['unit'],
            cfg['digit_left'], 1110,
            cfg['digit_h'], cfg['unit_h'], cfg['unit_offset']
        )

    img.save(output_path)


def load_logo(logo_path, target_width=200):
    logo = Image.open(logo_path)
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')
    ratio = target_width / logo.width
    target_height = int(logo.height * ratio)
    logo = logo.resize((target_width, target_height), Image.Resampling.LANCZOS)
    return logo


def find_inkscape():
    """Возвращает путь к inkscape.exe, если доступен."""
    if platform.system() == 'Windows':
        default = r'C:\Program Files\Inkscape\bin\inkscape.exe'
        if os.path.exists(default):
            return default
    for cmd in ('inkscape', 'inkscape.exe'):
        for path in os.environ.get('PATH', '').split(os.pathsep):
            full = os.path.join(path, cmd)
            if os.path.exists(full):
                return full
    return None


def convert_svg_to_png(svg_path, png_path, dpi=300):
    inkscape = find_inkscape()
    if inkscape is None:
        raise RuntimeError('Inkscape не найден. Установите Inkscape или укажите путь.')
    subprocess.run([
        inkscape, svg_path,
        '--export-type=png',
        f'--export-filename={png_path}',
        f'--export-dpi={dpi}',
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def paste_logo(img, logo, right_margin=20, top_margin=20):
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    x = img.width - logo.width - right_margin
    y = top_margin
    img.paste(logo, (x, y), logo)
    return img


def generate_image_conv(template_path, font_path, thickness, width, length, output_path,
                        logo_path=None):
    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)
    bg = (237, 235, 234, 255)

    configs = [
        {
            'name': 'length',
            'digit_left': 170,
            'digit': str(length),
            'unit': 'м',
            'digit_h': 48,
            'unit_h': 22,
            'unit_offset': 12,
        },
        {
            'name': 'width',
            'digit_left': 450,
            'digit': str(width),
            'unit': 'см',
            'digit_h': 48,
            'unit_h': 22,
            'unit_offset': 12,
        },
        {
            'name': 'thickness',
            'digit_left': 770,
            'digit': str(thickness),
            'unit': 'мм',
            'digit_h': 48,
            'unit_h': 22,
            'unit_offset': 12,
        },
    ]

    for cfg in configs:
        draw_value_with_unit(
            draw, font_path,
            cfg['digit'], cfg['unit'],
            cfg['digit_left'], 1110,
            cfg['digit_h'], cfg['unit_h'], cfg['unit_offset']
        )

    if logo_path:
        logo = load_logo(logo_path)
        img = paste_logo(img, logo)

    img.save(output_path)


def main_rubber(template=None, excel=None, output_dir=None,
                  font_path=None, logo_svg=None, logo_png=None):
    template = template or os.path.join(BASE_DIR, 'layouts', 'belt.png')
    excel = excel or os.path.join(BASE_DIR, 'data', 'belt-sizes.xlsx')
    font_path = font_path or os.path.join(BASE_DIR, 'fonts', 'Montserrat-Black.ttf')
    logo_svg = logo_svg or os.path.join(BASE_DIR, 'assets', 'logo-rusbelt.svg')
    logo_png = logo_png or os.path.join(BASE_DIR, 'assets', 'logo-rusbelt.png')
    output_dir = output_dir or os.path.join(BASE_DIR, 'output', 'belt')

    os.makedirs(output_dir, exist_ok=True)
    if not os.path.exists(logo_png):
        convert_svg_to_png(logo_svg, logo_png)
        print(f"Converted logo: {logo_png}")
    sizes = load_sizes(excel)

    for thickness, width, length in sizes:
        filename = f"{thickness}мм{width}см{length}м_резиновая_лента.png"
        output_path = os.path.join(output_dir, filename)
        generate_image_conv(template, font_path, thickness, width, length, output_path,
                            logo_path=logo_png)
        print(f"Generated: {filename}")

    print(f"\nTotal generated: {len(sizes)}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate Ozon size cards for Rusbelt rubber-coated belt.'
    )
    parser.add_argument('--template', default=None,
                        help='Path to the clean PNG template')
    parser.add_argument('--excel', default=None,
                        help='Path to the Excel file with sizes')
    parser.add_argument('--output-dir', default=None,
                        help='Output directory for generated cards')
    args = parser.parse_args()

    main_rubber(
        template=args.template,
        excel=args.excel,
        output_dir=args.output_dir,
    )


if __name__ == '__main__':
    main()
