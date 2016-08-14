# -*- coding: utf-8 -*-
# @Author: Charles Starr
# @Date:   2016-07-27 21:44:47
# @Last Modified by:   Charles Starr
# @Last Modified time: 2016-08-14 12:59:31

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from lxml import html
import datetime
import sqlite3
import time as tm
from helpers import *

def main(db_filename):
	db_file = db_filename
	driver = webdriver.Firefox()
	get_tm_events(driver, '70114', 'n186')
	events = extract_events(driver)
	artist_list = field_extraction(events, 'Artist')
	artist_dic = simple_table_update(db_file, artist_list, 'artists', 'artist_name')
	city_list = field_extraction(events, 'City')
	city_dic = simple_table_update(db_file, city_list, 'cities', 'city_name')
	state_list = field_extraction(events, 'State')
	state_dic = simple_table_update(db_file, state_list, 'states', 'state_name')
	venue_dic = venue_table_update(db_file, normalize_venue(events), city_dic, state_dic)
	event_table_update(db_file, events, artist_dic, venue_dic)

def get_tm_events(driver, location, time_window):
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
			try:
				summary = xpath_executor(event,'./td[2]/div[1]/div[1]/a[1]/text()')[0]
				details = xpath_executor(event,'./td[2]/div[1]/div[3]/a/text()')
				venue = xpath_executor(event,'./td[3]/div[1]/a/text()')[0].strip()
				city = xpath_executor(event,'./td[3]/div[1]/abbr[1]/text()')[0].strip()
				state = xpath_executor(event,'./td[3]/div[1]/abbr[2]/text()')[0].strip()
				date = xpath_executor(event,'./td[4]/div[1]/span[1]/text()[1]')[0].strip()
				time = xpath_executor(event,'./td[4]/div[1]/span[1]/text()[2]')[0].strip()
				#details preffered because it gives exact artist information
				event_dic = {'Date':datetime.date(int('20' + date[6:8]), int(date[:2]), int(date[3:5])), 
							'Venue':venue, 
							'Artist':summary, 
							'Time':time_conversion(time), 
							'City':city, 
							'State':state}
				if len(details) > 1:
					for artist in details:
						cp = event_dic.copy()
						cp['Artist'] = artist
						events.append(cp)
				else:
					events.append(event_dic)
			except:
				print 'fuckups'
		if page_html.xpath('//div[@class="browsePagi"]/a[@onclick="nextPage();"]'):
			driver.find_element_by_xpath('//div[@class="browsePagi"]/a[@onclick="nextPage();"]').click()
			tm.sleep(3)		
		else:
			break
	return events

def normalize_venue(event_dic):
	#standardizes venue fields to all fields in db
	venue_list = []
	for event in event_dic:
		venue_list.append((event['Venue'],'', event['City'], event['State'],'', '', ''))
	return set(venue_list)

def time_conversion(time):
	minutes = int(time[-5:-3])
	hours = int(time[:-6])
	if 'p' in time and hours != 12:
		hours += 12
	return datetime.time(hours, minutes)




