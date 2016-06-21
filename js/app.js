'use strict'

let world = require('./world');
let renderer = require('./render');

// note: currently ignored
let renderOptions = {
    showWater: false,
    useCamera: true,
};

const MAP_DETAIL = 8;

window.addEventListener('load', function () {
    let game = new world.World(Math.pow(2, MAP_DETAIL) + 1);
    game.init();

    renderer.start(game, document.getElementById('game'), renderOptions);

    // key listener
    window.addEventListener('keyup', function (event) {
        let key = event.keyCode;

        if (key === 84) { // 't'
            renderer.update({
                showTerrain: !renderer.options.showTerrain,
            });

            if (renderer.options.showTerrain) console.log('showing terrain');
            else console.log('hiding terrain');
        } else if (key === 67) { // 'c'
            // renderer.update({
            //     useCamera: renderer.options.useCamera,
            // });
            renderer.update({
                moving: !renderer.options.moving,
            });
        } else if (key === 187) {
            renderer.changeCamera({
                zoom: renderer.camera.zoom + 0.1,
            });
        } else if (key === 189) {
            renderer.changeCamera({
                zoom: renderer.camera.zoom - 0.1,
            });
        }

        console.log(key);
    })

});

