import neovim
import docopt

import os
import sys
import os_code
import time
import threading
from trollius import py33_exceptions

class V:
    def __init__(self, args):
        self.args = args

        if args["-d"]:
            nvim_launcher_thread = threading.Thread(target=self.__call_nvim__) #Launch nvim in new thread so that V doesn't hang
            nvim_launcher_thread.start()
            time.sleep(1)
            socket = os_code.get_socket_path(args)

            try:
                self.nvim_instance = neovim.attach("socket", path=socket)
            except py33_exceptions.FileNotFoundError:
                sys.stderr.write("Couldn't connect to nvim. Did you export your NVIM_LIST_ADDRESS?\n\n")
                sys.exit()

        else:
            args = os_code.get_embedded_nvim_args(args)
            try:
                self.nvim_instance = neovim.attach("child", argv=args)
            except py33_exceptions.FileNotFoundError:
                sys.stderr.write("Couldn't find the neovim executable! Is nvim in your $PATH?\n\n")
                sys.exit()

        if self.args["--safe"]:
            self.nvim_instance.command("source nvim/safe_mode.vim")

        self.active_reg = "a"
        self.pending_number = ""
        self.pending_command = ""
        self.loop_symbol = ""
        self.loop_num = ""
        self.recorded_text = ""
        self.recording = False
        self.keys_sent = []

    def __call_nvim__(self):
        socket = os_code.get_socket_path(self.args)

        arg = os_code.get_external_nvim_command(self.args)
        os.system(arg)

    def key_stroke(self, key):
        self.nvim_instance.feedkeys(key)

    def set_register(self, register, value):
        command = ":let @{}='{}'".format(register, value)
        try:
            self.nvim_instance.command(command)
            return True
        except:
            return False

    def get_mode(self):
        return self.nvim_instance.eval("mode(1)")

    def get_literal(self, key):
        if key in literals:
            return literals[key]
        if ord(key) > 127:
            return "<M-{}>".format(chr(ord(key) - 128))
        return key

    def get_register(self, register):
        command = "@{}".format(register)
        return self.nvim_instance.eval(command)

    def get_text(self):
        for line in self.nvim_instance.buffers:
            yield line

    def close(self):
        if not self.args["-d"]:
            self.nvim_instance.quit()

    def clean_up(self):
        if self.get_mode() == "i":
            self.key_stroke(chr(27))

        if self.recording:
            self.key_stroke(self.loop_symbol)
