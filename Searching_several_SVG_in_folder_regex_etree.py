## imports

import os
import re
import xml.etree.ElementTree as ET

## set cwd

path = input('Directory to be searched (e.g. "C:\\Users\\xy\\Desktop\\Folder" or [Mac] "/Users/xy/Desktop/Folder"): ') 
path = os.path.abspath(os.path.join(path))
os.chdir(path)
filelist = os.listdir(path)


## set search pattern

pattern = input('Pattern to search (string or regular expression [e.g. "v -58" or "v\s?-?58"]): ') 

## look for "pattern" in all svg-files of cwd and add the matches to "match_list" 

match_list = []
for file in filelist:
    if file.endswith('.svg'):
        if re.search(r'\s[0-9]+\.svg', file): ## if end of file name contains a page number (default when original pdf has been extracted by Acrobate)
            file_page = (re.search(r'\s[0-9]+\.', file).group(0)) 
            file_page = int(file_page[0:-1])
            tree = ET.parse(file)
            root = tree.getroot()
            all_attrib_text = [(elem.attrib, elem.text) for elem in root.iter()]
            for item in all_attrib_text:
                if re.findall(pattern, str(item)):
                    match = file_page, file, str(item)
                    match_list.append(match)
        else:
            tree = ET.parse(file)
            root = tree.getroot()
            all_attrib_text = [(elem.attrib, elem.text) for elem in root.iter()]
            for item in all_attrib_text:
                if re.findall(pattern, str(item)):
                    match = 0, file, str(item) 
                    match_list.append(match) 

	
match_list = sorted(match_list)

print(match_list)

## save "match_list" as a txt-file (in the same directory) with all matches in a single line

with open('match_list_etree.txt', 'w', encoding='utf-8') as output:
        for match in match_list:
            match = str(match) 
            output.write(match + '\n')
               
               

          
              
          


