from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import PythonLexer, YamlLexer
from pygments.styles import get_style_by_name

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
FONT = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 22)
TITLE = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 30)
SMALL = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 21)
STYLE = get_style_by_name('monokai')


def render(source, name, subtitle, ranges):
    lines = (ROOT / source).read_text(encoding='utf-8').splitlines()
    rows = []
    for index, (start, end) in enumerate(ranges):
        if index:
            rows.append((None, '... omitted source lines ...'))
        rows.extend((n, lines[n - 1]) for n in range(start, min(end, len(lines)) + 1))
    width = max(1180, int(max(FONT.getlength(s) for _, s in rows)) + 150)
    height = 170 + len(rows) * 31
    img = Image.new('RGB', (width, height), '#10151f')
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((16, 16, width - 16, height - 16), 16, fill='#1b2130')
    draw.text((38, 30), source, font=TITLE, fill='#f1f5ff')
    draw.text((38, 77), subtitle, font=SMALL, fill='#aebcd4')
    draw.line((38, 119, width - 38, 119), fill='#364155', width=2)
    lexer = YamlLexer() if source.endswith('.yaml') else PythonLexer()
    for i, (number, code) in enumerate(rows):
        y = 137 + i * 31
        if number is None:
            draw.text((110, y), code, font=FONT, fill='#8290a8')
            continue
        draw.text((36, y), str(number).rjust(4), font=FONT, fill='#7b8ba7')
        x = 110
        for token, value in lex(code, lexer):
            value = value.rstrip('\n')
            while token not in STYLE._styles:
                token = token.parent
            color = STYLE.style_for_token(token)['color'] or 'e6edf3'
            draw.text((x, y), value, font=FONT, fill='#' + color)
            x += FONT.getlength(value)
    img.save(OUT / name)


render('backend/main.py', 'backend-main.png',
       'AI model integration | Ollama request, token parsing, and streamed response',
       [(17, 19), (135, 153), (174, 200)])
render('compose.yaml', 'compose.png',
       'Containerization | Services, environment variables, and Docker service discovery',
       [(1, 27)])
render('frontend/app.py', 'frontend-app.png',
       'Full-stack implementation | Chat input, API request, and live response display',
       [(1162, 1171), (1235, 1264), (1277, 1304)])
