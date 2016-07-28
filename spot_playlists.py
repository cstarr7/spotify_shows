# -*- coding: utf-8 -*-
# @Author: Charles Starr
# @Date:   2016-07-10 12:49:18
# @Last Modified by:   Charles Starr
# @Last Modified time: 2016-07-26 22:59:05

import user_input
import sqlite3


def main():
	artist_set = get_artists('no_shows.sqlite')
	user = user_input.User()
	print user.common_artists(artist_set)


def get_artists(db_file):
	#retrieves artists from the db
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	artist_blob = c.execute('''SELECT artist_name FROM artists''')
	return set([x[0] for x in artist_blob])

main()