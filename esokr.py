# -*- coding: utf-8 -*-
#
import re
import os
import sys
import codecs

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
def addIdToFile(txtFilename, idFilename):
    """Generates a text file from two text files one containing ID numbers and one containing text."""
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
        lineOut = '{{{{{}:}}}}{}\r\n'.format(idLines[i], textLines[i])
        out.write(lineOut)
    out.close()

@mainFunction
def removeIdFromFile(txtFilename):
    """Generates a text file from two text files one containing ID numbers and one containing text."""
    reHead = re.compile(r'^\{\{(.+):\}\}(.+)')
    def identifier(maObject):
        identifier_line = maObject.group(1).strip()
        if ':' in identifier_line:
            (text_id, the_text) = [chunk.strip() for chunk in identifier_line.split(':', 1)]
        return '{}'.format(the_text)

    # Get ID numbers ------------------------------------------------------
    textLines = []
    textIns = open(txtFilename, 'r', encoding="utf8")
    for line in textIns:
        maHead = reHead.match(line)
        if maHead:
            lead, text = maHead.group(1, 2)
        textLines.append(text)
    textIns.close()
    # --Write Output ------------------------------------------------------
    out = open("noid_output.txt", 'w', encoding="utf8")
    for i in range(len(textLines)):
        lineOut = '{}\n'.format(textLines[i])
        out.write(lineOut)
    out.close()

@mainFunction
def esoToKorean(txtFilename):
    not_eof = True
    with open(txtFilename, 'rb') as textIns:
        while not_eof:
            shift = 1
            char = textIns.read(shift)
            value = int.from_bytes(char, "big")
            next_char = None
            if value > 0 and value <= 127:
                shift = 1
            elif value >= 192  and value <= 223:
                shift = 2
            elif value >= 224 and value <= 239:
                shift = 3
            elif value >= 240 and value <= 247:
                shift = 4
            if shift > 1:
                next_char = textIns.read(shift-1)
            if next_char:
                char = b''.join([char,next_char])
            outText = codecs.decode(char, 'UTF-8')
            carriageReturn = value == 13
            lineFeed = value == 10
            if not char:
                # eof
                break
            if not carriageReturn and not lineFeed:
                print(outText)

if __name__ == '__main__':
        callables.main()
