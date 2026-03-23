from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
ARTBOOK_DIR = ROOT / "artbook"
OUTPUT_DIR = ROOT / "artbook_v2"

TITLE = "CREPULIN ENFANT"
SUBTITLE = "concept artbook"


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts") / name,
        Path("C:/Windows/Fonts") / "arial.ttf",
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


FONT_TITLE = load_font("georgiab.ttf", 74)
FONT_SUBTITLE = load_font("georgia.ttf", 28)
FONT_HEADING = load_font("georgiab.ttf", 34)
FONT_BODY = load_font("segoeui.ttf", 22)
FONT_SMALL = load_font("segoeui.ttf", 20)


PAGES = [
    {
        "source": "page01_cover_base.png",
        "output": "page01_cover.png",
        "mode": "cover",
        "heading": TITLE,
        "body": "A visual field guide to Block Nine, the DetnDimension, and the domestic horrors that gather around Enfant.",
    },
    {
        "source": "page02_toc_base.png",
        "output": "page02_table_of_contents.png",
        "mode": "toc",
        "heading": "Table of Contents",
        "body": "03  Enfant Design Sheet\n04  Block Nine Exterior\n05  The DetnDimension\n06  Crepulin Lifecycle\n07  Domov Keeper / Keyhole Kikimora\n08  Babka Kuroles and the Threshold Hut\n09  The Black Road Pursuit\n10  Bird Over Reactor Nine\n11  Ritual Tools\n12  Legalities\n13  Rear Cover",
    },
    {
        "source": "page02_enfant_design.png",
        "output": "page03_enfant_design.png",
        "mode": "standard",
        "heading": "Enfant Design Sheet",
        "body": "Enfant is framed as a small, stubborn survivor whose silhouette must stay readable against cavernous Soviet interiors. The oversized coat, bruised palette, and observant stance emphasize vulnerability without surrender.",
    },
    {
        "source": "page03_block_nine.png",
        "output": "page04_block_nine.png",
        "mode": "standard",
        "heading": "Block Nine Exterior",
        "body": "Block Nine establishes the game's oppressive scale: endless concrete repetition, dead communal spaces, and tiny human figures swallowed by architecture. The courtyard is mundane first, then quietly wrong the longer you look.",
    },
    {
        "source": "page04_detn_dimension.png",
        "output": "page05_detn_dimension.png",
        "mode": "standard",
        "heading": "The DetnDimension",
        "body": "The DetnDimension is not a separate fantasy realm but a folded copy of home space under psychic pressure. Gravity, geometry, and domestic familiarity all slip at once, turning rooms into predatory puzzles.",
    },
    {
        "source": "page05_crepulin_lifecycle.png",
        "output": "page06_crepulin_lifecycle.png",
        "mode": "standard",
        "heading": "Crepulin Lifecycle",
        "body": "Crepulin behaves like an urban mold fed by fear, neglect, and unresolved bargains. Each stage becomes less biological and more architectural, until infestation starts rewriting the room itself.",
    },
    {
        "source": "page06_domov_kikimora.png",
        "output": "page07_domov_kikimora.png",
        "mode": "standard",
        "heading": "Domov Keeper / Keyhole Kikimora",
        "body": "These two figures define the house-spirit logic of the game: one preserves thresholds through ritual order, the other exploits every crack, keyhole, and moment of neglect. They should feel like opposing readings of the same home.",
    },
    {
        "source": "page07_babka_hut.png",
        "output": "page08_babka_hut.png",
        "mode": "standard",
        "heading": "Babka Kuroles",
        "body": "Babka Kuroles is a guide only in the transactional sense. Her hut and posture signal warmth, but every kindness still comes with a cost measured in memory, safety, or future leverage.",
    },
    {
        "source": "page08_black_volga.png",
        "output": "page09_black_volga.png",
        "mode": "standard",
        "heading": "The Black Road Pursuit",
        "body": "The Black Volga sequence pushes Soviet urban legend into chase grammar: headlights, wet concrete, and the certainty of pursuit before the threat is ever fully seen. Speed matters less than inevitability.",
    },
    {
        "source": "page09_bird_reactor.png",
        "output": "page10_bird_reactor.png",
        "mode": "standard",
        "heading": "Bird Over Reactor Nine",
        "body": "The Bird functions as a disaster omen rather than a conventional monster. It should be felt as a scale event, a warning sign in the sky that makes every human structure below seem temporary and already condemned.",
    },
    {
        "source": "page10_ritual_tools.png",
        "output": "page11_ritual_tools.png",
        "mode": "standard",
        "heading": "Ritual Tools",
        "body": "Each tool is ordinary enough to be found in a neglected apartment, but charged through use, habit, and superstition. The kit reads less like fantasy inventory and more like household survival theology.",
    },
    {
        "source": "page12_legalities_base.png",
        "output": "page12_legalities.png",
        "mode": "legal",
        "heading": "Legalities",
        "body": "Crepulin Enfant is an original drIpTECH horror property represented here through generated concept images, visual development notes, and fictive in-world archival styling. This artbook is a development visualization package only; names, characters, environments, and symbols shown here remain part of the same original project world and are not a release build, marketing claim, or legal filing. All third-party references are atmospheric inspirations only and no external logos, marks, or licensed characters are asserted by this document.",
    },
    {
        "source": "page13_rear_cover_base.png",
        "output": "page13_rear_cover.png",
        "mode": "rear",
        "heading": "Rear Cover",
        "body": "A quiet walk through Block Nine's haunted domestic systems: threshold spirits, Soviet ruin, pursuit folklore, and fear-reactive architecture gathered into one compact visual dossier.",
    },
]


