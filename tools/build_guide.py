from __future__ import annotations

import base64
import json
import re
import unicodedata
from io import BytesIO
from pathlib import Path

from bs4 import BeautifulSoup, Doctype, NavigableString
from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "releases" / "Milan_Surroundings_Modular_Travel_Planner_2026_v1_1.html"
GUIDE = ROOT / "guide"
IMAGE_DIR = GUIDE / "images"


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "photograph"


def replace_text(node: NavigableString, replacements: list[tuple[str, str]]) -> None:
    text = str(node)
    for old, new in replacements:
        text = text.replace(old, new)
    text = re.sub(r"\bunverified\b", "unconfirmed", text, flags=re.I)
    text = re.sub(r"\bverified\b", "confirmed", text, flags=re.I)
    text = re.sub(r"\baudited\b", "", text, flags=re.I)
    text = re.sub(r"\baudit\b", "review", text, flags=re.I)
    text = re.sub(r"\bsource-controlled\b", "carefully organized", text, flags=re.I)
    text = re.sub(r"\bmodular\b", "flexible", text, flags=re.I)
    text = re.sub(r"\bmodules\b", "day plans", text, flags=re.I)
    text = re.sub(r"\bmodule\b", "day plan", text, flags=re.I)
    text = re.sub(r"\bdossiers\b", "guides", text, flags=re.I)
    text = re.sub(r"\bdossier\b", "guide", text, flags=re.I)
    text = re.sub(r"\bcontrolling\b", "primary", text, flags=re.I)
    text = re.sub(r"\bprovenance\b", "context", text, flags=re.I)
    text = re.sub(r"\bdiscovery lineage\b", "trip inspiration", text, flags=re.I)
    text = re.sub(r"\bdiscovery[- ]page\b", "overview page", text, flags=re.I)
    text = re.sub(r"\brelease\b", "information", text, flags=re.I)
    text = re.sub(r"\bgates\b", "conditions", text, flags=re.I)
    text = re.sub(r"\bgate\b", "condition", text, flags=re.I)
    node.replace_with(text)


raw = SOURCE.read_text(encoding="utf-8")
photo_match = re.search(r"window\.PHOTO_DATA=(\{.*?\});</script>", raw, flags=re.S)
if not photo_match:
    raise RuntimeError("Embedded photography could not be read from the preserved guide.")
photo_data = json.loads(photo_match.group(1))
soup = BeautifulSoup(raw, "html.parser")

source_styles = "\n".join(tag.get_text() for tag in soup.find_all("style"))
atlas = soup.find(id="photo-atlas")
credits: dict[str, dict[str, str]] = {}
if atlas:
    for figure in atlas.select("figure[data-photo-id]"):
        key = figure.get("data-photo-id", "")
        meta = figure.select_one(".photo-meta")
        creator = photo_data.get(key, {}).get("creator", "")
        licence_text = ""
        licence_url = ""
        if meta:
            for row in meta.find_all("div", recursive=False):
                text = row.get_text(" ", strip=True)
                if text.startswith("Creator:"):
                    creator = text.removeprefix("Creator:").strip()
                elif text.startswith("Licence:"):
                    licence_text = text.removeprefix("Licence:").strip()
                    link = row.find("a", href=True)
                    if link:
                        licence_url = link["href"]
        credits[key] = {
            "creator": creator,
            "licence_text": licence_text,
            "licence_url": licence_url,
        }

photo_slugs: dict[str, str] = {}
used_slugs: set[str] = set()
for key, item in photo_data.items():
    base = slugify(item["caption"])
    slug = base
    counter = 2
    while slug in used_slugs:
        slug = f"{base}-{counter}"
        counter += 1
    used_slugs.add(slug)
    photo_slugs[key] = slug

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
for key, item in photo_data.items():
    slug = photo_slugs[key]
    full_path = IMAGE_DIR / f"{slug}.jpg"
    if full_path.exists():
        image = Image.open(full_path).convert("RGB")
    else:
        payload = base64.b64decode(item["src"].split(",", 1)[1])
        image = Image.open(BytesIO(payload)).convert("RGB")
        image.save(full_path, "JPEG", quality=90, optimize=True, progressive=True)
    for width in (640, 960):
        derivative = IMAGE_DIR / f"{slug}-{width}.jpg"
        resized = image.copy()
        if resized.width > width:
            height = round(resized.height * width / resized.width)
            resized = resized.resize((width, height), Image.Resampling.LANCZOS)
        resized.save(derivative, "JPEG", quality=84, optimize=True, progressive=True)

# Replace the embedded implementation with external, cache-busted assets.
for tag in soup.find_all(["style", "script"]):
    tag.decompose()
for meta in soup.find_all("meta", attrs={"name": "release"}):
    meta.decompose()
soup.title.string = "Milan & Surroundings · Travel Guide"
description = soup.find("meta", attrs={"name": "description"})
if description:
    description["content"] = "A practical guide to Milan, the Italian lakes and thirty day trips, with routes, timings, hotels, safety notes and direct planning links."
head = soup.head
theme = soup.new_tag("meta", attrs={"name": "theme-color", "content": "#1f2421"})
head.append(theme)
stylesheet = soup.new_tag("link", rel="stylesheet", href="styles.css?v=20260825")
head.append(stylesheet)

body = soup.body
skip = soup.new_tag("a", href="#main-content", attrs={"class": "guide-skip"})
skip.string = "Skip to the guide"
body.insert(0, skip)

sidebar = soup.select_one(".sidebar")
brand = sidebar.select_one(".brand") if sidebar else None
if brand:
    brand.clear()
    brand.append("Milan + surroundings")
    small = soup.new_tag("small")
    small.string = "City · lakes · regional day trips"
    brand.append(small)
