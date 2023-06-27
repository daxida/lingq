import os
import re
from typing import List


def createFolderIfNotExist(folder_name: str):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)


def clearFolder(folder_name: str):
    path = f'{folder_name}/'
    print(f"Deleting old files at this path: {path}")
    for file_name in os.listdir(path):
        file = path + file_name
        if os.path.isfile(file):
            # print('Deleting file:', file)
            os.remove(file)


def separateByHeading(text, heading_list: List[str]):
    ''' Returns a dictionary where:
            - A key is the name of a chapter (=heading)
            - The value of the key is a list of strings each 
              representing a line of the chapter
    '''
    separated_data = dict()
    _buffer = list()
    heading = None
    lines = text.readlines()
    amt_lines = len(lines)

    for idx, line in enumerate(lines):
        if line.strip() in heading_list:
            if _buffer and heading:
                separated_data[heading] = _buffer
            heading = line.strip()
            _buffer = []
        else:
            _buffer.append(line)

        # Dump buffer at the end of input.
        if idx + 1 == amt_lines:
            if _buffer:
                separated_data[heading] = _buffer

    return separated_data


def write(separated_data: dict, heading_list: List[str]):
    ''' In case of not found chapters, it writes a ?? file for easier fixing'''
    for idx_p, heading in enumerate(heading_list, 1):
        if heading in separated_data.keys():
            text = separated_data[heading]
            with open(f'split/{idx_p:02d}. {heading}.txt', 'w') as c:
                for line in separated_data[heading]:
                    c.write(line)
        else:
            with open(f'split/{idx_p:02d}. ??????????????.txt', 'w') as c:
                c.write("NONE")


def testTitles(separated_data: dict, heading_list: List[str]):
    ''' Tests that every chapter in the heading list is correctly found '''
    print(f'{len(separated_data)} chapters were found:')

    for idx, heading in enumerate(heading_list, 1):
        if heading in separated_data.keys():
            print(f"\t{idx:02d}. {heading}")
        else:
            print(f"\t{idx:02d}. NOT FOUND")

    if len(separated_data) == len(heading_list):
        print(f"Found every chapter!")
    else:
        print(f"The following chapters couldn't be found:")
        for idx, heading in enumerate(heading_list, 1):
            if heading not in separated_data.keys():
                print(f"\t{idx:02d}. {heading}")


def main():
    # Creates some folders to output the splitted chapters.
    folder_name = 'split'
    createFolderIfNotExist(folder_name)
    clearFolder(folder_name)

    # The list with the headings (=chapter names) of the next.
    heading_list = open("headings.txt", 'r').read().split("\n")

    # The current file with the text that we want to split.
    filename = 'harry.txt'
    text = open(filename, 'r')
    separated_data = separateByHeading(text, heading_list)

    # Tests that we correctly splitted the text.
    testTitles(separated_data, heading_list)

    write(separated_data, heading_list)


if __name__ == '__main__':
    main()
