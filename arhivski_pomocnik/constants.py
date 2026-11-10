"""Konstante, podatkovne sheme in privzeta navodila za AI."""
import os
import sys

USD_TO_EUR = 0.92

PRICING = {
    "Gemini": {
        "default_in": 0.075, "default_out": 0.30,
        "gemini-1.5-flash": {"in": 0.075, "out": 0.30},
        "gemini-1.5-pro": {"in": 1.25, "out": 5.00},
        "gemini-2.0-flash-exp": {"in": 0.075, "out": 0.30}
    },
    "OpenAI": {
        "default_in": 2.50, "default_out": 10.00,
        "gpt-4o-mini": {"in": 0.15, "out": 0.60},
        "gpt-4o": {"in": 2.50, "out": 10.00},
        "o1-mini": {"in": 3.00, "out": 12.00}
    },
    "Anthropic": {
        "default_in": 3.00, "default_out": 15.00,
        "claude-3-5-haiku-20241022": {"in": 0.25, "out": 1.25},
        "claude-3-5-sonnet-20241022": {"in": 3.00, "out": 15.00}
    }
}

API_LIMIT_PRESETS = {
    "VARČNO": {"rpm": 2, "tpm": 20000, "rpd": 50},
    "NORMALNO": {"rpm": 15, "tpm": 1000000, "rpd": 1500},
    "PO MERI": {"rpm": 15, "tpm": 1000000, "rpd": 1500}
}

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SETTINGS_FILE = os.path.join(APP_DIR, "matricula_settings.txt")

PROMPT_FILE = os.path.join(APP_DIR, "matricula_prompt.txt")

ERROR_LOG_FILE = os.path.join(APP_DIR, "error_log.txt")

LEDGER_FILE = os.path.join(APP_DIR, "arhivski_pomocnik_evidenca.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/127.0.0.0 Safari/537.36",
    "Referer": "https://data.matricula-online.eu/",
}

SCHEMA_FIELDS = {
    "KRSTNE": [
        ("vpis_st_knjige", "zap. št. v knjigi", "INT NOT NULL"),
        ("vpis_st_na_strani", "zap. št. na strani", "INT NOT NULL"),
        ("zp_st", "zp. št.", "VARCHAR(50)"), ("zupnija", "župnija", "VARCHAR(150)"), 
        ("datum_rojstva", "datum rojstva", "VARCHAR(50)"), ("datum_krsta", "datum krsta", "VARCHAR(50)"), 
        ("naslov", "naslov", "VARCHAR(150)"), ("ime_otroka", "ime otroka", "VARCHAR(150)"), 
        ("ime_oceta", "ime očeta", "VARCHAR(150)"), ("priimek_oceta", "priimek očeta", "VARCHAR(150)"), 
        ("alt_priimek_oceta", "alt. priimek očeta", "VARCHAR(150)"), 
        ("ime_matere", "ime matere", "VARCHAR(150)"), ("priimek_matere", "priimek matere", "VARCHAR(150)"), 
        ("alt_priimek_matere", "alt. priimek matere", "VARCHAR(150)"), 
        ("poklic_oceta", "poklic očeta", "VARCHAR(150)"), ("izvor_oceta", "izvor očeta", "VARCHAR(150)"), 
        ("botri", "botri", "TEXT"), ("babica", "babica", "VARCHAR(150)"), 
        ("duhovnik", "duhovnik", "VARCHAR(150)"), ("opombe", "opombe", "TEXT"), 
        ("knjiga", "knjiga", "VARCHAR(100)"), ("slika", "slika", "VARCHAR(100)"), ("surovi_tekst", "surovi tekst", "TEXT")
    ],
    "POROCNE": [
        ("vpis_st_knjige", "zap. št. v knjigi", "INT NOT NULL"),
        ("vpis_st_na_strani", "zap. št. na strani", "INT NOT NULL"),
        ("zp_st", "zp. št.", "VARCHAR(50)"), ("zupnija", "župnija", "VARCHAR(150)"), ("datum_poroke", "datum poroke", "VARCHAR(50)"), 
        ("naslov_zenina", "naslov ženina", "VARCHAR(150)"), ("naslov_neveste", "naslov neveste", "VARCHAR(150)"),
        ("ime_zenina", "ime ženina", "VARCHAR(150)"), ("priimek_zenina", "priimek ženina", "VARCHAR(150)"), 
        ("starost_zenina", "starost ženina", "VARCHAR(50)"), ("stan_zenina", "stan ženina", "VARCHAR(150)"), ("izvor_zenina", "izvor ženina", "VARCHAR(150)"),
        ("ime_neveste", "ime neveste", "VARCHAR(150)"), ("priimek_neveste", "priimek neveste", "VARCHAR(150)"), 
        ("starost_neveste", "starost neveste", "VARCHAR(50)"), ("stan_neveste", "stan neveste", "VARCHAR(150)"), ("izvor_neveste", "izvor neveste", "VARCHAR(150)"),
        ("price", "priče", "TEXT"), ("duhovnik", "duhovnik", "VARCHAR(150)"), ("opombe", "opombe", "TEXT"), 
        ("knjiga", "knjiga", "VARCHAR(100)"), ("slika", "slika", "VARCHAR(100)"), ("surovi_tekst", "surovi tekst", "TEXT")
    ],
    "KNJIGE_MRTVIH": [
        ("vpis_st_knjige", "zap. št. v knjigi", "INT NOT NULL"),
        ("vpis_st_na_strani", "zap. št. na strani", "INT NOT NULL"),
        ("zp_st", "zp. št.", "VARCHAR(50)"), ("zupnija", "župnija", "VARCHAR(150)"), 
        ("datum_smrti", "datum smrti", "VARCHAR(50)"), ("datum_pokopa", "datum pokopa", "VARCHAR(50)"), ("naslov", "naslov", "VARCHAR(150)"),
        ("ime_pokojnika", "ime pokojnika", "VARCHAR(150)"), ("priimek_pokojnika", "priimek pokojnika", "VARCHAR(150)"), 
        ("starost", "starost", "VARCHAR(50)"), ("vzrok_smrti", "vzrok smrti", "VARCHAR(255)"),
        ("stan_pokojnika", "stan pokojnika", "VARCHAR(150)"), ("izvor_pokojnika", "izvor pokojnika", "VARCHAR(150)"), 
        ("zakonec_starsi", "zakonec/starši", "VARCHAR(255)"),
        ("duhovnik", "duhovnik", "VARCHAR(150)"), ("opombe", "opombe", "TEXT"), 
        ("knjiga", "knjiga", "VARCHAR(100)"), ("slika", "slika", "VARCHAR(100)"), ("surovi_tekst", "surovi tekst", "TEXT")
    ]
}

