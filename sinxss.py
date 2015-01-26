#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2014-08-11 13:35:56
# @Link    : https://github.com/sintrb/SinXSS
# @Version : 1.0


import hashlib
import urllib
import urllib2
import urlparse
from BeautifulSoup import BeautifulSoup
import random
import re

def md5(src):
	return hashlib.md5(src).hexdigest().upper()

class SinXSS(object):
	def __init__(self, urlmatch=lambda x: True, urlmax=-1):
		self.urlhash = {}
		self.urltodo = set()
		self.urlmatch = urlmatch
		self.urlmax = urlmax
		self.inject_str = ";!--\"'<%s>=&{()}" % ''.join([random.choice("abcdefghi1234567890") for _ in range(10)])

	def add_url(self, url):
		if self.urlmax>=0 and len(self.urlhash)>=self.urlmax:
			return
		u = urlparse.urlparse(url)
		parms = dict(urlparse.parse_qsl(u.query))
		qkeys = ' '.join(parms.keys())
		fullpath = '%s://%s%s'%(u.scheme, u.netloc, u.path)
		urlflag = fullpath + qkeys
		urlmd5 = md5(urlflag)
		if urlmd5 not in self.urlhash:
			# print 'add %s'%url
			self.urlhash[urlmd5] = urlflag
			self.urltodo.add(url)

	def reponse_of_url(self, url):
		print url
		return urllib2.urlopen(url)

	def can_inject(self, url):
		u = urlparse.urlparse(url)
		fullpath = '%s://%s%s'%(u.scheme, u.netloc, u.path)
		parms = urlparse.parse_qsl(u.query)
		can_in_parm = []
		if parms:
			rg = range(len(parms))
			for i in rg:
				ps = '&'.join(['%s=%s'%(parms[ix][0], urllib.quote(parms[ix][1] if ix!=i else self.inject_str)) for ix in rg])
				nurl = '%s?%s'%(fullpath, ps)
				try:
					html = self.reponse_of_url(nurl).read()
					html.index(self.inject_str)
					can_in_parm.append(parms[i][0])
				except:
					pass
		return can_in_parm

	def scan_url(self, url):
		html = None
		try:
			doc = urllib2.urlopen(url)
			if 'Content-Type' in doc.headers and 'html' not in doc.headers['Content-Type'].lower():
				return
			html = doc.read()
		except:
			pass
		if html:
			soup = BeautifulSoup(html)
			hrefre = re.compile('http[s]?://')
			for a in soup.findAll('a'):
				href = a.has_key('href') and a['href'].strip() or ''
				if href and href[0]!='#' and not hrefre.match(href):
					href = urlparse.urljoin(url, href)
				if not self.urlmatch(href):
					continue
				try:
					self.add_url(href)
				except UnicodeEncodeError:
					pass
			injs = self.can_inject(url)
			if injs:
				print '------->%s of %s'%(injs, url)
		else:
			pass

	def start_scan(self):
		while len(self.urltodo):
			url = self.urltodo.pop()
			self.scan_url(url)



if __name__ == '__main__':
	import sys
	xss = SinXSS(urlmatch=re.compile(r'.*/.*').match, urlmax=20)
	for v in sys.argv[1:]:
		print 'add: %s'%v
		xss.add_url(v)
	xss.start_scan()