if sidebar:
    toggle = soup.new_tag(
        "button",
        attrs={
            "type": "button",
            "class": "guide-menu",
            "id": "guideMenuToggle",
            "aria-controls": "guideNavigation",
            "aria-expanded": "false",
            "aria-label": "Open guide menu",
        },
    )
    toggle.string = "Menu"
    search = sidebar.select_one(".search")
    if search:
        search.insert_before(toggle)
    nav = sidebar.find("nav")
    if nav:
        nav["id"] = "guideNavigation"

main = soup.find("main")
if main:
    main["id"] = "main-content"
    main["tabindex"] = "-1"

id_map = {
    "module-builder": "trip-planner",
    "module-m1": "historic-milan",
    "module-m2": "navigli-tortona",
    "module-m3": "varenna-bellagio",
    "module-m4": "bergamo",
    "module-m5": "pavia-certosa",
    "module-m6": "monza",
    "module-m7": "stresa-borromean-islands",
    "photo-atlas": "photo-credits",
    "catalogue-plan-ready": "ready-to-plan",
    "catalogue-conditional": "check-conditions",
    "catalogue-inspiration": "specialist-overnight",
}
for old, new in id_map.items():
    target = soup.find(id=old)
    if target:
        target["id"] = new
    for link in soup.find_all("a", href=f"#{old}"):
        link["href"] = f"#{new}"

nav = soup.find("nav", id="guideNavigation")
nav_labels = {
    "#how-to-use": "How to use",
    "#master-map": "Map and routes",
    "#trip-planner": "Build your trip",
    "#compatibility": "Compare day trips",
    "#historic-milan": "Historic Milan",
    "#navigli-tortona": "Navigli and design",
    "#varenna-bellagio": "Varenna and Bellagio",
    "#bergamo": "Bergamo",
    "#pavia-certosa": "Pavia and Certosa",
    "#monza": "Monza",
    "#stresa-borromean-islands": "Stresa islands",
    "#excursion-catalogue": "More excursions",
    "#hotels": "Where to stay",
    "#transport": "Getting around",
    "#localities": "Place profiles",
    "#budget": "Trip budget",
    "#safety": "Safety and access",
    "#packing": "Before you go",
    "#photo-credits": "Photo credits",
}
if nav:
    for link in list(nav.find_all("a", recursive=False)):
        href = link.get("href")
        if href == "#all-links":
            link.decompose()
        elif href in nav_labels:
            link.string = nav_labels[href]
side_actions = soup.select_one(".side-actions")
if side_actions:
    for link in list(side_actions.find_all("a")):
        if link.get("href") == "#all-links":
            link.decompose()
        elif link.get("href", "").endswith(".pdf"):
            link["href"] = "Milan_Excursions_Travel_Planner_2026.pdf"
            link.string = "Open printable guide"

for link in soup.select("a.pdf-link"):
    link["href"] = "Milan_Excursions_Travel_Planner_2026.pdf"

cover = soup.select_one(".cover")
if cover:
    cover["id"] = "top"
    cover_image = cover.select_one(".cover-image")
    if cover_image:
        key = cover_image.get("data-cover-photo", "P001")
        item = photo_data[key]
        slug = photo_slugs[key]
        picture = soup.new_tag("picture", attrs={"class": "cover-image", "aria-hidden": "true"})
        source = soup.new_tag("source")
        source["srcset"] = f"images/{slug}-640.jpg 640w, images/{slug}-960.jpg 960w, images/{slug}.jpg {item['width']}w"
        source["sizes"] = "100vw"
        image = soup.new_tag("img", src=f"images/{slug}-960.jpg", alt=item["caption"])
        image["width"] = str(item["width"])
        image["height"] = str(item["height"])
        image["fetchpriority"] = "high"
        image["decoding"] = "async"
        picture.append(source)
        picture.append(image)
        cover_image.replace_with(picture)
    eyebrow = cover.select_one(".eyebrow")
    if eyebrow:
        eyebrow.string = "Milan · Lombardy · the Italian lakes"
    deck = cover.select_one(".deck")
    if deck:
        deck.string = "A flexible guide to seven complete day plans and thirty further excursions, with realistic travel times, direct booking links and practical alternatives."
    metas = cover.select(".cover-meta")
    if metas:
        metas[0].clear()
        for copy in ("7 complete day plans", "30 further excursions", "Rail-first routes", "Hotels, safety and live travel links"):
            span = soup.new_tag("span")
            span.string = copy
            metas[0].append(span)
        for extra in metas[1:]:
            extra.decompose()
    photo_button = cover.select_one("button.photo-open")
    if photo_button:
        key = photo_button.get("data-photo", "P001")
        item = photo_data[key]
        slug = photo_slugs[key]
        photo_button["data-photo"] = slug
        photo_button["data-full"] = f"images/{slug}.jpg"
        photo_button["data-title"] = item["caption"]
        photo_button["data-creator"] = credits.get(key, {}).get("creator", item.get("creator", ""))
        photo_button["data-source"] = item["pageUrl"]
        photo_button["aria-label"] = f"Open photograph: {item['caption']}"
        photo_button.string = "View cover photograph"
    for link in cover.select(".button-row a"):
        if link.get("href") == "#master-map":
            link.string = "See map and routes"

# Section numbers and internal day-plan codes are unnecessary for travelers.
for badge in soup.select(".badge,.module-code"):
    badge.decompose()

day_names = {
    "historic-milan": "Historic Milan",
    "navigli-tortona": "Navigli and Tortona",
    "varenna-bellagio": "Lake Como",
    "bergamo": "Bergamo",
    "pavia-certosa": "Pavia and Certosa",
    "monza": "Monza",
    "stresa-borromean-islands": "Stresa and the Borromean Islands",
}
for card in soup.select(".module-card"):
    checkbox = card.find("input", attrs={"type": "checkbox"})
    title = card.find("h3").get_text(" ", strip=True) if card.find("h3") else "Day plan"
    slug = slugify(title)
    if checkbox:
        checkbox["id"] = f"plan-select-{slug}"
        checkbox["value"] = title
        label = card.find("label")
        if label:
            label["for"] = checkbox["id"]
    direct = card.find("a", recursive=False)
    if direct:
        direct.string = "View day plan"

