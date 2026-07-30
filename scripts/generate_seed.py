#!/usr/bin/env python3
"""
24SEVEN E-Kiosk – Seed-Generator
Liest die Automaten-Verkaufsstatistik (data/automat-statistik-*.csv) und erzeugt:
  - products_seed.csv    (Shopify-Importformat, JEDER Listeneintrag = eigenes Produkt)
  - data/preisanalyse.csv (Stückpreis-Analyse: Automat-VK -> Online-Preis)

Preislogik:
  - Automaten-Preis = Umsatz / Verkäufe, gerundet auf 5 Cent (= compare_at_price)
  - Online-Preis    = ~7 % darunter (min. 10 Cent), auf 5 Cent gerundet;
                      Artikel <= 1,55 € behalten den Automatenpreis (Marge zu klein)
  - Bestseller-Tag  = Top 25 Artikel nach verkauften Einheiten
  - Social Proof    = Verkaufszahl im Beschreibungstext ab 30 Verkäufen/Monat
"""
import csv
import re
import sys
import unicodedata

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

# ---------------------------------------------------------------- Marken
BRANDS = [
    ('red bull', 'Red Bull'), ('monster', 'Monster'), ('gönrgy', 'Gönrgy'),
    ('coca cola', 'Coca-Cola'), ('fanta', 'Fanta'), ('sprite', 'Sprite'),
    ('mezzo mix', 'Mezzo Mix'), ('dr. pepper', 'Dr Pepper'), ('vita cola', 'Vita Cola'),
    ('capri sonne', 'Capri-Sun'), ('durstlöscher', 'Durstlöscher'), ('active o2', 'Active O2'),
    ('powerade', 'Powerade'), ('vio ', 'Vio'), ('volvic', 'Volvic'),
    ('fuze tea', 'Fuze Tea'), ('lipton', 'Lipton'), ('mountain dew', 'Mountain Dew'),
    ('calypso', 'Calypso'), ('mogumogu', 'Mogu Mogu'), ('starbucks', 'Starbucks'),
    ('nescafe', 'Nescafé'), ('yfood', 'YFood'), ('paulaner', 'Paulaner'),
    ('mixery', 'Mixery'), ('ur-krostizer', 'Ur-Krostitzer'), ('krombacher', 'Krombacher'),
    ('heineken', 'Heineken'), ('desparados', 'Desperados'), ('somersby', 'Somersby'),
    ('sternburg', 'Sternburg'), ('radeberger', 'Radeberger'), ('becks', "Beck's"),
    ('jack daniels', "Jack Daniel's"), ('jim beam', 'Jim Beam'), ('havanna club', 'Havana Club'),
    ('three sixty', 'Three Sixty'), ('effect', 'Effect'),
    ('gizeh', 'Gizeh'), ('pueblo', 'Pueblo'), ('marlboro', 'Marlboro'),
    ('american spirit', 'American Spirit'), ('purize', 'Purize'),
    ('siberia', 'Siberia'), ('skruf', 'Skruf'), ('pablo', 'Pablo'),
    ('elfbar', 'Elf Bar'), ('elfliq', 'Elf Bar'), ('elfx', 'Elf Bar'),
    ('randm', 'RandM / Fumot'), ('tornado', 'RandM / Fumot'), ('flerbar', 'Flerbar'),
    ('lyne', 'LYNE'), ('onlygrams', 'OnlyGrams'), ('h3bta', 'H3BTA'), ('h3ba', 'H3BTA'),
    ('happy amsterdam', "Happy's Amsterdam"), ('green8', 'Green8'), ('4blockz', '4Blockz'),
    ('meshflash', 'MeshFlash'), ('highpuff', 'HighPuffs'), ('kilogrammes', 'Kilogrammes'),
    ('takis', 'Takis'), ('doritos', 'Doritos'), ('pringles', 'Pringles'),
    ('trolli', 'Trolli'), ('haribo', 'Haribo'), ('hitschies', 'Hitschler'),
    ('buldak', 'Samyang'), ('yumyum', 'YumYum'), ('yum yum', 'YumYum'),
    ('milka', 'Milka'), ('bueno', 'Ferrero'), ('kinder', 'Ferrero'),
    ('duplo', 'Ferrero'), ('hanuta', 'Ferrero'), ('nutella', 'Ferrero'),
    ('m&m', "M&M's"), ('twix', 'Twix'), ('bounty', 'Bounty'), ('snickers', 'Snickers'),
    ('mars', 'Mars'), ('kitkat', 'KitKat'), ('toffifee', 'Storck'), ('manner', 'Manner'),
    ('7days', '7Days'), ('bifi', 'BiFi'), ('freezes', 'FREEZES'), ('kong crunch', 'Kong Crunch'),
    ('skittle', 'Skittles'), ('maoam', 'Maoam'), ('mentos', 'Mentos'), ('airwaves', 'Airwaves'),
    ('extra ', 'Extra'), ('hubba', 'Hubba Bubba'), ('reeses', "Reese's"), ('daim', 'Daim'),
    ('massiv', 'Massiv'), ('durex', 'Durex'), ('labubu', 'Labubu'),
    ('mystery pack', '24SEVEN'), ('neuware pack', '24SEVEN'), ('erotik pack', '24SEVEN'),
    ('24seven', '24SEVEN'),
]