EXCEL_COLUMNS = {k: [col[1] for col in v] for k, v in SCHEMA_FIELDS.items()}

DEFAULT_PROMPT = (
    "To je stran iz zgodovinske slovenske matične knjige. Tvoja naloga je natančna transkripcija in "
    "strukturiranje podatkov v JSON za neposreden prenos v bazo.\n\n"
    "1. PRAVILA ZA BRANJE\n"
    "Jeziki in pisave: slovenščina, nemščina, latinščina. Pisava je lahko kurent (gotica).\n"
    "Natančnost: Imena, priimke in kraje prepiši strogo dobesedno. Ne sloveniziraj in ne prevajaj.\n"
    "Nečitljivo: Zapiši [nečitljivo], v dvomu dodaj vprašaj, npr. [Zauzen?].\n"
    "Prečrtano: Ohrani in jasno označi popravke.\n\n"
    "2. STRUKTURIRANJE PODATKOV\n"
    "Vsak dogodek je samostojen JSON zapis. Datum normaliziraj v YYYY-MM-DD. "
    "Če podatek manjka, uporabi null. Ne izmišljaj si podatkov.\n"
    "Vrstni red zapisov ohrani natančno tako, kot si sledijo v knjigi na sliki "
    "(od prvega do zadnjega; ne razvrščaj jih po datumu ali priimku).\n\n"
    "3. OBVEZNA IZHODNA STRUKTURA – JSON\n"
    "Rezultat mora biti seznam objektov. Ne uporabljaj markdown oznak ali uvodov. Samo čist JSON array."
)

