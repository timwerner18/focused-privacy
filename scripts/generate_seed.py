#!/usr/bin/env python3
"""
24SEVEN E-Kiosk – Seed-Generator
Liest die Automaten-Verkaufsstatistik (data/automat-statistik-*.csv) und erzeugt:
  - products_seed.csv   (Shopify-Importformat, Sorten-Familien als Varianten)
  - data/preisanalyse.csv (Stückpreis-Analyse: Automat-VK -> Online-Preis)

Preislogik:
  - Automaten-Preis = Umsatz / Verkäufe, gerundet auf 5 Cent (= compare_at_price)
  - Online-Preis    = ~7 % darunter (min. 10 Cent), auf 5 Cent gerundet;
                      Artikel <= 1,55 € behalten den Automatenpreis (Marge zu klein)
  - Bestseller-Tag  = Top 25 Produkte nach verkauften Einheiten
  - Social Proof    = Verkaufszahl im Beschreibungstext ab 30 Verkäufen/Monat
"""
import csv
import re
import sys
import unicodedata
from collections import defaultdict

STATS = 'data/automat-statistik-2026-07.csv'
OUT_SEED = 'products_seed.csv'
OUT_ANALYSE = 'data/preisanalyse.csv'

# ---------------------------------------------------------------- Helpers

def parse_stats(path):
    rows = []
    with open(path, encoding='utf-8-sig') as f:
        for r in csv.reader(f, delimiter=';'):
            if len(r) < 3 or r[0] == 'Produkt' or not r[0].strip():
                continue
            name = r[0].strip()
            if 'Unbekanntes Produkt' in name:
                continue
            try:
                qty = float(r[1].replace(',', '.'))
                rev = float(r[2].replace('.', '').replace(',', '.'))
            except ValueError:
                continue
            if qty <= 0 or rev <= 0:
                continue
            rows.append((name, int(qty), rev, rev / qty))
    return rows


def round05(x):
    return round(round(x * 20) / 20, 2)


def price_pair(unit):
    automat = round05(unit)
    if automat <= 1.55:
        return automat, automat
    online = round05(automat - max(0.10, automat * 0.07))
    if online >= automat:
        online = round(automat - 0.05, 2)
    return automat, online


def slugify(s):
    s = s.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    s = s.replace("'", '').replace('&', 'und').replace('€', 'eur')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return s


def fmt(x):
    return f'{x:.2f}'

