# Copyright (c) 2013 Martin Abente Lahaye. - martin.abente.lahaye@gmail.com
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301 USA.

from grestful.object import Object
from grestful.decorators import asynchronous
from grestful.decorators import check_is_created
from grestful.decorators import check_is_not_created


class Paste(Object):

    CREATE_URL = 'http://fpaste.org/'
    SHOW_URL = 'http://fpaste.org/api/json/%s'
    LIST_URL = 'http://fpaste.org/~%s/api/json/all/%d'

    @asynchronous
    @check_is_not_created
    def create(self, data, lang='text', project=''):
        params = [
            ('paste_data', data),
            ('paste_lang', lang),
            ('paste_project', project),
            ('api_submit', 'true'),
            ('mode', 'json')]

        self._post(self.CREATE_URL, params)

    @asynchronous
    @check_is_created
    def show(self):
        self._get(self.SHOW_URL % self.id)

    @asynchronous
    def list(self, project, page):
        self._get(self.LIST_URL % (project, page))

    def _hook_header(self, params=None):
        return ['Expect:']

    def _hook_id(self, info):
        if isinstance(info, dict) and \
            'result' in info and \
                'id' in info['result']:
            self.id = str(info['result']['id'])