BOOK_TYPE_INSTRUCTIONS = {

    "KRSTNE": (
        "VRSTA DOKUMENTA: KRSTNA MATIČNA KNJIGA.\n"
        "Vsak posamezen krstni vpis obravnavaj kot samostojen dogodek.\n\n"

        "POMEN POSAMEZNIH POLJ:\n"
        "- zp_st: izvirna zaporedna številka vpisa. "
        "Če je ni, uporabi prazen podatek. Ne izmišljaj številke.\n"
        "- datum_rojstva: datum rojstva otroka.\n"
        "- datum_krsta: datum dejanskega krsta.\n"
        "- naslov: hišna številka oziroma prebivališče družine.\n"
        "- ime_otroka: vsa osebna imena otroka. Priimka ne ugibaj.\n"
        "- ime_oceta: osebno ime očeta, vključno z vsemi navedenimi imeni.\n"
        "- priimek_oceta: priimek očeta v izvirni obliki.\n"
        "- alt_priimek_oceta: alternativni oziroma vulgo priimek očeta, "
        "samo kadar je izrecno naveden.\n"
        "- ime_matere: osebno ime matere.\n"
        "- priimek_matere: priimek matere v izvirni obliki.\n"
        "- alt_priimek_matere: dekliški ali drug alternativni priimek matere, "
        "če je izrecno naveden.\n"
        "- poklic_oceta: izvirno navedeni poklic očeta.\n"
        "- izvor_oceta: kraj izvora oziroma rojstva očeta, "
        "ne njegovo trenutno prebivališče.\n"
        "- botri: vsa imena in priimki botrov v prvotnem vrstnem redu. "
        "Več oseb loči s podpičjem.\n"
        "- babica: babica oziroma porodna pomočnica, če je navedena.\n"
        "- duhovnik: ime in priimek duhovnika.\n"
        "- opombe: legitimacije, nezakonskost, popravki, prečrtanja "
        "in druge pomembne informacije.\n"
        "- surovi_tekst: celoten dobesedni prepis posameznega krstnega vpisa.\n\n"

        "POSEBNA PRAVILA:\n"
        "Ne zamenjuj podatkov očeta in matere. "
        "Ne sklepaj o priimku otroka na podlagi priimka očeta. "
        "Alternativnega priimka ne zamenjuj z običajnim priimkom. "
        "Pri nezakonskih otrocih ne izmišljaj podatkov o očetu. "
        "Ohrani vse naknadne legitimacije in popravke."
    ),

    "POROCNE": (
        "VRSTA DOKUMENTA: POROČNA MATIČNA KNJIGA.\n"
        "Vsako sklenitev zakonske zveze obravnavaj kot samostojen dogodek.\n\n"

        "POMEN POSAMEZNIH POLJ:\n"
        "- zp_st: izvirna zaporedna številka poročnega vpisa.\n"
        "- datum_poroke: datum sklenitve zakonske zveze.\n"
        "- naslov_zenina: prebivališče oziroma naslov ženina.\n"
        "- naslov_neveste: prebivališče oziroma naslov neveste.\n"
        "- ime_zenina: vsa osebna imena ženina.\n"
        "- priimek_zenina: priimek ženina.\n"
        "- starost_zenina: starost ženina, kot je zapisana.\n"
        "- stan_zenina: izvirno navedeni stan oziroma zakonski status ženina.\n"
        "- izvor_zenina: kraj izvora ženina.\n"
        "- ime_neveste: vsa osebna imena neveste.\n"
        "- priimek_neveste: priimek neveste.\n"
        "- starost_neveste: starost neveste, kot je zapisana.\n"
        "- stan_neveste: izvirno navedeni stan oziroma zakonski status neveste.\n"
        "- izvor_neveste: kraj izvora neveste.\n"
        "- price: priče pri poroki, nikoli cene ali zneski. "
        "Navedi vsa imena in priimke v prvotnem vrstnem redu.\n"
        "- duhovnik: ime in priimek duhovnika.\n"
        "- opombe: podatki o starših, prejšnjih zakonih, vdovstvu, "
        "posebnih okoliščinah in drugih pomembnih informacijah.\n"
        "- surovi_tekst: celoten dobesedni prepis posameznega poročnega vpisa.\n\n"

        "POSEBNA PRAVILA:\n"
        "Ženina in neveste nikoli ne zamenjuj. "
        "Podatkov njunih staršev ne pripisuj zakoncema. "
        "Priče ohrani v prvotnem vrstnem redu. "
        "Ohrani podatke o prejšnjih zakonih in zakonskem statusu."
    ),

    "KNJIGE_MRTVIH": (
        "VRSTA DOKUMENTA: MRLIŠKA MATIČNA KNJIGA.\n"
        "Vsak vpis o umrli osebi obravnavaj kot samostojen dogodek.\n\n"

        "POMEN POSAMEZNIH POLJ:\n"
        "- zp_st: izvirna zaporedna številka vpisa.\n"
        "- datum_smrti: datum smrti pokojnika.\n"
        "- datum_pokopa: datum pokopa, ločeno od datuma smrti.\n"
        "- naslov: hišna številka oziroma prebivališče pokojnika.\n"
        "- ime_pokojnika: vsa osebna imena pokojnika.\n"
        "- priimek_pokojnika: priimek pokojnika.\n"
        "- starost: starost v izvirni obliki, tudi če vključuje "
        "leta, mesece ali dneve.\n"
        "- vzrok_smrti: dobesedno navedeni vzrok smrti. "
        "Ne postavljaj lastne zdravstvene diagnoze.\n"
        "- stan_pokojnika: izvirno navedeni stan oziroma status pokojnika.\n"
        "- izvor_pokojnika: kraj izvora oziroma rojstva pokojnika.\n"
        "- zakonec_starsi: navedeni zakonec oziroma starši pokojnika. "
        "Vloge jasno označi, če so razvidne, npr. "
        "'Zakonec: ...; Oče: ...; Mati: ...'.\n"
        "- duhovnik: ime in priimek duhovnika.\n"
        "- opombe: dodatne okoliščine, popravki, prečrtanja "
        "in druge informacije, za katere ni posebnega polja.\n"
        "- surovi_tekst: celoten dobesedni prepis posameznega mrliškega vpisa.\n\n"

        "POSEBNA PRAVILA:\n"
        "Loči datum smrti od datuma pokopa. "
        "Ne zamenjuj pokojnika z njegovimi starši ali zakoncem. "
        "Starost prepiši brez preračunavanja. "
        "Vzroka smrti ne interpretiraj ali medicinsko dopolnjuj."
    )
}

