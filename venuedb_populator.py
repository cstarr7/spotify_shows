# -*- coding: utf-8 -*-
# @Author: Charles Starr
# @Date:   2016-07-18 22:16:49
# @Last Modified by:   Charles Starr
# @Last Modified time: 2016-08-09 13:26:58

import requests
from lxml import html
import sqlite3
import datetime

#contains the necessary functions to retrieve venue information from https://www.wwoz.org/organizations/...

def main():
	#get all venue information
	venue_list = venue_iterator()
	venue_info = venue_populator(venue_list)
	#make unique city table
	city_list = field_extraction(venue_info, 'City')
	cityid_dic = city_table(city_list)
	#make unique state table
	state_list = field_extraction(venue_info, 'State')
	stateid_dic = state_table(state_list)
	#make venue table
	venueid_dic = venue_table(venue_info, cityid_dic, stateid_dic)
	#extract all events
	events = event_iterator()
	#make unique artist table
	artist_list = field_extraction(events, 'Artist')
	artistid_dic = artist_table(artist_list)
	#populate events table using artistid dictionary, venueid dictionary and event date/time
	event_populator(events, venueid_dic, artistid_dic)


def venue_iterator():
	#retrieves venue info from pages of the form https://www.wwoz.org/venues?page=*. returns list 
	#of url extensions for all venues
	base_url = 'https://www.wwoz.org/venues?page='
	venue_extensions = []
	for i in range(1,25,1): #currently 22 pages of venues
		page_url = base_url + str(i)
		page = requests.get(page_url)
		page_html = html.fromstring(page.text)
		venue_elements = page_html.find_class('venue')
		for venue in venue_elements:
			venue_extensions.append(venue.xpath('a/@href')[0])
	return venue_extensions

def venue_populator(extension_list):
	#uses list of url extensions from venue_iterator and visits each venue page. returns list of 
	#dictionaries containing venue information
	base_url = 'https://www.wwoz.org'
	venue_dics = []
	for extension in extension_list:
		venue_url = base_url + extension
		page = requests.get(venue_url)
		page_html = html.fromstring(page.text)
		venue_dic = {}
		venue_dic['Name'] = xpath_executor(page_html, '//*[@class="page-title"]/text()')
		venue_dic['Street'] = xpath_executor(page_html, '//*[@class="thoroughfare"]/text()')
		venue_dic['City'] = xpath_executor(page_html, '//*[@class="locality"]/text()')
		venue_dic['State'] = xpath_executor(page_html, '//*[@class="state"]/text()')
		venue_dic['Postal Code'] = xpath_executor(page_html, '//*[@class="postal-code"]/text()')
		venue_dic['Phone'] = xpath_executor(page_html, '//a[contains(@href, "tel")]/text()')
		venue_dic['Website'] = xpath_executor(page_html, '//a[contains(text(), "http")]/../a/text()')
		venue_dics.append(venue_dic)
	return venue_dics

def field_extraction(venue_dics, field):
	#extracts city info from venue dictionaries so a city table can be created in the database
	field_list = ['']
	for venue in venue_dics:
		if venue[field]:
			field_list.append(venue[field])
	return set(field_list)

def city_table(city_list):
	#uses city list to populate a city table. returns city dictionary for use populating venues
	conn = sqlite3.connect('no_shows.sqlite')
	c = conn.cursor()
	c.execute('''DROP TABLE IF EXISTS cities''')
	c.execute('''CREATE TABLE cities 
				(city_id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
				city_name  TEXT UNIQUE)''')
	for city in city_list:
		c.execute('''INSERT INTO cities (city_name) VALUES (?)''',(city,))
	cities = c.execute('''SELECT * FROM cities''')
	cityid_dic = {city[1]: city[0] for city in cities}
	conn.commit()
	conn.close()
	return cityid_dic

