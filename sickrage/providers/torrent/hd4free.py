# coding=utf-8
# Author: Gonçalo M. (aka duramato/supergonkas) <supergonkas@gmail.com>
#
# URL: https://sickrage.ca
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import sickrage
from sickrage.core.caches.tv_cache import TVCache
from sickrage.core.helpers import convert_size
from sickrage.providers import TorrentProvider


class HD4FreeProvider(TorrentProvider):
    def __init__(self):
        super(HD4FreeProvider, self).__init__('HD4Free', 'https://hd4free.xyz', True)

        self.urls.update({
            'search': '{base_url}/searchapi.php'.format(**self.urls)
        })

        self.freeleech = None
        self.username = None
        self.api_key = None
        self.minseed = None
        self.minleech = None

        self.cache = TVCache(self)

    def _check_auth(self):
        if self.username and self.api_key:
            return True

        sickrage.app.log.warning(
            'Your authentication credentials for {} are missing, check your config.'.format(self.name))

        return False

    def search(self, search_strings, age=0, ep_obj=None, **kwargs):
        results = []
        if not self._check_auth:
            return results

        search_params = {
            'tv': 'true',
            'username': self.username,
            'apikey': self.api_key
        }

        for mode in search_strings:
            sickrage.app.log.debug("Search Mode: {0}".format(mode))
            for search_string in search_strings[mode]:
                if self.freeleech:
                    search_params['fl'] = 'true'
                else:
                    search_params.pop('fl', '')

                if mode != 'RSS':
                    sickrage.app.log.debug("Search string: {}".format(search_string.strip()))
                    search_params['search'] = search_string
                else:
                    search_params.pop('search', '')

                try:
                    data = self.session.get(self.urls['search'], params=search_params).json()
                    results += self.parse(data, mode)
                except Exception:
                    sickrage.app.log.debug("No data returned from provider")

        return results

    def parse(self, data, mode, **kwargs):
        """
        Parse search results from data
        :param data: response data
        :param mode: search mode
        :return: search results
        """

        results = []

        error = data.get('error')
        if error:
            sickrage.app.log.debug(error)
            return results

        try:
            if data['0']['total_results'] == 0:
                sickrage.app.log.debug("Provider has no results for this search")
                return results
        except Exception:
            return results

        for i in data:
            try:
                title = data[i]["release_name"]
                download_url = data[i]["download_url"]
                if not all([title, download_url]):
                    continue

                seeders = data[i]["seeders"]
                leechers = data[i]["leechers"]

                torrent_size = str(data[i]["size"]) + ' MB'
                size = convert_size(torrent_size, -1)

                results += [
                    {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
                ]

                if mode != 'RSS':
                    sickrage.app.log.debug("Found result: {}".format(title))
            except Exception:
                sickrage.app.log.error("Failed parsing provider")

        return results
