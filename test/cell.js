'use strict'
/**
 * Tests for World class.
 */

import { World, Cell } from '../_out/world';
import { Population } from '../_out/species';

let expect = require('expect.js');

const WORLD_DIM = Math.pow(2, 4) + 1;

let output = {
    log: console.log,

    disable() {
        console.log = function () { };
    },

    enable() {
        console.log = this.log;
    },
};

describe('Cell', function () {
    this.timeout(5000);

    let world = null;
    beforeEach(function () {
        output.disable();
        world = new World(WORLD_DIM)

        return world.init({
            update: function () { },
        }).then(function () {
            output.enable();
        });
    });

    it('should have appropriate fields set @ world initialization', function () {
        for (let i = 0; i < world.grid.length; i++) {
            let cell = world.grid[i];

            expect(cell.x).to.be.a.number;
            expect(cell.x).to.be.lessThan(world.dim);
            expect(cell.y).to.be.a.number;
            expect(cell.y).to.be.lessThan(world.dim);

            expect(['grass', 'water', 'sand', 'rock']).to.contain(cell.terrain);
        }
    });

    it('can spawn and remove a population', function () {
        let cell = world.find(1, 1);
        let pop = new Population(cell);

        expect(cell.populations).to.have.length(2);
        expect(pop.home).to.be.equal(cell);

        output.disable();
        pop.extinguish();
        output.enable();

        expect(cell.populations).to.have.length(1);
        expect(pop.home).to.be.equal(null);
    });

    it('spawning the same population twice should throw an exception', function () {
        let cell = world.find(1, 1);
        let pop = new Population(cell);

        try {
            // Second spawn (first is in the Population constructor)
            cell.spawn(pop);

            // Fail if an exception isn't thrown.
            // todo: check if there's a clearer way to do this.
            expect(true).to.be.equal(false);
        } catch (Exception) {}
    });
    // spawn()'ing after a pop has been added should throw an exception

});