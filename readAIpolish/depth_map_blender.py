import bpy
import numpy as np
from PIL import Image

img_path = r"C:\path\to\your\image.png"  # Change to your image file
depth_scale = 1.0  # Adjust for exaggeration

# Load image and convert to grayscale
img = Image.open(img_path).convert('L')
arr = np.array(img) / 255.0  # Normalize to [0,1]

size_y, size_x = arr.shape
bpy.ops.mesh.primitive_grid_add(x_subdivisions=size_x, y_subdivisions=size_y, size=2)
obj = bpy.context.active_object

mesh = obj.data
for i, v in enumerate(mesh.vertices):
    x = i % size_x
    y = i // size_x
    brightness = arr[y, x]
    v.co.z = brightness * depth_scale

# Add a camera
bpy.ops.object.camera_add(location=(0, -5, 2))