from kivy.uix.screenmanager import Screen
from kivy.factory import Factory


class I2CScreen(Screen):

    @staticmethod
    def write():
        Factory.I2cWritePopup().open()

    @staticmethod
    def open_load_script():
        Factory.I2cLoadScriptPopup().open()

    @staticmethod
    def open_run_script():
        Factory.I2cRunScriptPopup().open()
        pass

