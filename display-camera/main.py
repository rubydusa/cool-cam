import cv2
from tkinter import *
from PIL import Image, ImageTk

# Initialize the camera capture
cap = cv2.VideoCapture(5)

def close_window(event):
    root.destroy()

# Function to get the current frame from the camera
def get_frame():
    ret, frame = cap.read()
    if not ret:
        return None
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame

# Function to update the displayed frame
def update_frame():
    frame = get_frame()
    if frame is not None:
        frame_image = ImageTk.PhotoImage(image=Image.fromarray(frame))
        label.config(image=frame_image)
        label.image = frame_image
    root.after(10, update_frame)

# Create a Tkinter window
root = Tk()
root.title("Camera Feed")
root.attributes('-fullscreen', True)
root.config(cursor='none')
# Bind the 'Control+C' key to the close_window function
root.bind('<Control-c>', close_window)

# Create a label in the window to hold the frames
label = Label(root, bg='black')
label.pack(fill=BOTH, expand=YES)

# Start the update process
update_frame()

# Run the application
root.mainloop()

# Release the camera when the application closes
cap.release()
