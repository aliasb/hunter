#!/usr/bin/env python
#-*- coding: utf-8 -*-

# code by alias_b
# 본 프로그램은 사용자 과실에 대한 법적 책임을 지지 않습니다.

# hunter(find seed)
# for synology
# version 141212
# Completed DSM : 4.3-3810, 5.0-4418(beta), 5.0-4493(update7), 5.0-4528(update2)
# python 2.7.8

# license of python plugins
### bencode : BitTorrent Open Source License
### beautifulsoup4 : MIT
### mechanize : BSD

from bs4 import BeautifulSoup
import mechanize, bencode
import time, re, os, StringIO, hashlib, ConfigParser, ast
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#PATH_CONF#

#===============================================
get_hash_to_log = []
get_title_to_list = []
list_genre = []

conf = None

def read_conf_file() :
	try:
		global conf
		conf = ConfigParser.ConfigParser()
		conf.read(PATH_CONF)
		conf.sections()
	except Exception, e:
		print e
		print "setting.conf : 잘못된 값이 있습니다."
		print "프로그램이 종료 됩니다."
		sys.exit()

def read_list_file(chown) :
	path_list = conf.get("path", "list")
	if os.path.isfile(path_list) == True :
		listf = open(path_list, "r")

		while 1: 
			line = listf.readline()
			if not line: break 
			if line.find("#") == 0 or line == "\\n" : continue
			tmp = line
			line = line.replace("\\n","")
			line = line.replace(" ","")
			line = line.lower()
			sp = line.split(",")

			pass_sp = True
			for ch in sp :
				if ch == "" :
					pass_sp = False
					break

			basename_list = os.path.basename(path_list)
			if pass_sp == False or len(sp) != 4 :
				print "%s : [%s] 잘못된 형식입니다." %(basename_list, tmp.replace("\\n",""))
				continue

			try:
				if list_genre.index(sp[3]) >= 0 :
					get_title_to_list.append(sp)
				else :
					print "%s : [%s] 장르값이 잘못 되었습니다." %(basename_list, tmp.replace("\\n",""))
			except Exception, e:
				print "%s : [%s] 장르값이 잘못 되었습니다." %(basename_list, tmp.replace("\\n",""))

		listf.close()

	if  os.path.isfile(path_list) == False or len(get_title_to_list) == 0 :
		listf = open(path_list, "w")
		listf.write("""#################################################
# code by alias_b
# 본 프로그램은 사용자 과실에 대한 법적 책임을 지지 않습니다.
#
# 주석 처리된 부분은 지우지마세요.
#
# 대소문자, 띄어쓰기 상관없습니다.
#
# 파싱 사이트
# http://www.torrentbest.net
#
# 형식
# 프로그램이름, 화질, 릴그룹, 장르(드라마 = drama, 예능 = ent, 시사/다큐 = docu)
# ex) 유한도전, 720P, WITH, ent
# ex) 유한도전, *, *, ent  ==> 유한도전에 관련된 토렌트 모두 받습니다
#################################################""")
		listf.close()
		os.system("chown "+chown+" "+path_list)
		print "%s 리스트를 작성해주세요." %(path_list)
		sys.exit()

def read_log_file(chown) :
	path_log = conf.get("path", "log")
	if os.path.isfile(path_log) == True :
		logf = open(path_log, "r")
		i = 0
		while 1:
			line = logf.readline() 
			if not line: break
			if line.find("#") == 0 or line == "\\n" : continue
			if i%4 == 1 : 
				line = line.replace("\\n","")
				get_hash_to_log.append(line)
			i += 1
		logf.close()

	if  os.path.isfile(path_log) == False or len(get_hash_to_log) == 0 :
		logf = open(path_log, "w")
		logf.write("""#################################################
# code by alias_b
# 본 프로그램은 사용자 과실에 대한 법적 책임을 지지 않습니다.
#
# 주석 처리된 부분은 지우지마세요.
#
# 해쉬 값을 비교하여 일치하지 않으면 NOT equl hash가 출력됩니다.
# 일치하지 않은 파일은 받지 않습니다.
# 만약 파일을 받고 싶다면 data의 setting.conf에서 chk_hash값을 바꾸세요.
#
# 형식
# [DATE]
# hash
# name.torrent
# ==========
#################################################""")
		logf.close()
		os.system("chown "+chown+" "+path_log)

#===============================================

def set_browser():
	br = mechanize.Browser(factory=mechanize.RobustFactory())
	cj = mechanize.LWPCookieJar()
	br.set_cookiejar(cj)
	br.set_handle_equiv(True)
	br.set_handle_redirect(True)
	br.set_handle_referer(True)
	br.set_handle_robots(False)
	br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
	br.addheaders = [("User-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.4 (KHTML, like Gecko) Chrome/22.0.1229.94 Safari/537.4")]
	return br

def is_downloaded(get_hash, write_log):
	for ghash in get_hash_to_log:
		if ghash.find(get_hash) >= 0 :
			return True
	return False

def chk_title(get_name, title, start):
	if start >= len(title)-1 : return True
	
	if get_name.find(title[start].decode("utf-8")) >= 0 or title[start] == "*":
		return chk_title(get_name, title, start+1)
	return False

