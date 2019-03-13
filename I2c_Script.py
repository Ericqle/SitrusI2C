from pyftdi.i2c import I2cIOError, I2cNackError, I2cTimeoutError
import time
import threading


class I2cScript:
    def __init__(self, script_name, commands):
        self.script_name = script_name
        self.commands = commands

    def __eq__(self, script_name):
        return script_name == self.script_name

    def get_preview(self):
        preview = "Script: \n"
        for command in self.commands:
            if command.__contains__(" "):
                preview += ("Write " + command.split(" ")[1].strip('\n') + " to " + command.split(" ")[0] + "\n")
            elif command.strip('\n').__contains__('0x'):
                preview += ("Read " + command.strip('\n') + "\n")
            elif command.strip('\n').isdigit():
                preview += ("Wait " + command.strip('\n') + "ms\n")
            else:
                print((command))
                print("Error")
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
        edited_addresses = list()
        progress_segment = self.script_progress_bar.max / len(self.commands)
        self.script_preview_text_input.text = ''

        for command in self.commands:
            if command.__contains__(" "):
                try:
                    address = int(command.split(" ")[0], 16)
                    data = bytearray.fromhex(command.split(" ")[1].strip('0'))
                    self.slave.write_to(address, data)
                    if int(hex(self.slave.read_from(address, 1)[0]), 16) == data[0]:
                        edited_addresses.append(address)
                        self.script_log_label.text = (command.split(" ")[1].strip('\n')
                                                      + " has been written to "
                                                      + command.split(" ")[0])
                    else:
                        self.script_log_label.text = ("ERROR: "
                                                      + command.split(" ")[1].strip('\n')
                                                      + " could not be written to "
                                                      + command.split(" ")[0])
                except I2cNackError:
                    print("w1")
                except I2cIOError:
                    print("w1")
                except I2cTimeoutError:
                    print("w1")
                self.script_progress_bar.value += progress_segment
            elif command.strip('\n').__contains__('0x'):
                try:
                    address = int(command.strip('\n'), 16)
                    reg_data = hex(self.slave.read_from(address, 1)[0])
                    self.script_log_label.text = reg_data + " read from " + command.strip('\n')
                    self.script_progress_bar.value += progress_segment
                except I2cNackError:
                    print("r1")
                except I2cIOError:
                    print("r1")
                except I2cTimeoutError:
                    print("r1")
            elif command.strip('\n').isdigit():
                time.sleep((int(command)/1000) % 60)
                self.script_log_label.text = "Waiting..."
                self.script_progress_bar.value += progress_segment
            else:
                self.script_preview_text_input.text = "Error"
            self.script_preview_text_input.text += self.script_log_label.text + '\n'
        self.script_log_label.text = "End Script"
        self.script_progress_bar.value = 0

