from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.config import Config
from Menu_Screen import MenuScreen
from I2C_Screen import I2CScreen


class SitrusI2cApp(App):
    from kivy.lang import Builder
    Builder.load_file('Popups.kv')
    Builder.load_file('MenuScreen.kv')
    Builder.load_file('I2CScreen.kv')

    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(MenuScreen(name='menu_screen'))
        screen_manager.add_widget(I2CScreen(name='i2c_screen'))
        return screen_manager


if __name__ == '__main__':
    Window.size = (850, 500)
    Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
    SitrusI2cApp().run()
