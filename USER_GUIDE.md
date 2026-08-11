# BioEvidence Finder - User Guide

## 1. Overview

BioEvidence Finder helps biotech companies find their product mentioned in scientific publications and creates citations mapping products to publications.

This application gets publications, sentences, and product mentions of a specific biotech company. When a product catalog is imported, it allows users to generate automatic citations from catalog numbers or manually annotate sentences without catalog numbers. To help with annotation, this application also uses the product catalog to generate automatic product matches that the user accepts or corrects.

This application was specifically designed for GeneCopoeia. If you want to generate citations for a different biotech company, you can find my code here: `https://github.com/david-n-lu/pub-proof`

### Pipeline Overview:

`Create Project:` Choose file location and biotech company  <br>
`Download Publications:` Get publications that mention the manufacturer from Europe PMC <br>
`Extract Relevant Sentences:` Get sentences that include the manufacturer among the downloaded publications <br>
`Import Product Catalog:` Import product catalog with catalog numbers (HAS TO BE UNIQUE), product names, and product descriptions   <br>
`Find and Generate SKU Mentions:` Search for surefire catalog numbers in each sentence and generate quick citations     <br>
`Annotate Results:` Manually annotate each sentence with the help of automatically generated results and a manual product search    <br>
`Generate Annotation Results:` Generate citations from the manually annotated results   <br>



## 2. Getting Started and Project Setup

Look into the `dist/` folder until you find `launcher.exe` and click on the application to start.

The Launcher window will ask you to create a new project or open an existing project.

### Creating a new project

1. Choose a working directory. This is where the project configuration, user-imported, and application-generated files will be stored
2. Enter a manufacturer name. This is the EXACT name that the application will use to find publications in Europe PMC and find relevant sentences. Any typo will GREATLY HINDER the number of search results.

The project folder will be named after the manufacturer name. You can name the folder different after the initial setup since the manufacturer name will be saved in the project configuration file.

### Opening an existing project
1. The app automatically saves your last opened project and if this is the project you want to work on, you can just press `enter` right after opening `launcher.exe` to open that project.
2. If you want to work on a different project, you can browse a different directory. Make sure you choose a directory that follows the folder format of a new project and contains the `project.json` configuration file.

### Project folder structure
```
Project/
├── publications/
├── sentences/
├── products/
├── citations/
├── annotations/
├── cache/
└── project.json
```

- `publications/` is where all publications mentioning the manufacturer are stored.
- `sentences/` is where all sentences containing the manufacturer are stored.
- `products/` is where all the user imported .csv product files are copied and stored.
- `citations/` is where all the automatic SKU and manual annotation citations will be stored.
- `annotations/` is where all the user's manual annotations will be stored, along with the automatic matcher results.
- `cache/` is where the product index is created from the .csv files in `products/`. This product index cache is stored for quickly loading in the products and finding product mentions.
- `project.json` is the configuration file, which contains relevant metadata for finding product mentions and generating citations. It contains the manufacturer name, the three .csv columns used to create the product index, and automatically found trademark names for more accurate string matching.



## 3. Publication Search and Download

This stage searchs Europe PMC with the manufacturer as the query and retrieves metadata from all the filtered publications.

While this stage is relatively quick, there is checkpointing that allows you to continue where you started in case the server timesout.

All publication metadata is stored in `publications/MANUFACTURER_publications.jsonl` by default, where MANUFACTURER is replaced with what is in the configuration file `project.json`.



## 4. Sentence Search and Download

This stage retrieves the full text (if it exists) for each publication in `publications/MANUFACTURER_publications.jsonl` and extracts the sentences containing the manufacturer.

Since retrieving full texts takes time, retrieving all relevant sentences can take a **couple of hours**. In case the server times out while retriving sentences, there is checkpointing that allows you to continue where you started.

All manufacturer sentences are stored in `sentences/MANUFACTURER_sentences.jsonl` by default, where MANUFACTURER is replaced with what is in the configuration file `project.json`.



## 5. Product Import

To generate the citations, the applications needs .csv files of a product catalog (the application handles multiple .csv files).

