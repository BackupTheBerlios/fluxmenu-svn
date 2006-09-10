#!/usr/bin/env python
# Copyright 2005 Lauri Peltonen
# zan@mail.berlios.de
# This is fluxMenu that is based on fluxStyle because I don't know any python


"""FluxMenu
A class wrapper for working with and editing the fluxbox menu

Orignal Author Lauri Peltonen  zan@mail.berlios.de
Bug fixes, additional support: Michael Rice  errr@errr-online.com

Released under GPL v2.

TODO:

* Fix the drag 'n' drop so that dropping over items (anything but submenu or begin)
  wouldn't be possible (needs to write some kind of copy_tree -function)

* Menu and submenu sorting (by name?)

* Icons next to name in treeview.

* Maybe a little smarter default menu on File -> New. Like the default menu on fluxbox.

* A context menu for right mouse button on treeview, to show things like "delete" and "add->exec"?
  It should also have items like "Recursive visible" and "recursive hide", better names though

* Maybe some list similar to denu's showing all installed programs (freedesktop?) allowing faster
  selection of programs and their icons etc, but still that select-a-file-by-hand should be there 
  like it is now.                            

* Buttons for duplicating an entry and also for moving an entry up and down. Cut'n'paste? Also
  external drag and drop from f.e. filemanager could be cool.
"""

import sys
import gtk
import gtk.glade

if gtk.pygtk_version < (2,3,90):
    #we do have gtk so lets tell them via gui that they need to update pygtk
    #maybe we should add a 'would you like to open a browser to pygtk.org ??
    message = """PyGtk 2.3.90 or later required for this program it is reccomended that you get pygtk 2.6 or newer for best results."""
    m = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, \
           gtk.BUTTONS_NONE, message)
    m.add_button(gtk.STOCK_OK, gtk.RESPONSE_CLOSE)
    response = m.run()
    m.hide()
    if response == gtk.RESPONSE_CLOSE:
        m.destroy()
        raise SystemExit

import os
import gobject
import time
from os.path import isfile,expanduser
from fluxmenu import handleMenu,findIcons,parseConfig
from fluxmenu.iconSelector import iconSelector

#import preferences
#import selectIcon
#from selectIcon import selectIcon

#now we have both gtk and gtk.glade imported
#Also, we know we are running GTK v2

programPath = os.path.abspath(os.path.dirname(sys.argv[0])) + '/'
gladefile = programPath + "glade/fluxMenu.glade"

windowTitle = 'Fluxbox menu editor'


"""
Define names of fields on the right pane
They may change because, for example submenu can
set its child's caption in "command" -field
3rd field is wheter to show a "folder" (0) or a "file" (1) -dialog
"""
itemInfoCaptions = [['Name:', 'Command:', 1],
                    ['Title:', 'Command:', 1],
                    ['Name:', 'Submenu title:', 0],
                    ['Name:', 'Path:', 0],
                    ['Path:', 'Command:', 0]]


"""
Define a list of possible types of items
Default types are: begin, end and submenu. They are handled automagically
Others are items and are defined here.
1st item is theone in menufile, 2nd is what is shown in combobox
3rd is right pane's labels' texts, check itemInfoCaptions variable
4th is active (changeable) fields
Fields are: 0x01 = name, 0x02 = command, 0x04 = type and 0x08 = icon
And 0 = not editable, 1 = editable
More info:
  0x01 = only name is editable
  0x02 = only command is editable
  0x03 (0x01 + 0x02) = both command and name are editable
  0x04 = type can be changed
  0x05 (0x01 + 0x04) = type can be changed and name is editable
  0x06 (0x02 + 0x04) = type can be changed, command can be edited
  0x07 (0x01 + 0x02 + 0x04) = type can be changed, name and command can be edited
  etc etc
"""

possibleItemTypes = [['exec', 'exec: Application', 0, 0xFF],
                     ['exit', 'exit: Shutdown fluxbox', 0, 0x0D],
                     ['include', 'include: Include another menu', 3, 0x01],
                     ['nop', 'nop: No-operation', 0, 0x05],
                     ['separator', 'separator: Separator', 0, 0x04],
                     ['style', 'style: Style', 3, 0xFF],
                     ['stylesdir', 'stylesdir: Directory of styles', 4, 0x0D],
                     ['stylesmenu', 'stylesmenu: Stylemenu', 3, 0xFF],
                     ['reconfig', 'reconfig: Reconfigure', 0, 0x0D],
                     ['restart', 'restart: Restart WM', 0, 0xFF],
                     ['config', 'config: Configuration menu', 0, 0x0D],
                     ['commanddialog', 'commanddialog: Internal command', 0, 0x0D],
                     ['wallpapers', 'wallpapers: Wallpaper list', 4, 0x05],
                     ['workspaces', 'workspaces: List of workspaces', 0, 0x05],
                     ['begin', 'begin: Beginning of the menu (static)', 1, 0x01],
                     ['submenu', 'submenu: Submenu (static)', 2, 0xB],
                     ['comment', '#: Comment', 0, 0x01]]

