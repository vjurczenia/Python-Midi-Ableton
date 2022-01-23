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
import tkinter as tk
from tkinter import *
from tkinter import ttk
from functools import partial
import abc

import rtmidi
import rtmidi.midiutil as midiutil


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


class MidiProcessor:
    timer = None
    latch = {}
    midiin = in_port_name = None
    midiout = out_port_name = None

    def __init__(self, input_port, output_port):
        self.midiin, self.in_port_name = midiutil.open_midiinput(input_port)
        self.midiout, self.out_port_name = midiutil.open_midioutput(output_port)
        self.timer = time.time()

    def process_message(self):
        msg = self.midiin.get_message()

        if msg:
            message, deltatime = msg
            self.timer += deltatime
            self.log_in(self.in_port_name, self.timer, message)

            channel, cc, value = message

            if value == MAX_CC_VALUE:
                if channel in self.latch:
                    if cc in self.latch[channel]:
                        # todo: change cur_obj var name
                        cur_obj = self.latch[channel][cc]
                        if self.timer - cur_obj.timer < 0.25:
                            cur_obj.counter += 1
                            if cur_obj.counter == 3:
                                cur_obj.latch = not cur_obj.latch
                                cur_obj.flip_value()
                                logger.debug(f"channel: {channel} cc: {cc} latch: {cur_obj.latch}")
                        else:
                            cur_obj.counter = 1
                    else:
                        self.latch[channel][cc] = LatchChannelCC()
                else:
                    self.latch[channel] = {cc: LatchChannelCC()}
                self.latch[channel][cc].timer = self.timer

            # todo: clean up, change cur_latch name, streamline logic and references
            cur_latch = False
            if channel in self.latch and cc in self.latch[channel]:
                cur_latch = self.latch[channel][cc].latch

            if cur_latch:
                if value == MAX_CC_VALUE:
                    self.latch[channel][cc].flip_value()
                    message[2] = self.latch[channel][cc].value
                    self.midiout.send_message(message)
                    self.log_out(self.out_port_name, self.timer, message)
            else:
                self.midiout.send_message(message)
                self.log_out(self.out_port_name, self.timer, message)

    def close_ports(self):
        self.midiin.close_port()
        self.midiout.close_port()
        del self.midiin
        del self.midiout

    def log_in(self, port_name, timer, message):
        self.log('IN ', port_name, timer, message)


    def log_out(self, port_name, timer, message):
        self.log('OUT', port_name, timer, message)


    def log(self, in_out, port_name, timer, message):
        format_string = "[%s][%s] @%0.6f %r"
        logger.debug(format_string % (in_out, port_name, timer, message))


class PortsFrame(ttk.Frame):
    available_ports = []
    selected_port = None
    list_frame = None

    def __init__(self, master):
        super().__init__(master)
        self.list_frame = ttk.Frame(self)
        ttk.Button(self, text="Edit", command=self.edit_ports).pack()
        self.list_frame.pack()
        self.update_available_ports()
        self.edit_ports()

    def set_available_ports(self, ports=None, midiio=None):
        if ports is None:
            ports = midiio.get_ports()

        self.available_ports = []
        if ports:
            for portno, name in enumerate(ports):
                self.available_ports.append([portno, name, False])

    @abc.abstractmethod
    def update_available_ports(self, api=rtmidi.API_UNSPECIFIED):
        return

    def clear_list_frame(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

    def refresh_ports(self):
        self.clear_list_frame()
        self.update_available_ports()

        for i, port in enumerate(self.available_ports):
            if port[0] == self.selected_port:
                ttk.Label(self.list_frame, text="*").grid(column=0, row=i)
            ttk.Label(self.list_frame, text=port[0]).grid(column=1, row=i)
            ttk.Label(self.list_frame, text=port[1]).grid(column=2, row=i)

    def edit_ports(self):
        def set_port(port):
            self.selected_port = port
            self.refresh_ports()

        self.clear_list_frame()

        for i, port in enumerate(self.available_ports):
            ttk.Button(self.list_frame, text=f"{port[0]} {port[1]}", command=partial(set_port, port[0])).grid(column=0, row=i)


class InputPortsFrame(PortsFrame):
    def update_available_ports(self, api=rtmidi.API_UNSPECIFIED):
        midiin = rtmidi.MidiIn(midiutil.get_api_from_environment(api))
        self.set_available_ports(midiio=midiin)


class OutputPortsFrame(PortsFrame):
    def update_available_ports(self, api=rtmidi.API_UNSPECIFIED):
        midiout = rtmidi.MidiOut(midiutil.get_api_from_environment(api))
        self.set_available_ports(midiio=midiout)


class Root(tk.Tk):
    ports_container_frame = None
    input_ports_frame = None
    output_ports_frame = None
    run_frame = None
    midi_processor = None

    def __init__(self):
        super().__init__()
        self.title("MIDI CC Latch")

        self.ports_container_frame = ttk.Frame(self)
        self.ports_container_frame.pack()

        self.input_ports_frame = InputPortsFrame(self.ports_container_frame)
        self.input_ports_frame.pack(side=LEFT)

        self.output_ports_frame = OutputPortsFrame(self.ports_container_frame)
        self.output_ports_frame.pack(side=RIGHT)

        self.run_frame = ttk.Frame(self)
        self.run_frame.pack()

        # todo: change to stop when running, start when not running
        ttk.Button(self.run_frame, text="Start/Stop", command=self.start_stop).pack()

        # todo: add frame listing actively latched cc's

    def start_stop(self):
        # todo: don't instantiate new processor if ports have not changed
        input_port = self.input_ports_frame.selected_port
        output_port = self.output_ports_frame.selected_port
        if not self.midi_processor:
            self.midi_processor = MidiProcessor(input_port, output_port)
            self.run()
        else:
            self.midi_processor.close_ports()
            self.midi_processor = None

    def run(self):
        # todo: test latency, consider multithreading, add passthrough when off
        if self.midi_processor:
            self.midi_processor.process_message()
            self.after(1, self.run)


def main():
    # todo: make the whole thing look nicer
    root = Root()
    root.mainloop()


if __name__ == '__main__':
    main()
