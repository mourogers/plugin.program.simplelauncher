import xbmcaddon
import xbmcgui
import xbmc
import xbmcvfs
import xbmcplugin
import json
import os
import subprocess
import sys
import urllib.parse
import time
import subprocess

class SimpleLauncher:
    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.addon_path = xbmcvfs.translatePath(self.addon.getAddonInfo('path'))
        self.data_path = xbmcvfs.translatePath(self.addon.getAddonInfo('profile'))
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        self.programs_file = os.path.join(self.data_path, 'programs.json')

    def get_programs(self):
        if os.path.exists(self.programs_file):
            with open(self.programs_file, 'r') as f:
                return json.load(f)
        return []

    def save_programs(self, programs):
        with open(self.programs_file, 'w') as f:
            json.dump(programs, f)

    def add_program(self, title, year, description, image, fanart, clearlogo, path):
        programs = self.get_programs()
        programs.append({
            'title': title,
            'year': year,
            'description': description,
            'image': image,
            'fanart': fanart,
            'clearlogo': clearlogo,
            'path': path,
            'lastplayed': 0
        })
        self.save_programs(programs)
        self.refresh_view()

    def edit_program(self, index):
        programs = self.get_programs()
        program = programs[index]
        dialog = xbmcgui.Dialog()

        title = dialog.input("Enter program title", defaultt=program['title'])
        year = dialog.input("Enter year", defaultt=program['year'])
        description = dialog.input("Enter description", defaultt=program['description'])
        image = dialog.browse(2, "Select thumbnail image", "files", ".jpg|.png", defaultt=program['image'])
        fanart = dialog.browse(2, "Select fanart image", "files", ".jpg|.png", defaultt=program['fanart'])
        clearlogo = dialog.browse(2, "Select clearlogo image", "files", ".png", defaultt=program.get('clearlogo', ''))
        path = dialog.browse(1, "Select program", "files", defaultt=program['path'])

        if title and path:
            programs[index] = {
                'title': title,
                'year': year,
                'description': description,
                'image': image,
                'fanart': fanart,
                'clearlogo': clearlogo,
                'path': path,
                'lastplayed': program['lastplayed']
            }
            self.save_programs(programs)
            xbmcgui.Dialog().notification("Success", f"Updated program: {title}", xbmcgui.NOTIFICATION_INFO, 5000)
            self.refresh_view()
        else:
            xbmcgui.Dialog().notification("Error", "Failed to update program", xbmcgui.NOTIFICATION_ERROR, 5000)

    def remove_program(self, index):
        programs = self.get_programs()
        removed_program = programs.pop(index)
        self.save_programs(programs)
        xbmcgui.Dialog().notification("Success", f"Removed program: {removed_program['title']}", xbmcgui.NOTIFICATION_INFO, 5000)
        self.refresh_view()

    def launch_program(self, path):
        programs = self.get_programs()
        for program in programs:
            if program['path'] == path:
                program['lastplayed'] = int(time.time())
                break
        self.save_programs(programs)
        self.refresh_view()

        if xbmc.getCondVisibility('system.platform.windows'):
            os.startfile(path)
        elif xbmc.getCondVisibility('system.platform.linux'):
            try:
                import os
                import re
                import subprocess
                
                xbmc.log(f"Attempting to launch desktop file: {path}", level=xbmc.LOGINFO)
                
                # Parse the .desktop file to extract the Exec command
                try:
                    with open(path, 'r') as f:
                        desktop_content = f.readlines()
                    
                    exec_cmd = None
                    for line in desktop_content:
                        if line.startswith('Exec='):
                            exec_cmd = line[5:].strip()
                            break
                    
                    if exec_cmd:
                        xbmc.log(f"Found Exec command: {exec_cmd}", level=xbmc.LOGINFO)
                        
                        # Check if it's a Steam URL
                        if 'steam://' in exec_cmd:
                            xbmc.log("Detected Steam URL, handling specifically", level=xbmc.LOGINFO)
                            
                            # Extract the Steam URL
                            steam_url_match = re.search(r'steam://\S+', exec_cmd)
                            if steam_url_match:
                                steam_url = steam_url_match.group(0)
                                xbmc.log(f"Extracted Steam URL: {steam_url}", level=xbmc.LOGINFO)
                                
                                # Launch the Steam URL using flatpak-spawn
                                subprocess.Popen(['flatpak-spawn', '--host', 'xdg-open', steam_url])
                                xbmc.log(f"Launched Steam URL with xdg-open: {steam_url}", level=xbmc.LOGINFO)
                            else:
                                # If we couldn't extract the URL, just run the command
                                subprocess.Popen(['flatpak-spawn', '--host', 'sh', '-c', exec_cmd])
                                xbmc.log(f"Launched full command: {exec_cmd}", level=xbmc.LOGINFO)
                        else:
                            # Not a Steam URL, just run the command normally
                            subprocess.Popen(['flatpak-spawn', '--host', 'sh', '-c', exec_cmd])
                            xbmc.log(f"Launched command: {exec_cmd}", level=xbmc.LOGINFO)
                    else:
                        xbmc.log("No Exec line found in .desktop file, falling back to xdg-open", level=xbmc.LOGERROR)
                        subprocess.Popen(['flatpak-spawn', '--host', 'xdg-open', path])
                except Exception as e:
                    xbmc.log(f"Error processing .desktop file: {e}", level=xbmc.LOGERROR)
                    # Fall back to xdg-open
                    subprocess.Popen(['flatpak-spawn', '--host', 'xdg-open', path])
            except Exception as e:
                xbmc.log(f"All launch methods failed: {e}", level=xbmc.LOGERROR)
                print(f"An error occurred while trying to launch: {e}")
                
        elif xbmc.getCondVisibility('system.platform.osx'):
            subprocess.Popen(['open', path])

    def refresh_view(self):
        xbmc.executebuiltin('Container.Refresh')
        xbmc.executebuiltin('RefreshRSS')  # This updates widgets

    def add_program_dialog(self):
        dialog = xbmcgui.Dialog()
        title = dialog.input("Enter program title")
        if not title:
            return
        year = dialog.input("Enter year")
        description = dialog.input("Enter description")
        image = dialog.browse(2, "Select thumbnail image", "files", ".jpg|.png")
        fanart = dialog.browse(2, "Select fanart image", "files", ".jpg|.png")
        clearlogo = dialog.browse(2, "Select clearlogo image", "files", ".png")
        path = dialog.browse(1, "Select program", "files")

        if title and path:
            self.add_program(title, year, description, image, fanart, clearlogo, path)
            xbmcgui.Dialog().notification("Success", f"Added program: {title}", xbmcgui.NOTIFICATION_INFO, 5000)
        else:
            xbmcgui.Dialog().notification("Error", "Failed to add program", xbmcgui.NOTIFICATION_ERROR, 5000)

    def show_programs(self):
        programs = self.get_programs()
        listing = []

        is_widget = xbmc.getCondVisibility('Window.IsActive(home)') == 1

        programs.sort(key=lambda x: x['lastplayed'], reverse=True)

        if not is_widget:
            list_item = xbmcgui.ListItem(label="[COLOR green]Add New Program[/COLOR]")
            url = f"plugin://{self.addon.getAddonInfo('id')}/?action=add"
            listing.append((url, list_item, True))

        for index, program in enumerate(programs):
            list_item = xbmcgui.ListItem(label=program['title'])

            # Expanded art dictionary to include clearlogo
            art_dict = {
                'thumb': program['image'],
                'icon': program['image'],
                'poster': program['image'],
                'landscape': program['image'],
                'fanart': program['fanart']
            }

            # Add clearlogo if it exists
            if program.get('clearlogo'):
                art_dict['clearlogo'] = program['clearlogo']

            list_item.setArt(art_dict)

            list_item.setInfo('video', {
                'title': program['title'],
                'year': program['year'],
                'plot': program['description'],
                'lastplayed': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(program['lastplayed']))
            })

            if not is_widget:
                list_item.addContextMenuItems([
                    ('Edit', f'RunPlugin(plugin://{self.addon.getAddonInfo("id")}/?action=edit&index={index})'),
                    ('Remove', f'RunPlugin(plugin://{self.addon.getAddonInfo("id")}/?action=remove&index={index})')
                ])

            url = f"plugin://{self.addon.getAddonInfo('id')}/?action=launch&path={urllib.parse.quote(program['path'])}"
            listing.append((url, list_item, False))

        xbmcplugin.addDirectoryItems(handle=int(sys.argv[1]), items=listing, totalItems=len(listing))
        xbmcplugin.setContent(int(sys.argv[1]), 'videos')
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LASTPLAYED)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

if __name__ == '__main__':
    launcher = SimpleLauncher()
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    if params.get('action') == 'launch':
        launcher.launch_program(urllib.parse.unquote(params['path']))
    elif params.get('action') == 'add':
        launcher.add_program_dialog()
    elif params.get('action') == 'edit':
        launcher.edit_program(int(params['index']))
    elif params.get('action') == 'remove':
        launcher.remove_program(int(params['index']))
    else:
        launcher.show_programs()