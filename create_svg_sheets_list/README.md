# SVG Sheets List Creator

This Python project is a GUI application for creating a list of SVG sheets used in an online edition. The application is built using the wxPython library, which is a Python wrapper for the wxWidgets C++ library.

## Features

- Create a list of SVG sheets used in the online edition.
- The application allows to enter details about SVG sheets such as series ID, section ID, complex ID, M number, and the number of text, sketch, and work editions involved.
- Dynamically creates tabs for each edition type (text, sketch, work) based on the number of editions entered by the user.
- Allows users to enter details for each edition such as the number of partials and the source siglum.
- Saves the entered data in a structured format to a JSON file named `svg-sheets.json`.

## Requirements
- Python 3
- wxPython

## Uage

1. Clone the repository.
2. Change directory into `./create_svg_sheets_list` folder.
3. Install the requirements using pip:

```python
pip install -r requirements.txt --require-hashes
```

To run the application, you need to have Python and wxPython installed. Then, you can run the script using Python:

```python
python create_svg_sheets_list.py
```

4. Enter the required details in the GUI and click on the "Save" button to save the data to the JSON file.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT

