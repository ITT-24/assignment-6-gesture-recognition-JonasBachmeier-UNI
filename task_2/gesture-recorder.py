import pyglet
from pyglet.window import mouse
import xml.etree.ElementTree as ET
import time
import os

filename = input("Enter filename: ")


def save_gesture(points):
    # get number of files with same gesture name

    num = 0
    for root, subdirs, files in os.walk('../dataset'):
        for f in files:
            if filename in f:
                num += 1
    root = ET.Element("Gesture")
    root.set("Name", filename)
    root.set("NumPts", str(len(points)))
    root.set("Date", time.strftime("%A, %B %d, %Y"))
    root.set("TimeOfDay", time.strftime("%I:%M:%S %p"))

    for x, y, t in points:
        point = ET.SubElement(root, "Point")
        point.set("X", str(x))
        point.set("Y", str(y))
        point.set("T", str(t))
    
    tree = ET.ElementTree(root)
    tree.write(f"../dataset/{filename}{num}.xml")

window = pyglet.window.Window(500, 500)
drawing = False
points = []
label = pyglet.text.Label(x=10, y=10)


@window.event
def on_draw():
    window.clear()
    label.text = str(len(points))
    label.draw()
    if drawing:
        for x, y, t in points:
            pyglet.shapes.Circle(x, y, 5, color=(255, 255, 255)).draw()

@window.event
def on_mouse_press(x, y, button, modifiers):
    global drawing
    if button == mouse.LEFT:
        drawing = True
        points.append((x, y, time.time()))

@window.event
def on_mouse_release(x, y, button, modifiers):
    global drawing
    if button == mouse.LEFT:
        drawing = False
        save_gesture(points)
        points.clear()

@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    if drawing:
        points.append((x, y, time.time()))



pyglet.app.run()