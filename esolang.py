# -*- coding: utf-8 -*-
#
import argparse
import sys
import os
import inspect
import re
import struct
import codecs
from difflib import SequenceMatcher
from ruamel.yaml.scalarstring import PreservedScalarString
import ruamel.yaml
import section_constants as section

# List to hold information about callable functions
callable_functions = []


def mainFunction(func):
    """Decorator to mark functions as callable and add them to the list."""
    callable_functions.append(func)
    return func


def print_help():
    print("Available callable functions:")
    for func in callable_functions:
        print("- {}: {}".format(func.__name__, func.__doc__))


def print_docstrings():
    print("Docstrings for callable functions:")
    for func in callable_functions:
        print("\nFunction: {}".format(func.__name__))
        docstring = inspect.getdoc(func)
        if docstring:
            print(docstring)
        else:
            print("No docstring available.")


def main():
    parser = argparse.ArgumentParser(description="A script to perform various operations on text files.")
    parser.add_argument("--help-functions", action="store_true", help="Print available functions and their docstrings.")
    parser.add_argument("--list-functions", action="store_true", help="List available functions without docstrings.")
    parser.add_argument("--usage", action="store_true", help="Display usage information.")
    parser.add_argument("function", nargs="?", help="The name of the function to execute.")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the function.")

    args = parser.parse_args()

    if args.usage:
        print("Usage: esokr.py function [args [args ...]]")
        print("       esokr.py --help-functions, or help")
        print("       esokr.py --list-functions, or list")
    elif args.help_functions or args.function == "help":
        print_docstrings()
    elif args.list_functions or args.function == "list":
        print("Available functions:")
        for func in callable_functions:
            print(func.__name__)
    elif args.function:
        function_name = args.function
        for func in callable_functions:
            if func.__name__ == function_name:
                func_args = args.args
                if func == addIndexToLangFile and len(func_args) < 2:
                    print("Usage: {} <txtFilename> <idFilename>".format(func.__name__))
                else:
                    func(*func_args)
                break
        else:
            print("Unknown function: {}".format(function_name))
    else:
        print("No command provided.")


# Helper for escaped chars ----------------------------------------------------
def escape_special_characters(text):
    return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace(r'\\\"', r'\"')


# Conversion ------------------------------------------------------------------
# (txtFilename, idFilename)
@mainFunction
def addIndexToLangFile(txtFilename, idFilename):
    """Add tag from either kb.lang or kr.lang files for use with translation files."""
    textLines = []
    idLines = []

    with open(txtFilename, 'r', encoding="utf8") as textIns:
        for line in textIns:
            newstr = line.rstrip()
            textLines.append(newstr)

    with open(idFilename, 'r', encoding="utf8") as idIns:
        for line in idIns:
            newstr = line.strip()
            idLines.append(newstr)

    with open('output.txt', 'w', encoding="utf8") as output:
        for i in range(len(textLines)):
            lineOut = '{{{{{}:}}}}'.format(idLines[i]) + textLines[i] + '\n'
            output.write(lineOut)


@mainFunction
def removeIndexToLangFile(txtFilename):
    """Remove tag from either kb.lang or kr.lang files for use with official release."""
    reIndex = re.compile(r'^\{\{(.+):\}\}(.+)$')
    reIndexOld = re.compile(r'^(\d{1,10}-\d{1,7}-\d{1,7})(.+)$')

    # Get ID numbers ------------------------------------------------------
    textLines = []

    with open(txtFilename, 'r', encoding="utf8") as textIns:
        for line in textIns:
            matchIndex = reIndex.match(line)
            matchIndexOld = reIndexOld.match(line)
            if matchIndex:
                lead, text = matchIndex.group(1, 2)
                textLines.append(text)
            if matchIndexOld:
                lead = matchIndexOld.group(2)
                text = matchIndexOld.group(2)
                newString = text.replace(lead + " ", "")
                newString = newString.lstrip()
                textLines.append(newString)

    with open("output.txt", 'w', encoding="utf8") as out:
        for line in textLines:
            lineOut = '{}\n'.format(line)
            out.write(lineOut)


@mainFunction
def koreanToEso(txtFilename):
    """Shift text Korean UTF8 to Chinese UTF8."""
    not_eof = True
    with open(txtFilename, 'rb') as textIns:
        with open("output.txt", 'w', encoding="utf8") as out:
            while not_eof:
                shift = 1
                char = textIns.read(shift)
                value = int.from_bytes(char, "big")
                next_char = None
                if value > 0x00 and value <= 0x74:
                    shift = 1
                elif value >= 0xc0 and value <= 0xdf:
                    shift = 2
                elif value >= 0xe0 and value <= 0xef:
                    shift = 3
                elif value >= 0xf0 and value <= 0xf7:
                    shift = 4
                if shift > 1:
                    next_char = textIns.read(shift - 1)
                if next_char:
                    char = b''.join([char, next_char])
                if not char:
                    # eof
                    break
                temp = int.from_bytes(char, "big")
                if temp >= 0xE18480 and temp <= 0xE187BF:
                    temp = temp + 0x43400
                elif temp > 0xE384B0 and temp <= 0xE384BF:
                    temp = temp + 0x237D0
                elif temp > 0xE38580 and temp <= 0xE3868F:
                    temp = temp + 0x23710
                elif temp >= 0xEAB080 and temp <= 0xED9EAC:
                    if temp >= 0xEAB880 and temp <= 0xEABFBF:
                        temp = temp - 0x33800
                    elif temp >= 0xEBB880 and temp <= 0xEBBFBF:
                        temp = temp - 0x33800
                    elif temp >= 0xECB880 and temp <= 0xECBFBF:
                        temp = temp - 0x33800
                    else:
                        temp = temp - 0x3F800
                char = temp.to_bytes(shift, byteorder='big')
                outText = codecs.decode(char, 'UTF-8')
                out.write(outText)


