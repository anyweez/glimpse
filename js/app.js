'use strict'

let world = require('./world');
let renderer = require('./render');

let renderOptions = {
    showWater: false,
    useCamera: true,
};

let camera = {
    zoom: 2.0,

    offset: {
        x: 0,
        y: 0,
    },
    dims: {
        width: window.innerWidth,
        height: window.innerHeight,
    },

    visible(cell) {
        // let tl = 
        return true;
    },
}

window.addEventListener('load', function () {
    let game = new world.World(90);
    game.init();

    renderer.start(game, camera, document.getElementById('game'), renderOptions);

    // key listener
    window.addEventListener('keyup', function (event) {
        let key = event.keyCode;

        if (key === 87) { // 'w'
            renderer.update({
                showWater: !renderer.options.showWater,
            });

            if (renderer.options.showWater) console.log('showing water');
            else console.log('hiding water');
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

