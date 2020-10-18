"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
var mz_1 = require("mz");
var pngjs_1 = require("pngjs");
var file_format_1 = require("../generator/file_format");
var terrain_1 = require("../generator/terrain");
var filename = process.argv[2];
var CELL_DIMENSION_IN_PIXELS = 4;
var color = function (name) {
    if (name === 'SHALLOW_WATER')
        return { r: 112, g: 162, b: 194, a: 0 };
    if (name === 'WATER')
        return { r: 69, g: 123, b: 157, a: 0 };
    if (name === 'DEEP_WATER')
        return { r: 30, g: 79, b: 110, a: 0 };
    if (name === 'GRASS')
        return { r: 119, g: 207, b: 60, a: 0 };
    if (name === 'SAND')
        return { r: 248, g: 252, b: 111, a: 0 };
    if (name === 'ROCK')
        return { r: 166, g: 162, b: 162, a: 0 };
    return { r: 255, g: 0, b: 0, a: 0 };
};
var render = function (world, fn, filename) {
    var img = new pngjs_1.PNG({
        width: world.dim * CELL_DIMENSION_IN_PIXELS,
        height: world.dim * CELL_DIMENSION_IN_PIXELS,
        colorType: 6,
    });
    // Iterate over all PIXELS in the image. Cells in the World may be rendered in
    // more than one pixel (defined via CELL_DIMENSION_IN_PIXELS).
    for (var y = 0; y < img.height; y++) {
        for (var x = 0; x < img.width; x++) {
            var idx = (img.width * y + x) << 2; // 4 bytes per pixel
            var proj_x = Math.floor(x / CELL_DIMENSION_IN_PIXELS);
            var proj_y = Math.floor(y / CELL_DIMENSION_IN_PIXELS);
            var cell = world.find(proj_x, proj_y);
            // Call user-provided function to get the color for the specified cell.
            var c = fn(cell);
            img.data[idx] = c.r;
            img.data[idx + 1] = c.g;
            img.data[idx + 2] = c.b;
            img.data[idx + 3] = 255;
        }
    }
    img.pack().pipe(mz_1.fs.createWriteStream(filename));
};
var render_terrain = function (cell) {
    var terrain = cell.terrain, elevation = cell.elevation;
    var c = (terrain === terrain_1.Terrain.WATER && elevation < 5) ? color('DEEP_WATER') :
        (terrain === terrain_1.Terrain.WATER && elevation < 15) ? color('WATER') :
            (terrain === terrain_1.Terrain.WATER) ? color('SHALLOW_WATER') :
                (terrain === terrain_1.Terrain.GRASS) ? color('GRASS') :
                    (terrain === terrain_1.Terrain.SAND) ? color('SAND') :
                        (terrain === terrain_1.Terrain.ROCK) ? color('ROCK') :
                            { r: 255, g: 0, b: 0, a: 0 }; // bright red, error color
    return c;
};
var render_elevation = function (cell) {
    return {
        r: cell.elevation * 2.55,
        g: cell.elevation * 2.55,
        b: cell.elevation * 2.55,
        a: 255,
    };
};
var run = function () { return __awaiter(void 0, void 0, void 0, function () {
    var world;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, file_format_1.default.read(filename)];
            case 1:
                world = _a.sent();
                render(world, render_terrain, 'world_terrain.png');
                render(world, render_elevation, 'world_elevation.png');
                return [2 /*return*/];
        }
    });
}); };
run();
