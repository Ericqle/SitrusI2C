from kivy.uix.screenmanager import Screen
from kivy.factory import Factory


class I2CScreen(Screen):

    @staticmethod
    def write():
        Factory.I2cWritePopup().open()

    def show_details(self, address):
        current_lane_name = self.i2c_tabbed_panel.get_current_tab().text
        lane_list = self.manager.get_screen("menu_screen").lane_list

        for lane in lane_list:
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

