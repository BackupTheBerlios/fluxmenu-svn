import os,re,shutil,sys
from os.path import expanduser, isfile

# read_menu: Parses a fluxbox's menu-file
# Input: menufile = string pointing to the menu, MUST be absolute
#                   use expanduser etc BEFORE calling this.
#                   And use SINGLE quotes!
# Output: table containing the menu, 4 fields:
#         [type] [name] [command] [icon]
# BUGS: Possibly parse failure if command, type or something contains
#       characters [, ], {, }, (, ), <, or >

def read_menu(menufile):
    if isfile(menufile):

        # Read menu contents
        cFile = open(menufile, "r")
        if not cFile: return None
        menuContents = cFile.readlines()
        cFile.close()

        # Parse the file
        menu = []
        for menuItem in menuContents:
            # TODO: Check for comments, save them... to... itemName, with
            # itemType == Comment, ne?

            # Item's type is marked with [ and ]
            itemType = get_item(menuItem, '[', ']')
            # Name with ( and )
            itemName = get_item(menuItem, '(', ')')
            # Command with { and }
            itemCommand= get_item(menuItem, '{', '}')
            # And icon with < and >
            itemIcon = get_item(menuItem, '<', '>')
         
            if len(itemType) > 0:
                menu.append([itemType.lower(), itemName, itemCommand, itemIcon])

    return menu


# save_menu: Saves a menu into fluxbox's format
# Input: menu = a 4 column table containing the menu
#             NOTE: end-tag _MUST_ be inserted before calling this
#        filename = filename where to save
#        overwrite = if an existing menu should be overwritten
#        useIcons = if icons should be saved or not
# Output: 0 on general error
#         1 if succesfull
#         2 if file exists and overwrite is False

def save_menu(menu, filename, overwrite, useIcons):

    if isfile(filename) and not overwrite: return 2

    if not isfile(filename): return 0

    cFile = open(filename, "w")

    intendation = 0

    for menuline in menu:
        if menuline[0] == 'end':
            intendation = intendation - 4
            if intendation < 0: intendation = 0

        printString = '[' + menuline[0] + '] (' + menuline[1] + ') {' + menuline[2] + '}'
	if useIcons:
            printString = printString + ' <' + menuline[3] + '>'
        printString = printString + '\n'

        printString = printString.rjust(intendation + len(printString))

        cFile.write(printString)

        if menuline[0] == 'begin' or menuline[0] == 'submenu':
            intendation = intendation + 4

    cFile.close()

    return 1



# backup_menu: copies menufile into the same dir with different
#              extension (.bck or .original f.e.)
# Input: menufile = path to original file
#        extension = extension to add to the backup
#        overwrite = overwrite if there is already a file with same name (boolean)
# Output: 0 on general error
#         1 if everything was succesfull
#         2 if there aleady is a file and overwrite is false

def backup_menu(menufile, extension, overwrite):
    if not isfile(menufile): return 0

    if overwrite:
        # Copy the file and overwrite if there was a file with the same extension
        try:
            shutil.copy(menufile, menufile+extension)
        except:
            return 0
    else:
        # Check that no file with the same name as the destination does exist
        if not isfile(menufile+extension):
            try:
                shutil.copy(menufile, menufile+extension)
            except:
                return 0
        else:
            return 2

    return 1



# get_item: Returns everything between two characters in a strin
# Example: get_item("[menu] (foobar)", '(', ')') => foobar

def get_item(line, startchar, endchar):
    lineLen = len(line)
    if lineLen < 0: return ''

    itemStart = line.find(startchar)
    if itemStart < 0: return ''
    if itemStart >= lineLen: return ''
    itemStart = itemStart + 1

    itemEnd = line[itemStart:lineLen].find(endchar) + itemStart
    if itemEnd <= itemStart: return ''
    if itemEnd >= lineLen: return ''

    return line[itemStart:itemEnd]
