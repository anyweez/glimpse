// How much elevation should randomly vary from its surroundings.
const ELEVATION_NOISE_LEVEL = 7;

function World(dim) {
    this.dim = dim;
    this.grid = [];

    this.aquiferDepth = 35;

    for (let y = 0; y < dim; y++) {
        for (let x = 0; x < dim; x++) {
            this.grid.push(new Cell(x, y));
        }
    }

    return this;
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

World.prototype.generateElevations = function () {
    let self = this;

    function midpoint(tl, br) {
        return self.find(Math.round((tl.x + br.x) / 2), Math.round((tl.y + br.y) / 2));
    }

    function dropoff(variance) {
        return variance * 0.9;
    }

    function square(tl, tr, bl, br, variance) {
        let elev = (tl.elevation + tr.elevation + bl.elevation + br.elevation) / 4;
        let rand = (Math.random() - 0.5) * ELEVATION_NOISE_LEVEL * variance;

        let mid = midpoint(tl, br);
        mid.elevation = Math.max(0, elev + rand);
        // mid.elevation = 100;

        // Keep working on smaller and smaller squares
        if (br.x - mid.x > 1 && br.y - mid.y > 1) {
            // left diamond
            diamond(tl, mid, bl, self.find(mid.x - (mid.x - tl.x) * 2, mid.y), dropoff(variance));
            // top diamond
            diamond(self.find(mid.x, mid.y - (mid.y - tl.y) * 2), tr, mid, tl, dropoff(variance));
            // right diamond
            diamond(tr, self.find(mid.x + (tr.x - mid.x) * 2, mid.y), br, mid, dropoff(variance));
            // south diamond
            diamond(mid, br, self.find(mid.x, mid.y + (bl.y - mid.y) * 2), bl, dropoff(variance));
        } else {
            // left diamond
            diamond(tl, mid, bl, self.find(mid.x - 2, mid.y), dropoff(variance), true);
            // top diamond
            diamond(self.find(mid.x, mid.y - 2), tr, mid, tl, dropoff(variance), true);
            // right diamond
            diamond(tr, self.find(mid.x + 2, mid.y), br, mid, dropoff(variance), true);
            // bottom diamond
            diamond(mid, br, self.find(mid.x, mid.y + 2), bl, dropoff(variance), true);
        }
    }

    function diamond(n, e, s, w, variance, completed = false) {
        let elev = (n.elevation + e.elevation + s.elevation + w.elevation) / 4;
        let rand = (Math.random() - 0.5) * 10 * variance;

        let mid = midpoint({ x: w.x, y: n.y }, { x: e.x, y: s.y });
        mid.elevation = Math.max(0, elev + rand);
        // mid.elevation = 100;

        // if (!completed) {
        if (e.x - mid.x > 1 && s.y - mid.y > 1) {
            // northeast square
            square(n, self.find(e.x, n.y), mid, e, dropoff(variance));
            // southeast square
            square(mid, e, s, self.find(e.x, s.y), dropoff(variance));
            // southwest square
            square(w, mid, self.find(w.x, s.y), s, dropoff(variance));
            // northwest square
            square(self.find(w.x, n.y), n, w, mid, dropoff(variance));
        }
    }

    this.find(0, 0).elevation = Math.random() * 100;
    this.find(this.dim - 1, 0).elevation = Math.random() * 100;
    this.find(0, this.dim - 1).elevation = Math.random() * 100;
    this.find(this.dim - 1, this.dim - 1).elevation = Math.random() * 100;

    square(
        this.find(0, 0),                        // top left
        this.find(this.dim - 1, 0),             // top right
        this.find(0, this.dim - 1),             // bottom left
        this.find(this.dim - 1, this.dim - 1),  // bottom right
        10
    );
};

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
        console.log('starting terrainify iter #' + iteration);
        changed = false;

        this.grid.forEach(cell => {
            let label = cell.availableTerrains.find(terr => terr.func(cell, this)).label;

            if (cell.terrain !== label) {
                changed = true;
                cell.terrain = label;
            }
        });

        iteration++;
    }
};

World.prototype.init = function () {
    let start = Date.now();

    this.generateElevations();
    this.aquifer();
    this.rainfall();
    this.evaporate();

    this.terrainify();

    console.log(`World generated in ${Math.round((Date.now() - start) / 10) / 100} seconds.`)
};

function Cell(x, y) {
    this.x = x;
    this.y = y;
    this.terrain = null;
    this.elevation = 0; // default, will be replaced with something procedural
    this.water = false;

    return this;
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