import numpy, random

from decorators import genreq

@genreq(cellprops=[])
def generate(world, vd):
    Unassigned = -1

    # All cells start off with a plate_id of -1 (unassigned)
    plates_arr = world.new_cp_array(numpy.int16, Unassigned)

    # Configuration
    LandformConfig = {
        'InitialPlateSplitProb': random.random() / 50.0, # [0, .02]
        'InitialContinentMin': random.randint(1, 3),
        'InitialContinentMax': random.randint(3, 8),
    }

    world.set_param('InitialPlateSplitProb', LandformConfig['InitialPlateSplitProb'])
    world.set_param('InitialContinentMin', LandformConfig['InitialContinentMin'])
    world.set_param('InitialContinentMax', LandformConfig['InitialContinentMax'])

    num_plates = random.randint(
        LandformConfig['InitialContinentMin'], 
        LandformConfig['InitialContinentMax'], 
    )

    plate_centers = random.choices( list(world.cell_idxs()), k=num_plates )
    plate_dist = [1,] * num_plates  # distance to go out from the center to find available cells

    for plate_idx, region_idx in enumerate(plate_centers):
        plates_arr[region_idx] = plate_idx

    # Function to check whether a cell still needs to have a plate assigned. Boundary cells
    # are excluded.
    still_available = lambda idx: plates_arr[idx] == Unassigned

    remaining = sum( [1 for idx in world.cell_idxs() if still_available(idx)] )
    graph = world.graph

    # Add all cells to a plate
    while remaining > 0:
        # For each plate, expand out from the center
        for center_idx in plate_centers:
            plate_id = plates_arr[center_idx]

            avail = list( filter(still_available, graph.neighbors(center_idx, plate_dist[plate_id])) )

            while len(avail) == 0:
                plate_dist[plate_id] += 1
                avail = list( filter(still_available, graph.neighbors(center_idx, plate_dist[plate_id])) )

            selected_idx = random.choice(avail)

            # The selected cell becomes part of the plate
            plates_arr[selected_idx] = plates_arr[center_idx]

            # Count remaining cells to be marked; break the loop if we're done.
            remaining = sum( [1 for idx in world.cell_idxs() if still_available(idx)] )

            if remaining == 0:
                break

        # There's a chance to add a new plate each iteration. New plates
        # can only exist in unmarked cells.
        if random.random() < (LandformConfig['InitialPlateSplitProb'] / len(plate_centers)):
            avail = list( filter(still_available, world.cell_idxs()) )

            if len(avail) > 0:
                cell_idx = random.choice(avail)

                # Reserve a new plate_id                
                plates_arr[cell_idx] = len(plate_centers)
                plate_centers.append(cell_idx)
                plate_dist.append(1) # all plates start at dist=1

    # Add cp_plate to the world
    world.add_cell_property('plate', plates_arr)