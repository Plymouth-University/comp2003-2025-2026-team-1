#!/usr/bin/env python3
"""
Co OPERATION: MultiTurn - Level Editor
RPG Maker style: Grid editing + GridObjects editing (separate panels)
Integrated with game's Steam folder structure
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import re
import copy

# PIL/Pillow for image handling
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# pygltflib for GLB texture extraction (optional dependency)
# Allows extracting albedo textures from .glb 3D models for grid display
try:
    from pygltflib import GLTF2
    from pygltflib.utils import ImageFormat
    PYGLTFLIB_AVAILABLE = True
except ImportError:
    PYGLTFLIB_AVAILABLE = False


# ============================================
# Custom YAML Handling for Game Format
# ============================================

# Force YAML to output strings as literal block scalars (| style)
# This matches the game's expected YAML format for grid data
class LiteralString(str):
    """Helper class to force YAML to output a string as literal block scalar"""
    pass


def literal_string_representer(dumper, data):
    """Custom representer to output strings as literal block scalars"""
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')


yaml.add_representer(LiteralString, literal_string_representer)


class TaggedObject(dict):
    """Dict subclass that remembers its YAML tag"""
    def __init__(self, *args, **kwargs):
        tag = kwargs.pop('_tag', None)
        super().__init__(*args, **kwargs)
        self._tag = tag


def tagged_object_representer(dumper, data):
    """Represent TaggedObject with its original tag"""
    tag = getattr(data, '_tag', None)
    if tag:
        return dumper.represent_mapping(f'!{tag}', dict(data))
    return dumper.represent_mapping('tag:yaml.org,2002:map', dict(data))


yaml.add_representer(TaggedObject, tagged_object_representer)


# Custom YAML tag constructors (matching game documentation)
def animation_constructor(loader, node):
    """Constructor for !Animation tag"""
    if isinstance(node, yaml.MappingNode):
        data = loader.construct_mapping(node)
        return TaggedObject(data, _tag='Animation')
    return loader.construct_scalar(node)


def glb_animation_constructor(loader, node):
    """Constructor for !GLBAnimation tag"""
    data = loader.construct_mapping(node)
    return TaggedObject(data, _tag='GLBAnimation')


def spine_animation_constructor(loader, node):
    """Constructor for !SpineAnimation tag"""
    data = loader.construct_mapping(node)
    return TaggedObject(data, _tag='SpineAnimation')


def mesh_deform_animation_constructor(loader, node):
    """Constructor for !MeshDeformAnimation tag (correct spelling)"""
    data = loader.construct_mapping(node)
    return TaggedObject(data, _tag='MeshDeformAnimation')


def tween_animation_constructor(loader, node):
    """Constructor for !TweenAnimation tag"""
    data = loader.construct_mapping(node)
    return TaggedObject(data, _tag='TweenAnimation')


def unity_animator_constructor(loader, node):
    """Constructor for !UnityAnimator tag"""
    data = loader.construct_mapping(node)
    return TaggedObject(data, _tag='UnityAnimator')


# Register all custom tag constructors with both SafeLoader and Loader
for _loader in (yaml.SafeLoader, yaml.Loader):
    yaml.add_constructor('!Animation', animation_constructor, Loader=_loader)
    yaml.add_constructor('!GLBAnimation', glb_animation_constructor, Loader=_loader)
    yaml.add_constructor('!SpineAnimation', spine_animation_constructor, Loader=_loader)
    yaml.add_constructor('!MeshDeformAnimation', mesh_deform_animation_constructor, Loader=_loader)
    yaml.add_constructor('!TweenAnimation', tween_animation_constructor, Loader=_loader)
    yaml.add_constructor('!UnityAnimator', unity_animator_constructor, Loader=_loader)
    
    # Generic multi-constructor to handle ANY other custom tags
    def generic_tag_handler(loader, suffix, node):
        """Handle any custom tag with '!' prefix"""
        if isinstance(node, yaml.MappingNode):
            data = loader.construct_mapping(node)
            return TaggedObject(data, _tag=suffix)
        elif isinstance(node, yaml.SequenceNode):
            data = loader.construct_sequence(node)
            return TaggedObject({'_data': data, '_tag': suffix})
        else:
            data = loader.construct_scalar(node)
            return TaggedObject({'_value': data, '_tag': suffix})
    
    yaml.add_multi_constructor('!', generic_tag_handler, Loader=_loader)


# ============================================
# YAML Include Resolution
# ============================================

def load_yaml_file(filepath: str) -> Tuple[Dict, str]:
    """Load a single YAML file and return parsed data plus any errors"""
    try:
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        return data if data else {}, None
    except Exception as e:
        return None, str(e)


def resolve_includes(main_filepath: str, loaded_files: Set[str] = None) -> Tuple[Dict, List[str], List[str]]:
    """
    Recursively resolve YAML include directives.
    Returns: (merged_data, warnings, errors)
    """
    if loaded_files is None:
        loaded_files = set()
    
    main_path = os.path.abspath(main_filepath)
    if main_path in loaded_files:
        return {}, ['Circular include detected: {main_filepath}'], []
    loaded_files.add(main_path)
    
    data, error = load_yaml_file(main_filepath)
    if error:
        return {}, [], [f"Error loading {main_filepath}: {error}"]
    
    warnings = []
    errors = []
    
    # Get the base directory for resolving relative includes
    base_dir = os.path.dirname(main_path)
    
    # Process includes
    if 'include' in data:
        includes = data['include']
        if not isinstance(includes, list):
            includes = [includes]
        
        # Store includes for later (we'll preserve them in the data)
        # But merge the included data now
        merged_includes = {}
        
        for include_file in includes:
            include_path = os.path.join(base_dir, include_file)
            if not os.path.exists(include_path):
                warnings.append(f"Include file not found: {include_file}")
                continue
            
            included_data, inc_warnings, inc_errors = resolve_includes(include_path, loaded_files)
            warnings.extend(inc_warnings)
            errors.extend(inc_errors)
            
            if included_data:
                # Merge included data (but don't overwrite main file's keys)
                for key, value in included_data.items():
                    if key == 'include':
                        # Don't merge includes recursively at this level
                        continue
                    if key not in merged_includes:
                        merged_includes[key] = value
        
        # Now merge: included data first, then main data on top
        merged_data = merged_includes.copy()
        merged_data.update(data)
        
        # Store original includes for preservation
        merged_data['_original_includes'] = includes
        
        return merged_data, warnings, errors
    
    return data, warnings, errors


# ============================================
# GridObject Dialog (RPG Maker Style Event Editor)
# ============================================

class GridObjectDialog:
    """Dialog for editing GridObjects for a single cell (like RPG Maker event editor)"""
    def __init__(self, parent, cell_code, grid_objects, object_definitions, game_assets_path=None):
        self.parent = parent
        self.cell_code = cell_code
        self.grid_objects = grid_objects
        self.object_definitions = object_definitions
        self.game_assets_path = game_assets_path
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"GridObjects Editor - Cell {cell_code}")
        self.dialog.geometry("650x550")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.load_current_objects()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header
        header = ttk.Label(main_frame, text=f"Editing objects for cell: {self.cell_code}", 
                          font=("Arial", 12, "bold"))
        header.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        # Objects list with scrollbar
        list_frame = ttk.LabelFrame(main_frame, text="GridObjects (ordered list - drag to reorder)", padding="5")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)
        
        info_text = ("Each item: object code (e.g. 'F', 'B') references objectDefinitions, "
                    "or inline dict with {id: XXX} or {mapObject: Custom}")
        ttk.Label(list_frame, text=info_text, wraplength=550).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Listbox with scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)
        
        self.objects_listbox = tk.Listbox(list_container, height=15, selectmode=tk.SINGLE)
        self.objects_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.objects_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.objects_listbox.config(yscrollcommand=scrollbar.set)
        
        # Buttons frame
        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=2, column=0, pady=(5, 0))
        
        ttk.Button(btn_frame, text="Add Object Code", command=self.add_object_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Add Inline", command=self.add_inline_def).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Edit Selected", command=self.edit_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove", command=self.remove_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="↑ Up", command=self.move_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="↓ Down", command=self.move_down).pack(side=tk.LEFT, padx=2)
        
        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=2, column=0, pady=(10, 0))
        
        ttk.Button(bottom_frame, text="OK", command=self.save_and_close, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Cancel", command=self.cancel, width=15).pack(side=tk.LEFT, padx=5)
        
    def load_current_objects(self):
        self.objects_listbox.delete(0, tk.END)
        objects = self.grid_objects.get(self.cell_code, [])
        for i, obj in enumerate(objects):
            if isinstance(obj, str):
                # Check if it's in object_definitions
                in_defs = "✓" if obj in self.object_definitions else "?"
                self.objects_listbox.insert(tk.END, f"{i+1}. [Code] {obj} {in_defs}")
            elif isinstance(obj, dict):
                if 'id' in obj:
                    self.objects_listbox.insert(tk.END, f"{i+1}. [Inline] id={obj['id']}, dir={obj.get('dir', 'South')}")
                elif 'mapObject' in obj:
                    self.objects_listbox.insert(tk.END, f"{i+1}. [Inline] mapObject={obj['mapObject']}")
                else:
                    self.objects_listbox.insert(tk.END, f"{i+1}. [Inline] {str(obj)[:50]}")
                    
    def get_selected_index(self):
        selection = self.objects_listbox.curselection()
        return selection[0] if selection else None
        
    def add_object_code(self):
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Add Object Code")
        dialog.geometry("350x200")
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Object Code (must exist in objectDefinitions):").pack(pady=10)
        
        code_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=code_var, width=20)
        entry.pack(pady=5)
        entry.focus()
        
        # Show available codes
        if self.object_definitions:
            ttk.Label(dialog, text="Available codes:").pack(pady=(10, 0))
            codes_text = ", ".join(list(self.object_definitions.keys())[:15])
            ttk.Label(dialog, text=codes_text, wraplength=300).pack(pady=5)
        
        def add():
            code = code_var.get().strip()
            if not code:
                messagebox.showwarning("Empty", "Please enter a code")
                return
            if code not in self.object_definitions and not code.startswith('__'):
                if not messagebox.askyesno("Warning", f"Code '{code}' not found in objectDefinitions.\nAdd anyway?"):
                    return
            current = self.grid_objects.get(self.cell_code, [])
            current.append(code)
            self.grid_objects[self.cell_code] = current
            self.load_current_objects()
            dialog.destroy()
                
        ttk.Button(dialog, text="Add", command=add).pack(pady=10)
        dialog.bind('<Return>', lambda e: add())
        
    def add_inline_def(self):
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Add Inline Object Definition")
        dialog.geometry("450x350")
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Inline Definition (YAML format):").pack(pady=5, anchor=tk.W)
        ttk.Label(dialog, text="Examples:").pack(anchor=tk.W)
        ttk.Label(dialog, text='  {id: B, dir: East}', foreground="blue").pack(anchor=tk.W)
        ttk.Label(dialog, text='  {mapObject: Custom, dir: South}', foreground="blue").pack(anchor=tk.W)
        
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        text_widget = tk.Text(text_frame, height=8, width=50)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert('1.0', '{id: MyObject, dir: South}')
        
        def add():
            try:
                text = text_widget.get('1.0', tk.END).strip()
                # Parse as YAML
                parsed = yaml.safe_load(text)
                if isinstance(parsed, dict):
                    current = self.grid_objects.get(self.cell_code, [])
                    current.append(parsed)
                    self.grid_objects[self.cell_code] = current
                    self.load_current_objects()
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Please enter a valid YAML dictionary")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid YAML: {e}")
                
        ttk.Button(dialog, text="Add", command=add).pack(pady=5)
        
    def edit_selected(self):
        idx = self.get_selected_index()
        if idx is None:
            messagebox.showwarning("No Selection", "Select an object to edit")
            return
        
        current = self.grid_objects.get(self.cell_code, [])
        obj = current[idx]
        
        if isinstance(obj, str):
            # Edit as string
            dialog = tk.Toplevel(self.dialog)
            dialog.title("Edit Object Code")
            dialog.geometry("300x150")
            dialog.transient(self.dialog)
            dialog.grab_set()
            
            ttk.Label(dialog, text="Object Code:").pack(pady=10)
            code_var = tk.StringVar(value=obj)
            entry = ttk.Entry(dialog, textvariable=code_var, width=20)
            entry.pack(pady=5)
            entry.focus()
            
            def save():
                new_code = code_var.get().strip()
                if new_code:
                    current[idx] = new_code
                    self.grid_objects[self.cell_code] = current
                    self.load_current_objects()
                dialog.destroy()
                
            ttk.Button(dialog, text="Save", command=save).pack(pady=10)
        else:
            # Edit as YAML dict
            dialog = tk.Toplevel(self.dialog)
            dialog.title("Edit Inline Definition")
            dialog.geometry("450x350")
            dialog.transient(self.dialog)
            dialog.grab_set()
            
            text_frame = ttk.Frame(dialog)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            text_widget = tk.Text(text_frame, height=8, width=50)
            text_widget.pack(fill=tk.BOTH, expand=True)
            text_widget.insert('1.0', yaml.dump(obj, default_flow_style=False))
            
            def save():
                try:
                    text = text_widget.get('1.0', tk.END).strip()
                    parsed = yaml.safe_load(text)
                    if isinstance(parsed, dict):
                        current[idx] = parsed
                        self.grid_objects[self.cell_code] = current
                        self.load_current_objects()
                        dialog.destroy()
                    else:
                        messagebox.showerror("Error", "Please enter a valid YAML dictionary")
                except Exception as e:
                    messagebox.showerror("Error", f"Invalid YAML: {e}")
                    
            ttk.Button(dialog, text="Save", command=save).pack(pady=5)
        
    def remove_selected(self):
        idx = self.get_selected_index()
        if idx is None:
            return
        current = self.grid_objects.get(self.cell_code, [])
        current.pop(idx)
        self.grid_objects[self.cell_code] = current
        self.load_current_objects()
        
    def move_up(self):
        idx = self.get_selected_index()
        if idx is None or idx == 0:
            return
        current = self.grid_objects.get(self.cell_code, [])
        current[idx], current[idx-1] = current[idx-1], current[idx]
        self.grid_objects[self.cell_code] = current
        self.load_current_objects()
        self.objects_listbox.selection_set(idx-1)
        
    def move_down(self):
        idx = self.get_selected_index()
        if idx is None or idx == len(self.grid_objects.get(self.cell_code, [])) - 1:
            return
        current = self.grid_objects.get(self.cell_code, [])
        current[idx], current[idx+1] = current[idx+1], current[idx]
        self.grid_objects[self.cell_code] = current
        self.load_current_objects()
        self.objects_listbox.selection_set(idx+1)
        
    def save_and_close(self):
        self.result = self.grid_objects
        self.dialog.destroy()
        
    def cancel(self):
        self.dialog.destroy()


class GameFolderBrowser:
    """Handles browsing and integrating with the game's folder structure"""
    def __init__(self, parent, editor):
        self.parent = parent
        self.editor = editor
        self.game_path = tk.StringVar()
        
    def find_game_path(self):
        """Try to auto-find the game installation path"""
        possible_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\Co OPERATION MultiTurn",
            r"C:\Program Files\Steam\steamapps\common\Co OPERATION MultiTurn",
            os.path.expanduser(r"~\Games\Co OPERATION MultiTurn"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.game_path.set(path)
                return path
                
        return None
        
    def browse_for_game(self):
        """Open dialog to browse for game folder"""
        initial = self.game_path.get() or "C:\\"
        path = filedialog.askdirectory(
            title="Select Co OPERATION: MultiTurn Game Folder",
            initialdir=initial
        )
        if path:
            self.game_path.set(path)
            self.load_game_structure(path)
            return path
        return None
        
    def load_game_structure(self, game_path):
        """Load the game's folder structure"""
        # Try to find StreamingAssets
        possible_assets = [
            os.path.join(game_path, "Co OPERATION MultiTurn_Data", "StreamingAssets"),
            os.path.join(game_path, "StreamingAssets"),
            os.path.join(game_path, "Data", "StreamingAssets"),
        ]
        
        streaming_assets = None
        for path in possible_assets:
            if os.path.exists(path):
                streaming_assets = path
                break
                
        if streaming_assets:
            self.editor.streaming_assets_path = streaming_assets
            self.editor.load_assets_from_folder(streaming_assets)
            return True
        else:
            messagebox.showwarning("Folder Not Found", 
                f"Could not find StreamingAssets in:\n{game_path}\n\n"
                "Please ensure you selected the correct game folder.")
            return False


# ============================================
# Main Level Editor Class
# ============================================

class LevelEditor:
    """Main Level Editor application"""
    def __init__(self, root):
        self.root = root
        self.root.title("Co OPERATION: MultiTurn - Level Editor")
        self.root.geometry("1300x850")
        
        # Data
        self.grid_data = []  # 2D list of cell codes
        self.grid_objects = {}  # code -> list of objects
        self.object_definitions = {}  # code -> definition
        self.current_file = None
        self.streaming_assets_path = None
        self.available_assets = {'3d': [], '2d': [], 'sounds': []}
        
        # Shared definitions file path
        self.shared_defs_path = tk.StringVar()  # Path to shared YAML file
        self.shared_data = {}  # Cached shared definitions data
        
        # Full YAML data preservation
        self.full_yaml_data = {}  # Store full YAML to preserve all sections
        self.loaded_includes = []  # Track loaded include files
        
        # Grid state
        self.grid_rows = 15
        self.grid_cols = 12
        self.cell_size = 42
        self.selected_cell = None
        
        # Image display support
        self.cell_images = {}  # (row, col) -> canvas image id
        self.image_cache = {}  # (filepath, size) -> PhotoImage
        self._image_refs = []  # Prevent garbage collection
        self.extracted_textures = {}  # glb_path -> extracted_png_path
        
        # Pan state for middle-click panning
        self.pan_start = None  # (x, y) canvas coordinates
        
        # Selection highlight
        self.selection_id = None  # Canvas item id for selection rectangle
        
        # Painting state (RPG Maker-style)
        self.paint_code = None  # Last applied grid code for painting
        self.painting = False  # Whether right-click painting is active
        self.erasing = False  # Whether Ctrl+Right-click eraser mode is active
        
        # Undo/Redo system
        self.undo_stack = []  # History of previous states
        self.redo_stack = []  # States that were undone
        self.max_undo_history = 50  # Maximum undo history size
        
        # Camera settings (from YAML cameraSettings)
        self.camera_settings = {}  # Stores cameraSettings dict
        
        # Setup UI
        self.setup_menu()
        self.setup_ui()
        self.setup_grid()
        
        # Initialize with empty grid
        self.init_empty_grid()
        
        # Auto-detect Mod folder (contains Art/ and Levels/)
        self.root.after(100, self.auto_detect_mod_folder)
        
        # Bind Ctrl+S to save
        self.root.bind('<Control-s>', lambda e: self.save_yaml())
        self.root.bind('<Control-S>', lambda e: self.save_yaml())
        
        # Bind Ctrl+Z (Undo) and Ctrl+Shift+Z (Redo)
        self.root.bind_all('<Control-z>', self.undo)
        self.root.bind_all('<Control-Shift-Z>', self.redo)
        
        # Prompt on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Level", command=self.new_level)
        file_menu.add_command(label="Open YAML...", command=self.open_yaml)
        file_menu.add_command(label="Save YAML", command=self.save_yaml)
        file_menu.add_command(label="Save YAML As...", command=self.save_yaml_as)
        file_menu.add_separator()
        file_menu.add_command(label="Set Mod Folder...", command=self.set_mod_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        self.edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=self.edit_menu)
        
        # Undo/Redo at top of Edit menu
        self.edit_menu.add_command(label="Undo\tCtrl+Z", command=self.undo, state='disabled')
        self.edit_menu.add_command(label="Redo\tCtrl+Shift+Z", command=self.redo, state='disabled')
        self.edit_menu.add_separator()
        
        self.edit_menu.add_command(label="Grid Size...", command=self.change_grid_size)
        self.edit_menu.add_command(label="Camera Settings...", command=self.edit_camera_settings)
        self.edit_menu.add_command(label="Edit Object Definitions...", command=self.edit_object_definitions)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", command=self.zoom_out)
        
    def setup_ui(self):
        # Main container with panes
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Grid editor
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=3)
        
        # Grid controls
        controls_frame = ttk.Frame(left_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(controls_frame, text="Grid Code:").pack(side=tk.LEFT, padx=(0, 5))
        self.grid_code_var = tk.StringVar(value="01")
        code_entry = ttk.Entry(controls_frame, textvariable=self.grid_code_var, width=10)
        code_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Paint indicator
        self.paint_label = ttk.Label(controls_frame, text="Paint: None")
        self.paint_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Apply to Selected", 
                  command=self.apply_code_to_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Clear Cell", 
                  command=self.clear_selected_cell).pack(side=tk.LEFT, padx=5)
        
        # Quick palette
        ttk.Separator(controls_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Label(controls_frame, text="Quick:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.palette_var = tk.StringVar()
        self.palette_combo = ttk.Combobox(controls_frame, textvariable=self.palette_var, width=25, state="readonly")
        self.update_palette_values()  # Populate from object_definitions
        self.palette_combo.pack(side=tk.LEFT, padx=5)
        self.palette_combo.bind('<<ComboboxSelected>>', self.on_palette_select)
        
        # Grid canvas with scrollbars
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.grid_canvas = tk.Canvas(canvas_frame, 
                                     xscrollcommand=self.h_scrollbar.set,
                                     yscrollcommand=self.v_scrollbar.set,
                                     bg='white', highlightthickness=0)
        self.grid_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.h_scrollbar.config(command=self.grid_canvas.xview)
        self.v_scrollbar.config(command=self.grid_canvas.yview)
        
        self.grid_canvas.bind("<Button-1>", self.on_grid_click)
        self.grid_canvas.bind("<Motion>", self.on_grid_hover)
        self.grid_canvas.bind("<Leave>", self.on_grid_leave)
        
        # Scroll wheel zoom
        self.grid_canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.grid_canvas.bind("<Button-4>", lambda e: self.on_mouse_wheel(e, 1))  # Linux scroll up
        self.grid_canvas.bind("<Button-5>", lambda e: self.on_mouse_wheel(e, -1))  # Linux scroll down
        
        # Middle-click pan
        self.grid_canvas.bind("<Button-2>", self.on_middle_press)
        self.grid_canvas.bind("<B2-Motion>", self.on_middle_drag)
        self.grid_canvas.bind("<ButtonRelease-2>", self.on_middle_release)
        
        # Right-click paint (RPG Maker-style)
        self.grid_canvas.bind("<Button-3>", self.on_paint_click)
        self.grid_canvas.bind("<B3-Motion>", self.on_paint_drag)
        self.grid_canvas.bind("<ButtonRelease-3>", self.on_paint_release)
        
        # Right panel - Cell details (like RPG Maker event panel)
        right_frame = ttk.PanedWindow(main_container, orient=tk.VERTICAL)
        main_container.add(right_frame, weight=1)
        
        # Cell info frame
        cell_info_frame = ttk.LabelFrame(right_frame, text="Cell Details", padding="10")
        right_frame.add(cell_info_frame, weight=1)
        
        self.cell_info_text = tk.Text(cell_info_frame, height=10, wrap=tk.WORD)
        self.cell_info_text.pack(fill=tk.BOTH, expand=True)
        self.cell_info_text.insert('1.0', "Click a cell to see details")
        self.cell_info_text.config(state=tk.DISABLED)
        
        # GridObjects frame
        objects_frame = ttk.LabelFrame(right_frame, text="GridObjects Editor", padding="10")
        right_frame.add(objects_frame, weight=2)
        
        ttk.Label(objects_frame, text="Select a cell and click 'Edit Objects' to add/edit objects").pack(pady=5)
        
        self.edit_objects_btn = ttk.Button(objects_frame, text="Edit Objects for Selected Cell", 
                                          command=self.edit_cell_objects, state=tk.DISABLED)
        self.edit_objects_btn.pack(pady=5)
        
        # Quick object codes list
        ttk.Label(objects_frame, text="Object codes in this cell:").pack(anchor=tk.W, pady=(10, 5))
        
        # Object listbox with scrollbar
        obj_list_frame = ttk.Frame(objects_frame)
        obj_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.cell_objects_listbox = tk.Listbox(obj_list_frame, height=8)
        self.cell_objects_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        obj_scrollbar = ttk.Scrollbar(obj_list_frame, orient=tk.VERTICAL, command=self.cell_objects_listbox.yview)
        obj_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cell_objects_listbox.config(yscrollcommand=obj_scrollbar.set)
        
        # Object definitions quick view
        defs_frame = ttk.LabelFrame(right_frame, text="Object Definitions", padding="10")
        right_frame.add(defs_frame, weight=1)
        
        self.defs_text = tk.Text(defs_frame, height=6, wrap=tk.WORD)
        self.defs_text.pack(fill=tk.BOTH, expand=True)
        self.update_defs_display()
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def setup_grid(self):
        self.grid_canvas.delete("all")
        self.cell_rects = {}
        
        width = self.grid_cols * self.cell_size
        height = self.grid_rows * self.cell_size
        
        self.grid_canvas.config(scrollregion=(0, 0, width, height))
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                rect_id = self.grid_canvas.create_rectangle(x1, y1, x2, y2, 
                                                           fill='white', outline='gray', 
                                                           activefill='lightblue',
                                                           tags=(f"cell_{row}_{col}",))
                text_id = self.grid_canvas.create_text(x1 + self.cell_size/2, y1 + self.cell_size/2,
                                                      text="", font=("Courier", 7),
                                                      tags=(f"text_{row}_{col}",))
                
                self.cell_rects[(row, col)] = (rect_id, text_id)
                    
    def init_empty_grid(self):
        self.grid_data = [['__' for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
        self.update_grid_display()
        
    def update_grid_display(self):
        """Redraw the entire grid display.
        
        Clears all canvas items and redraws every cell.
        Called after major changes like loading a new level or applying code.
        """
        # Clear old images from canvas
        for cell, img_id in list(self.cell_images.items()):
            self.grid_canvas.delete(img_id)
            del self.cell_images[cell]
        
        # Also clear selection highlight (will be redrawn if cell is selected)
        if self.selection_id:
            self.grid_canvas.delete(self.selection_id)
            self.selection_id = None
        
        # Iterate through all grid cells and redraw them
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                # Get the grid code for this cell (or '__' if out of bounds)
                if row < len(self.grid_data) and col < len(self.grid_data[row]):
                    code = self.grid_data[row][col]
                else:
                    code = '__'
                    
                # Get the canvas item ids for this cell
                rect_id, text_id = self.cell_rects.get((row, col), (None, None))
                
                if rect_id:
                    # Color based on content (visual feedback for different cell types)
                    if code == '__':
                        color = '#f5f5f5'  # Light gray for empty
                    elif code in self.object_definitions:
                        color = '#c8e6c9'  # Green tint for defined objects
                    elif code in self.grid_objects and self.grid_objects[code]:
                        color = '#bbdefb'  # Blue tint for cells with objects
                    else:
                        color = '#fff9c4'  # Yellow tint for undefined
                    
                    # Update rectangle color on canvas
                    self.grid_canvas.itemconfig(rect_id, fill=color)
                    
                    # Remove old text (we're using images now, text is obsolete)
                    if text_id:
                        self.grid_canvas.delete(text_id)
                        # Update the rects dict to remove text_id
                        if (row, col) in self.cell_rects:
                            self.cell_rects[(row, col)] = (self.cell_rects[(row, col)][0], None)
                    
                    # Try to display texture (2D or extracted from GLB)
                    if code != '__' and PIL_AVAILABLE:
                        texture_path = self.get_cell_texture(row, col)
                        if texture_path:
                            # Check if it's already a full path (GLB-extracted temp file)
                            if os.path.isabs(texture_path) and os.path.exists(texture_path):
                                self.display_cell_image(row, col, texture_path, color)
                            else:
                                # It's a relative path, resolve it from Art/2D folder
                                full_path = self.resolve_art_path(texture_path, '2D')
                                if full_path and os.path.exists(full_path):
                                    self.display_cell_image(row, col, full_path, color)
                        # If no texture found, keep colored rectangle (Q2)
                        # This implements "colored rectangle only" fallback
                    
    def on_grid_click(self, event):
        """Handle mouse click on the grid - supports painting and erasing"""
        canvas_x = self.grid_canvas.canvasx(event.x)
        canvas_y = self.grid_canvas.canvasy(event.y)
        
        col = int(canvas_x // self.cell_size)
        row = int(canvas_y // self.cell_size)
        
        if 0 <= row < self.grid_rows and 0 <= col < self.grid_cols:
            self.selected_cell = (row, col)
            self.update_cell_info(row, col)
            self.edit_objects_btn.config(state=tk.NORMAL)
            self.status_bar.config(text=f"Selected cell: Row {row}, Col {col} (Code: {self.grid_data[row][col]})")
            self.draw_selection_highlight(row, col)
            
    def draw_selection_highlight(self, row, col):
        """Draw a highlight border around the selected cell"""
        # Remove previous selection highlight
        if self.selection_id:
            self.grid_canvas.delete(self.selection_id)
        
        x1 = col * self.cell_size
        y1 = row * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        
        # Draw selection border (thick yellow dashed line)
        self.selection_id = self.grid_canvas.create_rectangle(x1, y1, x2, y2,
                                        outline="yellow", width=3,
                                        dash=(5, 3), tags="selection")
        # Lift to top so it's visible over other objects
        self.grid_canvas.lift(self.selection_id)
            
    def on_grid_hover(self, event):
        canvas_x = self.grid_canvas.canvasx(event.x)
        canvas_y = self.grid_canvas.canvasy(event.y)
        
        col = int(canvas_x // self.cell_size)
        row = int(canvas_y // self.cell_size)
        
        if 0 <= row < self.grid_rows and 0 <= col < self.grid_cols:
            code = self.grid_data[row][col]
            obj_count = len(self.grid_objects.get(code, []))
            self.status_bar.config(text=f"Hover: Row {row}, Col {col} - Code: {code} ({obj_count} objects)")
            
    def on_grid_leave(self, event):
        if self.selected_cell:
            row, col = self.selected_cell
            self.status_bar.config(text=f"Selected cell: Row {row}, Col {col} (Code: {self.grid_data[row][col]})")
        else:
            self.status_bar.config(text="Ready")
            
    def on_mouse_wheel(self, event, fake_delta=None):
        """Handle scroll wheel zoom"""
        if fake_delta is not None:
            delta = fake_delta
        else:
            delta = event.delta // 120  # Windows: +/-120 per notch
        
        if delta > 0:
            self.zoom_in()
        elif delta < 0:
            self.zoom_out()
            
    def on_middle_press(self, event):
        """Start middle-click pan using tkinter's scan methods for smooth panning"""
        self.grid_canvas.config(cursor="fleur")
        # Use scan_mark to set the reference point for draging
        self.grid_canvas.scan_mark(event.x, event.y)
        
    def on_middle_drag(self, event):
        """Handle middle-click pan drag - smooth panning using scan_dragto"""
        # scan_dragto is designed for this - gain=1 means 1:1 movement
        self.grid_canvas.scan_dragto(event.x, event.y, gain=2)
            
    def on_middle_release(self, event):
        """End middle-click pan"""
        self.grid_canvas.config(cursor="")
        self.pan_start = None
            
    def on_paint_click(self, event):
        """Start right-click painting (paint with paint_code or erase with Ctrl+Right-click)
        
        RPG Maker-style tile painting:
        - Right-click: Paint the current paint_code to the clicked cell
        - Ctrl+Right-click: Erase the cell (set to '__')
        - Drag while holding: Paint/erase multiple cells
        """
        # Check if Ctrl key is held - eraser mode works even without paint_code
        ctrl_held = event.state & 0x0004
        
        if ctrl_held:
            # Eraser mode - no paint_code needed
            # Push undo state only at start of paint action (not on drag)
            if not self.painting:
                self._push_undo_state()
            self.painting = True
            self.erasing = True
            self.grid_canvas.config(cursor="X_cursor")  # Eraser cursor
            self._do_paint(event)
            return
        
        # Normal right-click - requires paint_code
        if not self.paint_code:
            self.status_bar.config(text="No paint code set. Apply a code to a cell first.")
            return
        
        # Set painting state to active
        # Push undo state only at start of paint action (not on drag)
        if not self.painting:
            self._push_undo_state()
        self.painting = True
        self.erasing = False
        self.grid_canvas.config(cursor="pencil")  # Paintbrush cursor
        
        # Perform the initial paint/erase action on the clicked cell
        self._do_paint(event)
            
    def on_paint_drag(self, event):
        """Continue painting/erasing while right-click is held and dragged.
        Called on <B3-Motion> event."""
        if self.painting:
            self._do_paint(event)
            
    def on_paint_release(self, event):
        """End right-click painting/erasing.
        Resets painting state and restores normal cursor."""
        self.painting = False
        self.erasing = False
        self.grid_canvas.config(cursor="")  # Restore default cursor
            
    def _do_paint(self, event):
        """Apply paint_code to cell at event position, or erase if Ctrl is held.
        
        Called by:
        - on_paint_click(): Initial right-click
        - on_paint_drag(): Drag while holding right-click
        """
        if not self.painting:
            return
        
        # Check if Ctrl is held (for eraser mode) - bitwise AND with state mask
        ctrl_held = (event.state & 0x0004) or self.erasing
        
        # Convert screen coordinates to canvas coordinates
        canvas_x = self.grid_canvas.canvasx(event.x)
        canvas_y = self.grid_canvas.canvasy(event.y)
        
        # Calculate which grid cell the mouse is over
        col = int(canvas_x // self.cell_size)
        row = int(canvas_y // self.cell_size)
        
        # Validate cell is within grid bounds
        if 0 <= row < self.grid_rows and 0 <= col < self.grid_cols:
            if ctrl_held:
                # Ctrl+Right-click: Erase cell (set to '__' empty)
                self.grid_data[row][col] = '__'
                action_text = "Erased"
            elif self.paint_code:
                # Normal right-click: Paint the cell with paint_code
                self.grid_data[row][col] = self.paint_code
                action_text = f"Painted '{self.paint_code}'"
            else:
                return
            
            # Redraw just this cell (efficient - only updates one cell)
            self.populate_cell(row, col)
            
            # Update selection info panel if this is the currently selected cell
            if self.selected_cell == (row, col):
                self.update_cell_info(row, col)
            
            self.status_bar.config(text=f"{action_text} at Row {row}, Col {col}")
            
    def populate_cell(self, row, col):
        """Redraw a single cell (for efficient painting).
        
        Called by _do_paint() when right-click painting/erasing cells.
        Only redraws the specified cell instead of the entire grid.
        """
        # Validate cell coordinates
        if row >= len(self.grid_data) or col >= len(self.grid_data[row]):
            return
        
        # Get the grid code for this cell
        code = self.grid_data[row][col]
        
        # Get the rectangle id for this cell from the cell_rects dict
        rect_id, text_id = self.cell_rects.get((row, col), (None, None))
        if not rect_id:
            return  # Cell not found in canvas
        
        # Color based on content (visual feedback for different cell types)
        if code == '__':
            color = '#f5f5f5'  # Light gray for empty
        elif code in self.object_definitions:
            color = '#c8e6c9'  # Green tint for defined objects
        elif code in self.grid_objects and self.grid_objects[code]:
            color = '#bbdefb'  # Blue tint for cells with objects
        else:
            color = '#fff9c4'  # Yellow tint for undefined
        
        # Update rectangle color on canvas
        self.grid_canvas.itemconfig(rect_id, fill=color)
        
        # Remove old text (we're using images now, text is obsolete)
        if text_id:
            self.grid_canvas.delete(text_id)
            # Update the rects dict to remove text_id
            if (row, col) in self.cell_rects:
                self.cell_rects[(row, col)] = (self.cell_rects[(row, col)][0], None)
        
        # Remove old image if exists (to prevent overlapping images)
        if (row, col) in self.cell_images:
            self.grid_canvas.delete(self.cell_images[(row, col)])
            del self.cell_images[(row, col)]
        
        # Display texture if available (2D or extracted from GLB)
        if code != '__' and PIL_AVAILABLE:
            texture_path = self.get_cell_texture(row, col)
            if texture_path:
                # Check if it's already a full path (GLB-extracted temp file)
                if os.path.isabs(texture_path) and os.path.exists(texture_path):
                    self.display_cell_image(row, col, texture_path, color)
                else:
                    # It's a relative path, resolve it from Art/2D folder
                    full_path = self.resolve_art_path(texture_path, '2D')
                    if full_path and os.path.exists(full_path):
                        self.display_cell_image(row, col, full_path, color)
            
    def update_palette_values(self):
        """Update Quick Palette dropdown with codes used in the grid only.
        Only shows codes that are actually placed in grid cells."""
        values = ['__ (empty)']
        
        # Get all codes actually in grid_data (placed on the grid)
        codes_in_grid = set()
        for row in self.grid_data:
            for cell in row:
                if cell and cell != '__':
                    codes_in_grid.add(cell)
        
        # Get shared definitions to filter them out
        shared_defs = getattr(self, 'shared_data', {}).get('objectDefinitions', {})
        
        # Add codes from grid_data with descriptions if available
        for code in sorted(codes_in_grid):
            # Skip shared definitions (they're available via include)
            if code in shared_defs:
                continue
            
            # Add description if code is in object_definitions
            if code in self.object_definitions:
                defn = self.object_definitions[code]
                if isinstance(defn, str):
                    values.append(f"{code} ({defn})")
                elif isinstance(defn, dict):
                    desc = defn.get('mapObject', defn.get('id', '?'))
                    if len(desc) > 20:
                        desc = desc[:17] + '...'
                    values.append(f"{code} ({desc})")
            else:
                # No definition found, just show the code
                values.append(f"{code}")
        
        self.palette_combo['values'] = sorted(set(values))
    
    def on_palette_select(self, event):
        value = self.palette_var.get()
        if value:
            # Extract code (before the space and description)
            # Format is "code (description)" or just "code"
            if ' (' in value:
                code = value.split(' (')[0].strip()
            else:
                code = value.strip()
            self.grid_code_var.set(code)
            
            # Set as paint code for right-click painting (RPG Maker-style)
            self.paint_code = code
            self.paint_label.config(text=f"Paint: {code}")
            self.status_bar.config(text=f"Paint code set: {code} (right-click to paint)")
            
    def update_cell_info(self, row, col):
        code = self.grid_data[row][col]
        objects = self.grid_objects.get(code, [])
        
        self.cell_info_text.config(state=tk.NORMAL)
        self.cell_info_text.delete('1.0', tk.END)
        self.cell_info_text.insert('1.0', f"Cell: Row {row}, Col {col}\n")
        self.cell_info_text.insert(tk.END, f"Grid Code: {code}\n")
        
        if code in self.object_definitions:
            self.cell_info_text.insert(tk.END, f"✓ Code defined in objectDefinitions\n")
        elif code != '__':
            self.cell_info_text.insert(tk.END, f"⚠ Code NOT in objectDefinitions\n")
            
        self.cell_info_text.insert(tk.END, f"\nGridObjects ({len(objects)} items):\n")
        
        for i, obj in enumerate(objects):
            if isinstance(obj, str):
                self.cell_info_text.insert(tk.END, f"  {i+1}. [Code] {obj}\n")
            elif isinstance(obj, dict):
                self.cell_info_text.insert(tk.END, f"  {i+1}. [Inline] {str(obj)[:50]}\n")
                
        self.cell_info_text.config(state=tk.DISABLED)
        
        # Update objects listbox
        self.cell_objects_listbox.delete(0, tk.END)
        for obj in objects:
            if isinstance(obj, str):
                self.cell_objects_listbox.insert(tk.END, f"{obj}")
            elif isinstance(obj, dict):
                short = f"Inline: {str(obj)[:30]}"
                self.cell_objects_listbox.insert(tk.END, short)
                
    def apply_code_to_selected(self):
        """Apply the entered grid code to the currently selected cell.
        Also sets this code as the 'paint code' for RPG Maker-style right-click painting."""
        if not self.selected_cell:
            messagebox.showwarning("No Selection", "Please select a cell first")
            return
        
        # Push current state to undo stack before making changes
        self._push_undo_state()
        
        row, col = self.selected_cell
        new_code = self.grid_code_var.get().strip()
        
        if not new_code:
            messagebox.showwarning("Invalid Code", "Please enter a grid code")
            return
        
        # Apply the code to the grid data
        self.grid_data[row][col] = new_code
        self.update_grid_display()
        self.update_cell_info(row, col)
        
        # Set as paint code for right-click painting (RPG Maker-style)
        # This allows user to then right-click other cells to "paint" them with the same code
        self.paint_code = new_code
        self.paint_label.config(text=f"Paint: {new_code}")
        self.status_bar.config(text=f"Paint code set: {new_code} (right-click to paint)")
        
        # Update Quick Palette to include the newly applied code in real-time
        self.update_palette_values()
        
    def clear_selected_cell(self):
        if not self.selected_cell:
            return
        
        # Push current state to undo stack before clearing
        self._push_undo_state()
        
        row, col = self.selected_cell
        self.grid_data[row][col] = '__'
        self.update_grid_display()
        self.update_cell_info(row, col)
        
    def edit_cell_objects(self):
        if not self.selected_cell:
            return
        
        row, col = self.selected_cell
        code = self.grid_data[row][col]
        
        if code == '__':
            messagebox.showinfo("Empty Cell", "This cell is empty (__). Apply a grid code first.")
            return
        
        # Push current state to undo stack before editing objects
        self._push_undo_state()
        
        # Ensure grid_objects entry exists
        if code not in self.grid_objects:
            self.grid_objects[code] = []
        
        dialog = GridObjectDialog(self.root, code, self.grid_objects, self.object_definitions, 
                                 self.streaming_assets_path)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.grid_objects = dialog.result
            self.update_cell_info(row, col)
            self.update_grid_display()
            
    def update_defs_display(self):
        self.defs_text.delete('1.0', tk.END)
        if self.object_definitions:
            for code, defn in list(self.object_definitions.items())[:10]:
                if isinstance(defn, str):
                    self.defs_text.insert(tk.END, f"{code} → {defn}\n")
                else:
                    map_obj = defn.get('mapObject', defn.get('id', '?'))
                    self.defs_text.insert(tk.END, f"{code} → {map_obj}\n")
            if len(self.object_definitions) > 10:
                self.defs_text.insert(tk.END, f"... and {len(self.object_definitions)-10} more\n")
        else:
            self.defs_text.insert('1.0', "No object definitions yet.\nUse Edit → Edit Object Definitions...")
        
        # Also update Quick Palette
        self.update_palette_values()
            
    def zoom_in(self):
        self.cell_size = min(80, self.cell_size + 5)
        self.setup_grid()
        self.update_grid_display()
        
    def zoom_out(self):
        self.cell_size = max(20, self.cell_size - 5)
        self.setup_grid()
        self.update_grid_display()
        
    def set_shared_defs(self):
        """Open file dialog to select shared definitions file"""
        filename = filedialog.askopenfilename(
            title="Select Shared Definitions YAML (e.g., from your level pack)",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        )
        
        if filename:
            self.load_shared_defs(filename)
            
    def load_shared_defs(self, filepath):
        """Load shared definitions from the specified file.
        
        Shared definitions allow multiple levels to reference the same object
        definitions without duplicating them in each level file.
        Uses include directive when saving.
        """
        try:
            data, error = load_yaml_file(filepath)
            
            if error:
                messagebox.showerror("Error Loading Shared Definitions", error)
                return False
            
            if not data:
                messagebox.showwarning("Empty File", "The shared definitions file is empty")
                return False
            
            self.shared_defs_path.set(filepath)
            self.shared_data = data
            
            # Merge shared object definitions
            if 'objectDefinitions' in data:
                # Merge: shared defs first, then current (current takes precedence)
                merged = data['objectDefinitions'].copy()
                merged.update(self.object_definitions)
                self.object_definitions = merged
                self.update_defs_display()
            
            # Merge shared grid objects
            if 'gridObjects' in data:
                merged = data['gridObjects'].copy()
                merged.update(self.grid_objects)
                self.grid_objects = merged
                
            self.status_bar.config(text=f"Loaded shared definitions: {os.path.basename(filepath)}")
            messagebox.showinfo("Shared Definitions Loaded", 
                f"Loaded shared definitions from:\n{filepath}\n\n"
                f"Object definitions: {len(data.get('objectDefinitions', {}))}\n"
                f"Grid objects: {len(data.get('gridObjects', {}))}")
            
            # Update display
            self.update_grid_display()
            return True
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return False
            
    def new_level(self):
        if messagebox.askyesno("New Level", "Create a new level? Unsaved changes will be lost."):
            self.grid_data = [['__' for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
            self.grid_objects = {}
            self.object_definitions = {}
            self.full_yaml_data = {}
            self.loaded_includes = []
            self.current_file = None
            
            # Clear undo/redo history for new level
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.update_undo_redo_menu()
            
            self.update_grid_display()
            self.update_defs_display()
            self.status_bar.config(text="New level created")
             
    def open_yaml(self):
        filename = filedialog.askopenfilename(
            title="Open Level YAML",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        )
        if filename:
            self.load_yaml(filename)
             
    def load_yaml(self, filename):
        """Load a level from YAML file, resolving includes if present.
        
        Uses resolve_includes() to handle files with include directives.
        Merges shared definitions if a shared defs file is set.
        Updates grid display, definitions, and objects after loading.
        """
        try:
            # Use the include-aware loader
            merged_data, warnings, errors = resolve_includes(filename)
            
            # Show warnings/errors
            if warnings:
                for w in warnings:
                    self.status_bar.config(text=f"Warning: {w}")
                messagebox.showwarning("Load Warnings", "\n".join(warnings))
            
            if errors:
                messagebox.showerror("Load Errors", "\n".join(errors))
                return
            
            if not merged_data:
                messagebox.showerror("Error", "Empty or invalid YAML file")
                return
            
            # Merge with shared definitions if set (use resolve_includes to get ALL shared data)
            if self.shared_defs_path.get() and os.path.exists(self.shared_defs_path.get()):
                shared_data, shared_warnings, shared_errors = resolve_includes(self.shared_defs_path.get())
                warnings.extend(shared_warnings)
                errors.extend(shared_errors)
                if shared_data:
                    # Merge ALL shared data (objectDefinitions, gridObjects, objectAnimations, music, sounds, etc.)
                    # Shared data first, then file data takes precedence
                    for key, value in shared_data.items():
                        if key == 'include' or key == '_original_includes':
                            continue  # Don't merge include directives
                        if key not in merged_data:
                            merged_data[key] = value
                        elif isinstance(value, dict) and isinstance(merged_data[key], dict):
                            # Merge dictionaries (e.g., objectDefinitions, gridObjects)
                            merged_dict = value.copy()
                            merged_dict.update(merged_data[key])
                            merged_data[key] = merged_dict
                    warnings.append(f"Merged with shared definitions: {os.path.basename(self.shared_defs_path.get())}")
            
            # Store full YAML data for preservation
            self.full_yaml_data = merged_data
            self.current_file = filename
            
            # Track includes
            self.loaded_includes = merged_data.get('_original_includes', [])
            if self.loaded_includes:
                inc_msg = f"Loaded with includes: {', '.join(self.loaded_includes)}"
                self.status_bar.config(text=inc_msg)
            
            # Load grid - handle multiline string with sections
            if 'grid' in merged_data:
                grid_str = merged_data['grid']
                lines = [line.strip() for line in str(grid_str).strip().split('\n') if line.strip()]
                
                self.grid_data = []
                max_cols = 0
                
                for line in lines:
                    # Parse comma-separated values
                    cells = [c.strip() for c in line.split(',') if c.strip()]
                    # Remove trailing empty strings from trailing commas
                    while cells and cells[-1] == '':
                        cells.pop()
                    if cells:
                        self.grid_data.append(cells)
                        max_cols = max(max_cols, len(cells))
                
                self.grid_rows = len(self.grid_data)
                self.grid_cols = max_cols
                
                # Pad all rows to grid_cols with '__' to prevent IndexError on hover
                for i, row in enumerate(self.grid_data):
                    if len(row) < self.grid_cols:
                        self.grid_data[i] = row + ['__'] * (self.grid_cols - len(row))
            
            # Load objectDefinitions (merge from includes)
            if 'objectDefinitions' in merged_data and merged_data['objectDefinitions']:
                self.object_definitions = merged_data['objectDefinitions']
                
            # Load other metadata
            if 'sceneName' in merged_data:
                self.scene_name = merged_data['sceneName']
            if 'fileProperties' in merged_data and 'creatorName' in merged_data['fileProperties']:
                self.creator_name = merged_data['fileProperties']['creatorName']
            
            # Load cameraSettings
            if 'cameraSettings' in merged_data:
                self.camera_settings = merged_data['cameraSettings']
            else:
                self.camera_settings = {}
                    
            self.setup_grid()
            self.update_grid_display()
            self.update_defs_display()
            self.update_palette_values()
            
            # Clear undo/redo history and set initial state for loaded file
            self.undo_stack.clear()
            self.redo_stack.clear()
            # Save initial state so "undo" after load reverts to empty (or previous)
            self._push_undo_state()
            self.update_undo_redo_menu()
            
            self.status_bar.config(text=f"Loaded: {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Error Loading YAML", str(e))
            import traceback
            traceback.print_exc()
            
    # ============================================
    # Undo/Redo System
    # ============================================
    # Implements state-snapshot undo/redo with keyboard shortcuts:
    # - Ctrl+Z: Undo last action
    # - Ctrl+Shift+Z: Redo last undone action
    # - Menu: Edit > Undo/Redo (enabled/disabled based on stack state)
    #
    # State snapshots capture: grid_data, grid_objects, object_definitions
    # Maximum history: 50 states (configurable via max_undo_history)
    # ============================================
    
    def _get_current_state(self):
        """Capture current editor state for undo/redo.
        
        Returns a deep copy of:
        - grid_data: 2D list of cell codes
        - grid_objects: dict mapping codes to object lists
        - object_definitions: dict mapping codes to definitions
        
        Uses deepcopy to ensure complete isolation between states.
        """
        return {
            'grid_data': copy.deepcopy(self.grid_data),
            'grid_objects': copy.deepcopy(self.grid_objects),
            'object_definitions': copy.deepcopy(self.object_definitions)
        }
    
    def _push_undo_state(self):
        """Save current state to undo stack before making changes.
        
        Called before any action that modifies level data.
        Clears redo stack since new actions invalidate redo history.
        Trims history to max_undo_history (removes oldest entry).
        """
        state = self._get_current_state()
        self.undo_stack.append(state)
        # Trim history if over limit (remove oldest entry)
        if len(self.undo_stack) > self.max_undo_history:
            self.undo_stack.pop(0)
        # Clear redo stack - new actions invalidate redo
        self.redo_stack.clear()
        self.update_undo_redo_menu()
    
    def _restore_state(self, state):
        """Restore editor to a previously saved state.
        
        Restores grid_data, grid_objects, and object_definitions
        from the saved state dictionary, then refreshes all UI elements.
        """
        self.grid_data = state['grid_data']
        self.grid_objects = state['grid_objects']
        self.object_definitions = state['object_definitions']
        # Refresh all UI elements to reflect restored state
        self.update_grid_display()
        if self.selected_cell:
            row, col = self.selected_cell
            self.update_cell_info(row, col)
        self.update_defs_display()
        self.update_palette_values()
    
    def undo(self, event=None):
        """Undo the last action (Ctrl+Z or Edit > Undo).
        
        Pops the last state from undo_stack and restores it.
        The current state is saved to redo_stack for possible redo.
        Shows "Nothing to undo" if undo_stack is empty.
        """
        if not self.undo_stack:
            self.status_bar.config(text="Nothing to undo")
            return
        
        # Save current state to redo stack
        current_state = self._get_current_state()
        self.redo_stack.append(current_state)
        
        # Restore previous state
        previous_state = self.undo_stack.pop()
        self._restore_state(previous_state)
        
        self.status_bar.config(text="Undo successful")
        self.update_undo_redo_menu()
    
    def redo(self, event=None):
        """Redo the last undone action (Ctrl+Shift+Z or Edit > Redo).
        
        Pops the last state from redo_stack and restores it.
        The current state is saved to undo_stack for possible undo.
        Shows "Nothing to redo" if redo_stack is empty.
        """
        if not self.redo_stack:
            self.status_bar.config(text="Nothing to redo")
            return
        
        # Save current state to undo stack
        current_state = self._get_current_state()
        self.undo_stack.append(current_state)
        
        # Restore redo state
        redo_state = self.redo_stack.pop()
        self._restore_state(redo_state)
        
        self.status_bar.config(text="Redo successful")
        self.update_undo_redo_menu()
    
    def update_undo_redo_menu(self):
        """Enable/disable Undo/Redo menu items based on stack state.
        
        Updates the Edit menu to show Undo/Redo as:
        - Enabled (normal): when there's something to undo/redo
        - Disabled (grayed out): when the respective stack is empty
        
        Menu indices: 0=Undo, 1=Redo (set in setup_menu)
        """
        if hasattr(self, 'edit_menu'):
            # Undo menu item (index 0)
            if self.undo_stack:
                self.edit_menu.entryconfig(0, state='normal')
            else:
                self.edit_menu.entryconfig(0, state='disabled')
            
            # Redo menu item (index 1)
            if self.redo_stack:
                self.edit_menu.entryconfig(1, state='normal')
            else:
                self.edit_menu.entryconfig(1, state='disabled')
    
    def save_yaml(self):
        if not self.current_file:
            self.save_yaml_as()
            return
            
        self.write_yaml(self.current_file)
        
    def save_yaml_as(self):
        filename = filedialog.asksaveasfilename(
            title="Save Level YAML",
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if filename:
            self.current_file = filename
            self.write_yaml(filename)
            
    def on_closing(self):
        """Prompt user to save/discard/cancel when closing"""
        if self.current_file or self.grid_objects or self.object_definitions:
            # Check if there are unsaved changes (simple check)
            has_content = (len(self.grid_objects) > 0 or 
                           len(self.object_definitions) > 0 or 
                           self.camera_settings)
            
            if has_content:
                response = messagebox.askyesnocancel(
                    "Save Changes?",
                    "Do you want to save changes before exiting?",
                    default=messagebox.YES
                )
                
                if response is True:  # Yes - save and close
                    if self.current_file:
                        self.save_yaml()
                    else:
                        self.save_yaml_as()
                    # Only destroy if save was successful (no return on error)
                    self.root.destroy()
                elif response is False:  # No - discard and close
                    self.root.destroy()
                # Cancel - do nothing, don't close
                return
        
        # No changes or user chose to close
        self.root.destroy()
            
    def write_yaml(self, filename):
        """Save level data to YAML file in game-compatible format.
        
        Outputs minimal YAML containing only essential keys:
        - fileProperties, sceneName, cameraSettings (required by game parser)
        - grid (as literal block scalar)
        - gridObjects (only for codes actually used in grid)
        - objectDefinitions (always present, even if empty)
        - include (when using shared definition files)
        """
        try:
            # Build grid string - match original format with sections
            grid_lines = []
            for i, row in enumerate(self.grid_data):
                padded_row = row + ['__'] * (self.grid_cols - len(row))
                line = ','.join(padded_row) + ','
                grid_lines.append('  ' + line)
                if (i + 1) % 8 == 0 and (i + 1) < len(self.grid_data):
                    grid_lines.append('')
            grid_str = '\n'.join(grid_lines)
            
            # Build output - ONLY include necessary keys for a runnable level
            output = {}
            
            # Required keys (game parser expects these)
            creator = getattr(self, 'creator_name', 'Level Editor User')
            output['fileProperties'] = {'creatorName': creator}
            output['sceneName'] = getattr(self, 'scene_name', 'OriginalWorld')
            output['grid'] = LiteralString(grid_str)
            
            # objectDefinitions - ALWAYS include (game parser requires it)
            output['objectDefinitions'] = {}
            
            # gridObjects - only save non-empty AND used in grid
            if self.grid_objects:
                used_codes = set()
                for row in self.grid_data:
                    for cell in row:
                        if cell and cell != '__':
                            used_codes.add(cell)
                
                filtered = {}
                for k, v in self.grid_objects.items():
                    if v and k in used_codes:
                        filtered[k] = v
                if filtered:
                    output['gridObjects'] = filtered
            
            # cameraSettings
            if hasattr(self, 'camera_settings') and self.camera_settings:
                output['cameraSettings'] = self.camera_settings
            
            # include directive (when using shared files)
            if self.loaded_includes:
                output['include'] = self.loaded_includes
            
            # Write to file
            with open(filename, 'w') as f:
                yaml.dump(output, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
                
            self.status_bar.config(text=f"Saved: {os.path.basename(filename)}")
            messagebox.showinfo("Saved", f"Level saved to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error Saving", str(e))
            import traceback
            traceback.print_exc()
            
    def set_game_folder(self):
        browser = GameFolderBrowser(self.root, self)
        browser.browse_for_game_folder()
        
    def change_grid_size(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Change Grid Size")
        dialog.geometry("250x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Rows:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        rows_var = tk.IntVar(value=self.grid_rows)
        ttk.Entry(dialog, textvariable=rows_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="Columns:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        cols_var = tk.IntVar(value=self.grid_cols)
        ttk.Entry(dialog, textvariable=cols_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        def apply():
            new_rows = rows_var.get()
            new_cols = cols_var.get()
            if new_rows > 0 and new_cols > 0:
                # Expand grid data if needed
                while len(self.grid_data) < new_rows:
                    self.grid_data.append(['__' for _ in range(self.grid_cols)])
                while len(self.grid_data) > new_rows:
                    self.grid_data.pop()
                    
                for row in self.grid_data:
                    while len(row) < new_cols:
                        row.append('__')
                    while len(row) > new_cols:
                        row.pop()
                        
                self.grid_rows = new_rows
                self.grid_cols = new_cols
                self.setup_grid()
                self.update_grid_display()
                dialog.destroy()
                
        ttk.Button(dialog, text="Apply", command=apply).grid(row=2, column=0, columnspan=2, pady=10)
        
    def edit_camera_settings(self):
        """Open dialog to edit cameraSettings (type, staticSettings, position, target)"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Camera Settings")
        dialog.geometry("400x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main = ttk.Frame(dialog, padding="10")
        main.pack(fill=tk.BOTH, expand=True)
        
        # Get current settings or use defaults
        settings = self.camera_settings if self.camera_settings else {}
        cam_type = settings.get('type', 'Static')
        static = settings.get('staticSettings', {})
        pos = settings.get('position', {})
        target = settings.get('target', {})
        
        # Type selector
        ttk.Label(main, text="Camera Type:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        type_var = tk.StringVar(value=cam_type)
        type_combo = ttk.Combobox(main, textvariable=type_var, state="readonly", width=15)
        type_combo['values'] = ['Static', 'Dynamic']
        type_combo.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
        
        # Static Settings frame
        static_frame = ttk.LabelFrame(main, text="Static Settings", padding="5")
        static_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(static_frame, text="distanceMultiplier:").grid(row=0, column=0, sticky=tk.W, pady=2)
        dist_var = tk.DoubleVar(value=static.get('distanceMultiplier', 2.0))
        ttk.Entry(static_frame, textvariable=dist_var, width=10).grid(row=0, column=1, pady=2)
        
        ttk.Label(static_frame, text="heightMultiplier:").grid(row=1, column=0, sticky=tk.W, pady=2)
        height_var = tk.DoubleVar(value=static.get('heightMultiplier', 0.73))
        ttk.Entry(static_frame, textvariable=height_var, width=10).grid(row=1, column=1, pady=2)
        
        ttk.Label(static_frame, text="FOV:").grid(row=2, column=0, sticky=tk.W, pady=2)
        fov_var = tk.DoubleVar(value=static.get('FOV', 15))
        ttk.Entry(static_frame, textvariable=fov_var, width=10).grid(row=2, column=1, pady=2)
        
        ttk.Label(static_frame, text="editorCameraSizeMultiplier:").grid(row=3, column=0, sticky=tk.W, pady=2)
        size_var = tk.DoubleVar(value=static.get('editorCameraSizeMultiplier', 0.55))
        ttk.Entry(static_frame, textvariable=size_var, width=10).grid(row=3, column=1, pady=2)
        
        ttk.Label(static_frame, text="editorCameraHeightMultiplier:").grid(row=4, column=0, sticky=tk.W, pady=2)
        cam_height_var = tk.DoubleVar(value=static.get('editorCameraHeightMultiplier', 1.02))
        ttk.Entry(static_frame, textvariable=cam_height_var, width=10).grid(row=4, column=1, pady=2)
        
        # Reset Static to defaults
        def reset_static():
            dist_var.set(2.0)
            height_var.set(0.73)
            fov_var.set(15)
            size_var.set(0.55)
            cam_height_var.set(1.02)
        
        ttk.Button(static_frame, text="Reset to Default", command=reset_static).grid(row=5, column=0, columnspan=2, pady=(10, 2))
        
        # Position frame (for Dynamic)
        pos_frame = ttk.LabelFrame(main, text="Position (Dynamic)", padding="5")
        pos_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        offset = pos.get('offset', {})
        ttk.Label(pos_frame, text="offset x:").grid(row=0, column=0, sticky=tk.W, pady=2)
        pos_x_var = tk.DoubleVar(value=offset.get('x', -45))
        ttk.Entry(pos_frame, textvariable=pos_x_var, width=10).grid(row=0, column=1, pady=2)
        
        ttk.Label(pos_frame, text="offset y:").grid(row=1, column=0, sticky=tk.W, pady=2)
        pos_y_var = tk.DoubleVar(value=offset.get('y', 32))
        ttk.Entry(pos_frame, textvariable=pos_y_var, width=10).grid(row=1, column=1, pady=2)
        
        ttk.Label(pos_frame, text="offset z:").grid(row=2, column=0, sticky=tk.W, pady=2)
        pos_z_var = tk.DoubleVar(value=offset.get('z', -45))
        ttk.Entry(pos_frame, textvariable=pos_z_var, width=10).grid(row=2, column=1, pady=2)
        
        # Reset Position to defaults
        def reset_position():
            pos_x_var.set(-45)
            pos_y_var.set(32)
            pos_z_var.set(-45)
        
        ttk.Button(pos_frame, text="Reset to Default", command=reset_position).grid(row=3, column=0, columnspan=2, pady=(10, 2))
        
        # Target frame (for Dynamic)
        target_frame = ttk.LabelFrame(main, text="Target (Dynamic)", padding="5")
        target_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(target_frame, text="screenTargetX:").grid(row=0, column=0, sticky=tk.W, pady=2)
        target_x_var = tk.DoubleVar(value=target.get('screenTargetX', 0.5))
        ttk.Entry(target_frame, textvariable=target_x_var, width=10).grid(row=0, column=1, pady=2)
        
        ttk.Label(target_frame, text="screenTargetY:").grid(row=1, column=0, sticky=tk.W, pady=2)
        target_y_var = tk.DoubleVar(value=target.get('screenTargetY', 0.5))
        ttk.Entry(target_frame, textvariable=target_y_var, width=10).grid(row=1, column=1, pady=2)
        
        view_offset = target.get('viewTargetOffset', {})
        ttk.Label(target_frame, text="viewTargetOffset x:").grid(row=2, column=0, sticky=tk.W, pady=2)
        view_x_var = tk.DoubleVar(value=view_offset.get('x', 0))
        ttk.Entry(target_frame, textvariable=view_x_var, width=10).grid(row=2, column=1, pady=2)
        
        ttk.Label(target_frame, text="viewTargetOffset y:").grid(row=3, column=0, sticky=tk.W, pady=2)
        view_y_var = tk.DoubleVar(value=view_offset.get('y', 0))
        ttk.Entry(target_frame, textvariable=view_y_var, width=10).grid(row=3, column=1, pady=2)
        
        ttk.Label(target_frame, text="viewTargetOffset z:").grid(row=4, column=0, sticky=tk.W, pady=2)
        view_z_var = tk.DoubleVar(value=view_offset.get('z', 0))
        ttk.Entry(target_frame, textvariable=view_z_var, width=10).grid(row=4, column=1, pady=2)
        
        # Reset Target to defaults
        def reset_target():
            target_x_var.set(0.5)
            target_y_var.set(0.5)
            view_x_var.set(0)
            view_y_var.set(0)
            view_z_var.set(0)
        
        ttk.Button(target_frame, text="Reset to Default", command=reset_target).grid(row=5, column=0, columnspan=2, pady=(10, 2))
        
        # Function to show/hide frames based on type
        def update_visibility(*args):
            if type_var.get() == 'Static':
                static_frame.grid()
                pos_frame.grid_remove()
                target_frame.grid_remove()
            else:
                static_frame.grid_remove()
                pos_frame.grid()
                target_frame.grid()
        
        type_combo.bind('<<ComboboxSelected>>', update_visibility)
        update_visibility()  # Initial state
        
        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        def reset_all():
            """Reset all camera settings to defaults"""
            type_var.set('Static')
            dist_var.set(2.0)
            height_var.set(0.73)
            fov_var.set(15)
            size_var.set(0.55)
            cam_height_var.set(1.02)
            pos_x_var.set(-45)
            pos_y_var.set(32)
            pos_z_var.set(-45)
            target_x_var.set(0.5)
            target_y_var.set(0.5)
            view_x_var.set(0)
            view_y_var.set(0)
            view_z_var.set(0)
            update_visibility()  # Update frame visibility
            self.status_bar.config(text="Reset all to defaults")
        
        def save():
            new_settings = {'type': type_var.get()}
            
            if type_var.get() == 'Static':
                new_settings['staticSettings'] = {
                    'distanceMultiplier': dist_var.get(),
                    'heightMultiplier': height_var.get(),
                    'FOV': fov_var.get(),
                    'editorCameraSizeMultiplier': size_var.get(),
                    'editorCameraHeightMultiplier': cam_height_var.get()
                }
            else:
                new_settings['position'] = {
                    'offset': {'x': pos_x_var.get(), 'y': pos_y_var.get(), 'z': pos_z_var.get()}
                }
                new_settings['target'] = {
                    'screenTargetX': target_x_var.get(),
                    'screenTargetY': target_y_var.get(),
                    'viewTargetOffset': {'x': view_x_var.get(), 'y': view_y_var.get(), 'z': view_z_var.get()}
                }
            
            self.camera_settings = new_settings
            dialog.destroy()
            self.status_bar.config(text="Camera settings updated")
        
        ttk.Button(btn_frame, text="OK", command=save).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Reset All to Defaults", command=reset_all).grid(row=0, column=2, padx=5)
    
    def edit_object_definitions(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Object Definitions")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        
        # Main frame
        main = ttk.Frame(dialog, padding="10")
        main.pack(fill=tk.BOTH, expand=True)
        
        # List of existing definitions
        list_frame = ttk.LabelFrame(main, text="Object Definitions", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview for definitions
        columns = ('Code', 'Type', 'Details')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        tree.heading('Code', text='Code')
        tree.heading('Type', text='Type')
        tree.heading('Details', text='Details')
        tree.column('Code', width=100)
        tree.column('Type', width=150)
        tree.column('Details', width=400)
        
        tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.config(yscrollcommand=scrollbar.set)
        
        # Populate tree
        for code, defn in self.object_definitions.items():
            if isinstance(defn, str):
                tree.insert('', 'end', values=(code, 'Short Form', defn))
            elif isinstance(defn, dict):
                map_obj = defn.get('mapObject', defn.get('id', '?'))
                tags = ', '.join(defn.get('tags', [])[:3])
                tree.insert('', 'end', values=(code, 'Long Form', f"{map_obj} | {tags}"))
                
        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X)
        
        def add_definition():
            add_dialog = tk.Toplevel(dialog)
            add_dialog.title("Add Object Definition")
            add_dialog.geometry("450x400")
            add_dialog.transient(dialog)
            add_dialog.grab_set()
            
            ttk.Label(add_dialog, text="Code (e.g. 'F', 'B1', 'wall_e'):").pack(pady=5)
            code_var = tk.StringVar()
            ttk.Entry(add_dialog, textvariable=code_var, width=20).pack()
            
            ttk.Label(add_dialog, text="Type:").pack(pady=(10, 5))
            type_var = tk.StringVar(value="short")
            ttk.Radiobutton(add_dialog, text="Short Form (just reference)", 
                           variable=type_var, value="short").pack(anchor=tk.W, padx=20)
            ttk.Radiobutton(add_dialog, text="Long Form (full definition)", 
                           variable=type_var, value="long").pack(anchor=tk.W, padx=20)
            
            # Long form fields
            long_frame = ttk.Frame(add_dialog)
            long_frame.pack(fill=tk.X, pady=5, padx=20)
            
            ttk.Label(long_frame, text="mapObject or id:").pack(side=tk.LEFT, padx=(0, 5))
            map_obj_var = tk.StringVar()
            ttk.Entry(long_frame, textvariable=map_obj_var, width=20).pack(side=tk.LEFT)
            
            ttk.Label(add_dialog, text="Direction:").pack(pady=(5, 0), padx=20, anchor=tk.W)
            dir_var = tk.StringVar(value="South")
            dir_combo = ttk.Combobox(add_dialog, textvariable=dir_var, width=15, state="readonly")
            dir_combo['values'] = ['North', 'East', 'South', 'West']
            dir_combo.pack(padx=20, anchor=tk.W)
            
            def save():
                code = code_var.get().strip()
                if not code:
                    messagebox.showwarning("Missing Code", "Please enter a code")
                    return
                
                # Push undo state before modifying definitions
                self._push_undo_state()
                
                if type_var.get() == "short":
                    self.object_definitions[code] = map_obj_var.get() or code
                else:
                    self.object_definitions[code] = {
                        'mapObject': map_obj_var.get() or 'Custom',
                        'dir': dir_var.get()
                    }
                
                # Refresh tree
                tree.delete(*tree.get_children())
                for c, d in self.object_definitions.items():
                    if isinstance(d, str):
                        tree.insert('', 'end', values=(c, 'Short Form', d))
                    elif isinstance(d, dict):
                        map_o = d.get('mapObject', d.get('id', '?'))
                        tags = ', '.join(d.get('tags', [])[:3])
                        tree.insert('', 'end', values=(c, 'Long Form', f"{map_o} | {tags}"))
                       
                self.update_defs_display()
                self.update_grid_display()
                add_dialog.destroy()
                
            ttk.Button(add_dialog, text="Save", command=save).pack(pady=10)
            
        ttk.Button(btn_frame, text="Add", command=add_definition).pack(side=tk.LEFT, padx=5)
        
        def remove_selected():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                code = item['values'][0]
                if messagebox.askyesno("Remove", f"Remove definition '{code}'?"):
                    # Push undo state before modifying definitions
                    self._push_undo_state()
                    
                    del self.object_definitions[code]
                    tree.delete(selection[0])
                    self.update_defs_display()
                    self.update_grid_display()
                    
        ttk.Button(btn_frame, text="Remove Selected", command=remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
    def load_assets_from_folder(self, streaming_assets_path):
        """Load available assets from the game's StreamingAssets folder"""
        try:
            # Look for 3D models
            art_3d = os.path.join(streaming_assets_path, "Art", "3D")
            if os.path.exists(art_3d):
                self.available_assets['3d'] = self.find_files_recursive(art_3d, ['.glb', '.gltf'])
                
            # Look for 2D textures
            art_2d = os.path.join(streaming_assets_path, "Art", "2D")
            if os.path.exists(art_2d):
                self.available_assets['2d'] = self.find_files_recursive(art_2d, ['.png', '.jpg', '.jpeg'])
                
            # Look for sounds
            sounds = os.path.join(streaming_assets_path, "Sounds")
            if os.path.exists(sounds):
                self.available_assets['sounds'] = self.find_files_recursive(sounds, ['.mp3', '.ogg', '.wav'])
                
            self.status_bar.config(text=f"Loaded {len(self.available_assets['3d'])} 3D models, "
                                       f"{len(self.available_assets['2d'])} 2D textures, "
                                       f"{len(self.available_assets['sounds'])} sounds")
        except Exception as e:
            print(f"Error loading assets: {e}")
            
    def find_files_recursive(self, folder, extensions):
        """Find all files with given extensions in folder and subfolders"""
        found = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    rel_path = os.path.relpath(os.path.join(root, file), folder)
                    found.append(rel_path)
        return sorted(found)

    def auto_detect_mod_folder(self):
        """Auto-detect Mod folder (contains Art/ and Levels/)"""
        # Try to auto-find from common game installation paths
        possible_bases = [
            r"C:\Program Files (x86)\Steam\steamapps\common\Co OPERATION MultiTurn",
            r"C:\Program Files\Steam\steamapps\common\Co OPERATION MultiTurn",
            os.path.expanduser(r"~\Games\Co OPERATION MultiTurn"),
        ]
        
        for base in possible_bases:
            if os.path.exists(base):
                # Check if it has Art/ and Levels/ or StreamingAssets
                streaming = os.path.join(base, "StreamingAssets")
                if os.path.exists(streaming):
                    self.streaming_assets_path = streaming
                    self.status_bar.config(text=f"Auto-detected: {streaming}")
                    self.load_assets_from_folder(streaming)
                    self.auto_load_shared_defs()
                    return
        
        # Not found, prompt user
        result = messagebox.askyesno(
            "Mod Folder",
            "No Mod folder detected. This should contain Art/ and Levels/ folders.\n\n"
            "Would you like to set it manually?"
        )
        if result:
            self.set_mod_folder()
        else:
            self.status_bar.config(text="No Mod folder set - textures and shared definitions will not load")
    
    def set_mod_folder(self):
        """Set the Mod folder (contains Art/ and Levels/)"""
        folder = filedialog.askdirectory(
            title="Select Mod Folder (contains Art/ and Levels/)",
            initialdir="C:\\"
        )
        if folder:
            # Check if it's StreamingAssets or has it inside
            streaming = None
            if "StreamingAssets" in folder:
                streaming = folder
            else:
                test_path = os.path.join(folder, "StreamingAssets")
                if os.path.exists(test_path):
                    streaming = test_path
                else:
                    # Assume folder is the game root
                    for sub in ["StreamingAssets", "Co OPERATION MultiTurn_Data"]:
                        test = os.path.join(folder, sub)
                        if os.path.exists(test):
                            streaming = test
                            break
            
            if streaming:
                self.streaming_assets_path = streaming
                self.status_bar.config(text=f"Mod folder set: {streaming}")
                if not PYGLTFLIB_AVAILABLE:
                    self.status_bar.config(text="Note: pygltflib not installed. 3D textures won't show. Run: py -m pip install pygltflib")
                self.load_assets_from_folder(streaming)
                self.auto_load_shared_defs()
            else:
                messagebox.showwarning("Invalid Folder", 
                    "Could not find StreamingAssets in the selected folder.\n"
                    "Please select the game installation folder or the StreamingAssets folder.")
    
    def auto_load_shared_defs(self):
        """Auto-find and load shared definitions from Mod folder"""
        if not self.streaming_assets_path:
            return
        
        # Look for common shared YAML files
        possible_names = ['LevelsShared.yaml', 'SharedDefinitions.yaml', 'Shared.yaml']
        search_dirs = [
            self.streaming_assets_path,
            os.path.join(self.streaming_assets_path, "Levels"),
            os.path.join(self.streaming_assets_path, "Definitions"),
        ]
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
            for fname in possible_names:
                fpath = os.path.join(search_dir, fname)
                if os.path.exists(fpath):
                    self.load_shared_defs(fpath)
                    return
        
    def set_game_folder(self):
        """Set game folder (now delegates to set_mod_folder)"""
        self.set_mod_folder()

    def get_cell_texture(self, row, col):
        """
        Get texture filepath for a grid cell.
        Returns filepath or None if no texture found.
        
        Priority:
        1. Check art2d textures (2D) for the cell's objects
        2. Fallback: Extract albedo texture from art3d GLB models (requires pygltflib)
        """
        if row >= len(self.grid_data) or col >= len(self.grid_data[row]):
            return None
            
        code = self.grid_data[row][col]
        if code == '__':
            return None
        
        # Get objects for this cell
        objects = self.grid_objects.get(code, [])
        
        # Check each object for displayable art
        for obj_ref in objects:
            # Handle string references (look up in object_definitions)
            if isinstance(obj_ref, str):
                obj = self.object_definitions.get(obj_ref)
            else:
                obj = obj_ref
                
            if not isinstance(obj, dict):
                continue
                
            # Priority 1: Check art2d first (2D textures)
            if 'art2d' in obj and obj['art2d']:
                art = obj['art2d'][0]  # Use first art2d
                if isinstance(art, dict):
                    if 'texture' in art:
                        return art['texture']
                    elif 'textures' in art and art['textures']:
                        return art['textures'][0]  # Use first texture
                    
            # Priority 2: GLB texture extraction fallback (requires pygltflib)
            if 'art3d' in obj and obj['art3d'] and PYGLTFLIB_AVAILABLE:
                art = obj['art3d'][0]
                if isinstance(art, dict) and 'model' in art:
                    glb_path = self.resolve_art_path(art['model'], '3D')
                    if glb_path and os.path.exists(glb_path):
                        texture = self.extract_glb_texture(glb_path)
                        if texture:
                            return texture  # Returns temp PNG path
        
        return None
    
    def resolve_art_path(self, texture_path, art_type='2D'):
        """Resolve relative art path to full path"""
        if not self.streaming_assets_path:
            return None
            
        # Try multiple possible locations
        possible_bases = [
            os.path.join(self.streaming_assets_path, "Art", art_type.upper()),
            os.path.join(self.streaming_assets_path, "Art", art_type.lower())
        ]
        
        for base in possible_bases:
            full_path = os.path.join(base, texture_path)
            if os.path.exists(full_path):
                return full_path
        
        # Try direct path relative to streaming_assets_path
        full_path = os.path.join(self.streaming_assets_path, texture_path)
        if os.path.exists(full_path):
            return full_path
            
        return None
            
        # Try multiple possible locations
        possible_bases = [
            os.path.join(self.streaming_assets_path, "Art", art_type.upper()),
            os.path.join(self.streaming_assets_path, "Art", art_type.lower())
        ]
        
        for base in possible_bases:
            full_path = os.path.join(base, texture_path)
            if os.path.exists(full_path):
                return full_path
        
        # Try direct path relative to streaming_assets_path
        full_path = os.path.join(self.streaming_assets_path, texture_path)
        if os.path.exists(full_path):
            return full_path
            
        return None
    
    def extract_glb_texture(self, glb_path):
        """
        Extract albedo (base color) texture from a GLB file.
        
        Follows the glTF material chain to find the correct albedo texture:
        material[0] -> pbrMetallicRoughness.baseColorTexture -> texture -> image
        
        Args:
            glb_path: Path to the .glb file
            
        Returns:
            Path to extracted PNG file in temp directory, or None if extraction fails.
            Result is cached in self.extracted_textures to avoid re-extraction.
        """
        if not PYGLTFLIB_AVAILABLE:
            return None
        
        # Return cached result if available
        if glb_path in self.extracted_textures:
            return self.extracted_textures[glb_path]
        
        try:
            from pygltflib import GLTF2
            from pygltflib.utils import ImageFormat
            import tempfile
            import hashlib
            import shutil
            import warnings
            import os
            
            # Suppress pygltflib warnings about bufferViews (cosmetic warnings, files still extract correctly)
            warnings.filterwarnings('ignore', category=UserWarning, module='pygltflib')
            
            # Load GLB file
            gltf = GLTF2().load(glb_path)
            
            # Find albedo (base color) texture via material chain
            target_image = None
            image_index = None  # Index in gltf.images array
            texture_purpose = "unknown"
            
            # Step 1: Get first material's albedo texture
            # glTF stores textures in material.pbrMetallicRoughness.baseColorTexture
            if gltf.materials:
                mat = gltf.materials[0]
                if mat.pbrMetallicRoughness and mat.pbrMetallicRoughness.baseColorTexture:
                    tex_info = mat.pbrMetallicRoughness.baseColorTexture
                    tex_idx = tex_info.index  # TextureInfo.index points to gltf.textures array
                    if tex_idx < len(gltf.textures):
                        tex = gltf.textures[tex_idx]
                        # Texture.source points to gltf.images array
                        if hasattr(tex, 'source') and tex.source is not None:
                            image_index = tex.source
                            texture_purpose = "albedo"
                            if image_index < len(gltf.images):
                                target_image = gltf.images[image_index]
            
            # Fallback: Use first image if material chain fails
            if not target_image and gltf.images:
                target_image = gltf.images[0]
                image_index = 0
                texture_purpose = "fallback_first"
            
            if not target_image:
                return None
            
            # Create unique output path using hash of glb_path to avoid conflicts
            glb_hash = hashlib.md5(glb_path.encode()).hexdigest()[:8]
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"glb_tex_{glb_hash}_{texture_purpose}.png")
            
            # Return cached version if already extracted
            if os.path.exists(output_path):
                self.extracted_textures[glb_path] = output_path
                return output_path
            
            # Clean up existing temp files (0.png, 1.png, etc.) to avoid pygltflib write conflicts
            for i in range(10):
                test_path = os.path.join(temp_dir, f"{i}.png")
                if os.path.exists(test_path):
                    os.remove(test_path)
            
            # Extract images to temp dir
            # This converts embedded bufferView data to PNG files
            gltf.convert_images(ImageFormat.FILE, path=temp_dir + '/')
            
            # Determine source path for target image
            # After convert_images, pygltflib may set uri or use default naming
            if target_image.uri:
                # URI is set (file path or data URI)
                src_path = os.path.join(temp_dir, os.path.basename(target_image.uri))
            elif image_index is not None:
                # Assume file named {image_index}.png (pygltflib convention)
                src_path = os.path.join(temp_dir, f"{image_index}.png")
            else:
                # Fallback to first extracted file
                src_path = None
                for i in range(10):
                    test_path = os.path.join(temp_dir, f"{i}.png")
                    if os.path.exists(test_path):
                        src_path = test_path
                        break
            
            # Copy to unique filename to avoid conflicts
            if src_path and os.path.exists(src_path):
                shutil.copy2(src_path, output_path)
                self.extracted_textures[glb_path] = output_path
                return output_path
            
        except Exception as e:
            print(f"Error extracting texture from {glb_path}: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def display_cell_image(self, row, col, filepath, bg_color):
        """Load and display an image on a grid cell.
        
        Handles both 2D images and GLB-extracted textures.
        Images are resized to fit the cell and cached for performance.
        """
        try:
            if not os.path.exists(filepath):
                return
            
            # Use cache key (filepath, cell_size) to avoid reloading
            cache_key = (filepath, self.cell_size)
            if cache_key in self.image_cache:
                photo = self.image_cache[cache_key]
            else:
                # Load and resize image to fit cell
                img = Image.open(filepath)
                size = int(self.cell_size * 0.9)
                img = img.resize((size, size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.image_cache[cache_key] = photo
            
            # Calculate center position
            x = col * self.cell_size + self.cell_size / 2
            y = row * self.cell_size + self.cell_size / 2
            
            # Create image on canvas
            img_id = self.grid_canvas.create_image(x, y, image=photo)
            self.cell_images[(row, col)] = img_id
            
            # Keep a reference to prevent garbage collection
            self._image_refs.append(photo)
            
        except Exception as e:
            print(f"Error loading image {filepath}: {e}")
            self.status_bar.config(text=f"Image error: {os.path.basename(filepath)}")


def main():
    root = tk.Tk()
    app = LevelEditor(root)
    
    # Try to auto-find game folder
    browser = GameFolderBrowser(root, app)
    browser.find_game_path()
    
    root.mainloop()


if __name__ == "__main__":
    main()
