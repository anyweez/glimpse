'use strict'
/**
 * Tests for World class.
 */

const World = require('../dist/generator/world').World;
const Terrain = require('../dist/generator/terrain').Terrain;

let expect = require('expect.js');
let dims = {
    small: Math.pow(2, 3) + 1,
    medium: Math.pow(2, 5) + 1,
    large: Math.pow(2, 8) + 1,
};

/**
 * Simple object for enabling or disabling console output.
 */
let output = {
    log: console.log,

    disable() {
        console.log = function () { };
    },

    enable() {
        console.log = this.log;
    },
};

describe('World', function () {
    /**
     * Make sure worlds are composed of the correct number of cells when the constructor
     * finishes running.
     */
    it('should generate an nxn grid', function () {
        let small = new World({ dim: dims.small });
        let medium = new World({ dim: dims.medium });
        let large = new World({ dim: dims.large });

        expect(small.meta.dim).to.be.equal(dims.small);
        expect(small.grid.length).to.be.equal(dims.small * dims.small);

        expect(medium.meta.dim).to.be.equal(dims.medium);
        expect(medium.grid.length).to.be.equal(dims.medium * dims.medium);

        expect(large.meta.dim).to.be.equal(dims.large);
        expect(large.grid.length).to.be.equal(dims.large * dims.large);
    });

    it('should be able to find existing neighbors', function () {
        const world = new World({ dim: dims.medium });

        for (let y = 1; y < world.meta.dim - 1; y++) {
            for (let x = 1; x < world.meta.dim - 1; x++) {
                const neighbors = world.neighbors({ x, y });

                expect(neighbors).to.have.length(4);
            }
        }
    });

    it('should return the right neighbor count edges', function () {
        let world = new World({ dim: dims.medium });

        for (let y = 0; y < world.meta.dim; y++) {
            for (let x = 0; x < world.meta.dim; x++) {
                let neighbors = world.neighbors({ x, y });

                let expected = 4;

                if (x === 0) expected--;
                if (x === world.meta.dim - 1) expected--;
                if (y === 0) expected--;
                if (y === world.meta.dim - 1) expected--;

                expect(neighbors).to.have.length(expected);
            }
        }
    });

    it('should have terrain assigned to every cell', function (done) {
        let world = new World({ dim: dims.small });

        output.disable();

        world.init({
            update: function () { },
        }).then(function () {
            output.enable();

            // Check that every cell has a valid terrain type.
            world.grid.forEach(cell => {
                expect(Object.values(Terrain)).to.contain(cell.terrain);
            });

            done();
        });
    });
});