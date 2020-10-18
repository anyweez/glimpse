import { fs } from 'mz';
import { PNG } from 'pngjs';
import file_format from '../generator/file_format';
import { World, Cell } from '../generator/world';
import { Terrain } from '../generator/terrain';

const filename = process.argv[2];

const CELL_DIMENSION_IN_PIXELS = 4;

interface Color {
    r: number
    g: number
    b: number
    a: number
}

const render = (world : World, fn : (cell : Cell) => Color, filename : string) => {
    const img = new PNG({
        width: world.dim * CELL_DIMENSION_IN_PIXELS,
        height: world.dim * CELL_DIMENSION_IN_PIXELS,
        colorType: 6, // RGBA
    });

    // Iterate over all PIXELS in the image. Cells in the World may be rendered in
    // more than one pixel (defined via CELL_DIMENSION_IN_PIXELS).
    for (let y = 0; y < img.height; y++) {
        for (let x = 0; x < img.width; x++) {
            const idx = (img.width * y + x) << 2;   // 4 bytes per pixel

            const proj_x = Math.floor(x / CELL_DIMENSION_IN_PIXELS);
            const proj_y = Math.floor(y / CELL_DIMENSION_IN_PIXELS);

            const cell = world.find(proj_x, proj_y) as Cell;
            // Call user-provided function to get the color for the specified cell.
            const c = fn(cell);

            img.data[idx] = c.r;
            img.data[idx + 1] = c.g;
            img.data[idx + 2] = c.b;
            img.data[idx + 3] = 255;    
        }
    }

    img.pack().pipe(fs.createWriteStream(filename));
}

const render_terrain = (cell : Cell) : Color => {
    const TerrainColors = {
        'WATER_SHALLOW':    { r: 112, g: 162, b: 194, a: 0 },
        'WATER':            { r: 69, g: 123, b: 157, a: 0 },
        'WATER_DEEP':       { r: 30, g: 79, b: 110, a: 0 },

        'GRASS_LOWLAND':    { r: 119, g: 207, b: 60, a: 0 },
        'GRASS_HILLS':      { r: 97, g: 179, b: 41, a: 0 },
        'GRASS_MOUNTAIN':   { r: 67, g: 138, b: 19, a: 0 },

        'SAND':             { r: 248, g: 252, b: 111, a: 0 },

        'MOUNTAIN':         { r: 166, g: 162, b: 162, a: 0 },
        'MOUNTAIN_SNOWCAP': { r: 232, g: 232, b: 232, a: 0 },
    };

    const { terrain, elevation } = cell;

    // Water conditions
    if (terrain === Terrain.WATER && elevation < 5) {
        return TerrainColors['WATER_DEEP'];
    }

    if (terrain === Terrain.WATER && elevation < 15) {
        return TerrainColors['WATER'];
    }

    if (terrain === Terrain.WATER) {
        return TerrainColors['WATER_SHALLOW'];
    }

    // Grass conditions
    if (terrain === Terrain.GRASS && elevation < 30) {
        const rand = Math.random();

        return (rand < .1) ? 
            TerrainColors['GRASS_HILLS'] :  // 20% hill grass
            TerrainColors['GRASS_LOWLAND']; // 80% lowland grass
    }

    if (terrain === Terrain.GRASS && elevation < 70) {
        const rand = Math.random();

        return (rand < .9) ? 
            TerrainColors['GRASS_HILLS'] :  // 80% hill grass
            TerrainColors['GRASS_LOWLAND']; // 20% lowland grass
    }

    if (terrain === Terrain.GRASS) {
        return TerrainColors['GRASS_MOUNTAIN'];
    }

    // Sand conditions
    if (terrain === Terrain.SAND) {
        return TerrainColors['SAND'];
    }

    // Rock conditions
    if (terrain === Terrain.ROCK && elevation < 98) {
        return TerrainColors['MOUNTAIN'];
    }

    if (terrain === Terrain.ROCK) {
        return TerrainColors['MOUNTAIN_SNOWCAP'];
    }

    // If all else fails, return full red. This should never happen.
    return { r: 255, g: 0, b: 0, a: 0 };
}

const render_elevation = (cell : Cell) : Color => {
    // Max elevation is 100, so multiply by 2.55 to get to a max of 255.
    return {
        r: cell.elevation * 2.55,
        g: cell.elevation * 2.55,
        b: cell.elevation * 2.55,
        a: 255,
    };
}

const run = async () => {
    const world = await file_format.read(filename);
    const filename_base = filename.split('.')[0];

    render(world, render_terrain, `${filename_base}_terrain.png`);
    render(world, render_elevation, `${filename_base}_elevation.png`);
}

run();