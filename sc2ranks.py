import urllib, json

valid_regions = ('us', 'eu', 'kr', 'tw', 'sea', 'ru', 'la')

max_chars = 98
class Sc2Ranks:
	def __init__(self, app_key):
		self.app_key = app_key
		
	def fetch_base_character(self, region, name, code):
		url = "http://sc2ranks.com/api/base/char/%s/%s$%s.json?appKey=%s" % (region, name, code, self.app_key)
		data = fetch_json(url)
		if data.has_key('error'):
			raise NoSuchCharacterException("Name: %s, region: %s, code: %s" % (name, region, code))
		else:
			return Sc2RanksResponse(data)
		
	
	def fetch_base_character_teams(self, region, name, code):
		url = "http://sc2ranks.com/api/base/teams/%s/%s$%s.json?appKey=%s" % (region, name, code, self.app_key)
		data = fetch_json(url)
		if data.has_key('error'):
			raise NoSuchCharacterException("Name: %s, region: %s, code: %s" % (name, region, code))
		else:
			return Sc2RanksResponse(data)
			
	def fetch_character_teams(self, region, name, code, bracket, is_random=False):
		bracket = int(bracket[0])
		is_random = 1 if is_random else 0
		url = "http://sc2ranks.com/api/char/teams/%s/%s$%s/%s/%s.json?appKey=%s" % (region, name, code, bracket, is_random, self.app_key)
		data = fetch_json(url)
		if data.has_key('error'):
			raise NoSuchCharacterException("Name: %s, region: %s, code: %s" % (name, region, code))
		else:
			return Sc2RanksResponse(data)
	
	def fetch_mass_base_characters(self, characters):
		"""Characters format: ((region1, name1, code1), (region2, name2, code2)..)"""
		
		def get_batch(characters):
			def single_char_data(num, character):
				return "characters[%s][region]=%s&characters[%s][name]=%s&characters[%s][code]=%s" % (num, character[0], num, character[1], num, character[2])
				
			params = '&'.join(map(lambda c: single_char_data(characters.index(c), c), characters))
			url = 'http://sc2ranks.com/api/mass/base/char/?appKey=%s' % self.app_key
			return fetch_json(url, params)

		for i in range(0, (len(characters) / max_chars) + 1):
			result = get_batch(characters[i * max_chars:(i+1)*max_chars])
			for r in result: yield Sc2RanksResponse(r)
			
	
	def fetch_mass_characters_team(self, characters, bracket, is_random=False):
		"""Characters format: ((region1, name1, code1), (region2, name2, code2)..)
		bracket is like: '1v1'
		is_random is True/False"""
		
		bracket = int(bracket[0])
		is_random = 1 if is_random else 0
		
		def get_batch(characters):
			def single_char_data(num, character):
				return "characters[%s][region]=%s&characters[%s][name]=%s&characters[%s][code]=%s" % (num, character[0], num, character[1], num, character[2])
				
			char_data = '&'.join(map(lambda c: single_char_data(characters.index(c), c), characters))
			params = 'team[bracket]=%s&team[is_random]=%s&%s' % (bracket, is_random, char_data)
			url = 'http://sc2ranks.com/api/mass/base/teams/?appKey=%s' % self.app_key
			return fetch_json(url, params)

		for i in range(0, (len(characters) / max_chars) + 1):
			result = get_batch(characters[i * max_chars:(i+1)*max_chars])
			for r in result: yield Sc2RanksResponse(r)
			
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
		if d.has_key('portrait'):
			d['portrait'] = Sc2RanksResponse(d['portrait'])
			
		if d.has_key('teams'):
			teams = dict(map(lambda t: ("%sv%s" % (t['bracket'], t['bracket']), Sc2RanksResponse(t)), d['teams']))
			d['teams'] = teams
			
		if d.has_key('members'):
			d['members'] = map(lambda m: Sc2RanksResponse(m), d['members'])
			
		self.__dict__.update(d)
		
	def __repr__(self):
		return "<Sc2RanksResponse(%s)>" % ', '.join(map(lambda t: "%s=%s" % t, self.__dict__.iteritems()))

	
if __name__ == '__main__':
	sc2 = Sc2Ranks('an_app_key')
	#response = sc2.fetch_base_character('eu', 'canute', 501)
	response = sc2.fetch_base_character_teams('eu', 'canute', 501)
	print response.name, response.region, response.bnet_id, response.teams['1v1'].league, response.teams['2v2'].points
	
	response = sc2.fetch_character_teams('eu', 'canute', 501, '3v3', False)
	print response.teams['3v3'].members[0].name, response.teams['3v3'].members[0].character_code
	
	#response = list(sc2.fetch_mass_base_characters((('eu', 'Canute', 501), ('us', 'HuK', 530))))
	response = list(sc2.fetch_mass_characters_team((('eu', 'Canute', 501), ('us', 'HuK', 530)), '1v1'))
	print response[0].teams['1v1'].points, response[1].teams['1v1'].points
