# onshape-utils
Utilities for Onshape

## OnKey

AutoKey script for Linux to replace a key sent to Onshape. For
example, to fix "Select Other" when using a non-default keyboard
layout.

Install [AutoKey](https://github.com/autokey/autokey/wiki/Installing),
start it, create a folder and add the script to the folder. You can
also add the JSON file to get a configuration for "Select Other" with
Onshape in Firefox. Configure AutoKey to autostart, to always have the
script active.

Assign a hotkey (the key you want to fix, e.g. `'`) and set the window
filter to only match Onshape tabs (e.g. `.*\|.* - Mozilla Firefox`)
for the Onkey script. Modify the script to change which key gets sent
to Onshape.
