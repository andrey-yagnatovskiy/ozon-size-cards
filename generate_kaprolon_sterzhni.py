from PIL import Image, ImageDraw
import argparse
import os

from generate_cards import draw_value_with_unit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE = os.path.join(BASE_DIR, 'layouts', 'kaprolon-rods.png')
DATA_FILE = os.path.join(BASE_DIR, 'data', 'kaprolon-rods-sizes.txt')
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'Montserrat-Black.ttf')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'kaprolon-rods')

# Длина 1000 мм уже отрисована в шаблоне дизайнером.
# Перерисовываем блок «Длина» только для других значений.
TEMPLATE_LENGTH = 1000

LENGTH_CLEAR = (138, 1055, 305, 1100)
LENGTH_BG = (251, 251, 251)
LENGTH_DIGIT_LEFT = 146
LENGTH_BASE_Y = 1084
LENGTH_DIGIT_H = 32
LENGTH_UNIT_H = 16
LENGTH_UNIT_OFFSET = 3
LENGTH_SPACING = 6

DIAMETER_CLEAR = (445, 1050, 575, 1100)
DIAMETER_BG = (252, 252, 252)
DIAMETER_DIGIT_LEFT = 451
DIAMETER_BASE_Y = 1094
DIAMETER_DIGIT_H = 32
DIAMETER_UNIT_H = 16
DIAMETER_UNIT_OFFSET = 1
DIAMETER_SPACING = 14


def load_sizes(data_path):
    with open(data_path, 'r', encoding='cp1251') as f:
        lines = f.read().splitlines()

    sizes = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split('\t')
        if len(cols) < 2:
            continue
        diameter = ''.join(ch for ch in cols[0].strip() if ch.isdigit())
        length = ''.join(ch for ch in cols[1].strip() if ch.isdigit())
        if diameter and length:
            sizes[int(diameter)] = int(length)

    return sorted(sizes.items())


def generate_card(template_path, font_path, diameter, length, output_path):
    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)

    if length != TEMPLATE_LENGTH:
        draw.rectangle(LENGTH_CLEAR, fill=LENGTH_BG)
        draw_value_with_unit(
            draw, font_path,
            str(length), 'мм',
            LENGTH_DIGIT_LEFT, LENGTH_BASE_Y,
            LENGTH_DIGIT_H, LENGTH_UNIT_H,
            unit_bottom_offset=LENGTH_UNIT_OFFSET,
            spacing=LENGTH_SPACING,
        )

    draw.rectangle(DIAMETER_CLEAR, fill=DIAMETER_BG)
    draw_value_with_unit(
        draw, font_path,
        str(diameter), 'мм',
        DIAMETER_DIGIT_LEFT, DIAMETER_BASE_Y,
        DIAMETER_DIGIT_H, DIAMETER_UNIT_H,
        unit_bottom_offset=DIAMETER_UNIT_OFFSET,
        spacing=DIAMETER_SPACING,
    )

    img.save(output_path)


def main():
    parser = argparse.ArgumentParser(
        description='Generate Ozon size cards for Rusbelt kaprolon (PA-6) rods.'
    )
    parser.add_argument('--template', default=TEMPLATE)
    parser.add_argument('--data', default=DATA_FILE)
    parser.add_argument('--output-dir', default=OUTPUT_DIR)
    parser.add_argument('--only-first', action='store_true',
                        help='Generate only the first size (for a test run)')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    sizes = load_sizes(args.data)

    if args.only_first:
        sizes = sizes[:1]

    for diameter, length in sizes:
        filename = f"{diameter}мм_капролон_стержневой_ПА6.png"
        output_path = os.path.join(args.output_dir, filename)
        generate_card(args.template, FONT_PATH, diameter, length, output_path)
        print(f"Generated: {filename}")

    print(f"\nTotal generated: {len(sizes)}")


if __name__ == '__main__':
    main()
