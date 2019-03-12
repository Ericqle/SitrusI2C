from pyftdi.i2c import I2cIOError, I2cNackError, I2cTimeoutError
import time
import threading


class I2cScript:
    def __init__(self, script_name, commands):
        self.script_name = script_name
        self.commands = commands  # list or array of read in script lines

    def __eq__(self, script_name):
        return script_name == self.script_name

    def get_preview(self):
        preview = "Script: \n"
        for command in self.commands:
            if command.__contains__(" "):
                preview += ("Write " + command.split(", ")[1] + " to " + command.split(", ")[0] + "\n")
            else:
                preview += ("Read " + command + "\n")
        return preview

    def execute(self, slave, script_log_label, script_progress_bar):
        run = Run(self.commands, slave, script_log_label, script_progress_bar)
        run.start()


class Run(threading.Thread):
    def __init__(self, commands, slave, script_log_label, script_progress_bar):
        super(Run, self).__init__()
        self.commands = commands
        self.slave = slave
        self.script_log_label = script_log_label
        self.script_progress_bar = script_progress_bar

    def run(self):
        progress_segment = self.script_progress_bar.max / len(self.commands)
        try:
            for command in self.commands:
                address = int(command.split(" ")[0], 16)
                data = bytearray.fromhex(command.split(", ")[1].strip('0'))
                self.slave.write_to(address, data)
                if int(hex(self.slave.read_from(address, 1)[0]), 16) == data[0]:
                    self.script_log_label.text = (command.split(", ")[1]
                                                    + " has been written to "
                                                    + command.split(", ")[0]
                                                    + "\n")
                else:
                    self.script_log_label.text = ("ERROR: "
                                                    + command.split(", ")[1]
                                                    + " could not be written to "
                                                    + command.split(", ")[0]
                                                    + "\n")
                self.script_progress_bar.value += progress_segment
                time.sleep(.5)
            self.script_progress_bar.value = 0
        except I2cNackError:
            print("1")
        except I2cIOError:
            print("2")
        except I2cTimeoutError:
            print("3")
