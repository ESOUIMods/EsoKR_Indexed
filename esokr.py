# -*- coding: utf-8 -*-
#
import re
import struct
import io
import sys
import codecs
from difflib import SequenceMatcher
import section_constants as section

# ------------------------------------------------------------------------------
class Callables:
    """A singleton set of objects (typically functions or class instances) that
    can be called as functions from the command line.

    Functions are called with their arguments, while object instances are called
    with their method and then their functions. E.g.:
    * bish afunction arg1 arg2 arg3
    * bish anInstance.aMethod arg1 arg2 arg3"""

    # --Ctor
    def __init__(self):
        """Initialization."""
        self.callObjs = {}

    # --Add a callable
    def add(self, callObj, callKey=None):
        """Add a callable object.

        callObj:
            A function or class instance.
        callKey:
            Name by which the object will be accessed from the command line.
            If callKey is not defined, then callObj.__name__ is used."""
        callKey = callKey or callObj.__name__
        self.callObjs[callKey] = callObj

    # --Help
    def printHelp(self, callKey):
        """Print help for specified callKey."""
        print(help(self.callObjs[callKey]))

    # --Main
    def main(self):
        callObjs = self.callObjs
        # --Call key, tail
        # This makes no sense since if there was a dot it would be in the filename
        callKey = sys.argv[1]
        # This makes no sense because it doesn't seem to capture what is after genHtml
        # The intent here is to use callObj.__name__ but there isn't a tail
        # callTail = (len(callParts) > 1 and callParts[1])
        # --Help request?
        if callKey == '-h':
            self.printHelp(self)
            return
        # --Not have key?
        if callKey not in callObjs:
            print("Unknown function/object: {}".format(callKey))
            return
        # --Callable
        callObj = callObjs[callKey]
        if isinstance(callObj, str):
            callObj = eval(callObj)
        # The intent here is to use callObj.__name__ but there isn't a tail
        # if callTail:
        #    callObj = eval('callObj.' + callTail)
        # --Args
        args = sys.argv[2:]
        # --Keywords?
        keywords = {}
        argDex = 0
        reKeyArg = re.compile(r'^\-(\D\w+)')
        reKeyBool = re.compile(r'^\+(\D\w+)')
        while argDex < len(args):
            arg = args[argDex]
            if reKeyArg.match(arg):
                keyword = reKeyArg.match(arg).group(1)
                value = args[argDex + 1]
                keywords[keyword] = value
                del args[argDex:argDex + 2]
            elif reKeyBool.match(arg):
                keyword = reKeyBool.match(arg).group(1)
                keywords[keyword] = 1
                del args[argDex]
            else:
                argDex = argDex + 1
        # --Apply
        callObj(*args, **keywords)


# --Callables Singleton
callables = Callables()


def mainFunction(func):
    """A function for adding functions to callables."""
    callables.add(func)
    return func


# Conversion ------------------------------------------------------------------
# (txtFilename, idFilename)
@mainFunction
def addIndexToLangFile(txtFilename, idFilename):
    """Add tag from either kb.lang or kr.lang files for use with translation files."""
    textLines = []
    idLines = []
    # Get ID numbers ------------------------------------------------------
    textIns = open(txtFilename, 'r', encoding="utf8")
    for line in textIns:
        newstr = line.rstrip()
        textLines.append(newstr)
    textIns.close()
    # Get Text ------------------------------------------------------
    idIns = open(idFilename, 'r', encoding="utf8")
    for line in idIns:
        newstr = line.strip()
        idLines.append(newstr)
    idIns.close()
    # --Write Output ------------------------------------------------------
    out = open("output.txt", 'w', encoding="utf8")
    for i in range(len(textLines)):
        lineOut = '{{{{{}:}}}}{}\n'.format(idLines[i], textLines[i])
        out.write(lineOut)
    out.close()


