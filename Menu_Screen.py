from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
import re
import csv
from pathlib import Path
import ntpath
ntpath.basename("a/b/c")


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


Builder.load_string('''
<I2cRecycleViewRow@BoxLayout>:
    canvas.before:
        Color:
            rgb: 185/255, 185/255, 185/255
        Rectangle:
            pos: self.pos
            size: self.size
    orientation: 'horizontal'
    address: ''
    chip_pin: ''
    value: ''
    default: ''
    Button:
        text: root.address
        on_press: 
            root.value = app.root.get_screen("i2c_screen").read(root.address)
            app.root.get_screen("i2c_screen").show_details(root.address, root.value)
    Label:
        text: root.chip_pin
    Label: 
        canvas.before:
            Color:
                rgb: 150/255, 150/255, 150/255
            Rectangle:
                pos: self.pos
                size: self.size
        text: root.default
    Button:
        text: root.value
        on_press: app.root.get_screen("i2c_screen").open_write_prompt(root.address)

<I2cRecycleView@RecycleView>:
    viewclass: 'I2cRecycleViewRow'
    bar_width: 20
    bar_length: 50
    bar_color: 1, 1, 1, 1
    bar_inactive_color: 160/255, 160/255, 160/255, 1
    effect_cls: "ScrollEffect"
    scroll_type: ['bars']

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


class I2cLane:

    def __init__(self, file):
        self.name = path_leaf(file).strip('.csv')
        self.i2c_address_list = list()
        self.chip_pin_list = list()
        with open(file) as csv_file:
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
                        self.i2c_address_list.append(temp_address)
                        temp_address = I2cAddress(row)

            temp_chip_pin = None
            for address in self.i2c_address_list:
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

    def __eq__(self, name):
        return self.name == name

    def get_i2c_address(self, address):
        for i2c_address in self.i2c_address_list:
            if i2c_address.i2c_address == address:
                return i2c_address
        return None


class MenuScreen(Screen):
    lane_list = list()

    @staticmethod
    def get_default_path():
        return str(Path.home())

    def load_lane(self):
        path = Path(self.config_file_text_input.text)
        if path_leaf(self.config_file_text_input.text).strip('.csv') in self.lane_list:
            pass
        elif path.is_file() and self.config_file_text_input.text.endswith('.csv'):
            temp_lane = I2cLane(self.config_file_text_input.text)
            self.lane_list.append(temp_lane)
            self.loaded_lanes_recycle_view.data = ({'text': lane.name} for lane in self.lane_list)

    def swap_to_i2c_screen(self):
        i2c_screen = self.manager.get_screen("i2c_screen")
        i2c_screen.lane_list = self.lane_list
        i2c_screen.configure_ftdi(port_address=self.port_address_text_input.text)
        i2c_screen.configure_lane_tabs()
        self.manager.current = "i2c_screen"
