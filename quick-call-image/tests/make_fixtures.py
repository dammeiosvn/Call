"""Optional synthetic OCR images. Use only in Quick Call Image Test."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent / 'fixtures'
ROOT.mkdir(exist_ok=True)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
CASES = {
    'vn-single': ['COUNTRY: VN +84', 'Recipient phone:', '0912 345 678'],
    'vn-multiple-tax': ['COUNTRY: VN +84', 'Tax ID: 0312345678',
                        'Recipient: 0912 345 678', 'Store: 0987 654 321'],
    'us-fictional': ['COUNTRY: US +1', 'Phone: +1 (201) 555-0123'],
}
for name, lines in CASES.items():
    image = Image.new('RGB', (1200, 900), '#f3f6fa')
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((45, 45, 1155, 855), radius=28, fill='white', outline='#d0d8e4', width=3)
    draw.text((85, 90), 'QuickCall · OCR TEST FIXTURE', fill='#1442a3', font=ImageFont.truetype(FONT, 40))
    draw.line((85, 165, 1115, 165), fill='#d0d8e4', width=3)
    for i, line in enumerate(lines):
        draw.text((85, 225 + i * 104), line, fill='#111827', font=ImageFont.truetype(FONT, 42))
    draw.text((85, 735), 'DO NOT CALL · USE THE TEST VERSION', fill='#b42318', font=ImageFont.truetype(FONT, 33))
    image.save(ROOT / (name + '.png'), optimize=True)
print('Generated', len(CASES), 'synthetic images')
