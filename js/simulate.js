let world = require('./world');
/* Constants */
const MAP_DETAIL = 2;

window.addEventListener('load', function () {
    console.log('loaded');

    let sim = new world.World(Math.pow(2, MAP_DETAIL) + 1);
    sim.init({
        update: function () {}
    }).then(function () {
        sim.spawnNext();
        setInterval(sim.cycle.bind(sim), 1000);
    });
});