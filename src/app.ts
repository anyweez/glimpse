'use strict'

import { World } from './world';
import progress from './progress';
import { Renderer, CameraOptions } from './render';

// // note: currently ignored
let renderOptions: CameraOptions = {
    showTerrain: true,
    showWater: true,
    moving: false,
};

let track = progress();
const MAP_DETAIL: number = 8;

window.addEventListener('load', function () {
    track.start([
        'Generating elevations',
        'Filling aquifers',
        'Rainfall',
        'Evaporation',
        'Converting to terrain',
        'Smoothing terrain',
    ]);

    let game = new World(Math.pow(2, MAP_DETAIL) + 1);
    game.init({
        update: track.next.bind(progress)
    }).then(function () {
        // The game takes one step every second
        setInterval(game.cycle.bind(game), 3000);
        setInterval(game.spawnNext.bind(game), 15000);

        let renderer = new Renderer(game, <HTMLCanvasElement>document.getElementById('game'), renderOptions);

        // key listener for settings options
        window.addEventListener('keyup', function (event) {
            let key = event.keyCode;

            if (key === 84) renderer.update({ showTerrain: !renderer.options.showTerrain });
            else if (key === 67) renderer.update({ moving: !renderer.options.moving });
        });
    });
});

