#!/usr/bin/env python3
# bib_clean_and_map.py
# Usage: python3 bib_clean_and_map.py sample.bib sample_clean.bib

import re, sys, os

if len(sys.argv) < 3:
    print("Usage: python3 bib_clean_and_map.py input.bib output.bib")
    sys.exit(1)

INFILE = sys.argv[1]
OUTFILE = sys.argv[2]

# Toggle: set True to remove url/publisher/ISSN for @article entries
REMOVE_EXTRA_FIELDS = True

# Journal mapping: full name -> APS-style compact name.
JOURNAL_MAP = {
    "Physical Review D": "Phys. Rev. D",
    "Physical Review B": "Phys. Rev. B",
    "Physics Letters B": "Phys. Lett. B",
    "Physical Review": "Phys. Rev.",
    "Physical Review Letters": "Phys. Rev. Lett.",
    "Progress of Theoretical and Experimental Physics": "Prog. Theor. Exp. Phys.",
    "Reviews of Modern Physics": "Rev. Mod. Phys.",
    "International Journal of Modern Physics A": "Int. J. Mod. Phys. A",
    "Journal of High Energy Physics": "JHEP",
    "Proceedings of the National Academy of Sciences": "Proc. Natl. Acad. Sci.",
    "Physics Reports": "Phys. Rep.",
    "The European Physical Journal C": "EPJC",
    "European Physical Journal C": "EPJC",
    "Kongelige Danske Videnskabernes Selskab, Mathematisk-fysiske Meddelelser": "Mat.-Fys. Medd.",
    "Zeitschrift für Physik": "Z. Phys.",
    "Scientific Reports": "Sci. Rep.",
    "Czechoslovak Journal of Physics": "Czech. J. Phys.",
    "Journal of Mathematical Physics": "J. Math. Phys.",
    "Nuclear Physics B": "Nucl. Phys. B",
    "Nuclear Physics A": "Nucl. Phys. A",
    "Physikalische Zeitschrift der Sowjetunion": "Phys. Z. Sowjetunion",
    "Philosophical Transactions of the Royal Society of London": "Philos. Trans. R. Soc.",
    "Soviet Physics - Journal of Experimental and Theoretical Physics": "Sov. Phys. JETP",
    "Foundations of Physics Letters": "Found. Phys. Lett.",
    "Contemporary Mathematics": "Contemp. Math.",
    "Contemporary Physics": "Contemp. Phys.",
    "Lecture Notes in Physics": "LNP",
    "Journal of Physics A: Mathematical and Theoretical": "J. Phys. A: Math. Theor.",
    "Journal of Chemical Physics": "J. Chem. Phys.",
    "Journal of Cosmology and Astroparticle Physics": "JCAP",
    "Nature Physics": "Nat. Phys.",
    "Journal of Applied Physics": "J. Appl. Phys.",
    "General Relativity and Gravitation": "Gen. Relativ. Gravit.",
    "Annals of Physics": "Ann. Phys.",
    "Physics-Uspekhi": "Phys. Usp.",
    "Astronomy {\&}amp; Astrophysics": "A{\&}A",
    "Astronomy {\&} Astrophysics": "A{\&}A",
    "EPJ Web of Conferences": "EPJ Web. Conf.",
    "The Astrophysical Journal": "ApJ",
    "Low Temperature Physics": "Low Temp. Phys.",
    "New Journal of Physics": "New J. Phys.",
    "Theoretical and Mathematical Physics": "Theor. Math. Phys.",
    # add more mappings as you like...
}

def map_journal_name(jval):
    # Try direct replacement, or case-insensitive match
    for long, short in JOURNAL_MAP.items():
        if long.lower() in jval.lower():
            return short
    return jval

def clean_entry_text(entry_text):
    # Replace Unicode en/em dashes with ASCII double-dash
    entry_text = entry_text.replace('–', '--').replace('—', '--')
    # Normalize page ranges: pages = {123--456}
    entry_text = re.sub(r'pages\s*=\s*\{([^\}]*)\}', 
                        lambda m: 'pages = {' + m.group(1).replace('-', '--').replace('–','--').replace('—','--') + '}', entry_text, flags=re.IGNORECASE)
    # Optionally remove url/publisher/ISSN fields inside @article
    if REMOVE_EXTRA_FIELDS:
        entry_text = re.sub(r'(?mi)^\s*(url|publisher|issn)\s*=\s*\{[^\}]*\}\s*,?\s*\n', '', entry_text)
    return entry_text

def parse_bib_entries(bibtext):
    # crude split at top-level '@' then restore '@' for each
    items = re.split(r'(?=@)', bibtext)
    parsed = []
    for it in items:
        it = it.strip()
        if not it: continue
        # find key
        m = re.match(r'@(\w+)\s*\{\s*([^,]+),', it, flags=re.DOTALL)
        if not m:
            continue
        etype = m.group(1).strip()
        key = m.group(2).strip()
        body = it[m.end():].rstrip().rstrip('}').strip()
        parsed.append({'etype':etype, 'key':key, 'raw':it, 'body':body})
    return parsed

def extract_fields(body):
    fields = {}
    for fm in re.finditer(r'(\w+)\s*=\s*(\{(?:[^{}]|\{[^}]*\})*\}|\"[^\"]*\"|[^,]+),?', body, re.DOTALL):
        name = fm.group(1).strip().lower()
        val = fm.group(2).strip()
        if val.startswith('{') and val.endswith('}'): val = val[1:-1].strip()
        elif val.startswith('"') and val.endswith('"'): val = val[1:-1].strip()
        fields[name] = val
    return fields

# Read bib file
with open(INFILE, 'r', encoding='utf-8') as f:
    text = f.read()

entries = parse_bib_entries(text)

report = []
out_entries = []

for ent in entries:
    raw = ent['raw']
    # apply journal mapping within raw text: find 'journal = {...}'
    body = ent['body']
    fields = extract_fields(body)
    if 'journal' in fields:
        orig = fields['journal']
        mapped = map_journal_name(orig)
        if mapped != orig:
            # replace the journal value in raw (first occurrence)
            raw = re.sub(r'(journal\s*=\s*\{)[^\}]*\}', r'\1' + mapped + '}', raw, flags=re.IGNORECASE, count=1)
    # clean the raw entry text
    raw = clean_entry_text(raw)
    # recompute fields after cleaning
    body2 = raw[raw.find(',')+1:].rstrip().rstrip('}').strip()
    fields2 = extract_fields(body2)
    # required & optional
    required = ['author','title','journal','year']
    optional = ['volume','number','pages','doi','eprint','month']
    missing_required = [r for r in required if r not in fields2]
    missing_optional = [o for o in optional if o not in fields2]
    report.append({'key':ent['key'], 'etype':ent['etype'], 'missing_required':missing_required, 'missing_optional':missing_optional})
    out_entries.append(raw)

# Write output .bib
with open(OUTFILE, 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(out_entries))

# Print summary
print("Wrote cleaned bibliography to:", OUTFILE)
print("Entries parsed:", len(report))
print("Entries missing required fields:")
for r in report:
    if r['missing_required']:
        print(" -", r['key'], "missing:", r['missing_required'])
print("\nSample (first 20) entries and missing optional fields:")
for r in report[:20]:
    print(" *", r['key'], "optional missing:", r['missing_optional'])
