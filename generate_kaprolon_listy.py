from PIL import Image, ImageDraw
import argparse
import os

from generate_cards import draw_value_with_unit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE = os.path.join(BASE_DIR, 'layouts', 'kaprolon-sheets.png')
DATA_FILE = os.path.join(BASE_DIR, 'data', 'kaprolon-sheets-sizes.txt')
FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'Montserrat-Black.ttf')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output', 'kaprolon-sheets')

THICKNESS_CLEAR = (740, 1035, 870, 1095)
THICKNESS_BG = (253, 253, 252)
THICKNESS_DIGIT_LEFT = 748
THICKNESS_BASE_Y = 1084
THICKNESS_DIGIT_H = 31
THICKNESS_UNIT_H = 16
THICKNESS_UNIT_OFFSET = 1
THICKNESS_SPACING = 14


def load_thicknesses(data_path):
    with open(data_path, 'r', encoding='cp1251') as f:
        lines = f.read().splitlines()

    thicknesses = []
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split('\t')
        if len(cols) < 3:
            continue
        raw = cols[2].strip()
        num = ''.join(ch for ch in raw if ch.isdigit())
        if num:
            thicknesses.append(int(num))

    return sorted(set(thicknesses))


def generate_card(template_path, font_path, thickness, output_path):
    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)

    draw.rectangle(THICKNESS_CLEAR, fill=THICKNESS_BG)
    draw_value_with_unit(
        draw, font_path,
        str(thickness), 'мм',
        THICKNESS_DIGIT_LEFT, THICKNESS_BASE_Y,
        THICKNESS_DIGIT_H, THICKNESS_UNIT_H,
        unit_bottom_offset=THICKNESS_UNIT_OFFSET,
        spacing=THICKNESS_SPACING,
    )

    img.save(output_path)


def main():
    parser = argparse.ArgumentParser(
        description='Generate Ozon size cards for Rusbelt kaprolon (PA-6) sheets.'
    )
    parser.add_argument('--template', default=TEMPLATE)
    parser.add_argument('--data', default=DATA_FILE)
    parser.add_argument('--output-dir', default=OUTPUT_DIR)
    parser.add_argument('--only-first', action='store_true',
                        help='Generate only the first size (for a test run)')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    thicknesses = load_thicknesses(args.data)

    if args.only_first:
        thicknesses = thicknesses[:1]

    for thickness in thicknesses:
        filename = f"{thickness}мм_капролон_листовой_ПА6.png"
        output_path = os.path.join(args.output_dir, filename)
        generate_card(args.template, FONT_PATH, thickness, output_path)
        print(f"Generated: {filename}")

    print(f"\nTotal generated: {len(thicknesses)}")


if __name__ == '__main__':
    main()
