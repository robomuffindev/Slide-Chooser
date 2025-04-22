# Slide Chooser

A Python-based application that helps you compare and select the best images across multiple batches of similar prompts.

![SlideChooserAppImg](https://github.com/user-attachments/assets/e79d3208-0b98-4bb1-987b-39bd75022573)


## Overview

Slide Chooser is designed for artists, designers, and content creators who generate multiple batches of similar images (e.g., from AI image generators, rendering pipelines, or photo sessions) and need to efficiently compare and select the best versions.

The application allows you to:
- View multiple images in sequence
- Compare different versions of the same image across folders
- Select your preferred versions
- Export your selections as a ZIP file for further processing

## Features

- **Master Folder Selection**: Point to a folder containing subfolders of image batches
- **Multi-Image View**: Display 1, 2, or 3 images at once
- **Sequence Navigation**: Move forward and backward through the image sequences
- **Version Comparison**: Navigate up and down between versions of the same image in different folders
- **Export Functionality**: Create a ZIP file of your selected images
- **Responsive Design**: Images automatically resize with the window
- **Performance Optimizations**: 
  - Background image loading
  - Size-aware image caching
  - Efficient window resize handling

## Requirements

- Python 3.8 or newer
- PIL (Pillow) library for image processing

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/slide-chooser.git
   cd slide-chooser
   ```

2. Run the installer script:
   - On Windows: Double-click `installer.bat` or run it from the command line
   - On macOS/Linux: Run `chmod +x installer.sh && ./installer.sh`

The installer will create a Python virtual environment and install all required dependencies.

## Usage

1. Launch the application:
   - On Windows: Double-click `run.bat` or run it from the command line
   - On macOS/Linux: Run `./run.sh`

2. Click "Browse..." to select your master folder containing subfolders of images.

3. Navigate through the images:
   - Left/Right arrows (or buttons) to move through the sequence
   - Up/Down arrows on each image to switch between versions in different folders

4. Once you've selected your preferred images, go to File > Export Selected to create a ZIP file.

## Folder Structure Requirements

The application expects a specific folder structure:
```
MASTER_FOLDER/
├── Batch1/
│   ├── image_001.jpg
│   ├── image_002.jpg
│   └── ...
├── Batch2/
│   ├── image_001.jpg
│   ├── image_002.jpg
│   └── ...
└── ...
```

Each subfolder should contain images with the same filenames across all batches.

## Keyboard Shortcuts

- **Left Arrow**: Previous sequence
- **Right Arrow**: Next sequence
- **Esc**: Exit the application

## Technical Details

### Dynamic Image Resizing

The application now features a sophisticated image resizing system that:
- Resizes images automatically when the window size changes
- Uses threshold detection to prevent unnecessary reloads during small window adjustments
- Implements a timer-based approach to handle rapid resize events efficiently
- Caches images at different sizes for optimal performance

### Performance Optimizations

- **Background Threading**: Image loading happens in a separate thread to keep the UI responsive
- **Smart Caching**: Images are cached based on both path and size
- **Debounced Resizing**: Window resize events are efficiently managed to prevent excessive reloading
- **Grid Layout System**: Improved layout management for better scaling with window size

## Project Structure

```
slide-chooser/
├── slide_chooser.py    # Main application code
├── installer.bat       # Windows installation script
├── run.bat             # Windows launch script
├── installer.sh        # macOS/Linux installation script (optional)
├── run.sh              # macOS/Linux launch script (optional)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Tkinter](https://docs.python.org/3/library/tkinter.html) - Python's standard GUI package
- [Pillow](https://pillow.readthedocs.io/) - Python Imaging Library

Project Link: [https://github.com/yourusername/slide-chooser](https://github.com/yourusername/slide-chooser)
