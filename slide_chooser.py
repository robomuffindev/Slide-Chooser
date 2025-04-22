# slide_chooser.py
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import shutil
import zipfile
from PIL import Image, ImageTk
import threading
import queue
import logging
from collections import defaultdict

# Set up logging
logging.basicConfig(filename='slide_chooser.log', level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SlideChooser(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Slide Chooser")
        self.geometry("1200x800")
        self.minsize(800, 600)

        # Application state
        self.master_folder = None
        self.image_catalog = {}  # Structure: {image_name: {folder_path: full_image_path}}
        self.current_sequence_index = 0
        self.slides_per_view = tk.IntVar(value=3)
        self.selected_images = {}  # Structure: {image_name: selected_folder_path}
        self.folders = []
        self.image_names = []
        self.load_queue = queue.Queue()
        self.image_cache = {}
        
        # Window resize tracking
        self.last_width = self.winfo_width()
        self.last_height = self.winfo_height()
        self.size_threshold = 50  # Minimum pixel change to trigger resize
        self.resize_timer = None  # Timer for resize events
        self._resize_bound = False

        # Create UI
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        
        # Bind keyboard shortcuts
        self.bind("<Left>", lambda e: self.navigate_sequence(-1))
        self.bind("<Right>", lambda e: self.navigate_sequence(1))
        
        # Wait for window to be fully drawn before getting initial dimensions
        self.after(100, self.initialize_dimensions)

    def initialize_dimensions(self):
        """Get initial window dimensions after rendering"""
        self.last_width = self.winfo_width()
        self.last_height = self.winfo_height()

    def create_menu(self):
        menubar = tk.Menu(self)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Master Folder", command=self.select_master_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Export Selected", command=self.export_selected)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_radiobutton(label="Show 1 Slide", variable=self.slides_per_view, value=1, 
                                  command=self.update_slides_per_view)
        view_menu.add_radiobutton(label="Show 2 Slides", variable=self.slides_per_view, value=2,
                                  command=self.update_slides_per_view)
        view_menu.add_radiobutton(label="Show 3 Slides", variable=self.slides_per_view, value=3,
                                  command=self.update_slides_per_view)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Add menus to menubar
        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="View", menu=view_menu)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=menubar)

    def create_main_frame(self):
        # Main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top control panel
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(control_frame, text="Master Folder:").pack(side=tk.LEFT, padx=(0, 5))
        self.folder_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.folder_var, width=50, state="readonly").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Browse...", command=self.select_master_folder).pack(side=tk.LEFT)
        
        # Navigation frame
        nav_frame = ttk.Frame(self.main_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(nav_frame, text="←", width=3, command=lambda: self.navigate_sequence(-1)).pack(side=tk.LEFT, padx=(0, 5))
        self.sequence_label = ttk.Label(nav_frame, text="Sequence: 0 / 0")
        self.sequence_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="→", width=3, command=lambda: self.navigate_sequence(1)).pack(side=tk.LEFT, padx=5)
        
        # Slides container
        self.slides_container = ttk.Frame(self.main_frame)
        self.slides_container.pack(fill=tk.BOTH, expand=True)
        
        # Create empty slide frames initially
        self.slide_frames = []
        for i in range(3):  # Max 3 slides
            frame = self.create_slide_frame(i)
            self.slide_frames.append(frame)
    
    def create_slide_frame(self, index):
        frame = ttk.Frame(self.slides_container)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        frame.columnconfigure(0, weight=1)  # Make column expandable
        frame.rowconfigure(1, weight=1)     # Make image row expandable
        
        # Up arrow button
        up_button = ttk.Button(frame, text="▲", width=3)
        up_button.grid(row=0, column=0, pady=(0, 5), sticky="n")
        up_button.configure(command=lambda idx=index: self.navigate_version(idx, -1))
        
        # Image container (with border)
        img_frame = ttk.Frame(frame, borderwidth=2, relief="groove")
        img_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        img_frame.columnconfigure(0, weight=1)
        img_frame.rowconfigure(0, weight=1)
        
        # Image label
        img_label = ttk.Label(img_frame)
        img_label.grid(row=0, column=0, sticky="nsew")
        
        # Version info
        version_frame = ttk.Frame(frame)
        version_frame.grid(row=2, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Label(version_frame, text="Folder:").pack(side=tk.LEFT)
        version_var = tk.StringVar()
        version_label = ttk.Label(version_frame, textvariable=version_var)
        version_label.pack(side=tk.LEFT, padx=5)
        
        # Down arrow button
        down_button = ttk.Button(frame, text="▼", width=3)
        down_button.grid(row=3, column=0, pady=(0, 5), sticky="s")
        down_button.configure(command=lambda idx=index: self.navigate_version(idx, 1))
        
        # Store references to widgets
        frame.img_label = img_label
        frame.version_var = version_var
        frame.up_button = up_button
        frame.down_button = down_button
        frame.current_folder_index = 0
        frame.image_name = None
        frame.img_frame = img_frame
        
        return frame

    def create_status_bar(self):
        self.status_bar = ttk.Frame(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_label = ttk.Label(self.status_bar, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=2)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.status_bar, mode='determinate')
        self.progress.pack(side=tk.RIGHT, padx=5, pady=2)

    def select_master_folder(self):
        folder = filedialog.askdirectory(title="Select Master Folder")
        if folder:
            self.master_folder = folder
            self.folder_var.set(folder)
            
            # Start scanning in a separate thread to keep UI responsive
            threading.Thread(target=self.scan_master_folder, daemon=True).start()
    
    def scan_master_folder(self):
        """Scan the master folder for images and build the catalog"""
        try:
            self.status_var.set("Scanning master folder...")
            self.image_catalog = defaultdict(dict)
            self.folders = []
            
            # Get all immediate subfolders
            self.folders = [f for f in os.listdir(self.master_folder) 
                           if os.path.isdir(os.path.join(self.master_folder, f))]
                           
            if not self.folders:
                raise ValueError("No subfolders found in master folder")
                
            # Initialize progress bar
            total_folders = len(self.folders)
            self.progress["maximum"] = total_folders
            self.progress["value"] = 0
            
            # Scan each subfolder
            for folder_idx, folder in enumerate(self.folders):
                folder_path = os.path.join(self.master_folder, folder)
                
                # Get all images in the folder
                image_files = [f for f in os.listdir(folder_path) 
                              if os.path.isfile(os.path.join(folder_path, f)) and 
                              f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
                
                # Add to catalog
                for img in image_files:
                    self.image_catalog[img][folder] = os.path.join(folder_path, img)
                
                # Update progress
                self.progress["value"] = folder_idx + 1
                self.update_idletasks()
            
            # Get sorted list of image names
            self.image_names = sorted(list(self.image_catalog.keys()))
            
            # Log catalog info
            logger.info(f"Scanned master folder: {self.master_folder}")
            logger.info(f"Found {len(self.folders)} subfolders and {len(self.image_names)} unique images")
            
            # Update UI
            self.after(0, self.update_ui_after_scan)
        
        except Exception as e:
            logger.error(f"Error scanning master folder: {str(e)}")
            messagebox.showerror("Error", f"Failed to scan master folder: {str(e)}")
            self.status_var.set("Error scanning folder")
    
    def update_ui_after_scan(self):
        """Update the UI after folder scanning is complete"""
        if self.image_names:
            self.status_var.set(f"Found {len(self.folders)} folders with {len(self.image_names)} images")
            self.current_sequence_index = 0
            self.update_sequence_display()
        else:
            self.status_var.set("No images found in master folder")
    
    def update_slides_per_view(self):
        """Update the number of visible slides"""
        num_slides = self.slides_per_view.get()
        
        # Show/hide slide frames based on the selected count
        for i, frame in enumerate(self.slide_frames):
            if i < num_slides:
                frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            else:
                frame.pack_forget()
        
        # Refresh the display
        self.update_sequence_display()
        
        # Bind to configure event for dynamic resizing if not already bound
        if not hasattr(self, '_resize_bound') or not self._resize_bound:
            self.bind("<Configure>", self.on_window_resize)
            self._resize_bound = True
        
        # Reset window dimension tracking to force refresh
        self.last_width = 0
        self.last_height = 0
        self.check_and_update_size()
    
    def navigate_sequence(self, direction):
        """Navigate to the next/previous sequence of images"""
        if not self.image_names:
            return
            
        num_slides = self.slides_per_view.get()
        max_index = max(0, len(self.image_names) - num_slides)
        
        new_index = self.current_sequence_index + direction
        if 0 <= new_index <= max_index:
            self.current_sequence_index = new_index
            self.update_sequence_display()
    
    def navigate_version(self, slide_index, direction):
        """Navigate to the next/previous version (folder) of the image"""
        if not self.folders or slide_index >= len(self.slide_frames):
            return
            
        frame = self.slide_frames[slide_index]
        if not frame.image_name:
            return
            
        # Calculate the new folder index
        new_folder_index = (frame.current_folder_index + direction) % len(self.folders)
        frame.current_folder_index = new_folder_index
        
        # Update the image display
        self.display_image_in_frame(frame.image_name, frame, new_folder_index)
        
        # Update selected images dict
        self.selected_images[frame.image_name] = self.folders[new_folder_index]
    
    def update_sequence_display(self, resize_only=False):
        """Update the sequence navigation and slide display"""
        if not self.image_names:
            self.sequence_label.config(text="Sequence: 0 / 0")
            return
            
        num_slides = self.slides_per_view.get()
        max_index = max(0, len(self.image_names) - num_slides + 1)
        
        # Update sequence counter (unless this is just a resize operation)
        if not resize_only:
            self.sequence_label.config(
                text=f"Sequence: {self.current_sequence_index + 1} / {max_index}")
        
        # Update image displays
        for i in range(num_slides):
            if i < len(self.slide_frames):
                img_idx = self.current_sequence_index + i
                if img_idx < len(self.image_names):
                    img_name = self.image_names[img_idx]
                    # Force reload when resizing
                    self.display_image_in_frame(img_name, self.slide_frames[i], force_reload=resize_only)
                else:
                    self.clear_slide_frame(self.slide_frames[i])
    
    def on_window_resize(self, event=None):
        """
        Handle window resize events with improved timer-based approach and 
        threshold detection to minimize unnecessary reloads
        """
        # Skip if event is None
        if event is None:
            return
            
        # Skip if not related to our main window
        try:
            if event.widget != self:
                return
        except (AttributeError, TypeError):
            return  # Skip if event has no widget attribute
        
        # Cancel existing timer if one exists
        if self.resize_timer is not None:
            try:
                self.after_cancel(self.resize_timer)
            except Exception:
                pass
            self.resize_timer = None
        
        # Schedule a new timer
        self.resize_timer = self.after(200, self.check_and_update_size)

    def check_and_update_size(self):
        """Check if window size has changed significantly and update if needed"""
        # Clear the timer reference
        self.resize_timer = None
        
        # Only proceed if we have images
        if not self.image_names or not hasattr(self, 'current_sequence_index'):
            return
        
        # Get current dimensions
        current_width = self.winfo_width()
        current_height = self.winfo_height()
        
        # Check if size changed enough to warrant reloading
        width_delta = abs(current_width - self.last_width)
        height_delta = abs(current_height - self.last_height)
        
        if width_delta > self.size_threshold or height_delta > self.size_threshold:
            # Update stored dimensions
            self.last_width = current_width
            self.last_height = current_height
            
            # Update the display with resize flag
            self.update_sequence_display(resize_only=True)
            
            # Log size change
            logger.debug(f"Window resized to {current_width}x{current_height}, reloading images")
    
    def get_optimal_image_size(self):
        """Calculate the optimal image size based on current window dimensions"""
        # Get the number of visible slides
        num_slides = self.slides_per_view.get()
        
        # Calculate available width per slide (accounting for padding)
        available_width = (self.winfo_width() - 20) // num_slides  # 20px for padding
        
        # Calculate available height (accounting for buttons and labels)
        available_height = self.winfo_height() - 150  # Approximate space for other UI elements
        
        # Ensure we have positive dimensions
        max_dim = max(50, min(available_width, available_height))
        return (max_dim, max_dim)

    def display_image_in_frame(self, image_name, frame, folder_index=None, force_reload=False):
        """Display an image in the specified slide frame"""
        if image_name not in self.image_catalog:
            return
            
        # Set the image name for this frame
        frame.image_name = image_name
        
        # Determine which folder to use
        if folder_index is None:
            # If image was previously selected, use that folder
            if image_name in self.selected_images:
                folder_name = self.selected_images[image_name]
                folder_index = self.folders.index(folder_name)
            else:
                # Otherwise use the first folder
                folder_index = 0
        
        frame.current_folder_index = folder_index
        folder_name = self.folders[folder_index]
        
        # Update folder display
        frame.version_var.set(folder_name)
        
        # Get image path
        img_path = self.image_catalog[image_name].get(folder_name)
        if not img_path:
            # If image doesn't exist in this folder, show placeholder
            frame.img_label.config(text=f"Image not available in folder: {folder_name}")
            return
        
        # Load and display image in a separate thread (or use cached version)
        img_size = self.get_optimal_image_size()
        cache_key = f"{img_path}_{img_size[0]}x{img_size[1]}"
        
        if force_reload or cache_key not in self.image_cache:
            self.load_queue.put((img_path, frame, img_size))
            if not hasattr(self, 'loading_thread') or not self.loading_thread.is_alive():
                self.loading_thread = threading.Thread(target=self.load_images_thread, daemon=True)
                self.loading_thread.start()
        else:
            # Use cached image
            frame.img_label.config(image=self.image_cache[cache_key])
    
    def load_images_thread(self):
        """Thread to load images in the background"""
        while True:
            try:
                if self.load_queue.empty():
                    break
                    
                img_path, frame, img_size = self.load_queue.get(timeout=1)
                
                # Load and resize image
                img = Image.open(img_path)
                img.thumbnail(img_size)  # Resize image to fit in frame
                photo = ImageTk.PhotoImage(img)
                
                # Create cache key based on path and size
                cache_key = f"{img_path}_{img_size[0]}x{img_size[1]}"
                
                # Store in cache and update UI in main thread
                self.image_cache[cache_key] = photo
                self.after(0, lambda f=frame, p=photo: f.img_label.config(image=p))
                
            except queue.Empty:
                break  # Exit when queue is empty
            except Exception as e:
                logger.error(f"Error loading image {img_path}: {str(e)}")
                self.after(0, lambda f=frame: f.img_label.config(text="Error loading image"))
    
    def clear_slide_frame(self, frame):
        """Clear a slide frame"""
        frame.img_label.config(image='', text='No image')
        frame.version_var.set('')
        frame.image_name = None
    
    def export_selected(self):
        """Export selected images to a zip file"""
        if not self.selected_images:
            messagebox.showinfo("Export", "No images have been selected yet")
            return
        
        # Ask for export location
        export_path = filedialog.asksaveasfilename(
            title="Export Selected Images",
            defaultextension=".zip",
            filetypes=[("Zip files", "*.zip"), ("All files", "*.*")]
        )
        
        if not export_path:
            return
            
        try:
            # Create a zip file
            with zipfile.ZipFile(export_path, 'w') as zipf:
                for img_name, folder_name in self.selected_images.items():
                    img_path = self.image_catalog[img_name].get(folder_name)
                    if img_path and os.path.exists(img_path):
                        # Add file to zip with just the image name (not the folder path)
                        zipf.write(img_path, img_name)
            
            messagebox.showinfo("Export Successful", 
                               f"Successfully exported {len(self.selected_images)} images to {export_path}")
            
            logger.info(f"Exported {len(self.selected_images)} images to {export_path}")
        
        except Exception as e:
            logger.error(f"Error exporting images: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export images: {str(e)}")
    
    def show_about(self):
        """Show the about dialog"""
        messagebox.showinfo("About Slide Chooser", 
                            "Slide Chooser v1.0\n\n"
                            "A tool for comparing and selecting the best images "
                            "across multiple batches of similar prompts.")

if __name__ == "__main__":
    try:
        app = SlideChooser()
        app.mainloop()
    except Exception as e:
        logging.error(f"Application error: {str(e)}", exc_info=True)
        messagebox.showerror("Application Error", f"An unexpected error occurred: {str(e)}")