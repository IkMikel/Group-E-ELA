import tkinter as tk
from time import strftime

# Create the main window
root = tk.Tk()
root.title("Python Clock")

# Configure label to show time
def time():
    string = strftime('%H:%M:%S %p')  # Format: Hours:Minutes:Seconds AM/PM
    label.config(text=string)
    label.after(1000, time)  # Update every second

label = tk.Label(root, font=('Arial', 80), background='blue', foreground='red')
label.pack(anchor='center')

time()  # Start the clock
root.mainloop()