@mainFunction
def esoToKorean(txtFilename):
    """Shift text from Chinese UTF8 to Korean UTF8."""
    not_eof = True
    with open(txtFilename, 'rb') as textIns:
        with open("output.txt", 'w', encoding="utf8") as out:
            while not_eof:
                shift = 1
                char = textIns.read(shift)
                value = int.from_bytes(char, "big")
                next_char = None
                if value > 0x00 and value <= 0x74:
                    shift = 1
                elif value >= 0xc0 and value <= 0xdf:
                    shift = 2
                elif value >= 0xe0 and value <= 0xef:
                    shift = 3
                elif value >= 0xf0 and value <= 0xf7:
                    shift = 4
                if shift > 1:
                    next_char = textIns.read(shift - 1)
                if next_char:
                    char = b''.join([char, next_char])
                if not char:
                    # eof
                    break
                temp = int.from_bytes(char, "big")
                if temp >= 0xE5B880 and temp <= 0xE5BBBF:
                    temp = temp - 0x43400
                elif temp > 0xE5BC80 and temp <= 0xE5BC8F:
                    temp = temp - 0x237D0
                elif temp > 0xE5BC90 and temp <= 0xE5BD9F:
                    temp = temp - 0x23710
                elif temp >= 0xE6B880 and temp <= 0xE9A6AC:
                    if temp >= 0xE78080 and temp <= 0xE787BF:
                        temp = temp + 0x33800
                    elif temp >= 0xE88080 and temp <= 0xE887BF:
                        temp = temp + 0x33800
                    elif temp >= 0xE98080 and temp <= 0xE987BF:
                        temp = temp + 0x33800
                    else:
                        temp = temp + 0x3F800
                char = temp.to_bytes(shift, byteorder='big')
                outText = codecs.decode(char, 'UTF-8')
                out.write(outText)


@mainFunction
def addIndexToEosui(txtFilename):
    """Add tags to either kr_client.str or kr_pregame.str for use with translation files."""
    reConstantTag = re.compile(r'^\[(.+?)\] = "(.*?)"$')
    reFontTag = re.compile(r'^\[Font:(.+?)')
    reEmptyLine = re.compile(r'^\[(.+?)\] = ("")$')

    no_prefix_indexes = [
        "SI_PLAYER_NAME",
        "SI_PLAYER_NAME_WITH_TITLE_FORMAT",
        "SI_MEGASERVER0",
        "SI_MEGASERVER1",
        "SI_MEGASERVER2",
        "SI_KEYBINDINGS_LAYER_BATTLEGROUNDS",
        "SI_KEYBINDINGS_LAYER_DIALOG",
        "SI_KEYBINDINGS_LAYER_GENERAL",
        "SI_KEYBINDINGS_LAYER_HOUSING_EDITOR",
        "SI_KEYBINDINGS_LAYER_HOUSING_EDITOR_PLACEMENT_MODE",
        "SI_KEYBINDINGS_LAYER_HUD_HOUSING",
        "SI_KEYBINDINGS_LAYER_INSTANCE_KICK_WARNING",
        "SI_KEYBINDINGS_LAYER_NOTIFICATIONS",
        "SI_KEYBINDINGS_LAYER_SIEGE",
        "SI_KEYBINDINGS_LAYER_USER_INTERFACE_SHORTCUTS",
        "SI_KEYBINDINGS_LAYER_UTILITY_WHEEL"
    ]

    textLines = []
    indexPrefix = ""

    if re.search('client', txtFilename):
        indexPrefix = "C:"
    if re.search('pregame', txtFilename):
        indexPrefix = "P:"

    with open(txtFilename, 'r', encoding="utf8") as textIns:
        for indexCount, line in enumerate(textIns, start=1):
            maFontTag = reFontTag.match(line)
            maConstantIndex = reConstantTag.match(line)
            maConstantText = reConstantTag.match(line)
            maEmptyLine = reEmptyLine.match(line)
            conIndex = ""
            conText = ""

            if maEmptyLine:
                textLines.append(line)
                continue
            if maFontTag:
                textLines.append(line)
                continue
            if maConstantIndex or maConstantText:
                if maConstantIndex:
                    conIndex = maConstantIndex.group(1)
                if maConstantText:
                    conText = maConstantText.group(2)
                if conIndex not in no_prefix_indexes:
                    lineOut = '[{}] = "{{{}}}{}"\n'.format(conIndex, indexPrefix + str(indexCount), conText)
                else:
                    lineOut = '[{}] = "{}"\n'.format(conIndex, conText)
                textLines.append(lineOut)

    with open("output.txt", 'w', encoding="utf8") as out:
        for i in range(len(textLines)):
            lineOut = textLines[i]
            out.write(lineOut)


