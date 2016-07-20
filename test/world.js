'use strict'
/**
 * Tests for World class.
 */

import { World } from '../_out/world';

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
    // Increase timeout duration since I need to initialize the world for this one.
    this.timeout(5000);

    /**
     * Make sure worlds are composed of the correct number of cells when the constructor
     * finishes running.
     */
    it('should generate an nxn grid', function () {
        let small = new World(dims.small);
        let medium = new World(dims.medium);
        let large = new World(dims.large);

        expect(small.dim).to.be.equal(dims.small);
        expect(small.grid.length).to.be.equal(dims.small * dims.small);

        expect(medium.dim).to.be.equal(dims.medium);
        expect(medium.grid.length).to.be.equal(dims.medium * dims.medium);

        expect(large.dim).to.be.equal(dims.large);
        expect(large.grid.length).to.be.equal(dims.large * dims.large);
    });


    it('should be able to randomly spawn populations', function () {
        let world = new World(dims.large);

        output.disable();
        for (let i = 0; i < 250; i++) {
            let pop = world.spawnNext();

            expect(pop.home).to.not.be(null);
            expect(pop.home.x).to.be.greaterThan(-1);
            expect(pop.home.x).to.be.lessThan(dims.large);
            expect(pop.home.y).to.be.greaterThan(-1);
            expect(pop.home.y).to.be.lessThan(dims.large);
        }
        output.enable();
    });

    it('should be able to find existing neighbors', function () {
        let world = new World(dims.medium);

        for (let y = 1; y < world.dim - 1; y++) {
            for (let x = 1; x < world.dim - 1; x++) {
                let target = {
                    x: x,
                    y: y,
                    elevation: 1.0,
                };

                let neighbors = world.neighbors(target);

                expect(neighbors).to.have.length(4);
                neighbors.forEach(neighbor => {
                    // Check to make sure these are real cells (not locations) by determining whether
                    // they have a Cell-only field.
                    expect(neighbor).to.have.property('populations');
                })
            }
        }

    });

    it('should return the right neighbor count edges', function () {
        let world = new World(dims.medium);

        for (let y = 0; y < world.dim; y++) {
            for (let x = 0; x < world.dim; x++) {
                let neighbors = world.neighbors({
                    x: x,
                    y: y,
                    elevation: 1.0,
                });

                let expected = 4;

                if (x === 0) expected--;
                if (x === world.dim - 1) expected--;
                if (y === 0) expected--;
                if (y === world.dim - 1) expected--;

                expect(neighbors).to.have.length(expected);
            }
        }
    });

    it('should be able to find existing and simulated cells', function () {
        let world = new World(dims.medium);

        for (let y = -1; y < world.dim + 1; y++) {
            for (let x = -1; x < world.dim + 1; x++) {
                let loc = world.find(x, y);

                if (x < 0 || y < 0 || x === world.dim || y === world.dim) {
                    expect(loc).to.not.have.property('populations');
                } else {
                    expect(loc).to.have.property('populations');
                }

                expect(loc.x).to.equal(x);
                expect(loc.y).to.equal(y);
            }
        }
    });

    it('should have terrain assigned to every cell', function (done) {
        let world = new World(dims.small);
        output.disable();
        world.init({
            update: function () { },
        }).then(function () {
            output.enable();

            world.grid.forEach(cell => {
                expect(['grass', 'water', 'sand', 'rock']).to.contain(cell.terrain);
            });

            done();
        });
    });


    it('should have sunshine in every tile', function (done) {
        let world = new World(dims.small);

        output.disable();
        world.init({
            update: function () { },
        }).then(function () {
            output.enable();

            world.grid.forEach(cell => {
                expect(cell.populations).to.have.length(1);
                expect(cell.populations[0].features.type).to.be.equal('energy');
            });

            done();
        });
    });

    it('should properly handle extinguishing populations @ world level', function (done) {
        let world = new World(dims.small);

        output.disable();
        world.init({
            update: function () { },
        }).then(function () {
            let baseCount = world.populations.length;
            let pop = world.spawnNext();


            // Spawning a population increases the world count by one
            expect(world.populations).to.have.length(baseCount + 1);

            pop.extinguish();
            output.enable();

            expect(pop.home).to.be.equal(null);
            expect(world.populations).to.have.length(baseCount);
            expect(world.extinctions).to.be.equal(1);

            done();
        })
    });
});