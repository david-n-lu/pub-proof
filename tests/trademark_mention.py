import csv
import json
from math import prod
from matching.product_map import build_alias_map, build_product_map, build_shortened_sku_map
from matching.sku_matcher import find_sku
from matching.mention_extractor import extract_product_mention, get_keyword_indexes, get_phrases, extract_best_product_mention, get_best_phrases, score_phrase
from matching.normalization import normalize_for_matching


def run_pipeline(sentences, product_map_path: str, output_csv_path: str):
    product_map = build_product_map(product_map_path)
    print("Built product map")

    alias_map = build_alias_map(product_map)
    print("Build alias map")

    shortened_sku_map = build_shortened_sku_map(product_map)
    print("Built shortened SKU map")

    for sentence in sentences.split("\n"):

        print(f"sentence: {sentence}")

        phrases = get_best_phrases(sentence, alias_map, penalty=5.0, n = None)

        min_words = 2
        phrases = [phrase for phrase in phrases if len(phrase.split()) > 1]

        print(f"Phrases: {phrases}")
        print("")
        
        skus = []
        products = []
        scores = []
        corresponding_phrases = []
        min_score = 0
        for phrase in phrases:

            phrase_skus = extract_best_product_mention(phrase, alias_map, n = 10)
            for phrase_sku in phrase_skus:
                phrase_product = product_map.get(phrase_sku,{}).get("product_name","")
                score = score_phrase(phrase, phrase_product)

                if score > min_score:
                    skus.append(phrase_sku)
                    products.append(phrase_product)
                    scores.append(str(score))
                    corresponding_phrases.append(phrase)

        top_n = 10
        
        # get indexes of top_n scores
        top_score_indexes = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]

        skus = [skus[i] for i in top_score_indexes]
        products = [products[i] for i in top_score_indexes]
        scores = [scores[i] for i in top_score_indexes]
        corresponding_phrases = [corresponding_phrases[i] for i in top_score_indexes]

        for i in range(len(skus)):
            print(f"phrase: {corresponding_phrases[i]}\tproduct: {products[i]}\tsku: {skus[i]}\tscore: {scores[i]}")

        print("-" * 60)


