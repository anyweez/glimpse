"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Renderer = void 0;
var terrain_1 = require("../generator/terrain");
var color = {
    elevation: function (cell) {
        var r = Math.round(255 * ((100 - cell.elevation) / 100));
        var g = Math.round(255 * (cell.elevation / 100));
        var b = 0;
        return "rgb(" + r + "," + g + "," + b + ")";
    },
    terrain: function (cell) {
        var color = terrain_1.colorize(cell);
        // color.a = (cell.populations.length > 1) ? 0.25 : 1;
        return "rgba(" + color.r + "," + color.g + "," + color.b + "," + color.a + ")";
    }
};
var BOUNCE_BORDER = 25;
var Renderer = /** @class */ (function () {
    function Renderer(map, canvas, options) {
        this.canvas = null;
        this.context = null;
        this.options = {
            showTerrain: true,
            showWater: true,
            moving: false,
        };
        // Camera settings will be updated in the constructor. Semi-reasonable default here but
        // shouldn't really be used without further configuration (via constructor).
        this.camera = {
            zoom: 1.0,
            direction: {
                x: 6,
                y: 4,
            },
            offset: {
                x: 0,
                y: 0,
            },
            transform: {
                x: 0,
                y: 0,
            },
            dims: {
                width: 600,
                height: 400,
                primary: 400,
            },
        };
        this.world = map;
        this.canvas = canvas;
        this.context = canvas.getContext('2d');
        this.options = options;
        // maybe a good idea?
        this.camera.zoom = map.dim / 50;
        this.camera.direction.x /= this.camera.zoom;
        this.camera.direction.y /= this.camera.zoom;
        this.camera.dims.width = window.innerWidth;
        this.camera.dims.height = window.innerHeight;
        this.camera.dims.primary = Math.min(window.innerWidth, window.innerHeight),
            console.log("rendering @ zoom=" + this.camera.zoom);
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        if (this.options.moving)
            setInterval(this._bounce.bind(this), 25);
        window.requestAnimationFrame(this._renderFrame.bind(this));
        console.log('rendering started');
    }
    /**
     * Check if the provided cell is visible or not.
     */
    Renderer.prototype.visible = function (cell) {
        var dimension = this.camera.zoom * this.camera.dims.primary / this.world.dim;
        var pixelX = cell.x * dimension;
        var pixelY = cell.y * dimension;
        // lower bound
        if (this.camera.transform.x > pixelX + dimension)
            return false;
        if (this.camera.transform.y > pixelY + dimension)
            return false;
        // upper bound
        if (this.camera.transform.x + this.camera.dims.width < pixelX)
            return false;
        if (this.camera.transform.y + this.camera.dims.height < pixelY)
            return false;
        return true;
    };
    Renderer.prototype._bounce = function () {
        // If disabled or in a background tab, don't advance. Don't advance in background
        // tab because it'll get out of sync with animation (which only occurs in the foreground).
        if (!this.options.moving || document.hidden)
            return;
        var targetX = this.camera.direction.x + this.camera.transform.x + this.camera.offset.x;
        var targetY = this.camera.direction.y + this.camera.transform.y + this.camera.offset.y;
        // lower limit
        if (targetX < -1 * BOUNCE_BORDER && this.camera.direction.x < 0)
            this.camera.direction.x *= -1;
        if (targetY < -1 * BOUNCE_BORDER && this.camera.direction.y < 0)
            this.camera.direction.y *= -1;
        // upper limit
        if (targetX > this.camera.dims.primary * this.camera.zoom - this.camera.dims.width + BOUNCE_BORDER)
            this.camera.direction.x *= -1;
        if (targetY > this.camera.dims.primary * this.camera.zoom - this.camera.dims.height + BOUNCE_BORDER)
            this.camera.direction.y *= -1;
        this.camera.offset.x += this.camera.direction.x;
        this.camera.offset.y += this.camera.direction.y;
    };
    /**
     * Renders an individual frame. The goal is to call this function 60 times per second.
     */
    Renderer.prototype._renderFrame = function () {
        var self = this;
        var dimension = Math.floor(this.camera.zoom * this.camera.dims.primary / this.world.dim);
        // clear the canvas
        self.context.clearRect(this.camera.transform.x, this.camera.transform.y, this.camera.dims.width, this.camera.dims.height);
        // apply and store the translation
        if (this.camera.offset.x !== 0 || this.camera.offset.y !== 0) {
            // translate moves in the opposite direction vs what i would expect (as someone not great at
            // linear algebra). invert directions here so that i can use intuitive directions elsewhere.
            this.context.translate(-1 * this.camera.offset.x, -1 * this.camera.offset.y);
            this.camera.transform.x += this.camera.offset.x;
            this.camera.transform.y += this.camera.offset.y;
            this.camera.offset.x = 0;
            this.camera.offset.y = 0;
        }
        // render the visible items
        this.world.grid.filter(this.visible.bind(this)).forEach(function (cell) {
            if (self.options.showTerrain)
                self.context.fillStyle = color.terrain(cell);
            else
                self.context.fillStyle = color.elevation(cell);
            self.context.fillRect(cell.x * dimension + 1, cell.y * dimension + 1, dimension - 2, dimension - 2);
        });
        window.requestAnimationFrame(this._renderFrame.bind(this));
    };
    Renderer.prototype.update = function (options) {
        for (var prop in options) {
            this.options[prop] = options[prop];
        }
    };
    return Renderer;
}());
exports.Renderer = Renderer;