defaultMenus = ['~/.fluxbox/menu',\
                '/usr/local/share/fluxbox/menu',\
                '/usr/share/fluxbox/menu',\
                '/usr/local/fluxbox/menu']


# Default preferences
saveOriginal = True
overwriteOriginal = False
saveBackup = True
saveBackupBeforeGenerating = True
deleteBackup = True

useIcons = True
useOnlyXpm = False
iconPaths = ['/usr/share/icons/',\
             '~/.icons/',\
             '/usr/share/pixmaps/']
externalGenerator = 'fluxbox-generate_menu'
generatedFile = '~/.fluxbox/menu'

settingsFile = '~/.fluxbox/fluxMenu.rc'



class fluxMenu:
    
    def main(self):
        gtk.main()

    def __init__(self):

        """The main fluxMenu window will show"""
        
        windowname="window1"
        self.wTree=gtk.glade.XML (gladefile,windowname)
        #self.set_geometry_hints(min_width = 300)
 
        self.window = self.wTree.get_widget("window1")
        self.typeBox = self.wTree.get_widget("typebox")
        self.typeLabel = self.wTree.get_widget("typelabel")
        self.treeview = self.wTree.get_widget("treeview1")
        self.nameEntry = self.wTree.get_widget("nameentry")
        self.commandEntry = self.wTree.get_widget("commandentry")
        self.commandButton = self.wTree.get_widget("commandbutton")
        self.nameLabel = self.wTree.get_widget("namelabel")
        self.iconButton = self.wTree.get_widget("iconbutton")
        self.clearIconButton = self.wTree.get_widget("clearicon")
        self.iconIcon = self.wTree.get_widget("icon")
        self.commandLabel = self.wTree.get_widget("commandlabel")
        self.errorLabel = self.wTree.get_widget("errorlabel")
        self.iconSelectorButton = self.wTree.get_widget("showiconselector")
        self.tooltips = gtk.Tooltips()

        self.__enable_fields__(0x00)

        # Disable (unusable) toolbar items
        self.__enable_toolbar__(False, False)      
        #self.wTree.get_widget("preferencesbutton").set_sensitive(False)
        #self.wTree.get_widget("generatebutton").set_sensitive(False)
        self.wTree.get_widget("sortbutton").set_sensitive(False)

        self.pmenu=gtk.glade.XML(gladefile, "popupmenu")
        self.popupMenu=self.pmenu.get_widget("popupmenu")
        self.openthis=self.pmenu.get_widget("open_this_file1")
        self.showall=self.pmenu.get_widget("show_all1")
        self.show=self.pmenu.get_widget("show1")
        self.hide=self.pmenu.get_widget("hide1")
        self.openthis.set_sensitive(False)
        self.showall.set_sensitive(False)

        handler = {"on_save1_activate":self.__save_clicked__,
                   "on_save_as1_activate":self.__save_as_clicked__,
                   "on_open1_activate":self.__open_menu__,
                   
                   "on_new1_activate":self.__new_menu__,
                   "on_undo1_activate":self.__undo_clicked__,
                   
                   "on_deletebutton_clicked":self.__delete_item__,
                   "on_submenubutton_clicked":self.__create_submenu__,
                   "on_itembutton_clicked":self.__create_item__,
                   "on_separatorbutton_clicked":self.__create_separator__,
                   "on_generatebutton_clicked":self.__generatebutton_clicked__,
                   "on_fill_icons1_clicked":self.__fill_icons__,
                   "on_preferencesbutton_clicked":self.__preferences_dialog__,
                   "on_preferences1_activate":self.__preferences_dialog__,

                   "on_commandbutton_clicked":self.__commandbutton_clicked__,
                   "on_icon_clicked":self.__icon_clicked__,
                   "on_showiconselector_clicked":self.__iconselector_clicked__,
                   "on_clearicon_clicked":self.__clearicon_clicked__,
 
                   "on_include1_activate":self.__include_clicked__,
                   "on_duplicate1_activate":self.__duplicate_clicked__,
                   "on_insert1_activate":self.__insert_clicked__,
                   "on_show1_activate":self.__show_clicked__,
                   "on_show_all1_activate":self.__showall_clicked__,
                   "on_hide1_activate":self.__hide_clicked__,
                   "on_open_this_activate":self.__open_selected__,

                   "on_typebox_changed":self.__typebox_changed__,
                   "on_treeview1_cursor_changed":self.__treeview_changed__,
                   "on_treeview1_popup_menu":self.__treeview_menu__,
                   "on_info_changed":self.__info_changed__,
                   "on_about1_activate":self.__about1_activate__,
                   "on_quit1_activate":(gtk.main_quit),
                   "on_quit_clicked":(gtk.main_quit),
                   "on_window1_destroy":(gtk.main_quit)}
        
        self.wTree.signal_autoconnect (handler)
        self.pmenu.signal_autoconnect (handler)


        # Prepare the "type" -combobox for use
        self.__prepare_type_combobox__()
        # And the treeview
        self.__prepare_treeview__()

        # Read the menu file and fill the treeview
        # Try to find a default menu
        self.menuFile = ''
        for fileName in defaultMenus:
            menu = handleMenu.read_menu(expanduser(fileName))
            if menu: 
                self.menuFile = expanduser(fileName)
                self.__fill_treeview__(menu)
                break

        # If a menu was found and 'save original' is set
        # try to do a backup (overwrite as in 'overwrite original')
        if menu:
            if saveOriginal:
                if handleMenu.backup_menu(self.menuFile, '.original', overwriteOriginal) == 0:
                    warning = gtk.MessageDialog(self.window, 0, gtk.MESSAGE_WARNING,
                                            gtk.BUTTONS_OK, "Could not save original menu to menu.original!\r\nProbably permission problem, do you have write access?")
                    warning.run()
                    warning.destroy()

            # Set title for window according to filename...
            self.window.set_title(self.menuFile + ' - ' + windowTitle)


        self.oldType = 0

        # Load settings from config
        self.__load_config__(expanduser(settingsFile))

        # Create iconselector and load icons into it
        self.iconselector = iconSelector.iconSelector(self.icon_selected)
        if useIcons:
            for path in iconPaths:
                self.iconselector.load_icons(path, True, useOnlyXpm)
        return