if __name__ == "__main__":
    manufacturer = "GeneCopoeia"
    sentence_corpus_path = "tests/data/genecopoeia_sentences_1000.jsonl"
    product_map_path = "data/raw_products"
    output_csv_path = "tests/data/matcher_results_without_sku_trademark_1000.csv"


    # sentence = "qRT‒PCR assays were conducted on a CFX96 Real-Time PCR System (Bio-Rad, USA) using BlazeTaq™ SYBR® Green qPCR Mix 2.0 (GeneCopoeia)."
    # test_sentence(manufacturer = manufacturer, sentence = sentence, product_map_path = product_map_path)


    sentences = """cDNA synthesis from FFPE tissue sections For cDNA synthesis and subsequent quantitative reverse transcription polymerase chain reaction (RT‑qPCR) analysis, the All-in-one™ kit 2.0 (GeneCopoeia, Rockville, MD, USA) was utilized.
RT‑qPCR from FFPE tissue sections Following cDNA synthesis, RT-qPCR was performed using the All-in-one™ kit 2.0 (GeneCopoeia).
The All-in-one™ kit 2.0 (GeneCopoeia) was used to analyze miRNA expression in platelets, following the same approach as for patient tissues.
RT-qPCR from human platelets RT-qPCR was performed for miRNA expression analysis in platelets using the All-in-one™ kit 2.0 (GeneCopoeia).
ast carcinoma EMT6-wildtype cell line (EMT6-WT; NCI DCTD Tumor Repository, RRID:CVCL1923) using Lentifect™ lentiviral particles harboring the Homo sapiens TACSTD2 gene and a puromycin-resistant gene (GeneCopoeia, LPP-G0457).
RT-qPCR RNA extraction was performed with TriQuick Reagent (Solarbio, Beijing), and cDNA was synthesized using the SureScript RTase kit (GeneCopoeia, USA).
The gene expression of 31 key genes involved in intestinal inflammatory response and integrity was assessed using the ExProfile™ Gene qPCR Array (GeneCopoeia, Rockville, MD, USA), a customized 96-well plate ( Table S1—Supplementary File ).
f mitochondrial dysfunction in CVD Relative quantification of mitomiRs via RT-qPCR The experiment was conducted by carrying out RT-qPCR in triplicates using the “All-in-one miRNA qPCR detection kit” (Genecopoeia, USA), which contains SYBR ® Green.
First-strand cDNA was synthesised from 1 μg of RNA using 5 × All-In-One RT MasterMix (GeneCopoeia) and incubated at 37 °C for 15 minutes and 60 °C for 10 minutes.
Briefly, 293 T cells were transfected with these plasmids along with packaging plasmids using the Lenti-Pac™ Lentivirus Expression Packaging Kit (GeneCopoeia, USA) according to the manufacturer’s instructions.
The expression levels of miRNAs were measured by employing a specific forward primer for the mature miRNA sequence, the universal adaptor reverse primer (GeneCopoeia), and the SYBR green detection.
Viral Transduction Transduction-ready Lentiviral particles (Lentifect TM ) were custom-made by Genecopoeia inc. (Rockville, MD, USA) for overexpression of mouse Steap4 .
say, the fragment (−3000 bp to +1000 bp) of human PHGDH, PSAT1, PSPH and SLC1A4 promoters, containing ΔNp63α putative binding sites, was inserted into the Gluc-On promoter reporter vector (pEZX-PG04, GeneCopoeia, Guangzhou, China) and designated as PHGDH-Gluc, PSAT1-Gluc, PSPH-Gluc, SLC1A4-Gluc, respectively.
cDNA was generated via the PrimeScript™ RT Reagent Kit (GeneCopoeia, China), and RT-qPCR was conducted via SYBR Green Master Mix (GeneCopoeia) on a QuantStudio™ 5 Real-Time PCR System (Thermo Fisher Scientific, USA).
For miRNA analysis, a First-strand cDNA synthesis kit (GeneCopoeia) and the All-in-one miRNA qRT-PCR Detection kit (GeneCopoeia) were used according to the manufacturer’s instructions, as described in previous studies.
Then, miRNA expression levels were analyzed by RT‒qPCR using an All-in-One™ miRNA qPCR Kit (GeneCopoeia, USA) and a 7900HT Fast Real-Time PCR System (ABI, USA).
miRNA was analyzed using All‐in‐One miRNA First‐Strand cDNA synthesis kit and miRNA qPCR kit (GeneCopoeia, United States).
Validated All-in-One™ qPCR primers for Kaiso, PXR, NF-κB, HER2, ABCB1 (P-gp), HIF1A, and ACTB (β-actin) were obtained from GeneCopoeia and confirmed for specificity and efficiency.
To detect miRNAs, Dnase‐treated total RNA was reverse transcribed to cDNA using the All‐in‐One miRNA RT‐qPCR Detection Kit (GeneCopoeia, Rockville, MD).
Supernatant containing viral particles was harvested at 48 and 72 hours, combined with Lenti-Pac (GeneCopoeia), and incubated at 4°C overnight.
Dormant SACC cells were transfected with pEZ-Lv201- PLIN2 wild-type plasmid and pEZ-Lv201-PLIN2 plasmid using EndoFectin Max (GeneCopoeia).
irus MD Anderson Functional Genomics Core Cat# OHS5832 pLOC-hFoxO3a lentivirus MD Anderson Functional Genomics Core Cat# PLOHS_ccsbBEn_00577 Firefly Luciferase Lentifect Purified Lentiviral Particles GeneCopoeia Cat# #LPP-FLUC-Lv105-100 Mouse: BLAB/c nude mice Charles River RRID:IMSR_RJ:BALB-C-NUDE Oligonucleotides ALPP taqman probe Thermo Fisher Scientific Cat# Hs03046558_s1 RT-qPCR primers for ALPP promote
For the promoter assay, a fragment (–3000 bp to +1000 bp) of the human NFE2L2 gene containing putative SOX2 binding sites was inserted into the Gluc-On promoter reporter vector (pEZX-PG04; GeneCopoeia, Guangzhou, China) and designated NFE2L2-Gluc.
qPCR was conducted using the All-in-One qPCR Mix Kit (Genecopoeia) on the Mx3000P system (Agilent Technologies) applying the following protocol: 95 °C for 5 min, followed by 39 cycles of 95 °C for 15 s and 60 °C for 1 min.
Real-time PCR detection was performed using SYBR Green reagents (GeneCopoeia) on an RT-PCR instrument (QuantStudio 6 Flex, Life Technologies) with 40 amplification cycles.
rd, UK) and All-in-One qPCR primers for Usp7 (MQP023609) 5′-CTCCCAGACCATGGGGTTTC-3′ and 5′-ATCTAACATTGCAGGCCGCT-3′ and Senp3 (MQP106473) 5′-CCATCAGGGCTGGAAAGGTT-3′ and 5′-CTGGGTGAAGCTGAATGGCT-3′ from GeneCopoeia (Rockville, MD, USA).
miRNA expression was assessed using the All-in-One™ miRNA RT-PCR Kit (GeneCopoeia, catalog no. QP010, USA) on a Bio-Rad CFX96 system (Hercules, CA), normalized to Rno-U6.
Changes in KRAS–firefly luciferase expression in response to siRNA treatment were evaluated with the Luc-Pair Duo-Luciferase HT Assay Kit using the manufacturer’s protocol (Genecopoeia).
Quantitative real-time polymerase chain reaction (qRT-PCR) was subsequently performed using SYBR Green RT-qPCR Master Mix (GeneCopoeia) to analyze gene expression levels.
QRT‐PCR was conducted using the EnTurbo™ SYBR Green Polymerase Chain Reaction (PCR) SuperMix (GeneCopoeia) on a QuantStudio 6 Flex PCR system (Thermo Fisher Scientific).
SARS-CoV-2 pseudovirus: Lentifect SARS-CoV-2 Spike is a type of pseudotyped lentivirus that utilizes the vs.V vector as its backbone (GeneCopoeia, USA).
Lentivirus was produced by co-transfecting human embryonic kidney 293 T cells with either SNHG3 WT , SNHG3 ED , or an empty vector, using the Lenti-Pac TM HIV (Genecopoeia, Rockville, MD).
The cDNA was used as a template to perform qRT-PCR using the All-in-One qRT-PCR Mix (GeneCopoeia).
Total RNA equivalents (2 ng) were amplified with PowerUp SYBR Green (#A25742, Thermo Fisher Scientific, MA, USA) using commercial miRNA-specific primers (GeneCopoeia).
Quantitative real-time polymerase chain reaction was performed with all-in-one quantitative real-time polymerase chain reaction Mix Kit (GeneCopoeia) in LightCycler 480 (Roche Life Science, Switzerland).
Quantitative real‐time PCR was performed using the All‐in‐One SYBR Green system q‐PCR Mix (GeneCopoeia, USA) on a 96‐well real‐time PCR device (LightCycler® 96 Roche, Swiss).
MiRNAs were reverse transcribed into cDNAs via the All‐in‐One™ miRNA First‐Strand cDNA Synthesis Kit (GeneCopoeia, China), whereas mRNAs were reverse transcribed into cDNAs via the HiScript III All‐in‐one RT SuperMix Perfect for real‐time quantitative polymerase chain reaction (qPCR) (Vazyme Biotech, China).
cDNA was synthesized using the GoScript RT System (Promega, USA) and the All-in-One miRNA Reverse Transcription Kit (GeneCopoeia, USA).
RT-qPCR analysis employed GoTaq qPCR Master Mix (Promega, USA) and SYBR Green Human miRNA Assay Kit (GeneCopoeia, USA).
To trace the EVs released from implemented NSCs in vivo, CD63‐copGFP‐Flag Lentifect (GeneCopoeia) was transfected into primary cultivated NSCs following the user's manual.
ExProfile™ Gene qPCR Array (GeneCopoeia, Rockville, MD, USA), a customized 96-well plate array, was used to study the gene expression of 40 key genes involved in the intestinal inflammatory response (Supplementary Table S1) .
Microarray analysis Total RNA from CRC patient-derived exosomes was extracted using the All-in-One microRNA extraction kit (GeneCopoeia, Rockville, MD, United States) per the manufacturer’s instructions.
Real-time PCR was performed utilizing Hieff qPCR SYBR Green Master Mix (High ROX Plus) (Yeasen, China) and All-in-One™ miRNA Universal Adaptor PCR Primer (GeneCopoeia, USA).
SYBR Green Master Mix (GeneCopoeia, inc.) was used for qPCR.
We then performed qRT-PCR with the 2× All-in-One™ qPCR mix (Genecopoeia, Guangzhou, China).
Generation of CRISPR knockout cell lines All-in-one CRISPR/Cas9 clones targeting Snord67 and Snord111 were purchased from Genecopoeia (vector pCRISPR-CG02).
Quantitative real-time polymerase chain reaction (qRT-PCR) The expression of circulating exomiRNAs was measured by qRT‒PCR using the All-in-One™ miRNA qPCR Kit (GeneCopoeia, QP010, USA), as described previously [ 21 ].
For promoter activity assays, the fragment (−3000 bp to +1000) of the human ΔNp63 promoter was cloned into the Gluc-On promoter reporter vector (pEZX-PG04, GeneCopoeia, Guangzhou, China), referred to as ΔNp63-Gluc.
CRISPR construct The custom CRISPR gene editing constructs were obtained from Genecopoeia as an all-in-one CRISPR clone with a single guide RNA (sgRNA) targeting all variants for CACNA1E (target Site: CCTCAGGATGGCTCGCTTCG), NTSR2 (target site: CCGCGCTCTACGCACTCATC), TRPV1 (target site: CC
The Luc-Pair miR Luciferase assay kit (GeneCopoeia) was used to measure firefly and Renilla luciferase activity according to the manufacturer’s protocol.
n and amplification through the All-in-One ™ miRNA quantitative real-time PCR (qPCR) Detection Kit and the TaqMan MicroRNA Assay (Applied Biosystems, CA, United States), as suggested by the provider (GeneCopoeia inc., MD, United States).
After 24 h, luciferase activity was measured using Luc-Pair ™ Duo-Luciferase Assay Kit 2.0 (#217LF002, Genecopoeia), following the manufacturer’s instructions, and luminescence was detected in a luminescence microplate reader (LUMIstar Omega, BMG Labtech, Ortenberg, Germany).
OVCA432 and OVCAR-8 cells, which have been shown to be representative models of HGSC ( 13 ), were transfected with Firefly luciferase Lentifect purified lentiviral particles (GeneCopoeia) according to the manufacturer’s standard protocol to generate luciferase-labeled cells (OVCA432-luc and OVCAR-8-luc) for use with the IVIS optical imaging system (PerkinElmer).
Real-time fluorescence quantitative PCR (RT-qPCR) analysis was performed using the All-in-One qPCRMix (GeneCopoeia).
The cDNA was amplified using the TaKaRa reverse transcription reagents and qRT‐PCR analysis was performed using All‐in‐One qPCR Mix Kit (GeneCopoeia, China) on ABI Quant Studio 3 (Applied Biosystems, Waltham, MA).
The acquired total RNA (1 μg) was taken and reverse transcribed into cDNA using All-in-One TM miRNA First-Strand cDNA Synthesis Kit (GeneCopoeia, Guangzhou, China), and then was used to perform qRT-PCR using All-in-One miRNA qRT-PCR Detection Kit (GeneCopoeia).
The next day, the concentration of firefly Luciferase was measured using the Luc-Pair Duo-Luciferase Assay Kit 2.0 (Genecopoeia).
Each reaction system imported a forward primer (All-in-One™ miRNA qPCR validated primers, GeneCopoeia) for the mature miRNA sequence and a universal adaptor reverse primer.
For PLCη2 overexpression and knockdown, we used an OmicsLink open reading frame expression plasmid (pReceiver-PLCη2 expression vector; GeneCopoeia, EX-H0612-M61) and an OmicsLink short hairpin RNA (shRNA) clone (psi-H1-PLCη2 shRNA; GeneCopoei, HSH023033).
PC-3 cells expressing luciferase (PC-3-luciferase) were generated using Firefly Luciferase Lentifect Purified Lentiviral Particles (GeneCopoeia).
"""

    run_pipeline(sentences,
                 product_map_path=product_map_path,
                 output_csv_path=output_csv_path)