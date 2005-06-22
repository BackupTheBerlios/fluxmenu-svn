#!/usr/bin/env python
# Copyright 2005 Michael Rice
# errr@errr-online.com
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


# This is fluxMenu that is based on fluxStyle because I don't know any python
# :D

import sys

try:
    import pygtk

    #tell pyGTK, if possible, that we want GTKv2.4!
    pygtk.require("2.0")
except:
    #Some distributions come with GTK2, but not pyGTK
    print "No pygtk 2.4, trying to load gtk..."

    pass


try:
    import gtk
except:
    print "You need to have gtk!"
    sys.exit(1)

try:
    import gtk.glade
except:
    print "You need libglade2!",
    sys.exit(1)

import os
import gobject
from os.path import isfile,expanduser

import handleMenu
import findIcons

#now we have both gtk and gtk.glade imported
#Also, we know we are running GTK v2


windowTitle = 'Fluxbox menu editor'


# Define names of fields on the right pane
# They may change because, for example submenu can
# set its child's caption in "command" -field
# 3rd field is wheter to show a "folder" (0) or a "file" (1) -dialog
itemInfoCaptions = [['Name:', 'Command:', 1],
                    ['Title:', 'Command:', 1],
                    ['Name:', 'Submenu title:', 0],
                    ['Name:', 'Path:', 0],
                    ['Path:', 'Command:', 0]]


# Define a list of possible types of items
# Default types are: begin, end and submenu. They are handled automagically
# Others are items and are defined here.
# 1st item is theone in menufile, 2nd is what is shown in combobox
# 3rd is right pane's labels' texts, 4th is active (changeable) fields
# Fields are: 0x01 = name, 0x02 = command, 0x04 = type and 0x08 = icon
# And 0 = not editable, 1 = editable

possibleItemTypes = [['exec', 'exec: Application', 0, 0xFF],
                     ['exit', 'exit: Shutdown fluxbox', 0, 0x0D],
                     ['include', 'include: Include another menu', 3, 0xFF],
                     ['nop', 'nop: No-operation', 0, 0x05],
                     ['separator', 'separator: Separator', 0, 0x04],
                     ['style', 'style: Style', 3, 0xFF],
                     ['stylesdir', 'stylesdir: Directory of styles', 4, 0x0D],
                     ['stylesmenu', 'stylesmenu: Stylemenu', 3, 0xFF],
                     ['reconfig', 'reconfig: Reconfigure', 0, 0x0D],
                     ['restart', 'restart: Restart WM', 0, 0xFF],
                     ['config', 'config: Configuration menu', 0, 0x0D],
                     ['wallpaper', 'wallpaper: Wallpaper menu', 3, 0xFF],
                     ['workspaces', 'workspaces: List of workspaces', 0, 0x05],
                     ['begin', 'begin: Beginning of the menu (static)', 1, 0x01],
                     ['submenu', 'submenu: Submenu (static)', 2, 0xB],
                     ['comment', '#: Comment', 0, 0x00]]

defaultMenus = ['~/.fluxbox/menu',
                '/usr/local/share/fluxbox/menu',
                '/usr/share/fluxbox/menu',
                '/usr/local/fluxbox/menu']


# Default preferences
saveOriginal = True
overwriteOriginal = False
saveBackup = True
saveBackupBeforeGenerating = True
deleteBackup = True

useIcons = True
useOnlyXpm = False
iconPaths = ['/usr/share/icons/',
             '~/.icons/']
generateDebian = False
generateDefault = False
generateExternal = True
externalGenerator = 'fluxbox-generate_menu'



class appgui:
    def __init__(self):

        """The main fluxMenu window will show"""
        
        gladefile="project1.glade"
        windowname="window1"
        self.wTree=gtk.glade.XML (gladefile,windowname)
#        self.set_geometry_hints(min_width = 300)

        self.window = self.wTree.get_widget("window1")
        self.typeBox = self.wTree.get_widget("typebox")
        self.typeLabel = self.wTree.get_widget("typelabel")
        self.treeview = self.wTree.get_widget("treeview1")
        self.nameEntry = self.wTree.get_widget("nameentry")
        self.commandEntry = self.wTree.get_widget("commandentry")
        self.commandButton = self.wTree.get_widget("commandbutton")
        self.nameLabel = self.wTree.get_widget("namelabel")
        self.iconButton = self.wTree.get_widget("iconbutton")
        self.iconIcon = self.wTree.get_widget("icon")
        self.commandLabel = self.wTree.get_widget("commandlabel")
        self.errorLabel = self.wTree.get_widget("errorlabel")

        self.enable_fields(0x00)

        # Disable (unusable) toolbar items
        self.enable_toolbar(False, False)      
