from kivy.uix.screenmanager import Screen
from kivy.uix.tabbedpanel import TabbedPanelItem


class MenuScreen(Screen):

    tabs = 4

    def swap_to_i2c_screen(self):
        i2c_screen = self.manager.get_screen("i2c_screen")

        i2c_screen.i2c_tabbed_panel.clear_widgets()
        i2c_screen.i2c_tabbed_panel.clear_tabs()

        for i in range(0, self.tabs):
            new_tab = TabbedPanelItem(text="Tab: " + str(i))
            i2c_screen.i2c_tabbed_panel.add_widget(new_tab)

        self.manager.current = "i2c_screen"

    pass
