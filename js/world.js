let _ = require('lodash');
let species = require('./species');

// How much elevation should randomly vary from its surroundings.
const ELEVATION_NOISE_LEVEL = 7;

function World(dim) {
    this.dim = dim;
    this.grid = [];
    // Living populations. Once a population goes extinct it should unregister itself
    // from this list.
    this.populations = [];
    // The queue of populations that should be spawned at the next spawn interval.
    this.spawns = [];

    this.aquiferDepth = 35;

    for (let y = 0; y < dim; y++) {
        for (let x = 0; x < dim; x++) {
            let cell = new Cell(x, y);
            cell.world = this;

            this.grid.push(cell);
        }
    }

    return this;
}

/**
 * Remove a population from the global list if it becomes extinct.
 */
World.prototype.extinguish = function (pop) {
    console.log('extinguishing @ world')
    this.populations = this.populations.filter(p => p.id !== pop.id);
}

World.prototype.find = function (x, y) {
    // Inherit elevation (and potentially other properties, if needed) from out-of-bounds
    // cells. Coordinates (even if out of bounds) remain intact.
    if (x < 0 || x >= this.dim) {
        let realCell = null;

        if (x < 0) realCell = this.find(this.dim - x, y);
        else realCell = this.find(x - this.dim, y);

        return { x: x, y: y, elevation: realCell.elevation };
    }

    if (y < 0 || y >= this.dim) {
        let realCell = null;

        if (y < 0) realCell = this.find(x, this.dim - y);
        else realCell = this.find(x, y - this.dim);

        return { x: x, y: y, elevation: realCell.elevation };
    }

    return this.grid[y * this.dim + x];
};

World.prototype.neighbors = function (cell) {
    let neighbors = [];

    if (cell.x - 1 >= 0) neighbors.push(this.find(cell.x - 1, cell.y));
    if (cell.y - 1 >= 0) neighbors.push(this.find(cell.x, cell.y - 1));
    if (cell.x + 1 < this.dim) neighbors.push(this.find(cell.x + 1, cell.y));
    if (cell.y + 1 < this.dim) neighbors.push(this.find(cell.x, cell.y + 1));

    return neighbors;
}

