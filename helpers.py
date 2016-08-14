# -*- coding: utf-8 -*-
# @Author: Charles Starr
# @Date:   2016-08-13 11:35:02
# @Last Modified by:   Charles Starr
# @Last Modified time: 2016-08-13 20:17:08
import sqlite3
import datetime


def xpath_executor(tree, expression):
	try:
		return tree.xpath(expression) + ['']
	except:
		return ['']

def field_extraction(item_dics, field):
	#extracts a given field from a dictionary of items with field names
	field_list = ['']
	for item in item_dics:
		if item[field]:
			field_list.append(item[field])
	return set(field_list)

def date_generator(window=60):
	#generates dates for a certain number of days into the future (default 60)
	today = datetime.date.today()
	end = today + datetime.timedelta(days=window)
	while today < end:
		yield today
		today += datetime.timedelta(days=1)

def simple_table_update(db_name, update_list, update_table, update_fields):
	#updates simple fields like city, state, artist. returns dictionary of the form item:id
	conn = sqlite3.connect(db_name)
	c = conn.cursor()
	c.execute('''SELECT * FROM %s''' % update_table)
	existing_items = set([x[1] for x in c.fetchall()])
	real_update_list = set(update_list) - existing_items
	for item in real_update_list:
		c.execute('''INSERT INTO %s (%s) VALUES (?)''' % (update_table, update_fields), (item,))
	table_items = c.execute('''SELECT * FROM %s''' % update_table)
	table_dic = {x[1]:x[0] for x in c.fetchall()}
	conn.commit()
	conn.close()
	return table_dic

def venue_table_update(db_name, venue_info, city_dic, state_dic):
	conn = sqlite3.connect(db_name)
	c = conn.cursor()
	c.execute('''SELECT * FROM venues''')
	existing_items = c.fetchall()
	existing_venues = [venue[1] for venue in existing_items]
	update_venues = venue_info
	real_update_list = [x for x in update_venues if x[0] not in existing_venues]
	for venue in real_update_list:
		c.execute('''INSERT INTO venues (venue_name, address, city, state, postal_code, phone, website) 
					VALUES (?,?,?,?,?,?,?)''', tuple(venue))
	venues = c.execute('''SELECT * FROM venues''')
	venue_dic = {venue[1]:venue[0] for venue in venues}
	conn.commit()
	conn.close()
	return venue_dic

def event_table_update(db_name, events, artist_dic, venue_dic):
	conn = sqlite3.connect(db_name)
	c = conn.cursor()
	for event in events:
		event_time = datetime.datetime.combine(event['Date'],event['Time'])
		c.execute('''INSERT INTO events (artist_id, venue_id, show_datetime) VALUES (?, ?, ?)''', 
				(artist_dic[event['Artist']], venue_dic[event['Venue']], event_time.isoformat()))
	conn.commit()
	conn.close()

def rebuild_eventdb(db_file):
	#dumps everything in the current db file and remakes all tables
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	#cities table
	c.execute('''DROP TABLE IF EXISTS cities''')
	c.execute('''CREATE TABLE cities 
				(city_id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
				city_name  TEXT UNIQUE)''')
	#state table
	c.execute('''DROP TABLE IF EXISTS states''')
	c.execute('''CREATE TABLE states 
				(state_id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
				state_name  TEXT UNIQUE)''')
	#venue table
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
	#artist table
	c.execute('''DROP TABLE IF EXISTS artists''')
	c.execute('''CREATE TABLE artists
		(artist_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
		artist_name TEXT UNIQUE)''')
	#event table
	c.execute('''DROP TABLE IF EXISTS events''')
	c.execute('''CREATE TABLE events
		(event_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
		artist_id INTEGER,
		venue_id INTEGER,
		show_datetime TEXT)''')
	conn.commit()
	conn.close()