def measure_multiline(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, spacing: int) -> tuple[int, int]:
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_pixels(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    words = text.split()
    lines = []
    current = []
    for word in words:
        trial = " ".join(current + [word])
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


def draw_panel(base: Image.Image, x: int, y: int, w: int, h: int, fill=(12, 16, 22, 168), outline=(255, 255, 255, 60)) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle((x, y, x + w, y + h), radius=22, fill=fill, outline=outline, width=2)
    base.alpha_composite(overlay)


def draw_standard_page(image: Image.Image, heading: str, body: str, align_right: bool) -> None:
    draw = ImageDraw.Draw(image)
    panel_w = int(image.width * 0.42)
    body_text = wrap_pixels(draw, body, FONT_BODY, panel_w - 56)
    heading_h = measure_multiline(draw, heading, FONT_HEADING, 6)[1]
    body_h = measure_multiline(draw, body_text, FONT_BODY, 8)[1]
    panel_h = heading_h + body_h + 58
    x = image.width - panel_w - 42 if align_right else 42
    y = image.height - panel_h - 38
    draw_panel(image, x, y, panel_w, panel_h)
    draw = ImageDraw.Draw(image)
    draw.text((x + 26, y + 20), heading, font=FONT_HEADING, fill=(245, 242, 234, 255))
    draw.multiline_text((x + 26, y + 22 + heading_h), body_text, font=FONT_BODY, fill=(230, 230, 226, 255), spacing=8)


def draw_cover_page(image: Image.Image, heading: str, body: str) -> None:
    draw = ImageDraw.Draw(image)
    title_lines = heading.replace(" ", "\n", 1)
    title_w, title_h = measure_multiline(draw, title_lines, FONT_TITLE, 4)
    top_panel_h = title_h + 58
    top_y = 44
    top_x = (image.width - max(title_w + 90, 520)) // 2
    top_w = max(title_w + 90, 520)
    draw_panel(image, top_x, top_y, top_w, top_panel_h, fill=(10, 12, 18, 148))
    draw = ImageDraw.Draw(image)
    draw.multiline_text((image.width // 2, top_y + 24), title_lines, font=FONT_TITLE, fill=(246, 241, 230, 255), spacing=4, anchor="ma", align="center")

    subtitle_w = draw.textbbox((0, 0), SUBTITLE, font=FONT_SUBTITLE)[2]
    foot_w = max(subtitle_w + 90, 320)
    foot_h = 68
    foot_x = (image.width - foot_w) // 2
    foot_y = image.height - foot_h - 34
    draw_panel(image, foot_x, foot_y, foot_w, foot_h, fill=(10, 12, 18, 130))
    draw = ImageDraw.Draw(image)
    draw.text((image.width // 2, foot_y + 18), SUBTITLE, font=FONT_SUBTITLE, fill=(238, 232, 220, 255), anchor="ma")


def draw_toc_page(image: Image.Image, heading: str, body: str) -> None:
    draw = ImageDraw.Draw(image)
    panel_x = 56
    panel_y = 56
    panel_w = int(image.width * 0.48)
    panel_h = image.height - 112
    draw_panel(image, panel_x, panel_y, panel_w, panel_h, fill=(12, 16, 22, 178))
    draw = ImageDraw.Draw(image)
    draw.text((panel_x + 30, panel_y + 24), heading, font=FONT_HEADING, fill=(245, 242, 234, 255))
    draw.multiline_text((panel_x + 30, panel_y + 84), body, font=FONT_BODY, fill=(232, 232, 228, 255), spacing=12)


def draw_legal_page(image: Image.Image, heading: str, body: str) -> None:
    draw = ImageDraw.Draw(image)
    panel_w = int(image.width * 0.62)
    wrapped = wrap_pixels(draw, body, FONT_SMALL, panel_w - 60)
    heading_h = measure_multiline(draw, heading, FONT_HEADING, 6)[1]
    body_h = measure_multiline(draw, wrapped, FONT_SMALL, 9)[1]
    panel_h = heading_h + body_h + 66
    panel_x = (image.width - panel_w) // 2
    panel_y = (image.height - panel_h) // 2
    draw_panel(image, panel_x, panel_y, panel_w, panel_h, fill=(18, 14, 12, 182), outline=(255, 226, 196, 60))
    draw = ImageDraw.Draw(image)
    draw.text((panel_x + 30, panel_y + 24), heading, font=FONT_HEADING, fill=(246, 236, 220, 255))
    draw.multiline_text((panel_x + 30, panel_y + 28 + heading_h), wrapped, font=FONT_SMALL, fill=(238, 229, 215, 255), spacing=9)


def draw_rear_page(image: Image.Image, heading: str, body: str) -> None:
    draw = ImageDraw.Draw(image)
    panel_w = int(image.width * 0.36)
    wrapped = wrap_pixels(draw, body, FONT_BODY, panel_w - 50)
    heading_h = measure_multiline(draw, heading, FONT_HEADING, 6)[1]
    body_h = measure_multiline(draw, wrapped, FONT_BODY, 8)[1]
    panel_h = heading_h + body_h + 58
    panel_x = image.width - panel_w - 44
    panel_y = image.height - panel_h - 40
    draw_panel(image, panel_x, panel_y, panel_w, panel_h, fill=(8, 10, 14, 160))
    draw = ImageDraw.Draw(image)
    draw.text((panel_x + 24, panel_y + 20), heading, font=FONT_HEADING, fill=(242, 240, 234, 255))
    draw.multiline_text((panel_x + 24, panel_y + 22 + heading_h), wrapped, font=FONT_BODY, fill=(230, 230, 226, 255), spacing=8)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    for index, page in enumerate(PAGES):
        source = ARTBOOK_DIR / page["source"]
        output = OUTPUT_DIR / page["output"]
        image = Image.open(source).convert("RGBA")
        mode = page["mode"]

        if mode == "cover":
            draw_cover_page(image, page["heading"], page["body"])
        elif mode == "toc":
            draw_toc_page(image, page["heading"], page["body"])
        elif mode == "legal":
            draw_legal_page(image, page["heading"], page["body"])
        elif mode == "rear":
            draw_rear_page(image, page["heading"], page["body"])
        else:
            draw_standard_page(image, page["heading"], page["body"], align_right=(index % 2 == 1))

        image.save(output, format="PNG")
        print(f"Saved {output}")


if __name__ == "__main__":
    main()