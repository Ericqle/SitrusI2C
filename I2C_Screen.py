from kivy.uix.screenmanager import Screen
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.factory import Factory
from pyftdi.i2c import I2cController, I2cNackError, I2cIOError, I2cTimeoutError
from pyftdi.ftdi import FtdiError
from pyftdi.usbtools import UsbToolsError
from usb.core import USBError
from I2c_Script import I2cScript
from kivy.uix.popup import Popup
from pathlib import Path
import ntpath
import re
import os
import csv
import math
ntpath.basename("a/b/c")


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


class I2cTabbedPanelItem(TabbedPanelItem):
    pass


class LutPopup(Popup):
    addresses = range(64)
    script_values = list()

    @staticmethod
    def get_lut(addresses, bin_weight_eye_adj_param1, bin_weight_eye_adj_param2, a_pre, b_main, c_post, scale_factor,
                round_checkbox):

        y_values = list()
        minimized_values = list()
        normalized_values = list()
        final_lut_ints = list()
        final_lut_bins = list()

        count = 4
        b_fix = False
        for address in addresses:
            bin_string = format(address, '06b')

            a = ((bin_weight_eye_adj_param2 * int(bin_string[0])) + (
                        bin_weight_eye_adj_param1 * int(bin_string[1]))) * a_pre

            if ((address == 12 or address == 28 or address == 44 or address == 60) or b_fix is True) and address != 0:
                b_fix = True
                b = ((2 * int(bin_string[2])) + (1 * int(bin_string[3]))) * b_main
                count -= 1
                if count == 0:
                    b_fix = False
                    count = 4
            else:
                b = ((bin_weight_eye_adj_param2 * int(bin_string[2])) + (
                            bin_weight_eye_adj_param1 * int(bin_string[3]))) * b_main

            if (address + 1) % 4 == 0:
                c = ((2 * int(bin_string[4])) + (1 * int(bin_string[5]))) * c_post
            else:
                c = ((bin_weight_eye_adj_param2 * int(bin_string[4])) + (
                            bin_weight_eye_adj_param1 * int(bin_string[5]))) * c_post

            sum_factor = a + b + c

            y_values.append(sum_factor)

        for y_value in y_values:
            minimized_values.append(y_value - min(y_values))

        for minimized_value in minimized_values:
            normalized_values.append((minimized_value / max(minimized_values)) * 63)

        for normalized_value in normalized_values:
            final_lut_ints.append(((normalized_value - 31.5) * scale_factor) + 31.5)

        if not round_checkbox.active:
            for final_lut_int in final_lut_ints:
                final_lut_bins.append(format(int(final_lut_int), '06b'))

        elif round_checkbox.active:
            i = 0
            for final_lut_int in final_lut_ints:
                if i <= 31:
                    final_lut_bins.append(format(math.ceil(final_lut_int), '06b'))
                    i += 1
                else:
                    final_lut_bins.append(format(int(final_lut_int), '06b'))
        return final_lut_bins

    def calc_lut(self):
        try:
            bin_weight_eye_adj_param1 = float(self.pam1.text)
            bin_weight_eye_adj_param2 = float(self.pam2.text)
            a_pre = float(self.a.text)
            b_main = float(self.b.text)
            c_post = float(self.c.text)
            scale_factor = float(self.scale.text)
            round_checkbox = self.round_checkbox

            # get lut valuse
            lut = self.get_lut(self.addresses, bin_weight_eye_adj_param1, bin_weight_eye_adj_param2, a_pre, b_main,
                               c_post, scale_factor, round_checkbox)

            # transpose to get 64 bit values
            lut_transposed = [''.join(s) for s in zip(*lut)]

            self.lut_text.text = ''

            lut_value_list = list()

            for row in reversed(lut_transposed):
                row = ' '.join(row[i:i+8] for i in range(0, len(row), 8))
                self.lut_text.text += (row + '\n\n')

                row = row.split(' ')
                for value in row:
                    value = ''.join(reversed(value))
                    value = "{0:#0{1}x}".format((int(value, 2)), 4)
                    lut_value_list.append(value)

            self.script_values = lut_value_list

        except ValueError:
            self.lut_text.text = 'Error: invalid input values'
        except ZeroDivisionError:
            self.lut_text.text = 'Error: invalid input values'