@mainFunction
def removeIndexFromEosui(txtFilename):
    """Remove tags from either kr_client.str or kr_pregame.str for use with official release."""
    reConstantTagNew = re.compile(r'^\[(.+?)\] = "(\{(C|P):(.+?)\})(.+?)"$')
    reConstantTagOld = re.compile(r'^\[(.+?)\] = "(\{[^CP].+?\})(.+?)"$')
    reConstantTagOlder = re.compile(r'^\[(.+?)\] = "([^CP\{\}].+?)"$')
    reFontTag = re.compile(r'^\[Font:(.+?)')
    reEmptyLine = re.compile(r'^\[(.+?)\] = ("")$')

    textLines = []

    with open(txtFilename, 'r', encoding="utf8") as textIns:
        for line in textIns:
            line = line.rstrip()
            maFontTag = reFontTag.match(line)
            maConstantTagNew = reConstantTagNew.match(line)
            maConstantTagOld = reConstantTagOld.match(line)
            maConstantTagOlder = reConstantTagOlder.match(line)
            maEmptyLine = reEmptyLine.match(line)
            conIndex = ""
            conText = ""

            if maEmptyLine or maFontTag:
                textLines.append(line + "\n")
                continue

            if maConstantTagOlder:
                conIndex = maConstantTagOlder.group(1)
                conText = maConstantTagOlder.group(2)
                newString = conText.replace(conIndex + " ", "")
                lineOut = '[{}] = "{}"\n'.format(conIndex, newString)
                textLines.append(lineOut)
            elif maConstantTagOld:
                conIndex = maConstantTagOld.group(1)
                conText = maConstantTagOld.group(3)
                lineOut = '[{}] = "{}"\n'.format(conIndex, conText)
                textLines.append(lineOut)
            elif maConstantTagNew:
                conIndex = maConstantTagNew.group(1)
                conText = maConstantTagNew.group(5)
                lineOut = '[{}] = "{}"\n'.format(conIndex, conText)
                textLines.append(lineOut)

    with open("output.txt", 'w', encoding="utf8") as out:
        for lineOut in textLines:
            out.write(lineOut)


currentFileIndexes = {}
currentFileStrings = {}
previousFileIndexes = {}
previousFileStrings = {}
translatedFileIndexes = {}
translatedFileStrings = {}


def readUInt32(file): return struct.unpack('>I', file.read(4))[0]


def writeUInt32(file, value): file.write(struct.pack('>I', value))


def readNullStringByChar(offset, start, file):
    """Reads one byte and any subsequent bytes of a multi byte sequence."""
    nullChar = False
    textLine = None
    currentPosition = file.tell()
    file.seek(start + offset)
    while not nullChar:
        shift = 1
        char = file.read(shift)
        value = int.from_bytes(char, "big")
        next_char = None
        if value > 0x00 and value <= 0x74:
            shift = 1
        elif value >= 0xc0 and value <= 0xdf:
            shift = 2
        elif value >= 0xe0 and value <= 0xef:
            shift = 3
        elif value >= 0xf0 and value <= 0xf7:
            shift = 4
        if shift > 1:
            next_char = file.read(shift - 1)
        if next_char:
            char = b''.join([char, next_char])
        if not char:
            # eof
            break
        if textLine is None:
            textLine = char
            continue
        if textLine is not None and char != b'\x00':
            textLine = b''.join([textLine, char])
        # if textLine is not None and char != b'\x00' and char == b'\x0A':
        #     textLine = b''.join([textLine, b'\x5C\x6E'])
        if textLine is not None and char == b'\x00':
            nullChar = True
    file.seek(currentPosition)
    return textLine


def readNullString(offset, start, file):
    """Reads the amount of bytes of chunkSize and looks for a null char then returns a string."""
    chunkSize = 1024
    nullChar = False
    textLine = b''
    currentPosition = file.tell()
    file.seek(start + offset)
    while not nullChar:
        chunk = file.read(chunkSize)
        if not chunk:
            # End of file
            break
        null_index = chunk.find(b"\x00")
        if null_index >= 0:
            # Found the null terminator within the chunk
            textLine += chunk[:null_index]
            nullChar = True
        else:
            # Null terminator not found in this chunk, so append the whole chunk to textLine
            textLine += chunk
    file.seek(currentPosition)
    return textLine


def readLangFile(languageFileName):
    with open(languageFileName, 'rb') as lineIn:
        numSections = readUInt32(lineIn)
        numIndexes = readUInt32(lineIn)
        stringsStartPosition = 8 + (16 * numIndexes)
        predictedOffset = 0
        stringCount = 0
        fileIndexes = {'numIndexes': numIndexes, 'numSections': numSections}
        fileStrings = {'stringCount': stringCount}

        for index in range(numIndexes):
            chunk = lineIn.read(16)
            sectionId, sectionIndex, stringIndex, stringOffset = struct.unpack('>IIII', chunk)
            indexString = readNullString(stringOffset, stringsStartPosition, lineIn)
            fileIndexes[index] = {
                'sectionId': sectionId,
                'sectionIndex': sectionIndex,
                'stringIndex': stringIndex,
                'stringOffset': stringOffset,
                'string': indexString
            }
            if indexString not in fileStrings:
                # Create a dictionary entry for the offset with the indexString as a key
                fileStrings[indexString] = {
                    'stringOffset': predictedOffset,
                }
                # Create a dictionary entry for the string with stringCount as a key
                fileStrings[stringCount] = {
                    'string': indexString,
                }
                # add one to stringCount
                stringCount += 1
                # 1 extra for the null terminator
                predictedOffset += (len(indexString) + 1)
        fileStrings['stringCount'] = stringCount

    return fileIndexes, fileStrings


