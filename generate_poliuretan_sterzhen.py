from PIL import Image, ImageDraw
import argparse
import os

from generate_cards import draw_value_with_unit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE = os.path.join(BASE_DIR, 'layouts', 'polyurethane-rods.png')
DATA_FILE = os.path.join(BASE_DIR, 'data', 'polyurethane-rods-sizes.txt')
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'Montserrat-Black.ttf')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'polyurethane-rods')

LENGTH_CLEAR = (148, 1068, 305, 1112)
LENGTH_BG = (251, 251, 251)
LENGTH_DIGIT_LEFT = 153
LENGTH_BASE_Y = 1108
LENGTH_DIGIT_H = 34
LENGTH_UNIT_H = 17
LENGTH_UNIT_OFFSET = 0
LENGTH_SPACING = 14

DIAMETER_CLEAR = (458, 1068, 615, 1112)
DIAMETER_BG = (251, 251, 251)
DIAMETER_DIGIT_LEFT = 463
DIAMETER_BASE_Y = 1108
DIAMETER_DIGIT_H = 34
DIAMETER_UNIT_H = 17
DIAMETER_UNIT_OFFSET = 0
DIAMETER_SPACING = 14


def load_sizes(data_path):
    with open(data_path, 'r', encoding='cp1251') as f:
        lines = f.read().splitlines()

    sizes = []
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split('\t')
        if len(cols) < 2:
            continue
        diameter = ''.join(ch for ch in cols[0].strip() if ch.isdigit())
        length = ''.join(ch for ch in cols[1].strip() if ch.isdigit())
        if diameter and length:
            sizes.append((int(diameter), int(length)))

    return sizes


def generate_card(template_path, font_path, diameter, length, output_path):
    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)

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
        description='Generate Ozon size cards for Rusbelt polyurethane rods.'
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
        filename = f"{diameter}мм_{length}мм_полиуретан_стержень.png"
        output_path = os.path.join(args.output_dir, filename)
        generate_card(args.template, FONT_PATH, diameter, length, output_path)
        print(f"Generated: {filename}")

    print(f"\nTotal generated: {len(sizes)}")


if __name__ == '__main__':
    main()
