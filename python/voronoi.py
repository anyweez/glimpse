import numpy

from scipy.spatial import Voronoi

def generate(points, n_smooth=3):
    vor = None

    for _ in range(n_smooth):
        vor = Voronoi(points)
        new_points = numpy.zeros(points.shape)

        for point_idx, region_id in enumerate(vor.point_region):
            region = vor.regions[region_id]

            if -1 in region:
                new_points[point_idx] = points[point_idx]

            vertices = [vor.vertices[idx] for idx in region]
            new_points[point_idx] = numpy.mean(vertices, 0)

        points = new_points
    
    return vor