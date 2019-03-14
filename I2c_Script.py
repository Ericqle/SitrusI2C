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
                        address = int(command[1], 16)
                        data = bytearray.fromhex(command[3].strip('0x'))
                        self.slave.write_to(address, data)
                        if int(hex(self.slave.read_from(address, 1)[0]), 16) == data[0]:
                            self.script_log_label.text = (command[3] + " written to bit(s) " + command[2] + " in " +
                                                          command[1])
                        else:
                            self.script_log_label.text = ("Failed to write " + command[3] + " to bit(s) " + command[2] +
                                                          " in " + command[1])

                    elif re.compile('\\[.*:.*\\]').match(command[2]):
                        # Read
                        address = int(command[1], 16)
                        reg_data = '{0:08b}'.format(self.slave.read_from(address, 1)[0])

                        # Make Write Value
                        bit_range = command[2]
                        value = command[3]

                        max = 7 - int(bit_range[1])
                        min = 7 - int(bit_range[3])

                        write_value = reg_data[:max] + value + reg_data[min + 1:]
                        write_value = hex(int(write_value, 2))

                        if write_value.replace("0x", '').__len__() == 1:
                            write_value = '0' + write_value

                        # write
                        data = bytearray.fromhex(write_value.replace("0x", ''))
                        self.slave.write_to(address, data)

                        if int(hex(self.slave.read_from(address, 1)[0]), 16) == data[0]:
                            self.script_log_label.text = (command[3] + " written to bit(s) " + command[2] + " in " +
                                                          command[1])
                        else:
                            self.script_log_label.text = ("Failed to write " + command[3] + " to bit(s) " + command[2] +
                                                          " in " + command[1])

                    elif command[2].isdigit():
                        # Read
                        address = int(command[1], 16)
                        reg_data = '{0:08b}'.format(self.slave.read_from(address, 1)[0])

                        # Make Write Value
                        bit_range = command[2]
                        value = command[3]

                        bit_location = 7 - int(bit_range)

                        temp_reg_data = list(reg_data)
                        temp_reg_data[bit_location] = value
                        write_value = "".join(temp_reg_data)
                        write_value = hex(int(write_value, 2))

                        if write_value.replace("0x", '').__len__() == 1:
                            write_value = '0' + write_value

                        # write
                        data = bytearray.fromhex(write_value.replace("0x", ''))
                        self.slave.write_to(address, data)

                        if int(hex(self.slave.read_from(address, 1)[0]), 16) == data[0]:
                            self.script_log_label.text = (command[3] + " written to bit(s) " + command[2] + " in " +
                                                          command[1])
                        else:
                            self.script_log_label.text = ("Failed to write " + command[3] + " to bit(s) " + command[2] +
                                                          " in " + command[1])

                except I2cNackError:
                    break
                except I2cIOError:
                    break
                except I2cTimeoutError:
                    break
                self.script_progress_bar.value += progress_segment

            elif 'wait' in command:
                time.sleep((int(command[1])/1000) % 60)
                self.script_log_label.text = "Waiting " + command[1] + "ms"
                self.script_progress_bar.value += progress_segment

            else:
                self.script_preview_text_input.text = "Error"

            self.script_preview_text_input.text += self.script_log_label.text + '\n'

        self.script_log_label.text = "End Script"
        self.script_progress_bar.value = 0

