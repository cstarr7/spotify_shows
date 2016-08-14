# -*- coding: utf-8 -*-
# @Author: Charles Starr
# @Date:   2016-07-18 22:16:49
# @Last Modified by:   Charles Starr
# @Last Modified time: 2016-08-14 12:49:42

import requests
from lxml import html
import sqlite3
import datetime
from helpers import *

#contains the necessary functions to retrieve venue information from https://www.wwoz.org/organizations/...

def main(db_filename):
	db_file = db_filename
	#get all venue information
	venue_list = venue_iterator()
	venue_info = venue_populator(venue_list)
	#make unique city table
	city_list = field_extraction(venue_info, 'City')
	cityid_dic = simple_table_update(db_file, city_list, 'cities', 'city_name')
	#make unique state table
	state_list = field_extraction(venue_info, 'State')
	stateid_dic = simple_table_update(db_file, state_list, 'states', 'state_name')
	#make venue table
	venueid_dic = venue_table_update(db_file, normalize_venues(venue_info), cityid_dic, stateid_dic)
	#extract all events
	events = event_iterator()
	#make unique artist table
	artist_list = field_extraction(events, 'Artist')
	artistid_dic = simple_table_update(db_file, artist_list, 'artists', 'artist_name')
	#populate events table using artistid dictionary, venueid dictionary and event date/time
	event_table_update(db_file, events, artistid_dic, venueid_dic)

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
		venue_dic['Name'] = xpath_executor(page_html, '//*[@class="page-title"]/text()')[0].strip()
		venue_dic['Street'] = xpath_executor(page_html, '//*[@class="thoroughfare"]/text()')[0].strip()
		venue_dic['City'] = xpath_executor(page_html, '//*[@class="locality"]/text()')[0].strip()
		venue_dic['State'] = xpath_executor(page_html, '//*[@class="state"]/text()')[0].strip()
		venue_dic['Postal Code'] = xpath_executor(page_html, '//*[@class="postal-code"]/text()')[0].strip()
		venue_dic['Phone'] = xpath_executor(page_html, '//a[contains(@href, "tel")]/text()')[0].strip()
		venue_dic['Website'] = xpath_executor(page_html, '//a[contains(text(), "http")]/../a/text()')[0].strip()
		venue_dics.append(venue_dic)
	return venue_dics

def normalize_venues(venue_list):
	#converts venue dictionaries into normalized tuples for insertion into the database
	normal_list = []
	for venue in venue_list:
		normal_list.append((venue['Name'], venue['Street'], venue['City'], venue['State'],
							 venue['Postal Code'], venue['Phone'], venue['Website']))
	return normal_list

def event_iterator():
	events = []
	base_url = 'https://www.wwoz.org/calendar/livewire-music?date='
	for date in date_generator():
		url = base_url + date.isoformat()
		page = requests.get(url)
		page_html = html.fromstring(page.text)
		for venue in page_html.xpath('//div[@class="panel panel-default"]'):
			venue_name = xpath_executor(venue, './/h3[@class="panel-title"]/a/text()')[0].strip()
			for show in venue.xpath('.//div[@class="col-xs-10 calendar-info"]'):
				artist = xpath_executor(show,'.//p[1]/a/text()')[0].strip()
				time = xpath_executor(show,'.//p[2]/text()')[0].strip()
				events.append({'Date':date, 'Venue':venue_name, 'Artist':artist, 'Time':time_conversion(time[time.rfind(' ')+1:])})
	return events

def time_conversion(time):
	minutes = int(time[-4:-2])
	hours = int(time[:-5])
	if 'p' in time and hours != 12:
		hours += 12
	return datetime.time(hours, minutes)