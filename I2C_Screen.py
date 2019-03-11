from kivy.uix.screenmanager import Screen
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.factory import Factory
from pyftdi.i2c import I2cController, I2cNackError, I2cIOError, I2cTimeoutError
from pyftdi.usbtools import UsbToolsError
from usb.core import USBError
import re


class I2cTabbedPanelItem(TabbedPanelItem):
    pass


class I2CScreen(Screen):

    lane_list = list()
    slave_device = None

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

    def write(self, address, value):
        if self.slave_device is not None:
            if value != '':
                try:
                    temp_address = int(address, 16)
                    if self.validate_input(value):
                        data = bytearray.fromhex(value.strip('0'))
                        self.slave_device.write_to(temp_address, data)  # write
                        self.show_details(address)  # read and refresh
                    else:
                        print("ERROR: invalid input (must be a 2->4 digit hex value)" + "\n")
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
            except I2cNackError:
                pass
            except I2cIOError:
                pass
            except I2cTimeoutError:
                pass
            return "Read_Fail"
        else:
            return 'Error'

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

    def configure_lane_tabs(self):
        self.i2c_tabbed_panel.clear_widgets()
        self.i2c_tabbed_panel.clear_tabs()

        for lane in self.lane_list:
            new_tab = I2cTabbedPanelItem(text=lane.name)
            new_tab.i2c_recycle_View.data = [{'address': address.i2c_address, 'chip_pin': address.chip_pin_name,
                                              'value': address.value, 'default': address.default}
                                             for address in lane.i2c_address_list]
            self.i2c_tabbed_panel.add_widget(new_tab)
        pass

    def show_details(self, address):
        current_lane_name = self.i2c_tabbed_panel.get_current_tab().text

        for lane in self.lane_list:
            if current_lane_name == lane.name:

                for i2c_address in lane.i2c_address_list:
                    if address == i2c_address.i2c_address:
                        i2c_address.value = self.read(i2c_address.i2c_address)  # read
                        self.bit_recycle_view.data = ({'text': bit} for bit in i2c_address.bits)
                        self.refresh_lane()

    def refresh_lane(self):
        current_tab = self.i2c_tabbed_panel.get_current_tab()

        for lane in self.lane_list:
            if current_tab.text == lane.name:
                current_tab.i2c_recycle_View.data = [{'address': address.i2c_address, 'chip_pin': address.chip_pin_name,
                                                      'value': address.value, 'default': address.default}
                                                     for address in lane.i2c_address_list]


    @staticmethod
    def open_load_script():
        Factory.I2cLoadScriptPopup().open()

    @staticmethod
    def open_run_script():
        Factory.I2cRunScriptPopup().open()
        pass