#       self.wTree.get_widget("preferencesbutton").set_sensitive(False)
        self.wTree.get_widget("generatebutton").set_sensitive(False)
        self.wTree.get_widget("sortbutton").set_sensitive(False)


        handler = {"on_save1_activate":self.save_clicked,
                   "on_save_as1_activate":self.save_as_clicked,
                   "on_open1_activate":self.open_menu,
                   "on_new1_activate":self.new_menu,
                   "on_undo1_activate":self.undo_clicked,
                   
                   "on_deletebutton_clicked":self.delete_item,
                   "on_submenubutton_clicked":self.create_submenu,
                   "on_itembutton_clicked":self.create_item,
                   "on_separatorbutton_clicked":self.create_separator,
                   "on_preferencesbutton_clicked":self.preferences_dialog,
                   
                   "on_commandbutton_clicked":self.commandbutton_clicked,
 
                   "on_typebox_changed":self.typebox_changed,
                   "on_treeview1_cursor_changed":self.treeview_changed,
                   "on_info_changed":self.info_changed,
                   "on_quit1_activate":(gtk.main_quit),
                   "on_quit_clicked":(gtk.main_quit),
                   "on_window1_destroy":(gtk.main_quit)}
        
        self.wTree.signal_autoconnect (handler)


        # Prepare the "type" -combobox for use
        self.prepare_type_combobox()
        # And the treeview
        self.prepare_treeview()

        # Read the menu file and fill the treeview
        # Try to find a default menu
        self.menuFile = ''
        for fileName in defaultMenus:
            menu = handleMenu.read_menu(expanduser(fileName))
            if menu: 
                self.menuFile = expanduser(fileName)
                self.fill_treeview(menu)
                break

        # If a menu was found and 'save original' is set
        # try to do a backup (overwrite as in 'overwrite original')
        if menu:
            if saveOriginal: handleMenu.backup_menu(self.menuFile, '.original', overwriteOriginal)

            # Set title for window according to filename...
            self.window.set_title(self.menuFile + ' - ' + windowTitle)


        self.oldType = 0

        return


# All preparation -functios

    def prepare_type_combobox(self):
        self.typeList = gtk.ListStore(str)
        cell = gtk.CellRendererText()
        self.typeBox.set_model(self.typeList)
        self.typeBox.pack_start(cell, True)
        self.typeBox.add_attribute(cell, 'text', 0)  

        for itemType in possibleItemTypes:
            iter = self.typeList.append((itemType[1],))
            self.typeList.set(iter)

        return

    def prepare_treeview(self):
        self.treemodel=gtk.TreeStore(gobject.TYPE_STRING,
                                     gobject.TYPE_STRING,
                                     gobject.TYPE_STRING,
                                     gobject.TYPE_STRING)
        self.treeview.set_model(self.treemodel)

        renderer=gtk.CellRendererText()
        column=gtk.TreeViewColumn("Item", renderer, text=0)
        column.set_resizable(True)
        self.treeview.append_column(column)

        return


    def fill_treeview(self, menu):
        model = self.treemodel
        iter = None
        for item in menu:
            if(item[0].lower() == 'begin'):
                iter = self.insert_row(model, None, item[1], item[2], item[3], item[0])
            elif(item[0].lower() == 'submenu'):
                if not iter: break
                iter = self.insert_row(model, iter, item[1], item[2], item[3], item[0])
            elif(item[0].lower() == 'end'):
                if not iter: break
                iter = model.iter_parent(iter)
            elif(item[0].lower() == 'separator'):
                if not iter: break
                self.insert_row(model, iter, '--------', item[2], item[3], item[0])
            else:
                if not iter: break
                self.insert_row(model, iter, item[1], item[2], item[3], item[0])

        # Expand the root -level of the menu
        # Changing 2nd parameter to True will expand whole menu
        # (Or changing function to "expand_all()"
        self.treeview.expand_row('0', False)

        return
    
