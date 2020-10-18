'use strict'

import * as ini from 'ini';
import { fs } from 'mz';

import { World } from './world';
import progress from './progress';
import file_format from './file_format';

const MAP_DIMENSION: number = 10;

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
    const config = ini.parse( fs.readFileSync('world.ini', 'utf-8') );

    let track = progress();
    
    const game = new World({
        dim:                !isNaN( parseInt(config.meta.world_size, 10) )
                                ? Math.pow(2, parseInt(config.meta.world_size)) + 1 
                                : Math.pow(2, MAP_DIMENSION) + 1,
        altitudeVariance:   parseInt(config.meta.altitude_variance) || 20.0,
        aquiferDepth:       parseInt(config.meta.aquifer_depth) || 35,
    });

    console.log(`Generating world based on properties:`);
    console.log(game.meta);

    console.log()
    console.log()
    
    track.start([
        'Generating elevations',
        'Filling aquifers',
        'Rainfall',
        'Evaporation',
        'Converting to terrain',
        'Smoothing terrain',
    ]);
    
    await game.init({
        update: track.next.bind(progress)
    });

    const filename = `worlds/${random_name(10)}.json`;
    console.log(`Saving world to '${filename}'...`)

    await file_format.write(filename, game);
};

generate();