comparison = soup.find(id="compatibility")
if comparison:
    heading = comparison.find("h2")
    if heading:
        heading.string = "Compare day trips"
    caption = comparison.find("caption")
    if caption:
        caption.string = "Day-plan comparison"
    first_header = comparison.select_one("thead th")
    if first_header:
        first_header.string = "Day plan"
    advance_header = comparison.find("th", string=lambda value: value and "Advance" in value)
    if advance_header:
        advance_header.string = "Plan ahead"
    for index, cell in enumerate(comparison.select("tbody tr td:first-child")):
        if index < len(day_names):
            cell.string = list(day_names.values())[index]

# Excursion status labels and semantic anchors.
status_map = {
    "PLAN-READY": ("READY TO PLAN", "ready-to-plan"),
    "CONDITIONAL": ("CHECK CONDITIONS", "check-conditions"),
    "INSPIRATION": ("SPECIALIST / OVERNIGHT", "specialist-overnight"),
}
for card in soup.select(".excursion-card"):
    title = card.find("h4").get_text(" ", strip=True)
    status = card.get("data-status", "")
    visible, semantic = status_map.get(status, (status, slugify(status)))
    card["id"] = f"excursion-{slugify(title)}"
    card["data-status"] = semantic
    card.attrs.pop("data-excursion-id", None)
    code = card.select_one(".excursion-id")
    if code:
        code.decompose()
    pill = card.select_one(".status-pill")
    if pill:
        pill.string = visible
    checked = card.select_one(".checked")
    if checked:
        checked.clear()
        checked.string = "Information dated 24 August 2026; confirm live details before departure."
    headings = card.select(".excursion-sources h5")
    if headings:
        headings[0].string = "Ideas and context"
    if len(headings) > 1:
        headings[1].string = "Direct planning links"

group_copy = {
    "ready-to-plan": (
        "Ready to plan",
        "Straightforward outings once current transport, opening and weather information has been checked.",
    ),
    "check-conditions": (
        "Check conditions before choosing",
        "Worthwhile outings whose transport, access, booking, trail or weather conditions must be checked first.",
    ),
    "specialist-overnight": (
        "Specialist or overnight journeys",
        "Allow additional time, preparation or specialist experience; an overnight stay is often the better plan.",
    ),
}
for section_id, (heading_copy, body_copy) in group_copy.items():
    heading = soup.find(id=section_id)
    if heading:
        heading.string = heading_copy
        sibling = heading.find_next_sibling("p")
        if sibling:
            sibling.string = body_copy

# Build a compact, human-readable photography credit section and remove the technical link appendix.
credit_section = soup.find(id="photo-credits")
if credit_section:
    credit_section.clear()
    header = soup.new_tag("header", attrs={"class": "section-head"})
    header_body = soup.new_tag("div")
    heading = soup.new_tag("h2")
    heading.string = "Photo credits"
    intro = soup.new_tag("p")
    intro.string = "Photography appears throughout the guide. Creator and licence details link to the original sources."
    header_body.append(heading)
    header_body.append(intro)
    header.append(header_body)
    credit_section.append(header)
    grid = soup.new_tag("div", attrs={"class": "credits-grid"})
    for key, item in photo_data.items():
        info = credits.get(key, {})
        creator = info.get("creator") or item.get("creator") or "Creator listed on the source page"
        if key == "P018":
            creator = "Fortepan / Schoch Frigyes"
        entry = soup.new_tag("article", attrs={"class": "credit-item"})
        title = soup.new_tag("strong")
        title.string = item["caption"]
        byline = soup.new_tag("span")
        byline.string = creator
        links = soup.new_tag("span")
        source_link = soup.new_tag("a", href=item["pageUrl"], target="_blank", rel="noopener")
        source_link.string = "Original photograph"
        links.append(source_link)
        licence_url = info.get("licence_url", "")
        licence_text = info.get("licence_text", "") or "Public domain"
        links.append(" · ")
        if licence_url:
            licence_link = soup.new_tag("a", href=licence_url, target="_blank", rel="noopener")
            licence_link.string = licence_text
            links.append(licence_link)
        else:
            links.append(licence_text)
        entry.append(title)
        entry.append(byline)
        entry.append(links)
        grid.append(entry)
    credit_section.append(grid)
all_links = soup.find(id="all-links")
if all_links:
    all_links.decompose()

# Convert every remaining photograph to responsive local files and semantic lightbox data.
for figure in soup.select("figure.photo-card"):
    button = figure.select_one("button.photo-open")
    image = figure.find("img")
    if not button or not image:
        continue
    key = button.get("data-photo") or image.get("data-photo-src")
    if key not in photo_data:
        continue
    item = photo_data[key]
    slug = photo_slugs[key]
    image.attrs.pop("data-photo-src", None)
    image["src"] = f"images/{slug}-640.jpg"
    image["srcset"] = f"images/{slug}-640.jpg 640w, images/{slug}-960.jpg 960w, images/{slug}.jpg {item['width']}w"
    image["sizes"] = "(max-width: 720px) 100vw, (max-width: 1100px) 50vw, 32vw"
    image["width"] = str(item["width"])
    image["height"] = str(item["height"])
    image["loading"] = "lazy"
    image["decoding"] = "async"
    image["alt"] = item["caption"]
    button["data-photo"] = slug
    button["data-full"] = f"images/{slug}.jpg"
    button["data-title"] = item["caption"]
    button["data-creator"] = credits.get(key, {}).get("creator", item.get("creator", ""))
    button["data-source"] = item["pageUrl"]
    button["aria-label"] = f"Open photograph: {item['caption']}"
    figure.attrs.pop("id", None)
    figure.attrs.pop("data-photo-id", None)
    figure.attrs.pop("data-occurrence", None)
    photo_id = figure.select_one(".photo-id")
    if photo_id:
        photo_id.decompose()
    caption = figure.find("figcaption")
    if caption:
        for small in caption.find_all("small"):
            small.decompose()

