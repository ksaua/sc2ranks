# -*- coding: utf-8 -*-
import urllib
import json

MAX_CHARS = 98
API_KEY = 'github.com/anrie/sc2ranks'


class Sc2Ranks:
    def __init__(self, app_key):
        self.app_key = app_key

    def api_fetch(self, path, params=''):
        """
        Fetch some JSON from the API

        >>> client = Sc2Ranks(API_KEY)
        >>> client.api_fetch('search/exact/eu/Kapitulation')
        {u'total': 1, u'characters': [{u'bnet_id': 316741, u'name': u'Kapitulation'}]}
        """
        url = "http://sc2ranks.com/api/%s.json?appKey=%s" % (path, self.app_key)
        return fetch_json(url, params)

    def validate(self, data, exception):
        if type(data).__name__ == 'dict' and 'error' in data:
            raise exception
        else:
            if type(data).__name__ == 'dict':
                return Sc2RanksResponse(data)
            elif type(data).__name__ == 'list':
                return [Sc2RanksResponse(datum) for datum in data]

    def search_for_character(self, region, name, search_type='exact'):
        """
        Search for a character by screen name

        >>> client = Sc2Ranks(API_KEY)
        >>> client.search_for_character(region='eu', name='Kapitulation')
        <Sc2RanksResponse(total=1, characters=[{u'bnet_id': 316741, u'name': u'Kapitulation'}])>
        >>> client.search_for_character(region='eu', name='PleaseNobodyTakeThisUsername')
        Traceback (most recent call last):
            ...
        NoSuchCharacterException: Name: PleaseNobodyTakeThisUsername, region: eu
        """

        return self.validate(
            data=self.api_fetch('search/%s/%s/%s' % (search_type, region, name)),
            exception=NoSuchCharacterException("Name: %s, region: %s" % (name, region)))

    def search_for_profile(self, region, name, search_type='1t', search_subtype='division', value='Division'):
        """
        Search for a character profile

        >>> client = Sc2Ranks(API_KEY)
        >>> client.search_for_profile(name='Kapitulation', region='eu')
        ... #doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
        [<Sc2RanksResponse(bnet_id=316741, name=Kapitulation, achievement_points=..., character_code=..., region=eu,
            team={u'division_id': ...,
                  u'division_name': ...,
                  u'wins': ...,
                  u'losses': ...,
                  u'points': ...,
                  u'id': ...}, id=...)>]
        >>> client.search_for_profile(name='PleaseNobodyTakeThisUsername', region='eu')
        Traceback (most recent call last):
            ...
        NoSuchCharacterException: Name: PleaseNobodyTakeThisUsername, region: eu
        """

        return self.validate(
            data=self.api_fetch('psearch/%s/%s/%s/%s/%s' % (region, name, search_type, search_subtype, value)),
            exception=NoSuchCharacterException("Name: %s, region: %s" % (name, region)))

    def fetch_base_character(self, region, name, bnet_id):
        """
        Minimum amount of character data, just gives achievement points, character code and battle.net id info.

        >>> client = Sc2Ranks(API_KEY)
        >>> client.fetch_base_character(region='eu', name='Kapitulation', bnet_id='316741')
        ... #doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
        <Sc2RanksResponse(bnet_id=316741,
                          name=Kapitulation,
                          achievement_points=...,
                          region=eu,
                          updated_at=...,
                          character_code=...,
                          portrait=<Sc2RanksResponse(column=..., icon_id=..., row=...)>,
                          id=...)>

        """

        return self.validate(
            data=self.api_fetch("base/char/%s/%s!%s" % (region, name, bnet_id)),
            exception=NoSuchCharacterException("Name: %s, region: %s, bnet_id: %s" % (name, region, bnet_id)))

    def fetch_base_character_teams(self, region, name, bnet_id):
        """
        Base character data plus team items

        >>> client = Sc2Ranks(API_KEY)
        >>> client.fetch_base_character_teams(region='eu', name='Kapitulation', bnet_id='316741')
        ... #doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
        <Sc2RanksResponse(bnet_id=316741, name=Kapitulation, achievement_points=..., region=eu, updated_at=...,
        teams={...},
        character_code=..., portrait=<Sc2RanksResponse(column=..., icon_id=..., row=...)>, id=...)>

        """

        return self.validate(
            data=self.api_fetch("base/teams/%s/%s!%s" % (region, name, bnet_id)),
            exception=NoSuchCharacterException("Name: %s, region: %s, bnet_id: %s" % (name, region, bnet_id)))

    def fetch_character_teams(self, region, name, bnet_id, bracket, is_random=False):
        """
        Gets character info and extended team info

        >>> client = Sc2Ranks(API_KEY)
        >>> client.fetch_character_teams(region='eu', name='Kapitulation', bnet_id='316741', bracket='3v3')
        ... #doctest: +NORMALIZE_WHITESPACE, +ELLIPSIS
        <Sc2RanksResponse(bnet_id=316741,
                          name=Kapitulation,
                          achievement_points=...,
                          region=eu,
                          updated_at=...,
                          teams={'3v3':...},
                          character_code=...,
                          id=...)>
        """
        bracket = int(bracket[0])
        is_random = 1 if is_random else 0
        return self.validate(
            data=self.api_fetch("char/teams/%s/%s!%s/%s/%s" % (region, name, bnet_id, bracket, is_random)),
            exception=NoSuchCharacterException("Name: %s, region: %s, bnet_id: %s" % (name, region, bnet_id)))

    def fetch_mass_base_characters(self, characters):
        """
        Characters format: ((region1, name1, bnet_id1), (region2, name2, bnet_id2)..)"""

        def get_batch(characters):
            def single_char_data(num, character):
                return "characters[%s][region]=%s&characters[%s][name]=%s&characters[%s][bnet_id]=%s" % (num, character[0], num, character[1], num, character[2])

            params = '&'.join(map(lambda c: single_char_data(characters.index(c), c), characters))
            url = 'http://sc2ranks.com/api/mass/base/char/?appKey=%s' % self.app_key
            return fetch_json(url, params)

        for i in range(0, (len(characters) / MAX_CHARS) + 1):
            result = get_batch(characters[i * MAX_CHARS:(i + 1) * MAX_CHARS])
            for r in result:
                yield Sc2RanksResponse(r)

    def fetch_mass_characters_team(self, characters, bracket, is_random=False):
        """Characters format: ((region1, name1, bnet_id1), (region2, name2, bnet_id2)..)
        bracket is like: '1v1'
        is_random is True/False"""

        bracket = int(bracket[0])
        is_random = 1 if is_random else 0

        def get_batch(characters):
            def single_char_data(num, character):
                return "characters[%s][region]=%s&characters[%s][name]=%s&characters[%s][bnet_id]=%s" % (num, character[0], num, character[1], num, character[2])

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
        return "http://sc2ranks.com/char/%s/%s/%s" % (region, bnet_id, name)

    elif code != None:
        return "http://sc2ranks.com/charcode/%s/%s/%s" % (region, code, name)

    else:
        raise ParameterException("Either bnet_id or code must be supplied")


def fetch_json(url, params=None):
    f = urllib.urlopen(url, params)
    data = json.loads(f.read())
    f.close()
    return data


class ParameterException(Exception):
    pass


class NoSuchCharacterException(Exception):
    pass


class Sc2RanksResponse:
    def __init__(self, d):
        if 'portrait' in d:
            d['portrait'] = Sc2RanksResponse(d['portrait'])

        if 'teams' in d:
            teams = dict(map(lambda t: ("%sv%s" % (t['bracket'], t['bracket']), Sc2RanksResponse(t)), d['teams']))
            d['teams'] = teams

        if 'members' in d:
            d['members'] = map(lambda m: Sc2RanksResponse(m), d['members'])

        self.__dict__.update(d)

    def __repr__(self):
        return "<Sc2RanksResponse(%s)>" % ', '.join(map(lambda t: "%s=%s" % t, self.__dict__.iteritems()))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
