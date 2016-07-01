
let color = {
    elevation: function (cell) {
        let r = Math.round(255 * ((100 - cell.elevation) / 100));
        let g = Math.round(255 * (cell.elevation / 100));
        let b = 0;

        return `rgb(${r},${g},${b})`;
    },

    terrain: function (cell) {
        if (cell.terrain === 'water') {
            if (cell.elevation < 5) return '#1E4F6E';
            else if (cell.elevation < 15) return '#457B9D'
            else return '#70A2C2';
        }
        if (cell.terrain === 'sand') return '#F8FC6F';
        if (cell.terrain === 'grass') {
            if (cell.elevation < 30) return '#77CF3C';
            else if (cell.elevation < 70) return '#61B329';
            else return '#438A13';
        }
        if (cell.terrain === 'rock') {
            if (cell.elevation > 98) return '#E8E8E8'; // snow
            else return '#A6A2A2';
        }
    }
};

let fps = {
    total: 0,
};

function count_frame() {
    let sec = Math.floor(Date.now() / 1000);
    if (sec in fps) fps[sec] += 1;
    else fps[sec] = 1;

    fps.total += 1;

    if (fps.total % 1000 === 0) console.log(fps);
}

const BOUNCE_BORDER = 25;

module.exports = {
    options: {
        showTerrain: true,
        moving: true,
    },

    camera: {
        zoom: 1.6,

        // Assume zoom @ 1.0
        offset: {
            x: 0,
            y: 0,
        },

        // Assume zoom @ 1.0
        transform: {
            x: 0,
            y: 0,
        },

        direction: {
            x: -4,
            y: -2.4,
        },

        dims: {
            width: window.innerWidth,
            height: window.innerHeight,
            primary: Math.min(window.innerWidth, window.innerHeight),
        },

        // todo: identify which cells are visible
        visible(cell) {
            let dimension = this.camera.zoom * this.camera.dims.primary / this.map.dim;

            let pixelX = cell.x * dimension;
            let pixelY = cell.y * dimension;

            // lower bound
            if (this.camera.transform.x > pixelX + dimension) return false;
            if (this.camera.transform.y > pixelY + dimension) return false;

            // upper bound
            if (this.camera.transform.x + this.camera.dims.width < pixelX) return false;
            if (this.camera.transform.y + this.camera.dims.height < pixelY) return false;

            return true;
        },
    },

    /**
     * Start animating. Should not be called more than once.
     */
    start: function (map, canvas, options = {}) {
        // maybe a good idea?
        this.camera.zoom = map.dim / 50;
        // this.camera.zoom = 1.0;
        this.camera.direction.x /= this.camera.zoom;
        this.camera.direction.y /= this.camera.zoom;

        console.log(`rendering @ zoom=${this.camera.zoom}`);

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        console.log('canvas size:', canvas.width, canvas.height);

        this.map = map;
        this.ctx = canvas.getContext('2d');

        setInterval(this._bounce.bind(this), 25);

        window.requestAnimationFrame(this._renderFrame.bind(this));
        console.log('rendering started');
    },

    _bounce: function () {
        // If disabled or in a background tab, don't advance. Don't advance in background
        // tab because it'll get out of sync with animation (which only occurs in the foreground).
        if (!this.options.moving || document.hidden) return;

        let targetX = this.camera.direction.x + this.camera.transform.x + this.camera.offset.x;
        let targetY = this.camera.direction.y + this.camera.transform.y + this.camera.offset.y;

        // lower limit
        if (targetX < -1 * BOUNCE_BORDER && this.camera.direction.x < 0) this.camera.direction.x *= -1;
        if (targetY < -1 * BOUNCE_BORDER && this.camera.direction.y < 0) this.camera.direction.y *= -1;

        // upper limit
        if (targetX > this.camera.dims.primary * this.camera.zoom - this.camera.dims.width + BOUNCE_BORDER) this.camera.direction.x *= -1;
        if (targetY > this.camera.dims.primary * this.camera.zoom - this.camera.dims.height + BOUNCE_BORDER) this.camera.direction.y *= -1;

        this.camera.offset.x += this.camera.direction.x;
        this.camera.offset.y += this.camera.direction.y;
    },

    /**
     * Renders an individual frame.
     */
    _renderFrame: function () {
        let self = this;
        let dimension = this.camera.zoom * this.camera.dims.primary / this.map.dim;

        count_frame();

        // clear the canvas
        // todo: zoom multipliers
        self.ctx.clearRect(
            this.camera.transform.x,
            this.camera.transform.y,
            this.camera.dims.width,
            this.camera.dims.height
        );

        // apply and store the translation
        if (this.camera.offset.x !== 0 || this.camera.offset.y !== 0) {
            // translate moves in the opposite direction vs what i would expect (as someone not great at
            // linear algebra). invert directions here so that i can use intuitive directions elsewhere.
            this.ctx.translate(-1 * this.camera.offset.x, -1 * this.camera.offset.y);

            this.camera.transform.x += this.camera.offset.x;
            this.camera.transform.y += this.camera.offset.y;

            this.camera.offset.x = 0;
            this.camera.offset.y = 0;
        }

        // render the visible items
        this.map.grid.filter(this.camera.visible.bind(this)).forEach(function (cell) {
            if (self.options.showTerrain) self.ctx.fillStyle = color.terrain(cell)
            else self.ctx.fillStyle = color.elevation(cell);

            self.ctx.fillRect(cell.x * dimension + 1, cell.y * dimension + 1, dimension - 2, dimension - 2);
        });

        window.requestAnimationFrame(this._renderFrame.bind(this));
    },

    changeCamera: function (options) {
        for (let prop in options) {
            this.camera[prop] = options[prop];
        }
    },

    update: function (opts) {
        for (let prop in opts) {
            this.options[prop] = opts[prop];
        }
    },
};