lightbox_image = soup.find(id="lightboxImage")
if lightbox_image:
    lightbox_image["alt"] = "Selected travel photograph"
lightbox_source = soup.find(id="lightboxSource")
if lightbox_source:
    lightbox_source.string = "Original photograph"

exact_replacements = [
    ("Standalone verdict", "Best for"),
    ("GO / caution / NO-GO gate", "When this trip works"),
    ("Failure-safe alternative", "Backup plan"),
    ("Realistic envelope", "Travel time and day length"),
    ("Decisive gate", "What to check"),
    ("Pairing or fallback", "Alternative plan"),
    ("Live inventory", "Tickets and availability"),
    ("New excursion photography", "A glimpse beyond Milan"),
    ("Easy day trips", "Ready to plan"),
    ("Discovery-page targets", "Trip inspiration links"),
    ("First-party targets", "Direct planning links"),
    ("Hotels.com nature-list discovery page", "Hotels.com: natural sights near Milan"),
    ("YesMilano outdoor trips discovery page", "YesMilano: outdoor trips from Milan"),
    ("YesMilano urban trekking discovery route", "YesMilano: urban trekking route"),
    ("YesMilano Idroscalo discovery page", "YesMilano: Idroscalo information"),
    ("YesMilano wildlife-oases discovery page", "YesMilano: wildlife oases"),
    ("YesMilano Lake Maggiore cycling discovery page", "YesMilano: Lake Maggiore cycling"),
    ("boat and weather gate", "boat and weather check"),
    ("Villa calendar gate", "Villa calendar check"),
    ("boat and palace gate", "boat and palace openings"),
    ("Advance gate", "Advance planning"),
    ("Weather gate", "Weather check"),
    ("boat or mobility gate fails", "boats are unavailable or access is unsuitable"),
    ("DRIVING GATE", "DRIVING CHECK"),
    ("Driving gate", "Driving check"),
    ("weekday, weather and event gates", "weekday openings, weather and event conditions"),
    ("Cathedral gate", "Cathedral booking"),
    ("all three gates pass", "all three conditions align"),
    ("opening gates pass", "opening times work"),
    ("the chosen gate", "the chosen entrance"),
    ("the cable-car gate remains", "the cable-car schedule remains decisive"),
    ("no universal gate or park-wide opening time", "no universal entrance or park-wide opening time"),
    ("seasonal module gate", "seasonal operating window"),
    ("retained for provenance", "included for context"),
]
for node in list(soup.find_all(string=True)):
    if not isinstance(node, Doctype) and node.parent and node.parent.name not in {"script", "style"}:
        replace_text(node, exact_replacements)

# Replace internal day-plan shorthand while preserving real Milan Metro line names.
day_code_copy = {
    "M1": "Historic Milan",
    "M2": "Navigli and Tortona",
    "M3": "Lake Como",
    "M4": "Bergamo",
    "M5": "Pavia and Certosa",
    "M6": "Monza",
    "M7": "Stresa and the Borromean Islands",
}
for node in list(soup.find_all(string=True)):
    if isinstance(node, Doctype) or not node.parent or node.parent.name in {"script", "style"}:
        continue
    text = str(node)
    if "Metro" not in text:
        text = re.sub(r"\bM1\s*[-–]\s*M7\b", "all seven day plans", text)
        text = re.sub(r"\bM1\s*[-–]\s*M6\b", "the six non-seasonal day plans", text)
        for code, copy in day_code_copy.items():
            text = re.sub(rf"\b{code}\b", copy, text)
    node.replace_with(text)

# Milan Metro line names remain factual, but are written out to avoid confusion with the former day-plan shorthand.
for node in list(soup.find_all(string=True)):
    if isinstance(node, Doctype) or not node.parent or node.parent.name in {"script", "style"}:
        continue
    text = str(node)
    text = re.sub(r"\bMetro lines M2/M4\b", "Metro Lines 2 and 4", text, flags=re.I)
    text = re.sub(r"\bMetro M1 \+ M3\b", "Metro Lines 1 and 3", text, flags=re.I)
    text = re.sub(r"\bMetro M2 or M4\b", "Metro Line 2 or Line 4", text, flags=re.I)
    text = re.sub(r"\bMetro M([1-4])\b", r"Metro Line \1", text, flags=re.I)
    text = re.sub(r"\bM([1-4])/M([1-4])\b", r"Lines \1 and \2", text)
    text = re.sub(r"\bM([1-4])\b", r"Line \1", text)
    node.replace_with(text)

