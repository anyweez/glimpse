import random, structs, numpy, datetime
import voronoi

seed = round( datetime.datetime.now().timestamp() * 10000 )
random.seed(seed)

# Configuration variables
PointCount = 100

print('seed=%d, num_points=%d' % (seed, PointCount))

def point_cloud(n):
    return [(random.random(), random.random()) for _ in range(n)]

points = numpy.array(point_cloud(PointCount))
vor = voronoi.generate(points)

world = structs.World(vor)
world.build()
world.label()

## Render
world.render(
    cell_labels=True, 
    color_boundaries=True, 
    cell_elevation=True, 
    show_graph=False, 
    tectonics=False,
    outline_landforms=True,
)