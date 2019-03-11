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

    def execute(self, slave, log_text_input, script_progress_bar):
        run = Run(self.commands, slave, log_text_input, script_progress_bar)
        run.start()


class Run(threading.Thread):
    def __init__(self, commands, slave, log_text_input, script_progress_bar):
        super(Run, self).__init__()
        self.commands = commands
        self.slave = slave
        self.log_text_input = log_text_input
        self.script_progress_bar = script_progress_bar

    def run(self):
        progress_segment = self.script_progress_bar.max / len(self.commands)
        try:
            for command in self.commands:
                if command.__contains__(" "):
                    address = int(command.split(", ")[0], 16)
                    data = bytearray.fromhex(command.split(", ")[1].replace("0x", ""))
                    self.slave.write_to(address, data)
                    if int(hex(self.slave.read_from(address, 1)[0]), 16) == data[0]:
                        self.log_text_input.insert_text(command.split(", ")[1]
                                                        + " has been written to "
                                                        + command.split(", ")[0]
                                                        + "\n")
                    else:
                        self.log_text_input.insert_text("ERROR: "
                                                        + command.split(", ")[1]
                                                        + " could not be written to "
                                                        + command.split(", ")[0]
                                                        + "\n")
                elif command.__contains__("rall"):
                    print("read all")
                elif command.__contains__("wdef"):
                    print("write to default")
                else:
                    address = int(command, 16)
                    data = self.slave.read_from(address, 1)
                    self.log_text_input.insert_text(command + " has been read. Data read: 0x" + str(data[0]) + "\n")
                self.script_progress_bar.value += progress_segment
                time.sleep(1)
            self.script_progress_bar.value = 0
        except I2cNackError:
            pass
        except I2cIOError:
            pass
        except I2cTimeoutError:
            pass
