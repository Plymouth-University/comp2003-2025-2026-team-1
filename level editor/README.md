# Co OPERATION: MultiTurn - Level Editor

A Python tkinter-based level editor for creating YAML level files for the game Co OPERATION: MultiTurn.

## Features

### RPG Maker Style Workflow
- **Grid Editor (Left Panel)**: Visual grid where you can click cells and assign grid codes
- **GridObjects Editor (Right Panel)**: Separate panel for editing objects in each cell (like RPG Maker events)
- Two distinct workflows kept separate for clarity

### Integration with Game Folder
- Auto-detects Steam installation path
- Browses `StreamingAssets` folder for available 3D models, 2D textures, and sounds
- File → Set Game Folder to manually select the game directory

### Grid Editing
- Click any cell to select it
- Enter a grid code (e.g., `01`, `a1`, `gm`) and click "Apply to Selected"
- Use the Quick Palette dropdown for common codes (shows only codes used in grid)
- "Clear Cell" sets cell to `__` (empty)
- **Right-click to paint**: Paint the current code to cells RPG Maker-style
- **Ctrl+Right-click to erase**: Erase cells without needing a paint code
- **Drag to paint multiple cells**: Hold right-click and drag to paint/erase multiple cells
- Zoom in/out from View menu
- Change grid size from Edit menu

### GridObjects Editing
- Select a cell with a grid code (not `__`)
- Click "Edit Objects for Selected Cell"
- Add object codes (references to objectDefinitions)
- Add inline definitions (e.g., `{id: B, dir: East}`)
- Reorder objects with ↑↓ buttons
- Remove objects as needed

### Object Definitions
- Edit → Edit Object Definitions to manage all object codes
- Add short form (just a reference like `Floor`)
- Add long form (full definition with `mapObject`, `dir`, `tags`, etc.)
- Imports from existing YAML files

### Undo/Redo System (New!)
- **Ctrl+Z**: Undo the last action
- **Ctrl+Shift+Z**: Redo the last undone action
- **Edit Menu**: Undo and Redo options in the Edit dropdown (enabled/disabled based on availability)
- Supports undo/redo for:
  - Grid painting (all drag-painted cells grouped as one action)
  - Applying codes to cells
  - Clearing cells
  - Editing GridObjects
  - Adding/removing object definitions
- Maximum history: 50 states (configurable)
- New actions clear the redo history automatically

### Minimal YAML Output (New!)
The editor now saves only the essential YAML keys required by the game:
- `fileProperties` (creator name)
- `sceneName`
- `cameraSettings`
- `grid` (as literal block scalar)
- `gridObjects` (only for codes actually used in the grid)
- `objectDefinitions` (always present, even if empty)
- `include` (when using shared definition files)

This ensures smaller, cleaner level files that are compatible with the game parser.

### Quick Palette Shows Only Used Codes (New!)
- The Quick Palette dropdown now only displays grid codes that are actually placed in grid cells
- Updates in real-time when you apply new codes
- Reduces clutter and makes it easier to find frequently used codes

### Shared Definitions Feature

The editor supports loading a shared definitions file (typically provided with the level pack):

- **Startup Prompt**: When you first run the editor, you'll be asked if you want to load shared definitions
- **File Menu**: Use "File → Set Shared Definitions" to change or set the file at any time
- **Auto-Merge**: When loading a level YAML, the editor merges:
  1. Shared definitions (loaded first)
  2. Included files (via `include` directive, if any)
  3. The level file's own definitions (takes precedence)
- **Multiple Sources**: Object definitions can come from:
  - The shared definitions file
  - Files included via the `include` directive
  - The level file's own `objectDefinitions` section

### Custom YAML Tag Support

The editor now supports all game-specific YAML tags from the documentation:

- `!Animation` - Generic animation reference
- `!GLBAnimation` - GLB/glTF 3D model animations
- `!SpineAnimation` - Spine 2D animation
- `!MeshDeformAnimation` - Mesh deform animation (correct spelling)
- `!TweenAnimation` - Tween movement animation
- `!UnityAnimator` - Unity Animator controller parameters

Tags are preserved when saving YAML files. Unknown tags (any `!tag` not listed above) are also handled gracefully using a generic fallback handler.