@mainFunction
def removeIndexToLangFile(txtFilename):
    """Remove tag from either kb.lang or kr.lang files for use with official release."""
    reIndex = re.compile(r'^\{\{(.+):\}\}(.+)$')
    reIndexOld = re.compile(r'^(\d{1,10}-\d{1,7}-\d{1,7})(.+)$')

    # Get ID numbers ------------------------------------------------------
    textLines = []
    textIns = open(txtFilename, 'r', encoding="utf8")
    for line in textIns:
        maIndex = reIndex.match(line)
        maIndexOld = reIndexOld.match(line)
        if maIndex:
            lead, text = maIndex.group(1, 2)
            textLines.append(text)
        if maIndexOld:
            lead = maIndexOld.group(2)
            text = maIndexOld.group(2)
            newString = text.replace(lead + " ", "")
            newString = newString.lstrip()
            textLines.append(newString)
    textIns.close()
    # --Write Output ------------------------------------------------------
    out = open("output.txt", 'w', encoding="utf8")
    for i in range(len(textLines)):
        lineOut = '{}\n'.format(textLines[i])
        out.write(lineOut)
    out.close()


@mainFunction
def koreanToEso(txtFilename):
    """Shift text Korean UTF8 to Chinese UTF8."""
    not_eof = True
    out = open("output.txt", 'w', encoding="utf8")
    with open(txtFilename, 'rb') as textIns:
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
    out.close()


@mainFunction
def esoToKorean(txtFilename):
    """Shift text from Chinese UTF8 to Korean UTF8."""
    not_eof = True
    out = open("output.txt", 'w', encoding="utf8")
    with open(txtFilename, 'rb') as textIns:
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
    out.close()


@mainFunction
def addIndexToEosui(txtFilename):
    """Add tags to either kr_client.str or kr_pregame.str for use with translation files."""
    reConstantTag = re.compile(r'^\[(.+?)\] = "(.+?)"$')
    reFontTag = re.compile(r'^\[Font:(.+?)')
    reEmptyLine = re.compile(r'^\[(.+?)\] = ("")$')

    textLines = []
    # Get ID numbers ------------------------------------------------------
    indexPrefix = ""
    indexCount = 0
    if re.search('client', txtFilename):
        indexPrefix = "C:"
    if re.search('pregame', txtFilename):
        indexPrefix = "P:"
    textIns = open(txtFilename, 'r', encoding="utf8")
    for line in textIns:
        indexCount = indexCount + 1
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
            lineOut = '[{}] = "{{{}}}{}"\n'.format(conIndex, indexPrefix + str(indexCount), conText)
            textLines.append(lineOut)
    textIns.close()
    # --Write Output ------------------------------------------------------
    out = open("output.txt", 'w', encoding="utf8")
    for i in range(len(textLines)):
        lineOut = textLines[i]
        out.write(lineOut)
    out.close()


@mainFunction
def removeIndexFromEosui(txtFilename):
    """Remove tags from either kr_client.str or kr_pregame.str for use with official release."""
    reConstantTagNew = re.compile(r'^\[(.+?)\] = "(\{(C|P):(.+?)\})(.+?)"$')
    reConstantTagOld = re.compile(r'^\[(.+?)\] = "(\{[^CP].+?\})(.+?)"$')
    reConstantTagOlder = re.compile(r'^\[(.+?)\] = "([^CP\{\}].+?)"$')
    reFontTag = re.compile(r'^\[Font:(.+?)')
    reEmptyLine = re.compile(r'^\[(.+?)\] = ("")$')

    textLines = []
    # Get ID numbers ------------------------------------------------------
    textIns = open(txtFilename, 'r', encoding="utf8")
    for line in textIns:
        line = line.rstrip()
        maFontTag = reFontTag.match(line)
        maConstantTagNew = reConstantTagNew.match(line)
        maConstantTagOld = reConstantTagOld.match(line)
        maConstantTagOlder = reConstantTagOlder.match(line)
        maEmptyLine = reEmptyLine.match(line)
        conIndex = ""
        conText = ""
        if maEmptyLine:
            textLines.append(line + "\n")
            continue
        if maFontTag:
            textLines.append(line + "\n")
            continue
        if maConstantTagOlder and not maFontTag:
            conIndex = maConstantTagOlder.group(1)
            conText = maConstantTagOlder.group(2)
            newString = conText.replace(conIndex + " ", "")
            lineOut = '[{}] = "{}"\n'.format(conIndex, newString)
            textLines.append(lineOut)
        if maConstantTagOld and not maFontTag:
            conIndex = maConstantTagOld.group(1)
            conText = maConstantTagOld.group(3)
            lineOut = '[{}] = "{}"\n'.format(conIndex, conText)
            textLines.append(lineOut)
        if maConstantTagNew and not maFontTag:
            conIndex = maConstantTagNew.group(1)
            conText = maConstantTagNew.group(5)
            lineOut = '[{}] = "{}"\n'.format(conIndex, conText)
            textLines.append(lineOut)
    textIns.close()
    # --Write Output ------------------------------------------------------
    out = open("output.txt", 'w', encoding="utf8")
    for i in range(len(textLines)):
        lineOut = textLines[i]
        out.write(lineOut)
    out.close()