# Samodejno sestavljanje posebnega JSON-prompta za vsako vrsto matične knjige.
# Ta blok mora ostati v constants.py: brez njega je slovar prazen in AI
# transkripcija se ustavi z napako KeyError: 'KRSTNE'.
PROMPT_JSON_SCHEMAS = {}

for book_type, fields in SCHEMA_FIELDS.items():
    ai_fields = [
        field for field in fields
        if field[0] not in (
            "zupnija", "knjiga", "slika", "vpis_st_knjige", "vpis_st_na_strani"
        )
    ]

    json_keys = [f'"{field[0]}": null' for field in ai_fields]
    schema_str = "[\n  {\n    " + ",\n    ".join(json_keys) + "\n  }\n]"

    PROMPT_JSON_SCHEMAS[book_type] = (
        f"\n\nVRSTA MATIČNE KNJIGE: {book_type}\n\n"
        "OBVEZNA JSON STRUKTURA:\n"
        "Vsak posamezen dogodek mora biti samostojen objekt.\n"
        "Uporabi natančno naslednje ključe:\n\n"
        f"{schema_str}\n\n"
        "OBVEZNA PRAVILA:\n"
        "- Uporabi vse navedene ključe v vsakem objektu.\n"
        "- Ne spreminjaj imen ključev.\n"
        "- Ne dodajaj novih ključev.\n"
        "- Ne izpuščaj nobenega ključa.\n"
        "- Objekte v JSON seznamu vrni v natančnem vrstnem redu vpisov na sliki, "
        "od prvega do zadnjega; ne razvrščaj po datumu ali priimku.\n"
        "- Polja zupnija, knjiga, slika, vpis_st_knjige in vpis_st_na_strani "
        "določi program; ne izmišljaj si jih in jih ne vključuj v JSON.\n"
        "- Vsa polja morajo biti prisotna v vsakem objektu.\n"
        "- Manjkajoče podatke označi z null.\n"
        "- Vse vrednosti morajo biti besedilni nizi ali null.\n"
        "- Ne uporabljaj besedila 'None' ali 'neznano' za manjkajoče podatke.\n"
        "- Ne ugibaj in ne izmišljaj podatkov.\n"
        "- Vsak dogodek mora imeti svoj celoten surovi_tekst.\n\n"
        "PODROBNA NAVODILA ZA RAZVRŠČANJE:\n"
        f"{BOOK_TYPE_INSTRUCTIONS[book_type]}\n\n"
        "KONČNI IZPIS:\n"
        "Vrni samo veljaven JSON seznam objektov.\n"
        "Brez uvodnega ali zaključnega besedila.\n"
        "Brez Markdown oznak in komentarjev."
    )

DL_PRESETS = {
    "POČASI": {"min_delay": 3.0, "max_delay": 7.0, "pause_every": 10, "pause_duration": 30.0, "timeout": 120, "retries": 5, "max_session": 50, "concurrent": 1},
    "NORMALNO": {"min_delay": 1.0, "max_delay": 3.0, "pause_every": 50, "pause_duration": 15.0, "timeout": 60, "retries": 3, "max_session": 200, "concurrent": 2},
    "HITRO": {"min_delay": 0.1, "max_delay": 1.0, "pause_every": 100, "pause_duration": 5.0, "timeout": 30, "retries": 2, "max_session": 500, "concurrent": 4}
}