Make sure each .csv file contains columns representing:
```
1. Unique product identifier (SKU)
2. Product name
3. Description
```

The description helps differentiate poor, ambiguous product names. If all your product names are unique, the description column will not be used.

The product import section will ask you to import .csv files of your product catalog. Then click **"Choose Columns"** to choose the columns to represent the SKU, Product Name, and Description. Finally, click **"Create Product Index"**, which generates a data structure used for finding product mentions and generating citations.

The product index is stored as `cache/product_index.msgpack` by default.


## 6. Annotating Results

If you want to manually find product mentions in each sentence, you can use the annotator UI window.

1. **Before you start annotating, generate all the automatic matches.** Matching follows exact catalog number matching, gene product matching, and general string matching. Since publications cite products in various ways and sometimes cite incorrectly, these results are not the most accurate. However, they do aid in with annotating. Generating all the automatic matches takes **several minutes** and results are stored in `annotations/MANUFACTURER_auto_results.json` by default, where MANUFACTURER is replaced with what is in the configuration file `project.json`.

2. If the automatic results for a particular sentence are incorrect, you can manually search for a product in the **"Manual Product Search"** section, which can search through all rows and columns in your imported .csv files (not just the product index).

3. **Click on the checkmark** besides map to validate the right product mentions for a particular sentence, and **click "Save Annotation"** to save those correct mentions (if any) and move on to the next sentence. Annotations are saved in `annotations/MANUFACTURER_annotations.json` by default, where MANUFACTURER is replaced with what is in the configuration file `project.json`.

4. If you are unsure about the product mentions for a sentence, it is recommended you **do NOT click "Save Annotations"** and instead click **"Next Sentence"** as coming back to that sentence is easier by clicking **"Search Sentence"** and then **"Next Unannotated"**.

5. If you want to come back to where you last annotated later, you can find your last annotated sentence by clicking **"Search Sentence"** and then **"Last Annotated"**.

6. In the `dist/` folder, you can find a .csv of a list of genes in `launcher/_internal/data/genes.csv`. These are a list of genes GeneCopoeia provided via their product catalogs. If you want to add more genes to improve the automatic gene product matching, you can update or replace this file. **Make sure** you follow its format with the gene name column and the unique accession number column as this applications removes duplicate rows.

7. In the `dist/` folder, there is also a .json file mapping certain keywords with gene product names in `launcher/_internal/data/gene_product_map.json`. The automatcher will perform gene matching on any product name that contains the names in this file. If you want to add more gene product names in order to use this special gene matching rather than general string matching, you can update or replace this file. **Make sure** you follow its format as a .json dictionary of string keywords mapping to lists of gene product names.


## 7. Generating Citation Results

There are two types of citation results:
```
1. Quick SKU Citations: Generated from exact catalog number matching and skips annotations entirely.
2. Annotation Citations: Generated from manual annotations.
```

You can generate the Quick SKU Citations directly after importing your product catalog.

The Annotation Citations are generated directly from `annotations/MANUFACTURER_annotations.json` by default, where MANUFACTURER is replaced with what is in the configuration file `project.json`.

Both types of citations are stored as `citations/MANUFACTURER_sku_citations` and `citations/MANUFACTURER_annotation_citations` where MANUFACTURER is replaced with what is in the configuration file `project.json`.



## 8. Troubleshooting

### WINDOWS 11: If at any point the app breaks, like the annotator window does not open or an error occurs, you will have to open task manager and kill the process called "launcher". You can verify it is the right process by clicking on it and seeing window names like "BioEvidence Launcher" or "Product Annotator".



## 9. Limitations

This application was specifically designed for GeneCopoeia biotech products. Specifically, how product names are shortened and how citations are formatted are hard coded into the application. If you want to generate citations for a different biotech company, you can find my code here: `https://github.com/david-n-lu/pub-proof`

Because publications cite products in various ways, usually leave out catalog numbers, and are usually ambiguous (especially the gene products), the automatic matcher results are usually not that accurate since performs pure string matching. This means most sentences require manual annotation to find the correct product mentions, which can be very tedious especially for poorly cited products.