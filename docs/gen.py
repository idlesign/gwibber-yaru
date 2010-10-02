#!/bin/sh

PYTHONPATH=.. epydoc \
 	-n "Gwibber" \
	-u "http://www.gwibber.com/docs/" \
	-o html \
	-v gwibber.lib.GwibberPublic \
	gwibber.microblog.dispatcher.Dispatcher \
	gwibber.microblog.dispatcher.URLShorten