# ------------------------------------------------- Varianten-Gruppierung
# (regex, produkt_key) – erste passende Regel gewinnt, Gruppe 1 = Variantenname
GROUPS = [
    (r'^Elfbar Pods (.+)$', 'elfbar-pods'),
    (r'^Elfbar (.+) Pods$', 'elfbar-pods'),
    (r'^(?:ELFLIQ|Elfliq) (.+)$', 'elfliq'),
    (r'^Elfbar 800 (.+)$', 'elfbar-800'),
    (r'^RandM (.+) Liquid$', 'randm-liquid'),
    (r'^RandM (.+) Pods$', 'randm-tornado-pod'),
    (r'^Tornado Pro (Pods)$', 'randm-tornado-pod'),
    (r'^Red Bull (.+)$', 'red-bull'),
    (r'^Monster (.+)$', 'monster'),
    (r'^Gönrgy (.+)$', 'goenrgy'),
    (r'^Capri Sonne (.+)$', 'capri-sonne'),
    (r'^Active O2 (.+)$', 'active-o2'),
    (r'^Calypso (.+)$', 'calypso'),
    (r'^Durstlöscher (.+)$', 'durstloescher'),
    (r'^Powerade (.+)$', 'powerade'),
    (r'^MoguMogu (.+)$', 'mogu-mogu'),
    (r'^Takis (.+)$', 'takis'),
    (r'^Doritos (.+)$', 'doritos'),
    (r'^Pringles (.+)$', 'pringles'),
    (r'^Trolli (.+)$', 'trolli'),
    (r'^Hitschies (.+)$', 'hitschies'),
    (r'^Buldak (.+)$', 'buldak'),
    (r'^Y[uU]m[yY]um (.+)$', 'yumyum'),
    (r'^FREEZES (.+)$', 'freezes'),
    (r'^Happy Amsterdam (.+)$', 'happys-amsterdam'),
    (r'^1g Onlygrams (.+) Blüte$', 'onlygrams-bluete'),
    (r'^Onlygrams PREROLLS (.+)$', 'onlygrams-prerolls'),
    (r'^Onlygrams (.+) Prerolls$', 'onlygrams-prerolls'),
    (r'^Onlygrams (.+) Vape$', 'onlygrams-vape'),
    (r'^1g (H3B(?:TA|A)) (.+)$', 'h3bta', 2),
    (r'^H3BTA (.+)$', 'h3bta'),
    (r'^(?:2g )?Green8 (.+)$', 'green8'),
    (r'^4Blockz (.+)$', '4blockz'),
    (r'^(?:1,5g )?MeshFlash (.+?)(?: Preroll)?$', 'meshflash'),
    (r'^HighPuffs? (.+?) Vape$', 'highpuffs'),
    (r'^Jack Daniels (.+)$', 'jack-daniels'),
    (r'^Jim Beam (.+)$', 'jim-beam'),
    (r'^Fanta (.+)$', 'fanta'),
    (r'^Lipton Sparkling (.+)$', 'lipton-sparkling'),
    (r'^Fuze Tea (.+)$', 'fuze-tea'),
    (r'^Nescafe (.+)$', 'nescafe'),
    (r'^Starbucks (.+)$', 'starbucks'),
    (r'^Mixery (.+)$', 'mixery'),
    (r'^Somersby (.+)$', 'somersby'),
    (r'^Skittle (.+)$', 'skittles'),
    (r'^Vio (.+)$', 'vio'),
    (r'^Three Sixty (.+)$', 'three-sixty'),
    (r'^LYNE (.+)$', 'lyne'),
    (r'^Pablo (.+)$', 'pablo'),
    (r'^American Spirit (.+)$', 'american-spirit'),
    (r'^Pueblo (.+)$', 'pueblo'),
    (r'^Siberia (.+)$', 'siberia'),
    (r'^Skruf (.+)$', 'skruf'),
    (r'^Gizeh (.+)$', 'gizeh'),
    (r'^Massiv (?:Zahnstocher )?(.+?)(?: Zahnstocher)?$', 'massiv-zahnstocher'),
    (r'^(\d+€) Neuware Pack$', 'neuware-pack'),
    (r'^Hubba (.+)$', 'hubba-bubba'),
    (r'^Bifi ?(.*)$', 'bifi'),
    (r'^Mentos (.+)$', 'mentos'),
    (r'^Extra Professional (.+)$', 'extra-professional'),
    (r'^Toffifee ?(.*)$', 'toffifee'),
    (r'^Yfood (.+)$', 'yfood'),
    (r'^7Days (.+)$', '7days'),
    (r'^Manner ?(.*)$', 'manner'),
    (r'^Bueno (.+)$', 'kinder-bueno'),
    (r'^M&M (.+)$', 'mms'),
    (r'^Paulaner (.+)$', 'paulaner'),
    (r'^Milka (.+)$', 'milka'),
    (r'^Kong Crunch (.+)$', 'kong-crunch'),
    (r'^Elfliq (.+)$', 'elfliq'),
]