class FileReader(io.FileIO):
    """File-object with convenience reading functions."""

    def unpack(self, fmt): return struct.unpack(fmt, self.read(struct.calcsize(fmt)))

    def readUByte(self): return struct.unpack('>B', self.read(1))[0]
    def readUInt16(self): return struct.unpack('>H', self.read(2))[0]
    def readUInt32(self): return struct.unpack('>I', self.read(4))[0]

    def readByte(self): return struct.unpack('>b', self.read(1))[0]
    def readInt16(self): return struct.unpack('>h', self.read(2))[0]
    def readInt32(self): return struct.unpack('>i', self.read(4))[0]

    def readSig(self): return struct.unpack('4s', self.read(4))[0]
    def readString8(self): return self.read(struct.unpack('B', self.read(1))[0])
    def readString16(self): return self.read(struct.unpack('>H', self.read(2))[0])
    def readString32(self): return self.read(struct.unpack('I', self.read(4))[0])

def writeUInt32(file, value): file.write(struct.pack('>I', value))

currentFileIndexes = {}
currentFileStrings = {}
previousFileIndexes = {}
previousFileStrings = {}
translatedFileIndexes = {}
translatedFileStrings = {}


@mainFunction
def readLangFile(currentLanguageFile):
    """Reads a language files such as en.lang and stores the indexes and strings in dictionaries for later processing."""

    def readString(offset, start, file):
        nullChar = False
        textLine = None
        currentPosition = file.tell()
        file.seek(start + offset)
        while not nullChar:
            shift = 1
            char = lineIn.read(shift)
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
                next_char = lineIn.read(shift - 1)
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

    lineIn = open(currentLanguageFile, 'rb')
    numSections = FileReader.readUInt32(lineIn)
    # add 1 so the range is 1 to numIndexes, instead of 0 to X
    numIndexes = FileReader.readUInt32(lineIn)
    stringsStartPosition = 8 + (16 * numIndexes)
    sectionToOutput = section.npc_names
    predictedOffset = 0
    stringCount = 0
    currentFileIndexes.update(numIndexes = numIndexes)
    for index in range(0, numIndexes):
        # Assign Section ID and Index, the offset and the string
        sectionId = FileReader.readUInt32(lineIn)
        sectionIndex = FileReader.readUInt32(lineIn)
        stringIndex = FileReader.readUInt32(lineIn)
        stringOffset = FileReader.readUInt32(lineIn)
        indexString = readString(stringOffset, stringsStartPosition, lineIn)
        # Store index
        currentFileIndexes[index] = {}
        currentFileIndexes[index].update(sectionId = sectionId)
        currentFileIndexes[index].update(sectionIndex = sectionIndex)
        currentFileIndexes[index].update(stringIndex = stringIndex)
        currentFileIndexes[index].update(stringOffset = stringOffset)
        currentFileIndexes[index].update(string = indexString)
        # Store the string with predicted offset as a value
        if currentFileStrings.get(indexString) is None:
            currentFileStrings[indexString] = {}
            currentFileStrings[indexString].update(stringOffset = predictedOffset)
            # 1 extra for the null terminator
            predictedOffset = predictedOffset + (len(indexString) + 1)
            currentFileStrings[stringCount] = {}
            currentFileStrings[stringCount].update(string = indexString)
            stringCount = stringCount + 1
    lineIn.close()
    currentFileStrings.update(stringCount = stringCount)
    print(currentFileStrings.get('stringCount'))
    numIndexes = currentFileIndexes.get('numIndexes')
    for index in range(0, numIndexes):
        currentIndex = currentFileIndexes.get(index)
        dictString = currentIndex.get('string')
        currentStringInfo = currentFileStrings.get(dictString)
        currentOffset = currentStringInfo.get('stringOffset')
        currentFileIndexes[index].update(stringOffset = currentOffset)
    indexOut = open('output.lang', 'wb')
    writeUInt32(indexOut, numSections)
    writeUInt32(indexOut, numIndexes)
    numIndexes = currentFileIndexes.get('numIndexes')
    for index in range(0, numIndexes):
        currentIndex = currentFileIndexes.get(index)
        sectionId = currentIndex.get('sectionId')
        sectionIndex = currentIndex.get('sectionIndex')
        stringIndex = currentIndex.get('stringIndex')
        stringOffset = currentIndex.get('stringOffset')
        writeUInt32(indexOut, sectionId)
        writeUInt32(indexOut, sectionIndex)
        writeUInt32(indexOut, stringIndex)
        writeUInt32(indexOut, stringOffset)
    numStrings = currentFileStrings.get('stringCount')
    for index in range(0, numStrings):
        currentDict = currentFileStrings.get(index)
        currentString = currentDict.get('string')
        indexOut.write(currentString + b'\x00')
    indexOut.close()


