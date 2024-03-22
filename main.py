import subprocess
import re
import time
from os import listdir, environ, popen
from os.path import isfile, join

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.LaunchAppAction import LaunchAppAction


PATH = environ["HOME"] + "/.local/share/warp-terminal/launch_configurations/"
APP_PATH = '/usr/share/applications/dev.warp.Warp.desktop'
configs = []

class DemoExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        find_configurations()
        


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        arg = event.get_query()
        arg = arg.replace('wp ', '')
        for c in configs:
            if re.search(arg, c, re.IGNORECASE):
                items.append(
                    ExtensionResultItem(
                        icon="images/icon.png",
                        name="Configuration %s" % c,
                        description="",
                        on_enter=ExtensionCustomAction({'cfg_name': c}, keep_app_open=False),
                    )
                )

        return RenderResultListAction(items)
    
class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_data()

        if is_warp_running():
            activate_warp()
        else:
            action = LaunchAppAction(APP_PATH)
            action.run()

        check_count = 0
        while check_count < 5:
            if is_warp_running() and is_warp_active_and_focused():
                break
            time.sleep(0.25)
            check_count = check_count + 1

        if is_warp_active_and_focused():
            time.sleep(0.15)
            subprocess.run(["xdotool", "key", "ctrl+shift+p"])
            subprocess.run(["xdotool", "type", data['cfg_name']])
            subprocess.run(["xdotool", "key", "Return"])


def find_configurations():
    onlyfiles = [join(PATH, f) for f in listdir(PATH) if isfile(join(PATH, f))]
    for file in onlyfiles:
        with open(file) as f:
            data = f.read()
            match = re.search(r"(?!.*Example)name: (.+)", data)
            configs.append(match.group(1))

def is_warp_running():
    process = 'warp-terminal'
    tmp = popen("ps -Af").read()
    count = tmp.count(process)

    return count > 0

def is_warp_active_and_focused():
    res = False
    windows = find_warp_windows()
    ret = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True)
    active_window = ret.stdout.replace("\n", "")
    ret = subprocess.run(["xdotool", "getwindowfocus"], capture_output=True, text=True)
    focused_window = ret.stdout.replace("\n", "")

    res = active_window in windows and focused_window in windows
    return res

def find_warp_windows():
    ret = subprocess.run(["xdotool", "search", "--class", "warp"], capture_output=True, text=True)
    warp_windows = ret.stdout
    windows = warp_windows.split('\n')
    return windows

def activate_warp():
    windows = find_warp_windows()
    if len(windows) > 0:
        window = windows[0]
        subprocess.run(["xdotool", "windowactivate", window])
        subprocess.run(["xdotool", "windowfocus", window])

if __name__ == "__main__":
    DemoExtension().run()