awkward_replacements = {
    "Bergamo / Bergamo": "Bergamo",
    "Monza / Monza": "Monza",
    "Stresa / Stresa and the Borromean Islands": "Stresa and the Borromean Islands",
    "Historic Milan core programme": "central Milan plan",
    "Milan historic core core programme": "central Milan plan",
    "Weather fallback: Navigli and design Navigli and Tortona.": "Weather fallback: Navigli and Tortona.",
    "High-water fallback: Monza Monza or Bergamo Bergamo.": "High-water fallback: Monza or Bergamo.",
    "use as an Stresa and the Borromean Islands alternative": "use as an alternative to Stresa and the Borromean Islands",
    "Cancellation fallback: Bergamo Bergamo.": "Cancellation fallback: Bergamo.",
    "Stresa and the Borromean Islands's island visit": "the island visit from Stresa",
    "Lake Maggiore Stresa and the Borromean Islands.": "Lake Maggiore or the Stresa and Borromean Islands day plan.",
    "Good / caution / NO-GO": "Good conditions / adjust / choose an alternative",
    "GO / CAUTION / NO-GO": "GOOD CONDITIONS / ADJUST / ALTERNATIVE",
    "GO": "Good conditions",
    "CAUTION": "Adjust the plan",
    "NO-GO": "Choose an alternative",
}
for node in list(soup.find_all(string=True)):
    if isinstance(node, Doctype) or not node.parent or node.parent.name in {"script", "style"}:
        continue
    text = str(node)
    for old, new in awkward_replacements.items():
        text = text.replace(old, new)
    node.replace_with(text)

# Exact traveler-facing headings and descriptions.
heading_copy = {
    "how-to-use": ("How to use this guide", "Seven complete day plans, one Milan base and no forced chronology."),
    "master-map": ("Map and routes", "What lies where, and which journeys share a corridor."),
    "trip-planner": ("Build your trip", "Choose any complete day plan; each stands on its own."),
    "excursion-catalogue": ("More excursions from Milan", "Thirty additional possibilities, grouped by the preparation they require."),
    "hotels": ("Where to stay", "Seven well-located bases with practical access notes."),
    "transport": ("Getting around", "Travel times, route patterns and the live information to check."),
    "localities": ("Place profiles", "A quick sense of each destination and its role in the trip."),
    "safety": ("Safety and access", "Weather, mobility, transport and personal-safety considerations."),
    "packing": ("Before you go", "A practical checklist for bookings, weather and the journey home."),
}
for section_id, (title_copy, subtitle_copy) in heading_copy.items():
    section = soup.find(id=section_id)
    if not section:
        continue
    header = section.find("header", recursive=False)
    if not header:
        continue
    heading = header.find(["h2", "h3"])
    if heading:
        heading.string = title_copy
    subtitle = header.find("p")
    if subtitle:
        subtitle.string = subtitle_copy

how_to = soup.find(id="how-to-use")
if how_to:
    lead = how_to.select_one(".lead")
    if lead:
        lead.string = (
            "Use Milan as your base, then choose the days that fit your bookings, the weather and the season. "
            "Historic Milan and Navigli stay within the city; Lake Como, Bergamo, Pavia, Monza and Stresa are regional days. "
            "The thirty additional excursions are grouped as ready to plan, check conditions, or specialist and overnight journeys."
        )
    fact_copy = [
        ("7", "Complete day plans"),
        ("30", "Further excursions"),
        ("31", "Travel photographs"),
        ("3 groups", "By preparation needed"),
        ("Rail-first", "For regional journeys"),
        ("Live checks", "Transport, weather and access"),
    ]
    for fact, (value, label) in zip(how_to.select(".facts > div"), fact_copy):
        strong = fact.find("strong")
        span = fact.find("span")
        if strong:
            strong.string = value
        if span:
            span.string = label
    cards = how_to.select(".cards > article")
    if len(cards) >= 3:
        cards[2].find("h3").string = "Choose by preparation"
        cards[2].find("p").string = (
            "Some outings need only a timetable check; others depend on a trail, booking, car or overnight stay. "
            "Choose the preparation level that suits your trip."
        )
    rule = how_to.select_one(".callout")
    if rule:
        rule.find("h4").string = "Check before booking"

excursion_section = soup.find(id="excursion-catalogue")
if excursion_section:
    lead = excursion_section.find("p", class_="lead")
    if lead:
        lead.string = (
            "These thirty outings broaden the choices beyond the seven complete day plans. "
            "Each one gives a realistic travel window, the condition most likely to change the plan and a practical alternative."
        )
    fact_copy = [
        ("30", "Further excursions"),
        ("12", "Ready to plan"),
        ("14", "Check conditions"),
        ("4", "Specialist or overnight"),
        ("Rail-first", "Where practical"),
        ("Live checks", "Before departure"),
    ]
    for fact, (value, label) in zip(excursion_section.select(":scope > .facts > div"), fact_copy):
        strong = fact.find("strong")
        span = fact.find("span")
        if strong:
            strong.string = value
        if span:
            span.string = label
    notes = excursion_section.select_one(".catalogue-notes")
    if notes:
        note_cards = notes.find_all("article", recursive=False)
        if len(note_cards) >= 3:
            note_cards[0].find("h3").string = "Use current operating information"
            note_cards[0].find("p").string = (
                "Articles from YesMilano and Hotels.com are useful for ideas. Use the linked transport, park, municipal, "
                "attraction and route pages to make the actual plan."
            )
            note_cards[1].find("h3").string = "Leonardo connects several places"
            note_cards[1].find("p").string = (
                "The Last Supper, Navigli, Martesana, Paderno and the canal cycleways can form a theme, "
                "but each route keeps its own booking, transport and safety conditions."
            )
            note_cards[2].find("h3").string = "Choose by preparation"
            note_cards[2].find("p").string = (
                "Ready to plan means a credible Milan outing after current checks. Check conditions means one car, booking, "
                "trail, weather or connection issue can change the day. Specialist or overnight journeys need more preparation or time."
            )
    choice = excursion_section.find(["h3", "h4"], string=lambda value: value and "status" in value.lower())
    if choice:
        choice.string = "Choose by preparation"
        paragraph = choice.find_next_sibling("p")
        if paragraph:
            paragraph.string = (
                "Ready-to-plan outings still need current times. For conditional outings, confirm the named dependency first. "
                "Treat specialist or overnight journeys as larger projects rather than ordinary day trips."
            )
    photo_lead = excursion_section.select_one(".catalogue-photo-lead")
    if photo_lead:
        paragraph = photo_lead.find("p", recursive=False)
        if paragraph:
            paragraph.string = (
                "Lake Iseo, Sacro Monte di Varese, Campo dei Fiori and Val di Mello offer a first look at the wider region."
            )

