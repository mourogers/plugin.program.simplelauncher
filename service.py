import xbmc
import xbmcgui
from resources.lib.simple_launcher import SimpleLauncher

if __name__ == '__main__':
    monitor = xbmc.Monitor()
    launcher = SimpleLauncher()

    while not monitor.abortRequested():
        if monitor.waitForAbort(10):
            break

        # Update widget here if needed
        xbmc.executebuiltin('Container.Refresh')
