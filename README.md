# 24SEVEN E-Kiosk – Shopify Theme & Setup

High-Converting Shopify-Shop für **24SEVEN E-Kiosk** (24seven-ekiosk.de) – der Online-Ableger der automatisierten 24/7-Kioske in Aue (Postplatz 4) und Zwickau.

**Positionierung:** „Dein Kiosk. Jetzt auch online." – komplettes Kiosk-Sortiment nach Hause, online günstiger als am Automaten, 1–3 Tage Lieferzeit.

---

## Repo-Inhalt

| Pfad | Inhalt |
|---|---|
| `24seven-theme/` | Custom Theme (Online Store 2.0, Liquid + JSON-Templates, Dawn-kompatible Struktur) |
| `products_seed.csv` | 52 Produkte / 71 SKUs im Shopify-Importformat, inkl. 5 Bundles & Mystery Packs |
| `legal-pages/` | Platzhaltertexte für alle Rechtsseiten (**VOM ANWALT PRÜFEN LASSEN**) |

## Theme-Features

- **Dark-Neon-Design** (#0c0a14 / #1b1530, Akzente Lila/Violett/Pink, Erfolgsgrün) über Design-Token-System in `snippets/theme-tokens.liquid`
- **Preisvergleich Automat vs. Online** auf jeder Card/Produktseite (`compare_at_price` = Automaten-Preis) + „Online günstiger"-Badge
- **Cart-Drawer** mit Free-Shipping-Fortschrittsbalken, Upsell-Slot „Passt dazu", **PLZ-Checker** (08xxx/09xxx → „Express-Region – meist in 24 h")
- **Sticky Add-to-Cart** (mobil), Quick-Add auf Collection-Cards
- **Ehrliche Knappheit:** „Nur noch X auf Lager" nur bei echtem Bestand ≤ 5, kein Fake-Timer
- **Age-Gate** (Cookie, 30 Tage), 18+-Badges via Tag `age_restricted`, Altersverifikations-Hinweis im Cart
- **Cookie-Consent** über Shopify Customer Privacy API; Meta Pixel & GA4 laden **erst nach Marketing-Consent** (IDs in den Theme-Settings)
- **Newsletter-Popup** (Exit-Intent, einmalig, Double-Opt-in-Hinweis) + Newsletter-Section
- **SEO:** Title/Meta-Templates je Seitentyp, JSON-LD für Organization, LocalBusiness (beide Standorte), Product, FAQPage
- Vanilla JS (~13 KB unminified), keine Frameworks, lokal gehostete Fonts (kein Google-CDN)

## Setup

### 1. Voraussetzungen

```bash
npm install -g @shopify/cli@latest
```

### 2. Fonts ablegen (einmalig)

Variable Fonts herunterladen (z. B. von fonts.google.com → Download, **nicht** per CDN einbinden) und ablegen als:

- `24seven-theme/assets/inter-variable.woff2`
- `24seven-theme/assets/archivo-variable.woff2`

Ohne die Dateien fällt das Theme auf System-Fonts zurück. Logo ersetzen: `24seven-theme/assets/logo.png`.

### 3. Lokale Entwicklung

```bash
cd 24seven-theme
shopify theme dev --store=DEIN-STORE.myshopify.com
```

### 4. Produkte importieren

Shopify Admin → **Produkte → Importieren** → `products_seed.csv` hochladen.