# All preparation -functios

    def __load_config__(self, file):
        """Loads config file 'file' and fills the global preferences
        according to values in the config"""

        global saveOriginal
        global overWriteOriginal
        global saveBackup
        global saveBackupBeforeGenerating
        global deleteBackup
        global useIcons
        global useOnlyXpm
        global externalGenerator
        global generatedFile
        global iconPaths

        settings = parseConfig.parse_file(file)
        #print settings

        if settings:
            if settings.has_key('SAVE_ORIGINAL'): saveOriginal = ( settings['SAVE_ORIGINAL'] == ['True'] )
            if settings.has_key('OVERWRITE_ORIGINAL'): overWriteOriginal = ( settings['OVERWRITE_ORIGINAL'] == ['True'] )
            if settings.has_key('SAVE_BACKUP'): saveBackup = ( settings['SAVE_BACKUP'] == ['True'] )
            if settings.has_key('SAVE_BACKUP_BEFORE_GENERATING'): saveBackupBeforeGenerating = ( settings['SAVE_BACKUP_BEFORE_GENERATING'] == ['True'] )
            if settings.has_key('DELETE_BACKUP'): deleteBackup = ( settings['DELETE_BACKUP'] == ['True'] )
            if settings.has_key('USE_ICONS'): useIcons = ( settings['USE_ICONS'] == ['True'] )
            if settings.has_key('USE_ONLY_XPM'): useOnlyXpm = ( settings['USE_ONLY_XPM'] == ['True'] )

            if settings.has_key('ICON_PATH'): iconPaths = settings['ICON_PATH']
            if settings.has_key('GENERATOR'): externalGenerator = settings['GENERATOR'][0]
            if settings.has_key('GENERATED_FILE'): generatedFile = settings['GENERATED_FILE'][0]

            return True
        else: return False


    def __prepare_type_combobox__(self):
        """Prepare the "type" -combobox for use"""
        self.typeList = gtk.ListStore(str)
        cell = gtk.CellRendererText()
        self.typeBox.set_model(self.typeList)
        self.typeBox.pack_start(cell, True)
        self.typeBox.add_attribute(cell, 'text', 0)  

        for itemType in possibleItemTypes:
            iter = self.typeList.append((itemType[1],))
            self.typeList.set(iter)

        return

    def __prepare_treeview__(self):
        self.treemodel=gtk.TreeStore(gobject.TYPE_STRING,
                                     gobject.TYPE_STRING,
                                     gobject.TYPE_STRING,
                                     gobject.TYPE_STRING,
                                     gobject.TYPE_BOOLEAN)
        self.treeview.set_model(self.treemodel)

        renderer=gtk.CellRendererText()
        renderer2=gtk.CellRendererToggle()
        renderer2.set_property("activatable", True)
        renderer2.connect( 'toggled', self.__visible_toggled__, self.treemodel)
        column=gtk.TreeViewColumn("Item", renderer, text=0)
        column2=gtk.TreeViewColumn("Visible", renderer2, active=4)
        column.set_resizable(True)
        self.treeview.append_column(column)
        self.treeview.append_column(column2)
        self.treeview.set_expander_column(column)
        return


    def __fill_treeview__(self, menu):
        model = self.treemodel
        iter = None
        beginhasbeen = False

        if not menu:
            print "Hazardous error: No menu to load!"
            warning = gtk.MessageDialog(self.window, 0, gtk.MESSAGE_WARNING,
                                    gtk.BUTTONS_OK, "Menu file was empty or there was no proper menu, creating a default menu!")
            warning.run()
            warning.destroy()
            self.__new_menu__(None)
            return

        for item in menu:
            if(item[0].lower() == 'begin'):
                if not beginhasbeen:
                    iter = self.__insert_row__(model, None, item[1], item[2], item[3], item[0], item[4])
                    beginhasbeen = True
            elif(item[0].lower() == 'submenu'):
                if not iter: break
                iter = self.__insert_row__(model, iter, item[1], item[2], item[3], item[0], item[4])
            elif(item[0].lower() == 'end'):
                if not iter: break
                iter = model.iter_parent(iter)
            elif(item[0].lower() == 'separator'):
                if not iter: break
                self.__insert_row__(model, iter, '--------', item[2], item[3], item[0], item[4])
            else:
                if not iter:
                    if not beginhasbeen:
                        self.__insert_row__(model, None, item[1], item[2], item[3], item[0], item[4])
                    else: break
                else: self.__insert_row__(model, iter, item[1], item[2], item[3], item[0], item[4])


        # Expand the root -level of the menu
        # Changing 2nd parameter to True will expand whole menu
        # (Or changing function to "expand_all()"
        self.treeview.expand_row('0', False)

        return
    
