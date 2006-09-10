import sys
import os
from os.path import join

import gtk
import gtk.glade

class iconSelector:
    icons = []
    dialog_is_visible = False
    selected_icon = None
    is_selected = False

    def __init__(self, destroyfunction):
        """Init takes 'destroyfuncion' as a parameter
        so that the program calling this can know when
        the use has either selected an icon or clicked cancel"""

        self.on_destroy = destroyfunction

        self.programPath = os.path.abspath(os.path.dirname(sys.argv[0])) + '/'
        gladefile = self.programPath + "glade/fluxMenu.glade"
        windowname = "iconselector"
        self.wTree = gtk.glade.XML (gladefile, windowname)

        self.window = self.wTree.get_widget(windowname)
        self.cancelbutton = self.wTree.get_widget("iconselector_cancel")
        self.iconview = self.wTree.get_widget("iconview2")
        self.match = self.wTree.get_widget("matchentry")

        handler = {"on_iconselector_cancel_clicked": self.__cancel_clicked__,
                   "on_iconselector_find_clicked": self.__match_changed__,
                   "on_iconselector_item_activated": self.__icon_selected__,
                   "on_iconselector_destroy": self.__cancel_clicked__ }

        self.wTree.signal_autoconnect (handler)

        self.model = gtk.ListStore(str, gtk.gdk.Pixbuf, str)
        self.iconview.set_model(self.model)
        self.iconview.set_text_column(0)
        self.iconview.set_pixbuf_column(1)

        self.dialog_is_visible = False
        self.window.hide()
        return


    def load_icons(self, path, recursive, onlyXpm):
        """"Loads icons under the directory 'path'
        and if 'recursive' is True, then under it's
        subdirectories too. if onlyXpm is true, only
        .xpm icons are matched, otherwise all images"""

        print "Loading icons from " + path

        for root, dirs, files in os.walk(path):
            for file in files:
                if onlyXpm:
                    if file.find('.xpm') >= 0:
                        self.icons.append( (join(root, file), file) )
                else:
                    if (file.find('.xpm') >= 0) or \
                       (file.find('.png') >= 0) or \
                       (file.find('.jpg') >= 0) or \
                       (file.find('.jpeg') >= 0):
                        self.icons.append( (join(root, file), file, join(root, file)) )

#        for icon in self.icons:
#            print icon

        return

    def clear_icons(self):
        """Removes all paths added and clears list of icons.
        Used in case the paths are changed so they need to be
        reloaded."""
       
        icons = []
        self.model.clear()

        return

    def dialog(self, iconname):
        """Shows a dialog under the mouse that lists
        all icons that match 'icon' in their name.
        Closes the dialog when the user makes the selection or 
        presses cancel (so this function is blocking!)
        Returns the path of the selected icon or None"""

        if not self.dialog_is_visible:
            self.dialog_is_visible = True
            self.window.set_position(gtk.WIN_POS_MOUSE)
            self.window.show()

        self.model.clear()

        iconname = iconname.lower()

        self.match.set_text(iconname)

        for icon in self.icons:
            if icon[0].lower().find(iconname) >= 0:
                pixbuf = gtk.gdk.pixbuf_new_from_file(icon[0])
                self.model.append([icon[1], pixbuf, icon[0]])

        return None

    def get_icon(self):
        if self.is_selected:
            return self.selected_icon
        else: return None


    def __hide__(self):
        self.dialog_is_visible = False
        self.window.hide()
        return

    def __icon_selected__(self, widget):
        self.is_selected = True
        self.on_destroy()
        return

    def __cancel_clicked__(self, widget):
        self.selected_icon = None
        self.is_selected = False

        self.__hide__()
       
        self.on_destroy()
        return

    def __match_changed__(self, widget):
        matchline = self.match.get_text()

        if (len(matchline) > 0):
#            print matchline
            self.dialog(matchline)
        return

    def __icon_selected__(self, widget, path):
#        print path
        path = self.model.get_iter(path[0])
#        print self.model.get_value(path, 2)
        self.is_selected = True
        self.selected_icon = self.model.get_value(path, 2)
        self.__hide__()
        self.on_destroy()
        return
