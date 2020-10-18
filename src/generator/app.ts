'use strict'

import { World } from './world';
import progress from './progress';
import file_format from './file_format';

const MAP_DETAIL: number = 8;

/**
 * Generate the world.
 */
const generate = async () => {
    let track = progress();

    track.start([
        'Generating elevations',
        'Filling aquifers',
        'Rainfall',
        'Evaporation',
        'Converting to terrain',
        'Smoothing terrain',
    ]);
    
    const game = new World(Math.pow(2, MAP_DETAIL) + 1);
    
    await game.init({
        update: track.next.bind(progress)
    });

    await file_format.write('world.json', game);
};

generate();