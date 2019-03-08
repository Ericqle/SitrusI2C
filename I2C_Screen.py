from kivy.uix.screenmanager import Screen
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.factory import Factory
from pyftdi.i2c import I2cController, I2cNackError, I2cIOError, I2cTimeoutError
from pyftdi.usbtools import UsbToolsError
from usb.core import USBError


class I2cTabbedPanelItem(TabbedPanelItem):
    pass


class I2CScreen(Screen):

    lane_list = list()
    slave_device = None

    @staticmethod
    def write():
        Factory.I2cWritePopup().open()

    def read(self, address):
        if self.slave_device is not None:
            try:
                address = int(address, 16)
                reg_data = hex(self.slave_device.read_from(address, 1)[0])  # read
                return reg_data
            except I2cNackError:
                print(I2cNackError)
            except I2cIOError:
                print(I2cIOError)
            except I2cTimeoutError:
                print(I2cTimeoutError)
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
            print(USBError)
        except UsbToolsError:
            print(UsbToolsError)

    def configure_lane_tabs(self):
        self.i2c_tabbed_panel.clear_widgets()
        self.i2c_tabbed_panel.clear_tabs()

        for lane in self.lane_list:
            new_tab = I2cTabbedPanelItem(text=lane.name)
            new_tab.i2c_recycle_View.data = [{'address': address.i2c_address, 'chip_pin': address.chip_pin_name,
                                              'value': self.read(address.i2c_address)} for address in lane.i2c_address_list]
            self.i2c_tabbed_panel.add_widget(new_tab)
        pass

    def show_details(self, address):
        current_lane_name = self.i2c_tabbed_panel.get_current_tab().text

        for lane in self.lane_list:
            if current_lane_name == lane.name:

                for i2c_address in lane.i2c_address_list:
                    if address == i2c_address.i2c_address:
                        self.bit_recycle_view.data = ({'text': bit} for bit in i2c_address.bits)

    @staticmethod
    def open_load_script():
        Factory.I2cLoadScriptPopup().open()

    @staticmethod
    def open_run_script():
        Factory.I2cRunScriptPopup().open()
        pass

