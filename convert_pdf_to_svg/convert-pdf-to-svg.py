'''
The following code will ask for two directories on your local drive:

First, a directory containing one or several PDF-files.
(The PDFs will ideally consist of one single page. 
If there are more pages, only the first one will be converted by the code.)

Second, the directory containing 'inkscape.exe'.

After these inputs the code will convert all PDF-files (or the first page of it) 
within the first directory to SVG-files using the Inkscape software 
without opening its GUI.
The new SVG-files will be saved in the same directory as the PDF-files.
'''

# imports
import logging
import subprocess
from pathlib import Path


def convert_pdfs_to_svgs(pdf_dir: str, inkscape_dir: str):
    """
    Converts all PDF files in the specified directory to SVG files using Inkscape.

    Args:
        pdf_dir (str): The directory containing the PDF files.
        inkscape_dir (str): The directory containing the Inkscape executable.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    pdf_dir = Path(pdf_dir).resolve()
    inkscape_dir = Path(inkscape_dir).resolve()

    logging.info('Converting PDFs to SVGs in pdfdir: %s', pdf_dir)

    for pdf_file in pdf_dir.iterdir():
        if not pdf_file.is_file() or not pdf_file.suffix == '.pdf':
            continue

        logging.info('Converting %s to SVG...', pdf_file)

        svg_file = pdf_file.with_suffix('.svg')
        inkscape_path = inkscape_dir / 'inkscape.com'

        logging.info('inkscape_path: %s', inkscape_path)
        logging.info('pdf_file: %s', pdf_file)

        try:
            subprocess.run(['pdftocairo.exe', '-svg',
                           str(pdf_file), str(svg_file)], check=True)
        except subprocess.CalledProcessError as error:
            logging.error('Error converting %s: %s', pdf_file, error)
        except subprocess.TimeoutExpired:
            logging.error('Timeout expired while converting %s', pdf_file)
        except Exception as error:
            logging.error('Error converting %s: %s', pdf_file, error)


if __name__ == '__main__':
    # input('Enter the directory containing the PDF files: ')
    PDF_DIRECTORY = '.'
    # input('Enter the directory containing the Inkscape executable: ')
    INKSCAPE_DIRECTORY = r'C:\Program Files\Inkscape\bin'
    convert_pdfs_to_svgs(PDF_DIRECTORY, INKSCAPE_DIRECTORY)


# C:\Users\musicEnfanthen\Desktop\AWG\PDF2SVG
# C:\Program Files\Inkscape\bin
# /c/Program\ Files/Inkscape/bin/inkscape.com ./single.pdf --actions="export-filename:single.svg;export-plain-svg;export-do"
# /c/Program\ Files/Inkscape/bin/inkscape.com ./single.pdf --export-plain-svg single.svg
# export-text-to-path


# https://inkscape.org/learn/faq/#how-to-use-inkscape-from-the-command-line


# https://inkscape.org/forums/beyond/cli-pdf-import-combined-with-actions/
# inkscape --pdf-poppler --pages=1 --export-plain-svg --export-text-to-path --export-filename tmp2.svg tmp.pdf

# /c/Program\ Files/Inkscape/bin/inkscape.com --export-type=svg --pdf-font-strategy=keep --pages=all single.pdf