def writeLangFile(languageFileName, fileIndexes, fileStrings):
    numIndexes = fileIndexes['numIndexes']
    numSections = fileIndexes['numSections']
    numStrings = fileStrings['stringCount']

    # Read the indexes and update offset if string length has changed.
    for index in range(numIndexes):
        currentIndex = fileIndexes[index]
        dictString = currentIndex['string']
        currentStringInfo = fileStrings[dictString]
        currentOffset = currentStringInfo['stringOffset']
        fileIndexes[index]['stringOffset'] = currentOffset

    with open(languageFileName, 'wb') as indexOut:
        writeUInt32(indexOut, numSections)
        writeUInt32(indexOut, numIndexes)
        for index in range(numIndexes):
            currentIndex = fileIndexes[index]
            sectionId = currentIndex['sectionId']
            sectionIndex = currentIndex['sectionIndex']
            stringIndex = currentIndex['stringIndex']
            stringOffset = currentIndex['stringOffset']
            chunk = struct.pack('>IIII', sectionId, sectionIndex, stringIndex, stringOffset)
            indexOut.write(chunk)
        for index in range(numStrings):
            currentDict = fileStrings[index]
            currentString = currentDict['string']
            indexOut.write(currentString + b'\x00')


@mainFunction
def readCurrentLangFile(currentLanguageFile):
    """Reads a language files such as en.lang and stores the indexes and strings in dictionaries for later processing."""

    currentFileIndexes, currentFileStrings = readLangFile(currentLanguageFile)
    print(currentFileStrings['stringCount'])
    writeLangFile('output.lang', currentFileIndexes, currentFileStrings)


@mainFunction
def combineClientFiles(client_filename, pregame_filename):
    """Read in client and pregame files and save the combined information to
    output.txt as one file to avoid duplication of SI_ constants."""
    reConstantTag = re.compile(r'^\[(.+?)\] = "(.*?)"$')
    textLines = []
    conIndex_set = set()

    def extract_constant(line):
        conIndex = None
        conText = None
        match = reConstantTag.match(line)
        if match:
            conIndex, conText = match.groups()
            if conText == "":
                conText = '""'  # Set conText as two double quotes
        return conIndex, conText

    def add_line(line, conIndex, conText):
        if conIndex not in conIndex_set:
            escaped_conText = escape_special_characters(conText)
            textLines.append('[{}] = "{}"\n'.format(conIndex, escaped_conText))
            conIndex_set.add(conIndex)

    # Process client.str file
    with open(client_filename, 'r', encoding="utf8") as textInsClient:
        for line in textInsClient:
            line = line.rstrip()
            if line.startswith("["):
                conIndex, conText = extract_constant(line)
                add_line(line, conIndex, conText)
            else:
                textLines.append(line + "\n")

    # Process pregame.str file
    with open(pregame_filename, 'r', encoding="utf8") as textInsPregame:
        for line in textInsPregame:
            line = line.rstrip()
            if line.startswith("["):
                conIndex, conText = extract_constant(line)
                add_line(line, conIndex, conText)
            else:
                textLines.append(line + "\n")

    # Write output to output.txt
    with open("output.txt", 'w', encoding="utf8") as out:
        for lineOut in textLines:
            out.write(lineOut)


@mainFunction
def createWeblateFile(input_filename, langValue):
    """Read output.txt from combineClientFiles and specify the langValue
    such as turkish to use as the name of the translated string and save
    the resulting text as a yaml file for use with weblate."""
    reConstantTag = re.compile(r'^\[(.+?)\] = "(.*?)"$')
    output_filename = os.path.splitext(input_filename)[0] + ".yaml"

    try:
        with open(input_filename, 'r', encoding="utf8") as textIns:
            translations = {}
            for line in textIns:
                match = reConstantTag.match(line)
                if match:
                    conIndex, conText = match.groups()
                    translations[conIndex] = conText
    except FileNotFoundError:
        print("{} not found. Aborting.".format(input_filename))
        return

    if not translations:
        print("No translations found in {}. Aborting.".format(input_filename))
        return

    first_conIndex = list(translations.keys())[0]
    if not first_conIndex.startswith("SI_"):
        print("First conIndex '{}' does not start with 'SI_'. Aborting.".format(first_conIndex))
        return

    # Generate the YAML-like output
    with open(output_filename, 'w', encoding="utf8") as weblate_file:
        for conIndex, conText in translations.items():
            # Use double quotes around the placeholder and escape single quotes inside conText
            weblate_file.write('{}:\n'.format(conIndex))
            weblate_file.write('  english: "{}"\n'.format(conText))
            weblate_file.write('  {}: "{}"\n'.format(langValue, conText))


