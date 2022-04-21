import argparse
import os
import sys
from lxml import etree
import re


NS = {'a':"http://www.loc.gov/standards/alto/ns-v4#"}  # namespace for the Alto xml


def order_files(dir):
    """Generates a numerically ordered list of file names from the given directory path.

    Returns:
        ordered_files (list): files names from directory ordered by folio number
    """    
    file_names = [file for file in os.listdir(dir) if file.endswith(".xml")]
    # parses file names from a directory (given as an argument in command line) into a list of strings
    folio_numbers = sorted([int(re.search(r"(.*f)(\d+)", file).group(2)) for file in file_names])
    # extracts the folio number into a list, and orders the list of integers
    prefix = re.search(r"(.*f)(\d+)", file_names[0]).group(1)
    # parses the folio number's prefix: eg. "f" or "document_f"
    ordered_files = [prefix+str(number)+".xml" for number in folio_numbers]
    # constructs an ordered list of the complete file names by concatenating the prefix and folio number into a list of strings
    return ordered_files


def extract(ordered_files, dir):
    """Extracts text from Alto file's MainZone and puts each TextLine's contents into a list.

    Args:
        ordered_files (list): files names from directory ordered by folio number

    Returns:
        text (list): text from every TextLine/String[@CONTENT] that descends from a MainZone <TextBlock>
    """    
    text = []
    for file in ordered_files:
        # parses an xml file (the one currently passed in the loop through the directory's files) and gets the root of the generated etree
        root = etree.parse("{}/{}".format(dir, file)).getroot()
        # searches for <OtherTag> whose attribute @LABEL equals a type of "MainZone" and returns the value of that tag's attribute @ID
        mainZone_id = root.find('.//a:OtherTag[@LABEL="MainZone"]', namespaces=NS).get("ID")
        lines = [string.get("CONTENT") for string in root.findall('.//a:TextBlock[@TAGREFS="{}"]/a:TextLine/a:String'.format(mainZone_id), namespaces=NS)]
        # searches for child <String> of tag any <TextBlock> whose attribute @TAGREFS equals the id associated with MainZone,
        # gets the value of the tag's attribute @CONTENTS and appends it to a list lines[]
        if root.find('.//a:OtherTag[@LABEL="MainZone#1"]', namespaces=NS) is not None:
            mainZone1_id = root.find('.//a:OtherTag[@LABEL="MainZone#1"]', namespaces=NS).get("ID")
            MainZone1_lines = [string.get("CONTENT") for string in root.findall('.//a:TextBlock[@TAGREFS="{}"]/a:TextLine/a:String'.format(mainZone1_id), namespaces=NS)]
            lines.extend(MainZone1_lines)
        if root.find('.//a:OtherTag[@LABEL="MainZone#2"]', namespaces=NS) is not None:
            mainZone2_id = root.find('.//a:OtherTag[@LABEL="MainZone#2"]', namespaces=NS).get("ID")
            MainZone2_lines = [string.get("CONTENT") for string in root.findall('.//a:TextBlock[@TAGREFS="{}"]/a:TextLine/a:String'.format(mainZone2_id), namespaces=NS)]
            lines.extend(MainZone2_lines)
        # appends each new page's list of lines to the document's text[]
        text.extend(lines)
    return text


def dump(text, directory):
    """Formats a text according to the needs of the lemmatisation team.

    Args:
        text (list): lines of text from a document's MainZone
    """    
    s = " ".join(text)
    # join all the lines into a single string
    joined_words = re.sub(r"[\¬|-]\s+", r"", s)
    # join together words broken by a ¬ or -
    separate_lines = re.sub(r"([\.\!\?\:])( )([A-ZÉÀ1-9])", r"\1\n\n\3", joined_words)
    separate_lines = re.sub(r"(?<!^)(⁋)", r"\n\n\1", separate_lines)
    # at the end of every sentence or a clause which terminates with a semicolon and precedes a capitalized word, start a new line
    # ex. 'Escoutez ce qu’il en dit :\nTouchant'
    et_abbreviation = re.sub(r"⁊", "et", separate_lines)
    # replace the medieval abbreviation ⁊ with the word "et"
    with open(os.path.join(directory, os.path.basename(directory)+".txt"), "w") as f:
        f.write(et_abbreviation)

    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        directories = [path for path in sys.argv[1:] if os.path.isdir(path)]  # create a list of directories in data/
        for directory in directories:
            ordered_files = order_files(directory)
            text = extract(ordered_files, directory)
            dump(text, directory)
    else:
        print("No directory given")
