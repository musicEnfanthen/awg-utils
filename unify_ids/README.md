# HOW TO ... unify IDs in SVG and JSON files?

## WHY?

SVG files generated from music notation and/or image software may contain auto-generated, non-descriptive group IDs (e.g. `g6407`). To make those IDs consistent and meaningful across the online edition, they need to be replaced with standardised IDs that follow the AWG naming convention. The two Python scripts automate this process:

* `unify_tkk_ids.py` — replaces SVG group IDs for textcritical comment (TKK) elements with IDs of the form `awg-tkk-<entryId>-001`, where `<entryId>` is lowercased and the final segment is a zero-padded counter to support multiple comments per entry.
* `unify_link_box_ids.py` — replaces SVG group IDs for link-box elements with IDs of the form `awg-lb-<entryId>-to-<sheetId>`. In the generated ID, the relevant parts are lowercased. Additionally, if the SVG filename contains an `-NvonM-` pattern, the script may append a per-SVG suffix to `<entryId>` (for example, resulting in IDs ending in `...sk1a...` or `...sk1b...`).
* `unify_kv_ids.py` — assigns sequential svgGroupIds to blockComment entries in a source description JSON file, using IDs of the form `awg-kv-<complexId><corrSuffix>-001`. No SVG files are modified; only the JSON file is updated.

`unify_tkk_ids.py` and `unify_link_box_ids.py` update the IDs in the JSON textcritics file and in the corresponding SVG files at the same time. `unify_kv_ids.py` only updates the JSON file.

## HOW?

> [!NOTE]
> These scripts use the latest Python version (3.13 for now). Make sure to have Python installed on your system, or get it from here: [https://www.python.org/downloads/](https://www.python.org/downloads/)

### Preparation

* Make sure that you have a JSON textcritics file and a folder containing the corresponding SVG files ready.
* Make sure that you have created a fork from this GitHub repository `awg-utils` and you have a local copy of this fork on your machine.
* In your file explorer, navigate to your local folder `awg-utils`, right-click on it, and open it with **VSCode** editor.
* Open a new terminal in **VSCode** editor (preferably **Git Bash**, following paths and directions are using Git Bash syntax).
* In the terminal, change directory to the subfolder `unify_ids` by typing: `cd unify_ids` (it should be sufficient to type `cd un` + `TAB` key, the console autocompletes the name on its own). This subfolder is where the unification scripts live.
* In the terminal, create and activate a virtual environment (see [Virtual Environments](../README.md#virtual-environments) in the main README for details):
  ```bash
  python -m venv .venv   # skip if already created
  source .venv/Scripts/activate
  ```
* In the terminal, type `pip install -r requirements.txt --require-hashes` to install the latest library versions with verified hashes.

Now you're good to run the scripts.

### Unification (Python scripts)

* Open the script you want to run (`unify_tkk_ids.py`, `unify_link_box_ids.py`, or `unify_kv_ids.py`) in **VSCode**.
* In the `main()` function at the bottom of the file, fill in the configuration variables:
  * For `unify_tkk_ids.py` and `unify_link_box_ids.py`: set `json_path` and `svg_folder`.
  * For `unify_kv_ids.py`: set `json_path` and `complex_id` (no SVG folder needed).
* In the terminal, type `python unify_tkk_ids.py`, `python unify_link_box_ids.py`, or `python unify_kv_ids.py` to run the chosen script.

> [!TIP]
> If your files are in the same directory as the script, use `./` at the start of the path.

#### Examples of path configuration in the script:

```python
# External directory:
json_path = "/c/Users/<USERNAME>/AWG/textcritics.json"
svg_folder = "/c/Users/<USERNAME>/AWG/svg/"

# Same directory:
json_path = "./textcritics.json"
svg_folder = "./svg/"
```

### Unification (Jupyter Notebook)

As an alternative to editing the scripts directly, you can use the interactive Jupyter Notebook `unify_ids.ipynb`, which guides you through the process with input prompts.

* Install the additional notebook packages (the base packages are already installed via [Preparation](#preparation)):
  ```bash
  pip install --require-hashes -r requirements-notebook.txt
  ```
* Open `unify_ids.ipynb` in **VSCode** and select the `.venv` kernel.
* Run the notebook cells top-to-bottom and enter the paths when prompted.

## Credits

The scripts in this folder were mainly developed by [@lili041](https://github.com/lili041) during an internship at the Anton Webern Gesamtausgabe (AWG), with support and additional contributions by [@musicEnfanthen](https://github.com/musicEnfanthen).
