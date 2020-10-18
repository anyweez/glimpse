import { Terrain, available } from './terrain';

/**
 * Represents a Cell or Cell-like object that marks a point in the world
 */
interface Location {
    x: number;
    y: number;
    elevation: number;
}

export interface WorldMeta {
    dim?: number;
    // The depth of the aquifer in the world; anything beneath this depth becomes a water tile.
    aquiferDepth?: number;
    altitudeVariance?: number;
}

export class World {
    dim: number;
    grid: Array<Cell> = [];
    meta: WorldMeta;
    // aquiferDepth: number = AQUIFER_DEPTH;

    constructor(meta : WorldMeta) {
        this.meta = meta;

        if (this.meta.altitudeVariance === undefined) {
            this.meta.altitudeVariance = 20.0;
        }

        if (this.meta.dim === undefined) {
            this.meta.dim = 1025; // 2^10+1
        }

        if (this.meta.aquiferDepth === undefined) {
            this.meta.aquiferDepth = 35;
        }

        // Generate cells for a world of size `meta.dim`
        for (let y = 0; y < meta.dim; y++) {
            for (let x = 0; x < meta.dim; x++) {
                let cell = new Cell(x, y);
                cell.world = this;

                this.grid.push(cell);
            }
        }
    }

    init({ update }: { update: Function }) {
        const steps = [
            generateElevations.bind(null, this),
            aquifer.bind(null, this),
            rainfall.bind(null, this),
            evaporate.bind(null, this),
            terrainify.bind(null, this),
            smoothTerrain.bind(null, this),
        ];

        // Run all steps
        return steps.reduce((promise, next) => {
            return promise.then(() => {
                next();
                return update();
            });
        }, Promise.resolve());
    };

    /**
     * Finds and returns a particular Cell (or Location). A Cell emulator is not a real cell 
     * object but contains most of the important properties; they simulate wraparound and other 
     * effects for terrain generation.
     *  
     * @param {number} x coordinate
     * @param {number} y coordinate
     * @returns {Location} containing (at least) x, y, and elevation properties
     */
    find(x: number, y: number): Location {
        // Inherit elevation (and potentially other properties, if needed) from out-of-bounds
        // cells. Coordinates (even if out of bounds) remain intact.
        if (x < 0 || x >= this.meta.dim) {
            let realCell = (x < 0) ? this.find(this.meta.dim - x, y) : this.find(x - this.meta.dim, y);

            return { x: x, y: y, elevation: realCell.elevation };
        }

        if (y < 0 || y >= this.meta.dim) {
            let realCell = (y < 0) ? this.find(x, this.meta.dim - y) : this.find(x, y - this.meta.dim);

            return { x: x, y: y, elevation: realCell.elevation };
        }

        return this.grid[y * this.meta.dim + x];
    }

    // TODO: ambiguity issue between Location and Cell
    neighbors(cell: Location): Array<any> {
        let neighbors: Array<any> = [];

        if (cell.x - 1 >= 0) neighbors.push(this.find(cell.x - 1, cell.y));
        if (cell.y - 1 >= 0) neighbors.push(this.find(cell.x, cell.y - 1));
        if (cell.x + 1 < this.meta.dim) neighbors.push(this.find(cell.x + 1, cell.y));
        if (cell.y + 1 < this.meta.dim) neighbors.push(this.find(cell.x, cell.y + 1));

        return neighbors;
    }
}

/**
 * World generation functions. These functions are related to generating the *initial state* of the world 
 * less than evolutions beyond the initial state. They primarily revolve around terrain generation, watersheds,
 * terrain types, and so on.
 */

