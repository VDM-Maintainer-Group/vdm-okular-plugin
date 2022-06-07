#!/usr/bin/env python3
import os, time, json, dbus
import subprocess as sp
from pathlib import Path
from pyvdm.interface import CapabilityLibrary, SRC_API

DBG = 1
SLOT = 0.40
PROG_NAME = 'okular'

class OkularPlugin(SRC_API):
    def _gather_records(self):
        sess = dbus.SessionBus()
        dbus_iface = dbus.Interface(sess.get_object('org.freedesktop.DBus', '/'),
                    dbus_interface='org.freedesktop.DBus')
        okular_names = filter(lambda x:x.startswith('org.kde.okular'), sess.list_names())
        records = dict()

        for _name in okular_names:
            ## get content status from dbus
            _iface = dbus.Interface(sess.get_object(_name, '/okular'),
                    dbus_interface='org.kde.okular')
            _path  = _iface.currentDocument()
            _page  = _iface.currentPage()
            ## get window status from x11
            _pid = dbus_iface.GetConnectionUnixProcessID(_name)
            _window = self.xm.get_windows_by_pid(_pid)[0]
            ##
            records[_path] = {
                'page': _page,
                'window':{
                    'desktop': _window['desktop'],
                    'states':  _window['states'],
                    'xyhw':    _window['xyhw']
                }
            }
            pass

        return records

    def _rearrange_window(self, records):
        _time = time.time()
        _limit = len(records) * SLOT
        sess = dbus.SessionBus()
        dbus_iface = dbus.Interface(sess.get_object('org.freedesktop.DBus', '/'),
                    dbus_interface='org.freedesktop.DBus')

        okular_names = list()
        while len(okular_names)<len(records) or time.time()-_time<_limit:
            okular_names = list( filter(lambda x:x.startswith('org.kde.okular'), sess.list_names()) )

        for _name in okular_names:
            try:
                _pid = dbus_iface.GetConnectionUnixProcessID(_name)
                _status = records[ _iface.currentDocument() ]
                _window = self.xm.get_windows_by_pid(_pid)[0]
                ##
                _iface = dbus.Interface(sess.get_object(_name, '/okular'),
                        dbus_interface='org.kde.okular')
                _iface.goToPage( _status['page'] )
                ##
                s = _status['window']
                self.xm.set_window_by_xid(_window['xid'], s['desktop'], s['states'], s['xyhw'])
            except:
                pass     
        pass

    def onStart(self):
        self.xm = CapabilityLibrary.CapabilityHandleLocal('x11-manager')
        return 0

    def onStop(self):
        return 0

    def onSave(self, stat_file):
        ## gathering records
        records = self._gather_records()
        ## write to file
        with open(stat_file, 'w') as f:
            json.dump(records, f)
            pass
        return 0

    def onResume(self, stat_file):
        ## load stat file with failure check
        with open(stat_file, 'r') as f:
            _file = f.read().strip()
        if len(_file)==0:
            return 0
        else:
            try:
                records = json.loads(_file)
            except:
                return -1
        ## open windows
        for item in records.keys():
            sp.Popen([ PROG_NAME, item['path'] ], start_new_session=True)
        ## rearrange windows by title
        self._rearrange_window(records)
        return 0

    def onClose(self):
        ## force close all
        os.system( f'killall {PROG_NAME}' )
        return 0
    pass

if __name__ == '__main__':
    _plugin = OkularPlugin()
    _plugin.onStart()

    ## gathering records
    records = _plugin._gather_records()
    print( json.dumps(records, indent=4) )
    pass