def vendor_of(name):
    n = name.lower()
    for prefix, vendor in BRANDS:
        if prefix in n:
            return vendor
    return name.split()[0]

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


def categorize(name):
    n = name.lower()
    if 'happy amsterdam' in n:
        return "Happy's Amsterdam", 'happys, age_restricted', '🌴', 'Cannabinoid-Produkt'
    if any(k in n for k in MYSTERY):
        tags = 'mystery'
        if 'erotik' in n:
            tags += ', age_restricted'
        return 'Mystery Packs', tags, '🎁', 'Mystery Pack'
    if any(k in n for k in CANNA):
        return 'Onlygrams & H3BTA', 'onlygrams, age_restricted', '🫐', 'Cannabinoid-Produkt'
    if any(k in n for k in VAPE):
        return 'Vapes & Liquids', 'vape, nikotin, age_restricted', '💨', 'Vape'
    if any(k in n for k in TABAK):
        if 'gizeh' in n or 'purize' in n:
            return 'Tabak & Drehzubehör', 'drehzubehoer', '📜', 'Drehzubehör'
        return 'Tabak & Drehzubehör', 'tabak, age_restricted', '🚬', 'Tabakware'
    if any(k in n for k in ALK):
        return 'Bier & Spirituosen', 'alkohol, age_restricted', '🍺', 'Alkoholisches Getränk'
    if any(k in n for k in SONSTIGES):
        return 'Sonstiges & Trend', 'sonstiges', '🧿', 'Trend-Artikel'
    if any(k in n for k in DRINKS):
        return 'Getränke', 'getraenke', '🥤', 'Getränk'
    return 'Snacks & Sweets', 'snacks', '🍫', 'Snack'


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
DESC_DREH = 'Zubehör aus dem Kiosk-Sortiment – Papers, Filter & mehr.'


