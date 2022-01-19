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


logger = logging.getLogger('midi_cc_latch')
logging.basicConfig(level=logging.DEBUG)

MAX_CC_VALUE = 127


class LatchChannelCC:
    timer = None
    counter = 1
    latch = False
    value = 0

    def flip_value(self):
        self.value = 0 if self.value else MAX_CC_VALUE


def main():
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
        while True:
            msg = midiin.get_message()

            if msg:
                message, deltatime = msg
                timer += deltatime
                log_in(in_port_name, timer, message)

                channel, cc, value = message

                if value == MAX_CC_VALUE:
                    if channel in latch:
                        if cc in latch[channel]:
                            # todo: change cur_obj var name
                            cur_obj = latch[channel][cc]
                            if timer - cur_obj.timer < 0.25:
                                cur_obj.counter += 1
                                if cur_obj.counter == 3:
                                    cur_obj.latch = not cur_obj.latch
                                    cur_obj.flip_value()
                                    logger.debug(f"channel: {channel} cc: {cc} latch: {cur_obj.latch}")
                            else:
                                cur_obj.counter = 1
                        else:
                            latch[channel][cc] = LatchChannelCC()
                    else:
                        latch[channel] = {cc: LatchChannelCC()}
                    latch[channel][cc].timer = timer

                # todo: clean up, change cur_latch name, streamline logic and references
                cur_latch = False
                if channel in latch and cc in latch[channel]:
                    cur_latch = latch[channel][cc].latch

                if cur_latch:
                    if value == MAX_CC_VALUE:
                        latch[channel][cc].flip_value()
                        message[2] = latch[channel][cc].value
                        midiout.send_message(message)
                        log_out(out_port_name, timer, message)
                else:
                    midiout.send_message(message)
                    log_out(out_port_name, timer, message)


            time.sleep(0.01)
    except KeyboardInterrupt:
        print('')
    finally:
        print("Exit.")
        midiin.close_port()
        midiout.close_port()
        del midiin
        del midiout


def log_in(port_name, timer, message):
    log('IN ', port_name, timer, message)


def log_out(port_name, timer, message):
    log('OUT', port_name, timer, message)


def log(in_out, port_name, timer, message):
    format_string = "[%s][%s] @%0.6f %r"
    logger.debug(format_string % (in_out, port_name, timer, message))


if __name__ == '__main__':
    main()