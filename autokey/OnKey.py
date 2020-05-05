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

# Why this script?
# "§", which opens "Select other" is shift+alt_gr+s in Ubuntu sv_dvorak.
# This results in Onshape thinking that only "s" is pressed.
# (I think the reason that I have to actually send "`" is because that is the key
# for the Javascript keycode on US keyboards.

import os
import subprocess
import time

# AutoKey API reference: https://autokey.github.io/

# How to replace a key:
# Check correct keycode with QWERTY keyboard in browser console
# document.body.onkeydown = e => console.log(e);
# --> keyCode: 192
# (This is NOT the same as the input/kernel keycode used in xmodmap)
# Google for javascript keycode 192 (grave accent)
# Map unused keyboard keycode (97 - presumably F13 place?) with xmodmap to the found key
# xmodmap -pke   to find unused key and also figure out the X name for the key to use
# xmodmap -e 'keycode 97 = grave'
# Send the keycode using <codeXX>

# Note: Keys without modifiers in the target keyboard layout should be possible
#       to send directly. E.g. send_keys('a')

# TODO: Actually support sending different keys by listening in code

# X keycode: X keysym
key_map = { 97: 'grave' }

notif_title = 'OnKey'
notif_msg = ''

# Map the key if needed
modmap = subprocess.run(['/usr/bin/xmodmap', '-pke'], capture_output=True)
mapped_key = False
for keycode, keysym in key_map.items():
    if f'keycode {keycode:3} = {keysym}'.encode('utf-8') not in modmap.stdout:
        subprocess.run(['xmodmap', '-e', f'keycode {keycode} = {keysym}'])
        mapped_key = True

if mapped_key:
    notif_msg += 'Mapped keys'


keyboard.send_keys(f'<code{next(iter(key_map.keys()))}>')


if 'last_notification' not in store:
    last_notification = None
else:
    last_notification = store.get_value('last_notification')

# Warn the user that keys are being replaced and might be replaced in other tabs
# if they happen to match the window title filter.
ONE_DAY = 24 * 3600
now = time.time()
if not last_notification or now - last_notification > ONE_DAY:
    if not notif_msg:  
        notif_msg += 'Key replacer is active'
    
if notif_msg:
    subprocess.run(['notify-send', '-t', '1000', notif_title, notif_msg])
    last_notification = now
    store.set_value('last_notification', last_notification)
