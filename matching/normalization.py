# normalization.py

import re

UNICODE_NORMALIZATION = {
    "–": "-",
    "—": "-",
    "−": "-",
    "×": "x",
    "µ": "u",
    "™": "",
    "®": "",
    "’": "'",
    "´": "'",
}


def normalize_unicode(text: str) -> str:
    """
    Normalize common Unicode characters found in biotech catalogs.
    """
    if not text:
        return ""

    text = str(text)

    for old, new in UNICODE_NORMALIZATION.items():
        text = text.replace(old, new)

    return text


def normalize_whitespace(text: str) -> str:
    """
    Collapse whitespace and normalize line endings.
    """
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize(
    text: str,
    keep_chars: str = "-.",
) -> str:
    """
    General-purpose normalization for product names and aliases.

    Keeps:
        - letters
        - digits
        - whitespace
        - characters in keep_chars

    Replaces everything else with spaces.
    """
    if not text:
        return ""

    text = normalize_unicode(text)

    escaped = re.escape(keep_chars)

    text = re.sub(
        rf"[^\w\s{escaped}]",
        " ",
        text,
    )

    text = normalize_whitespace(text)

    return text


def normalize_for_matching(text: str) -> str:
    """
    Aggressive normalization for alias matching.
    """
    text = normalize(text)

    return text.casefold()



def shorten_product_name(product_name):
    short = []
    EDITIONS = ["1.0", "2.0", "3.0","4.0", "5.0", "6.0", "7.0", "8.0", "9.0"]
    EXCLUDE = ["for"]
    UNITS = [
    # volume
    "L", "mL", "uL", "nL", "pL",

    # mass
    "g", "mg", "ug", "ng", "pg",

    # concentration
    "M", "mM", "uM", "nM", "pM",
    
    "rxns"]
    DONT_CAPITALIZE = [
        "cdna",
        "qpcr",
        "pcr",
        "rt-pcr",
        "rtpcr",
        "qpcr",
        "rt-qpcr",
        "dna",
        "rna",
        "mrna",
        "trna",
        "rrna",
        "mirna",
        "and",
    ]

    def is_float(value):
        try:
            float(value)
            return True
        except ValueError:
            return False
    

    for w in product_name.split():
        w_norm = w.lower()

        # no 20, 20ml allowed
        # 2.0, 3.0 allowed

        if is_float(w_norm) or any(is_float(w_norm.replace(u.lower(),"").replace("(","").replace(")","")) for u in UNITS):
            if w_norm not in EDITIONS:
                break
            
        if w_norm in EXCLUDE:
            break
        
        if w_norm not in DONT_CAPITALIZE:
            w = w[0].upper() + w[1:]
        
        w = w.replace(",","").replace("*","")

        # miRNA Scrambled Control-MR03 Lentiviral Particles(25 Μl X
        # gets rid of (25 Ml X if product name poorly formatted
        
        w_original = w
        w = re.sub(r"\(\d.*$", "", w)

        short.append(w)

        # gets rid of (25 Ml X if product name poorly formatted
        if not w_original == w:
            break

    short = " ".join(short)

    # print(product_name)
    # print(short)

    return short




