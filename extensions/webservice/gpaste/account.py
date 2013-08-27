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

from gettext import gettext as _

from gi.repository import Gtk
from gi.repository import GConf
from gi.repository import GObject

from sugar3.datastore import datastore
from sugar3.graphics.alert import NotifyAlert
from sugar3.graphics.icon import Icon
from sugar3.graphics.menuitem import MenuItem

from jarabe.journal import journalwindow
from jarabe.journal import model
from jarabe.webservice import account, accountsmanager

ACCOUNT_NAME = _('Pastebin')
ACCOUNT_ICON = 'text-x-generic'


class Account(account.Account):

    PROJECT_NAME = "/desktop/sugar/collaboration/gpaste_project_name"

    def __init__(self):
        self.gpaste = accountsmanager.get_service('gpaste')
        self._shared_journal_entry = None

    def get_description(self):
        return ACCOUNT_NAME

    def get_token_state(self):
        return self.STATE_VALID

    def _get_project_name(self):
        client = GConf.Client.get_default()
        return client.get_string(self.PROJECT_NAME)

    def get_shared_journal_entry(self):
        if self._shared_journal_entry is None:
            self._shared_journal_entry = _SharedJournalEntry(self)
        return self._shared_journal_entry


class _SharedJournalEntry(account.SharedJournalEntry):
    __gsignals__ = {
        'transfer-state-changed': (GObject.SignalFlags.RUN_FIRST, None,
                                   ([str])),
    }

    def __init__(self, account):
        self._account = account
        self._alert = None

    def get_share_menu(self, get_uid_list):
        menu = _ShareMenu(self._account, get_uid_list, True)
        self._connect_transfer_signals(menu)
        return menu

    def _connect_transfer_signals(self, transfer_widget):
        transfer_widget.connect('transfer-state-changed',
                                self.__display_alert_cb)

    def __display_alert_cb(self, widget, message):
        if self._alert is None:
            self._alert = NotifyAlert()
            self._alert.props.title = ACCOUNT_NAME
            self._alert.connect('response', self.__alert_response_cb)
            journalwindow.get_journal_window().add_alert(self._alert)
            self._alert.show()
        self._alert.props.msg = message

    def __alert_response_cb(self, alert, response_id):
        journalwindow.get_journal_window().remove_alert(alert)
        self._alert = None


class _ShareMenu(MenuItem):
    __gsignals__ = {
        'transfer-state-changed': (GObject.SignalFlags.RUN_FIRST, None,
                                   ([str])),
    }

    def __init__(self, account, get_uid_list, is_active):
        MenuItem.__init__(self, ACCOUNT_NAME)

        self._account = account
        self.set_image(Icon(icon_name=ACCOUNT_ICON,
                            icon_size=Gtk.IconSize.MENU))
        self.show()
        self._get_uid_list = get_uid_list
        self.connect('activate', self.__share_menu_cb)

    def _get_metadata(self):
        return model.get(self._get_uid_list()[0])

    def _get_data(self):
        data = None

        metadata = self._get_metadata()
        if metadata.get('mime_type', '').startswith('text/'):
            jobject = datastore.get(metadata['uid'])
            with open(jobject.file_path, 'r') as jfile:
                data = jfile.read()

        return data

    def __share_menu_cb(self, menu_item):
        data = self._get_data()

        if data is None:
            self.emit('transfer-state-changed',
                      _('This entry cannot be pasted'))
            return

        self.emit('transfer-state-changed', _('Upload started'))
        paste = self._account.gpaste.Paste()
        paste.connect('completed', self.__completed_cb)
        paste.connect('updated', self.__updated_cb)
        paste.connect('failed', self.__failed_cb)
        paste.create(data, project=self._account.PROJECT_NAME)

    def __updated_cb(self, paste, tdown, down, tup, up):
        message = _('Uploading %d of %d KBs') % (up, tup)
        self.emit('transfer-state-changed', message)

    def __completed_cb(self, paste, info):
        url = paste.CREATE_URL + paste.id

        metadata = self._get_metadata()
        tags = '%s %s' % (metadata.get('tags', ''), url)

        ds_object = datastore.get(metadata['uid'])
        ds_object.metadata['tags'] = tags
        datastore.write(ds_object, update_mtime=False)

        self.emit('transfer-state-changed',
                  _('Successfully pasted to %s') % url)

    def __failed_cb(self, paste, info):
        self.emit('transfer-state-changed',
                  _('Cannot be pasted this time, sorry!'))


def get_account():
    return Account()
