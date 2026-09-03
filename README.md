<img src="/res/branding.png">

# mango python - workflow solutions
root compiled project of a series for npr workflow-focused custom C4D plugins and assets.

## Including (roadmap; not limited to)

- Camera track baking to parent (or other) track's keys for space switching.
- Camera depth dependent detail preservation and loss of detail for shaders.
- Camera angle dependent mesh flattening (flatten node).
- Anti-parallaxing geometry for small non-zero camera animation (using look-at operators).
- Separation of shader AOVs & objects into automatic render engine passes (takes system).
- Cleaner Standard/Physical node-space compatible baking (one click solution to bake shader AOVs -> texture).
- Export selected points or the inverted selection in the structure manager to comma separated value and/or nodes selection.

#### And the proprietary solutions for our pipeline;

- Automatic  <a href="https://elimango.github.io/studio/assetry/nodes/info/curvature">curvature</a> shader rim on overlapping mesh silhouettes

- Linked tracks:
  - Automatic or baked syncing of keyframes of one track to another:
    (i.e; 'pos.x' and 'pos.z' of an object would transform at the same rate, on the same keys.)
  - Isolate keyframes of a track dependent of a parent (or other) track's keys.
- Screen-Space controller pinning 
  - Rig switch allowing pinning of local transformations for any controller to the camera 
   (i.e; force controllers to stay in the same positions in screen-space over time)
- Weight Transfer
  - Transfer the same weights from one skeleton to another, bulk capability and single object. 
- Axis Transfer 
  - Easily set the frozen axis location to zero, or that of another object without affecting the objects translated or frozen PSR
- Motion Transfer
  - Interpret skeletal animation (such as from fbx) as transforms and transfer to controllers
- Relative Pathing
  - Interpret absolute file paths as relative (get relativity of an absolute path to the working directory)
- Team Render Express 
  - Easily package scenes with tokens and relative paths, fetched from the most recent git commit of the sequence
- Parallaxing 2D Backgrounds
  - Convert sequence environment to 2d plane 
  (i.e; works by taking a singular selected frame of your scene, renders the active perspective at 2,3,4x... the render resolution, and pastes it back into the scene as a plane in camera space for a set range of frames)


#### Py Plugin Development (?)
- Layer -> tag folders for vertical tag view.

### Contribution or related credit:
@elimango - lead developer

