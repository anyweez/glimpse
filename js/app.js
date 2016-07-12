'use strict'

let world = require('./world');
let renderer = require('./render');
let progress = require('./progress')();

// note: currently ignored
let renderOptions = {
    showWater: false,
    useCamera: true,
};

const MAP_DETAIL = 3;

window.addEventListener('load', function () {
    progress.start([
        'Generating elevations',
        'Filling aquifers',
        'Rainfall',
        'Evaporation',
        'Converting to terrain',
        'Smoothing terrain',
    ]);

    let game = new world.World(Math.pow(2, MAP_DETAIL) + 1);
    game.init({
        update: progress.next.bind(progress)
    }).then(function () {
        // The game takes one step every second
        setInterval(game.cycle.bind(game), 1000);
        setInterval(game.spawnNext.bind(game), 5000);

        renderer.start(game, document.getElementById('game'), renderOptions);

        // key listener for settings options
        window.addEventListener('keyup', function (event) {
            let key = event.keyCode;

            if (key === 84) { // 't'
                renderer.update({ showTerrain: !renderer.options.showTerrain });
            } else if (key === 67) { // 'c'
                renderer.update({ moving: !renderer.options.moving });
            } else if (key === 187) {
                renderer.changeCamera({ zoom: renderer.camera.zoom + 0.1 });
            } else if (key === 189) {
                renderer.changeCamera({ zoom: renderer.camera.zoom - 0.1 });
            }
        })
    })
});