@mainFunction
def importClientTranslations(inputYaml, inputClientFile, langValue):
    """Read inputYaml from createWeblateFile and either the client.str
    or pregame.str file and update the translated text langValue."""

    reConstantTag = re.compile(r'^\[(.+?)\] = "(.*?)"$')
    translations = {}

    # Read the translations from the YAML file
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    with open(inputYaml, 'r', encoding="utf8") as yaml_file:
        yaml_data = yaml.load(yaml_file)

    # Access the YAML items
    for conIndex, conText in yaml_data.items():
        translations[conIndex] = {
            'english': conText['english'],
            langValue: conText[langValue],  # Use langValue as the key for the specified language
        }

    # Update translations from the inputClientFile
    with open(inputClientFile, 'r', encoding="utf8") as textIns:
        for line in textIns:
            match = reConstantTag.match(line)
            if match:
                conIndex, conText = match.groups()
                if conIndex in translations and conText != translations[conIndex]['english']:
                    translations[conIndex][langValue] = conText  # Update the specified language

    # Generate the updated YAML-like output with double-quoted scalars and preserved formatting
    output_filename = os.path.splitext(inputYaml)[0] + "_updated.yaml"
    with open(output_filename, 'w', encoding="utf8") as updatedFile:
        for conIndex, values in translations.items():
            escaped_english_text = escape_special_characters(values['english'])
            escaped_lang_text = escape_special_characters(values[langValue])  # Use langValue here
            yaml_text = (
                "{}:\n  english: \"{}\"\n  {}: \"{}\"\n".format(
                    conIndex, escaped_english_text, langValue, escaped_lang_text
                )
            )
            updatedFile.write(yaml_text)

    print("Updated translations saved to {}.".format(output_filename))


@mainFunction
def mergeCurrentEosuiText(translatedFilename, unTranslatedFilename):
    """replaced with: diffEsouiText

    Merges either kb_client.str or kb_pregame.str with updated translations for current live server files.
    Untested, previously attempted to merge en_client.str and kb_client.str
    """

    reConstantTag = re.compile(r'^\[(.+?)\] = "(.*?)"$')
    reFontTag = re.compile(r'^\[Font:(.+?)')
    reEmptyLine = re.compile(r'^\[(.+?)\] = \"\"')

    textTranslatedDict = {}
    textUntranslatedDict = {}
    # Get ID numbers ------------------------------------------------------
    textIns = open(translatedFilename, 'r', encoding="utf8")
    for line in textIns:
        line = line.rstrip()
        maFontTag = reFontTag.match(line)
        maConstantIndex = reConstantTag.match(line)
        maConstantText = reConstantTag.match(line)
        maEmptyLine = reEmptyLine.match(line)
        conIndex = ""
        conText = ""
        if maEmptyLine:
            continue
        if maFontTag:
            continue
        if maConstantIndex or maConstantText and not maFontTag:
            if maConstantIndex:
                conIndex = maConstantIndex.group(1)
            if maConstantText:
                conText = maConstantText.group(2)
                newString = conText.replace(conIndex + " ", "")
            textTranslatedDict[conIndex] = newString
    textIns.close()
    textIns = open(unTranslatedFilename, 'r', encoding="utf8")
    for line in textIns:
        line = line.rstrip()
        maFontTag = reFontTag.match(line)
        maConstantIndex = reConstantTag.match(line)
        maConstantText = reConstantTag.match(line)
        maEmptyLine = reEmptyLine.match(line)
        conIndex = ""
        conText = ""
        if maEmptyLine:
            continue
        if maFontTag:
            continue
        if maConstantIndex or maConstantText and not maFontTag:
            if maConstantIndex:
                conIndex = maConstantIndex.group(1)
            if maConstantText:
                conText = maConstantText.group(2)
                newString = conText.replace(conIndex + " ", "")
            textUntranslatedDict[conIndex] = newString
    textIns.close()
    # --Write Output ------------------------------------------------------
    out = open("output.txt", 'w', encoding="utf8")
    for key in textUntranslatedDict:
        conIndex = key
        conText = None
        if textTranslatedDict.get(conIndex) is not None:
            conText = textTranslatedDict[key]
        if not conText:
            conText = textUntranslatedDict[key]
        lineOut = '[{}] = "{}"\n'.format(conIndex, conText)
        out.write(lineOut)
    out.close()


textUntranslatedLiveDict = {}
textUntranslatedPTSDict = {}
textTranslatedDict = {}


def readTaggedLangFile(taggedFile, targetDict):
    reLangConstantTag = re.compile(r'^\{\{(.+?):\}\}(.+?)$')

    with open(taggedFile, 'r', encoding="utf8") as textIns:
        for line in textIns:
            maConstantText = reLangConstantTag.match(line)
            if maConstantText:
                conIndex = maConstantText.group(1)
                conText = maConstantText.group(2)
                targetDict[conIndex] = conText


def cleanText(line):
    if line is None:
        return None

    # Strip weird dots … or other chars
    line = line.replace('…', '').replace('—', '').replace('â€¦', '')

    # Remove unnecessary color tags
    reColorTagError = re.compile(r'(\|c000000)(\|c[0-9a-zA-Z]{6,6})')
    maColorTagError = reColorTagError.match(line)
    if maColorTagError:
        line = line.replace("|c000000", "")

    return line


def calculate_similarity_and_threshold(text1, text2):
    reColorTag = re.compile(r'\|c[0-9a-zA-Z]{1,6}|\|r')
    reControlChar = re.compile(r'\^f|\^n|\^F|\^N|\^p|\^P')

    if not text1 or not text2:
        return False

    subText1 = reColorTag.sub('', text1)
    subText2 = reColorTag.sub('', text2)
    subText1 = reControlChar.sub('', subText1)
    subText2 = reControlChar.sub('', subText2)

    similarity_ratio = SequenceMatcher(None, subText1, subText2).ratio()

    return text1 == text2 or similarity_ratio > 0.6


