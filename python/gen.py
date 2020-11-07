import random, numpy, structs
import matplotlib.pyplot as plt

from scipy.spatial import Voronoi, voronoi_plot_2d

random.seed()

# Configuration variables
PointCount = 480

def point_cloud(n):
    return [(random.random(), random.random()) for _ in range(n)]

points = numpy.array(point_cloud(PointCount))
vor = None

for i in range(3):
    vor = Voronoi(points)
    new_points = numpy.zeros(points.shape)

    for point_idx, region_id in enumerate(vor.point_region):
        region = vor.regions[region_id]

        if -1 in region:
            new_points[point_idx] = points[point_idx]

        vertices = [vor.vertices[idx] for idx in region]

        new_points[point_idx] = numpy.mean(vertices, 0)

    points = new_points

world = structs.World(vor)

## Render
world.render(cell_labels=False, color_boundaries=True, cell_elevation=True)