def main():
    rows = parse_stats(STATS)
    rows.sort(key=lambda r: -r[1])
    bestseller_names = {r[0] for r in rows[:25]}

    header = ['Handle', 'Title', 'Body (HTML)', 'Vendor', 'Type', 'Tags', 'Published',
              'Option1 Name', 'Option1 Value', 'Variant SKU', 'Variant Inventory Tracker',
              'Variant Inventory Qty', 'Variant Inventory Policy', 'Variant Fulfillment Service',
              'Variant Price', 'Variant Compare At Price', 'Variant Requires Shipping',
              'Variant Taxable', 'Status', 'Collection']
    out = [header]
    analyse = [['Produkt', 'Verkäufe/Monat', 'Umsatz €', 'Automat VK €', 'Online-Preis €', 'Collection']]
    seen = set()
    counts = {}

    for name, qty, rev, unit in rows:
        collection, tags, emoji, ptype = categorize(name)
        automat, online = price_pair(unit)
        handle = slugify(name)
        if handle[0].isdigit():
            handle = 'p-' + handle
        if handle in seen:
            handle += '-2'
        seen.add(handle)
        counts[collection] = counts.get(collection, 0) + 1

        tag_list = tags + (', bestseller' if name in bestseller_names else '')
        desc_extra = DESC_DREH if 'drehzubehoer' in tags else DESC.get(collection, '')
        proof = f'<p><strong>🔥 {qty}× diesen Monat an unseren Automaten gekauft.</strong></p>' if qty >= 30 else ''
        body = f'<p>{name} – wie am Automaten in Aue &amp; Zwickau, online günstiger.</p>{proof}<p>{desc_extra}</p>'
        sku = handle.upper().replace('-', '')[:20]
        inv = max(3, min(60, qty // 2))

        out.append([handle, name, body, vendor_of(name), ptype, tag_list, 'TRUE',
                    'Title', 'Default Title', sku, 'shopify', str(inv), 'deny', 'manual',
                    fmt(online), fmt(automat) if automat > online else '',
                    'TRUE', 'TRUE', 'active', collection])
        analyse.append([name, qty, fmt(rev), fmt(automat), fmt(online), collection])

    # ------------------------------------------------ Daten-basierte Bundles
    def bundle(handle, title, body, vendor, tags, online, compare, qty=15):
        out.append([handle, title, body, vendor, 'Bundle', 'bundle, ' + tags, 'TRUE',
                    'Title', 'Default Title', ('BND-' + handle)[:20].upper().replace('-', ''),
                    'shopify', str(qty), 'deny', 'manual', fmt(online), fmt(compare),
                    'TRUE', 'TRUE', 'active', 'Bundles & Deals'])
        analyse.append([title, '', '', fmt(compare), fmt(online), 'Bundles & Deals'])
        counts['Bundles & Deals'] = counts.get('Bundles & Deals', 0) + 1

    bundle('energy-mix-6er', 'Energy Mix 6er-Pack',
           '<p>Bundle: 6 Dosen aus unseren Energy-Bestsellern – Red Bull Original/White, Monster White/Loco/Original + Überraschung. Zzgl. Pfand.</p>',
           '24SEVEN', 'getraenke, energy', 13.90, 16.00)
    bundle('drehset-klassiker', 'Drehset Klassiker – Pueblo + Gizeh (18+)',
           '<p>Bundle: Pueblo Classic + Gizeh King Size Slim + Gizeh Slim Filter – die drei meistgekauften Dreh-Artikel unserer Automaten.</p><p>Rauchen fügt Ihnen und den Menschen in Ihrer Umgebung erheblichen Schaden zu. Abgabe nur ab 18 Jahren.</p>',
           '24SEVEN', 'tabak, age_restricted', 9.90, 10.75)
    bundle('h3bta-haze-trio', 'H3BTA Haze Trio – 3× 1 g (18+)',
           '<p>Bundle: je 1 g Amnezia Haze, Lemon Haze und Gelato Haze – unsere drei H3BTA-Topseller.</p><p>Abgabe nur ab 18 Jahren. Verkauf nur im rechtlich zulässigen Rahmen.</p>',
           'H3BTA', 'onlygrams, age_restricted', 34.90, 38.70)
    bundle('happys-amsterdam-3er-set', "Happy's Amsterdam 3er-Set (18+)",
           '<p>Bundle: 3 Sorten nach Wahl unseres Teams (z. B. Amnezia Haze, Golden Kush, Cali Exotic). Am Automaten 89,70 € – online deutlich günstiger.</p><p>Abgabe nur ab 18 Jahren. Verkauf nur im rechtlich zulässigen Rahmen.</p>',
           "Happy's Amsterdam", 'happys, age_restricted', 79.90, 89.70, qty=8)
    bundle('onlygrams-vape-duo', 'Onlygrams Vape Duo – 2 Sorten (18+)',
           '<p>Bundle: 2× Onlygrams Vape nach Wahl (z. B. Peach Ice – unser Umsatz-Champion – plus Frozen Berries oder Dragon Fruit Blackberry).</p><p>Abgabe nur ab 18 Jahren. Verkauf nur im rechtlich zulässigen Rahmen.</p>',
           'OnlyGrams', 'onlygrams, age_restricted', 54.90, 59.80, qty=10)
    bundle('elfbar-pods-trio', 'Elfbar Pods Trio – 3× 2er-Pack (18+)',
           '<p>Bundle: 3× Elfbar Pods Doppelpack in 3 Sorten nach Wahl unseres Teams (6 Pods gesamt).</p><p>Dieses Produkt enthält Nikotin: einen Stoff, der sehr stark abhängig macht. Abgabe nur ab 18 Jahren. TPD2-konform.</p>',
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

    print(f'{OUT_SEED}: {len(out)-1} Produkte (je 1 SKU, davon 8 Bundles)')
    for c, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f'  {n:>3}  {c}')


if __name__ == '__main__':
    sys.exit(main())
