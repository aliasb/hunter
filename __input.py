#!/usr/bin/env python
#-*- coding: utf-8 -*-

# code by alias_b
# 본 프로그램은 사용자 과실에 대한 법적 책임을 지지 않습니다.

# hunter(find seed)
# for synology
# version 141216
# Completed DSM : 4.3-3810, 5.0-4418(beta), 5.0-4493(update7), 5.0-4528(update2)
# python 2.7.8

# licenses of python plugins
### bencode : BitTorrent Open Source License
### beautifulsoup4 : MIT
### mechanize : BSD

from bs4 import BeautifulSoup
import mechanize, bencode
import time, os, hashlib, ConfigParser, ast, md5
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#PATH_CONF#

#===============================================
get_sha1_to_log = []
get_md5_to_log = []
get_title_to_list = []

conf = None

#===============================================
#===============================================

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
		list_genre = ast.literal_eval(conf.get("option", "genre"))
		while 1: 
			line = listf.readline()
			if not line: break 
			if line.find("#") == 0 or line == "\\n" : continue
			tmp = line
			line = line.replace("\\n","")
			line = line.replace(" ","")
			line = line.lower()
			sp = line.split(",")

			try:
				if get_title_to_list.index(sp) >= 0 :
					print "%s : [%s] 중복 되었습니다." %(basename_list, tmp.replace("\\n",""))
					continue
			except Exception, e:
				pass

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
		deep_search = conf.getboolean("option", "deep_search")
		while 1:
			line = logf.readline() 
			if not line: break
			if line.find("#") == 0 or line == "\\n" : continue

			if deep_search == False :
				if i%5 == 1: 
					line = line.replace("\\n","")
					get_md5_to_log.append(line)
			if i%5 == 2:
				line = line.replace("\\n","")
				get_sha1_to_log.append(line)
			
			i += 1
		logf.close()

	if  os.path.isfile(path_log) == False or len(get_sha1_to_log) == 0 :
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

#===============================================
#=============================================== validate

def is_downloaded(get_hash):
	for ghash in get_sha1_to_log:
		if ghash.find(get_hash) >= 0 :
			return True
	return False

def compare_title(get_name, title, start):
	if start >= len(title)-1 : return True
	
	if get_name.find(title[start].decode("utf-8")) >= 0 or title[start] == "*":
		return compare_title(get_name, title, start+1)
	return False

#===============================================
#=============================================== calc

def calc_md5(get_str):
	tmp = get_str.replace(" ", "")
	tmp = get_str.replace("\\n", "")
	tmp = get_str.lower()
	return md5.md5(tmp).hexdigest()

def calc_sha1(strem):
	meta = bencode.bdecode(strem)
	info = meta["info"]
	calc_hash = hashlib.sha1(bencode.bencode(info)).hexdigest().upper()
	return calc_hash

#===============================================
#=============================================== last process

def download_torrent(br, info):

	path_save = conf.get("path", "save")

	print "[Download]%s" %info[0].encode("utf-8")

	try:
		response = br.open(info[1])
		res_read = response.read()
	except Exception, e:
		print "다운로드 중 문제가 발생하였습니다."
		return

	if conf.getboolean("option", "chk_hash") == True :
		calc_hash = calc_sha1(res_read)
		print "%10s : %s" %("calc_hash", calc_hash)
	else :
		calc_hash = info[3]
				
	print "%10s : %s" %("wget_hash",info[3])
	
	path_log = conf.get("path", "log")
	logf = open(path_log, "a")

	now = time.localtime()
	if calc_hash == info[3] :
		print "%s" %("\\tHASH_CHK_PASS")
		write_log = "\\n[%04d%02d%02d %02d:%02d:%02d]\\n%s\\n%s\\n%s\\n==========" %(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec, info[2], info[3], info[0])
		logf.write(write_log)

		rmsapce = info[0].replace(" ", "")
		rss_path = path_save+"/"+str(unicode(rmsapce.replace(".torrent", ".rss")))
		down_path = path_save+"/"+str(unicode(rmsapce))

		torrentf = open(rss_path, "wb")
		torrentf.write(res_read)
		torrentf.close()

		os.system("chown "+conf.get("runner", "chown")+" "+rss_path)
		os.system("mv "+rss_path+" "+down_path)

		print "[Done]%s" %info[0].encode("utf-8")
	else :
		print "%s" %("\\tHASH_CHK_FAILED")
		write_log = "\\n[%04d%02d%02d %02d:%02d:%02d]\\n%s\\n%s\\n%s\\n==========" %(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec, info[2], "Invalid hash", info[0])
		logf.write(write_log)

		print "[Failed]%s" %info[0].encode("utf-8")
	logf.close()
	print '---------------------------------------------'

#===============================================
#=============================================== process level