@mainFunction
def mergeCurrentEosuiText(translatedFilename, unTranslatedFilename):
    """replaced with: diffEsouiText

    Merges either kb_client.str or kb_pregame.str with updated translations for current live server files.
    Untested, previously attempted to merge en_client.str and kb_client.str
    """

    reConstantTag = re.compile(r'^\[(.+?)\] = "(.+?)"$')
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


@mainFunction
def mergeCurrentLangText(translatedFilename, unTranslatedFilename):
    """Untested: Merges either kb.lang or kr.lang with updated translations for current live server files."""
    reConstantTag = re.compile(r'^\{\{(.+?):\}\}(.+?)$')

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
        maConstantText = reConstantTag.match(line)
        conIndex = maConstantText.group(1)
        conText = maConstantText.group(2)
        textTranslatedDict[conIndex] = conText
    textIns.close()
    textIns = open(unTranslatedFilename, 'r', encoding="utf8")
    for line in textIns:
        maConstantText = reConstantTag.match(line)
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
    """Read live and pts en.lang, if text is unchanged use existing translation.

    translatedFilename: will almost always be kb.lang.txt
    unTranslatedLiveFilename: should be the previous en.lang converted to text and then the tags added. This can be
    en_live.lang_tag.txt or en_prv.lang_tag.txt. Anything that indicates it is older or the the previous en.lang from
    a previous chapter or patch
    unTranslatedPTSFilename: should be the current en.lang converted to text and then the tags added. This should be
    from the current en.lang from the current version after the chapter or the patch is released. This can be either
    en_pts.lang_tag.txt or en_cur.lang_tag.txt

    translatedFilename: example kb.lang.txt or kr.lang_tag.txt
    unTranslatedLiveFilename: example en_prv.lang_tag.txt
    unTranslatedPTSFilename: example en_cur.lang_tag.txt
    """
    reConstantTag = re.compile(r'^\{\{(.+?):\}\}(.+?)$')
    reColorTagStart = re.compile(r'(\|c[0-9a-zA-Z]{1,6})')
    reColorTagEnd = re.compile(r'(\|r)')
    reControlChar = re.compile(r'(\^f|\^n|\^F|\^N|\^p|\^P)')

    #-- removeUnnecessaryText
    reColorTagError = re.compile(r'(\|c000000)(\|c[0-9a-zA-Z]{6,6})')

    #-- removeUnnecessaryText not Used yet, BETA
    def removeUnnecessaryText(line):
        maColorTagError = reColorTagError.match(line)
        if maColorTagError:
            line = line.replace("|c000000", "")
        return line

    def stripWeirdChars(line):
        # Strip weird dots … or other chars
        # …, —, â€¦
        lineBytes = bytes(line, 'utf-8')
        lineBytes = lineBytes.replace(b'\xe2\x80\xa6', b'')
        lineBytes = lineBytes.replace(b'\xe2\x80\x94', b'')
        lineBytes = lineBytes.replace(b'\xc3\xa2\xe2\x82\xac\xc2\xa6', b'')
        line = lineBytes.decode('utf-8')
        return line

    def isTranslatedText(line):
        for char in range(0, len(line)):
            returnedBytes = bytes(line[char], 'utf-8')
            length = len(returnedBytes)
            if length > 1: return True
        return None

    textTranslatedDict = {}
    textUntranslatedLiveDict = {}
    textUntranslatedPTSDict = {}
    # Get Previous Translation ------------------------------------------------------
    textIns = open(translatedFilename, 'r', encoding="utf8")
    for line in textIns:
        maConstantText = reConstantTag.match(line)
        if maConstantText:
            conIndex = maConstantText.group(1)
            conText = maConstantText.group(2)
            textTranslatedDict[conIndex] = conText
    textIns.close()
    # Get Previous/Live English Text ------------------------------------------------------
    textIns = open(unTranslatedLiveFilename, 'r', encoding="utf8")
    for line in textIns:
        maConstantText = reConstantTag.match(line)
        if maConstantText:
            conIndex = maConstantText.group(1)
            conText = maConstantText.group(2)
            textUntranslatedLiveDict[conIndex] = conText
    textIns.close()
    # Get Current/PTS English Text ------------------------------------------------------
    textIns = open(unTranslatedPTSFilename, 'r', encoding="utf8")
    for line in textIns:
        maConstantIndex = reConstantTag.match(line)
        maConstantText = reConstantTag.match(line)
        if maConstantIndex or maConstantText:
            conIndex = maConstantText.group(1)
            conText = maConstantText.group(2)
            textUntranslatedPTSDict[conIndex] = conText
    textIns.close()
    # Compare PTS with Live text, write output -----------------------------------------
    out = open("output.txt", 'w', encoding="utf8")
    verifyOut = open("verify_output.txt", 'w', encoding="utf8")
    for key in textUntranslatedPTSDict:
        translatedText = textTranslatedDict.get(key)
        liveText = textUntranslatedLiveDict.get(key)
        ptsText = textUntranslatedPTSDict.get(key)
        translatedTextStripped = None
        liveTextStripped = None
        ptsTextStripped = None
        #-- Strip Odd Chars
        if translatedText is not None:
            translatedTextStripped = stripWeirdChars(translatedText)
        if liveText is not None:
            liveTextStripped = stripWeirdChars(liveText)
        if ptsText is not None:
            ptsTextStripped = stripWeirdChars(ptsText)
        #-- Assign lineOut to ptsText
        lineOut = ptsText
        hasExtendedChars = False
        hasTranslation = False
        if translatedTextStripped is not None:
            hasExtendedChars = isTranslatedText(translatedTextStripped)
        # ---Determine Change Ratio between Live and Pts---
        liveAndPtsGreaterThanThreshold = False
        hasLiveAndPts = False
        if liveTextStripped is not None and ptsTextStripped is not None:
            hasLiveAndPts = True
            subLiveText = liveTextStripped
            subPtsText = ptsTextStripped
            # Strip color codes
            subLiveText = reColorTagStart.sub('', subLiveText)
            subLiveText = reColorTagEnd.sub('', subLiveText)
            subPtsText = reColorTagStart.sub('', subPtsText)
            subPtsText = reColorTagEnd.sub('', subPtsText)
            # Strip Control Chars ^n ^f ^p
            subLiveText = reControlChar.sub('', subLiveText)
            subPtsText = reControlChar.sub('', subPtsText)
            #-- Get Ratio
            s = SequenceMatcher(None, subLiveText, subPtsText)
            if (liveTextStripped == ptsTextStripped) or (s.ratio() > 0.6):
                liveAndPtsGreaterThanThreshold = True
        # ---Determine Change Ratio between Translated and Pts ---
        translatedAndPtsGreaterThanThreshold = False
        hasTranslatedAndPts = False
        if translatedTextStripped is not None and ptsTextStripped is not None:
            hasTranslatedAndPts = True
            subTranslatedText = translatedTextStripped
            subPtsText = ptsTextStripped
            # Strip color codes
            subTranslatedText = reColorTagStart.sub('', subTranslatedText)
            subTranslatedText = reColorTagEnd.sub('', subTranslatedText)
            subPtsText = reColorTagStart.sub('', subPtsText)
            subPtsText = reColorTagEnd.sub('', subPtsText)
            # Strip Control Chars ^n ^f ^p
            subTranslatedText = reControlChar.sub('', subTranslatedText)
            subPtsText = reControlChar.sub('', subPtsText)
            #-- Get Ratio
            s = SequenceMatcher(None, subTranslatedText, subPtsText)
            if (translatedTextStripped == ptsTextStripped) or (s.ratio() > 0.6):
                translatedAndPtsGreaterThanThreshold = True
        writeOutput = False
        #-- Determine if there is a questionable comparison
        if translatedTextStripped is not None and ptsTextStripped is not None and not translatedAndPtsGreaterThanThreshold and not hasExtendedChars:
            if (translatedTextStripped != ptsTextStripped):
                hasTranslation = True
                writeOutput = True

        # Determine translation state ------------------------------
        if not hasTranslation and hasExtendedChars:
            hasTranslation = True
        if translatedTextStripped is None:
            hasTranslation = False
        #-- changes between live and pts requires new translation
        if liveTextStripped is not None and ptsTextStripped is not None:
            if not liveAndPtsGreaterThanThreshold:
                hasTranslation = False
        #-- New Line from ptsText that did not exist previously
        if liveTextStripped is None and ptsTextStripped is not None:
            hasTranslation = False

        if hasTranslation:
            lineOut = translatedText
        lineOut = '{{{{{}:}}}}{}\n'.format(key, lineOut.rstrip())
        #-- Save questionable comparison to verify
        if writeOutput:
            verifyOut.write('{{{{{}:}}}}{}\n'.format(key, translatedText.rstrip()))
            verifyOut.write('{{{{{}:}}}}{}\n'.format(key, liveText.rstrip()))
            verifyOut.write('{{{{{}:}}}}{}\n'.format(key, ptsText.rstrip()))
            verifyOut.write(lineOut)
        out.write(lineOut)
    out.close()
    verifyOut.close()


