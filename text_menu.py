# -*- coding: utf-8 -*-
# @Author: Charles Starr
# @Date:   2016-08-14 11:56:47
# @Last Modified by:   Charles Starr
# @Last Modified time: 2016-08-14 12:49:26

import tm_events
import wwoz_events
import user_classes
import helpers
from validate_email import validate_email

class Text_Menu(object):
	#contains routines for different menus
	def __init__(self, db_filename):
		self.db_filename = db_filename
	
	def database_options(self):
		#self explanatory database operations
		while True:
			print 'Database options:'
			print '1. Rebuild Database'
			print '2. Update Database'
			print '3. Accept Database'
			selection = raw_input('Enter selection: ')
			if selection == '1':
				helpers.rebuild_eventdb(self.db_filename)
				wwoz_events.main(self.db_filename)
				tm_events.main(self.db_filename)
			elif selection == '2':
				wwoz_events.main(self.db_filename)
				tm_events.main(self.db_filename)
			elif selection == '3':
				break
			else:
				print 'Please enter a valid selection'

	def user_options(self):
		#gets user email and creates user class based on service. returns class
		email = ''
		while True:
			email = raw_input('Please enter a valid email address: ')
			if validate_email(email):
				break
		while True:
			print 'Service options: '
			print '1. Spotify'
			print '2. iTunes'
			selection = raw_input('Enter selection: ')
			if selection == '1':
				username = raw_input('Please enter username: ')
				return user_classes.Spot_User(username, email)
			elif selection == '2':
				filename = raw_input('Please enter library xml filename: ')
				return user_classes.Tunes_User(filename, email)
			else:
				'Please enter a valid selection'










