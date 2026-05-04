# Co OPERATION: MultiTurn Level Editor User Guide

## Introduction
This editor is a Python tkinter tool for creating YAML level files for *Co OPERATION: MultiTurn*, using an RPG Maker-style workflow:
- Left panel: Visual grid editor to assign grid codes to cells
- Right panel: Separate editor for managing GridObjects (like RPG Maker events)
- Supports texture display, undo/redo, shared definition files, and game folder integration.

## Prerequisites
- Python 3.7+ (tested with 3.13)
- Required packages:
  ```bash
  pip install pyyaml pillow  # Core requirements
  pip install pygltflib    # Optional: Enables 3D model texture extraction
  ```

## Launching the Editor
1. Open a terminal in the `level editor` directory.
2. Run:
   ```bash
   py level_editor.py  # Windows
   python3 level_editor.py  # Linux/macOS
   ```
3. On first launch, you will be prompted to set the Mod Folder. (e.g., `FinalPackage/` folder). You can skip this and set it later via *File → Set Mod Folder*.

## Step-by-Step: Create a New Level
### 1. Start a New Level
- Go to *File → New Level* to create a blank grid (default 15x12 cells)

### 2. Edit the Grid
- **Select a cell**: Left-click any grid cell
- **Assign a grid code**: Enter a code (e.g., `01`, `F`, `gm`) in the "Grid Code" field, click *Apply to Selected*
- **Paint multiple cells**: Right-click to paint the current code to cells (RPG Maker-style). Hold right-click and drag to paint multiple cells.
- **Erase cells**: Ctrl+Right-click to set cells to `__` (empty)
- **Undo/Redo**: Use Ctrl+Z (undo) / Ctrl+Shift+Z (redo) for mistakes
- **Zoom**: Use *View → Zoom In/Out* to adjust grid size

### 3. Edit GridObjects (Cell Objects)
1. Select a non-empty cell (code ≠ `__`)
2. Click *Edit Objects for Selected Cell* in the right panel
3. Add objects:
   - **Object Code**: References codes in `objectDefinitions`
   - **Inline Definition**: Add custom YAML dicts (e.g., `{id: B, dir: East}`)
4. Reorder objects with ↑/↓ buttons, remove unwanted objects

### 4. Manage Object Definitions
- Go to *Edit → Edit Object Definitions* to add/modify object codes:
  - Short form: Just a reference (e.g., `F: Floor`)
  - Long form: Full definition with `mapObject`, `dir`, `tags`, etc.

### 5. Save Your Level
- Go to *File → Save YAML* (or *Save YAML As...* for a new file)
- Files are saved with minimal YAML (only essential keys for the game parser)

## Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| Ctrl+S | Save YAML |
| Ctrl+Z | Undo last action |
| Ctrl+Shift+Z | Redo last undone action |
| Right-click | Paint current code to cell |
| Ctrl+Right-click | Erase cell (set to `__`) |
| Drag + Right-click | Paint/erase multiple cells |

## Tips
- `__` represents an empty cell
- The Quick Palette dropdown only shows codes you have already used in the grid
- Grid codes can be multi-character (e.g., `a1`, `wall_e`)
- The editor warns you if you use undefined object codes
- Up to 50 undo states are saved automatically

## Troubleshooting
- **No textures displayed**: Install Pillow, set the correct game folder, or add `art2d`/`art3d` entries to your object definitions
- **Undefined code warnings**: Add the code to *Edit → Object Definitions* or make sure you have set the Mod Folder: *File → Set Mod Folder*
- **YAML errors**: Ensure inline definitions use valid YAML syntax (e.g., `{id: X, dir: South}`)
