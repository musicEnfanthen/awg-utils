"""
Utility functions for the conversion of source descriptions from Word to JSON.

This module should not be run directly. Instead, run the `convert_source_description.py` module.
"""

import copy

from bs4 import BeautifulSoup

from typed_classes import (SourceList, TextCritics)
from default_objects import (defaultSourceList, defaultTextcriticsList,
                             defaultTextcritics, defaultTextcriticalComment)
from utils_helper import ConversionUtilsHelper

############################################
# Public class: ConversionUtils
############################################


class ConversionUtils:
    """A class that contains utility functions for the conversion of source descriptions
        from Word to JSON."""

    utils_helper = ConversionUtilsHelper()

    ############################################
    # Public class function: create_source_list
    ############################################
    def create_source_list(self, soup: BeautifulSoup) -> SourceList:
        """
        Creates a list of source descriptions based on the given soup elements.

        Args:
            soup (BeautifulSoup): A BeautifulSoup object representing the document.

        Returns:
            A SourceList object containing a list of SourceDescription objects.
        """
        source_list = copy.deepcopy(defaultSourceList)
        sources = source_list['sources']

        # Find all p tags in soup
        paras = soup.find_all('p')

        # Find all siglum indices
        siglum_indices = self.utils_helper.find_siglum_indices(paras)

        # Iterate over siglum ranges and create source descriptions
        for i, current_siglum_index in enumerate(siglum_indices):
            next_siglum_index = next(
                (siglum_indices[i + 1] for i in range(i, len(siglum_indices) - 1)), len(paras))

            if current_siglum_index < next_siglum_index:
                filtered_paras = paras[current_siglum_index:next_siglum_index]

                source_description = self.utils_helper.create_source_description(filtered_paras)
                source_id = source_description['id']

                try:
                    next(
                        source for source in sources if source['id'] == source_id)
                    print(
                        f"Duplication: Source description for {source_id} included."
                        f"Please check the source file.")
                except StopIteration:
                    print(
                        f"Appending source description for {source_id}...")
                    sources.append(source_description)

        return source_list

    ############################################
    # Public class function: create_textcritics
    ############################################
    def create_textcritics(self, soup: BeautifulSoup) -> TextCritics:
        """
        Creates a list of textcritics based on the given soup elements.

        Args:
            soup (BeautifulSoup): A BeautifulSoup object representing the document.

        Returns:
            A SourceList object containing a list of SourceDescription objects.
        """
        textcritics_list = copy.deepcopy(defaultTextcriticsList)

        # Find all table tags in soup
        tables = soup.find_all('table')

        # Iterate over tables and create textcritics
        for table_index, table in enumerate(tables):
            textcritics = copy.deepcopy(defaultTextcritics)

            rows_in_table = table.find_all('tr')
            for row in rows_in_table[1:]:
                comment = copy.deepcopy(defaultTextcriticalComment)
                columns_in_row = row.find_all('td')
                comment['measure'] = self.utils_helper.strip_tag_and_clean(columns_in_row[0], 'td')
                comment['system'] = self.utils_helper.strip_tag_and_clean(columns_in_row[1], 'td')
                comment['position'] = self.utils_helper.strip_tag_and_clean(columns_in_row[2], 'td')
                comment_text = self.utils_helper.strip_tag_and_clean(columns_in_row[3], 'td')
                comment['comment'] = self.utils_helper.replace_glyphs(comment_text)

                textcritics['comments'][0]['blockComments'].append(comment)

            print(
                f"Appending textcritics for table {table_index + 1}...")
            textcritics_list['textcritics'].append(textcritics)

        return textcritics_list
