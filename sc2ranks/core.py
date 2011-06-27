# -*- coding: utf-8 -*-
"""
Python module to interface the sc2ranks API documented at
http://www.sc2ranks.com/api

Valid regions are: us, eu, kr, tw, sea, ru and la

NOTE: It does not seem that the API at sc2ranks.com is versioned. This module
may break as soon as sc2ranks.com decides to make changes that are not
backwards-compatible. Let's hope that does not happen. If it does, please feel
free to contact the authors of this module with a detailed description of the
error.
"""

import sys
import urllib
import logging

# we assume simplejson is installed for pre Python2.6 platforms (as defined in
# setup.py)
if sys.hexversion < 0x02060000:
    import simplejson as json
else:
    import json

MAX_CHARS = 98
LOG = logging.getLogger(__name__)

class Sc2Ranks(object):
    """
    The API proxy
    """

    def __init__(self, app_key):
        """
        Creates a new proxy to the API using the given API key.

        For more information on the key, please visit
        http://www.sc2ranks.com/api
        """
        LOG.debug("Initialised SC2Ranks with API key '%s'" % app_key)
        self.app_key = app_key

    def api_fetch(self, path, params=''):
        """Fetch some JSON from the API."""
        url = "http://sc2ranks.com/api/%s.json?appKey=%s" % (path, self.app_key)
        LOG.debug("Fetching %s" % url)
        return fetch_json(url, params)

    def validate(self, data):
        """
        Checks if the returned data does not contain an error.

        If the response contained an error, that error is logged and the method
        returns `None`. Otherwise, the data is wrapped with an Sc2RanksResponse
        instance and returned. Either as list or signle object according to the
        response type.
        """
        if type(data).__name__ == 'dict' and 'error' in data:
            LOG.error("SC2Ranks ERROR: %r" % data)
            return None
        else:
            if type(data).__name__ == 'dict':
                return Sc2RanksResponse(data)
            elif type(data).__name__ == 'list':
                return [Sc2RanksResponse(datum) for datum in data]

    def search_for_character(self, region, name, search_type='exact'):
        """
        Allows you to perform small searches, useful if you want to hookup an
        IRC bot or such. Only returns the first 10 names. Search is
        case-insensitive.

        **region** please refer to the module description for a list of
        available region strings

        **name** is the search string.

        **search_type** can be 'exact', 'contains', 'starts', 'ends'.
        Default='exact'
        """
        return self.validate(
            data=self.api_fetch('search/%s/%s/%s' % (search_type,
                region.lower(),
                name)))

    def search_for_profile(self, region, name, search_type='1t', search_subtype='division', value='Division'):
        """
        Let's you search for profiles to find a characters battle.net id. This
        allows you to search for characters without having the character code,
        or relying purely on names.

        **type** can be '1t', '2t', '3t', '4t', 'achieve'.

        #t refers to team, so '1t' is 1v1 team and so on, 'achieve' refers to
        the characters achievements. **Default:** '1t'

        **sub_type** can be 'points', 'wins', 'losses', 'division' for #t,
        otherwise it's just 'points'. **Default:** division

        **value** is the value of what to search on based on type + sub_type,
        if you passed division then it's the division name, if you pass losses
        it's the total number of losses and so on. Matches are all inexact, if
        you pass `500` for `points` it searches for `>= 400` and `<= 600`, if
        you search for `division name` it does an inexact match.
        **Default:** `division`
        """

        return self.validate(
            data=self.api_fetch('psearch/%s/%s/%s/%s/%s' % (
                region.lower(),
                name,
                search_type.lower(),
                search_subtype.lower(),
                value)))

    def fetch_base_character(self, region, name, bnet_id):
        """
        Minimum amount of character data, just gives achievement points,
        character code and battle.net id info.

        **region:** The region (see module docstring for a complete list)

        **name:** The character name (exact!)

        **bnet_id:** The Battle.NET id
        """

        return self.validate(
            data=self.api_fetch("base/char/%s/%s!%s" % (region.lower(), name,
                bnet_id)))

    def fetch_base_character_teams(self, region, name, bnet_id):
        """
        Fetches the base character data plus team data.

        **region:** The region (see module docstring for a complete list)

        **name:** The character name (exact!)

        **bnet_id:** The Battle.NET id
        """

        return self.validate(
            data=self.api_fetch("base/teams/%s/%s!%s" % (region.lower(), name,
                bnet_id)))

    def fetch_character_teams(self, region, name, bnet_id, bracket, is_random=False):
        """
        Fetches character info and extended team info.

        **region:** The region (see module docstring for a complete list)

        **name:** The character name (exact!)

        **bnet_id:** The Battle.NET id

        **bracker:** ?

        **is_random:** ?
        """
        try:
            bracket = int(bracket[0])
        except:
            pass
        is_random = 1 if is_random else 0
        return self.validate(
            data=self.api_fetch("char/teams/%s/%s!%s/%s/%s" % (region.lower(),
                name, bnet_id, bracket, is_random)))

    def fetch_mass_base_characters(self, characters):
        """
        Fetches the data for multiple characters at once.

        Characters format: ((region1, name1, bnet_id1), (region2, name2, bnet_id2)..)"""

        def get_batch(characters):
            def single_char_data(num, character):
                return "characters[%s][region]=%s&characters[%s][name]=%s&characters[%s][bnet_id]=%s" % (num, character[0].lower(), num, character[1], num, character[2])

            params = '&'.join(map(lambda c: single_char_data(characters.index(c), c), characters))
            url = 'http://sc2ranks.com/api/mass/base/char/?appKey=%s' % self.app_key
            return fetch_json(url, params)

        for i in range(0, (len(characters) / MAX_CHARS) + 1):
            result = get_batch(characters[i * MAX_CHARS:(i + 1) * MAX_CHARS])
            for r in result:
                yield Sc2RanksResponse(r)

    def fetch_custom_division_characters(self, division_id, region='all', league='all', bracket=1, is_random=False):
        """
        Fetches characters and teams from custom divisions.

        **division_id:** The division ID

        **region:** The region (see module docstring for a complete list)
        **Default:** 'all'

        **league:** The league
        **Default:** 'all'

        **bracket:** ?
        **Default:** 1

        **is_random:** ?
        **Default:** False
        """

        is_random = int(is_random)

        result = self.validate(
            data=self.api_fetch("clist/%d/%s/%s/%d/%d" % (division_id, region.lower(), league, bracket, is_random)))
        return result

    def fetch_mass_characters_team(self, characters, bracket='1v1', is_random=False):
        """
        This is the same as `fetch_character_teams` except it fetches the data
        for multiple characters at once inlcuding extended team data.

        Characters format: ((region1, name1, bnet_id1), (region2, name2, bnet_id2)..)
        """

        bracket = int(bracket[0])
        is_random = 1 if is_random else 0

        def get_batch(characters):
            def single_char_data(num, character):
                return "characters[%s][region]=%s&characters[%s][name]=%s&characters[%s][bnet_id]=%s" % (num, character[0].lower(), num, character[1], num, character[2])

            char_data = '&'.join(map(lambda c: single_char_data(characters.index(c), c), characters))
            params = 'team[bracket]=%s&team[is_random]=%s&%s' % (bracket, is_random, char_data)
            url = 'http://sc2ranks.com/api/mass/base/teams/?appKey=%s' % self.app_key
            return fetch_json(url, params)

        for i in range(0, (len(characters) / MAX_CHARS) + 1):
            result = get_batch(characters[i * MAX_CHARS:(i + 1) * MAX_CHARS])
            for r in result:
                yield Sc2RanksResponse(r)