# Call backs begin here 

    def new_menu(self, widget):
        # Clear the treeview and that's it
        model = self.treeview.get_model()
        model.clear()

        # Also it could be wise to create a very basic tree, begin and exit are enough ^^
        iter = self.insert_row(model, None, 'Fluxbox', '', '', 'begin')
        self.insert_row(model, iter, 'Exit fluxbox', '', '', 'exit')

        # Expand the menu
        self.treeview.expand_row('0', False)

        self.menuFile = ''
        return


    def open_menu(self, widget):
        dialog = gtk.FileChooserDialog("Open menu...",
                                        self.window ,gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_CANCEL)

        filter = gtk.FileFilter()
        filter.set_name("Fluxbox menu")
        filter.add_pattern("menu")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.treeview.get_model().clear()
            self.menuFile = dialog.get_filename()
            menu = handleMenu.read_menu(self.menuFile)
            self.fill_treeview(menu)
            self.window.set_title(self.menuFile + ' - ' + windowTitle)
            dialog.destroy()
        elif response == gtk.RESPONSE_CANCEL:
            #print 'Closed, no files selected'
            dialog.destroy()

        return


    def save_clicked(self, widget):
        # Save the menu, call handleMenu -> save
        if self.menuFile:
            menu = self.serialize_menu()

            # Save a backup if it is enabled
            if saveBackup: handleMenu.backup_menu(self.menuFile, '.bck', True)

            handleMenu.save_menu(menu, self.menuFile, True)
        else:
            # Call save as -function to get the new filename
            print 'No menu-file'

        return


    def save_as_clicked(self, widget):
        dialog = gtk.FileChooserDialog("Save menu as...",
                                        self.window, gtk.FILE_CHOOSER_ACTION_SAVE,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_CANCEL)
        dialog.set_current_name("menu")

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            menufile = dialog.get_filename()
            isAlready = isfile(menufile)
            answer = None

            if isAlready:
                message = gtk.MessageDialog(dialog, 0, gtk.MESSAGE_QUESTION, 
                                            gtk.BUTTONS_YES_NO, "File %s exists. Overwrite?" %menufile)
                answer = message.run()
                message.destroy()

            if not isAlready or answer == gtk.RESPONSE_YES:
                self.menuFile = dialog.get_filename()
                self.window.set_title(self.menuFile + ' - ' + windowTitle)
                menu = self.serialize_menu()
                handleMenu.save_menu(menu, self.menuFile, True)

        dialog.destroy()

        return


    def undo_clicked(self, widget):
        # Copy menu.bck over menu and reload it.
        # TODO: Fix this.
        if not isfile(self.menuFile + '.bck'): return
        try:
            shutil.copyfile(self.menuFile + '.bck', self.menuFile)
        except:
            return
        
        self.treeview.get_model().clear()
        menu = handleMenu.read_menu(dialog.get_filename())
        self.fill_treeview(menu)
        return


    def delete_item(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        if iter:
            result = model.remove(iter)

            # The selection will get lost when removing an item
            # So disable the toolbar
            self.enable_toolbar(False, False)

        # Check if last item of the menu was deleted
        # (shouldn't be possible, but)
        if not model.get_iter('0'):
            self.menuFile = ''
        return


    def create_submenu(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        if model.get_value(iter, 3) == 'submenu' or model.get_value(iter, 3) == 'begin':
            newIter = model.insert_after(iter, None, ['New submenu', '', '', 'submenu'])
            self.treeview.expand_row(model.get_path(iter), False)
        else:
            newIter = model.insert_after(None, iter, ['New submenu', '', '', 'submenu'])

        # I don't know if this is a good option, but add one "new item" under 
        # the just created submenu
        # First select the submenu we created
        treeselection.select_iter(newIter)

        # Then create a new item under that
        model.insert_after(newIter, None, ['New item', '', '', 'exec'])

        return


    def create_item(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        if model.get_value(iter, 3) == 'submenu' or model.get_value(iter, 3) == 'begin':
            newIter = model.prepend(iter, ['New item', '', '', 'exec'])
            self.treeview.expand_row(model.get_path(iter), False)
        else:
            newIter = model.insert_after(model.iter_parent(iter), iter, ['New item', '', '', 'exec'])

        # Select the item just created
        treeselection.select_iter(newIter)

        return


    def create_separator(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        if model.get_value(iter, 3) == 'submenu' or model.get_value(iter, 3) == 'begin':
            newIter = model.prepend(iter, ['', '', '', 'separator'])
            self.treeview.expand_row(model.get_path(iter), False)
        else:
            newIter = model.insert_after(model.iter_parent(iter), iter, ['', '', '', 'separator'])
       
        # Select the separator that was created
        treeselection.select_iter(newIter)

        return


#    def icon_clicked(self,widget):
#        windowname2 = "dialog1"
#        gladefile = "project1.glade"
#        self.wTree2 = gtk.glade.XML(gladefile, windowname2)


    def commandbutton_clicked(self, widget):
        filter = gtk.FileFilter()


        # Check whether it should be "select file" or "select folder" -dialog
        model = self.typeBox.get_model()
        index = self.typeBox.get_active()

        itemLabels = possibleItemTypes[index][2]
        dialogStyle = itemInfoCaptions[itemLabels][2]

        if dialogStyle == 0:
            dialogTitle = "Choose folder..."
            dialogType = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER
        else:
            dialogTitle = "Choose an application..."
            dialogType = gtk.FILE_CHOOSER_ACTION_OPEN


        dialog = gtk.FileChooserDialog(dialogTitle,
                                        self.window, dialogType,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_CANCEL)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.commandEntry.set_text(dialog.get_filename())
            dialog.destroy()
        elif response == gtk.RESPONSE_CANCEL:
            #print 'Closed, no files selected'
            dialog.destroy()

        return



    def typebox_changed(self, widget):
        model = self.typeBox.get_model()
        index = self.typeBox.get_active()

        if index > -1:
            availableFields = possibleItemTypes[index][3]

            # If user selected a field what is marked as not editable,
            # don't let user select it but revert to the old one

            if self.oldType != index:
                if availableFields & 0x04:
                    self.enable_fields(availableFields)

                    # Change the labels on right pane
                    self.change_labels(possibleItemTypes[index][2])

                    # Clear possible error and set old type to be the current one
                    self.errorLabel.set_text('')
                    self.oldType = index
                else:
                    # Revert to the previous selected type
                    # and display an error
                    self.typeBox.set_active(self.oldType)
                    self.errorLabel.set_text("You cannot change item's type to a static type!")
                    index = self.oldType

            # Make the change to the treeview
            treeselection = self.treeview.get_selection()
            (model, iter) = treeselection.get_selected()

            # Store new type into the selection
            # Note: unnecessary fields (if no icon etc) will be handled
            # when saving the menu
            model.set_value(iter, 3, possibleItemTypes[index][0])

        return


    def treeview_changed(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        # Fill values into their fields on the right pane
        name = model.get_value(iter, 0)
        self.nameEntry.set_text(name)
        command = model.get_value(iter, 1)
        self.commandEntry.set_text(command)

        # The type is a little bit harder
        type = model.get_value(iter, 3)
        for itemType in possibleItemTypes:
            if itemType[0].lower() == type:

                # NOTE: Must be in this order, because typebox_changed
                # will be called IMMEDIATELY after set_active
                self.oldType = possibleItemTypes.index(itemType)
                self.typeBox.set_active(possibleItemTypes.index(itemType))

                # Change the labels on right pane
                self.change_labels(itemType[2])

                # If the item selected from the menu does not allow
                # changing its type, then disable the type-field
                self.enable_fields(itemType[3])

                # Clear the error-label and set the oldtype to current one
                self.errorLabel.set_text('')

                # Add a correct icon in the icon-button if an icon is specified
                iconFile = model.get_value(iter, 2)
                if iconFile:
                    self.iconIcon.set_from_file(iconFile)
                else:
                    self.iconIcon.set_from_stock(gtk.STOCK_NO, gtk.ICON_SIZE_DIALOG)

                # Disable toolbar if 'begin' is enabled
                if type == 'begin': self.enable_toolbar(True, False)
                else: self.enable_toolbar(True, True)

        return


    def info_changed(self, widget):
        # Update changes to treeview

        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        if widget == self.commandEntry:
            model.set_value(iter, 1, self.commandEntry.get_text())
        elif widget == self.nameEntry:
            model.set_value(iter, 0, self.nameEntry.get_text())

        return

#    def about1_activate(self,widget):
#        windowname2="window2"
#        gladefile="project3.glade"
#        self.wTree2=gtk.glade.XML (gladefile,windowname2)

    def change_labels(self, nameIndex):
        self.nameLabel.set_text(itemInfoCaptions[nameIndex][0])
        self.commandLabel.set_text(itemInfoCaptions[nameIndex][1])
        return

    def insert_row(self, model, parent, first, second, third, fourth):
        myiter = model.insert_before(parent, None)
        model.set_value(myiter, 0, first)
        model.set_value(myiter, 1, second)
        model.set_value(myiter, 2, third)
        model.set_value(myiter, 3, fourth)
        return myiter

    def enable_fields(self, fields):
        self.nameEntry.set_sensitive(fields & 0x01)
        self.nameLabel.set_sensitive(fields & 0x01)

        self.commandEntry.set_sensitive(fields & 0x02)
        self.commandLabel.set_sensitive(fields & 0x02)
        self.commandButton.set_sensitive(fields & 0x02)

        self.typeBox.set_sensitive(fields & 0x04)
        self.typeLabel.set_sensitive(fields & 0x04)

        self.iconButton.set_sensitive(fields & 0x08)
        return



    def enable_toolbar(self, enable_add, enable_modify):
        self.wTree.get_widget("deletebutton").set_sensitive(enable_modify)

        self.wTree.get_widget("submenubutton").set_sensitive(enable_add)
        self.wTree.get_widget("itembutton").set_sensitive(enable_add)
        self.wTree.get_widget("separatorbutton").set_sensitive(enable_add)
        return


    # Serialize the menu from treeview to table
    def serialize_menu(self):
        treeselection = self.treeview.get_selection()
        model = self.treeview.get_model()
        iter = model.get_iter('0')

        menu = []

        serializeMenu = True
        while serializeMenu:
            itemType = model.get_value(iter, 3)
            itemName = model.get_value(iter, 0)
            itemCommand = model.get_value(iter, 1)
            itemIcon = model.get_value(iter, 2)

            menu.append([itemType, itemName, itemCommand, itemIcon])

            newIter = model.iter_children(iter)
            if newIter: iter = newIter
            else:
                newIter = model.iter_next(iter)
                if newIter: iter = newIter
                else:
                    # This loop goes up the tree until it finds an item
                    # with next_item or the tree ends.

                    goUp = True
                    while goUp:

                        # Get the parent's iter
                        # If there is no parent, end of menu has been reached
                        newIter = model.iter_parent(iter)
                        if not newIter:
                            goUp = False
                            serializeMenu = False
                        else:
                            menu.append(['end', '', '', ''])

                        # We do not want to parse same tree again
                        # So if there is no next item, will continue going up
                        if newIter: iter = model.iter_next(newIter)

                        if iter: goUp = False
                        else: iter = newIter
        return menu



# Other dialogs here, maybe they could be in separate file?
# Could they still use those global variables?
    def preferences_dialog(self, widget):
        gladefile = "project1.glade"
        window2 = "preferences"
        self.wTree2 = gtk.glade.XML(gladefile, window2)

        # Messagehandlers for this window
        handler = {"on_checkbutton2_toggle":self.original_toggled,
                   "on_checkbutton6_toggle":self.icon_toggled,
                   "on_okbutton2_clicked":self.preferences_ok,
                   "on_cancelbutton2_clicked":self.preferences_cancel}

        self.wTree2.signal_autoconnect(handler)

        return

    def original_toggled(self, widget):
        self.wTree2.get_widget("checkbutton5").set_sensitive(self.wTree2.get_widget("checkbutton2").get_value())
        return

    def icon_toggled(self, widget):
        print "Shit"
        self.wTree2.get_widget("checkbutton5").set_sensitive(self.wTree2.get_widget("checkbutton2").get_value())
        return

    def preferences_ok(self, widget):
        self.wTree2.get_widget("preferences").destroy()
        return

    def preferences_cancel(self, widget):
        self.wTree2.get_widget("preferences").destroy()
        return
        

app=appgui()
gtk.main()   