@mainFunction
def diffEsouiText(translatedFilename, liveFilename, ptsFilename):
    """Reads live and pts en_client.str or en_pregame.str and if text is the same uses existing translation."""
    reConstantTag = re.compile(r'^\[(.+?)\] = "(.+?)"$')
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


@mainFunction
def diffEnglishLangFiles(LiveFilename, ptsFilename):
    """Determines the differences between the current and pts en.lang after converted to text and tagged."""
    reConstantTag = re.compile(r'^\{\{(.+?):\}\}(.+?)$')
    reColorTagStart = re.compile(r'(\|c[0-9a-zA-Z]{1,6})')
    reColorTagEnd = re.compile(r'(\|r)')
    reControlChar = re.compile(r'(\^f|\^n|\^F|\^N|\^p|\^P)')

    textUntranslatedLiveDict = {}
    textUntranslatedPTSDict = {}
    # Get Previous/Live English Text ------------------------------------------------------
    textIns = open(LiveFilename, 'r', encoding="utf8")
    for line in textIns:
        maConstantIndex = reConstantTag.match(line)
        maConstantText = reConstantTag.match(line)
        conIndex = ""
        conText = None
        if maConstantIndex or maConstantText:
            if maConstantIndex:
                conIndex = maConstantIndex.group(1)
            if maConstantText:
                conText = maConstantText.group(2)
            textUntranslatedLiveDict[conIndex] = conText
    textIns.close()
    # Get Current/PTS English Text ------------------------------------------------------
    textIns = open(ptsFilename, 'r', encoding="utf8")
    for line in textIns:
        maConstantIndex = reConstantTag.match(line)
        maConstantText = reConstantTag.match(line)
        conIndex = ""
        conText = None
        if maConstantIndex or maConstantText:
            if maConstantIndex:
                conIndex = maConstantIndex.group(1)
            if maConstantText:
                conText = maConstantText.group(2)
            textUntranslatedPTSDict[conIndex] = conText
    textIns.close()
    # Compare PTS with Live text, write output -----------------------------------------
    matchedText = []
    closeMatchLiveText = []
    closeMatchPtsText = []
    changedText = []
    deletedText = []
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
            matchedText.append(lineOut)
            continue
        subLiveText = liveText
        subPtsText = ptsText
        # Strip color codes
        subLiveText = reColorTagStart.sub('', subLiveText)
        subLiveText = reColorTagEnd.sub('', subLiveText)
        subPtsText = reColorTagStart.sub('', subPtsText)
        subPtsText = reColorTagEnd.sub('', subPtsText)
        # Strip Control Chars ^n ^f ^p
        subLiveText = reControlChar.sub('', subLiveText)
        subPtsText = reControlChar.sub('', subPtsText)
        s = SequenceMatcher(None, subLiveText, subPtsText)
        if liveText == ptsText:
            matchedCount = matchedCount + 1
            lineOut = '{{{{{}:}}}}{}\n'.format(key, ptsText)
            matchedText.append(lineOut)
        elif s.ratio() > 0.6:
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
    # --Write Output ------------------------------------------------------
    out = open("matchedIndexes.txt", 'w', encoding="utf8")
    lineOut = '{}: new indexes added\n'.format(addedIndexCount)
    out.write(lineOut)
    lineOut = '{}: indexes matched\n'.format(matchedCount)
    out.write(lineOut)
    for i in range(len(matchedText)):
        lineOut = matchedText[i]
        out.write(lineOut)
    out.close()
    # --Write Output ------------------------------------------------------
    out = open("closeMatchLiveIndexes.txt", 'w', encoding="utf8")
    lineOut = '{}: indexes were a close match\n'.format(closMatchCount)
    out.write(lineOut)
    for i in range(len(closeMatchLiveText)):
        lineOut = closeMatchLiveText[i]
        out.write(lineOut)
    out.close()
    out = open("closeMatchPtsIndexes.txt", 'w', encoding="utf8")
    lineOut = '{}: indexes were a close match\n'.format(closMatchCount)
    out.write(lineOut)
    for i in range(len(closeMatchPtsText)):
        lineOut = closeMatchPtsText[i]
        out.write(lineOut)
    out.close()
    # --Write Output ------------------------------------------------------
    out = open("changedIndexes.txt", 'w', encoding="utf8")
    lineOut = '{}: indexes changed\n'.format(changedCount)
    out.write(lineOut)
    for i in range(len(changedText)):
        lineOut = changedText[i]
        out.write(lineOut)
    out.close()
    # --Write Output ------------------------------------------------------
    out = open("deletedIndexes.txt", 'w', encoding="utf8")
    lineOut = '{}: indexes deleted\n'.format(deletedCount)
    out.write(lineOut)
    for i in range(len(deletedText)):
        lineOut = deletedText[i]
        out.write(lineOut)
    out.close()


if __name__ == '__main__':
    callables.main()
