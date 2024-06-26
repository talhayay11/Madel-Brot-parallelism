import numpy as np
from concurrent.futures import ProcessPoolExecutor
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time
import os

def mandelbrot(c, max_iter):
    z = complex(0, 0)
    n = 0
    while abs(z) <= 2 and n < max_iter:
        z = z * z + c
        n += 1
    return n

def compute_mandelbrot_region(args):
    region_name, xmin, xmax, ymin, ymax, width, height, max_iter = args
    x = np.linspace(xmin, xmax, width)
    y = np.linspace(ymin, ymax, height)
    C = np.array(np.meshgrid(x, y)).T.reshape(-1, 2)
    C = C[:, 0] + 1j * C[:, 1]

    start_time = time.time()
    count = np.array([mandelbrot(c, max_iter) for c in C])
    elapsed_time = time.time() - start_time
    #print(f"Process ID: {os.getpid()} Region: {region_name}, Computation time: {elapsed_time:.2f} seconds")
    
    return count.reshape((height, width))

class ZoomableMandelbrot:
    def __init__(self, ax, max_iter, regions=1, width=800, height=800):
        self.ax = ax
        self.max_iter = max_iter
        self.width = width
        self.height = height
        self.regions = regions
        self.press = None
        self.xmin, self.xmax = -2.0, 2.0
        self.ymin, self.ymax = -2.0, 2.0

        self.cid_press = ax.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = ax.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = ax.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

        self.rect = patches.Rectangle((0,0), 0, 0, fill=False, edgecolor='white', linewidth=1.5)
        self.ax.add_patch(self.rect)
        self.plot_mandelbrot()

    def on_press(self, event):
        if event.inaxes != self.ax:
            return
        self.press = event.xdata, event.ydata
        self.rect.set_width(0)
        self.rect.set_height(0)
        self.rect.set_xy((event.xdata, event.ydata))

    def on_motion(self, event):
        if self.press is None or event.inaxes != self.ax:
            return
        xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress
        self.rect.set_width(dx)
        self.rect.set_height(dy)
        self.ax.figure.canvas.draw_idle()

    def on_release(self, event):
        if self.press is None or event.inaxes != self.ax:
            return
        xpress, ypress = self.press
        xrelease, yrelease = event.xdata, event.ydata
        self.press = None

        # Calculate new region boundaries
        xmin = min(xpress, xrelease)
        xmax = max(xpress, xrelease)
        ymin = min(ypress, yrelease)
        ymax = max(ypress, yrelease)

        # Update the region without changing the axes limits
        self.plot_mandelbrot(xmin, xmax, ymin, ymax)

    def plot_mandelbrot(self, xmin=None, xmax=None, ymin=None, ymax=None):
        for processesNumber in [1,2,3,4,5,6,7,8,9,10,11,12]:
            if xmin is None:
                xmin, xmax = self.xmin, self.xmax
            if ymin is None:
                ymin, ymax = self.ymin, self.ymax
            #max_workers = min(os.cpu_count(), 40)  # Adjust the upper limit as needed
            
            # Dynamically increase the number of workers until the system limit is reached
            #for workers in range(max_workers, 0, -1):
            #    if self.regions ** 2 % workers == 0:
            #        max_workers = workers
            #        break

            

            print(f"Number of regions: {self.regions}")

            # Calculate width and height of each region
            region_width = self.width // self.regions
            region_height = self.height // self.regions

            # Adjust the region boundaries to ensure integer number of pixels per region
            x_step = (xmax - xmin) / self.width
            y_step = (ymax - ymin) / self.height
            x_steps = np.linspace(xmin, xmax, self.regions + 1)
            y_steps = np.linspace(ymin, ymax, self.regions + 1)

            regions = []
            for i in range(self.regions):
                for j in range(self.regions):
                    x_min = x_steps[i]
                    x_max = x_steps[i + 1]
                    y_min = y_steps[j]
                    y_max = y_steps[j + 1]
                    regions.append((f"Region-{i}-{j}", x_min, x_max, y_min, y_max, region_width, region_height, self.max_iter))

            start_time = time.time()
            with ProcessPoolExecutor(processesNumber) as executor:
                results = list(executor.map(compute_mandelbrot_region, regions))

            final_result = np.zeros((self.height, self.width))
            for j in range(self.regions):
                for i in range(self.regions):
                    idx = j * self.regions + i
                    result = results[idx]
                    final_result[j * region_height:(j + 1) * region_height, i * region_width:(i + 1) * region_width] = result

            elapsed_time = time.time() - start_time
            print(f"Max Workers: {processesNumber} Total computation time: {elapsed_time:.2f} seconds")

            start_time_sequential = time.time()
            final_result_sequential = compute_mandelbrot_region(("Sequential", self.xmin, self.xmax, self.ymin, self.ymax, self.width, self.height, self.max_iter))
            elapsed_time_sequential = time.time() - start_time_sequential

            # Compute the speedup
            speedup = elapsed_time_sequential / elapsed_time

            # Compute the efficiency
            efficiency = speedup / processesNumber

            print(f"Speedup: {speedup:.2f}")
            print(f"Efficiency: {efficiency:.2f}")

            self.ax.clear()
            self.ax.imshow(final_result.T, extent=[self.xmin, self.xmax, self.ymin, self.ymax], origin='lower', cmap='hot')
            self.ax.figure.canvas.draw_idle()

# Usage of the class remains similar    
if __name__ == '__main__':
    fig, ax = plt.subplots(figsize=(10, 10))
    mandelbrot_display = ZoomableMandelbrot(ax, max_iter=300, regions=20)
    plt.show()