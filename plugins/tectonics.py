import numpy, random

from decorators import genreq

@genreq(cellprops=[])
def generate(world, vd):
    # return

    Unassigned = -1

    # All cells start off with a plate_id of -1 (unassigned)
    plates_arr = world.new_cp_array(numpy.int16, Unassigned)

    # Configuration
    LandformConfig = {
        'InitialPlateSplitProb': 0.05,
        'InitialContinentMin': random.randint(4, 8),
        'InitialContinentMax': random.randint(8, 12),
    }

    world.set_param('InitialPlateSplitProb', LandformConfig['InitialPlateSplitProb'])
    world.set_param('InitialContinentMin', LandformConfig['InitialContinentMin'])
    world.set_param('InitialContinentMax', LandformConfig['InitialContinentMax'])

    num_plates = random.randint(
        LandformConfig['InitialContinentMin'], 
        LandformConfig['InitialContinentMax'], 
    )

    plate_centers = random.choices( list(world.cell_idxs()), k=num_plates )
    plate_dist = [1,] * num_plates      # distance to go out from the center to find available cells

    unlabeled = set(world.cell_idxs())  # all cells start off as unlabeled

    for plate_idx, region_idx in enumerate(plate_centers):
        plates_arr[region_idx] = plate_idx
        unlabeled.discard(region_idx)

    graph = world.graph

    # Add all cells to a plate
    while len(unlabeled) > 0:
        # For each plate, expand out from the center
        for center_idx in plate_centers:
            plate_id = plates_arr[center_idx]

            avail = list( filter(lambda idx: idx in unlabeled, graph.neighbors(center_idx, plate_dist[plate_id])) )

            # If there are no neighbors in the current radius, try expanding once. If there's nothing there
            # if means we're surrounded and should skip from here on out.
            if len(avail) == 0:
                avail = list( filter(lambda idx: idx in unlabeled, graph.neighbors(center_idx, plate_dist[plate_id] + 1)) )

                # If there are neighbors to mark, continue. If not, move on to the next plate.
                if len(avail) > 0:
                    plate_dist[plate_id] += 1
                else:
                    continue

            # The selected cells becomes part of the plate
            for idx in avail:
                plates_arr[idx] = plates_arr[center_idx]
                unlabeled.discard(idx)

            # Count remaining cells to be marked; break the loop if we're done.
            if len(unlabeled) == 0:
                break

        # There's a chance to add a new plate each iteration. New plates
        # can only exist in unmarked cells.
        if random.random() < LandformConfig['InitialPlateSplitProb']:
            # avail = list( filter(lambda idx: idx in unlabeled, world.cell_idxs()) )

            if len(unlabeled) > 0:
                cell_idx = random.choice(list(unlabeled))

                # Reserve a new plate_id                
                plates_arr[cell_idx] = len(plate_centers)
                plate_centers.append(cell_idx)      # add to plate centers so it joins the core rotation
                plate_dist.append(1)                # all plates start at dist=1
                unlabeled.discard(cell_idx)         # cell_idx no longer available for labeling

    # Add cp_plate to the world
    world.add_cell_property('plate', plates_arr)