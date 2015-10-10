# -*- coding: utf-8 -*-
import urllib
import urllib2
import os.path
import re
import xbmcplugin
import xbmcaddon
import xbmcgui

path = os.path.dirname(os.path.realpath(__file__))
icon = os.path.join(path, 'icon.png')
addon = xbmcaddon.Addon(id='plugin.video.eurosport')
hd = addon.getSetting('maxQuality') == '1'
language = int(addon.getSetting('language'))

base_url = [
        'http://video.eurosport.co.uk',
        'http://video.eurosport.com',
        'http://video.eurosport.de',
        'http://video.eurosport.es',
        'http://video.eurosport.fr',
        'http://video.it.eurosport.com',
        'http://video.eurosport.ru'
    ][language]

body = '/_ajax_/video_section_v8/video_section_videos_list_v8.zone?O2=1&mime=text%%2fxml&site=%s&langueid=%i&domainid=%i'
    
body_params_tuple = [
        ('vib', 0, 127),
        ('vid', 0, 117),
        ('vde', 1, 128),
        ('vie', 6, 122),
        ('vid', 3, 117),
        ('vid', 4, 129),
        ('vid', 15, 116)
    ][language]
    
ajax_url = base_url + body % body_params_tuple

categories = {
    'latest'            : '&Order=6',
    'popular'           : '&Order=1',
    'soccer'            : '&Order=6&sportid=22',
    'tennis'            : '&Order=6&sportid=57',
    'cycling'           : '&Order=6&sportid=18',
    'snooker'           : '&Order=6&sportid=52',
    'basketball'        : '&Order=6&sportid=8',
    'moto'              : '&Order=6&familyid=10',
    'boxing'            : '&Order=6&familyid=16',
    'rugby'             : '&Order=6&sportid=44',
    'athletics'         : '&Order=6&sportid=6',
    'watersports'       : '&Order=6&familyid=12',
    'wintersports'      : '&Order=6&familyid=13',
    'golf'              : '&Order=6&sportid=28',
    'handball'          : '&Order=6&sportid=30',
    'volleyball'        : '&Order=6&sportid=62',
    'horse'             : '&Order=6&sportid=70',
    'others'            : '&Order=6&sportid=95',
    }

def get_stream_url(webpage):
    regex_get_stream = 'name="twitter:player:stream".*?content="(.+?)"'
    try:
        html = urllib2.urlopen(webpage).read()
        stream_url = re.findall(regex_get_stream, html)[0]
    except: return False
    if hd: return stream_url.replace('-700-512-288', '-2300-1024-576')
    return stream_url

def list_videos(url_body, date = '', current_page = 1):
    if date:
        url = ajax_url + url_body + '&date=' + date
    else:
        url = ajax_url + url_body
    try:
        xml = urllib2.urlopen(url).read()
    except: return False
    regex_video_info = '<div id=.*?class="video">.*?<a href="(.+?)".*?title="(.+?)">.*?<img src="(.+?)".*?<div class="duration">(.+?)<.*?class="since">(.+?)<'
    videos = re.findall(regex_video_info, xml)
    item_added = False
    for video in videos:
        try:
            title = video[1].replace('&quot;', '"').replace('&amp;', '&')
            url = base_url + video[0]
            thumb = video[2]
            duration = video[3]
            try:
                splitted_duration = duration.split(':')
                duration_in_seconds = int(splitted_duration[0])*60 + int(splitted_duration[1])
            except: duration_in_seconds = 0
            date = video[4]
            for part in date.split(' '):
                if part.count('/') == 2:
                    date = part.replace('/', '.')
                    break
            if add_video(title, date, thumb, url, duration_in_seconds): item_added = True
        except: continue
    last_date = re.findall('data-last-date="(.+?)"', xml)[0].replace(' ', '%20')
    if last_date and not categories['popular'] in url_body and len(videos)>1:
        add_category('%s (%i)' % (translation(30103), current_page+1), 'list-videos', url_body, last_date, current_page+1)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    return item_added

def add_video(title, date, thumb, url, duration_in_seconds = 0):
    link = sys.argv[0] + '?url=' + urllib.quote_plus(url) + '&mode=play-video'
    item = xbmcgui.ListItem('%s - %s' % (date, title), iconImage=icon, thumbnailImage=thumb)
    item.setInfo(type='Video', infoLabels={'Title' : title})
    item.addStreamInfo('video', {'duration': duration_in_seconds})
    item.setProperty('IsPlayable', 'true')
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=link, listitem=item)

def add_category(title, mode, category, date = '', page_number = 1, thumb = ''):
    link = sys.argv[0] + '?mode=' + mode + '&url=' + urllib.quote_plus(category) + '&date=' + urllib.quote_plus(date) + '&page=%i' % page_number
    liz = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=thumb)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=link, listitem=liz, isFolder=True)
    
def play_video(url):
    try:
        stream_url = get_stream_url(url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=stream_url))
        return True
    except: return False

def translation(id):
    return addon.getLocalizedString(id).encode('utf-8')
 
def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split('&')
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict
    
def warning(text, title = 'Eurosport', time = 4500):
    xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (title, text, time, icon))
    
params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
next_page = urllib.unquote_plus(params.get('page', ''))
date = urllib.unquote_plus(params.get('date', ''))

if mode == 'play-video':
    if not play_video(url): warning(translation(30104))
elif mode == 'list-videos':
    if not list_videos(url, date, int(next_page)): warning(translation(30105))
else:
    add_category(translation(30106), 'list-videos', categories['latest'])
    add_category(translation(30107), 'list-videos', categories['popular'])
    add_category(translation(30109), 'list-videos', categories['soccer'])
    add_category(translation(30110), 'list-videos', categories['tennis'])
    add_category(translation(30116), 'list-videos', categories['snooker'])
    add_category(translation(30112), 'list-videos', categories['cycling'])
    add_category(translation(30114), 'list-videos', categories['boxing'])
    add_category(translation(30113), 'list-videos', categories['moto'])
    add_category(translation(30108), 'list-videos', categories['athletics'])
    add_category(translation(30121), 'list-videos', categories['rugby'])
    add_category(translation(30117), 'list-videos', categories['basketball'])
    add_category(translation(30120), 'list-videos', categories['golf'])
    add_category(translation(30111), 'list-videos', categories['watersports'])
    add_category(translation(30118), 'list-videos', categories['wintersports'])
    #add_category(translation(30115), 'list-videos', categories['handball'])
    #add_category(translation(30122), 'list-videos', categories['volleyball'])
    #add_category(translation(30123), 'list-videos', categories['horse'])
    add_category(translation(30119), 'list-videos', categories['others'])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))