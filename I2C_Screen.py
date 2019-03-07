from kivy.uix.screenmanager import Screen
from kivy.factory import Factory


class I2CScreen(Screen):

    def initialize_data(self):
        address_list = self.manager.get_screen("menu_screen").address_list
        chip_pin_list = self.manager.get_screen("menu_screen").chip_pin_list

    @staticmethod
    def write():
        Factory.I2cWritePopup().open()

    def show_details(self):
        # self.address_details_rst.text = address_list.bits_string + '\n' + chip_pin_list.breakdown
        pass

    @staticmethod
    def open_load_script():
        Factory.I2cLoadScriptPopup().open()

    @staticmethod
    def open_run_script():
        Factory.I2cRunScriptPopup().open()
        pass

