#!/usr/bin/env python
# vim: noexpandtab:ts=4:sts=4
# Copyright 2005,2006 Michael Rice
# errr@errr-online.com
# installer for fluxMenu
# released under the gpl

"""Fluxmenu is a graphical menu editor written in python using pygtk and glade.
Fluxmenu is for the fluxbox window manager. Many special thanks to Michael Rice
aka errr for his help making this app."""

from distutils.core import setup
from distutils.sysconfig import get_python_lib
import sys,textwrap

ver = get_python_lib() 

m0 = "You are missing gtk bindings for python"

m1 = "You need to install libglade2 http://ftp.gnome.org/pub/GNOME/sources"
m1 += "/libglade/2.0/ or set your PYTHONPATH correctly. try: export "
m1 += "PYTHONPATH=%s/"%(ver)

m2 = "You have an out dated version of pygtk. You will need to update "
m2 += "to 2.4 or newer for best results."

doclines = __doc__.split("\n")

try:
    import gtk
except ImportError:
    print m0
    raise SystemExit

# we now have gtk check for gtk.glade
try:
    import gtk.glade
except ImportError:
    try:
        from fluxstyle import errorMessage
        errorMessage.infoMessage(m1)
    except IomportError:
        m1 = textwrap.wrap(m1,50)
        for l in m1:
          print l
    raise SystemExit
#we have gtk and gtk.glade now check for pygtk version
if gtk.pygtk_version < (2,3,90):
    try:
        from fluxstyle import errorMessage
        errorMessage.infoMessage(m2)
    except ImportError:
        m2 = textwrap.wrap(m2,50)
        for l in m2:
            print l
        raise SystemExit
	  
# if we made it this far all needed dpes should be here..

setup(name='fluxmenu',
	  version='1.0',
	  description=doclines[0],
	  long_description = "\n".join(doclines[1:]),
	  platforms = ["Linux"],
	  author='Lauri Peltonen',
	  author_email='zan@mail.berlios.de',
	  url='http://fluxmenu.berlios.de/',
	  license = 'http://www.gnu.org/copyleft/gpl.html',
	  packages=['fluxmenu','fluxmenu/iconSelector'],
	  data_files=[('/usr/share/fluxmenu-1.0/pixmaps',
		  ['pixmaps/mini-fluxbox5.png']),
	      ('/usr/share/fluxmenu-1.0/glade',['glade/fluxMenu.glade']),
		  ('/usr/share/fluxmenu-1.0/docs',['docs/ChangeLog','docs/TODO'])]
	 )