@mainFunction
def mergeCurrentLangText(translatedFilename, unTranslatedFilename):
    """Untested: Merges either kb.lang or kr.lang with updated translations for current live server files."""
    reLangConstantTag = re.compile(r'^\{\{(.+?):\}\}(.+?)$')

    def isTranslatedText(line):
        for char in range(0, len(line)):
            returnedBytes = bytes(line[char], 'utf-8')
            length = len(returnedBytes)
            if length > 1: return True
        return None

    textTranslatedDict = {}
    textUntranslatedDict = {}
    # Get ID numbers ------------------------------------------------------
    textIns = open(translatedFilename, 'r', encoding="utf8")
    for line in textIns:
        maConstantText = reLangConstantTag.match(line)
        conIndex = maConstantText.group(1)
        conText = maConstantText.group(2)
        textTranslatedDict[conIndex] = conText
    textIns.close()
    textIns = open(unTranslatedFilename, 'r', encoding="utf8")
    for line in textIns:
        maConstantText = reLangConstantTag.match(line)
        conIndex = maConstantText.group(1)
        conText = maConstantText.group(2)
        textUntranslatedDict[conIndex] = conText
    textIns.close()
    # --Write Output ------------------------------------------------------
    out = open("output.txt", 'w', encoding="utf8")
    for key in textUntranslatedDict:
        conText = None
        if textTranslatedDict.get(key) is None:
            conText = textUntranslatedDict[key]
            lineOut = '{{{{{}:}}}}{}\n'.format(key, conText.rstrip())
            out.write(lineOut)
            continue
        if textTranslatedDict.get(key) is not None:
            if isTranslatedText(textTranslatedDict.get(key)):
                conText = textTranslatedDict[key]
        if not conText:
            conText = textUntranslatedDict[key]
        lineOut = '{{{{{}:}}}}{}\n'.format(key, conText)
        out.write(lineOut)
    out.close()


@mainFunction
def diffIndexedLangText(translatedFilename, unTranslatedLiveFilename, unTranslatedPTSFilename):
    """
    Compare translations between different versions of language files.

    This function compares translations between different versions of language files and writes the results to output files.

    Args:
        translatedFilename (str): The filename of the translated language file (e.g., kb.lang.txt).
        unTranslatedLiveFilename (str): The filename of the previous/live English language file with tags (e.g., en_prv.lang_tag.txt).
        unTranslatedPTSFilename (str): The filename of the current/PTS English language file with tags (e.g., en_cur.lang_tag.txt).

    Notes:
        - `translatedFilename` should be the translated language file, usually for another language.
        - `unTranslatedLiveFilename` should be the previous/live English language file with tags.
        - `unTranslatedPTSFilename` should be the current/PTS English language file with tags.
        - The output is written to "output.txt" and "verify_output.txt" files.

    The function performs the following steps:
    - Reads the translations from the specified files into dictionaries.
    - Cleans and preprocesses the texts by removing unnecessary characters and color tags.
    - Compares the PTS and live texts to determine if translation changes are needed.
    - Writes the output to "output.txt" with potential new translations and to "verify_output.txt" for verification purposes.
    """

    def isTranslatedText(line):
        return any(ord(char) > 127 for char in line)

    # Get Previous Translation ------------------------------------------------------
    readTaggedLangFile(translatedFilename, textTranslatedDict)
    # Get Previous/Live English Text ------------------------------------------------------
    readTaggedLangFile(unTranslatedLiveFilename, textUntranslatedLiveDict)
    # Get Current/PTS English Text ------------------------------------------------------
    readTaggedLangFile(unTranslatedPTSFilename, textUntranslatedPTSDict)
    # Compare PTS with Live text, write output -----------------------------------------
    with open("output.txt", 'w', encoding="utf8") as out:
        with open("verify_output.txt", 'w', encoding="utf8") as verifyOut:
            for key in textUntranslatedPTSDict:
                translatedText = textTranslatedDict.get(key)
                liveText = textUntranslatedLiveDict.get(key)
                ptsText = textUntranslatedPTSDict.get(key)
                translatedTextStripped = cleanText(translatedText)
                liveTextStripped = cleanText(liveText)
                ptsTextStripped = cleanText(ptsText)
                # -- Assign lineOut to ptsText
                lineOut = ptsText
                hasTranslation = False
                hasExtendedChars = isTranslatedText(translatedTextStripped)
                # ---Determine Change Ratio between Live and Pts---
                liveAndPtsGreaterThanThreshold = calculate_similarity_and_threshold(liveTextStripped, ptsTextStripped)
                # ---Determine Change Ratio between Translated and Pts ---
                translatedAndPtsGreaterThanThreshold = calculate_similarity_and_threshold(translatedTextStripped,
                                                                                          ptsTextStripped)
                writeOutput = False
                # -- Determine if there is a questionable comparison
                if translatedTextStripped and ptsTextStripped and not translatedAndPtsGreaterThanThreshold and not hasExtendedChars:
                    if translatedTextStripped != ptsTextStripped:
                        hasTranslation = True
                        writeOutput = True
                # Determine translation state ------------------------------
                if not hasTranslation and hasExtendedChars:
                    hasTranslation = True
                if translatedTextStripped is None:
                    hasTranslation = False
                # -- changes between live and pts requires new translation
                if liveTextStripped is not None and ptsTextStripped is not None:
                    if not liveAndPtsGreaterThanThreshold:
                        hasTranslation = False
                # -- New Line from ptsText that did not exist previously
                if liveTextStripped is None and ptsTextStripped is not None:
                    hasTranslation = False
                if hasTranslation:
                    lineOut = translatedText
                lineOut = '{{{{{}:}}}}{}\n'.format(key, lineOut.rstrip())
                # -- Save questionable comparison to verify
                if writeOutput:
                    verifyOut.write('{{{{{}:}}}}{}\n'.format(key, translatedText.rstrip()))
                    verifyOut.write('{{{{{}:}}}}{}\n'.format(key, liveText.rstrip()))
                    verifyOut.write('{{{{{}:}}}}{}\n'.format(key, ptsText.rstrip()))
                    verifyOut.write(lineOut)
                out.write(lineOut)


