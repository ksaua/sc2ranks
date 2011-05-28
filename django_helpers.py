from sc2ranks import Sc2Ranks
from django.core.cache import cache

CACHE_TIME = 60 * 60 * 4

try:
    from django.conf import settings
    SC2RANKS_API_KEY = settings.SC2RANKS_API_KEY
except (ImportError, AttributeError):
    print "Please configure 'SC2RANKS_API_KEY' in your settings.py"


class Sc2RanksManager(object):
    """
    Descriptor for handling access to Sc2Ranks-API.
    """

    def __init__(self, name, realm, bid):
        self.bnet = {}
        self.bnet['name'] = name
        self.bnet['realm'] = realm
        self.bnet['bid'] = bid

    def __get__(self, instance, owner):
        # get instance values and pass data to api wrapper
        return Sc2RanksAPIWrapper(instance, **self.bnet)


class Sc2RanksAPIWrapper(object):

    def __init__(self, instance, name, realm, bid):
        self.bnet_name = instance.__dict__[name]
        self.bnet_realm = instance.__dict__[realm]
        self.bnet_id = instance.__dict__[bid]
        self.client = Sc2Ranks(SC2RANKS_API_KEY)

    @property
    def profile_page(self):
        return "http://www.sc2ranks.com/%s/%s/%s/" % (self.bnet_realm,
                                                      self.bnet_id,
                                                      self.bnet_name)

    def get_team_stats(self, bracket=1, *partner):
        """
        Fetch team stats from sc2ranks.

        if no further parameter is given single player stats are returned
        further options:
            bracket = 1,2 etc.
            partner = HandJudas, MrChance etc ...
        """
        data = None
        cache_key = '%s%s' % (self.bnet_name, bracket)
        cached_teams = cache.get(cache_key)

        if cached_teams is not None:
            data = cached_teams
        else:
            data = self.client.fetch_character_teams(region=self.bnet_realm,
                                                       name=self.bnet_name,
                                                       bracket=bracket,
                                                       bnet_id=self.bnet_id)
            cache.set(cache_key, data, CACHE_TIME)

        teams = []
        for team in data.teams:
            # get the actual team from the list of all player's team in bracket
            if hasattr(team, 'members'):
                if all([member.name in partner for member in team.members]):
                    teams.append(team)
            else:
                # as there are no members we can assume it's a single player team
                teams = data.teams

        return list(set(teams))

    def search_character(self):
        """Search a character by name."""

        return self.client.search_for_character(self.bnet_realm, self.bnet_name)

    @property
    def bnet_url(self):
        if self.bnet_id and self.bnet_name:
            return 'http://%s.battle.net/sc2/en/profile/%s/1/%s/' % (self.bnet_realm,
                                                                     self.bnet_id,
                                                                     self.bnet_name)


    @property
    def base_character(self, cache_seconds=CACHE_TIME):
        character = None
        cache_key = self.bnet_name
        character = cache.get(cache_key)

        if character is not None:
            return character

        character_data = self.client.fetch_base_character(name=self.bnet_name,
                                                          bnet_id=self.bnet_id,
                                                          region=self.bnet_realm)
        if character_data:
            character = character_data
            cache.set(cache_key, character, cache_seconds)
        return character


    def get_portrait(self, size=75):
        """Returns the data needed to render the starcraft profile image."""

        if self.base_character:
            try:
                portrait = self.base_character.portrait
                x = -(portrait.column * size)
                y = -(portrait.row * size)
                image = 'portraits-%d-%d.jpg' % (portrait.icon_id, size)
                position = '%dpx %dpx no-repeat; width: %dpx; height: %dpx;' % (x, y, size, size)
                return  {'image': image, 'position': position}
            except:
                pass
