from kivy.uix.screenmanager import Screen
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.factory import Factory


class I2cTabbedPanelItem(TabbedPanelItem):
    pass


class I2CScreen(Screen):

    lane_list = list()

    @staticmethod
    def write():
        Factory.I2cWritePopup().open()

    def read(self):
        pass

    def configure_ftdi(self):
        pass

    def configure_lane_tabs(self):
        self.i2c_tabbed_panel.clear_widgets()
        self.i2c_tabbed_panel.clear_tabs()

        for lane in self.lane_list:
            new_tab = I2cTabbedPanelItem(text=lane.name)
            new_tab.i2c_recycle_View.data = [{'address': address.i2c_address, 'chip_pin': address.chip_pin_name,
                                              'value': address.value} for address in lane.i2c_address_list]
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

