import argparse
import os
import sys
from lxml import etree
import re


# Provide --help description for a user running this application from the command line
parser = argparse.ArgumentParser(description="Extracts and collates MainZone text content from Alto xml files in a given directory.")
parser.add_argument("Directory (str)", type=str, help=": Relative file path of the directory. The directory name should be equal to the document's Archival Resource Key (ark), eg. bpt6k107371t/")
args = parser.parse_args()


DIRECTORY = str(sys.argv[1])  # directory containing Alto xml files
NS = {'a':"http://www.loc.gov/standards/alto/ns-v4#"}  # namespace for the Alto xml



def order_files():
    """Generates a numerically ordered list of file names from the given directory path.

    Returns:
        ordered_files (list): files names from directory ordered by folio number
    """    
    file_names = [file for file in os.listdir(DIRECTORY) if file.endswith(".xml")]
    # parses file names from a directory (given as an argument in command line) into a list of strings
    folio_numbers = sorted([int(re.search(r"(.*f)(\d+)", file).group(2)) for file in file_names])
    # extracts the folio number into a list, and orders the list of integers
    prefix = re.search(r"(.*f)(\d+)", file_names[0]).group(1)
    # parses the folio number's prefix: eg. "f" or "document_f"
    ordered_files = [prefix+str(number)+".xml" for number in folio_numbers]
    # constructs an ordered list of the complete file names by concatenating the prefix and folio number into a list of strings
    return ordered_files


def extract(ordered_files):
    """Extracts text from Alto file's MainZone and puts each TextLine's contents into a list.

    Args:
        ordered_files (list): files names from directory ordered by folio number

    Returns:
        text (list): text from every TextLine/String[@CONTENT] that descends from a MainZone <TextBlock>
    """    
    text = []
    for file in ordered_files:
        root = etree.parse("{}/{}".format(DIRECTORY, file)).getroot()
        # parses an xml file (the one currently passed in the loop through the directory's files) and gets the root of the generated etree
        mainZone_id = root.find('.//a:OtherTag[@LABEL="MainZone"]', namespaces=NS).get("ID") 
        # searches for <OtherTag> whose attribute @LABEL equals "MainZone" and returns the value of that tag's attribute @ID 
        lines = [string.get("CONTENT") for string in root.findall('.//a:TextBlock[@TAGREFS="{}"]/a:TextLine/a:String'.format(mainZone_id), namespaces=NS)]
        # searches for child <String> of tag any <TextBlock> whose attribute @TAGREFS equals the id associated with MainZone,
        # gets the value of the tag's attribute @CONTENTS and appends it to a list lines[]
        text.extend(lines)
        # appends each new page's list of lines to the document's text[]
    return text


def format(text):
    """Formats a text according to the needs of the lemmatisation team.

    Args:
        text (list): lines of text from a document's MainZone
    """    
    s = " ".join(text)
    # join all the lines into a single string
    joined_words = re.sub(r"[\¬|-] ", r"", s)
    # join together words broken by a ¬ or -
    separate_lines = re.sub(r"([\.!?:])( )([A-ZÉÀ1-9])", r"\1\n\n\3", joined_words)
    # at the end of every sentence or a clause which terminates with a semicolon and precedes a capitalized word, start a new line
    # ex. 'Escoutez ce qu’il en dit :\nTouchant'
    et_abbreviation = re.sub(r"\⁊", "et", separate_lines)
    # replace the medieval abbreviation ⁊ with the word "et"
    with open("{}{}.txt".format(DIRECTORY,DIRECTORY[:-1]), "w") as f:
        f.write(et_abbreviation)

    
if __name__ == "__main__":
    ordered_files = order_files()
    text = extract(ordered_files)
    format(text)