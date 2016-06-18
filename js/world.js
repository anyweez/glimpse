
function World(dim) {
    this.dim = dim;
    this.grid = [];

    for (let y = 0; y < dim; y++) {
        for (let x = 0; x < dim; x++) {
            this.grid.push(new Cell(x, y));
        }
    }

    return this;
}

World.prototype.find = function (x, y) {
    // todo: be smarter about wraparound values?
    if (x < 0 || x >= this.dim) return { x: x, y: y, elevation: 50 };
    if (y < 0 || y >= this.dim) return { x: x, y: y, elevation: 50 };

    return this.grid[y * this.dim + x];
};

World.prototype.init = function () {
    let self = this;

    function midpoint(tl, br) {
        return self.find( Math.round((tl.x + br.x) / 2), Math.round((tl.y + br.y) / 2) );
    }

    function square(tl, tr, bl, br, variance) {
        // console.log('square');
        let elev = (tl.elevation + tr.elevation + bl.elevation + br.elevation) / 4;
        let rand = (Math.random() * 10) - 5;

        let mid = midpoint(tl, br);
        // this.get(x, y).elevation = Math.max(0, variance);
        mid.elevation = 100;

        // Keep working on smaller and smaller squares
        if (br.x - mid.x > 1 && br.y - mid.y > 1) {
            // left diamond
            diamond(tl, mid, bl, self.find(mid.x - (mid.x - tl.x) * 2, mid.y), variance - 1);
            // top diamond
            diamond(self.find(mid.x,  mid.y - (mid.y - tl.y) * 2), tr, mid, tl, variance - 1);
            // right diamond
            diamond(tr, self.find(mid.x + (tr.x - mid.x) * 2, mid.y), br, mid, variance - 1);
            // south diamond
            diamond(mid, br, self.find(mid.x, mid.y + (bl.y - mid.y) * 2), bl, variance - 1);
        } else {
            // left diamond
            diamond(tl, mid, bl, self.find(mid.x - 2, mid.y), variance - 1, true);
            // top diamond
            diamond(self.find(mid.x, mid.y - 2), tr, mid, tl, variance - 1, true);
            // right diamond
            diamond(tr, self.find(mid.x + 2, mid.y), br, mid, variance - 1, true);
            // bottom diamond
            diamond(mid, br, self.find(mid.x, mid.y + 2), bl, variance - 1, true);
        }
    }

    function diamond(n, e, s, w, variance, completed = false) {
        // console.log('diamond');
        let elev = (n.elevation + e.elevation + s.elevation + w.elevation) / 4;
        let rand = (Math.random() * 10) - 5;

        let mid = midpoint( {x: w.x, y: n.y}, {x: e.x, y: s.y} );
        // console.log(`tl: (${w.x}, ${n.y}), br: (${e.x}, ${s.y}), mid: (${mid.x}, ${mid.y})`);
        // if (completed) mid.elevation = 100;
        // else mid.elevation = 50;
        mid.elevation = 100;
        // mid.elevation = (completed) ? 200 : 100;

        // console.log(`xgap: ${e.x - w.x}, ygap: ${s.y - n.y}`)
        
        if (e.x - mid.x > 1 && s.y - mid.y > 1) {
            // northeast square
            square(n, self.find(e.x, n.y), mid, e, variance - 1);
            // southeast square
            square(mid, e, s, self.find(e.x, s.y), variance - 1);
            // southwest square
            square(w, mid, self.find(w.x, s.y), s, variance - 1);
            // northwest square
            square(self.find(w.x, n.y), n, mid, w, variance - 1);
        }
    }

    this.find(0, 0).elevation = 100;
    this.find(this.dim - 1, 0).elevation = 100;
    this.find(0, this.dim - 1).elevation = 100;
    this.find(this.dim - 1, this.dim - 1).elevation = 100;

    square(
        this.find(0, 0),                        // top left
        this.find(this.dim - 1, 0),             // top right
        this.find(0, this.dim - 1),             // bottom left
        this.find(this.dim - 1, this.dim - 1),  // bottom right
        10
    );
};

function Cell(x, y) {
    this.x = x;
    this.y = y;
    this.terrain = this.availableTerrains[Math.floor(Math.random() * this.availableTerrains.length)];
    // this.elevation = Math.round(Math.random() * 100);
    this.elevation = 10;

    return this;
}

Cell.prototype.availableTerrains = ['grass', 'dirt', 'water'];

module.exports = {
    World: World,
};