Danach:
1. **Collections anlegen** (die CSV-Spalte „Collection" erzeugt manuelle Collections für die Erstzuordnung; empfohlen sind zusätzlich automatische Collections per Tag):

   | Collection | Handle | Automatische Bedingung (Tag) |
   |---|---|---|
   | Vapes & Liquids | `vapes-liquids` | `vape` |
   | Happy's Amsterdam | `happys-amsterdam` | `happys` |
   | Onlygrams & H3BTA | `onlygrams-h3bta` | `onlygrams` ODER `h3bta` |
   | Getränke | `getraenke` | `getraenke` |
   | Snacks & Sweets | `snacks-sweets` | `snacks` ODER `sweets` |
   | Tabak & Drehzubehör | `tabak-drehzubehoer` | `tabak` ODER `drehzubehoer` |
   | Mystery Packs | `mystery-packs` | `mystery` |
   | Bundles & Deals | `bundles-deals` | `bundle` |
   | Bestseller | `bestseller` | `bestseller` |
   | Neu im Kiosk | `neu-im-kiosk` | `neu` |

   **Wichtig:** Die Handles müssen exakt so lauten – `templates/index.json` und das Age-Gate referenzieren sie.
2. **Navigation:** Hauptmenü (`main-menu`) mit den 8 Sortiments-Collections befüllen; Unterpunkte erzeugen das Mega-Menü.
3. **Filter:** App **Shopify Search & Discovery** (kostenlos) installieren und Filter für Marke (Vendor), Geschmack (Option) und Preis aktivieren – das Collection-Template rendert `collection.filters` automatisch.
4. **Metafelder für Bundles** (optional): `custom.bundle_hinweis` (Text) und `custom.bundle_inhalt` (Rich Text) anlegen – werden in der Bundle-Box auf Produktseiten angezeigt.

### 5. Seiten anlegen

Admin → **Onlineshop → Seiten**: für jede Datei in `legal-pages/` eine Seite mit demselben Handle anlegen (impressum, datenschutz, agb, widerruf, widerrufsformular, versand-zahlung, jugendschutz, batteriegesetz, ueber-uns, standorte) und den Inhalt einfügen. Footer-Links zeigen bereits auf diese Handles.

### 6. Theme veröffentlichen

```bash
shopify theme push --store=DEIN-STORE.myshopify.com
```

---

## ⚠️ Payment-Provider (wichtig, vor Launch klären!)

**Shopify Payments erlaubt keine E-Zigaretten-/Tabakprodukte** (Prohibited Businesses der zugrunde liegenden Acquirer). Shopify Payments für diesen Shop **nicht aktivieren** – es drohen Auszahlungssperren und Account-Kündigung. Stattdessen einen Drittanbieter konfigurieren:

| Option | Vorteile | Nachteile |
|---|---|---|
| **Spezialisierte High-Risk-Gateways** (z. B. auf Vape-/Tabak-Handel ausgerichtete PSPs, via „Drittanbieter-Zahlungsanbieter" in Shopify) | Kreditkarte möglich, auf die Branche eingestellt, geringes Sperr-Risiko | Höhere Gebühren, Onboarding mit Prüfung, teils Rolling Reserve |
| **Vorkasse / Banküberweisung (manuelle Zahlung)** | Sofort verfügbar, keine Gebühren, kein Sperr-Risiko | Conversion-Killer als einzige Option, manueller Abgleich |
| **Klarna / PayPal direkt** | Bekannt, hohe Conversion | AGB beider Anbieter schließen Tabak/E-Zigaretten je nach Vertrag aus – **vor Aktivierung schriftlich klären**, sonst Kontosperrung möglich |

Empfehlung: High-Risk-Gateway als Hauptzahlart + Vorkasse als Fallback; PayPal/Klarna nur nach schriftlicher Freigabe.

## Altersverifikation (zweistufig, Pflicht für Nikotinversand)

1. **Bei Bestellung:** Altersverifikations-App installieren, z. B. eine Age-Verification-App aus dem Shopify App Store mit echter Verifikation (Ausweis-/Datenbank-Check, z. B. via Schufa IdentitätsCheck o. ä.) – das reine Age-Gate im Theme ist **keine** rechtssichere Verifikation, nur die erste Hürde.
2. **Bei Zustellung:** Versand aller 18+-Bestellungen als **DHL „Alterssichtprüfung 18+"** (im DHL-Geschäftskundenportal als Service buchen; in Shopify über Versandprofile/Apps auf Produkte mit Tag `age_restricted` anwenden).
3. Der Hinweisblock im Cart (Theme, automatisch bei `age_restricted`-Produkten) informiert Kund:innen über beide Stufen.

## Launch-Checkliste

- [ ] Fonts in `assets/` abgelegt, Logo & Favicon ersetzt
- [ ] Produkte importiert, Collections + Navigation angelegt
- [ ] Search & Discovery installiert, Filter konfiguriert
- [ ] Alle `legal-pages/`-Seiten angelegt und **vom Anwalt freigegeben**
- [ ] Payment-Provider eingerichtet (kein Shopify Payments!), Testbestellung durchgeführt
- [ ] Altersverifikations-App aktiv + DHL Alterssichtprüfung 18+ gebucht und getestet
- [ ] Versandprofile: Preise, Gratisversand-Schwelle (Theme-Setting „Gratisversand ab" identisch konfigurieren!)
- [ ] Impressum-/USt-Angaben, Zwickauer Adresse in `structured-data.liquid`, `index.json` (Store-Locator) und `standorte`-Seite eintragen
- [ ] Meta Pixel / GA4 IDs in Theme-Settings (laden nur nach Consent)
- [ ] Lighthouse-Check mobil (Ziel ≥ 90, LCP < 2 s) – Hero ist CSS-only, keine Render-Blocker außer base.css
- [ ] Pfand-Ausweisung bei Getränken prüfen
- [ ] Test: Age-Gate („Nein" blockiert 18+-Collections), PLZ-Checker, Cart-Drawer, Newsletter-Double-Opt-in

## Offene rechtliche To-dos

1. **Cannabinoid-Produkte (Happy's Amsterdam, Onlygrams, H3BTA):** Rechtliche Einordnung der konkreten Inhaltsstoffe (HHC-Nachfolger, H3-/H4-CBD etc.) **vor Launch juristisch prüfen lassen** – Rechtslage ändert sich laufend (NpSG/KCanG); Produkte ggf. nicht online verkaufen.
2. Alle Platzhalter-Rechtstexte (`legal-pages/`) vom Anwalt erstellen/prüfen lassen (Impressum nach DDG, DSGVO, AGB, Widerruf inkl. Hygiene-Ausschluss, Jugendschutz, BattG).
3. **BattG/ElektroG-Registrierung** für den Vertrieb von Vapes (Batterien + Elektrogeräte, stiftung ear) prüfen.
4. **TabakerzG-Werbebeschränkungen:** Copy enthält bewusst keine Health-Claims/Verharmlosung – bei allen künftigen Texten und Ads beibehalten; Pflichtwarnhinweise auf Produktbildern/Verpackungen sicherstellen.
5. **Verpackungsgesetz (LUCID)**-Registrierung für Versandverpackungen.
6. PayPal/Klarna-Freigabe für Tabak-/Vape-Sortiment schriftlich einholen (siehe Payment-Tabelle).
7. Preisangabenverordnung: Grundpreise (€/ml bei Liquids, €/kg bei Snacks) ergänzen.

---

## Theme-Struktur (Kurzüberblick)

```
24seven-theme/
├── layout/theme.liquid          # Grundgerüst, Consent-abhängige Tracking-Slots
├── config/settings_schema.json  # Logo, Gratisversand-Schwelle, Pixel-IDs
├── locales/de.default.json
├── templates/*.json             # index, product, collection, cart, page, search, 404
├── sections/                    # header(-group), trust-bar, hero, usp-bar, category-grid,
│                                # featured-collection, brand-spotlight, savings-banner,
│                                # how-it-works, store-locator, newsletter, faq,
│                                # main-product, main-collection, cart-drawer, footer …
├── snippets/                    # theme-tokens, product-card, price-compare, badge-18plus,
│                                # age-gate, newsletter-popup, cookie-banner, meta-tags,
│                                # structured-data
└── assets/                      # base.css, theme.js, logo.png (+ Fonts, siehe Setup)
```
