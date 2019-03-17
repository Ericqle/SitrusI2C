from kivy.uix.screenmanager import Screen
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.factory import Factory
from pyftdi.i2c import I2cController, I2cNackError, I2cIOError, I2cTimeoutError
from pyftdi.ftdi import FtdiError
from pyftdi.usbtools import UsbToolsError
from usb.core import USBError
from I2c_Script import I2cScript
import ntpath
import re
import csv
ntpath.basename("a/b/c")


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


class I2cTabbedPanelItem(TabbedPanelItem):
    pass


class I2CScreen(Screen):
    script_list = list()
    lane_list = list()
    slave_device = None
    script_pop_up_reference = None

    @staticmethod
    def open_write_prompt(address):
        write_pop_up = Factory.I2cWritePopup()
        write_pop_up.address = address
        write_pop_up.open()

    @staticmethod
    def validate_input(text):
        valid = re.compile(r"^[a-fA-F0-9]{2,4}$")
        if not valid.match(text.replace("0x", "")):
            return False
        else:
            return True

    @staticmethod
    def get_valid_value_form(value):
        if len(value) > 2:
            value = value.strip('0')
            return value
        else:
            return value

    def write(self, address, value):
        if self.slave_device is not None:
            if value != '':
                try:
                    temp_address = int(address, 16)
                    if self.validate_input(value):
                        data = bytearray.fromhex(self.get_valid_value_form(value))
                        self.slave_device.write_to(temp_address, data)  # write
                        self.show_details(address, self.read(address))  # read and refresh
                    else:
                        format_error = Factory.ErrorPopup()
                        format_error.text = "ERROR: invalid input (must be a 2->4 digit hex value)"
                        format_error.open()
                except FtdiError:
                    usb_slave_error = Factory.ErrorPopup()
                    usb_slave_error.text = "Error: No usb device (it may have been disconnected)"
                    usb_slave_error.open()
                except I2cNackError:
                    pass
                except I2cIOError:
                    pass
                except I2cTimeoutError:
                    pass

    def read(self, address):
        if self.slave_device is not None:
            try:
                address = int(address, 16)
                reg_data = hex(self.slave_device.read_from(address, 1)[0])  # read
                return reg_data
            except FtdiError:
                usb_slave_error = Factory.ErrorPopup()
                usb_slave_error.text = "Error: No usb device (it may have been disconnected)"
                usb_slave_error.open()
            except I2cNackError:
                pass
            except I2cIOError:
                pass
            except I2cTimeoutError:
                pass
            return "Read_Fail"
        else:
            no_slave_error = Factory.ErrorPopup()
            no_slave_error.text = "Error: No Save Device"
            no_slave_error.open()
            return ''

    def get_dual_display_read(self, address):
        reg_data = self.read(address)
        return bin(int(reg_data, 16))[2:].zfill(8) + " (" + reg_data + ")"

    def configure_ftdi(self, port_address):
        try:
            i2c = I2cController()
            i2c.configure('ftdi://ftdi:232h/1')
            slave_device = i2c.get_port(int(port_address, 16))
            slave_device.configure_register(bigendian=True, width=2)
            self.slave_device = slave_device
        except USBError:
            usb_error = Factory.ErrorPopup()
            usb_error.text = str(USBError)
            usb_error.open()
        except UsbToolsError:
            usb_tool_error = Factory.ErrorPopup()
            usb_tool_error.text = str(UsbToolsError)
            usb_tool_error.open()
        except I2cIOError:
            i2c_io_error = Factory.ErrorPopup()
            i2c_io_error.text = str(I2cIOError)
            i2c_io_error.open()

    def configure_lane_tabs(self):
        self.i2c_tabbed_panel.clear_widgets()
        self.i2c_tabbed_panel.clear_tabs()

        for lane in self.lane_list:
            new_tab = I2cTabbedPanelItem(text=lane.name)
            new_tab.i2c_recycle_View.data = [{'address': address.i2c_address, 'chip_pin': address.chip_pin_name,
                                              'value': address.value,
                                              'default': address.default + ' (' + hex(int(address.default, 2)) + ')'}
                                             for address in lane.i2c_address_list]
            self.i2c_tabbed_panel.add_widget(new_tab)
        pass

    def show_details(self, address, value):
        current_lane_name = self.i2c_tabbed_panel.current_tab.text

        for lane in self.lane_list:
            if current_lane_name == lane.name:

                for i2c_address in lane.i2c_address_list:
                    if address == i2c_address.i2c_address:
                        i2c_address.value = value  # from read
                        self.bit_recycle_view.data = ({'text': bit} for bit in i2c_address.bits)

    def open_read_lane(self):
        if self.slave_device is not None:
            read_lane_popup = Factory.ReadLanePopup()
            read_lane_popup.lane_name = self.i2c_tabbed_panel.current_tab.text
            for string in self.read_all_in_lane():
                read_lane_popup.data += string + '\n'
            read_lane_popup.open()
        else:
            no_slave_error = Factory.ErrorPopup()
            no_slave_error.text = "Error: No Save Device"
            no_slave_error.open()

    def read_all_in_lane(self):
        strings = list()
        current_tab = self.i2c_tabbed_panel.current_tab
        for lane in self.lane_list:
            if current_tab.text == lane.name:
                for i2c_address in lane.i2c_address_list:
                    string = i2c_address.i2c_address + ": " + self.read(i2c_address.i2c_address)
                    strings.append(string)
        return strings

    def open_write_lane(self):
        if self.slave_device is not None:
            write_all_popup = Factory.WriteAllPopup()
            if self.write_all_in_lane() is True:
                write_all_popup.text = "All addresses have successfully been written to default values"
            else:
                write_all_popup.text = "Error occured while writing"
            write_all_popup.open()
        else:
            no_slave_error = Factory.ErrorPopup()
            no_slave_error.text = "Error: No Save Device"
            no_slave_error.open()

    def write_all_in_lane(self):
        status = True
        current_tab = self.i2c_tabbed_panel.current_tab
        for lane in self.lane_list:
            if current_tab.text == lane.name:
                for i2c_address in lane.i2c_address_list:
                    value = hex(int(i2c_address.default, 2))
                    if value.replace("0x", '').__len__() == 1:
                        value = '0' + value.replace("0x", '')
                    value = value.replace("0x", '')

                    self.write(i2c_address.i2c_address, value)

                    if self.read(i2c_address.i2c_address) == hex(int(i2c_address.default, 2)):
                        pass
                    else:
                        status = False
        return status

    def load_script(self, file_path):
        if path_leaf(file_path) in self.script_list:
            pass
        elif file_path.__contains__(".csv"):
            with open(file_path) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=';')
                commands = list()

                for row in csv_reader:
                    if 'write' in row:
                        command_sequence = row.copy()[0: 4]
                        commands.append(command_sequence)
                    elif 'wait' in row:
                        command_sequence = row.copy()[0: 2]
                        commands.append(command_sequence)
                    elif 'read' in row:
                        command_sequence = row.copy()[0: 2]
                        commands.append(command_sequence)
            self.script_list.append(I2cScript(path_leaf(file_path), commands))

    def show_script_preview(self, script_name, preview):
        self.script_pop_up_reference.currently_selected_script = script_name
        self.script_pop_up_reference.script_preview_text_input.text = preview

    def run_script(self):
        if self.slave_device is not None:
            for script in self.script_list:
                if script.script_name == self.script_pop_up_reference.currently_selected_script:
                    script.execute(self.slave_device, self.script_pop_up_reference.script_log_label,
                                   self.script_pop_up_reference.script_progress_bar,
                                   self.script_pop_up_reference.script_preview_text_input)

    @staticmethod
    def open_load_script():
        Factory.I2cLoadScriptPopup().open()

    def open_run_script(self):
        if self.slave_device is not None:
            self.script_pop_up_reference = Factory.I2cRunScriptPopup()
            self.script_pop_up_reference.scripts_recycle_view.data = [{'script_name': script.script_name,
                                                                       'script_preview': script.get_preview()}
                                                                      for script in self.script_list]
            self.script_pop_up_reference.open()
        else:
            no_slave_error = Factory.ErrorPopup()
            no_slave_error.text = "Error: No Save Device"
            no_slave_error.open()

