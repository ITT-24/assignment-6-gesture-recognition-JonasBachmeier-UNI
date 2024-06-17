from matplotlib import pyplot as plt
import numpy as np
import os
import math
import tkinter as tk


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


# nice progress bar for loading data
from tqdm.notebook import tqdm

# resample signal to n samples
from scipy.signal import resample

# XML parser
import xml.etree.ElementTree as ET

# encoding and normalizing data
from sklearn.preprocessing import StandardScaler

NUM_POINTS = 50

def get_gesture_data():
    data = []
    counter = 0
    for root, subdirs, files in os.walk('../../lstm_demo/xml_logs/s01'):
        if 'ipynb_checkpoint' in root:
            continue

        if len(files) > 0:
            if 'medium' in root:
                for f in tqdm(files):
                    if '01.xml' in f:
                        counter = counter + 1
                        fname = f.split('.')[0]
                        label = fname[:-2]
                        xml_root = ET.parse(f'{root}/{f}').getroot()
                        points = []
                        for element in xml_root.findall('Point'):
                            x = element.get('X')
                            y = element.get('Y')
                            points.append([x, y])
                            
                        points = np.array(points, dtype=float)
                        
                        scaler = StandardScaler()
                        points = scaler.fit_transform(points)
                        
                        resampled = resample(points, NUM_POINTS)
                        
                        data.append((label, resampled))
    return data
    
def preprocess_data(points):
    points = np.array(points, dtype=float)
                        
    scaler = StandardScaler()
    points = scaler.fit_transform(points)
    resampled = resample(points, NUM_POINTS)
    rotated_points = rotate_data(resampled)
    return rotated_points

# Rotates the data by first finding the centroid of the data and then rotating the data so that the first point is on the same y-level as the centroid
def rotate_data(points):
    rotated_data = []
    angle = np.arctan2(-points[0][1], -points[0][0])
    rotation_matrix = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    rotated_points = np.dot(points, rotation_matrix)
    rotated_data.append(rotated_points)
    return rotated_data

def compare_to_templates(data, templates):
    best_match = None
    prev_mean_dist = math.inf
    for label, template in templates:
        distances = []
        for i in range(len(data)):
            distance_x =template[i][0] - data[i][0]
            distance_y = template[i][1] - data[i][1]
            distance = np.sqrt(distance_x**2 + distance_y**2)
            distances.append(distance)
        mean_distance = np.mean(distances)
        print(f'Mean distance for {label}: {mean_distance}')
        if mean_distance < prev_mean_dist:
            prev_mean_dist = mean_distance
            best_match = label

    return best_match

def main():
    templates = []
    gesture_data = get_gesture_data()
    for label, points in gesture_data:
        rotated_data = rotate_data(points)
        templates.append([label,rotated_data])        

    root = tk.Tk()
    canvas = tk.Canvas(root, width=500, height=500)
    canvas.pack()

    drawing = False
    points = []

    def start_draw(event):
        nonlocal drawing, points
        drawing = True
        points.append([event.x, event.y])

    def stop_draw(event):
        nonlocal drawing, points
        drawing = False
        # clear the canvas
        canvas.delete("all")
        preprocess_points = preprocess_data(points)
        best_match = compare_to_templates(preprocess_points, templates)
        print(best_match)
        print(f'Best match for {label}')
        points = []

    def draw(event):
        if drawing:
            points.append([event.x, event.y])
            canvas.create_oval(event.x - 1, event.y - 1, event.x + 1, event.y + 1, fill="black")

    canvas.bind("<Button-1>", start_draw)  # Mouse down event
    canvas.bind("<ButtonRelease-1>", stop_draw)  # Mouse up event
    canvas.bind("<B1-Motion>", draw)  # Mouse move event with left button down

    root.mainloop()

main()