for strong in soup.select(".fine strong"):
    if strong.get_text(" ", strip=True) == "Time status:":
        strong.string = "Planning note:"
for heading in soup.select(".decision-grid .go h4"):
    heading.string = "Good conditions"
for heading in soup.select(".decision-grid .caution h4"):
    heading.string = "Adjust the plan"
for heading in soup.select(".decision-grid .no h4"):
    heading.string = "Choose an alternative"
for label in soup.select(".check .form-check-label, .check label, .check span"):
    copy = label.get_text(" ", strip=True)
    copy = copy.replace("Exact MX trailhead", "Exact trailhead")
    copy = copy.replace("Photo ID and booking confirmations", "Identification and booking confirmations")
    label.string = copy

hotels = soup.find(id="hotels")
if hotels:
    callout = hotels.select_one(".callout")
    if callout:
        heading = callout.find(["h3", "h4"])
        paragraph = callout.find("p")
        if heading:
            heading.string = "Prices and availability"
        if paragraph:
            paragraph.string = (
                "Property details shown here are dated 24 August 2026. Room prices and availability change, so compare the "
                "official cancellable rate for your dates and request written confirmation for parking, accessibility or late arrival when needed."
            )

# Rename implementation classes so public source no longer carries the old internal vocabulary.
class_replacements = {
    "module-grid": "day-plan-grid",
    "module-card": "day-plan-card",
    "module-head": "day-plan-head",
    "module-section": "day-plan-section",
    "module-code": "day-plan-code",
    "catalogue-section": "excursion-section",
    "catalogue-notes": "excursion-notes",
    "catalogue-photo-lead": "excursion-photo-lead",
    "catalogue-group": "excursion-group",
    "photo-atlas": "photo-credits",
    "status-plan-ready": "status-ready",
    "status-conditional": "status-check",
    "status-inspiration": "status-specialist",
}
for tag in soup.find_all(class_=True):
    tag["class"] = [class_replacements.get(value, value) for value in tag.get("class", [])]

footer = soup.find("footer")
if footer:
    footer.clear()
    footer.append("Milan & Surroundings · Travel Guide")
    note = soup.new_tag("span")
    note.string = "Check transport, opening times, weather and access before departure."
    footer.append(note)

app_script = soup.new_tag("script", src="app.js?v=20260825", defer=True)
body.append(app_script)

html = soup.prettify(formatter="html")
html = html.replace("viewbox=", "viewBox=")
html = html.replace("Milan and Surroundings Flexible Travel Planner 2026", "Milan & Surroundings · Travel Guide")
html = html.replace("Milan and Surroundings Travel Planner 2026", "Milan & Surroundings · Travel Guide")
html = re.sub(r"\s+·\s+v1\.1", "", html, flags=re.I)
GUIDE.mkdir(parents=True, exist_ok=True)
(GUIDE / "index.html").write_text(html, encoding="utf-8", newline="\n")

css = source_styles
for old, new in class_replacements.items():
    css = css.replace(f".{old}", f".{new}")
for old, new in id_map.items():
    css = css.replace(f"#{old}", f"#{new}")
