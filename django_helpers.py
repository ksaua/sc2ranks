from sc2ranks import Sc2Ranks
from django.core.cache import cache
import logging


try:
    from django.conf import settings
    SC2RANKS_API_KEY = settings.SC2RANKS_API_KEY
except (ImportError, AttributeError):
    print "Please configure 'SC2RANKS_API_KEY' in your settings.py"


class Sc2RanksMixin(object):
    """Add methods for fetching SC2Ranks-Data to a Django model"""

    client = Sc2Ranks(SC2RANKS_API_KEY)
    # How to best enforce that a model that uses this mixin has these fields set?
    # TODO: evaluate abstract properties
    player_fieldname = None
    bnet_id_fieldname = None
    bnet_realm_fieldname = None

    @property
    def bnet_name(self):
        try:
            assert bool(self.player_fieldname)
            player_field = getattr(self, 'player_fieldname')
            return  getattr(self, player_field)
        except AssertionError:
            raise AssertionError('No field mapping for player_fieldname specified')
        except AttributeError:
            raise AttributeError('The fieldname specified for player_fieldname does not exist on this model')

    @property
    def bnet_id(self):
        try:
            assert bool(self.bnet_id_fieldname)
            bnet_id_field = getattr(self, 'bnet_id_fieldname')
            return  getattr(self, bnet_id_field)
        except AssertionError:
            raise AssertionError('No field mapping for bnet_id_fieldname specified')
        except AttributeError:
            raise AttributeError('The fieldname specified for bnet_id_fieldname does not exist on this model')

    @property
    def bnet_realm(self):
        try:
            assert bool(self.bnet_realm_fieldname)
            bnet_realm_field = getattr(self, 'bnet_realm_fieldname')
            return  getattr(self, bnet_realm_field)
            raise AssertionError('No field mapping for bnet_realm_fieldname specified')
        except AttributeError:
            raise AttributeError('The fieldname specified for bnet_realm does not exist on this model')

    def assert_bnet_id(self):
        """Updates the players battle.net id if it isn't set yet."""

        if not self.bnet_id:
            try:
                bnet_id = self.get_sc2ranks_bnet_id()
                setattr(self, self.bnet_id_fieldname, bnet_id)
                self.save()
            except Exception, e:
                logging.debug('bnet_id could not be updated.\n %s' % e)


    ########################
    # Sc2Ranks-Api methods #
    ########################
    def search_character(self):
        """Search a character by name."""

        data = self.client.search_for_character(self.bnet_realm, self.bnet_name)
        return data

    @property
    def bnet_url(self):
        if self.bnet_id and self.bnet_name:
            return 'http://%s.battle.net/sc2/en/profile/%s/1/%s/' % (self.bnet_realm,
                                                                     self.bnet_id,
                                                                     self.bnet_name)

    @property
    def sc2ranks_profile_page(self):
        return "http://www.sc2ranks.com/%s/%s/%s/" % (self.bnet_realm,
                                                      self.bnet_id,
                                                      self.bnet_name)

    @property
    def get_sc2ranks_base_character(self, cache_seconds=1800):
        character = None
        cache_key = self.bnet_name
        character = cache.get(cache_key)
        self.assert_bnet_id()

        if character is not None:
            return character

        character_data = self.client.fetch_base_character(name=self.bnet_name,
                                                          bnet_id=self.bnet_id,
                                                          region=self.bnet_realm)
        if character_data:
            character = character_data
            cache.set(cache_key, character, cache_seconds)
        return character

    def get_sc2ranks_stats(self, bracket=1, *partner):
        """
        Get team stats from sc2ranks.com

        if no further parameter is given single player stats are returned
        further options:
            bracket = 1,2 etc.
            partner = HandJudas, MrChance etc ...
        """
        teams = None
        cache_key = '%s%s' % (self.bnet_name, bracket)
        cached_teams = cache.get(cache_key)

        if cached_teams is not None:
            teams = cached_teams
        else:
            teams = self.client.fetch_character_teams(region=self.bnet_realm,
                                                       name=self.bnet_name,
                                                       bracket=bracket,
                                                       bnet_id=self.bnet_id)
            cache.set(cache_key, teams, 1800)

        teams_partner = []
        if partner:
            for team in teams.teams:
                for member in team.members:
                    if member.name in partner:
                        teams_partner.append(team)
            teams = list(set(teams_partner))
        return teams

    def get_sc2ranks_bnet_id(self):
        """Get the battle.net id for a player name."""

        return self.search_character().characters[0]['bnet_id']

    def get_sc2ranks_portrait(self, size=75):
        """Returns the data needed to render the starcraft profile image."""

        if self.get_sc2ranks_base_character:
            try:
                portrait = self.get_sc2ranks_base_character.portrait
                x = -(portrait.column * size)
                y = -(portrait.row * size)
                image = 'portraits-%d-%d.jpg' % (portrait.icon_id, size)
                position = '%dpx %dpx no-repeat; width: %dpx; height: %dpx;' % (x, y, size, size)
                return  {'image': image, 'position': position}
            except:
                pass
