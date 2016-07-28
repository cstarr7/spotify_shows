# -*- coding: utf-8 -*-
# @Author: Charles Starr
# @Date:   2016-07-10 12:25:59
# @Last Modified by:   Charles Starr
# @Last Modified time: 2016-07-26 23:00:19

import getpass
import spotipy
import spotipy.util as util


class User(object):
	#object instance will store user/pass and create authentication token for spotify
	def __init__(self):
		self.username = raw_input('username: ')
		self.password = getpass.getpass('password: ')
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
		return artists

	def common_artists(self, artist_set):
		#checks for common entries between artist set and user artists
		common_artists = []
		for artist in self.artists:
			if artist in artist_set:
				common_artists.append(artist)
		return set(common_artists)


