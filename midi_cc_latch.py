#!/usr/bin/env python
#
# midi_cc_latch.py
#
"""
Convert momentary CC to latch
Based on midiin_poll.py from python-rtmidi examples
Show how to receive MIDI input by polling an input port.
"""

from __future__ import print_function

import logging
import sys
import time

from rtmidi.midiutil import open_midiinput, open_midioutput


# todo: utilize logging instead of print
log = logging.getLogger('midi_cc_latch')
logging.basicConfig(level=logging.DEBUG)

in_port = sys.argv[1] if len(sys.argv) > 1 else None
out_port = sys.argv[2] if len(sys.argv) > 2 else None

try:
    # prompt if passed None
    midiin, in_port_name = open_midiinput(in_port)
    midiout, out_port_name = open_midioutput(out_port)
except (EOFError, KeyboardInterrupt):
    sys.exit()

print("Entering main loop. Press Control-C to exit.")
try:
    timer = time.time()
    latch = {}
    latch_channel_cc_dict = {
        'timer': None, 
        'counter': 1, 
        'latch': False, 
        'value': 0
        }
    while True:
        msg = midiin.get_message()

        if msg:
            message, deltatime = msg
            timer += deltatime
            print("[In ][%s] @%0.6f %r" % (in_port_name, timer, message))

            channel, cc, value = message

            if value == 127:
                if channel in latch:
                    if cc in latch[channel]:
                        # todo: change cur_dict var name
                        cur_dict = latch[channel][cc]
                        if timer - cur_dict['timer'] < 0.25:
                            cur_dict['counter'] += 1
                            if cur_dict['counter'] == 3:
                                cur_dict['latch'] = not cur_dict['latch']
                                latch[channel][cc]['value'] = abs(latch[channel][cc]['value'] - value)

                                print(latch)
                        else:
                            cur_dict['counter'] = 1
                    else:
                        latch[channel][cc] = latch_channel_cc_dict.copy()
                else:
                    latch[channel] = {cc: latch_channel_cc_dict.copy()}
                latch[channel][cc]['timer'] = timer

            # todo: clean up, change cur_latch name, streamline logic and references
            cur_latch = False
            if channel in latch and cc in latch[channel]:
                cur_latch = latch[channel][cc]['latch']

            if cur_latch:
                if value == 127:
                    latch[channel][cc]['value'] = abs(latch[channel][cc]['value'] - value)
                    message[2] = latch[channel][cc]['value']
                    midiout.send_message(message)
                    print("[Out][%s] @%0.6f %r" % (out_port_name, timer, message))
            else:
                midiout.send_message(message)
                print("[Out][%s] @%0.6f %r" % (out_port_name, timer, message))


        time.sleep(0.01)
except KeyboardInterrupt:
    print('')
finally:
    print("Exit.")
    midiin.close_port()
    midiout.close_port()
    del midiin
    del midiout