# Titel/Vendor/Option je Gruppe
GROUP_META = {
    'elfbar-pods': ('Elfbar Elfa Prefilled Pods (2er-Pack)', 'Elf Bar', 'Pods', 'Geschmack'),
    'elfliq': ('Elfbar ELFLIQ Nikotinsalz-Liquid 10 ml', 'Elf Bar', 'Liquid', 'Geschmack'),
    'elfbar-800': ('Elfbar 800 Einweg-Vape', 'Elf Bar', 'Einweg-Vape', 'Geschmack'),
    'randm-liquid': ('RandM Liquid 10 ml', 'RandM / Fumot', 'Liquid', 'Geschmack'),
    'randm-tornado-pod': ('RandM Tornado Prefilled Pods (2er-Pack)', 'RandM / Fumot', 'Pods', 'Geschmack'),
    'red-bull': ('Red Bull Energy Drink 250 ml', 'Red Bull', 'Energy Drink', 'Sorte'),
    'monster': ('Monster Energy 500 ml', 'Monster', 'Energy Drink', 'Sorte'),
    'goenrgy': ('Gönrgy Energy 500 ml', 'Gönrgy', 'Energy Drink', 'Sorte'),
    'capri-sonne': ('Capri-Sonne 330 ml', 'Capri-Sun', 'Softdrink', 'Sorte'),
    'active-o2': ('Active O2 500 ml', 'Active O2', 'Wasser', 'Sorte'),
    'calypso': ('Calypso Lemonade 473 ml', 'Calypso', 'Trend-Drink', 'Sorte'),
    'durstloescher': ('Durstlöscher 500 ml', 'Durstlöscher', 'Eistee', 'Sorte'),
    'powerade': ('Powerade 500 ml', 'Powerade', 'Sportgetränk', 'Sorte'),
    'mogu-mogu': ('Mogu Mogu 320 ml', 'Mogu Mogu', 'Trend-Drink', 'Sorte'),
    'takis': ('Takis Chips', 'Takis', 'Chips', 'Sorte'),
    'doritos': ('Doritos Chips', 'Doritos', 'Chips', 'Sorte'),
    'pringles': ('Pringles', 'Pringles', 'Chips', 'Sorte'),
    'trolli': ('Trolli Fruchtgummi', 'Trolli', 'Süßwaren', 'Sorte'),
    'hitschies': ('Hitschies', 'Hitschler', 'Süßwaren', 'Sorte'),
    'buldak': ('Buldak Ramen', 'Samyang', 'Instant-Nudeln', 'Sorte'),
    'yumyum': ('YumYum Instant-Nudeln', 'YumYum', 'Instant-Nudeln', 'Sorte'),
    'freezes': ('FREEZES Candy', 'FREEZES', 'Süßwaren', 'Sorte'),
    'happys-amsterdam': ("Happy's Amsterdam", "Happy's Amsterdam", 'Cannabinoid-Produkt', 'Sorte'),
    'onlygrams-bluete': ('Onlygrams Blüte 1 g', 'OnlyGrams', 'Cannabinoid-Produkt', 'Sorte'),
    'onlygrams-prerolls': ('Onlygrams Prerolls', 'OnlyGrams', 'Cannabinoid-Produkt', 'Sorte'),
    'onlygrams-vape': ('Onlygrams Vape 1 ml', 'OnlyGrams', 'Cannabinoid-Produkt', 'Sorte'),
    'h3bta': ('H3BTA 1 g', 'H3BTA', 'Cannabinoid-Produkt', 'Sorte'),
    'green8': ('Green8 2 g', 'Green8', 'Cannabinoid-Produkt', 'Sorte'),
    '4blockz': ('4Blockz', '4Blockz', 'Cannabinoid-Produkt', 'Sorte'),
    'meshflash': ('MeshFlash', 'MeshFlash', 'Cannabinoid-Produkt', 'Sorte'),
    'highpuffs': ('HighPuffs Vape', 'HighPuffs', 'Cannabinoid-Produkt', 'Sorte'),
    'jack-daniels': ('Jack Daniel\'s Mix-Dose 330 ml', 'Jack Daniel\'s', 'Longdrink-Dose', 'Sorte'),
    'jim-beam': ('Jim Beam Mix-Dose 330 ml', 'Jim Beam', 'Longdrink-Dose', 'Sorte'),
    'fanta': ('Fanta', 'Fanta', 'Softdrink', 'Sorte'),
    'lipton-sparkling': ('Lipton Sparkling 330 ml', 'Lipton', 'Eistee', 'Sorte'),
    'fuze-tea': ('Fuze Tea 400 ml', 'Fuze Tea', 'Eistee', 'Sorte'),
    'nescafe': ('Nescafé Dose 250 ml', 'Nescafé', 'Kaffee-Drink', 'Sorte'),
    'starbucks': ('Starbucks Kaffee-Drink 220 ml', 'Starbucks', 'Kaffee-Drink', 'Sorte'),
    'mixery': ('Mixery 500 ml', 'Mixery', 'Biermischgetränk', 'Sorte'),
    'somersby': ('Somersby Cider 330 ml', 'Somersby', 'Cider', 'Sorte'),
    'skittles': ('Skittles', 'Skittles', 'Süßwaren', 'Sorte'),
    'vio': ('Vio Wasser 500 ml', 'Vio', 'Wasser', 'Sorte'),
    'three-sixty': ('Three Sixty Vodka Mix-Dose', 'Three Sixty', 'Longdrink-Dose', 'Sorte'),
    'lyne': ('LYNE Vape', 'LYNE', 'Einweg-Vape', 'Geschmack'),
    'pablo': ('Pablo Nikotinbeutel', 'Pablo', 'Nikotinbeutel', 'Sorte'),
    'american-spirit': ('American Spirit Drehtabak 30 g', 'American Spirit', 'Drehtabak', 'Sorte'),
    'pueblo': ('Pueblo Drehtabak 30 g', 'Pueblo', 'Drehtabak', 'Sorte'),
    'siberia': ('Siberia Snus', 'Siberia', 'Nikotinbeutel', 'Sorte'),
    'skruf': ('Skruf Snus', 'Skruf', 'Nikotinbeutel', 'Sorte'),
    'gizeh': ('Gizeh Papers & Filter', 'Gizeh', 'Drehzubehör', 'Sorte'),
    'massiv-zahnstocher': ('Massiv Zahnstocher (aromatisiert)', 'Massiv', 'Trend-Artikel', 'Sorte'),
    'neuware-pack': ('Neuware Mystery Pack', '24SEVEN', 'Mystery Pack', 'Wert'),
    'hubba-bubba': ('Hubba Bubba Kaugummi', 'Hubba Bubba', 'Süßwaren', 'Sorte'),
    'bifi': ('BiFi', 'BiFi', 'Snack', 'Sorte'),
    'mentos': ('Mentos', 'Mentos', 'Süßwaren', 'Sorte'),
    'extra-professional': ('Extra Professional Kaugummi', 'Extra', 'Süßwaren', 'Sorte'),
    'toffifee': ('Toffifee', 'Storck', 'Süßwaren', 'Sorte'),
    'yfood': ('YFood Trinkmahlzeit 330 ml', 'YFood', 'Trend-Drink', 'Sorte'),
    '7days': ('7Days Croissant', '7Days', 'Snack', 'Sorte'),
    'manner': ('Manner Waffeln', 'Manner', 'Süßwaren', 'Sorte'),
    'kinder-bueno': ('Kinder Bueno', 'Ferrero', 'Süßwaren', 'Sorte'),
    'mms': ("M&M's", "M&M's", 'Süßwaren', 'Sorte'),
    'paulaner': ('Paulaner Limo 500 ml', 'Paulaner', 'Softdrink', 'Sorte'),
    'milka': ('Milka', 'Milka', 'Süßwaren', 'Sorte'),
    'kong-crunch': ('Kong Crunch Snack', 'Kong Crunch', 'Snack', 'Sorte'),
}

