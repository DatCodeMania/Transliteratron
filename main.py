import json
import time
from threading import Thread

import gi
import requests
import yaml

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)


class TransliterationApp(Gtk.Window):
    def __init__(self):
        # Initialization of window.
        Gtk.Window.__init__(self, title="Transliteratron")

        self.set_border_width(10)
        self.set_default_size(400, 300)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.input_label = Gtk.Label(label="Input:")
        vbox.pack_start(self.input_label, True, True, 0)

        self.input_box = Gtk.TextView()
        vbox.pack_start(self.input_box, True, True, 0)

        self.transliterate_button = Gtk.Button(label="Transliterate")
        self.transliterate_button.connect("clicked", self.on_transliterate_clicked)
        vbox.pack_start(self.transliterate_button, True, True, 0)

        self.spinner = Gtk.Spinner()
        vbox.pack_start(self.spinner, True, True, 0)

        self.output_label = Gtk.Label(label="Output:")
        vbox.pack_start(self.output_label, True, True, 0)

        self.output_box = Gtk.TextView()
        vbox.pack_start(self.output_box, True, True, 0)

        self.time_label = Gtk.Label(label="Processing Time: N/A")
        vbox.pack_start(self.time_label, True, True, 0)

        self.connect("key-press-event", self.on_key_press_event)

    # Checking for enter key to allow for transliteration mouse-less.
    def on_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Return:
            self.on_transliterate_clicked(widget)

    # Sends data off to the request helper function and measures time.
    def on_transliterate_clicked(self, widget):
        input_buffer = self.input_box.get_buffer()
        start_iter, end_iter = input_buffer.get_bounds()
        input_text = input_buffer.get_text(start_iter, end_iter, True)

        self.spinner.start()

        start_time = time.time()

        thread = Thread(target=self.make_request, args=(input_text, start_time))
        thread.start()

    # Removes status spinner and shows processing time when transliteration is complete.
    def update_ui(self, output_text, processing_time):
        self.spinner.stop()

        output_buffer = self.output_box.get_buffer()
        output_buffer.set_text(output_text)

        self.time_label.set_text(f"Processing Time: {processing_time:.2f} seconds")

    # Makes a request to the API defined in the config file, then changes UI
    # using helper function.
    def make_request(self, text, start_time):
        url = config["api_url"]
        instruction = config["instruction"]
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {config["api_token"]}'
        }
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {
                    'role': 'user',
                    'content': f"{instruction} {text}"
                }
            ]
        }

        print(json.dumps(data, indent=2))
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_data = response.json()

        output_text = response_data['choices'][0]['message']['content'].strip()

        end_time = time.time()
        processing_time = end_time - start_time

        # Calls back to the original thread to update the UI to show
        # processing time and hide the spinner.
        GLib.idle_add(self.update_ui, output_text, processing_time)


if config["api_url"] == "YOUR_API_URL" or config["api_token"] == "YOUR_API_TOKEN":
    print("Please enter your API data in config.yaml")
else:
    win = TransliterationApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