def torrentbest_level_2(br, soup) :
	get_link = soup.find(attrs={"class", "view_file"}).find("a")
	sp_link = get_link["href"].split("'")

	get_down = sp_link[1].replace("./", "http://www.torrentbest.net/bbs/")
	get_title =  soup.find(attrs={"class", "view_file"}).find("a").get_text()
	get_hash = soup.find(attrs={"class", "value"}).get_text().upper()
	md5_title = calc_md5(soup.find("span", id="writeSubject").get_text().strip())

	info = [get_title, get_down, md5_title, get_hash]

	if is_downloaded(get_hash.encode("utf-8")) == False:
		download_torrent(br, info)

def torrentbest_level_1(soup, title, action_url, parser_cache) :
	
	links = soup.find_all(attrs={"class", "subject"})
	deep_search = conf.getboolean("option", "deep_search")

	for link in links:
		alink = link.find("a")
		tmp = alink.get_text()
		
		if deep_search == False :
			try:
				if get_md5_to_log.index(calc_md5(tmp)) >= 0 : 
					continue
			except Exception, e:
				pass

		tmp = tmp.replace(" ", "")
		get_title = tmp.lower()

		get_act_link = alink["href"].replace("../", "http://www.torrentbest.net/")

		if conf.getboolean("option", "enable_cache") :
			tmp_list = [get_title, get_act_link]
			parser_cache.append(tmp_list)
			
		if compare_title(get_title, title, 0) :
				action_url.append(get_act_link)

	return [action_url, parser_cache]

def torrent82_level_1(soup, title, action_url, parser_cache) :
	
	links = soup.find_all("nobr")
	deep_search = conf.getboolean("option", "deep_search")

	for link in links:
		alink = link.find("a")
		tmp = alink["title"]
		
		if deep_search == False :
			try:
				if get_md5_to_log.index(calc_md5(tmp)) >= 0 : 
					continue
			except Exception, e:
				pass

		tmp = tmp.replace(" ", "")
		get_title = tmp.lower()

		get_act_link = "http://www.torrent82.com"+alink["href"]

		if conf.getboolean("option", "enable_cache") :
			tmp_list = [get_title, get_act_link]
			print "%s, %s" %(get_title, get_act_link)
			parser_cache.append(tmp_list)
			
		if compare_title(get_title, title, 0) :
				action_url.append(get_act_link)
	sys.exit()
	return [action_url, parser_cache]


#===============================================
#===============================================

def make_url_from_genre(genre) :
	ret_url = []
	if genre == "*" :
		list_genre = ast.literal_eval(conf.get("option", "genre"))
		for get_genre in list_genre:
			if get_genre == "*" : continue
			ret_url = make_url(ret_url, get_genre)
	else :
		ret_url = make_url(ret_url, genre)

	return ret_url

def make_url(list_url, genre) :
	conf_page = conf.getint("option", "search_page")
	if conf_page < 1 or conf_page > 20 : conf_page = 1

	for key,path in conf.items(genre):
			for line in path.split("\\n") :
				for i in range(1, conf_page+1) :
					list_url.append(line+"&page="+str(i))

	return list_url

#===============================================
#===============================================

def find_active_url(br) :
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
						if compare_title(cache[0], title, 0) :
							parser_cache.remove(cache)
							action_url.append(cache[1])
			except Exception, e:
				cached_genre.append(title[3])
				pass
				
			if cache_hit : continue

		urls = make_url_from_genre(title[3].lower())

		for url in urls:
			try:			
				response = br.open(url)
				soup = BeautifulSoup(response.read())
			except Exception, e:
				print "%s\\n응답이 없습니다." %(url)
				continue

			if url.find("torrentbest") >= 0 :
				ret_list = torrentbest_level_1(soup, title, action_url, parser_cache)
			elif url.find("torrent82") >= 0 :
				ret_list = torrent82_level_1(soup, title, action_url, parser_cache)

			action_url = ret_list[0]
			parser_cache = ret_list[1]

	return action_url

#===============================================
#===============================================

def processing(br) :

	action_url = find_active_url(br)

	for url in action_url:
		try:
			response = br.open(url)
			soup = BeautifulSoup(response.read())
		except Exception, e:
			print "%s\\n응답이 없습니다." %(url)
			continue

		torrentbest_level_2(br, soup)

#===============================================
#===============================================

def main() :

	read_conf_file()
	read_log_file(conf.get("runner", "chown"))
	read_list_file(conf.get("runner", "chown"))

	processing(set_browser())

#===============================================
#===============================================

if __name__ == "__main__":
	start_time = time.time()
	now = time.localtime()

	print "==========START [%04d%02d%02d %02d:%02d:%02d]" %(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
	main()

	print "===============END (processing time : %.02fs) # code by alias_b" % (time.time()-start_time)