### Texture Display on Grid Tiles

The grid editor displays textures on tiles instead of text codes:

- **2D Art Support**: Loads `art2d` textures (`.png`, `.jpg`) from the game's `StreamingAssets/Art/2D` folder
- **GLB Texture Extraction** (New!): Automatically extracts albedo (base color) textures from 3D models (`art3d` GLB files) for display
- **Colored Placeholders**: For objects with no textures, displays colored rectangles
- **Auto-Resolution**: Automatically finds textures referenced in object definitions via `art2d` or `art3d` entries
- **Image Caching**: Caches images and extracted textures for performance
- **Pillow Integration**: Uses PIL/Pillow for image loading and resizing

#### How it works:
1. For each grid cell, the editor looks up the objects in `gridObjects`
2. Priority 1: It searches for `art2d` entries with `texture` or `textures` fields
3. Priority 2 (Fallback): If no 2D texture, checks `art3d` entries and extracts albedo texture from GLB files using `pygltflib`
4. The texture is displayed centered in the cell (resized to fit)
5. If no texture is found: shows a colored rectangle only

## Usage

1. **Run the editor**:
   ```
   py level_editor.py
   ```
   - On first run, you'll be prompted to load a shared definitions file
   - This file (e.g., `LevelsShared.yaml`) contains common object definitions used across multiple levels
   - You can skip or set it later via File → Set Shared Definitions

2. **Set Game Folder** (optional):
   - File → Set Game Folder
   - Browse to your Co OPERATION: MultiTurn installation

3. **Set Shared Definitions** (recommended):
   - File → Set Shared Definitions
   - Select the shared YAML file from your level pack
   - This ensures all object codes are properly defined

4. **Create/Open Level**:
   - File → New Level for a blank level
   - File → Open YAML to load existing level file
   - The editor will automatically merge shared definitions with the level file

5. **Edit Grid**:
   - Click cells, enter grid codes, apply
   - Right-click to paint codes RPG Maker-style
   - Ctrl+Right-click to erase cells
   - Use Undo (Ctrl+Z) / Redo (Ctrl+Shift+Z) to revert mistakes

6. **Edit Objects**:
   - Select a cell, click "Edit Objects for Selected Cell"
   - Add object codes or inline definitions
   - Object codes must exist in either the level's objectDefinitions or the shared definitions

7. **Save**:
   - File → Save YAML (or Save YAML As...)
   - Files are saved with minimal YAML (only essential keys)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+S | Save YAML |
| Ctrl+Z | Undo last action |
| Ctrl+Shift+Z | Redo last undone action |
| Right-click | Paint current code to cell |
| Ctrl+Right-click | Erase cell (set to `__`) |
| Drag + Right-click | Paint/erase multiple cells |

## YAML Format

The editor generates YAML files matching the game's expected format:

```yaml
fileProperties:
  creatorName: YourName
sceneName: OriginalWorld
grid: |
  01,02,03,__,
  __,04,05,06,
  
gridObjects:
  01: [F, P1]
  02: [F, {id: B, dir: East}]
  
objectDefinitions:
  F: Floor
  B: { mapObject: Bed }
```

When using shared definitions, the `include` directive is used instead of duplicating definitions:

```yaml
include:
  - LevelsShared.yaml
grid: |
  01,02,03,__,
objectDefinitions: {}
```

## Requirements

- Python 3.7+ (tested with 3.13)
- PyYAML (`py -m pip install pyyaml`)
- Pillow (`py -m pip install Pillow`) - Required for texture display
- **pygltflib** (`py -m pip install pygltflib`) - Optional, enables GLB texture extraction
  - Without pygltflib: 3D models display as colored rectangles only
  - With pygltflib: Automatically extracts and displays albedo textures from GLB files
- tkinter (usually included with Python on Windows)

## Tips

- Grid codes can be multi-character (e.g., `a1`, `3j`, `wall_e`)
- `__` represents an empty cell
- Object codes in `gridObjects` should match codes in `objectDefinitions`
- The editor will warn you if you use undefined codes
- Import existing levels to see the format and learn by example
- Use Ctrl+Z liberally - the undo system supports up to 50 actions!
- The Quick Palette only shows codes you've actually used in the grid for easier access
