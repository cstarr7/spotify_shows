# -*- coding: utf-8 -*-
# @Author: Charles Starr
# @Date:   2016-07-10 12:49:18
# @Last Modified by:   Charles Starr
# @Last Modified time: 2016-08-13 20:03:46

import user_input
import venuedb_populator
import tm_events
import helpers


def main():
	helpers.rebuild_eventdb('no_shows.sqlite')
	venuedb_populator.main()
	tm_events.main()
	calendar = user_input.Event_Calendar('no_shows.sqlite')
	user = user_input.Tunes_User('my_library.xml')
	common_artists = user.dp_common_artists(calendar.artist_set())
	events = calendar.events_by_artist(common_artists)
	print events

main()