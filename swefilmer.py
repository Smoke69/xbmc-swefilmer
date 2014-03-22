# -*- coding: utf-8 -*-
import cookielib
import HTMLParser
import os
import re
import time
import urllib
import urllib2

SAVE_FILE = True
BASE_URL = 'http://www.swefilmer.com/'
USERAGENT = ' Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

class Swefilmer:

    class MyHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
            return urllib2.HTTPRedirectHandler.http_error_302(self, req, fp,
                                                              code, msg,
                                                              headers)

        http_error_301 = http_error_303 = http_error_307 = http_error_302


    def __init__(self, xbmc, xbmcplugin, xbmcgui, xbmcaddon):
        self.xbmc = xbmc
        self.xbmcplugin = xbmcplugin
        self.xbmcgui = xbmcgui
        self.xbmcaddon = xbmcaddon
        temp = self.xbmc.translatePath(
            os.path.join(self.xbmcaddon.Addon().getAddonInfo('profile').\
                             decode('utf-8'), 'temp'))
        if not os.path.exists(temp):
            os.makedirs(temp)
        cookiejarfile = os.path.join(temp, 'swefilmer_cookies.dat')
        self.cookiejar = cookielib.LWPCookieJar(cookiejarfile)
        if os.path.exists(cookiejarfile):
            self.cookiejar.load()

        cookieprocessor = urllib2.HTTPCookieProcessor(self.cookiejar)
        opener = urllib2.build_opener(Swefilmer.MyHTTPRedirectHandler,
                                      cookieprocessor)
        urllib2.install_opener(opener)

    def get_url(self, url, filename=None, referer=None, data=None):
        """Send http request to url.
        Send the request and return the html response.
        Sends cookies, receives cookies and saves them.
        Resonse html can be saved in file for debugging.
        """
        self.xbmc.log('get_url' + ((' (' + filename + ')')
                                   if filename else '') + ': ' +
                      str(url))
        req = urllib2.Request(url)
        req.add_header('User-Agent', USERAGENT)
        if referer:
            req.add_header('Referer', referer)
        response = urllib2.urlopen(req, data)
        url = response.geturl()
        html = response.read()
        response.close()
        self.cookiejar.save()

        if filename and SAVE_FILE:
            filename = self.xbmc.translatePath('special://temp/' + filename)
            file = open(filename, 'w')
            file.write(html)
            file.close()
        return html

    def login(self, username, password):
        """Login to the site.
        First check if cookies from earlier login exist and are not about
        to expire.
        Login has the side effect of getting cookies which are then used in
        subsequent requests to the site.
        """
        # TODO: what if user changes settings for credentials and cookies
        # are intact?
        for cookie in self.cookiejar:
            if cookie.name.find('phpsugar_') > -1:
                if (cookie.expires - time.time())/3600/24 > 0:
                    return True
                break
        self.cookiejar.clear()
        url = BASE_URL + 'login.php'
        form = {'username' : username,
                'pass' : password,
                'remember' : '1',
                'ref' : '',
                'Login' : 'Logga in' }
        data = urllib.urlencode(form)
        data = data.encode('utf-8') # data should be bytes
        html = self.get_url(url, 'login.html', data=data)
        if html.find('<div class="error_msg') > -1:
            return False
        return True

    def convert(self, val):
        if isinstance(val, unicode):
            val = val.encode('utf8')
        elif isinstance(val, str):
            try:
                val.decode('utf8')
            except:
                pass
        return val

    def parameters_string_to_dict(self, str):
        """Parses parameter string and returns dictionary of keys and values.
        """
        params = {}
        if str:
            pairs = str[1:].split("&")
            for pair in pairs:
                split = pair.split('=')
                if (len(split)) == 2:
                    key = self.convert(urllib.unquote_plus(split[0]))
                    value = self.convert(urllib.unquote_plus(split[1]))
                    params[key] = value
        return params

    def unpack(self, p, a, c, k):
        while c > 0:
            c -= 1
            if k[c]:
                p = re.sub('\\b' + self.baseN(c, a) + '\\b', k[c], p)
        return p

    def baseN(self, num, b, numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
        return ((num == 0) and numerals[0]) or \
            (self.baseN(num // b, b, numerals).lstrip(numerals[0]) + \
                 numerals[num % b])

    def addCookies2Url(self, url):
        c = ''
        for cookie in self.cookiejar:
            if cookie.domain_specified and cookie.domain in url:
                c += cookie.name + '=' + cookie.value + ';'
        if len(c) > 0:
            url += '|Cookie=' + urllib.quote(c)
        return url

    def parse(self, html, part_pattern, url_and_name_pattern,
              img_pattern):
        # check for more pages
        pagination = [
            BASE_URL + x for x in
            re.findall('<div class="fastphp".*<a href="(.+?)">n&auml;sta',
                       html)
            if not 'class="disabled' in x]
        html = re.findall(part_pattern, html, re.DOTALL)
        if not html:
            return []
        htmlParser = HTMLParser.HTMLParser()
        url_and_name = [(x[0], htmlParser.unescape(x[1])) for x in
                        re.findall(url_and_name_pattern, html[0])]
        img = [None]*len(url_and_name)
        if img_pattern:
            img = re.findall(img_pattern, html[0])
            if len(img) != len(url_and_name):
                raise Exception('found ' + str(len(img)) +
                                ' images but ' + str(len(url_and_name)) +
                                ' names!')
        ret = zip(url_and_name, img)
        return ret, pagination

    def scrape_list(self, html):
        return self.parse(
            html,
            part_pattern='<div class="filmcontent">(.+?)<div id="sidebar">',
            url_and_name_pattern=\
                '<div class="movief"><a href="(.+?)">(.+?)</a></div>',
            img_pattern='<img src="(.+?)"[ ]+alt=.+?/></a>')

    def scrape_categories(self, html):
        return self.parse(
            html,
            part_pattern="<ul id='ul_categories'>(.+?)<ul class='hidden_li'>",
            url_and_name_pattern='<li class=.+?<a href="(.+?)">(.+?)</a>',
            img_pattern=None)

    def scrape_series(self, html):
        return self.parse(
            html,
            part_pattern='<ul class=\'hidden_li\'>(.+?)</ul>',
            url_and_name_pattern='<a href="(.+?)">(.+?)</a>',
            img_pattern=None)

    def scrape_video(self, html):
        if html.find('id="restricted_video"') > -1:
            # registered users only, not logged in?
            return None
        name = re.findall('class="filmcontent".+?title="(.+?)"', html,
                          re.DOTALL)
        if not name:
            name = 'unknown'
        else:
            name = name[0]
        description = re.findall(
            '>Beskrivning<.*?<p>(.+?)</p>', html, re.DOTALL)
        self.xbmc.log('scrape_video: description=' + str(description))
        img = re.findall(
            '<div class="filmaltiimg">.*?<img src="(.+?)".*?</div>', html,
            re.DOTALL)
        self.xbmc.log('scrape_video: img=' + str(img))
        url = re.findall('<iframe .*?src="(.+?)" ', html)
        self.xbmc.log('scrape_video: url=' + str(url[0]))
        if 'docs.google.com' in url[0]:
            return name, description, img, self.scrape_googledocs(url[0])
        document = self.get_url(url[0], 'document.html')
        flashvars = re.findall('<param name="flashvars" value="(.+?)">',
                               document)
        if len(flashvars) > 0:
            return name, description, img, self.scrape_video_vk(flashvars[0])
        else:
            url = self.scrape_video_registered(document)
            if not url:
                return
            url = self.addCookies2Url(url)
            return name, description, img, [('', url)]

    def scrape_googledocs(self, url):
        html = self.get_url(url, 'googledocs.html')
        formats = re.findall('"fmt_list":"(.+?)"', html)[0].split(',')
        streams = re.findall('"url_encoded_fmt_stream_map":"(.+?)"',
                             html)[0].split(',')
        urls = [self.addCookies2Url(urllib2.unquote(x).split('\\u0026')[1]
                                    .split('\\u003d')[1]) for x in streams]
        return zip(formats, urls)

    def scrape_video_vk(self, flashvars):
        names = [x[3:] for x in re.findall('(url[0-9]+)=.+?&amp;', flashvars)]
        urls = re.findall('url[0-9]+=(.+?)&amp;', flashvars)
        return zip(names, urls)

    def scrape_video_registered(self, html):
        script = re.findall(
            '(<script type=\'text/javascript\'>eval\(function\(.*}\(.*)', html)
        if len(script) > 0:
            pack = re.findall(
                '}\(\'(.+?[^\\\])\',([0-9]+),([0-9]+),\'(.+?)\'\.split',
                script[0])[0]
            unpacked = self.unpack(pack[0], int(pack[1]), int(pack[2]),
                                   pack[3].split('|'))
            url = re.findall('file:"(.+?)"', unpacked)[0]
            self.xbmc.log('scrape_video_registered: url= ' + str(url))
            return url
        self.xbmc.log('scrape_video_registered: search for videoSrc')
        videosrc = re.findall('videoSrc = "(.+?)"', html)
        if videosrc:
            self.xbmc.log('scrape_video_registered: url= ' + str(videosrc[0]))
            return videosrc[0]

    def new_menu_html(self):
        url = BASE_URL + 'newvideos.html'
        return self.get_url(url, 'new.html')

    def top_menu_html(self):
        url = BASE_URL + 'topvideos.html'
        return self.get_url(url, 'top.html')

    def favorites_menu_html(self):
        url = BASE_URL + 'favorites.php?a=show'
        return self.get_url(url, 'favorites.html')

    def categories_menu_html(self):
        return self.get_url(BASE_URL, 'categories.html')

    def search_menu_html(self, search_string):
        url = BASE_URL + 'search.php?' + \
            urllib.urlencode({'keywords': search_string})
        return self.get_url(url, 'search.html')

    def menu_html(self, url):
        return self.get_url(url, 'menu.html')

    def video_html(self, url):
        if 'ajax_request' in url:
            url = eval(url.replace('false', 'False').replace('true', 'True'))
        return self.get_url(url, 'video.html')
