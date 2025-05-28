import os
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
import threading
import time
import shlex  # Added for proper handling of paths with spaces
import re  # Added for case-insensitive file extension matching

def is_float(s):
    try:
        float(s)
        return True
    except:
        return False

def is_hkx_file(filename):
    """Check if file is an HKX file (case insensitive)"""
    return bool(re.search(r'\.hkx$', filename, re.IGNORECASE))

def is_txt_or_json_file(filename):
    """Check if file is a TXT or JSON file (case insensitive)"""
    return bool(re.search(r'\.(txt|json)$', filename, re.IGNORECASE))

class ModernHKXShift:
    def __init__(self, root):
        self.root = root
        self.root.title("HKXShift - Skyrim Animation Speed Adjuster v1.3")
        self.root.geometry("900x650")
        self.root.configure(bg="#f5f5f5")
        self.root.minsize(800, 600)
        
        # Debug mode for verbose logging
        self.debug_mode = False
        
        # Track last used values
        self.last_used_directory = ""
        self.last_used_multiplier = 1.0
        
        # Set app icon if available
        try:
            self.root.iconbitmap("hkxshift.ico")
        except:
            pass
            
        # Main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create a style
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("TButton", padding=5, font=("Segoe UI", 10))
        self.style.configure("TLabel", background="#f5f5f5", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        self.style.configure("Subheader.TLabel", font=("Segoe UI", 12))
        
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header_frame, text="HKXShift", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(header_frame, text="by Hoverstein", foreground="#666666").pack(side=tk.LEFT, padx=(5, 0), pady=5)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.setup_tab = ttk.Frame(self.notebook)
        self.console_tab = ttk.Frame(self.notebook)
        self.help_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.setup_tab, text="Setup")
        self.notebook.add(self.console_tab, text="Console")
        self.notebook.add(self.help_tab, text="Help")
        
        # Setup Tab Content
        self.create_setup_tab()
        
        # Console Tab Content
        self.create_console_tab()
        
        # Help Tab Content
        self.create_help_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Processing state
        self.processing = False

    def create_setup_tab(self):
        # Input folder section
        input_frame = ttk.LabelFrame(self.setup_tab, text="Input Settings")
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(input_frame, text="Source Folder:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.input_frame_path = ttk.Frame(input_frame)
        self.input_frame_path.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        input_frame.columnconfigure(1, weight=1)
        
        self.input_entry = ttk.Entry(self.input_frame_path)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(self.input_frame_path, text="Browse", command=self.browse_folder).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Speed multiplier section
        speed_frame = ttk.Frame(input_frame)
        speed_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
        
        ttk.Label(speed_frame, text="Speed Multiplier:").pack(side=tk.LEFT)
        
        # Create a frame for the scale and entry
        scale_entry_frame = ttk.Frame(speed_frame)
        scale_entry_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        # Create the scale
        self.speed_scale = ttk.Scale(scale_entry_frame, from_=0.1, to=2.0, orient=tk.HORIZONTAL, length=200)
        self.speed_scale.set(1.0)
        self.speed_scale.pack(side=tk.LEFT)
        
        # Create speed entry with validation
        vcmd = (self.root.register(self.validate_float), '%P')
        self.speed_entry = ttk.Entry(scale_entry_frame, width=5, validate="key", validatecommand=vcmd)
        self.speed_entry.insert(0, "1.0")
        self.speed_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Link scale and entry
        self.speed_scale.configure(command=self.update_speed_entry)
        self.speed_entry.bind("<FocusOut>", self.update_speed_scale)
        self.speed_entry.bind("<Return>", self.update_speed_scale)
        
        # Preset buttons
        presets_frame = ttk.LabelFrame(self.setup_tab, text="Recommended Speed Presets")
        presets_frame.pack(fill=tk.X, padx=10, pady=10)
        
        preset_buttons_frame = ttk.Frame(presets_frame)
        preset_buttons_frame.pack(pady=5)
        
        presets = [
            ("x0.7 (Faster)", 0.7),
            ("x0.8", 0.8),
            ("x0.9", 0.9),
            ("x1.0 (Original)", 1.0),
            ("x1.1", 1.1),
            ("x1.2", 1.2),
            ("x1.3 (Slower)", 1.3),
        ]
        
        for i, (label, value) in enumerate(presets):
            btn = ttk.Button(preset_buttons_frame, text=label, 
                             command=lambda v=value: self.set_preset_speed(v))
            btn.grid(row=0, column=i, padx=5, pady=5)
        
        # Options section
        options_frame = ttk.LabelFrame(self.setup_tab, text="Options")
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.delete_temp_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Delete temporary files after completion", 
                       variable=self.delete_temp_var).pack(anchor=tk.W, padx=5, pady=5)
        
        self.open_folder_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Open results folder when complete", 
                       variable=self.open_folder_var).pack(anchor=tk.W, padx=5, pady=5)
        
        # Add backup option
        self.backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Create backup of original files", 
                       variable=self.backup_var).pack(anchor=tk.W, padx=5, pady=5)
        
        # Debug mode option
        self.debug_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Enable debug logging", 
                       variable=self.debug_var, command=self.toggle_debug).pack(anchor=tk.W, padx=5, pady=5)
        
        # Action buttons
        buttons_frame = ttk.Frame(self.setup_tab)
        buttons_frame.pack(fill=tk.X, padx=10, pady=(20, 10))
        
        self.run_button = ttk.Button(buttons_frame, text="Run HKXShift", command=self.run_shift_threaded)
        self.run_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.cancel_button = ttk.Button(buttons_frame, text="Cancel", command=self.cancel_operation, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.RIGHT, padx=(5, 0))

    def toggle_debug(self):
        """Toggle debug mode"""
        self.debug_mode = self.debug_var.get()
        if self.debug_mode:
            self.log("Debug mode enabled")
        else:
            self.log("Debug mode disabled")

    def create_console_tab(self):
        console_frame = ttk.Frame(self.console_tab)
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Progress bar frame
        progress_frame = ttk.Frame(console_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(progress_frame, text="Overall Progress:").pack(side=tk.LEFT)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           length=500, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)
        
        # Progress percentage label
        self.progress_percent = tk.StringVar(value="0%")
        ttk.Label(progress_frame, textvariable=self.progress_percent, width=5).pack(side=tk.LEFT)
        
        # Console output
        self.console_output = ScrolledText(console_frame, width=80, height=20, wrap=tk.WORD, 
                                          font=("Consolas", 10))
        self.console_output.pack(fill=tk.BOTH, expand=True)
        self.console_output.configure(state=tk.DISABLED)
        
        # Console buttons
        console_buttons = ttk.Frame(console_frame)
        console_buttons.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(console_buttons, text="Copy to Clipboard", 
                  command=self.copy_output).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(console_buttons, text="Clear Console", 
                  command=self.clear_console).pack(side=tk.RIGHT, padx=(5, 0))

    def create_help_tab(self):
        help_frame = ttk.Frame(self.help_tab)
        help_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Help text
        help_text = ScrolledText(help_frame, width=80, height=20, wrap=tk.WORD)
        help_text.pack(fill=tk.BOTH, expand=True)
        
        help_content = """# HKXShift - Skyrim Animation Speed Adjuster v1.3

# UPDATE LOG
## Changes in v1.3:
- Added backup option feature
- Adjusted recommended speed multiplier presets
- Will show a warning if you use extreme speed multiplier (e.g. 0.5 or 1.5)
- As always, might introduce more sneaky bugs!

## Changes in v1.2:
- Added support or compatibility for .HKX (uppercase) files
- Added copying of TXT and/or JSON files from source to result folders
- Your _conditions.txt and/or config.json will be copied now
- Added display of HKX, TXT, and JSON file counts
- Introduce hard limits on speed multiplier (0.1 to 2.0)
- Show prevention of using 1.0 (no change in speed) multiplier
- Show notice when source directory changes but multiplier doesn't
- Might introduce even more new bugs!

## Changes in v1.1:
- Addressed security concerns revolving around shell=True code
- Less likely to be flagged as false positive or unsafe by the system or antiviruses
- Added debug logging option
- Enhanced error reporting
- Might introduce unexpected bugs, please report if you found any!

## What does it do?
HKXShift allows you to adjust the timing of Skyrim animation files (.hkx) by speeding them up or slowing them down.

## How to use:
1. Select the source folder containing .hkx files or subfolders with .hkx files
2. Set your desired speed multiplier (below 1.0 speeds up, above 1.0 slows down)
3. Click "Run HKXShift"
4. Wait for processing to complete
5. Find your results in the HKXShift_results folder in the same directory as this application
6. Your usable folder has "-merged" in it's name

## Requirements:
- hkanno64.exe must be in the same folder as this application
- Make sure you have read/write permissions for the folders
- Speed multiplier cannot be 1.0 (as this would make no changes)

## Tips:
- Use the presets for common speed adjustments
- The program will automatically detect single folder or batch mode
- Check the Console tab for detailed processing information
- Enable debug logging for more detailed output when troubleshooting
- TXT and JSON files from the source folder will be copied to the result folder
- Original files are backed up to the backup folder for safety

## About:
HKXShift was created by Hoverstein
https://next.nexusmods.com/profile/Hoverstein
"""
        help_text.insert(tk.END, help_content)
        help_text.configure(state=tk.DISABLED)

    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)
            self.notebook.select(self.setup_tab)

    def validate_float(self, value):
        if value == "":
            return True
        try:
            val = float(value)
            return 0.1 <= val <= 2.0  # Hard limits between 0.1 and 2.0
        except:
            return False

    def update_speed_entry(self, val):
        value = round(float(val), 2)
        self.speed_entry.delete(0, tk.END)
        self.speed_entry.insert(0, f"{value:.2f}")

    def update_speed_scale(self, event=None):
        try:
            value = float(self.speed_entry.get())
            if 0.1 <= value <= 2.0:
                self.speed_scale.set(value)
        except:
            pass

    def set_preset_speed(self, value):
        self.speed_scale.set(value)
        self.update_speed_entry(value)

    def update_progress(self, value, message=None):
        """Update progress bar and status message"""
        self.progress_var.set(value)
        self.progress_percent.set(f"{value:.1f}%")
        if message:
            self.status_var.set(message)
        self.root.update()

    def log(self, message, debug=False):
        """Log messages to console with debug option"""
        # Skip debug messages unless debug mode is enabled
        if debug and not self.debug_mode:
            return
            
        # Prefix debug messages
        if debug:
            message = "[DEBUG] " + message
            
        self.console_output.configure(state=tk.NORMAL)
        self.console_output.insert(tk.END, message + "\n")
        self.console_output.see(tk.END)
        self.console_output.configure(state=tk.DISABLED)
        
        # Only update status bar with non-debug messages
        if not debug:
            self.status_var.set(message.strip())
            
        self.root.update()

    def copy_output(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.console_output.get("1.0", tk.END))
        messagebox.showinfo("Copied", "Console output copied to clipboard.")

    def clear_console(self):
        self.console_output.configure(state=tk.NORMAL)
        self.console_output.delete("1.0", tk.END)
        self.console_output.configure(state=tk.DISABLED)
        self.progress_var.set(0)
        self.progress_percent.set("0%")

    def cancel_operation(self):
        if self.processing:
            self.processing = False
            self.log("⚠️ Operation cancelled by user")
            self.status_var.set("Cancelled")
            self.update_button_states(False)
            self.notebook.select(self.setup_tab)  # Return to setup tab

    def update_button_states(self, is_processing):
        if is_processing:
            self.run_button.configure(state=tk.DISABLED)
            self.cancel_button.configure(state=tk.NORMAL)
        else:
            self.run_button.configure(state=tk.NORMAL)
            self.cancel_button.configure(state=tk.DISABLED)

    def run_shift_threaded(self):
        # Create a thread to run the process
        threading.Thread(target=self.run_shift, daemon=True).start()
    
    # Safe subprocess execution with proper shlex handling for paths with spaces
    def run_hkanno_cmd(self, cmd_type, args):
        """Run hkanno64.exe command with proper argument parsing for paths with spaces"""
        if not os.path.isfile("hkanno64.exe"):
            return None, "hkanno64.exe not found"
        
        # Build command list based on type
        cmd_list = ["hkanno64.exe"]
        cmd_list.extend(cmd_type)
        cmd_list.extend(args)
        
        try:
            # Log the command for debugging using shlex.quote for safe display
            cmd_str = " ".join(shlex.quote(str(arg)) for arg in cmd_list)
            self.log(f"Running command: {cmd_str}", debug=True)
            
            # Run the command without shell=True
            result = subprocess.run(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Log return code for debugging
            self.log(f"Command return code: {result.returncode}", debug=True)
            
            # Filter output
            filtered = [line for line in (result.stdout + result.stderr).splitlines() if "hctFilterTexture.dll" not in line]
            return filtered, None
        except Exception as e:
            error_msg = str(e)
            self.log(f"Command execution error: {error_msg}", debug=True)
            return None, error_msg

    def handle_file_path(self, path):
        """Quote a file path for safe display in logs"""
        return shlex.quote(path)
        
    def backup_source(self, source, results_dir, base):
        """Create a backup of the source folder structure and files"""
        if not self.backup_var.get():
            self.log("Backup skipped (disabled in options)")
            return 0
            
        self.log("\n--- Creating backup of original files ---")
        
        backup_dir = os.path.join(results_dir, f"{base}-backup")
        backed_up_files = 0
        
        self.log(f"Backup location: {self.handle_file_path(backup_dir)}")
        
        # Handle single mode (source directory contains HKX files directly)
        if any(is_hkx_file(f) for f in os.listdir(source)):
            # Create backup directory
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy all files from source to backup
            for file in os.listdir(source):
                try:
                    src_file = os.path.join(source, file)
                    if os.path.isfile(src_file):
                        dest_file = os.path.join(backup_dir, file)
                        shutil.copy2(src_file, dest_file)
                        backed_up_files += 1
                except Exception as e:
                    self.log(f"⚠️ Error backing up {file}: {str(e)}", debug=True)
        else:
            # Batch mode - copy folder structure
            for root, dirs, files in os.walk(source):
                # Get relative path from source
                rel_path = os.path.relpath(root, source)
                if rel_path == '.':
                    rel_path = ''
                
                # Create directory in backup
                backup_subdir = os.path.join(backup_dir, rel_path)
                os.makedirs(backup_subdir, exist_ok=True)
                
                # Copy all files
                for file in files:
                    try:
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(backup_subdir, file)
                        shutil.copy2(src_file, dest_file)
                        backed_up_files += 1
                    except Exception as e:
                        self.log(f"⚠️ Error backing up {file}: {str(e)}", debug=True)
        
        self.log(f"✅ Backed up {backed_up_files} files")
        return backed_up_files

    def run_shift(self):
        if self.processing:
            return
            
        self.processing = True
        self.update_button_states(True)
        self.clear_console()
        self.notebook.select(self.console_tab)
        
        # Reset progress
        self.progress_var.set(0)
        self.progress_percent.set("0%")
        
        source = self.input_entry.get().strip()
        multiplier_str = self.speed_entry.get().strip()
        
        # Log path for debugging
        self.log(f"Source path: {self.handle_file_path(source)}", debug=True)
        
        if not os.path.isdir(source):
            messagebox.showerror("Error", "Source folder does not exist.")
            self.update_button_states(False)
            self.processing = False
            self.notebook.select(self.setup_tab)  # Return to setup tab
            return
            
        if not os.path.isfile("hkanno64.exe"):
            messagebox.showerror("Error", "hkanno64.exe not found in current directory.")
            self.update_button_states(False)
            self.processing = False
            self.notebook.select(self.setup_tab)  # Return to setup tab
            return
            
        if not is_float(multiplier_str):
            messagebox.showerror("Error", "Invalid speed multiplier.")
            self.update_button_states(False)
            self.processing = False
            self.notebook.select(self.setup_tab)  # Return to setup tab
            return
        
        # Check if multiplier is 1.0 (no change)    
        scale = float(multiplier_str)
        if scale == 1.0:
            messagebox.showerror("Error", 
                               "Speed multiplier is set to 1.0, which will not change animation speed.\n\n"
                               "Please select a different multiplier value.")
            self.update_button_states(False)
            self.processing = False
            self.notebook.select(self.setup_tab)  # Return to setup tab
            return
        
        # Warning for extreme speed multipliers
        if scale <= 0.6 or scale >= 1.4:
            warning_message = (
                f"Warning: Speed multiplier {scale} is outside the recommended range.\n\n"
                f"Extreme speed multipliers may cause animations to play\n"
                f"significantly faster or slower but with inaccurate hit registration!\n\n"
                f"Do you want to continue anyway?"
            )
            if not messagebox.askyesno("Speed Multiplier Warning", warning_message):
                # User chose to cancel after the warning
                self.update_button_states(False)
                self.processing = False
                self.notebook.select(self.setup_tab)  # Return to setup tab
                return
                
        # Check if directory changed but multiplier is the same as last time
        if self.last_used_directory != source and self.last_used_multiplier == scale and self.last_used_directory != "":
            response = messagebox.askyesno("Notice", 
                                        f"You've changed the source directory but are using the same speed multiplier ({scale}).\n\n"
                                        "Do you want to continue with this multiplier?")
            if not response:
                self.update_button_states(False)
                self.processing = False
                self.notebook.select(self.setup_tab)  # Return to setup tab
                return
                
        # Store current values for next run
        self.last_used_directory = source
        self.last_used_multiplier = scale
            
        base = os.path.basename(os.path.normpath(source))
        results_dir = "HKXShift_results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Create backup if enabled
        backed_up_files = self.backup_source(source, results_dir, base)
        
        summary = {
            'dumped': 0, 
            'scaled': 0, 
            'merged': 0, 
            'failed': 0, 
            'hkx_count': 0, 
            'txt_count': 0, 
            'json_count': 0,
            'backed_up': backed_up_files
        }
        
        log_path = os.path.join(results_dir, f"{base}_log.txt")
        
        # Find folders with HKX files (case insensitive)
        folders = []
        if os.path.isdir(source):
            for item in os.listdir(source):
                item_path = os.path.join(source, item)
                if os.path.isdir(item_path) and any(is_hkx_file(f) for f in os.listdir(item_path)):
                    folders.append(item_path)
                  
        # Single mode detection with case-insensitive HKX check
        if not folders and any(is_hkx_file(f) for f in os.listdir(source)):
            folders = [source]  # Single mode
            self.log("📁 Single folder mode detected.")
        elif not folders:
            messagebox.showerror("Error", "No .hkx files or valid subfolders found.")
            self.update_button_states(False)
            self.processing = False
            self.notebook.select(self.setup_tab)  # Return to setup tab
            return
        else:
            self.log(f"🔁 Batch mode detected: {len(folders)} subfolders")
        
        # Log folder paths for debugging
        if self.debug_mode:
            self.log("Folders to process:", debug=True)
            for folder in folders:
                self.log(f"  - {self.handle_file_path(folder)}", debug=True)
        
        # Progress tracking
        total_files = 0
        for folder in folders:
            hkx_files = [f for f in os.listdir(folder) if is_hkx_file(f)]
            total_files += len(hkx_files)
            summary['hkx_count'] += len(hkx_files)
            
            # Count TXT and JSON files
            txt_files = [f for f in os.listdir(folder) if f.lower().endswith('.txt')]
            json_files = [f for f in os.listdir(folder) if f.lower().endswith('.json')]
            summary['txt_count'] += len(txt_files)
            summary['json_count'] += len(json_files)
        
        processed_files = 0
        self.update_progress(0, f"Processing {total_files} files...")
        
        # Log file counts
        self.log(f"📄 Found {summary['hkx_count']} HKX files to process")
        self.log(f"📄 Found {summary['txt_count']} TXT files to copy")
        self.log(f"📄 Found {summary['json_count']} JSON files to copy")
        self.log(f"📄 Backed up {summary['backed_up']} files")
        
        start_time = time.time()
        
        with open(log_path, "w", encoding="utf-8") as log_file:
            # Calculate total operations for progress tracking
            # Each file needs: dump + scale + merge = 3 operations
            total_operations = total_files * 3
            completed_operations = 0
            
            for folder in folders:
                if not self.processing:
                    break
                    
                subname = os.path.basename(folder)
                self.log(f"\n--- Processing: {subname} ---")
                
                converted = os.path.join(results_dir, f"{base}-converted", subname)
                rescaled = os.path.join(results_dir, f"{base}-rescaled", subname)
                merged = os.path.join(results_dir, f"{base}-merged", subname)
                
                # Log path debug info
                self.log(f"Converted dir: {self.handle_file_path(converted)}", debug=True)
                self.log(f"Rescaled dir: {self.handle_file_path(rescaled)}", debug=True)
                self.log(f"Merged dir: {self.handle_file_path(merged)}", debug=True)
                
                os.makedirs(converted, exist_ok=True)
                os.makedirs(rescaled, exist_ok=True)
                os.makedirs(merged, exist_ok=True)
                
                # Get all HKX files (case-insensitive)
                hkx_files = [f for f in os.listdir(folder) if is_hkx_file(f)]
                
                # Get all TXT and JSON files to copy
                txt_json_files = [f for f in os.listdir(folder) if is_txt_or_json_file(f)]
                
                # Copy TXT and JSON files to merged output folder
                for file in txt_json_files:
                    try:
                        src = os.path.join(folder, file)
                        dest = os.path.join(merged, file)
                        self.log(f"  Copying support file: {file}", debug=True)
                        shutil.copy2(src, dest)
                    except Exception as e:
                        self.log(f"  ⚠️ Error copying {file}: {str(e)}", debug=True)
                
                # Step 1: Dump annotation files
                for idx, file in enumerate(hkx_files, 1):
                    if not self.processing:
                        break
                        
                    processed_files += 1
                    completed_operations += 1
                    progress = (completed_operations / total_operations) * 100
                    
                    self.update_progress(progress, f"Dumping {file}...")
                    self.log(f"  Dumping {file} ({idx}/{len(hkx_files)})")
                    
                    try:
                        src = os.path.join(folder, file)
                        dest_dir = os.path.join(converted, file)
                        os.makedirs(dest_dir, exist_ok=True)
                        dest_hkx = os.path.join(dest_dir, file)
                        
                        # Log file paths for debugging
                        self.log(f"Source file: {self.handle_file_path(src)}", debug=True)
                        self.log(f"Destination HKX: {self.handle_file_path(dest_hkx)}", debug=True)
                        
                        shutil.copy2(src, dest_hkx)
                        
                        # Run the command safely
                        out_anno_file = os.path.join(dest_dir, "anno.txt")
                        filtered, error = self.run_hkanno_cmd(
                            ["dump", "-o", out_anno_file], 
                            [dest_hkx]
                        )
                        
                        if error:
                            log_file.write(f"[ERROR - DUMP] {file}: {error}\n")
                            summary['failed'] += 1
                            self.log(f"  ⚠️ Error dumping {file}: {error}", debug=True)
                        else:
                            log_file.write(f"[DUMP] {file}\n" + "\n".join(filtered) + "\n\n")
                            summary['dumped'] += 1
                            
                    except Exception as e:
                        error_msg = str(e)
                        log_file.write(f"[ERROR - DUMP] {file}: {error_msg}\n")
                        summary['failed'] += 1
                        self.log(f"  ⚠️ Exception while dumping {file}: {error_msg}")
                
                # Step 2: Rescale annotations
                for idx, sub in enumerate(os.listdir(converted), 1):
                    if not self.processing:
                        break
                        
                    completed_operations += 1
                    progress = (completed_operations / total_operations) * 100
                    
                    self.update_progress(progress, f"Rescaling {sub}...")
                    self.log(f"  Rescaling {sub} ({idx}/{len(os.listdir(converted))})")
                    
                    in_path = os.path.join(converted, sub)
                    out_path = os.path.join(rescaled, sub)
                    anno_in = os.path.join(in_path, "anno.txt")
                    anno_out = os.path.join(out_path, "anno.txt")
                    hkx_file = os.path.join(in_path, sub)
                    hkx_copy = os.path.join(out_path, sub)
                    
                    # Log paths for debugging
                    self.log(f"Anno in: {self.handle_file_path(anno_in)}", debug=True)
                    self.log(f"Anno out: {self.handle_file_path(anno_out)}", debug=True)
                    
                    if os.path.isfile(anno_in):
                        os.makedirs(out_path, exist_ok=True)
                        try:
                            shutil.copy2(hkx_file, hkx_copy)
                        except Exception as e:
                            error_msg = str(e)
                            log_file.write(f"[ERROR - COPY] {hkx_file}: {error_msg}\n")
                            summary['failed'] += 1
                            self.log(f"  ⚠️ Error copying HKX file: {error_msg}")
                            continue
                        
                        modified_lines = []
                        try:
                            with open(anno_in, "r", encoding="utf-8") as file:
                                for line in file:
                                    parts = line.strip().split(" ", 1)
                                    if len(parts) < 2 or not is_float(parts[0]):
                                        modified_lines.append(line)
                                        continue
                                    try:
                                        new_time = f"{float(parts[0]) * scale:.6f}"
                                        modified_lines.append(f"{new_time} {parts[1]}\n")
                                    except:
                                        modified_lines.append(line)
                            with open(anno_out, "w", encoding="utf-8") as file:
                                file.writelines(modified_lines)
                            summary['scaled'] += 1
                        except Exception as e:
                            error_msg = str(e)
                            log_file.write(f"[ERROR - SCALE] {anno_in}: {error_msg}\n")
                            summary['failed'] += 1
                            self.log(f"  ⚠️ Error scaling {sub}: {error_msg}")
                
                # Step 3: Merge annotations back into HKX files
                for idx, sub in enumerate(os.listdir(rescaled), 1):
                    if not self.processing:
                        break
                        
                    completed_operations += 1
                    progress = (completed_operations / total_operations) * 100
                    
                    self.update_progress(progress, f"Merging {sub}...")
                    self.log(f"  Merging {sub} ({idx}/{len(os.listdir(rescaled))})")
                    
                    path = os.path.join(rescaled, sub)
                    anno = os.path.join(path, "anno.txt")
                    hkx = os.path.join(path, sub)
                    merged_hkx = os.path.join(merged, sub)
                    
                    # Log paths for debugging
                    self.log(f"Anno path: {self.handle_file_path(anno)}", debug=True)
                    self.log(f"HKX path: {self.handle_file_path(hkx)}", debug=True)
                    self.log(f"Output path: {self.handle_file_path(merged_hkx)}", debug=True)
                    
                    if os.path.isfile(anno) and os.path.isfile(hkx):
                        try:
                            # Run the command safely
                            filtered, error = self.run_hkanno_cmd(
                                ["update", "-i", anno], 
                                [hkx]
                            )
                            
                            if error:
                                log_file.write(f"[ERROR - MERGE] {sub}: {error}\n")
                                summary['failed'] += 1
                                self.log(f"  ⚠️ Error merging {sub}: {error}")
                            else:
                                log_file.write(f"[MERGE] {sub}\n" + "\n".join(filtered) + "\n\n")
                                shutil.copy2(hkx, merged_hkx)
                                summary['merged'] += 1
                                
                        except Exception as e:
                            error_msg = str(e)
                            log_file.write(f"[ERROR - MERGE] {sub}: {error_msg}\n")
                            summary['failed'] += 1
                            self.log(f"  ⚠️ Exception while merging {sub}: {error_msg}")
            
            # Write summary to log file
            duration = time.time() - start_time
            log_file.write("\n--- SUMMARY ---\n")
            log_file.write(f"Files Dumped: {summary['dumped']}\n")
            log_file.write(f"Files Scaled: {summary['scaled']}\n")
            log_file.write(f"Files Merged: {summary['merged']}\n")
            log_file.write(f"Files Failed: {summary['failed']}\n")
            log_file.write(f"HKX Files Found: {summary['hkx_count']}\n")
            log_file.write(f"TXT Files Found: {summary['txt_count']}\n")
            log_file.write(f"JSON Files Found: {summary['json_count']}\n")
            log_file.write(f"Files Backed Up: {summary['backed_up']}\n")
            log_file.write(f"Time Elapsed: {duration:.2f} seconds\n")
            
        # Show summary
        self.log("\n=== PROCESSING COMPLETE ===")
        self.log(f"✅ Files Processed: {summary['dumped']}")
        self.log(f"✅ Files Scaled: {summary['scaled']}")
        self.log(f"✅ Files Merged: {summary['merged']}")
        if summary['failed'] > 0:
            self.log(f"⚠️ Files Failed: {summary['failed']}")
            
        self.log(f"📄 HKX Files Found: {summary['hkx_count']}")
        self.log(f"📄 TXT Files Found: {summary['txt_count']}")
        self.log(f"📄 JSON Files Found: {summary['json_count']}")
        self.log(f"📄 Files Backed Up: {summary['backed_up']}")
        
        self.log(f"⏱️ Time Elapsed: {duration:.2f} seconds")
        
        # Delete temp files if requested
        if self.delete_temp_var.get():
            self.log("\nCleaning up temporary files...")
            try:
                for folder in ["converted", "rescaled"]:
                    temp_dir = os.path.join(results_dir, f"{base}-{folder}")
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                self.log("✅ Cleanup complete")
            except Exception as e:
                self.log(f"⚠️ Error during cleanup: {str(e)}")
        
        # Open results folder if requested
        out_path = os.path.join(results_dir, f"{base}-merged")
        if self.open_folder_var.get() and os.path.exists(out_path):
            self.log("\nOpening results folder...")
            try:
                os.startfile(out_path)
            except Exception as e:
                self.log(f"⚠️ Error opening folder: {str(e)}")
        
        # Update UI
        self.update_progress(100, "Complete!")
        self.processing = False
        self.update_button_states(False)
        
        # Show completion message with backup information
        backup_msg = f"Backup created: {summary['backed_up']} files" if self.backup_var.get() else "Backup: Disabled"
        messagebox.showinfo("Processing Complete", 
                           f"Successfully processed {summary['merged']} files.\n"
                           f"Failed: {summary['failed']}\n"
                           f"{backup_msg}\n\n"
                           f"Results saved to: {os.path.join(results_dir, f'{base}-merged')}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernHKXShift(root)
    root.mainloop()