def character_url(region, name, bnet_id=None, code=None):
    """Returns the url to a character on sc2ranks.com"""

    if bnet_id != None:
        return "http://sc2ranks.com/char/%s/%s/%s" % (region.lower(), bnet_id, name)

    elif code != None:
        return "http://sc2ranks.com/charcode/%s/%s/%s" % (region.lower(), code, name)

    else:
        raise ParameterException("Either bnet_id or code must be supplied")


def fetch_json(url, params=None):
    """
    Tries to load a JSON object from an URL. If there is a connection problem,
    of JSON error, this method wil return None and the errors are logged.
    """
    LOG.debug("Fetching JSON data from '%s'. Params: %r" % (
        url, params))
    try:
        f = urllib.urlopen(url, params)
    except IOError, exc:
        LOG.exception("Unable to connect to remote host!")
        return None
    response_data = f.read()
    f.close()
    try:
        data = json.loads(response_data)
        LOG.debug("Response %r" % data)
        return data
    except Exception, exc:
        LOG.exception("Unable to parse respose as JSON. Response was: %r" %
                response_data)
        return None


class ParameterException(Exception):
    pass


class Sc2RanksResponse(object):
    """JSON-Response containing the queried information from sc2ranks.com."""

    def __init__(self, d={}):
        LOG.debug("Constructing an Sc2RanksResponse instance from %r" % d)
        if 'portrait' in d:
            d['portrait'] = Sc2RanksResponse(d['portrait'])

        if 'teams' in d:
            d['teams'] = [Sc2RanksResponse(team) for team in d['teams'] if team]

        if 'members' in d:
            d['members'] = [Sc2RanksResponse(member) for member in d['members'] if member]

        self.__dict__.update(d)

    def __repr__(self):
        return "<Sc2RanksResponse(%s)>" % ', '.join(map(lambda t: "%s=%s" % t, self.__dict__.iteritems()))


    def __eq__(self, other):
        for key, value in self.__dict__.iteritems():
            if getattr(other, key, None) != value:
                return False
        return True


if __name__ == "__main__":
    pass
