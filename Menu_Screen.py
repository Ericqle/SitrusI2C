from kivy.uix.screenmanager import Screen
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.lang import Builder
import re
import csv

Builder.load_string('''
<I2cRecycleViewRow@BoxLayout>:
    orientation: 'horizontal'
    address: ''
    chip_pin: ''
    value: ''
    Button:
        text: root.address
        on_press: app.root.get_screen("i2c_screen").show_details()
    Label:
        text: root.chip_pin
    Button:
        text: root.value
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


class I2cChipPin:

    def __init__(self, i2c_address):
        self.chip_pin_name = i2c_address.chip_pin_name
        self.i2c_addresses = list()
        self.msb = ''
        self.lsb = ''
        self.default = ''
        self.value = ''
        self.bits_string = ''
        self.breakdown = ''
        self.add_address(i2c_address)

    def add_address(self, i2c_address):
        self.i2c_addresses.append(i2c_address)
        self.msb = self.i2c_addresses[0]
        self.lsb = self.i2c_addresses[-1]
        self.default = ''
        self.bits_string = ''
        for i2c_address in self.i2c_addresses:
            self.default += i2c_address.default
            self.bits_string += i2c_address.bits_string
        self.breakdown = ("MSB: " + self.msb.i2c_address + " LSB: " + self.lsb.i2c_address + '\n' +
                          "Default: " + self.default + '\n' + self.bits_string)


class I2cAddress:

    def __init__(self, data):
        self.i2c_address = data[0]
        self.default = ''
        self.value = ''
        self. chip_pin_name = re.split('\[', data[3])[0]
        self.bits = list()
        self.bits_string = ''
        self.add_bit(data)

    def add_bit(self, data):
        bit = data[1] + ' ' + data[3] + ' ' + data[4] + ' ' + data[5] + ' ' + data[6]
        self.bits.append(bit)
        self.bits_string += bit + '\n'
        self.default += data[2]


class I2cTabbedPanelItem(TabbedPanelItem):
    pass


class MenuScreen(Screen):
    address_list = list()
    chip_pin_list = list()

    def load_addresses(self):
        with open('/Users/eric/Downloads/Athena A0 Test/Host_RX_01.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            temp_address = None
            for row in csv_reader:
                if len(row) == 7:
                    if temp_address is None:
                        temp_address = I2cAddress(row)
                        continue
                    if row[0] == temp_address.i2c_address:
                        temp_address.add_bit(row)
                    else:
                        self.address_list.append(temp_address)
                        temp_address = I2cAddress(row)

            temp_chip_pin = None
            for address in self.address_list:
                if temp_chip_pin is None:
                    temp_chip_pin = I2cChipPin(address)
                    temp_chip_pin.add_address(address)
                    continue
                if address.chip_pin_name == temp_chip_pin.chip_pin_name:
                    temp_chip_pin.add_address(address)
                else:
                    self.chip_pin_list.append(temp_chip_pin)
                    temp_chip_pin = I2cChipPin(address)
                    temp_chip_pin.add_address(address)

    def swap_to_i2c_screen(self):
        self.load_addresses()
        i2c_screen = self.manager.get_screen("i2c_screen")

        i2c_screen.i2c_tabbed_panel.clear_widgets()
        i2c_screen.i2c_tabbed_panel.clear_tabs()

        new_tab = I2cTabbedPanelItem(text="Test")
        new_tab.i2c_recycle_View.data = [{'address': address.i2c_address, 'chip_pin': address.chip_pin_name,
                                          'value': address.value} for address in self.address_list]
        i2c_screen.i2c_tabbed_panel.add_widget(new_tab)

        self.manager.current = "i2c_screen"
