# Glimpse
## Procedural world generation

I've wanted to generate my own virtual worlds for a long time but haven't had much background on how to pursue it. This project is still young
but is currently tackling terrain generation along with some camera work to provide beautiful fly-by's over my grid world. I'm intentionally not
using any libraries and am focusing on balancing the quality of the output with performance whenever possible.

At it's conclusion, I'd like to support infinitely large maps (bounded only by the memory available to the browser) as well as a life simulator. The
majority of world simulation will take place prior to first render, but the majority of life simulation would take place after rendering has begun.

### Altitude generation
Glimpse currently uses the [diamond-square algorithm](https://en.wikipedia.org/wiki/Diamond-square_algorithm) to generate the elevation map, the most 
important property of every cell in the grid. Every cell has an altitude and it doesn't change once assigned.

### Water table, rainfall, and evaporation
Once altitudes are assigned, certain cells are covered by water by one of two processes. The first process is the water table (aquifer), which covers
all cells that have a low altitude. The second process is rainfall, which randomly places water throughout the map and it recursively runs downhill until
it reaches a local minimum.

The final aquatic stage is evaporation, which simply removes all pools of water that only occupy a single cell.

### Terrainification
Terrain types are assigned based on whether specific predicates are true for a given cell; multiple iterations can be run to evolve terrain based
on other terrain types; for example, beaches must either be touching water or other beaches, so after multiple iterations beaches can conceivably
extend far from the water's edge if other conditions are met.

The currently supported terrain types include:
  - Water
  - Sand
  - Rock
  - Grass

### Rendering
The world is rendered on an HTML5 canvas using a sliding window. A few straightforward optimizations are in place, including the use of 
`requestAnimationFrame` and only rendering objects that are present on screen. The latter of these, along with zooming, should make it possible to
support very large maps without negatively effecting FPS.

A cell is colored based on its terrain type as well as other secondary properties (like elevation, which affects the shade of the terrain color).

### Life simulation
Currently there's no life simulation taking place. Ideally I'd like to have a few different types of species with a few different properties based
on where they start in the world. The biomes they live in, their diets, and other properties will be customizable and behaviors will be simulated
as the user watches. 

Once life simulation is in place I'd like to use the presence of life as an indicator that a world is still 'active', and transition to a new world
whenever the old one dies.