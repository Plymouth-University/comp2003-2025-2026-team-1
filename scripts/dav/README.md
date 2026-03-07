
# YAML Level Formatting and Empty Grid Object Removal by David Williams

## Overview
This directory contains tools for processing YAML level files, specifically for formatting grid data and removing blank/empty grid objects.
After using `blank_level.yaml` as a template for level designing, then use `delete_blank.py` to remove empty grid object definitions.

## Process

### 1. Input: `blank_level.yaml`
Raw YAML file containing grid objects with potential empty entries.

```yaml
include: [LevelsShared.yaml]

fileProperties:
  creatorName: PythonScript

sceneName: OriginalWorld

cameraSettings:
  type: static
  postProcessing:
    depthOfField: { enabled: false }

grid: |
  gm,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,

  __,__,__,__,__,__,__,__, a1,b1,c1,d1,e1,f1,g1,h1,i1, __,__,__,__,__,
  __,__,__,__,__,__,__,__, a2,b2,c2,d2,e2,f2,g2,h2,i2, __,__,__,__,__,
  __,__,__,__,__,__,__,__, a3,b3,c3,d3,e3,f3,g3,h3,i3, __,__,__,__,__,
  __,__,__,__,__,__,__,__, a4,b4,c4,d4,e4,f4,g4,h4,i4, __,__,__,__,__,
  __,__,__,__,__,__,__,__, a5,b5,c5,d5,e5,f5,g5,h5,i5, __,__,__,__,__,
  __,__,__,__,__,__,__,__, a6,b6,c6,d6,e6,f6,g6,h6,i6, __,__,__,__,__,
  __,__,__,__,__,__,__,__, a7,b7,c7,d7,e7,f7,g7,h7,i7, __,__,__,__,__,
  __,__,__,__,__,__,__,__, a8,b8,c8,d8,e8,f8,g8,h8,i8, __,__,__,__,__,
  __,__,__,__,__,__,__,__, a9,b9,c9,d9,e9,f9,g9,h9,i9, __,__,__,__,__,
  __,__,__,__,__,__,__,__, aA,bA,cA,dA,eA,fA,gA,hA,iA, __,__,__,__,__,

  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,

gridObjects:
  a1: []
  b1: []
  c1: []
  d1: []
  e1: []
  f1: []
  g1: []
  h1: []
  i1: []

  a2: []
  b2: []
  c2: []
  d2: []
  e2: []
  f2: []
  g2: []
  h2: []
  i2: []

  a3: []
  b3: []
  c3: []
  d3: []
  e3: []
  f3: []
  g3: []
  h3: []
  i3: []

  a4: []
  b4: []
  c4: []
  d4: []
  e4: []
  f4: []
  g4: []
  h4: []
  i4: []

  a5: []
  b5: []
  c5: []
  d5: []
  e5: [p1]
  f5: []
  g5: []
  h5: []
  i5: []

  a6: []
  b6: []
  c6: []
  d6: []
  e6: [p2]
  f6: []
  g6: []
  h6: []
  i6: []

  a7: []
  b7: []
  c7: []
  d7: []
  e7: []
  f7: []
  g7: []
  h7: []
  i7: []

  a8: []
  b8: []
  c8: []
  d8: []
  e8: []
  f8: []
  g8: []
  h8: []
  i8: []

  a9: []
  b9: []
  c9: []
  d9: []
  e9: []
  f9: []
  g9: []
  h9: []
  i9: []

  aA: []
  bA: []
  cA: []
  dA: []
  eA: []
  fA: []
  gA: []
  hA: []
  iA: []

objectDefinitions:

sounds:

globalData:
```

### 2. Processing with `delete_blank.py`
The script performs the following operations:
- Parses the input YAML file
- Identifies and filters out blank/empty grid objects
- Reorganizes the structure for consistency
- Validates object references and spatial data

### 3. Output: `formatted_level.yaml`
Cleaned and formatted YAML with all blank objects removed.

```yaml
include: [LevelsShared.yaml]

fileProperties:
  creatorName: PythonScript

sceneName: OriginalWorld

cameraSettings:
  type: static
  postProcessing:
    depthOfField: {enabled: false}

grid: |
  gm,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,

  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,e5,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,e6,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,

  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,
  __,__,__,__,__,__,__,__, __,__,__,__,__,__,__,__,__, __,__,__,__,__,

gridObjects:
  e5: [p1]
  e6: [p2]

objectDefinitions:

sounds:

globalData:
```

## File Descriptions

| File | Purpose |
|------|---------|
| `blank_level.yaml` | Raw level data with empty grid cells and mainly empty grid object definitions |
| `formatted_level.yaml` | Processed level data, cleaned and optimized |
| `delete_blank.py` | Script that performs the transformation |

## Usage
```bash
python delete_blank.py
```

or import **delete_blank** function from `delete_blank.py` and implement in your own script