css = re.sub(r":root\{--green:#6b2636;.*?\}", "", css, flags=re.S)
css += r'''

:root {
  --ink: #1d1d1f;
  --muted: #686864;
  --paper: #fbfaf7;
  --paper2: #f0eee8;
  --green: #34453d;
  --green2: #53685d;
  --gold: #9a7544;
  --red: #8c504a;
  --blue: #5c7180;
  --line: #d8d5cd;
  --dark: #1d2420;
  --radius: 22px;
  --serif: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  --sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
  --shadow: 0 20px 55px rgba(27, 31, 29, .11);
}

body { background: #e8e6e1; letter-spacing: -.005em; }
.app { max-width: 1680px; }
.sidebar { background: rgba(29, 36, 32, .985); }
.brand { letter-spacing: -.025em; }
.section { padding-block: clamp(58px, 7vw, 96px); }
.cover-image img { width: 100%; height: 100%; object-fit: cover; }
.cover-image::after { content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(12, 17, 14, .90), rgba(12, 17, 14, .62) 54%, rgba(12, 17, 14, .18)); }
.section-head, .day-plan-head { max-width: 1040px; }
.section-head > div, .day-plan-head > div { min-width: 0; }
.section-head h2, .day-plan-head h2 { letter-spacing: -.035em; }
.guide-skip { position: fixed; left: 16px; top: 12px; z-index: 2000; transform: translateY(-160%); padding: 10px 14px; border-radius: 10px; background: white; color: #1d1d1f; box-shadow: var(--shadow); }
.guide-skip:focus { transform: translateY(0); }
.guide-menu { display: none; min-height: 44px; padding: 8px 14px; border: 1px solid #50675b; border-radius: 10px; background: transparent; color: white; font-weight: 700; cursor: pointer; }
:where(a, button, input, summary):focus-visible { outline: 3px solid #c4a775; outline-offset: 3px; }
.sidebar nav a { min-height: 38px; display: flex; align-items: center; }
.button { min-height: 42px; transition: transform .2s ease, box-shadow .2s ease, background-color .2s ease; }
.button:hover { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(20, 28, 24, .13); }
.day-plan-card { transition: transform .22s ease, background-color .22s ease, outline-color .22s ease; }
.day-plan-card:hover { transform: translateY(-2px); }
.excursion-card { border-top-width: 4px; }
.excursion-head { grid-template-columns: auto minmax(0, 1fr); }
.excursion-head > div { grid-column: 1 / -1; }
.credits-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; overflow: hidden; border: 1px solid var(--line); border-radius: 18px; background: var(--line); }
.credit-item { display: grid; gap: 4px; padding: 15px 17px; background: white; break-inside: avoid; }
.credit-item strong { font: 18px/1.2 var(--serif); }
.credit-item span { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
.footer { display: flex; justify-content: space-between; gap: 22px; }
.footer span { color: #aebcb5; text-align: right; }

@media (max-width: 900px) {
  .sidebar { grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: "brand menu" "search search" "nav nav"; }
  .brand { grid-area: brand; }
  .guide-menu { display: inline-flex; grid-area: menu; align-items: center; justify-content: center; }
  .search { grid-area: search; width: 100%; max-width: none; }
  .sidebar nav { grid-area: nav; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); max-height: min(62vh, 540px); overflow: auto; padding-top: 8px; }
  .sidebar nav[hidden] { display: none !important; }
  .section { scroll-margin-top: 150px; }
}

@media (max-width: 720px) {
  .cover { min-height: 690px; }
  .cover h1 { font-size: clamp(44px, 14vw, 58px); }
  .cover-content { padding: 72px 22px 54px; }
  .cover-meta span { font-size: 12px; }
  .credits-grid { grid-template-columns: 1fr; }
  .footer { display: grid; }
  .footer span { text-align: left; }
}

@media (max-width: 420px) {
  .sidebar nav { grid-template-columns: 1fr; }
  .facts { grid-template-columns: 1fr 1fr; }
  .section { padding-inline: 16px; }
  .excursion-card { padding: 16px; }
}

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; }
}

@media print {
  @page { size: A4; margin: 16mm 14mm 19mm; }
  body { font-size: 10pt; letter-spacing: 0; }
  .section { padding: 8mm 0; }
  .guide-menu, .guide-skip { display: none !important; }
  .cover { height: 250mm; min-height: 250mm; }
  .cover h1 { font-size: 43pt; }
  .cover-content { padding: 28mm 16mm; }
  .section-head h2, .day-plan-head h2 { font-size: 27pt; }
  .day-plan-section { break-before: page; }
  .excursion-section { break-before: page; }
  .excursion-notes { grid-template-columns: repeat(3, 1fr) !important; }
  .excursion-photo-lead .photo-card { width: 31.3%; }
  .excursion-group { break-before: page !important; }
  .excursion-group > header { break-after: avoid; page-break-after: avoid; }
  .excursion-grid { display: block; }
  .excursion-card { display: block; width: 100%; margin: 0; padding: 5mm; break-before: page; page-break-before: always; }
  .excursion-card:first-child { break-before: auto; page-break-before: auto; }
  .excursion-head h4 { font-size: 15.5pt; }
  .excursion-details dd { font-size: 8.7pt; line-height: 1.42; }
  .excursion-why { font-size: 10pt; }
  .checked, .excursion-sources h5, .excursion-sources .button { font-size: 7.8pt; }
  .photo-credits { break-before: page; }
  .credits-grid { grid-template-columns: repeat(2, 1fr); }
  .credit-item { padding: 3mm; }
  .credit-item strong { font-size: 10pt; }
  .credit-item span { font-size: 8.2pt; }
  .footer { display: flex; padding: 8mm 0 0; background: white; color: var(--ink); border-top: 1px solid var(--line); }
  .footer span { color: var(--muted); }
}
'''
(GUIDE / "styles.css").write_text(css, encoding="utf-8", newline="\n")

