# -*- coding: utf-8 -*-
from copy import deepcopy
from mocks import Xbmc, Xbmcplugin, Xbmcgui, Xbmcaddon
import navigation
import swefilmer
import unittest
from navigation import Navigation
import sys

class FirstTests(unittest.TestCase):
    def setUp(self):
        self.xbmc = Xbmc(Xbmc.LOGNOTICE)
        self.xbmcplugin = Xbmcplugin(self.xbmc)
        self.xbmcgui = Xbmcgui()
        self.xbmcaddon = Xbmcaddon()

    def test_swefilmer(self):
        swe = swefilmer.Swefilmer(self.xbmc, self.xbmcplugin, self.xbmcgui,
                                  self.xbmcaddon)
        swe.get_url(swefilmer.BASE_URL)

    def test_navigation(self):
        swe = swefilmer.Swefilmer(self.xbmc, self.xbmcplugin, self.xbmcgui,
                                  self.xbmcaddon)
        nav = navigation.Navigation(self.xbmc, self.xbmcplugin, self.xbmcgui,
                                    self.xbmcaddon, swe, 'plugin', '1', '')
        username, password = nav.get_credentials()
        swe.login(username, password)

    def test_traverse_all(self):
        dir_items = self.diritems()
        self.traverse_video = True
        goal = [int(x) for x in args]
        self.traverse(dir_items, [], goal)

    def diritems(self, params=None):
        self.xbmcplugin.reset()
        swe = swefilmer.Swefilmer(self.xbmc, self.xbmcplugin, self.xbmcgui,
                                  self.xbmcaddon)
        nav = Navigation(self.xbmc, self.xbmcplugin, self.xbmcgui,
                         self.xbmcaddon, swe, 'plugin', '1', params)
        nav.dispatch()
        return self.xbmcplugin.dir_items

    def traverse(self, dir_items, stack, goal=[]):
        print '***** stack: ' + str(stack)
        i = 0
        if len(goal) > 0:
            print '***** goal: ' + str(goal)
            i = goal.pop(0) - 1
        for (handle, url, listitem, isFolder) in dir_items[i:]:
            i += 1
            params = '?' + url.split('?')[1]
            if isFolder or (self.traverse_video and url.find('plugin') == 0):
                if listitem.caption == self.xbmcaddon.Addon().getLocalizedString(30301):
                    continue
                stack.append(i)
                print '***** selecting %d: %s' % (i, listitem.caption)
                self.diritems(params)
                new_list = deepcopy(self.xbmcplugin.dir_items)
                self.traverse(new_list, stack, goal)
            else:
                continue
        if len(stack) > 0:
            stack.pop()
        return

if __name__ == '__main__':
    global args
    args = sys.argv[1:]
    sys.argv = sys.argv[:1]
    unittest.main()
