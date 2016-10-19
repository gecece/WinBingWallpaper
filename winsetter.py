#!/usr/bin/env python
import log
from os.path import abspath, join as pathjoin, dirname, splitext

import _winreg as winreg
import PIL.Image as Image
import win32gui

def convert_photo_to_bmp(inpath, outpath):
    if splitext(inpath)[1] == '.bmp':
        return
    Image.open(inpath).save(outpath)

SPI_SETDESKWALLPAPER = 0x0014

class Win32WallpaperSetter():
    KEY = winreg.HKEY_CURRENT_USER
    SUB_KEY = 'Control Panel\\Desktop'
    VALUE_NAME = 'Wallpaper'
    BACKUP = True

    def __init__(self):
        self._logger = log.getChild(self.__class__.__name__)

    def _read_value(self, k, valuename = None):
        if not valuename: valuename = self.VALUE_NAME
        try:
            value = winreg.QueryValueEx(k, valuename)
            if value[1] != winreg.REG_SZ:
                self._logger.fatal('cannot handle non-REG_SZ value %s', value)
                return None
        except:
            self._logger.warn('error encountered during reading value %s', valuename, exc_info=1)
            return None
        self._logger.debug('read {} from {} get {}'.format(valuename, k, value))
        return value

    def _set_value(self, k, v, valuename = None):
        if not valuename: valuename = self.VALUE_NAME
        self._logger.debug('set %s\\%s\\%s to %s', self.KEY, self.SUB_KEY, valuename, v)
        try:
            winreg.SetValueEx(k, valuename, 0, winreg.REG_SZ, v)
        except:
            self._logger.error('error encountered during setting value %s', valuename, exc_info=1)
            return False
        self._logger.debug('set {} of {} to {} succeeds'.format(valuename, k, v))
        return True

    def set(self, path):
        k = None
        inpath = abspath(path)
        outpath = pathjoin(dirname(inpath), "wallpaper.bmp")
        # windows only supports BMP, convert before setting
        try:
            convert_photo_to_bmp(inpath, outpath)
        except Exception as ex:
            self._logger.exception(ex)
            return False

        try:
            k = winreg.OpenKey(self.KEY, self.SUB_KEY, 0, winreg.KEY_READ|winreg.KEY_SET_VALUE)
            lastvalue = self._read_value(k)
            if lastvalue and self.BACKUP:
                ret = self._set_value(k, lastvalue[0], self.VALUE_NAME+'Backup')
            self._set_value(k, '0', 'TileWallpaper')
            self._set_value(k, '10', 'WallpaperStyle')
            win32gui.SystemParametersInfo(SPI_SETDESKWALLPAPER, outpath, 1+2)
        except Exception as ex:
            ret = False
            self._logger.exception(ex)
        finally:
            if k: k.Close()
        return ret

if __name__ == '__main__':
    log.setDebugLevel(log.DEBUG)
    setter = Win32WallpaperSetter()
    setter.set(r'w.jpg', None)