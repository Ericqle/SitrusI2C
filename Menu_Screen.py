from kivy.uix.screenmanager import Screen
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.lang import Builder

Builder.load_string('''
<I2cRecycleViewRow@BoxLayout>:
    orientation: 'horizontal'
    text : ''
    Button:
        text: 'Address'
    Label:
        text: 'Name'
    Button:
        text: 'Data'
        on_press: app.root.get_screen("i2c_screen").write()

<I2cRecycleView@RecycleView>:
    viewclass: 'I2cRecycleViewRow'
    RecycleBoxLayout:
        default_size: None, dp(56)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'        

<I2cTabbedPanelItem>:
    i2c_recycle_View: i2c_recycle_View
    I2cRecycleView:
        id: i2c_recycle_View
                    ''')


class I2cTabbedPanelItem(TabbedPanelItem):
    pass


class MenuScreen(Screen):
    tabs = 4

    def swap_to_i2c_screen(self):
        i2c_screen = self.manager.get_screen("i2c_screen")

        i2c_screen.i2c_tabbed_panel.clear_widgets()
        i2c_screen.i2c_tabbed_panel.clear_tabs()

        for i in range(0, self.tabs):
            new_tab = I2cTabbedPanelItem(text="Tab: " + str(i))
            new_tab.i2c_recycle_View.data = [{'text': "Button " + str(x), 'id': str(x)} for x in range(30)]
            i2c_screen.i2c_tabbed_panel.add_widget(new_tab)

        self.manager.current = "i2c_screen"