# ------------------------------------------------------ Kategorisierung
CANNA = ['h3bta', 'h3ba', 'onlygrams', 'kilogrammes', 'green8', '4blockz', 'meshflash', 'highpuff', 'og 420']
VAPE = ['elfbar', 'elfliq', 'elfx', 'randm', 'flerbar', 'lyne', 'tornado']
TABAK = ['gizeh', 'pueblo', 'marlboro', 'american spirit', 'purize', 'siberia', 'skruf', 'pablo', 'ocb', 'raw ']
ALK = ['ur-krostizer', 'krombacher', 'heineken', 'desparados', 'somersby', 'sternburg', 'radeberger',
       'becks', 'paulberger', 'berliner luft', 'jägermeister', 'feigling', 'zarewitsch', 'vodka',
       'jack daniels', 'jim beam', 'havanna club', 'likör', 'three sixty', 'mixery', 'effect vodka']
DRINKS = ['red bull', 'monster', 'gönrgy', 'coca cola', 'fanta', 'sprite', 'mezzo', 'dr. pepper',
          'vita cola', 'powerade', 'capri sonne', 'durstlöscher', 'vio ', 'active o2', 'volvic',
          'fuze tea', 'lipton', 'mountain dew', 'calypso', 'mogumogu', 'starbucks', 'nescafe',
          'yfood', 'erdbeermilch', 'kakaomilch', 'schokomilch', 'paulaner', 'effect']