if __name__ == "__main__":
    product_names = """Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
Biotin Protein Ligase
EndoFectin™ Max transfection reagent (1ml)
Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
EndoFectin™ Max transfection reagent (1ml)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
Mycoplasma PCR detection kit (50 rxns)
Lenti-Pac 293Ta Cell Line (1.5 x 10^6 cells)
Lenti-Pac™ SARS-CoV-2 Full Length Spike protein-pseudotyped (D614G) Lentivirus Packaging Kit (40 reactions)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
Biotin Protein Ligase
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
EndoFectin™ Lenti transfection reagent (3ml)
Lenti-Pac 293Ta Cell Line (1.5 x 10^6 cells)
Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
All-in-One™ qPCR Mix (200 qPCR reactions)
pEZ-Lv235 expression vector for LxR recombination cloning (lentiviral)
EndoFectin™ Lenti transfection reagent (1ml)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)
RNAzol® RT RNA Isolation Reagent|SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)|BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
T7 endonuclease I assay kit, 50 rxns
Luc-Pair Duo-Luciferase HT Assay Kits (100ml)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)|BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
EndoFectin™ Lenti transfection reagent (1ml)
EndoFectin™ Max transfection reagent (3ml)
EndoFectin™ Max transfection reagent (3ml)
BlazeTaq™ SYBR® Green qPCR mix 2.0 (without ROX) (200 qPCR reactions)
Lenti-Pac HIV qRT-PCR Titration Kit (20 RT reactions, 50 PCR reactions)
EndoFectin™ Max transfection reagent (1ml)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
Secrete-Pair Gaussia Luciferase Assay Kit (1000 rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
Secrete-Pair Gaussia Luciferase Assay Kit (100 rxns)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
All-in-one (Cas9 + sgRNA) clone targeting human AAVS1
BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
BlazeTaq™ SYBR® Green qPCR mix 2.0 (600 qPCR reactions)
BlazeTaq™ SYBR® Green qPCR mix 2.0 (without ROX) (200 qPCR reactions)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
All-in-One™ qPCR Mix (200 qPCR reactions)
Lenti-Pac HIV qRT-PCR Titration Kit (20 RT reactions, 50 PCR reactions)
Secrete-Pair Gaussia Luciferase Assay Kit (100 rxns)
Lenti-Pac 293Ta Cell Line (1.5 x 10^6 cells)
BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)|SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
BlazeTaq™ One-Step SYBR Green RT-qPCR Kit (200 rxn, with ROX)
Brain and Neuronal-associated Antigen Array
All-in-one (Cas9 + sgRNA) clone targeting human AAVS1
EndoFectin™ Max transfection reagent (1ml)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)|Lenti-Pac™ Lentivirus Concentration Solution (50 ml)|Lenti-Pac HIV qRT-PCR Titration Kit (20 RT reactions, 50 PCR reactions)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (60 RT and 600 qPCR reactions)(Old cat # QP016)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)|SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)|BlazeTaq™ SYBR® Green qPCR mix 2.0 (1000 qPCR reactions)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
ExoSure™ Exosome Isolation Kit (20 reactions) 
EndoFectin™ Max transfection reagent (1ml)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
All-in-One™ qPCR Mix (200 qPCR reactions)
EndoFectin™ Lenti transfection reagent (3ml)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
Fireflyer luciferase (hLuc) and Renillar luciferase (Rluc) reporter vector |Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
Lenti-Pac 293Ta Cell Line (1.5 x 10^6 cells)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)
EndoFectin™ Max transfection reagent (1ml)
Mycoplasma PCR detection kit (50 rxns)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
RNAzol® RT RNA Isolation Reagent
All-in-One™ qPCR Mix (200 qPCR reactions)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)|BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
IndelCheck™ CRISPR/TALEN indel detection system advanced (50 rxns)
EndoFectin™ Max transfection reagent (1ml)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
Biotin Protein Ligase
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)|BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
Luc-Pair Duo-Luciferase HT Assay Kits (10ml)
BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)|Lenti-Pac HIV qRT-PCR Titration Kit (20 RT reactions, 50 PCR reactions)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
EndoFectin™ RNAi  transfection reagent (1 mL)
Luc-Pair Luciferase Assay Kits 2.0 (1000rxns)
EndoFectin™ Max transfection reagent (1ml)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)|BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
miRNA Scrambled Control-MR03 Lentiviral Particles(25 µl x 4 vials)(Old cat # LPP-CmiR0001-MR03-100-C)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)|Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
EndoFectin™ Max transfection reagent (1ml)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)
All-in-One™ qPCR Mix (200 qPCR reactions)
EndoFectin™ Max transfection reagent (1ml)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
EndoFectin™ Max transfection reagent (3ml)
Lenti-Pac™ Lentivirus Concentration Solution (50 ml)
Luc-Pair™ Firefly Luciferase HS Assay Kits (100rxns)
EndoFectin™ Max transfection reagent (1ml)
BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
Lenti-Pac 293Ta Cell Line (1.5 x 10^6 cells)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
EndoFectin™ Max transfection reagent (1ml)
All-in-One™ qPCR Mix (200 qPCR reactions)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
EndoFectin™ Lenti transfection reagent (1ml)
EndoFectin™ Max transfection reagent (1ml)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
Secrete-Pair Gaussia Luciferase Assay Kit (1000 rxns)
EndoFectin™ Max transfection reagent (1ml)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
EndoFectin™ Max transfection reagent (1ml)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
EndoFectin™ Lenti transfection reagent (1ml)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
Secrete-Pair Gaussia Luciferase Assay Kit (1000 rxns)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)|BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
EndoFectin™ Lenti transfection reagent (1ml)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (60 RT and 600 qPCR reactions)(Old cat # QP016)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
EndoFectin™ Max transfection reagent (1ml)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Lenti-Pac™ Lentivirus Concentration Solution (50 ml)
EndoFectin™ Max transfection reagent (1ml)
All-in-One™ qPCR Mix (200 qPCR reactions)
EndoFectin™ Lenti transfection reagent (1ml)
All-in-One™ qPCR Mix (200 qPCR reactions)
Secrete-Pair Gaussia Luciferase Assay Kit (1000 rxns)
Luc-Pair Luciferase Assay Kits 2.0 (1000rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
EndoFectin™ Max transfection reagent (1ml)
All-in-One™ qPCR Mix (200 qPCR reactions)
All-in-One™ qPCR Mix (4000 qPCR reactions)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)
Secrete-Pair Dual Luminescence Assay Kit (1000 rxns)
GeneHero™ mouse ROSA26 safe harbor gene knock-in kit
EndoFectin™ Max transfection reagent (1ml)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)|BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
All-in-One™ qPCR Mix (200 qPCR reactions)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)|EndoFectin™ Lenti transfection reagent (3ml)
EndoFectin™ Lenti transfection reagent (1ml)
Infection and Vaccination-associated Autoimmune Antigen Array
EndoFectin™ Max transfection reagent (1ml)
All-in-One™ qPCR Mix (200 qPCR reactions)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
All-in-One™ qPCR Mix (4000 qPCR reactions)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Secrete-Pair Gaussia Luciferase Assay Kit (1000 rxns)
VividFISH™ FFPE pretreatment kit|FISH CEP probe for human chromosome Y-orange
All-in-One™ qPCR Mix (200 qPCR reactions)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
NileHiFi® Long Amplicon PCR Kit
Secrete-Pair Gaussia Luciferase Assay Kit (1000 rxns)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)|Lenti-Pac 293Ta Cell Line (1.5 x 10^6 cells)
EndoFectin™ Max transfection reagent (3ml)
All-in-One™ qPCR Mix (200 qPCR reactions)
Mycoplasma PCR detection kit (50 rxns)
All-in-one (Cas9 + sgRNA) clone targeting human AAVS1|DC-DON-SH01 expression vector for restriction enzyme cloning (AAVS1 knockin)
Lenti-Pac HIV qRT-PCR Titration Kit (20 RT reactions, 50 PCR reactions)
EndoFectin™ Max transfection reagent (1ml)|BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)|SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
Lenti-Pac 293Ta Cell Line (1.5 x 10^6 cells)|Lenti-Pac HIV Expression Packaging Kit (40 reactions)
Biotin Protein Ligase
Luc-Pair™ Firefly Luciferase HS Assay Kits (1000rxns)
EndoFectin™ Max transfection reagent (1ml)
EndoFectin™ Max transfection reagent (1ml)
Lenti-Pac 293Ta Cell Line (1.5 x 10^6 cells)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (60 RT and 600 qPCR reactions)(Old cat # QP016)
Mycoplasma PCR detection kit (50 rxns)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
Gaussia luciferase (Gluc) and secreted alkaline phosphatase (SEAP) reporter vector
EndoFectin™ Max transfection reagent (3ml)
Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
Mycoplasma PCR detection kit (50 rxns)
EndoFectin™ Lenti transfection reagent (1ml)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
Secrete-Pair Dual Luminescence Assay Kit (1000 rxns)
Fireflyer luciferase (hLuc) and Renillar luciferase (Rluc) reporter vector 
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)|Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
All-in-One™ qPCR Mix (4000 qPCR reactions)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
EndoFectin™ Max transfection reagent (1ml)
Luc-Pair™ Firefly Luciferase HS Assay Kits (1000rxns)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
pEZ-Lv235 expression vector for LxR recombination cloning (lentiviral)
All-in-One™ qPCR Mix (200 qPCR reactions)
BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
BlazeTaq™ SYBR® Green qPCR mix 2.0 (without ROX) (200 qPCR reactions)
BlazeTaq™ One-Step SYBR Green RT-qPCR Kit (200 rxn, with ROX)
Secrete-Pair Dual Luminescence Assay Kit (1000 rxns)
Secrete-Pair Gaussia Luciferase Assay Kit (1000 rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Secrete-Pair Dual Luminescence Assay Kit (1000 rxns)
RNAzol® RT RNA Isolation Reagent
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
DC-DON-SH02 expression vector for restriction enzyme cloning (ROSA26 knockin)|Genome-TALER™  mouse ROSA26 safe harbor gene knock-in kit (without donor)
EndoFectin™ Max transfection reagent (1ml)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Lenti-Pac 293Ta Cell Line (1.5 x 10^6 cells)
EndoFectin™ Max transfection reagent (3ml)
Luc-Pair™ Firefly Luciferase HS Assay Kits (1000rxns)
Biotin Protein Ligase
All-in-One™ qPCR Mix (200 qPCR reactions)
DC-DON-SH01 expression vector for restriction enzyme cloning (AAVS1 knockin)|All-in-one (Cas9 + sgRNA) clone targeting human AAVS1
Secrete-Pair Dual Luminescence Assay Kit (1000 rxns)
BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)|All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (60 RT and 600 qPCR reactions)(Old cat # QP016)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
EndoFectin™ Max transfection reagent (1ml)
EndoFectin™ Max transfection reagent (3ml)
BlazeTaq™ One-Step SYBR Green RT-qPCR Kit (200 rxn, with ROX)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
All-in-One™ qPCR Mix (200 qPCR reactions)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
BlazeTaq™ SYBR® Green qPCR mix 2.0 (200 qPCR reactions)
RNAzol® RT RNA Isolation Reagent
All-in-One™ qPCR Mix (1000 qPCR reactions)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
GCI-L3 Chemically Competent E.coli Cells (10 tubes)|GCI-5? Chemically Competent E.coli Cells, (10 tubes)|Lenti-Pac HIV Expression Packaging Kit (20 reactions)|Lenti-Pac 293Ta Cell Line (1.5 x 10^6 cells)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Secrete-Pair Gaussia Luciferase Assay Kit (1000 rxns)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
Secrete-Pair Gaussia Luciferase Assay Kit (100 rxns)
Lenti-Pac™ Lentivirus Concentration Solution (50 ml)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
EndoFectin™ Max transfection reagent (1ml)|Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
T7 endonuclease I assay kit, 200 rxns
Lenti-Pac HIV Expression Packaging Kit (40 reactions)
GeneHero™ mouse ROSA26 safe harbor gene knock-in kit
Biotin Protein Ligase
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Cancer and Neoplasm-associated Antigen Array
Biotin Protein Ligase
Lenti-Pac HIV Expression Packaging Kit (40 reactions)
BlazeTaq™ One-Step SYBR Green RT-qPCR Kit (200 rxn, with ROX)
All-in-One™ qPCR Mix (200 qPCR reactions)
Secrete-Pair Gaussia Luciferase Assay Kit (100 rxns)
Secrete-Pair Gaussia Luciferase Assay Kit (100 rxns)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)
All-in-One™ qPCR Mix (200 qPCR reactions)
EndoFectin™ Max transfection reagent (3ml)
All-in-One™ qPCR Mix (200 qPCR reactions)
Lenti-Pac™ Lentivirus Concentration Solution (50 ml)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)
BlazeTaq™ One-Step SYBR Green RT-qPCR Kit (200 rxn, with ROX)
BlazeTaq™ One-Step SYBR Green RT-qPCR Kit (200 rxn, with ROX)
BlazeTaq™ One-Step SYBR Green RT-qPCR Kit (200 rxn, with ROX)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)|BlazeTaq™ SYBR® Green qPCR mix 2.0 (600 qPCR reactions)|All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (60 RT and 600 qPCR reactions)(Old cat # QP016)
EndoFectin™ Max transfection reagent (1ml)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
EndoFectin™ Lenti transfection reagent (1ml)
EndoFectin™ Max transfection reagent (1ml)
Secrete-Pair Gaussia Luciferase Assay Kit (100 rxns)
Coronavirus infection-associated Autoimmune Antigen Array
EndoFectin™ Lenti transfection reagent (1ml)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
Genome-TALER™ human AAVS1 safe harbor gene knock-in kit (without donor)
All-in-One™ qPCR Mix (200 qPCR reactions)
Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (20 RT reactions)
AAVPrime™ AAV Serotype Testing Kit
Biotin Protein Ligase
All-in-One™ qPCR Mix (600 qPCR reactions)
All-in-one (Cas9 + sgRNA) clone targeting human AAVS1
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
T7 endonuclease I assay kit, 50 rxns
Biotin Protein Ligase
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
T7 endonuclease I assay kit, 50 rxns
Lenti-Pac HIV Expression Packaging Kit (40 reactions)
EndoFectin™ Lenti transfection reagent (1ml)
Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
Secrete-Pair Gaussia Luciferase Assay Kit (100 rxns)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)
EndoFectin™ Max transfection reagent (1ml)
All-in-One™ miRNA qRT-PCR Detection Kit 2.0* (20 RT and 200 qPCR reactions) (Old cat # QP015)
All-in-One™ qPCR Mix (200 qPCR reactions)
EndoFectin™ Max transfection reagent (1ml)
EndoFectin™ Max transfection reagent (1ml)
EndoFectin™ Max transfection reagent (1ml)
Fireflyer luciferase (hLuc) and Renillar luciferase (Rluc) reporter vector 
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
BlazeTaq™ One-Step SYBR Green RT-qPCR Kit (200 rxn, with ROX)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
All-in-One™ qPCR Mix (4000 qPCR reactions)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)
Biotin Protein Ligase
Luc-Pair™ Firefly Luciferase HS Assay Kits (1000rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
All-in-One™ qPCR Mix (4000 qPCR reactions)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
EndoFectin™ Max transfection reagent (3ml)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
Lenti-Pac HIV Expression Packaging Kit (20 reactions)
All-in-One™ qPCR Mix (1000 qPCR reactions)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
All-in-One™ qPCR Mix (600 qPCR reactions)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
Luc-Pair Duo-Luciferase HS Assay Kits (100rxns)
Luc-Pair Luciferase Assay Kits 2.0 (100rxns)
Lenti-Pac HIV qRT-PCR Titration Kit (20 RT reactions, 50 PCR reactions)
T7 endonuclease I assay kit, 50 rxns
Luc-Pair Luciferase Assay Kits 2.0 (300rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
All-in-One™ qPCR Mix (200 qPCR reactions)
Gaussia luciferase (Gluc) and secreted alkaline phosphatase (SEAP) reporter vector|Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
All-in-One™ miRNA Universal Adaptor PCR Primer (50 µM ; 20 µl)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
EndoFectin™ Max transfection reagent (3ml)
Luc-Pair™ Renilla Luciferase HS Assay Kits (1000rxns)
All-in-One™ miRNA Universal Adaptor PCR Primer (50 µM ; 20 µl)
Luc-Pair Luciferase Assay Kits 2.0 (300rxns)
Secrete-Pair Dual Luminescence Assay Kit (1000 rxns)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)|BlazeTaq™ Probe qPCR Mix (without ROX) (600 rxn)
SureScript™ First-Strand cDNA Synthesis Kit for gene qPCR array (60 RT reactions)|BlazeTaq™ Probe qPCR Mix (without ROX) (600 rxn)
EndoFectin™ Lenti transfection reagent (3ml)|BlazeTaq™ One-Step SYBR Green RT-qPCR Kit (1000 rxn, w/o ROX)|Secrete-Pair Dual Luminescence Assay Kit (300 rxns)
All-in-One™ qPCR Mix (4000 qPCR reactions)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
All-in-One™ qPCR Mix (600 qPCR reactions)
Secrete-Pair Dual Luminescence Assay Kit (100 rxns)
Secrete-Pair Gaussia Luciferase Assay Kit (100 rxns)
All-in-One™ qPCR Mix (200 qPCR reactions)
All-in-One™ qPCR Mix (200 qPCR reactions)
Lenti-Pac HIV Expression Packaging Kit (40 reactions)|Lenti-Pac™ Lentivirus Concentration Solution (50 ml)|Lenti-Pac HIV qRT-PCR Titration Kit (20 RT reactions, 50 PCR reactions)
To detect miRNA, total RNA was reverse-transcribed using the All-in-One miRNA First-Strand cDNA Synthesis Kit (QP013, GeneCopoeia).
"""

    products = product_names.split("\n")

    for p in products:
        print(f"Original:   {p}")
        print(f"Normalized: {normalize_for_matching(p)}")