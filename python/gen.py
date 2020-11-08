import random, structs, numpy
import voronoi

random.seed(3264)

# Configuration variables
PointCount = 1024

def point_cloud(n):
    return [(random.random(), random.random()) for _ in range(n)]

# points = numpy.array(point_cloud(PointCount))

# vor = voronoi.generate(points)

vor = voronoi.prebuilt_vor1()

world = structs.World(vor)
world.build()

## Render
world.render(
    cell_labels=True, 
    color_boundaries=True, 
    cell_elevation=True, 
    show_graph=False, 
    tectonics=False
)