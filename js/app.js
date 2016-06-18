'use strict'

let world = require('./world');
let render = require('./render');

window.addEventListener('load', function () {
    let game = new world.World(76);
    game.init();

    render(game, document.getElementById('game'));
});