@mainFunction
def diffEsouiText(translatedFilename, liveFilename, ptsFilename):
    """Reads live and pts en_client.str or en_pregame.str and if text is the same uses existing translation."""
    reConstantTag = re.compile(r'^\[(.+?)\] = "(.*?)"$')
    reFontTag = re.compile(r'^\[Font:(.+?)')
    reEmptyLine = re.compile(r'^\[(.+?)\] = ("")$')

    def isTranslatedText(line):
        for char in range(0, len(line)):
            returnedBytes = bytes(line[char], 'utf-8')
            length = len(returnedBytes)
            if length > 1: return True
        return None

    textTranslatedDict = {}
    liveUntranslatedDict = {}
    ptsUntranslatedDict = {}
    # Read translated text ----------------------------------------------------
    textIns = open(translatedFilename, 'r', encoding="utf8")
    for line in textIns:
        line = line.rstrip()
        maFontTag = reFontTag.match(line)
        maConstantText = reConstantTag.match(line)
        maEmptyLine = reEmptyLine.match(line)
        if maEmptyLine:
            conIndex = maEmptyLine.group(1)
            conText = maEmptyLine.group(2)
            textTranslatedDict[conIndex] = conText
            continue
        if maFontTag:
            continue
        if maConstantText and not maEmptyLine and not maFontTag:
            conIndex = maConstantText.group(1)
            conText = maConstantText.group(2)
            # newString = conText.replace(conIndex + " ", "")
            textTranslatedDict[conIndex] = conText
    textIns.close()
    # Read live text ----------------------------------------------------
    textIns = open(liveFilename, 'r', encoding="utf8")
    for line in textIns:
        line = line.rstrip()
        maFontTag = reFontTag.match(line)
        maConstantText = reConstantTag.match(line)
        maEmptyLine = reEmptyLine.match(line)
        if maEmptyLine:
            conIndex = maEmptyLine.group(1)
            conText = maEmptyLine.group(2)
            liveUntranslatedDict[conIndex] = conText
            continue
        if maFontTag:
            continue
        if maConstantText and not maEmptyLine and not maFontTag:
            conIndex = maConstantText.group(1)
            conText = maConstantText.group(2)
            # newString = conText.replace(conIndex + " ", "")
            liveUntranslatedDict[conIndex] = conText
    textIns.close()
    # Read pts text ----------------------------------------------------
    textIns = open(ptsFilename, 'r', encoding="utf8")
    for line in textIns:
        line = line.rstrip()
        maFontTag = reFontTag.match(line)
        maConstantText = reConstantTag.match(line)
        maEmptyLine = reEmptyLine.match(line)
        if maEmptyLine:
            conIndex = maEmptyLine.group(1)
            conText = maEmptyLine.group(2)
            ptsUntranslatedDict[conIndex] = conText
            continue
        if maFontTag:
            continue
        if maConstantText and not maEmptyLine and not maFontTag:
            conIndex = maConstantText.group(1)
            conText = maConstantText.group(2)
            # newString = conText.replace(conIndex + " ", "")
            ptsUntranslatedDict[conIndex] = conText
    textIns.close()
    # --Write Output ------------------------------------------------------
    out = open("output.txt", 'w', encoding="utf8")
    for key in ptsUntranslatedDict:
        translatedText = textTranslatedDict.get(key)
        liveText = liveUntranslatedDict.get(key)
        ptsText = ptsUntranslatedDict.get(key)
        if len(ptsText) == 2:
            firstChar = ord(ptsText[0])
            lastChar = ord(ptsText[1])
            if firstChar == 34 and lastChar == 34:
                lineOut = '[{}] = ""\n'.format(key)
                out.write(lineOut)
                continue
        hasExtendedChars = False
        hasTranslation = False
        outputText = ptsText

        if translatedText is not None and (translatedText != ""):
            hasExtendedChars = isTranslatedText(translatedText)
            if (translatedText != ptsText):
                hasTranslation = True
        if not hasTranslation and hasExtendedChars:
            hasTranslation = True
        if translatedText is None:
            hasTranslation = False

        if hasTranslation:
            outputText = translatedText
        lineOut = '[{}] = "{}"\n'.format(key, outputText)
        out.write(lineOut)
    out.close()


