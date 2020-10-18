'use strict'

import { World } from './world';
import progress from './progress';
import file_format from './file_format';

const MAP_DETAIL: number = 8;

const random_name = (length : number) => {
    const chars = 'abcdefghijklmnopqrstuvwxyz';
    const selected = [];

    for (let i = 0; i < length; i++) {
        const idx = Math.round( Math.random() * chars.length );

        selected.push( chars[idx] );
    }

    return selected.join('');
}

/**
 * Generate the world and save to a randomly generated filename in the 'worlds/' subdirectory.
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

    const filename = `worlds/${random_name(10)}.json`;
    console.log(`Saving world to '${filename}'...`)

    await file_format.write(filename, game);
};

generate();