def state_table(state_list):
	#uses state list to populate a state table. returns state dictionary for use populating venues
	conn = sqlite3.connect('no_shows.sqlite')
	c = conn.cursor()
	c.execute('''DROP TABLE IF EXISTS states''')
	c.execute('''CREATE TABLE states 
				(state_id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
				state_name  TEXT UNIQUE)''')
	for state in state_list:
		c.execute('''INSERT INTO states (state_name) VALUES (?)''',(state,))
	states = c.execute('''SELECT * FROM states''')
	stateid_dic = {state[1]: state[0] for state in states}
	conn.commit()
	conn.close()
	return stateid_dic

def venue_table(venue_info, cityid_dic, stateid_dic):
	#populates the venue table
	conn = sqlite3.connect('no_shows.sqlite')
	c = conn.cursor()
	c.execute('''DROP TABLE IF EXISTS venues''')
	c.execute('''CREATE TABLE venues
		(venue_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
		venue_name TEXT UNIQUE,
		address TEXT,
		city INTEGER,
		state INTEGER,
		postal_code INTEGER,
		phone TEXT,
		website TEXT)''')
	for venue in venue_info:
		c.execute('''INSERT INTO venues (venue_name, address, city, state, postal_code, phone, website)
					VALUES(?,?,?,?,?,?,?)''',(venue['Name'], venue['Street'], cityid_dic[venue['City']],
						stateid_dic[venue['State']], venue['Postal Code'], venue['Phone'], venue['Website']))
	venues = c.execute('''SELECT * FROM venues''')
	venueid_dic = {venue[1]:venue[0] for venue in venues}
	conn.commit()
	conn.close()
	return venueid_dic

def date_generator():
	today = datetime.date.today()
	end = today + datetime.timedelta(days=60)
	while today < end:
		yield today
		today += datetime.timedelta(days=1)

def event_iterator():
	events = []
	base_url = 'https://www.wwoz.org/calendar/livewire-music?date='
	for date in date_generator():
		url = base_url + date.isoformat()
		page = requests.get(url)
		page_html = html.fromstring(page.text)
		for venue in page_html.xpath('//div[@class="panel panel-default"]'):
			venue_name = xpath_executor(venue, './/h3[@class="panel-title"]/a/text()')
			for show in venue.xpath('.//div[@class="col-xs-10 calendar-info"]'):
				artist = xpath_executor(show,'.//p[1]/a/text()')
				time = xpath_executor(show,'.//p[2]/text()')
				events.append({'Date':date, 'Venue':venue_name, 'Artist':artist, 'Time':time[time.rfind(' ')+1:]})
	return events

def artist_table(artists):
	#takes artist list and makes sqlite table, returns dictionary of artists and unique IDs
	conn = sqlite3.connect('no_shows.sqlite')
	c = conn.cursor()
	c.execute('''DROP TABLE IF EXISTS artists''')
	c.execute('''CREATE TABLE artists
		(artist_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
		artist_name TEXT UNIQUE)''')
	for artist in artists:
		c.execute('''INSERT INTO artists (artist_name) values (?)''',(artist,))
	new_artists = c.execute('''SELECT * FROM artists''')
	artistid_dic = {new_artist[1]:new_artist[0] for new_artist in new_artists}
	conn.commit()
	conn.close()
	return artistid_dic

def event_populator(events, venue_id, artist_id):
	conn = sqlite3.connect('no_shows.sqlite')
	c = conn.cursor()
	c.execute('''DROP TABLE IF EXISTS events''')
	c.execute('''CREATE TABLE events
		(event_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
		artist_id INTEGER,
		venue_id INTEGER,
		show_datetime TEXT)''')
	for event in events:
		c.execute('''INSERT INTO events (artist_id, venue_id, show_datetime) values (?,?,?)''',
				(artist_id[event['Artist']],venue_id[event['Venue']],
				datetime.datetime.combine(event['Date'], time_conversion(event['Time'])).isoformat()))
	conn.commit()
	conn.close()

def xpath_executor(tree, expression):
	try:
		item_list = tree.xpath(expression)
		item = item_list[0].strip()
		return item
	except:
		return ''

def time_conversion(time):
	minutes = int(time[-4:-2])
	hours = int(time[:-5])
	if 'p' in time and hours != 12:
		hours += 12
	return datetime.time(hours, minutes)