javascript = r'''(() => {
  "use strict";
  const guideKey = document.documentElement.dataset.guide || "milan-travel-guide";
  const storage = {
    get(key) { try { return localStorage.getItem(key); } catch (_) { return null; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch (_) {} },
    remove(key) { try { localStorage.removeItem(key); } catch (_) {} }
  };

  const menuButton = document.querySelector("#guideMenuToggle");
  const navigation = document.querySelector("#guideNavigation");
  const sidebar = document.querySelector(".sidebar");
  const compact = matchMedia("(max-width: 900px)");
  const setMenu = (open, restoreFocus = false) => {
    if (!menuButton || !navigation) return;
    const isOpen = compact.matches ? Boolean(open) : true;
    navigation.hidden = !isOpen;
    menuButton.setAttribute("aria-expanded", String(isOpen));
    menuButton.setAttribute("aria-label", isOpen ? "Close guide menu" : "Open guide menu");
    menuButton.textContent = isOpen ? "Close" : "Menu";
    if (isOpen && compact.matches) {
      requestAnimationFrame(() => navigation.querySelector("a")?.focus());
    } else if (restoreFocus) {
      menuButton.focus();
    }
  };
  const syncMenu = () => setMenu(!compact.matches);
  menuButton?.addEventListener("click", () => setMenu(menuButton.getAttribute("aria-expanded") !== "true"));
  navigation?.querySelectorAll("a").forEach(link => link.addEventListener("click", () => {
    if (compact.matches) setMenu(false);
  }));
  document.addEventListener("pointerdown", event => {
    if (!compact.matches || menuButton?.getAttribute("aria-expanded") !== "true") return;
    if (!sidebar?.contains(event.target)) setMenu(false);
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && compact.matches && menuButton?.getAttribute("aria-expanded") === "true") {
      event.preventDefault();
      setMenu(false, true);
    }
  });
  compact.addEventListener?.("change", syncMenu);
  syncMenu();

  const search = document.querySelector("#guideSearch");
  const searchStatus = document.querySelector("#searchStatus");
  const searchable = [...document.querySelectorAll("main > section[id]")];
  search?.addEventListener("input", () => {
    const term = search.value.trim().toLocaleLowerCase();
    let matches = 0;
    searchable.forEach(section => {
      const match = !term || section.textContent.toLocaleLowerCase().includes(term);
      section.hidden = !match;
      if (match) matches += 1;
    });
    if (searchStatus) searchStatus.textContent = term ? `${matches} sections match` : "";
  });

  const planInputs = [...document.querySelectorAll('.day-plan-card input[type="checkbox"]')];
  const builderDays = document.querySelector("#builderDays");
  const builderText = document.querySelector("#builderText");
  const updateBuilder = () => {
    const selected = planInputs.filter(input => input.checked);
    const days = selected.reduce((total, input) => total + Number(input.dataset.days || 1), 0);
    if (builderDays) builderDays.textContent = `${days} day${days === 1 ? "" : "s"} selected`;
    if (builderText) builderText.textContent = selected.length
      ? selected.map(input => input.dataset.title).join(" · ")
      : "Choose one or more day plans to shape your trip.";
  };
  planInputs.forEach(input => input.addEventListener("change", updateBuilder));
  document.querySelector("#builderClear")?.addEventListener("click", () => {
    planInputs.forEach(input => { input.checked = false; });
    updateBuilder();
  });
  updateBuilder();

  document.querySelectorAll('.check input[type="checkbox"]').forEach((input, index) => {
    const key = `${guideKey}-check-${input.dataset.key || index}`;
    input.checked = storage.get(key) === "1";
    input.addEventListener("change", () => storage.set(key, input.checked ? "1" : "0"));
  });
  document.querySelector("#resetChecks")?.addEventListener("click", () => {
    document.querySelectorAll('.check input[type="checkbox"]').forEach((input, index) => {
      input.checked = false;
      storage.remove(`${guideKey}-check-${input.dataset.key || index}`);
    });
  });

  const budgetInputs = [...document.querySelectorAll('.budget input[type="number"]')];
  const budgetTotal = document.querySelector("#budgetTotal");
  const updateBudget = () => {
    const total = budgetInputs.reduce((sum, input) => sum + (Number(input.value) || 0), 0);
    if (budgetTotal) budgetTotal.textContent = `${total.toFixed(0)} ${budgetTotal.dataset.currency || ""}`.trim();
  };
  budgetInputs.forEach(input => input.addEventListener("input", updateBudget));
  updateBudget();

  const photoButtons = [...document.querySelectorAll(".photo-open[data-photo]")];
  const photos = [];
  const seen = new Set();
  photoButtons.forEach(button => {
    if (!seen.has(button.dataset.photo)) {
      seen.add(button.dataset.photo);
      photos.push(button);
    }
  });
  const lightbox = document.querySelector("#lightbox");
  const lightboxImage = document.querySelector("#lightboxImage");
  const lightboxCaption = document.querySelector("#lightboxCaption");
  const lightboxSource = document.querySelector("#lightboxSource");
  let currentPhoto = "";
  let returnFocus = null;
  const backgroundNodes = [document.querySelector(".app"), document.querySelector(".footer"), document.querySelector(".guide-skip")].filter(Boolean);
  const showPhoto = button => {
    if (!button || !lightboxImage || !lightboxCaption || !lightboxSource) return;
    currentPhoto = button.dataset.photo;
    lightboxImage.src = button.dataset.full;
    lightboxImage.alt = button.dataset.title;
    lightboxCaption.textContent = `${button.dataset.title} · ${button.dataset.creator}`;
    lightboxSource.href = button.dataset.source;
  };
  const openPhoto = button => {
    if (!lightbox) return;
    returnFocus = button;
    showPhoto(button);
    lightbox.classList.add("open");
    lightbox.setAttribute("aria-hidden", "false");
    backgroundNodes.forEach(node => { node.inert = true; });
    document.body.style.overflow = "hidden";
    document.querySelector("#lightboxClose")?.focus();
  };
  const closePhoto = () => {
    if (!lightbox) return;
    lightbox.classList.remove("open");
    lightbox.setAttribute("aria-hidden", "true");
    backgroundNodes.forEach(node => { node.inert = false; });
    document.body.style.overflow = "";
    returnFocus?.focus();
  };
  const shiftPhoto = delta => {
    const index = photos.findIndex(button => button.dataset.photo === currentPhoto);
    if (index >= 0) showPhoto(photos[(index + delta + photos.length) % photos.length]);
  };
  photoButtons.forEach(button => button.addEventListener("click", () => openPhoto(button)));
  document.querySelector("#lightboxClose")?.addEventListener("click", closePhoto);
  document.querySelector("#lightboxPrev")?.addEventListener("click", () => shiftPhoto(-1));
  document.querySelector("#lightboxNext")?.addEventListener("click", () => shiftPhoto(1));
  lightbox?.addEventListener("click", event => { if (event.target === lightbox) closePhoto(); });
  document.addEventListener("keydown", event => {
    if (!lightbox?.classList.contains("open")) return;
    if (event.key === "Escape") closePhoto();
    if (event.key === "ArrowLeft") shiftPhoto(-1);
    if (event.key === "ArrowRight") shiftPhoto(1);
    if (event.key === "Tab") {
      const focusable = [...lightbox.querySelectorAll("button:not([disabled]), a[href]")].filter(element => element.offsetParent !== null);
      const first = focusable[0];
      const last = focusable.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }
  });

  const visibleSections = [...document.querySelectorAll("main > section[id]")];
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(entries => {
      const current = entries.filter(entry => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!current) return;
      navigation?.querySelectorAll("a").forEach(link => link.classList.toggle("active", link.getAttribute("href") === `#${current.target.id}`));
    }, { rootMargin: "-20% 0px -68%", threshold: [0, .15, .4] });
    visibleSections.forEach(section => observer.observe(section));
  }
})();
'''
(GUIDE / "app.js").write_text(javascript, encoding="utf-8", newline="\n")

print(f"Built {GUIDE / 'index.html'} with {len(photo_data)} responsive photographs.")
