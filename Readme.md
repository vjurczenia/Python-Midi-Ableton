# python-midi-cc-latch

A utility to help convert momentary buttons on a midi controller to latching ones.

## Why:
* The [midiplus x3 mini](https://www.midiplus.com.tw/en/product-detail/X3mini/) has buttons that can send midi cc. They send a value of 127 when pressed, but a value of 0 when released. This is fine for mapping to transport controls like play and stop in Ableton, but can't be used to, let's say, crank the reverb on an instrument (and leave it cranked).

## How:
* Ahmad Moussa's [readme](https://github.com/AhmadMoussa/Python-Midi-Ableton/blob/master/Readme.md) (below) has a general gist of what needs to be done, so I followed it then expanded upon it.
* The script endlessly loops, listening for input. When it receives a cc value of 127, it updates some metadata in a helper dictionary. Using that data, it checks whether "a button has been triple clicked" then inverts the latch flag for that cc on that midi channel and keeps track of its value.
* For all cc messages, if the latch flag is set for that cc on that channel, and the value coming in is 127, then just flip the value stored in the helper dict and return it. Ignore all other values.

## Resources:
* [python-rtmidi](https://github.com/SpotlightKid/python-rtmidi)
  * Main library used.
* [mido](https://github.com/mido/mido)
  * Could be useful in the future. Gave me the idea to look for something like this when I found [this script](https://github.com/mungewell/mpd-utils/blob/master/utils/mpd218_pad2keys.py) in a [reddit thread](https://www.reddit.com/r/synthesizers/comments/c8awr8/free_midi_translator_for_win_10/).
* [Python-Midi-Ableton](https://github.com/AhmadMoussa/Python-Midi-Ableton)
  * It's just the readme but it was very helpful. The readme is included below for posterity.

---
---

# Python-Midi-Ableton

A tutorial on how to send midi signals from a python script to a midi track in ableton live

## What you'll need:
* Python (duh...), I am using (python 3.7.3)[https://www.python.org/downloads/]
* Pip install this package [pip install python-rtmidi](https://pypi.org/project/python-rtmidi/)
* Install this software: [loopMidi by Tobias Erichsen](http://www.tobias-erichsen.de/software/loopmidi.html)
* A DAW (short for Digital Audio Workstation), I am using Ableton live 10 Standard 10.0.6
* Windows?

## Why is this relevant:
* Because I couldn't find any resources on how to send Midi Notes from a Python script to Ableton for windows
* You want to send Midi Signals from Python to Ableton Live on a Windows pc

## What are we actually going to do:
1. We can't communicate directly between ableton live and python
2. We need to create a virtual [port](https://en.wikipedia.org/wiki/Port_(computer_networking)) to which we can send midi signals from python and to which ableton will be "listening" to
3. We need to write a script that send midi signals, for that purpose we will use the [python-rtmidi](https://pypi.org/project/python-rtmidi/) package
4. We need to setup ableton to listen to the port

## What you'll have to do:
1. Install python and the python rt-midi package ![like this](https://i.imgur.com/pV6qP5U.png)
2. Install the loopMidi software, once you launch it you should see something like this: ![like this](https://i.imgur.com/ytzI7MQ.png)
3. Now press the little plus button in the bottom-left corner: ![like this](https://i.imgur.com/mX2Ug8S.png) 
    You'll see that it'll add an item to list. Voila, we created a new port. 
4. Now let's write the python script that'll send some notes to the port:

```
import time
import rtmidi

midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()

# here we're printing the ports to check that we see the one that loopMidi created. 
# In the list we should see a port called "loopMIDI port".
print(available_ports)

# Attempt to open the port
if available_ports:
    midiout.open_port(1)
else:
    midiout.open_virtual_port("My virtual output")

note_on = [0x90, 60, 112]
note_off = [0x80, 60, 0]
midiout.send_message(note_on)
time.sleep(0.5) 
# I tried running the script without having to invoke the sleep function but it doesn't work. 
# If someone could enlighten me as to why this is, I'd be more than grateful.
midiout.send_message(note_off)

del midiout
```
Here we're simply sending a middle C note as MIDI to the port. Save this in a `.py` file, we'll need to run it later.

5. Now let's set up Ableton:
    * Go to Preferences -> MIDI link where you should see the loopMidi port as an input and output port. Set the loopMidi port's track and sync to "On" ![like this](https://i.imgur.com/Z0L9YNh.png)
    * Create a new Midi track in your project                                                                                           ![Create a new midi track in your project](https://i.imgur.com/njphzc5.png)
    * Set the input of the track to be the "loopMidi Port" and set the track to "In"
    * Also don't forget to load the track with a synth. An ableton stock sound should also do the trick.

6. Run the script `python "scriptname".py` in your command prompt, and you should be able to hear ableton play back a C note at you.

I hope this helped, if anything is unclear or you have suggestions let me know.