MYSTERY = ['neuware pack', 'mystery pack', 'erotik pack']
SONSTIGES = ['duftbaum', 'durex', 'panini', 'zahnstocher']


def categorize(name, group):
    n = name.lower()
    if group == 'happys-amsterdam' or 'happy amsterdam' in n:
        return "Happy's Amsterdam", 'happys, age_restricted', '🌴'
    if any(k in n for k in MYSTERY):
        tags = 'mystery'
        if 'erotik' in n:
            tags += ', age_restricted'
        return 'Mystery Packs', tags, '🎁'
    if any(k in n for k in CANNA):
        return 'Onlygrams & H3BTA', 'onlygrams, age_restricted', '🫐'
    if any(k in n for k in VAPE):
        tags = 'vape, age_restricted'
        if 'leer pod' not in n and 'refillable' not in n and 'elfx' not in n and 'master' not in n:
            tags = 'vape, nikotin, age_restricted'
        return 'Vapes & Liquids', tags, '💨'
    if any(k in n for k in TABAK):
        if group == 'gizeh' or 'purize' in n:
            return 'Tabak & Drehzubehör', 'drehzubehoer', '📜'
        return 'Tabak & Drehzubehör', 'tabak, age_restricted', '🚬'
    if any(k in n for k in ALK):
        return 'Bier & Spirituosen', 'alkohol, age_restricted', '🍺'
    if any(k in n for k in SONSTIGES):
        return 'Sonstiges & Trend', 'sonstiges', '🧿'
    if any(k in n for k in DRINKS):
        return 'Getränke', 'getraenke', '🥤'
    return 'Snacks & Sweets', 'snacks', '🍫'


DESC = {
    'Vapes & Liquids': 'TPD2-konform. Dieses Produkt kann Nikotin enthalten: einen Stoff, der abhängig macht. Abgabe nur ab 18 Jahren. Batteriehinweise siehe Batteriegesetz-Seite.',
    "Happy's Amsterdam": 'Bekannt von unseren Automaten in Aue und Zwickau. Abgabe nur ab 18 Jahren. Verkauf nur im rechtlich zulässigen Rahmen; Produktangaben siehe Verpackung.',
    'Onlygrams & H3BTA': 'Abgabe nur ab 18 Jahren. Verkauf nur im rechtlich zulässigen Rahmen; Produktangaben siehe Verpackung.',
    'Tabak & Drehzubehör': 'Rauchen fügt Ihnen und den Menschen in Ihrer Umgebung erheblichen Schaden zu. Abgabe nur ab 18 Jahren.',
    'Bier & Spirituosen': 'Alkoholhaltiges Getränk – Abgabe nur ab 18 Jahren. Bitte verantwortungsvoll genießen.',
    'Getränke': 'Gut gekühlt am besten. Pfandartikel werden zzgl. Pfand berechnet.',
    'Snacks & Sweets': 'Der Snack für zwischendurch – direkt aus dem Kiosk-Sortiment.',
    'Mystery Packs': 'Überraschungsinhalt – genau das ist der Spaß. Widerrufsrecht bleibt unberührt.',
    'Sonstiges & Trend': 'Trend-Artikel aus dem Kiosk-Sortiment.',
}

# Drehzubehör braucht keinen Tabak-Warnhinweis
DESC_DREH = 'Zubehör aus dem Kiosk-Sortiment – Papers, Filter & mehr.'