def write_output_file(filename, targetList, targetCount, targetString):
    with open(filename, 'w', encoding="utf8") as out:
        lineOut = '{}: indexes {}\n'.format(targetCount, targetString)
        out.write(lineOut)
        for i in range(len(targetList)):
            lineOut = targetList[i]
            out.write(lineOut)


@mainFunction
def diffEnglishLangFiles(LiveFilename, ptsFilename):
    """
    Compare differences between the current and PTS 'en.lang' files after conversion to text and tagging.

    This function analyzes differences between two versions of 'en.lang' files: the current version and the PTS version.
    It then categorizes and writes the findings to separate output files.

    Args:
        LiveFilename (str): The filename of the previous/live 'en.lang' file with tags.
        ptsFilename (str): The filename of the current/PTS 'en.lang' file with tags.

    Notes:
        The function reads the translation data from the specified files using the 'readTaggedLangFile' function.
        The analysis results are categorized into 'matched', 'close match', 'changed', 'added', and 'deleted' indexes.
        Output is written to various output files for further review and analysis.

    The function performs the following steps:
    - Reads translation data from the specified files into dictionaries.
    - Compares translations between PTS and live texts, categorizing indexes as 'matched', 'close match', 'changed',
      'added', or 'deleted'.
    - Identifies and categorizes new and deleted indexes.
    - Writes analysis results to separate output files.

    Outputs:
    - 'matchedIndexes.txt': Indexes that have identical translations in PTS and live versions.
    - 'closeMatchLiveIndexes.txt': Indexes with translations that are close in similarity between PTS and live versions.
    - 'closeMatchPtsIndexes.txt': Corresponding PTS translations for 'closeMatchLiveIndexes.txt'.
    - 'changedIndexes.txt': Indexes with changed translations between PTS and live versions.
    - 'deletedIndexes.txt': Indexes present in the live version but absent in the PTS version.
    - 'addedIndexes.txt': Indexes that are newly added in the PTS version.
    """
    # Get Previous/Live English Text ------------------------------------------------------
    readTaggedLangFile(LiveFilename, textUntranslatedLiveDict)
    # Get Current/PTS English Text ------------------------------------------------------
    readTaggedLangFile(ptsFilename, textUntranslatedPTSDict)
    # Compare PTS with Live text, write output -----------------------------------------
    matchedText = []
    closeMatchLiveText = []
    closeMatchPtsText = []
    changedText = []
    deletedText = []
    addedText = []
    addedIndexCount = 0
    matchedCount = 0
    closMatchCount = 0
    changedCount = 0
    deletedCount = 0
    for key in textUntranslatedPTSDict:
        ptsText = textUntranslatedPTSDict.get(key)
        liveText = textUntranslatedLiveDict.get(key)
        if textUntranslatedLiveDict.get(key) is None:
            addedIndexCount = addedIndexCount + 1
            lineOut = '{{{{{}:}}}}{}\n'.format(key, ptsText)
            addedText.append(lineOut)
            continue
        liveAndPtsGreaterThanThreshold = calculate_similarity_and_threshold(liveText, ptsText)
        if liveText == ptsText:
            matchedCount = matchedCount + 1
            lineOut = '{{{{{}:}}}}{}\n'.format(key, ptsText)
            matchedText.append(lineOut)
        elif liveAndPtsGreaterThanThreshold:
            closMatchCount = closMatchCount + 1
            lineOut = '{{{{{}:}}}}{}\n'.format(key, liveText)
            closeMatchLiveText.append(lineOut)
            lineOut = '{{{{{}:}}}}{}\n'.format(key, ptsText)
            closeMatchPtsText.append(lineOut)
        else:
            changedCount = changedCount + 1
            lineOut = '{{{{{}:pts:}}}}{}\n{{{{{}:live:}}}}{}\n\n'.format(key, ptsText, key, liveText)
            changedText.append(lineOut)
    for key in textUntranslatedLiveDict:
        liveText = textUntranslatedLiveDict.get(key)
        if textUntranslatedPTSDict.get(key) is None:
            deletedCount = deletedCount + 1
            lineOut = '{{{{{}:}}}}{}\n'.format(key, liveText)
            deletedText.append(lineOut)
    print('{}: new indexes added'.format(addedIndexCount))
    print('{}: indexes matched'.format(matchedCount))
    print('{}: indexes were a close match'.format(closMatchCount))
    print('{}: indexes changed'.format(changedCount))
    print('{}: indexes deleted'.format(deletedCount))
    # Write matched indexes
    write_output_file("matchedIndexes.txt", matchedText, matchedCount, 'matched')
    # Write close match Live indexes
    write_output_file("closeMatchLiveIndexes.txt", closeMatchLiveText, closMatchCount, 'were a close match')
    # Write close match PTS indexes
    write_output_file("closeMatchPtsIndexes.txt", closeMatchPtsText, closMatchCount, 'were a close match')
    # Write changed indexes
    write_output_file("changedIndexes.txt", changedText, changedCount, 'changed')
    # Write deleted indexes
    write_output_file("deletedIndexes.txt", deletedText, deletedCount, 'deleted')
    # Write added indexes
    write_output_file("addedIndexes.txt", addedText, addedIndexCount, 'added')


if __name__ == "__main__":
    main()