def make_list_url_to_conf(genre) :
	ret_url = []
	if genre == "*" :
		for get_genre in list_genre:
			ret_url = make_list_url(ret_url, get_genre)
	else :
		ret_url = make_list_url(ret_url, genre)

	return ret_url

def make_list_url(list_url, genre) :
	if genre == "*" : return list_url

	for key,path in conf.items(genre):
			for line in path.split("\\n") :
				list_url.append(line)

	return list_url

def get_active_url(br) :
	action_url = []
	parser_cache = []
	cached_genre = []
	for title in get_title_to_list:
		if conf.getboolean("option", "enable_cache") :
			cache_hit = False
			try:
				if cached_genre.index(title[3]) >= 0 :
					cache_hit = True
					for cache in parser_cache :
						if chk_title(cache[0], title, 0) :
							action_url.append(cache[1])
							break
			except Exception, e:
				cached_genre.append(title[3])
				
			if cache_hit : continue
		
		urls = make_list_url_to_conf(title[3].lower())
		for url in urls:
			try:			
				response = br.open(url)
				soup = BeautifulSoup(response.read())
			except Exception, e:
				print "%s\\n응답이 없습니다." %(url)
				continue

			links = soup.find_all(attrs={"class", "subject"})
			for link in links:
				alink = link.find("a")
				rmspace = alink.get_text().replace(" ", "")

				get_name = rmspace.lower()
				get_act_link = alink["href"].replace("../", "http://www.torrentbest.net/")

				if conf.getboolean("option", "enable_cache") :
					tmp = [get_name, get_act_link]
					parser_cache.append(tmp)
					
				if chk_title(get_name, title, 0) :
					action_url.append(get_act_link)
	return action_url

def calc_bencode(strem):
	meta = bencode.bdecode(strem)
	info = meta["info"]
	calc_hash = hashlib.sha1(bencode.bencode(info)).hexdigest().upper()
	return calc_hash

def processing(br, chown) :

	action_url = get_active_url(br)
	path_save = conf.get("path", "save")
	for url in action_url:
		try:
			response = br.open(url)
			soup = BeautifulSoup(response.read())
		except Exception, e:
			print "%s\\n응답이 없습니다." %(url)
			continue

		get_link =  soup.find(attrs={"class", "view_file"}).find("a")
		sp_link = get_link["href"].split("'")

		get_down = sp_link[1].replace("./", "http://www.torrentbest.net/bbs/")
		get_title =  soup.find(attrs={"class", "view_file"}).find("a").get_text()
		get_hash = soup.find(attrs={"class", "value"}).get_text()
		get_hash = get_hash.upper()

		now = time.localtime()
		write_log = "\\n[%04d%02d%02d %02d:%02d:%02d]\\n%s\\n%s\\n==========" %(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec, get_hash, get_title)
		if is_downloaded(get_hash.encode("utf-8"), write_log.encode("utf-8")) == False:
			print "[Download]%s" %get_title.encode("utf-8")

			try:
				response = br.open(get_down)
				res_read = response.read()
			except Exception, e:
				print "다운로드 중 문제가 발생하였습니다."
				continue

			if conf.getboolean("option", "chk_hash") == True :
				calc_hash = calc_bencode(res_read)
				print "%10s : %s" %("calc_hash", calc_hash)
			else :
				calc_hash = get_hash
						
			print "%10s : %s" %("wget_hash",get_hash)
			
			path_log = conf.get("path", "log")
			logf = open(path_log, "a")

			if calc_hash == get_hash :
				print "%s" %("\\tHASH_CHK_PASS")
				write_log = "\\n[%04d%02d%02d %02d:%02d:%02d]\\n%s\\n%s\\n==========" %(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec, get_hash, get_title)
				logf.write(write_log)

				rmsapce = get_title.replace(" ", "")
				rss_path = path_save+"/"+str(unicode(rmsapce.replace(".torrent", ".rss")))
				down_path = path_save+"/"+str(unicode(rmsapce))

				torrentf = open(rss_path, "wb")
				torrentf.write(res_read)
				torrentf.close()

				os.system("chown "+chown+" "+rss_path)
				os.system("mv "+rss_path+" "+down_path)

				print "[Done]%s" %get_title.encode("utf-8")
			else :
				print "%s" %("\\tHASH_CHK_FAILED")
				write_log = "\\n[%04d%02d%02d %02d:%02d:%02d]\\n%s\\n%s\\n==========" %(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec, "NOT equal hash", get_title)
				logf.write(write_log)
				print "[Failed]%s" %get_title.encode("utf-8")
			print '---------------------------------------------'
			logf.close()
#===================================================
if __name__ == "__main__":

	start_time = time.time()
	now = time.localtime()
	print "==========START [%04d%02d%02d %02d:%02d:%02d]" %(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)

	read_conf_file()

	list_genre = ast.literal_eval(conf.get("option", "genre"))

	chown = conf.get("runner", "chown")

	read_log_file(chown)
	read_list_file(chown)

	processing(set_browser(), chown)

	print "===============END (processing time : %.02fs) # code by alias_b" % (time.time()-start_time)
