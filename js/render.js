
let color = {
    elevation: function (cell) {
        let r = Math.round(255 * ((100 - cell.elevation) / 100));
        let g = Math.round(255 * (cell.elevation / 100));
        let b = 0;

        return `rgb(${r},${g},${b})`;
    },

    terrain: function (cell) {
        let color = { r: 0, g: 0, b: 0 };

        if (cell.terrain === 'water') {
            if (cell.elevation < 5) color = {r: 30, g: 79, b: 110};
            else if (cell.elevation < 15) color = {r: 69, g: 123, b: 157};
            else color = {r: 112, g:162, b:194};
        }
        else if (cell.terrain === 'sand') color = {r: 248, g: 252, b: 111};
        else if (cell.terrain === 'grass') {
            if (cell.elevation < 30) color = {r: 119, g: 207, b: 60};
            else if (cell.elevation < 70) color = {r: 97, g: 179, b: 41};
            else color = {r: 67, g: 138, b: 19};
        }
        else if (cell.terrain === 'rock') {
            if (cell.elevation > 98) color = {r: 232, g: 232, b: 232}; // snow
            else color = {r: 166, g: 162, b: 162};
        }

        // if (cell.populations.length > 1) {
        //     color.r = Math.round(color.r * 1.5);
        //     color.g = Math.round(color.g * 1.5);
        //     color.b = Math.round(color.b * 1.5);
        // }

        color.a = (cell.populations.length > 1) ? 0.25 : 1;

        return `rgba(${color.r},${color.g},${color.b},${color.a})`;
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
        moving: false,
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
            x: -8,
            y: -6,
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
        let dimension = Math.floor(this.camera.zoom * this.camera.dims.primary / this.map.dim);

        // count_frame();

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