// New version greatly influenced / copied from this article:
//   http://www.playfuljs.com/realistic-terrain-in-130-lines/
function generateElevations(world: World): void {
    let full = world.meta.dim - 1;

    function divide(size: number, variance: number): void {
        let half = size / 2;

        // Base case
        if (half < 1) return;

        for (let y = half; y < full; y += size) {
            for (let x = half; x < full; x += size) {
                square(x, y, half, variance);
            }
        }

        for (let y = 0; y <= full; y += half) {
            for (let x = (y + half) % size; x <= full; x += size) {
                diamond(x, y, half, variance);
            }
        }

        return divide(size / 2, variance * 0.9);
    }

    function square(x: number, y: number, half: number, variance: number): void {
        let tl = world.find(x - half, y - half);
        let tr = world.find(x + half, y - half);
        let bl = world.find(x - half, y + half);
        let br = world.find(x + half, y + half);

        let avg = [tl, tr, bl, br].map(p => p.elevation / 4).reduce((a, b) => a + b);

        world.find(x, y).elevation = avg + (Math.random() - 0.5) * variance;
    }

    function diamond(x: number, y: number, half: number, variance: number): void {
        let n = world.find(x, y - half);
        let e = world.find(x + half, y);
        let s = world.find(x, y + half);
        let w = world.find(x - half, y);

        let avg = [n, e, s, w].map(p => p.elevation / 4).reduce((a, b) => a + b);

        world.find(x, y).elevation = avg + (Math.random() - 0.5) * variance;
    }

    // Set initial elevations randomly in [0, 100]
    world.find(0, 0).elevation = Math.random() * 100;
    world.find(full, 0).elevation = Math.random() * 100;
    world.find(0, full).elevation = Math.random() * 100;
    world.find(full, full).elevation = Math.random() * 100;

    divide(full, world.meta.altitudeVariance);
}

function rainfall(world: World) {
    // todo: should return Cell but Location and Cell are getting too interwoven
    function drip(start: Location): any {
        let lowest = world.neighbors(start).reduce((lowest, next) => {
            if (next.elevation < lowest.elevation && !next.water) return next;
            else return lowest;
        }, start);

        if (start.x === lowest.x && start.y === lowest.y) return start;
        else return drip(lowest);
    }

    // todo: replace this.dim * 2 with a world-level 'wetness' constant
    for (let i = 0; i < world.dim * 5; i++) {
        let x = Math.floor(Math.random() * world.dim);
        let y = Math.floor(Math.random() * world.dim);

        let lowest = drip(world.find(x, y));
        lowest.water = true;
    }
};

function aquifer(world: World) {
    world.grid.forEach(cell => {
        if (cell.elevation < world.meta.aquiferDepth) cell.water = true;
    });
};

function evaporate(world: World) {
    world.grid.forEach(cell => {
        let count = world.neighbors(cell).filter(neighbor => neighbor.water).length;
        if (count === 0) cell.water = false;
    });
}

/**
 * Iteratively determine what terrain type each cell is. Terrainify will continue to iterate
 * over all cells until the terrain types of all cells are static for a full iteration.
 */
function terrainify(world: World): void {
    let changed = true;
    let iteration = 1;

    while (changed) {
        changed = false;

        world.grid.forEach(cell => {
            let label = available.find(terr => terr.func(cell, world)).label;

            if (cell.terrain !== label) {
                changed = true;
                cell.terrain = label;
            }
        });

        iteration++;

        // Stop after sqrt(dim) iterations for performance reasons.
        if (iteration > Math.sqrt(world.dim)) return;
    }
}

function smoothTerrain(world: World): void {
    world.grid.forEach(cell => {
        let terrains = new Set( world.neighbors(cell).map(c => c.terrain) );

        // If there's only one type of terrain around here, inherit it.
        if (terrains.size === 1) {
            let commonTerrain = terrains.values().next().value;

            if (cell.terrain !== commonTerrain) {
                cell.terrain = commonTerrain;

                if (cell.terrain === Terrain.WATER) cell.water = true;
            }
        }
    });
}

export class Cell implements Location {
    x: number;
    y: number;
    terrain: number = -1;
    elevation: number = 0;
    water: boolean = false;
    world: World;

    constructor(x: number, y: number) {
        this.x = x;
        this.y = y;
    }
}