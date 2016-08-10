# -*- coding: utf-8 -*-
# @Author: Charles Starr
# @Date:   2016-07-10 12:25:59
# @Last Modified by:   Charles Starr
# @Last Modified time: 2016-08-09 23:10:31

import spotipy
import spotipy.util as util
import sqlite3
import numpy as np
from lxml import etree



class User(object):
	#generic user object contains common code 
	def __init__(self):
		self.artists = []


	def common_artists(self, artist_set):
		#checks for common entries between artist set and user artists
		common_artists = []
		for artist in self.artists:
			if artist in artist_set:
				common_artists.append(artist)
		return set(common_artists)

	def dp_common_artists(self, artist_set):
		#implements dynamic programming algorithm to match artists with more tolerance for mismatch
		matches = []
		for playlist_artist in self.artists:
			try:
				print playlist_artist
			except:
				continue
			for local_artist in artist_set:
				dp_matrix = self.dp_matrix(playlist_artist, local_artist)
				if self.longest_alignment(dp_matrix):
					matches.append(local_artist)
		return matches

	def dp_matrix(self, artist_one, artist_two):
		#creates the dp matrix from the two artist inputs and returns it.
		dp_matrix = np.matrix([[0]*len(artist_one) for j in range(len(artist_two))])
		for i, one_letter in enumerate(artist_one):
			for j, two_letter in enumerate(artist_two):
				if one_letter == two_letter:
					#fill matrix top to bottom, left to right
					dp_matrix[j, i] = 1
		return dp_matrix

	def longest_alignment(self, dp_matrix):
		#finds longest diagonal sequence in matrix and returns it
		if 0 in dp_matrix.shape:
			return False
		for j in range(dp_matrix.shape[0]):
			match_count = 0
			i = 0
			while dp_matrix[j,i]:
				match_count += 1
				if match_count == dp_matrix.shape[1]:
					return True
				else:
					if i < dp_matrix.shape[1] - 1 and j < dp_matrix.shape[0] - 1:
						i += 1
						j += 1
					else:
						break
		return False

class Spot_User(User):
	#subclass contains methods specifically for spotify users
	def __init__(self):
		super(Spot_User, self).__init__()
		self.username = raw_input('username: ')
		self.token = self.get_token()
		self.sp = spotipy.Spotify(auth=self.token)
		self.playlists = self.get_playlists()
		self.tracks = self.get_tracks()
		self.artists = self.get_artists()

	def get_token(self):
		#uses spotipy library to get authentication token
		 token = util.prompt_for_user_token(self.username, 'playlist-read-private',
											 'dde5911d377b49458e1444e15dfb1d02',
											 '8f52142170ff425a8e47b2c2fbbfdf1c',
											 'http://localhost:8888/callback')
		 return token

	def get_playlists(self):
		#gets and returns user playlist ids
		playlists = self.sp.user_playlists(self.username, limit=50)
		return playlists

	def get_tracks(self):
		#gets track information from playlists
		tracks = []
		for playlist in self.playlists['items']:
			tracks.extend(self.sp.user_playlist_tracks(playlist['owner']['id'],playlist['id'])['items'])
		return tracks

	def get_artists(self):
		#pulls artist info from tracks
		artists = []
		for item in self.tracks:
			track = item['track']
			artist_info = track['artists'][0]
			artist_name = artist_info['name']
			artists.append(artist_name)
		return set(artists)

class Tunes_User(User):
	#subclass for itunes users
	def __init__(self, library_xml):
		super(Tunes_User, self).__init__()
		self.artists = self.get_artists(library_xml)

	def get_artists(self, library_xml):
		tree = etree.parse(library_xml)
		artists = tree.xpath('//plist/dict/dict/dict/key[text()="Artist"]/following-sibling::*[1]/text()')
		return set(artists)

class Event_Calendar(object):
	#opens up the database and extracts events based on a list of artists
	def __init__(self, db_file):
		self.db_file = db_file
		self.artist_dic = self.get_artist_ids()

	def get_artist_ids(self):
		#creates and returns artist_name:artist_id dictionary
		conn = sqlite3.connect(self.db_file)
		c = conn.cursor()
		c.execute('''SELECT * FROM artists''')
		artist_dic = {x[1]:x[0] for x in c.fetchall()}
		conn.close()
		return artist_dic

	def artist_set(self):
		#returns a set of artists for use in comparison with user playlist artists
		return set(self.artist_dic.keys())

	def events_by_artist(self, common_artists):
		#finds the shows associated with common user artists
		conn = sqlite3.connect(self.db_file)
		c = conn.cursor()
		matched_events = []
		for artist in common_artists:
			c.execute('''SELECT 
							artists.artist_name,
							venues.venue_name,
							events.show_datetime
						FROM
							artists
							INNER JOIN events ON artists.artist_id = events.artist_id
							INNER JOIN venues on events.venue_id = venues.venue_id
						WHERE 
							artists.artist_id = ?''', (self.artist_dic[artist],))
			matched_events.extend(c.fetchall())
		conn.close()
		return matched_events


