#
# Copyright (C) 2020  Thomas Axelsson
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import Xlib
import Xlib.display
from Xlib import X
from Xlib import XK
import re
import argparse
from array import array

import config
import keytypes

# Xlib reference: https://tronche.com/gui/x/xlib/
# python-xlib: https://github.com/python-xlib
# http://python-xlib.sourceforge.net/doc/html/python-xlib_toc.html

# Columns in X keyboard mapping (same as displayed by xmodmap -pke)
XMOD_NOMOD = 0
XMOD_SHIFT = 1
XMOD_MODESWITCH = 2
XMOD_MODESWITCH_AND_SHIFT = 3
XMOD_ISO_LEVEL3_SHIFT = 4
XMOD_ISO_LEVEL3_SHIFT_AND_SHIFT = 5

SHORTCUT_TOOLBAR_X_OFFSET = 30
SHORTCUT_TOOLBAR_Y_OFFSET = 30
SHORTCUT_TOOLBAR_X_SPACING = 34
SHORTCUT_TOOLBAR_Y_SPACING = 30


display = Xlib.display.Display()
#window = display.get_input_focus().focus

#cls = window.get_wm_class()
#name = window.get_wm_name()

# while window:
# #if cls is None:
#     window = window.query_tree().parent
#     print(window)
#     if window == 0:
#         break
#     cls = window.get_wm_class()
#     name = window.get_wm_name()
#     print(window, cls, name)


def find_windows(parent, inst, cls):
    children = parent.query_tree().children
    res = []
    for window in children:
        wm_cls = window.get_wm_class()
        if wm_cls and wm_cls[0] == inst and wm_cls[1] == cls:
            res.append(window)
        else:
            res += find_windows(window, inst, cls)
    return res

        
# Grabbing a key for only a Window requires us to let the user specify the browser,
# or have a set of default browsers

# children = root.query_tree().children
# #children = window.query_tree().children
# for window in children:
#     cls = window.get_wm_class()
#     if not cls:
#         continue
#     inst, cls = window.get_wm_class()
#     #print(inst, cls)
#     #if cls == 'Firefox':
#     print(window.get_wm_name())
#     print(window, window.get_wm_class(), window.get_wm_name())

# we tell the X server we want to catch keyPress event

WINDOW_TITLE_FILTER = re.compile(r'.*\|.*')

def handle_event(event):
    global keycode_map
    # TODO: Should call display.refresh_keyboard_mapping when we get mapping events
    
    if event.type == X.KeyPress or event.type == X.KeyRelease:
        new_event = event
        window = event.window
        title = window.get_wm_name()
        if WINDOW_TITLE_FILTER.match(title):
            # TODO: Handle modifier, also when grabbing
            keycode = (event.detail, 0)
            if keycode in keycode_map.keys():
                new_keycode = keycode_map[keycode]
                if isinstance(new_keycode, keytypes.Shortcut):
                    print("shortcut")
                else:
                    detail = new_keycode[0]
                    #keycode = event.detail
                    shift_mask = 0 #event.state # TODO: Let user record shift state
                    props = {
                        'time': event.time, # X.CurrentTime
                        'root':  event.root,
                        'window': window,
                        'same_screen': event.same_screen,
                        'child': event.child,
                        'root_x': event.root_x,
                        'root_y': event.root_y,
                        'event_x': event.event_x,
                        'event_y': event.event_y,
                        'state': shift_mask,
                        'detail': detail
                        }
                    if event.type == X.KeyPress:
                        new_event = Xlib.protocol.event.KeyPress(**props)
                    else:
                        new_event = Xlib.protocol.event.KeyRelease(**props)
        window.send_event(new_event, propagate = True)

def grab_keys(windows):
    map_keys()
    
    for window in windows:
        window.change_attributes(event_mask = X.KeyPressMask)

        modifier = X.AnyModifier#X.ShiftMask | X.ControlMask #X.AnyModifier
        owner_events = False # Has no effect?
        for keycode in keycode_map.keys():
            # TODO: handle modifier!
            window.grab_key(keycode[0], modifier, owner_events, X.GrabModeAsync, X.GrabModeAsync)

keycode_map = {}
        
def map_keys():
    global keycode_map
    #print(chr(display.keycode_to_keysym(40, 0)))
    #print(list(display.keysym_to_keycodes(ord('`'))))
    #  key  shift+key   modeswitch?+key modeswitch?+shift+key altgr+key altgr+shift+key
    # modeswitch seems to be the characters of the/an other xkb group (Dvorak vs QWERTY)
    # ISO_Level3_Shift = altgr
    # ctrl is separate. It is sent as a separate press only, so I guess we have to release it to map Ctrl+keyA -> keyB.

    # The keyboard mapping is cached by python-xlib (updated with refresh_keyboard_mapping)
    keyboard_mapping_offset = 8 # Keycodes starts at 8 for some reason
    keyboard_mapping = display.get_keyboard_mapping(8, 255-8)
    next_keycode_candidate = keyboard_mapping_offset + 0
    
    for old_sym, new_sym in config.KEY_MAP.items():
        # Assuming first match is the key the user will press
        # Only check for key, key+shift, key+altgr, key+altgr+shift
        # --> index 0, 1, 4, 5
        old_keycodes = [c for c in display.keysym_to_keycodes(ord(old_sym)) if c[1] in [0, 1, 4, 5]]
        if not old_keycodes:
            raise Exception("You cannot press this key, as it is not in your keyboard layout: " + old_sym)
        old_keycode = old_keycodes[0]

        if isinstance(new_sym, keytypes.Shortcut):
            new_keycode = new_sym
        else:
            new_keycode = map_sym_to_keycode(new_sym)

        keycode_map[old_keycode] = new_keycode
    # Sync to make new keycodes come into effect
    display.sync()

def map_sym_to_keycode(new_sym):
    # We need our symbols to be available without shift or altgr modifiers
    # I _think_ onshape checks shift separately, i.e. it asks Javascript for the
    # key on the keyboard and shift separately.
    new_keycodes = [c for c in display.keysym_to_keycodes(ord(new_sym)) if c[1] == 0]

    if new_keycodes:
        new_keycode = new_keycodes[0]
    else:
        # Find unused keycode
        free_keycode = None
        for i in range(next_keycode_candidate, 256):
            keysyms = keyboard_mapping[i - keyboard_mapping_offset]
            if keysyms[0] == X.NoSymbol:
                free_keycode = i
                break

        if not free_keycode:
            raise Exception("Found no free keycodes. Could not map key: " + new_sym)
            # TODO: clean-up existing mappings

        next_keycode_candidate = i + 1
        print(f'Mapping "{new_sym}" to keycode {free_keycode}')
        #raise False
        #new_keysyms = [ array('I', (ord(new_sym),)) ]
        new_keysyms = [ (ord(new_sym), ) ]
        display.change_keyboard_mapping(first_keycode=free_keycode,
                                        keysyms=new_keysyms)
        new_keycode = (free_keycode, 0) # key + position (modifier)

    return new_keycode
        
def main():
#    argparse = argparse.ArgumentParser()
#    parser.add_argument('--configure', 
    
    # TODO: Monitor for new Windows
    root = display.screen().root
    windows = find_windows(root, 'Navigator', 'Firefox')
    print(windows)
    grab_keys(windows)

    while 1:
        event = root.display.next_event()
        print("event")
        handle_event(event)

    # TODO: unmap mapped keys

main()

