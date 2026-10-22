"""Create a list of SVG sheets used in the online edition."""
import json
import wx


class SvgSheetsListCreator(wx.Frame):
    """Create a list of SVG sheets used in the online edition."""

    def __init__(self, parent, title):
        super().__init__(parent, title=title, size=(850, 650))

        self.data = None

        self.base_path = None
        self.complex_id = None
        self.m_number = None
        self.num_sketch_editions = None
        self.num_text_editions = None
        self.num_work_editions = None
        self.section_id = None
        self.series_id = None

        self.sketch_edition_convolute_textctrls = []
        self.sketch_edition_partials_textctrls = []
        self.text_edition_convolute_textctrls = []
        self.text_edition_partials_textctrls = []
        self.work_edition_convolute_textctrls = []
        self.work_edition_partials_textctrls = []

        self.notebook = wx.Notebook(self)

        self.create_general_tab()

    def create_general_tab(self):
        """Create the general tab."""
        general_panel = wx.Panel(self.notebook)
        self.notebook.AddPage(general_panel, "General")

        general_vbox = wx.BoxSizer(wx.VERTICAL)
        general_grid = wx.FlexGridSizer(4, 2, 10, 10)

        self.series_id_textctrl = self.add_text_input(
            general_panel, general_grid, "Enter series ID:")
        self.section_id_textctrl = self.add_text_input(
            general_panel, general_grid, "Enter section ID:")
        self.complex_id_textctrl = self.add_text_input(
            general_panel, general_grid, "Enter complex ID:")
        self.m_number_textctrl = self.add_text_input(
            general_panel, general_grid, "Enter M number:")

        self.num_text_editions_textctrl = self.add_text_input(
            general_panel, general_grid, "How many text editions are involved?")
        self.num_sketch_editions_textctrl = self.add_text_input(
            general_panel, general_grid, "How many sketch editions are involved?")

        general_vbox.Add(general_grid, flag=wx.EXPAND | wx.ALL, border=10)

        self.add_save_button(general_panel, general_vbox, self.on_general_tab_save)
        self.add_exit_button(general_panel, general_vbox)

        general_panel.SetSizerAndFit(general_vbox)

    def create_edition_tab(self, edition_type):
        """Create an edition tab."""
        edition_vars = self.get_edition_vars(edition_type)

        if edition_vars['num_editions'] == 0:
            return

        edition_panel = wx.Panel(self.notebook)
        self.notebook.AddPage(edition_panel, edition_vars['edition_type_key'])

        edition_vbox = wx.BoxSizer(wx.VERTICAL)
        edition_grid = wx.FlexGridSizer(edition_vars['num_editions'], 2, 10, 10)

        for item_index in range(edition_vars['num_editions']):
            partials_textctrl = self.add_text_input(
                edition_panel, edition_grid, f"How many partials does {
                    edition_vars['edition_type_prefix']}{
                    item_index + 1} have?")
            convolute_textctrl = self.add_text_input(
                edition_panel, edition_grid, f"What is the source siglum for {
                    edition_vars['edition_type_prefix']}{
                    item_index + 1}?")

            edition_vars['partials_textctrls'].append(partials_textctrl)
            edition_vars['convolute_textctrls'].append(convolute_textctrl)

        edition_vbox.Add(edition_grid, 1, wx.EXPAND)

        self.add_save_button(
            edition_panel,
            edition_vbox,
            lambda event: self.on_edition_tab_save(event, edition_type))
        self.add_exit_button(edition_panel, edition_vbox)

        edition_panel.SetSizerAndFit(edition_vbox)

    def add_exit_button(self, panel, vbox):
        """Create the exit button."""
        exit_button = wx.Button(panel, label="Exit")
        exit_button.Bind(wx.EVT_BUTTON, self.on_exit)
        vbox.Add(exit_button,
                 flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM,
                 border=10)

    def add_save_button(self, panel, vbox, save_event_handler):
        """Create the save button."""
        save_button = wx.Button(panel, label="Save")
        save_button.Bind(wx.EVT_BUTTON, save_event_handler)
        vbox.Add(save_button,
                 flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM,
                 border=10)

    def add_text_input(self, panel, container, label_text):
        """Add a text control input with a label to the panel and grid."""
        label = wx.StaticText(panel, label=label_text)
        textctrl = wx.TextCtrl(panel, size=(50, -1))
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(label, flag=wx.RIGHT, border=10)
        hbox.Add(textctrl, proportion=1)
        container.Add(hbox, flag=wx.EXPAND)
        return textctrl

    def get_edition_data(self, edition_type):
        """Get the data for the editions."""
        edition_vars = self.get_edition_vars(edition_type)

        for item_index in range(edition_vars['num_editions']):
            partials_textctrl = edition_vars['partials_textctrls'][item_index]
            convolute_textctrl = edition_vars['convolute_textctrls'][item_index]

            partials = int(partials_textctrl.GetValue())
            convolute = convolute_textctrl.GetValue()

            # Initialize the edition structure
            edition = {
                "id": f"M_{self.m_number}_{edition_vars['edition_type_prefix']}{item_index + 1}",
                "label": f"M {self.m_number} {edition_vars['edition_type_label']}{item_index + 1}",
                "content": []
            }

            # Create the partial items
            for content_index in range(partials):
                partial_edition = '' if partials == 1 else chr(97 + content_index)
                item = {
                    "svg": self.base_path + f"M_{
                        self.m_number}_{
                        edition_vars['edition_type_label'].strip()}{
                        item_index + 1}-{
                        content_index + 1}von{partials}-final.svg",
                    "image": "",
                    "partial": partial_edition,
                    "convolute": convolute}
                edition["content"].append(item)

            self.data["sheets"][edition_vars['edition_type_key']].append(edition)

    def get_edition_vars(self, edition_type):
        """Get the edition variables."""
        edition_map = {
            'sketch': {
                'num_editions': self.num_sketch_editions,
                'partials_textctrls': self.sketch_edition_partials_textctrls,
                'convolute_textctrls': self.sketch_edition_convolute_textctrls,
                'edition_type_key': "sketchEditions",
                'edition_type_prefix': "Sk",
                'edition_type_label': "Sk"
            },
            'text': {
                'num_editions': self.num_text_editions,
                'partials_textctrls': self.text_edition_partials_textctrls,
                'convolute_textctrls': self.text_edition_convolute_textctrls,
                'edition_type_key': "textEditions",
                'edition_type_prefix': "TF",
                'edition_type_label': "Textfassung "
            },
            'work': {
                'num_editions': self.num_work_editions,
                'partials_textctrls': self.work_edition_partials_textctrls,
                'convolute_textctrls': self.work_edition_convolute_textctrls,
                'edition_type_key': "workEditions",
                'edition_type_prefix': "WF",
                'edition_type_label': "Werkfassung "
            }
        }

        return edition_map.get(edition_type)

    def get_general_data(self):
        """Initialize the data structure for the sheets."""
        self.series_id = int(self.series_id_textctrl.GetValue())
        self.section_id = self.section_id_textctrl.GetValue()
        self.complex_id = self.complex_id_textctrl.GetValue()
        self.m_number = int(self.m_number_textctrl.GetValue())
        self.num_text_editions = int(self.num_text_editions_textctrl.GetValue())
        self.num_sketch_editions = int(self.num_sketch_editions_textctrl.GetValue())

        self.base_path = "assets/img/edition/series/" + str(self.series_id) + \
            "/section/" + str(self.section_id) + "/" + str(self.complex_id) + "/"

        self.data = {
            "sheets": {
                "workEditions": [],
                "textEditions": [],
                "sketchEditions": []
            }
        }

        return self.data

    def on_exit(self, _event):
        """Close the application."""
        self.Close()
        self.Destroy()

    def on_general_tab_save(self, _event):
        """Get the general data and write it to the JSON file."""
        self.get_general_data()

        if self.num_work_editions is not None and self.num_work_editions > 0:
            self.create_edition_tab('work')

        if self.num_text_editions is not None and self.num_text_editions > 0:
            self.create_edition_tab('text')

        if self.num_sketch_editions is not None and self.num_sketch_editions > 0:
            self.create_edition_tab('sketch')

        print('Saving general data ...')

        self.write_data()

    def on_edition_tab_save(self, _event, edition_type):
        """Get the edition data and write it to the JSON file."""
        self.get_edition_data(edition_type)

        print(f'Saving {edition_type} edition data ...')

        self.write_data()

    def write_data(self):
        """Write the data to the JSON file."""
        if self.data is not None:
            json_object = json.dumps(self.data, indent=4, ensure_ascii=False).encode(
                'utf8').decode('utf8')

            target_file_name = "svg-sheets.json"
            try:
                with open(target_file_name, "w", encoding='utf-8') as target_file:
                    target_file.write(json_object)
                print(f"Data written to {target_file_name} successfully.")
            except IOError:
                print(f"Error writing data to {target_file_name}.")


def main():
    """Run the application."""
    app = wx.App()
    frame = SvgSheetsListCreator(None, 'SVG Sheets List Creator')
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