# Call backs begin here 

    def __new_menu__(self, widget):
        # Clear the treeview and that's it
        model = self.treeview.get_model()
        model.clear()

        # Also it could be wise to create a very basic tree, begin and exit are enough ^^
        iter = self.__insert_row__(model, None, 'Fluxbox', '', '', 'begin', True)
        self.__insert_row__(model, iter, 'xterm', 'xterm', '', 'exec', True)
        self.__insert_row__(model, iter, 'Exit fluxbox', '', '', 'exit', True)

        # Expand the menu
        self.treeview.expand_row('0', False)

        self.menuFile = ''

        # Disable toolbar as the menu is brand new, no item is selected etc
        self.__enable_toolbar__(False, False)

        return


    def __open_menu__(self, widget):
        dialog = gtk.FileChooserDialog("Open menu...",
                                        self.window ,gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        if self.menuFile:
            dialog.set_filename(self.menuFile)

        filter = gtk.FileFilter()
        filter.set_name("Fluxbox menu")
        filter.add_pattern("menu")
        dialog.add_filter(filter)

        filter2 = gtk.FileFilter()
        filter2.set_name("All Files")
        filter2.add_pattern("*")
        dialog.add_filter(filter2)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.treeview.get_model().clear()
            self.menuFile = dialog.get_filename()
            menu = handleMenu.read_menu(self.menuFile)
            self.__fill_treeview__(menu)
            self.menuFile = dialog.get_filename()			# In case the menu was empty
            self.window.set_title(self.menuFile + ' - ' + windowTitle)
            dialog.destroy()
        else:
            #print 'Closed, no files selected'
            dialog.destroy()

        return


    def __open_selected__(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        type = model.get_value(iter, 3)
        if type == "include":
            self.menuFile = expanduser(model.get_value(iter, 0))
            self.treeview.get_model().clear()
            menu = handleMenu.read_menu(self.menuFile)
            self.__fill_treeview__(menu)
            self.window.set_title(self.menuFile + ' - ' + windowTitle)
        return


    def __save_clicked__(self, widget):
        # Save the menu, call handleMenu -> save
        if self.menuFile:
            menu = self.__serialize_menu__()

            # Save a backup if it is enabled
            if saveBackup: 
                if handleMenu.backup_menu(self.menuFile, '.bck', True) != 1:
                    warning = gtk.MessageDialog(self.window, 0, gtk.MESSAGE_WARNING,
                                            gtk.BUTTONS_OK, "Could not save backup to " + self.menuFile + ".bck!\r\nProbably permission problem, do you have write access?")
                    warning.run()
                    warning.destroy()


            handleMenu.save_menu(menu, self.menuFile, True, useIcons)
        else:
            # Call save as -function to get the new filename
            print 'No menu-file, calling save_as'
            self.save_as_clicked(widget)

        return


    def __save_as_clicked__(self, widget):
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
                message = gtk.MessageDialog(self.window, 0, gtk.MESSAGE_QUESTION, 
                                            gtk.BUTTONS_YES_NO, "File %s exists. Overwrite?" %menufile)
                answer = message.run()
                message.destroy()

            if not isAlready or answer == gtk.RESPONSE_YES:
                self.menuFile = dialog.get_filename()
                self.window.set_title(self.menuFile + ' - ' + windowTitle)
                menu = self.__serialize_menu__()
                handleMenu.save_menu(menu, self.menuFile, True, useIcons)

        dialog.destroy()

        return


    def __undo_clicked__(self, widget):
        """Loads the menu.bck, so reverts to last saved backup"""
        if saveBackup:
            if isfile(self.menuFile + '.bck'):
                self.treeview.get_model().clear()
                menu = handleMenu.read_menu(self.menuFile + '.bck')
                self.__fill_treeview__(menu)
            else:
                message = gtk.MessageDialog(self.window, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                             "Cannot revert to last backup: No backup-file (%s.bck)" %self.menuFile)
                message.run()
                message.destroy()
        else:
            message = gtk.MessageDialog(self.window, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK,
                                         "Cannot revert to last backup: Backups are not enabled")
            message.run()
            message.destroy()
     
        return

    def __include_clicked__(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        dialog = gtk.FileChooserDialog("Select menu to include...",
                                        self.window ,gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        if self.menuFile:
            dialog.set_filename(self.menuFile)

        filter = gtk.FileFilter()
        filter.set_name("Fluxbox menu")
        filter.add_pattern("menu")
        dialog.add_filter(filter)

        filter2 = gtk.FileFilter()
        filter2.set_name("All Files")
        filter2.add_pattern("*")
        dialog.add_filter(filter2)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.__insert_row__(model, iter, dialog.get_filename(), "", "", "include", True)
        dialog.destroy()

        return

    def __fill_icons__(self, widget):
        return

    def __duplicate_clicked__(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        return

    def __insert_clicked__(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        return

    def __show_clicked__(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        model.set_value(iter, 4, True)
        return

    def __showall_clicked__(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        (model, iter_child) = treeselection.get_selected()
        return

    def __hide_clicked__(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        model.set_value(iter, 4, False)
        return


    def __delete_item__(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        if iter:
            result = model.remove(iter)
            if result: 
                treeselection.select_iter(iter)
            else:
                # The selection will get lost when removing an item
                # So disable the toolbar
                self.__enable_toolbar__(False, False)

        # Check if last item of the menu was deleted
        # (shouldn't be possible, but)
        try:
            model.get_iter('0')
        except:
            self.menuFile = ''
        return


    def __create_submenu__(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        if model.get_value(iter, 3) == 'submenu' or model.get_value(iter, 3) == 'begin':
            newIter = model.insert_after(iter, None, ['New submenu', '', '', 'submenu', True])
            self.treeview.expand_row(model.get_path(iter), False)
        else:
            newIter = model.insert_after(None, iter, ['New submenu', '', '', 'submenu', True])

        # I don't know if this is a good option, but add one "new item" under 
        # the just created submenu
        # First select the submenu we created
        treeselection.select_iter(newIter)
        self.__treeview_changed__(newIter)
        self.nameEntry.grab_focus()

        # Then create a new item under that
        model.insert_after(newIter, None, ['New item', '', '', 'exec', True])

        return


    def __create_item__(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        if model.get_value(iter, 3) == 'submenu' or model.get_value(iter, 3) == 'begin':
            newIter = model.prepend(iter, ['New item', '', '', 'exec', True])
            self.treeview.expand_row(model.get_path(iter), False)
        else:
            newIter = model.insert_after(model.iter_parent(iter), iter, ['New item', '', '', 'exec', True])

        # Select the item just created
        treeselection.select_iter(newIter)
        self.__treeview_changed__(newIter)
        self.nameEntry.grab_focus()

        return


    def __create_separator__(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        if model.get_value(iter, 3) == 'submenu' or model.get_value(iter, 3) == 'begin':
            newIter = model.prepend(iter, ['--------', '', '', 'separator', True])
            self.treeview.expand_row(model.get_path(iter), False)
        else:
            newIter = model.insert_after(model.iter_parent(iter), iter, ['--------', '', '', 'separator', True])
       
        # Select the separator that was created
        treeselection.select_iter(newIter)
        self.__treeview_changed__(newIter)

        return


    def __icon_clicked__(self,widget):

        if not hasattr (self, 'prevIconPath'):
            self.prevIconPath = os.path.abspath(os.path.dirname(sys.argv[0])) + '/' + 'pixmaps'

        filter = gtk.FileFilter()

        dialogTitle = "Choose an icon..."
        dialogType = gtk.FILE_CHOOSER_ACTION_OPEN

        dialog = gtk.FileChooserDialog(dialogTitle,
                                        self.window, dialogType,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_filename(self.prevIconPath)

        filter.add_pattern("*.xpm")
        if not useOnlyXpm:
            filter.add_pattern("*.png")
            filter.add_pattern("*.jpg")
            filter.add_pattern("*.jpeg")

        dialog.add_filter(filter)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            # got an icon, proceed to attach it
            iconFile = dialog.get_filename()
            if iconFile and iconFile != "":
                self.iconIcon.set_from_file(iconFile)
                self.tooltips.set_tip(self.iconButton, iconFile)

                treeselection = self.treeview.get_selection()
                (model, iter) = treeselection.get_selected()

                model.set_value(iter, 2, iconFile)
                self.prevIconPath = os.path.abspath(iconFile)

                dialog.destroy()

        elif response == gtk.RESPONSE_CANCEL:
            #print 'Closed, no files selected'
            dialog.destroy()

        return

    def __clearicon_clicked__(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        model.set_value(iter, 2, None)
        self.iconIcon.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)
        return

    def __iconselector_clicked__(self, widget):
        command = self.commandEntry.get_text()
        if len(command) == 0:
            command = self.nameEntry.get_text()
            
        path, command = os.path.split(command)

        if len(command) == 0:
            command = "fluxbox"

        command = command.lower()

#        print command

        self.iconselector.dialog(command)
        return

    def __commandbutton_clicked__(self, widget):
        """Check whether it should be "select file" or "select folder" -dialog"""
        
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

    def __generatebutton_clicked__(self, widget):
        confirm = gtk.MessageDialog(self.window, gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, "Are you sure you want to generate a new menu?\r\nWARNING! All modifications after last save will be lost!\r\n\r\nThe file that will be generated is " + generatedFile)
        reallygenerate = confirm.run()
        confirm.destroy()

        if reallygenerate == gtk.RESPONSE_YES:
            pleasewait = gtk.MessageDialog(self.window, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, "Please wait, the menu is being generated ("+externalGenerator+")")
            pleasewait.show()

            backupfine = 1
            if saveBackupBeforeGenerating: 
                backupfine = handleMenu.backup_menu(self.menuFile, '.bck', True)

            if backupfine == 1:
                generated = os.system(expanduser(externalGenerator))
            else:
                warning = gtk.MessageDialog(self.window, 0, gtk.MESSAGE_WARNING,
                                        gtk.BUTTONS_OK, "Saving backup failed so menu was not generated!\r\nProbably a permission problem, do you have write access?")
                warning.run()
                warning.destroy()

                print "BACKUP FAILED!!!"
                generated = 1

            pleasewait.destroy()

            if generated == 0:
                # Generation was succesfull
                self.treeview.get_model().clear()
                menu = handleMenu.read_menu(expanduser(generatedFile))
                self.__fill_treeview__(menu)
                self.window.set_title(self.menuFile + ' - ' + windowTitle)

        return


    def __typebox_changed__(self, widget):
        """If user selected a field what is marked as not editable,
        don't let user select it but revert to the old one Change the 
        labels on right pane Clear possible error and set old type to 
        be the current one """
        model = self.typeBox.get_model()
        index = self.typeBox.get_active()

        if index > -1:
            availableFields = possibleItemTypes[index][3]

            # If user selected a field what is marked as not editable,
            # don't let user select it but revert to the old one

            if self.oldType != index:
                if availableFields & 0x04:
                    self.__enable_fields__(availableFields)

                    # Change the labels on right pane
                    self.__change_labels__(possibleItemTypes[index][2])

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


    def __treeview_changed__(self, widget):
        """Fill values into their fields on the right pane 
        The type is a little bit harder NOTE: Must be in this order, 
        because typebox_changed will be called IMMEDIATELY after 
        set_active """
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        # Fill values into their fields on the right pane
        name = model.get_value(iter, 0)
        self.nameEntry.set_text(name)
        command = model.get_value(iter, 1)
        self.commandEntry.set_text(command)

        # The type is a little bit harder
        type = model.get_value(iter, 3)
        visible = model.get_value(iter, 4)
        for itemType in possibleItemTypes:
            if itemType[0].lower() == type:

                # NOTE: Must be in this order, because typebox_changed
                # will be called IMMEDIATELY after set_active
                self.oldType = possibleItemTypes.index(itemType)
                self.typeBox.set_active(possibleItemTypes.index(itemType))

                # Change the labels on right pane
                self.__change_labels__(itemType[2])

                # If the item selected from the menu does not allow
                # changing its type, then disable the type-field
                self.__enable_fields__(itemType[3])

                # Clear the error-label and set the oldtype to current one
                self.errorLabel.set_text('')

                # Add a correct icon in the icon-button if an icon is specified
                iconFile = model.get_value(iter, 2)
                if iconFile:
                    self.iconIcon.set_from_file(iconFile)
                    self.tooltips.set_tip(self.iconButton, iconFile)
                else:
                    self.iconIcon.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_DIALOG)

                # Disable toolbar if 'begin' is enabled
                if type == 'begin': self.__enable_toolbar__(True, False)
                else: self.__enable_toolbar__(True, True)

                # If selected item is "include", enable the "open this menu" in context
                if type == "include":
                    self.openthis.set_sensitive(True)
                else:
                    self.openthis.set_sensitive(False)

                # Submenu shows the "show all" menuitem
                if type == "submenu":
                    self.showall.set_sensitive(True)
                else:
                    self.showall.set_sensitive(False)

                if visible == True:
                    self.show.set_sensitive(False)
                    self.hide.set_sensitive(True)
                else:
                    self.show.set_sensitive(True)
                    self.hide.set_sensitive(False)


        return


    def __info_changed__(self, widget):
        """Update changes to treeview"""

        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        if not iter or not model:
            return

        if widget == self.commandEntry:
            model.set_value(iter, 1, self.commandEntry.get_text())
        elif widget == self.nameEntry:
            model.set_value(iter, 0, self.nameEntry.get_text())

        return

    def __treeview_menu__(self, widget, event):
        if event.button == 3:
            (press_x, press_y) = event.get_coords()
            press_time = event.get_time()
            
#            context_menu = self.__create_context_menu__()
#            if not context_menu: return
#            context_menu.popup(None, None, None, 3, press_time)

            self.popupMenu.popup(None, None, None, 3, press_time)

        return


    def __visible_toggled__(self,widget, path, model):
        self.treemodel[path][4] = not self.treemodel[path][4]
        return

    def __about1_activate__(self,widget):
        #for the logo to show when its complete you need to edit the fluxMenu.glade
        #file manually and add the full path of where the icon will be installed.
        windowname2="aboutdialog1"
        self.wTree2=gtk.glade.XML (gladefile,windowname2)

    def __change_labels__(self, nameIndex):
        self.nameLabel.set_text(itemInfoCaptions[nameIndex][0])
        self.commandLabel.set_text(itemInfoCaptions[nameIndex][1])
        return

    def __insert_row__(self, model, parent, first, second, third, fourth, fifth):
        myiter = model.insert_before(parent, None)
        model.set_value(myiter, 0, first)
        model.set_value(myiter, 1, second)
        model.set_value(myiter, 2, third)
        model.set_value(myiter, 3, fourth)
        model.set_value(myiter, 4, fifth)
        return myiter


    def __enable_fields__(self, fields):
        self.nameEntry.set_sensitive(fields & 0x01)
        self.nameLabel.set_sensitive(fields & 0x01)

        self.commandEntry.set_sensitive(fields & 0x02)
        self.commandLabel.set_sensitive(fields & 0x02)
        self.commandButton.set_sensitive(fields & 0x02)

        self.typeBox.set_sensitive(fields & 0x04)
        self.typeLabel.set_sensitive(fields & 0x04)

        self.iconButton.set_sensitive(fields & 0x08)
        self.clearIconButton.set_sensitive(fields & 0x08)
        self.iconSelectorButton.set_sensitive(fields & 0x08)

        if not useIcons:
            self.iconButton.set_sensitive(False)
            self.clearIconButton.set_sensitive(False)
            self.iconSelectorButton.set_sensitive(False)

        return

    def __enable_toolbar__(self, enable_add, enable_modify):
        self.wTree.get_widget("deletebutton").set_sensitive(enable_modify)

        self.wTree.get_widget("submenubutton").set_sensitive(enable_add)
        self.wTree.get_widget("itembutton").set_sensitive(enable_add)
        self.wTree.get_widget("separatorbutton").set_sensitive(enable_add)
        return


    def __create_context_menu__(self):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        if not iter or not model:
            return

        type = model.get_value(iter, 3)
        print type

        c_menu = gtk.Menu()
        pask = gtk.MenuItem("_Blub")
        c_menu.attach(gtk.MenuItem("_Testi"), 0, 1, 0, 1)
        c_menu.attach(gtk.MenuItem("Testi_2"), 1, 2, 1, 2)
        c_menu.attach(pask, 2,3,2,3)

        return c_menu


    # Serialize the menu from treeview to table
    def __serialize_menu__(self):
        treeselection = self.treeview.get_selection()
        model = self.treeview.get_model()
        try:
            iter = model.get_iter('0')
        except:
            return []

        menu = []

        serializeMenu = True
        parentVisible = True
        while serializeMenu:
            itemType = model.get_value(iter, 3)
            itemName = model.get_value(iter, 0)
            itemCommand = model.get_value(iter, 1)
            itemIcon = model.get_value(iter, 2)
            
            if parentVisible and model.get_value(iter, 4):
                itemComment = True
            else:
                itemComment = False

	    # TODO: Fix the comment-save
            menu.append([itemType, itemName, itemCommand, itemIcon, itemComment])

            newIter = model.iter_children(iter)
            if newIter:
                if parentVisible: parentVisible = model.get_value(iter, 4)
                iter = newIter
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
                            menu.append(['end', '', '', '', parentVisible])

                            parentParentIter = model.iter_parent(newIter)
                            if parentParentIter:
                                if not model.get_value(newIter, 4) and model.get_value(parentParentIter, 4):
                                    parentVisible = True

                        # We do not want to parse same tree again
                        # So if there is no next item, will continue going up
                        if newIter: iter = model.iter_next(newIter)

                        if iter: goUp = False
                        else: iter = newIter
        return menu


    def icon_selected(self):
        icon = self.iconselector.get_icon()
        if icon:
            treeselection = self.treeview.get_selection()
            if treeselection:
                (model, iter) = treeselection.get_selected()
                if iter:
                    self.iconIcon.set_from_file(icon)
                    self.tooltips.set_tip(self.iconButton, icon)
                    model.set_value(iter, 2, icon)

            # Do something wise here :P
#        print "JO"
        return



# Other dialogs here, maybe they could be in separate file?
# Could they still use those global variables?
    def __preferences_dialog__(self, widget):
        window2 = "preferences"
        self.wTree2 = gtk.glade.XML(gladefile, window2)

        # Messagehandlers for this window
        handler = {"on_checkbutton2_toggled":self.__original_toggled__,
                   "on_checkbutton7_toggled":self.__icon_toggled__,
                   "on_checkbutton8_toggled":self.__xpm_toggled__,
                   "on_okbutton2_clicked":self.__preferences_ok__,
                   "on_cancelbutton2_clicked":self.__preferences_cancel__,
                   "on_preferences_destroy":self.__preferences_cancel__}


        self.wTree2.signal_autoconnect(handler)

        self.__fill_preferences_dialog__()

        return


# These functions are very quick'n'dirty, but I will fix them later
# When I move this whole dialog to another file.
# I just have to get this to work now.

    def __fill_preferences_dialog__(self):
        self.wTree2.get_widget("checkbutton2").set_active(saveOriginal)
        self.wTree2.get_widget("checkbutton3").set_active(not overwriteOriginal)
        self.wTree2.get_widget("checkbutton4").set_active(saveBackup)
        self.wTree2.get_widget("checkbutton5").set_active(saveBackupBeforeGenerating)
        self.wTree2.get_widget("checkbutton6").set_active(deleteBackup)

        self.wTree2.get_widget("checkbutton7").set_active(useIcons)
        self.wTree2.get_widget("checkbutton8").set_active(useOnlyXpm)

        self.pathList = self.wTree2.get_widget("treeview3")
        self.pathstore = gtk.ListStore(str)
        self.pathList.set_model(self.pathstore)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Path", renderer, text=0)
        self.pathList.append_column(column)

        for path in iconPaths:
            self.pathstore.append((path,))

        self.wTree2.get_widget("generatorentry").set_text(externalGenerator)
        self.wTree2.get_widget("generatedfile").set_text(generatedFile)

        return

    def __set_preferences__(self):
        global saveOriginal
        global overWriteOriginal
        global saveBackup
        global saveBackupBeforeGenerating
        global deleteBackup
        global useIcons
        global useOnlyXpm
        global generateExternal
        global externalGenerator
        global generatedFile
        global iconPaths

        saveOriginal = self.wTree2.get_widget("checkbutton2").get_active()
        overWriteOriginal = not self.wTree2.get_widget("checkbutton3").get_active()
        saveBackup = self.wTree2.get_widget("checkbutton4").get_active()
        saveBackupBeforeGenerating = self.wTree2.get_widget("checkbutton5").get_active()
        deleteBackup = self.wTree2.get_widget("checkbutton6").get_active()

        useIcons = self.wTree2.get_widget("checkbutton7").get_active()
        useOnlyXpm = self.wTree2.get_widget("checkbutton8").get_active()


        iconPaths = []
        iter = self.pathstore.get_iter('0')
        while iter:
            iconPaths.append(self.pathstore.get_value(iter, 0))
            iter = self.pathstore.iter_next(iter)


        externalGenerator = self.wTree2.get_widget("generatorentry").get_text()
        generatedFile = self.wTree2.get_widget("generatedfile").get_text()

        preferences = { 'SAVE_ORIGINAL': [saveOriginal],
                        'OVERWRITE_ORIGINAL': [overWriteOriginal],
                        'SAVE_BACKUP': [saveBackup],
                        'SAVE_BACKUP_BEFORE_GENERATING': [saveBackupBeforeGenerating],
                        'DELETE_BACKUP': [deleteBackup],
                        'USE_ICONS': [useIcons],
                        'USE_ONLY_XPM': [useOnlyXpm],
                        'ICON_PATH': iconPaths,
                        'GENERATOR': [externalGenerator],
                        'GENERATED_FILE': [generatedFile] }

        if not useIcons:
            self.iconButton.set_sensitive(False)
            self.clearIconButton.set_sensitive(False)

        return preferences


    def __original_toggled__(self, widget):
        self.wTree2.get_widget("checkbutton3").set_sensitive(self.wTree2.get_widget("checkbutton2").get_active())
        return

    def __icon_toggled__(self, widget):
        self.wTree2.get_widget("checkbutton8").set_sensitive(self.wTree2.get_widget("checkbutton7").get_active())
        if self.wTree2.get_widget("checkbutton7").get_active():
            self.wTree2.get_widget("convertxpm").set_sensitive(self.wTree2.get_widget("checkbutton8").get_active())
        else:
            self.wTree2.get_widget("convertxpm").set_sensitive(False)
        return

    def __xpm_toggled__(self, widget):
#        self.wTree2.get_widget("convertxpm").set_sensitive(self.wTree2.get_widget("checkbutton8").get_active())
        return


    def __preferences_ok__(self, widget):
        preferences = self.__set_preferences__()

        parseConfig.save_config(expanduser(settingsFile), preferences)
        self.wTree2.get_widget("preferences").destroy()

        # Add new paths into iconselector
        self.iconselector.clear_icons()
        if useIcons:
            for path in iconPaths:
                self.iconselector.load_icons(path, True, useOnlyXpm)

        return

    def __preferences_cancel__(self, widget):
        self.wTree2.get_widget("preferences").destroy()
        return


# Main program starts here

# First thing would be to parse command line arguments
# fluxMenu [-rc configfile] [menufile]

# Then load settings from ~/.fluxbox/fluxMenu
# ... load 'em ....

# Launch the app
if __name__ == "__main__":
    app = fluxMenu()
    app.main()

# If backup should be deleted on quit, do it here
# ... delete backup ...
