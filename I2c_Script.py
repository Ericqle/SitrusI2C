from pyftdi.i2c import I2cIOError, I2cNackError, I2cTimeoutError
import time
import threading
import re


class I2cScript:
    def __init__(self, script_name, commands):
        self.script_name = script_name
        self.commands = commands

    def __eq__(self, script_name):
        return script_name == self.script_name

    def get_preview(self):
        preview = "Script: \n"
        for command in self.commands:
            if 'write' in command:
                preview += ("Write " + command[3] + " to bit(s) " + command[2] + " in " + command[1] + "\n")
            elif 'wait' in command:
                preview += ("Wait " + command[1] + "ms\n")
            else:
                preview += "Error: unknown command"
        return preview

    def execute(self, slave, script_log_label, script_progress_bar, script_preview_text_input):
        run = Run(self.commands, slave, script_log_label, script_progress_bar, script_preview_text_input)
        run.start()


class Run(threading.Thread):
    def __init__(self, commands, slave, script_log_label, script_progress_bar, script_preview_text_input):
        super(Run, self).__init__()
        self.commands = commands
        self.slave = slave
        self.script_log_label = script_log_label
        self.script_progress_bar = script_progress_bar
        self.script_preview_text_input = script_preview_text_input

    def run(self):
        progress_segment = self.script_progress_bar.max / len(self.commands)
        self.script_preview_text_input.text = ''

        for command in self.commands:
            if 'write' in command:
                try:
                    if command[2] == '[7:0]':
                        self.script_log_label.text = "full write"
                        # address = int(command[1], 16)
                        # data = bytearray.fromhex(command[3].strip('0x'))
                        # self.slave.write_to(address, data)
                        # if int(hex(self.slave.read_from(address, 1)[0]), 16) == data[0]:
                        #     self.script_log_label.text = "write success"
                        # else:
                        #     self.script_log_label.text = "write fail"
                    elif re.compile('\\[.*:.*\\]').match(command[2]):
                        self.script_log_label.text = "partial write"
                    elif command[2].isdigit():
                        self.script_log_label.text = "bit write"
                except I2cNackError:
                    print("w1")
                except I2cIOError:
                    print("w1")
                except I2cTimeoutError:
                    print("w1")
                self.script_progress_bar.value += progress_segment
            elif 'wait' in command:
                time.sleep((int(command[1])/1000) % 60)
                self.script_log_label.text = "Waiting..."
                self.script_progress_bar.value += progress_segment
            else:
                self.script_preview_text_input.text = "Error"
            self.script_preview_text_input.text += self.script_log_label.text + '\n'
        self.script_log_label.text = "End Script"
        self.script_progress_bar.value = 0