class I2CScreen(Screen):
    lut_script_index = 0
    script_list = list()
    lane_list = list()
    slave_device = None
    i2c_device = I2cController()
    port_address = None
    script_pop_up_reference = None

    def activate_osx(self):
        try:
            self.i2c_device = I2cController()
            self.i2c_device.configure('ftdi://ftdi:232h/1')
            self.slave_device = self.i2c_device.get_port(int(self.port_address, 16))
            self.slave_device.configure_register(bigendian=True, width=2)
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

    @staticmethod
    def open_write_prompt(address):
        write_pop_up = Factory.I2cWritePopup()
        write_pop_up.address = address
        write_pop_up.open()

    @staticmethod
    def validate_input(text):
        valid = re.compile(r"^[a-fA-F0-9]{2}$")
        if not valid.match(text.replace("0x", "")):
            return False
        else:
            return True

    @staticmethod
    def validate_address(text):
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

    @staticmethod
    def open_lut_popup():
        lut_pop_up = LutPopup()
        lut_pop_up.open()

    @staticmethod
    def open_single_write():
        single_write_pop_up = Factory.I2cSingleWritePopup()
        single_write_pop_up.open()

    @staticmethod
    def open_single_read():
        single_read_pop_up = Factory.I2cSingleReadPopup()
        single_read_pop_up.open()

    def single_write(self, address, value):
        self.activate_osx()
        return_value = "Error occurred when writing"
        if self.i2c_device.configured is True:
            if self.validate_address(address):
                if value != '':
                    if self.validate_input(value):
                        try:
                            address = int(address, 16)
                            write_value = value

                            if write_value.replace("0x", '').__len__() == 1:
                                write_value = '0' + write_value.replace("0x", '')
                            if write_value.replace("0x", '').__len__() == 3:
                                write_value = '0' + write_value.replace("0x", '')

                            data = bytearray.fromhex(write_value.replace('0x', ''))
                            self.slave_device.write_to(address, data)

                            if int(hex(self.slave_device.read_from(address, 1)[0]), 16) == data[0]:
                                return_value = "0x" + write_value + " has been written to " + hex(address) + "\n" +\
                                       "Read value: " + hex(self.slave_device.read_from(address, 1)[0])
                            else:
                                return_value = "Error: " + "0x" + write_value + " could not be written to " +\
                                       hex(address) + "\n" + "Read value: " +\
                                       hex(self.slave_device.read_from(address, 1)[0])
                        except FtdiError:
                            usb_slave_error = Factory.ErrorPopup()
                            usb_slave_error.text = "Error: No usb device (it may have been disconnected)"
                            usb_slave_error.open()
                        except I2cNackError:
                            nack_error = Factory.ErrorPopup()
                            nack_error.text = "Error: Nack from Slave"
                            nack_error.open()
                        except I2cIOError:
                            pass
                        except I2cTimeoutError:
                            pass
                    else:
                        return_value = "Error: value must be a 2 digit hex value"
                else:
                    return_value = "Error: no value entered"
            else:
                return_value = "Error: address must be a 2->4 digit hex value"
        else:
            return_value = "Error: no slave device"
        self.i2c_device.terminate()
        return return_value

    def single_read(self, address):
        if self.validate_address(address):
            return self.get_dual_display_read(address)
        else:
            return "ERROR: address must be a 2->4 digit hex value"

    def write(self, address, value):
        self.activate_osx()
        if self.i2c_device.configured is True:
            if value != '':
                try:
                    temp_address = int(address, 16)
                    if self.validate_input(value):
                        if value.replace("0x", '').__len__() == 3:
                            value = '0' + value.replace("0x", '')
                        data = bytearray.fromhex(self.get_valid_value_form(value.replace('0x', '')))
                        self.slave_device.write_to(temp_address, data)  # write
                        self.show_details(address, self.read(address))  # read and refresh
                    else:
                        format_error = Factory.ErrorPopup()
                        format_error.text = "ERROR: invalid input (must be a 2 digit hex value)"
                        format_error.open()
                except FtdiError:
                    usb_slave_error = Factory.ErrorPopup()
                    usb_slave_error.text = "Error: No usb device (it may have been disconnected)"
                    usb_slave_error.open()
                except I2cNackError:
                    nack_error = Factory.ErrorPopup()
                    nack_error.text = "Error: Nack from Slave"
                    nack_error.open()
                except I2cIOError:
                    pass
                except I2cTimeoutError:
                    pass
        self.i2c_device.terminate()

    def read(self, address):
        self.activate_osx()
        if self.i2c_device.configured is True:
            try:
                address = int(address, 16)
                reg_data = hex(self.slave_device.read_from(address, 1)[0])  # read
                self.i2c_device.terminate()
                return reg_data
            except FtdiError:
                usb_slave_error = Factory.ErrorPopup()
                usb_slave_error.text = "Error: No usb device (it may have been disconnected)"
                usb_slave_error.open()
            except I2cNackError:
                nack_error = Factory.ErrorPopup()
                nack_error.text = "Error: Nack from Slave"
                nack_error.open()
            except I2cIOError:
                pass
            except I2cTimeoutError:
                pass
            self.i2c_device.terminate()
            return "Read_Fail"
        else:
            no_slave_error = Factory.ErrorPopup()
            no_slave_error.text = "Error: No Save Device"
            no_slave_error.open()
            self.i2c_device.terminate()
            return ''

    def get_dual_display_read(self, address):
        reg_data = self.read(address)
        if reg_data == '':
            return "Error: no slave device"
        if reg_data == 'Read_Fail':
            return "Error: slave error"
        return bin(int(reg_data, 16))[2:].zfill(8) + " (" + reg_data + ")"

    def configure_ftdi(self, port_address):
        self.port_address = port_address
        # try:
        #     i2c = I2cController()
        #     i2c.configure('ftdi://ftdi:232h/1')
        #     slave_device = i2c.get_port(int(port_address, 16))
        #     slave_device.configure_register(bigendian=True, width=2)
        #     self.slave_device = slave_device
        # except USBError:
        #     usb_error = Factory.ErrorPopup()
        #     usb_error.text = str(USBError)
        #     usb_error.open()
        # except UsbToolsError:
        #     usb_tool_error = Factory.ErrorPopup()
        #     usb_tool_error.text = str(UsbToolsError)
        #     usb_tool_error.open()
        # except I2cIOError:
        #     i2c_io_error = Factory.ErrorPopup()
        #     i2c_io_error.text = str(I2cIOError)
        #     i2c_io_error.open()

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
        read_lane_popup = Factory.ReadLanePopup()
        read_lane_popup.lane_name = self.i2c_tabbed_panel.current_tab.text
        for string in self.read_all_in_lane():
            read_lane_popup.data += string + '\n'
        read_lane_popup.open()

    def read_all_in_lane(self):
        strings = list()
        current_tab = self.i2c_tabbed_panel.current_tab
        if isinstance(current_tab, TabbedPanelItem):
            for row in current_tab.i2c_recycle_View.data:
                reg_data = self.get_dual_display_read(row["address"])
                row["value"] = reg_data
                string = row["address"] + ": " + reg_data
                strings.append(string)
        return strings

    def open_write_all_popup(self):
        write_all_confirm = Factory.ConfirmtaionWritePopup()
        write_all_confirm.lane = self.i2c_tabbed_panel.current_tab.text
        write_all_confirm.open()

    def open_write_lane(self):
        write_all_popup = Factory.WriteAllPopup()
        if self.write_all_in_lane() is True:
            write_all_popup.text = "All addresses have successfully been written to default values"
        else:
            write_all_popup.text = "Error occured while writing"
        write_all_popup.open()

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

    def export_lut_csv(self, commands):
        csv.register_dialect('myDialect',
                             delimiter=';',
                             quoting=csv.QUOTE_NONE,
                             skipinitialspace=True)

        if not os.path.exists(str(Path.home()) + '/Desktop/out'):
            os.mkdir(str(Path.home()) + '/Desktop/out')

        with open(str(Path.home()) + '/Desktop/out/LUT_Script_' + str(self.lut_script_index) + '.csv', 'w') as f:
            writer = csv.writer(f, dialect='myDialect')
            for row in commands:
                writer.writerow(row)

        self.lut_script_index += 1
        f.close()

    def create_load_lut_script(self, start_address, values, export_csv_checkbox):
        if len(values) != 0:
            if self.validate_address(start_address):
                if 'LUT_Script' in self.script_list:
                    self.script_list.remove('LUT_Script')

                commands = list()
                address = start_address

                for i in range(len(values)):
                    address = int(address, 16)
                    address = "{0:#0{1}x}".format(address, 6)
                    command_sequence = ['write', address, '[7:0]', values[i]]
                    commands.append(command_sequence)
                    address = int(address, 16) + 1
                    address = "{0:#0{1}x}".format(address, 6)

                self.script_list.append(I2cScript('LUT_Script', commands))
                if export_csv_checkbox.active:
                    self.export_lut_csv(commands)

                lut_script_notice = Factory.NoticePopup()
                lut_script_notice.text = "LUT Script has been Added"
                lut_script_notice.open()
            else:
                blank_adddr_error = Factory.ErrorPopup()
                blank_adddr_error.text = "Error: no address added or invalid address"
                blank_adddr_error.open()
        else:
            no_lut_error = Factory.ErrorPopup()
            no_lut_error.text = "Error: LUT not calculated"
            no_lut_error.open()

    def load_script(self, file_path):
        if file_path.__contains__(".csv"):
            if path_leaf(file_path) in self.script_list:
                self.script_list.remove(path_leaf(file_path))
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
        for script in self.script_list:
            if script.script_name == self.script_pop_up_reference.currently_selected_script:
                self.activate_osx()
                if self.i2c_device.configured is True:
                    script.execute(self.slave_device, self.script_pop_up_reference.script_log_label,
                                   self.script_pop_up_reference.script_progress_bar,
                                   self.script_pop_up_reference.script_preview_text_input,
                                   self.i2c_device)

    @staticmethod
    def open_load_script():
        Factory.I2cLoadScriptPopup().open()

    def open_run_script(self):
        self.script_pop_up_reference = Factory.I2cRunScriptPopup()
        self.script_pop_up_reference.scripts_recycle_view.data = [{'script_name': script.script_name,
                                                                   'script_preview': script.get_preview()}
                                                                  for script in self.script_list]
        self.script_pop_up_reference.open()
