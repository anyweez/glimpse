function colorOf(cell) {
    let r = Math.round(255 * ((100 - cell.elevation) / 100));
    let g = Math.round(255 * (cell.elevation / 100));
    let b = 0;

    return `rgb(${r},${g},${b})`;
}

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
        showWater: false,
        moving: true,
    },

    camera: {
        zoom: 1.7,

        offset: {
            x: 0,
            y: 0,
        },

        transform: {
            x: 0,
            y: 0,
        },

        direction: {
            x: 1,
            y: 0.6,
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
            if (this.camera.transform.x * -1 > pixelX + dimension) return false;
            if (this.camera.transform.y * -1 > pixelY + dimension) return false;

            // upper bound
            if (this.camera.transform.x * -1 + this.camera.dims.width < pixelX) return false;
            if (this.camera.transform.y * -1 + this.camera.dims.height < pixelY) return false;

            return true;
        },
    },

    /**
     * Start animating. Should not be called more than once.
     */
    start: function (map, camera, canvas, options = {}) {
        console.log(`rendering @ zoom=${camera.zoom}`);

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        console.log('canvas size:', canvas.width, canvas.height);

        let context = canvas.getContext('2d');

        this.map = map;
        this.ctx = canvas.getContext('2d');

        // setInterval(() => this.camera.offset.x += 10, 1000);
        setInterval(this._bounce.bind(this), 25);
        // this._bounce();

        window.requestAnimationFrame(this._renderFrame.bind(this));
        console.log('rendering started');
    },

    _bounce: function () {
        // If disabled or in a background tab, don't advance. Don't advance in background
        // tab because it'll get out of sync with animation (which only occurs in the foreground).
        if (!this.options.moving || document.hidden) return;

        let targetX = this.camera.direction.x + this.camera.transform.x;
        let targetY = this.camera.direction.y + this.camera.transform.y;

        // lower limit
        if (targetX > BOUNCE_BORDER && this.camera.direction.x > 0) this.camera.direction.x *= -1;
        if (targetY > BOUNCE_BORDER && this.camera.direction.y > 0) this.camera.direction.y *= -1;

        // upper limit
        // todo: why these magic 100's??
        if (targetX * -1 > this.camera.dims.primary / this.camera.zoom - BOUNCE_BORDER - 100) this.camera.direction.x *= -1;
        if (targetY * -1 > this.camera.dims.primary / this.camera.zoom + BOUNCE_BORDER + 100) this.camera.direction.y *= -1;

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
        self.ctx.clearRect(
            this.camera.transform.x * -1,
            this.camera.transform.y * -1,
            this.camera.dims.width,
            this.camera.dims.height
        );

        // apply and store the translation
        if (this.camera.offset.x !== 0 || this.camera.offset.y !== 0) {
            this.ctx.translate(this.camera.offset.x, this.camera.offset.y);

            this.camera.transform.x += this.camera.offset.x;
            this.camera.transform.y += this.camera.offset.y;

            this.camera.offset.x = 0;
            this.camera.offset.y = 0;
        }

        // render the visible items
        this.map.grid.filter(this.camera.visible.bind(this)).forEach(function (cell) {
            if (self.options.showWater && cell.water) self.ctx.fillStyle = 'blue';
            else self.ctx.fillStyle = colorOf(cell);

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