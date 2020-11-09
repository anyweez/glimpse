import random, structs, numpy, datetime
import voronoi

seed = round( datetime.datetime.now().timestamp() * 10000 )
random.seed(seed)

print('seed=%d' % (seed,))

# Configuration variables
PointCount = 1024

def point_cloud(n):
    return [(random.random(), random.random()) for _ in range(n)]

points = numpy.array(point_cloud(PointCount))
vor = voronoi.generate(points)

world = structs.World(vor)
world.build()

## Render
world.render(
    cell_labels=False, 
    color_boundaries=True, 
    cell_elevation=True, 
    show_graph=False, 
    tectonics=False
)