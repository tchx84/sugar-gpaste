# Copyright (c) 2013 Martin Abente Lahaye. - tch@sugarlabs.org
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import re
from gettext import gettext as _

from gi.repository import GConf
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

from sugar3.graphics import style
from jarabe.webservice import accountsmanager
from cpsection.webaccount.web_service import WebService


class WebService(WebService):

    def __init__(self):
        self._account = accountsmanager.get_account('gpaste')
        self._timeout_id = None

    def _restore_project_name(self):
        client = GConf.Client.get_default()
        project_name = client.get_string(self._account.PROJECT_NAME)
        if project_name:
            self._entry.set_text(project_name)

    def __pressed_start_cb(self, entry, data=None):
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
        self._timeout_id = GLib.timeout_add_seconds(2, self.__save_name_cb)

    def __save_name_cb(self):
        client = GConf.Client.get_default()
        project_name = self._entry.get_text()
        if project_name and self._entry.is_safe():
            client.set_string(self._account.PROJECT_NAME, project_name)

        self._timeout_id = None
        return False

    def get_icon_name(self):
        return 'text-x-generic'

    def config_service_cb(self, widget, event, container):
        separator = Gtk.HSeparator()

        tittle = Gtk.Label(label=_('Fedora Pastebin Service'))
        tittle.set_alignment(0, 0)

        info = Gtk.Label(_("The name will be used to identify all your"
                           " publications at the pastebin web service."))
        info.set_alignment(0, 0)
        info.set_line_wrap(True)

        label = Gtk.Label(_('Project name'))
        label.set_alignment(1, 0.5)
        label.modify_fg(Gtk.StateType.NORMAL,
                        style.COLOR_SELECTION_GREY.get_gdk_color())

        self._entry = SafeEntry()
        self._entry.set_alignment(0)
        self._entry.set_size_request(int(Gdk.Screen.width() / 3), -1)
        self._entry.connect('key-press-event', self.__pressed_start_cb)

        form = Gtk.HBox(spacing=style.DEFAULT_SPACING)
        form.pack_start(label, False, True, 0)
        form.pack_start(self._entry, False, True, 0)

        vbox = Gtk.VBox()
        vbox.set_border_width(style.DEFAULT_SPACING * 2)
        vbox.set_spacing(style.DEFAULT_SPACING)
        vbox.pack_start(info, False, True, 0)
        vbox.pack_start(form, False, True, 0)

        for c in container.get_children():
            container.remove(c)

        container.pack_start(separator, False, False, 0)
        container.pack_start(tittle, False, True, 0)
        container.pack_start(vbox, False, True, 0)
        container.show_all()

        self._restore_project_name()


class SafeEntry(Gtk.Entry):

    def __init__(self):
        Gtk.Entry.__init__(self)
        self._regexp = re.compile('^[a-zA-Z]*$')
        self.connect('changed', self.__check_cb)

    def __check_cb(self, entry, data=None):
        # XXX show something to alert the user, when is not valid
        pass
        
    def is_safe(self):
        try:
            return self._regexp.match(self.get_text())
        except:
            return False
        

def get_service():
    return WebService()