// New version greatly influenced / copied from this article:
//   http://www.playfuljs.com/realistic-terrain-in-130-lines/
World.prototype.generateElevations = function () {
    let self = this;
    let full = this.dim - 1;

    function divide(size, variance) {
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

    function square(x, y, half, variance) {
        let tl = self.find(x - half, y - half);
        let tr = self.find(x + half, y - half);
        let bl = self.find(x - half, y + half);
        let br = self.find(x + half, y + half);

        let avg = [tl, tr, bl, br].map(p => p.elevation / 4).reduce((a, b) => a + b);

        self.find(x, y).elevation = avg + (Math.random() - 0.5) * variance;
    }

    function diamond(x, y, half, variance) {
        let n = self.find(x, y - half);
        let e = self.find(x + half, y);
        let s = self.find(x, y + half);
        let w = self.find(x - half, y);

        let avg = [n, e, s, w].map(p => p.elevation / 4).reduce((a, b) => a + b);

        self.find(x, y).elevation = avg + (Math.random() - 0.5) * variance;
    }

    this.find(0, 0).elevation = Math.random() * 100;
    this.find(full, 0).elevation = Math.random() * 100;
    this.find(0, full).elevation = Math.random() * 100;
    this.find(full, full).elevation = Math.random() * 100;

    divide(full, 20);
}

World.prototype.rainfall = function () {
    let self = this;
    function drip(start) {
        let lowest = self.neighbors(start).reduce((lowest, next) => {
            if (next.elevation < lowest.elevation && !next.water) return next;
            else return lowest;
        }, start);

        if (start.x === lowest.x && start.y === lowest.y) return start;
        else return drip(lowest);
    }

    // todo: replace this.dim * 2 with a world-level 'wetness' constant
    for (let i = 0; i < this.dim * 5; i++) {
        let x = Math.floor(Math.random() * this.dim);
        let y = Math.floor(Math.random() * this.dim);

        let lowest = drip(this.find(x, y));
        lowest.water = true;
    }
};

World.prototype.aquifer = function () {
    this.grid.forEach(cell => {
        if (cell.elevation < this.aquiferDepth) cell.water = true;
    });
};

World.prototype.evaporate = function () {
    this.grid.forEach(cell => {
        let count = this.neighbors(cell).filter(neighbor => neighbor.water).length;
        if (count === 0) cell.water = false;
    });
}

/**
 * Iteratively determine what terrain type each cell is. Terrainify will continue to iterate
 * over all cells until the terrain types of all cells are static for a full iteration.
 */
World.prototype.terrainify = function () {
    let changed = true;
    let iteration = 1;

    while (changed) {
        // console.log('starting terrainify iter #' + iteration);
        changed = false;

        this.grid.forEach(cell => {
            let label = cell.availableTerrains.find(terr => terr.func(cell, this)).label;

            if (cell.terrain !== label) {
                changed = true;
                cell.terrain = label;
            }
        });

        iteration++;

        // Stop after sqrt(dim) iterations.
        if (iteration > Math.sqrt(this.dim)) return;
    }
};

World.prototype.smoothTerrain = function () {
    let smoothed = 0;

    this.grid.forEach(cell => {
        let terrains = new Set(this.neighbors(cell).map(c => c.terrain));

        // If there's only one type of terrain around here, inherit it.
        if (terrains.size === 1) {
            let commonTerrain = terrains.values().next().value;

            if (cell.terrain !== commonTerrain) {
                cell.terrain = commonTerrain;
                if (cell.terrain === 'water') cell.water = true;
                smoothed += 1;
            }
        }
    });

    console.log(`Cells smoothed: ${smoothed} / ${this.dim * this.dim} (${100 * smoothed / (this.dim * this.dim)}%)`);
};

World.prototype.init = function (events) {
    this.sunshine();

    let checkpoint = Date.now();
    let timing = {};

    let jobs = [
        this.generateElevations.bind(this),
        this.aquifer.bind(this),
        this.rainfall.bind(this),
        this.evaporate.bind(this),
        this.terrainify.bind(this),
        this.smoothTerrain.bind(this),
    ];

    // Run all jobs
    return jobs.reduce((promise, next) => {
        return promise.then(() => {
            next();
            return events.update();
        });
    }, Promise.resolve());
};

World.prototype.sunshine = function () {
    this.grid.forEach(function (cell) {
        console.log(cell);
        let sun = new species.RenewablePopulation(cell, {
            name: 'Sunshine',
            type: 'energy',
        });

        this.populations.push(sun);
        cell.populations.push(sun);
    }.bind(this));
};

function Cell(x, y) {
    this.x = x;
    this.y = y;
    this.terrain = null;
    this.elevation = 0; // default, will be replaced with something procedural
    this.water = false;
    this.populations = [];
    this.world = null;

    return this;
}

Cell.prototype.extinguish = function (pop) {
    console.log('extinguishing @ cell')
    this.populations = this.populations.filter(p => p.id !== pop.id);
    // Let the world know
    this.world.extinguish(pop);
}

/**
 * Iterate through one 'cycle' of the world. Currently this just calls step() on each
 * population, though the idea of a world cycle is based around a randomly ordered
 * task queue that can support tasks of any type.
 * 
 * It's currently important that the order of events is random so that certain populations
 * don't get the advantage on eating, etc just because they're listed first in the array.
 */
World.prototype.cycle = function () {
    console.log('running cycle');

    let tasks = [];
    // // Every population should take a step
    this.populations.forEach(pop => tasks.push(pop.step.bind(pop)));
    // // Call each function in a random order.
    _.shuffle(tasks).forEach(pop => pop());

    // // Now run each populations end() function to finish the turn
    tasks = [];
    this.populations.forEach(pop => tasks.push(pop.end.bind(pop)));
    // // Call each function in a random order.
    _.shuffle(tasks).forEach(pop => pop());

    if (this.populations.length > 0) {
        let pops = this.populations.filter(p => p.type !== 'energy');
        let show = this.populations.filter(p => {
            return pops.find(target => target.home.x === p.home.x && target.home.y === p.home.y) !== undefined;
        })

        console.log(`${pops.length} living populations`);
        show.forEach(function (pop) {
            console.log(`  (${pop.home.x}, ${pop.home.y}) ${pop.name}, pop ${pop.population} @ health ${pop.health}`);
        })

    } else {
        console.log(`${this.populations.length} living populations`);
    }
}

World.prototype.spawn = function () {
    // if (this.spawns.length === 0) return;

    let i = Math.floor(Math.random() * this.grid.length);
    let population = new species.Population(this.grid[i]);

    this.populations.push(population);
    // this.grid[i].populations.push(population);
}

Cell.prototype.availableTerrains = [
    {
        label: 'water',
        func: function (cell, world) { return cell.water; }
    },
    {
        label: 'sand',
        func: function (cell, world) {
            let valid = world.neighbors(cell).filter(cell => cell.water || cell.terrain === 'sand').length > 0;

            return valid && cell.elevation - world.aquiferDepth < 10;
        }
    },
    {
        label: 'rock',
        func: function (cell, world) {
            return cell.elevation > 90;
        }
    },
    // grass is the default unless terrain has another label
    {
        label: 'grass',
        func: function (cell, world) {
            return true;
        }
    }
];

module.exports = {
    World: World,
};