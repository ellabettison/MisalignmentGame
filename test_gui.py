from dearpygui.dearpygui import *

# Simple DearPyGui window
set_viewport_width(900)
set_viewport_height(720)
set_viewport_title("Alignment Inspector")

with window("Test Window", width=900, height=720):
    add_text("Hello, DearPyGui!")

start_dearpygui()