def main():
    rows = parse_stats(STATS)

    # Gruppieren
    products = {}   # key -> dict(title, vendor, type, option, variants=[(vname, qty, rev)], names=[])
    order = []

    def add(key, title, vendor, ptype, option, vname, name, qty, rev):
        if key not in products:
            products[key] = dict(title=title, vendor=vendor, type=ptype, option=option,
                                 variants=[], names=[])
            order.append(key)
        products[key]['variants'].append((vname, qty, rev))
        products[key]['names'].append(name)

    for name, qty, rev, unit in rows:
        matched = False
        for rule in GROUPS:
            pat, key = rule[0], rule[1]
            grp_idx = rule[2] if len(rule) > 2 else 1
            m = re.match(pat, name)
            if m:
                vname = (m.group(grp_idx) or 'Original').strip() or 'Original'
                meta = GROUP_META[key]
                add(key, meta[0], meta[1], meta[2], meta[3], vname, name, qty, rev)
                matched = True
                break
        if not matched:
            key = slugify(name)
            vendor = name.split()[0]
            add(key, name, vendor, '', 'Title', 'Default Title', name, qty, rev)

    # Bestseller: Top 25 nach Gesamt-Verkäufen
    totals = {k: sum(v[1] for v in p['variants']) for k, p in products.items()}
    bestsellers = set(sorted(totals, key=lambda k: -totals[k])[:25])

    header = ['Handle', 'Title', 'Body (HTML)', 'Vendor', 'Type', 'Tags', 'Published',
              'Option1 Name', 'Option1 Value', 'Variant SKU', 'Variant Inventory Tracker',
              'Variant Inventory Qty', 'Variant Inventory Policy', 'Variant Fulfillment Service',
              'Variant Price', 'Variant Compare At Price', 'Variant Requires Shipping',
              'Variant Taxable', 'Status', 'Collection']
    out = [header]
    analyse = [['Produkt', 'Variante', 'Verkäufe/Monat', 'Umsatz €', 'Automat VK €', 'Online-Preis €', 'Collection']]

    for key in order:
        p = products[key]
        first_name = p['names'][0]
        collection, tags, emoji = categorize(first_name, key)
        total_qty = totals[key]
        tag_list = tags
        if key in bestsellers:
            tag_list += ', bestseller'

        desc_extra = DESC_DREH if 'drehzubehoer' in tags else DESC.get(collection, '')
        proof = ''
        if total_qty >= 30:
            proof = f'<p><strong>🔥 {total_qty}× diesen Monat an unseren Automaten gekauft.</strong></p>'
        body = f'<p>{p["title"]} – wie am Automaten in Aue &amp; Zwickau, online günstiger.</p>{proof}<p>{desc_extra}</p>'

        handle = key if not key[0].isdigit() else 'p-' + key
        for i, (vname, qty, rev) in enumerate(sorted(p['variants'], key=lambda v: -v[1])):
            automat, online = price_pair(rev / qty)
            sku = (handle[:14] + '-' + slugify(vname)[:16]).upper().replace('-', '')[:20]
            inv = max(3, min(60, qty // 2))
            row = [handle]
            if i == 0:
                row += [p['title'], body, p['vendor'], p['type'], tag_list, 'TRUE']
            else:
                row += ['', '', '', '', '', '']
            row += [p['option'], vname, sku, 'shopify', str(inv), 'deny', 'manual',
                    fmt(online), fmt(automat) if automat > online else '',
                    'TRUE', 'TRUE', 'active', collection if i == 0 else '']
            out.append(row)
            analyse.append([p['title'], vname, qty, fmt(rev), fmt(automat), fmt(online), collection])

    # ------------------------------------------------ Daten-basierte Bundles
    def bundle(handle, title, body, vendor, tags, online, compare, collection='Bundles & Deals', qty=15):
        out.append([handle, title, body, vendor, 'Bundle', 'bundle, ' + tags, 'TRUE',
                    'Title', 'Default Title', ('BND-' + handle)[:20].upper().replace('-', ''),
                    'shopify', str(qty), 'deny', 'manual', fmt(online), fmt(compare),
                    'TRUE', 'TRUE', 'active', collection])
        analyse.append([title, 'Bundle', '', '', fmt(compare), fmt(online), collection])

    bundle('energy-mix-6er', 'Energy Mix 6er-Pack',
           '<p>Bundle: 6 Dosen aus unseren Energy-Bestsellern – Red Bull Original/White, Monster White/Loco/Original + Überraschung. Über 600 Energy-Verkäufe im Monat an unseren Automaten – hier als Spar-Sixpack. Zzgl. Pfand.</p>',
           '24SEVEN', 'getraenke, energy', 13.90, 16.00)
    bundle('drehset-klassiker', 'Drehset Klassiker – Pueblo + Gizeh (18+)',
           '<p>Bundle: Pueblo Classic 30 g + Gizeh King Size Slim + Gizeh Slim Filter – die drei meistgekauften Dreh-Artikel unserer Automaten in einem Set.</p><p>Rauchen fügt Ihnen und den Menschen in Ihrer Umgebung erheblichen Schaden zu. Abgabe nur ab 18 Jahren.</p>',
           '24SEVEN', 'tabak, age_restricted', 9.90, 10.75)
    bundle('h3bta-haze-trio', 'H3BTA Haze Trio – 3× 1 g (18+)',
           '<p>Bundle: je 1 g Amnezia Haze, Lemon Haze und Gelato Haze – unsere drei H3BTA-Topseller (zusammen über 150 Verkäufe/Monat).</p><p>Abgabe nur ab 18 Jahren. Verkauf nur im rechtlich zulässigen Rahmen.</p>',
           'H3BTA', 'onlygrams, age_restricted', 34.90, 38.70)
    bundle('happys-amsterdam-3er-set', "Happy's Amsterdam 3er-Set (18+)",
           '<p>Bundle: 3 Sorten nach Wahl unseres Teams (z. B. Amnezia Haze, Golden Kush, Cali Exotic). Am Automaten 89,70 € – online deutlich günstiger.</p><p>Abgabe nur ab 18 Jahren. Verkauf nur im rechtlich zulässigen Rahmen.</p>',
           "Happy's Amsterdam", 'happys, age_restricted', 79.90, 89.70, qty=8)
    bundle('onlygrams-vape-duo', 'Onlygrams Vape Duo – 2 Sorten (18+)',
           '<p>Bundle: 2× Onlygrams Vape nach Wahl (z. B. Peach Ice – unser Umsatz-Champion mit fast 1.900 € Monatsumsatz – plus Frozen Berries oder Dragon Fruit Blackberry).</p><p>Abgabe nur ab 18 Jahren. Verkauf nur im rechtlich zulässigen Rahmen.</p>',
           'OnlyGrams', 'onlygrams, age_restricted', 54.90, 59.80, qty=10)
    bundle('elfbar-pods-trio', 'Elfbar Pods Trio – 3× 2er-Pack (18+)',
           '<p>Bundle: 3× Elfa Prefilled Pods Doppelpack in 3 Sorten nach Wahl unseres Teams (6 Pods gesamt).</p><p>Dieses Produkt enthält Nikotin: einen Stoff, der sehr stark abhängig macht. Abgabe nur ab 18 Jahren. TPD2-konform.</p>',
           'Elf Bar', 'vape, nikotin, age_restricted', 31.90, 35.85)
    bundle('snack-attack-box', 'Snack Attack Box',
           '<p>Bundle: 2× Chips (Takis/Doritos) + 2× Candy (Trolli/Hitschies) + 2× Drink (Capri-Sonne/Durstlöscher) – die komplette Movie-Night, fertig gepackt.</p>',
           '24SEVEN', 'snacks', 12.90, 15.00, qty=25)
    bundle('feierabend-paket', 'Feierabend-Paket (18+)',
           '<p>Bundle: 2× Ur-Krostitzer 0,5 l + BiFi Roll + Erdnüsse – der sächsische Feierabend, fertig gepackt. Zzgl. Pfand.</p><p>Alkoholhaltig – Abgabe nur ab 18 Jahren.</p>',
           '24SEVEN', 'alkohol, age_restricted', 8.90, 9.70, qty=20)

    with open(OUT_SEED, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(out)
    with open(OUT_ANALYSE, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(analyse)

    n_products = len(order) + 8
    print(f'{OUT_SEED}: {len(out)-1} SKU-Zeilen, {n_products} Produkte (davon 8 Bundles)')
    print(f'{OUT_ANALYSE}: {len(analyse)-1} Zeilen')
    cols = defaultdict(int)
    for key in order:
        c, _, _ = categorize(products[key]['names'][0], key)
        cols[c] += 1
    for c, n in sorted(cols.items(), key=lambda x: -x[1]):
        print(f'  {n:>3}  {c}')


if __name__ == '__main__':
    sys.exit(main())
