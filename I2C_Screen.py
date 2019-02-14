from kivy.uix.screenmanager import Screen
from kivy.factory import Factory


class I2CScreen(Screen):

    def write(self):
        Factory.I2cWritePopup().open()

