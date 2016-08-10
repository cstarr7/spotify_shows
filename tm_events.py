# -*- coding: utf-8 -*-
# @Author: Charles Starr
# @Date:   2016-07-27 21:44:47
# @Last Modified by:   Charles Starr
# @Last Modified time: 2016-08-09 13:26:52

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from lxml import html
import datetime
import sqlite3
import time as tm

def main():
	db_file = 'no_shows.sqlite'
	driver = webdriver.Firefox()
	get_events(driver, '70114', 'n186')
	events = extract_events(driver)
	artists = field_extraction(events, 'Artist')
	artist_dic = simple_table_update(db_file, artists, 'artists', 'artist_name')
	cities = field_extraction(events, 'City')
	city_dic = simple_table_update(db_file, cities, 'cities', 'city_name')
	states = field_extraction(events, 'State')
	state_dic = simple_table_update(db_file, states, 'states', 'state_name')
	venue_dic = venue_table_update(db_file, events, city_dic, state_dic)
	event_table_update(db_file, events, artist_dic, venue_dic)

def get_events(driver, location, time_window):
	#sets up event page at tm for the area code and time range desired
	url = 'http://www.ticketmaster.com/browse/all-music-catid-10001/music-rid-10001'
	driver.get(url)
	area_field = driver.find_element_by_id('browse_area')
	area_field.send_keys(location)
	driver.find_element_by_xpath('//span[@data-guid="2"]').click()
	driver.find_element_by_xpath('//li[@data-value="%s"]' % time_window).click()
	driver.find_element_by_name('go').click()
	tm.sleep(20)

def extract_events(driver):
	#scrapes event data from tm webpage and returns a dictionary of details for each event
	events = []
	while True:
		page_html = html.fromstring(driver.page_source)
		#one liner to get number of events on the page
		population = abs(eval(page_html.xpath('//div[@class="browsePagi"]/text()')[0].replace('|','').strip().split(' ')[0]))+3
		for event in [page_html.xpath('//tbody[@id="browse_results"]/tr[%d]' % x)[0] for x in range(2,population)]:
			summary = xpath_executor(event,'./td[2]/div[1]/div[1]/a[1]/text()')[0]
			details = xpath_executor(event,'./td[2]/div[1]/div[3]/a/text()')
			venue = xpath_executor(event,'./td[3]/div[1]/a/text()')[0].strip()
			city = xpath_executor(event,'./td[3]/div[1]/abbr[1]/text()')[0].strip()
			state = xpath_executor(event,'./td[3]/div[1]/abbr[2]/text()')[0].strip()
			date = xpath_executor(event,'./td[4]/div[1]/span[1]/text()[1]')[0].strip()
			time = xpath_executor(event,'./td[4]/div[1]/span[1]/text()[2]')[0].strip()
			#details preffered because it gives exact artist information
			if len(details) > 1:
				for artist in details:
					events.append({'Date':date, 
									'Venue':venue, 
									'Artist':artist, 
									'Time':time, 
									'City':city, 
									'State':state})
			else:
				events.append({'Date':date, 
								'Venue':venue, 
								'Artist':summary, 
								'Time':time, 
								'City':city, 
								'State':state})
		if page_html.xpath('//div[@class="browsePagi"]/a[@onclick="nextPage();"]'):
			driver.find_element_by_xpath('//div[@class="browsePagi"]/a[@onclick="nextPage();"]').click()
			tm.sleep(3)		
		else:
			break
	return events

def field_extraction(event_dics, field):
	#extracts city info from venue dictionaries so a city table can be created in the database
	field_list = ['']
	for event in event_dics:
		if event[field]:
			field_list.append(event[field])
	return set(field_list)

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

def venue_table_update(db_name, event_dic, city_dic, state_dic):
	conn = sqlite3.connect(db_name)
	c = conn.cursor()
	c.execute('''SELECT * FROM venues''')
	existing_items = c.fetchall()
	existing_venues = set([(venue[1], venue[3], venue[4]) for venue in existing_items])
	update_venues = set([(event['Venue'], city_dic[event['City']], state_dic[event['State']]) for event in event_dic])
	real_update_list = update_venues - existing_venues
	for venue in real_update_list:
		c.execute('''INSERT INTO venues (venue_name, city, state) VALUES (?,?,?)''', (venue[0], venue[1], venue[2]))
	venues = c.execute('''SELECT * FROM venues''')
	venue_dic = {venue[1]:venue[0] for venue in venues}
	conn.commit()
	conn.close()
	return venue_dic

def event_table_update(db_name, events, artist_dic, venue_dic):
	conn = sqlite3.connect(db_name)
	c = conn.cursor()
	for event in events:
		try:
			date = datetime.date(int('20' + event['Date'][6:8]), int(event['Date'][:2]), int(event['Date'][3:5]))
			time = time_conversion(event['Time'])
			event_time = datetime.datetime.combine(date,time)
			c.execute('''INSERT INTO events (artist_id, venue_id, show_datetime) VALUES (?, ?, ?)''', 
					(artist_dic[event['Artist']], venue_dic[event['Venue']], event_time))
		except:
			continue
	conn.commit()
	conn.close()

def time_conversion(time):
	minutes = int(time[-5:-3])
	hours = int(time[:-6])
	if 'p' in time and hours != 12:
		hours += 12
	return datetime.time(hours, minutes)

def xpath_executor(tree, expression):
	try:
		return tree.xpath(expression) + ['']
	except:
		return ['']


