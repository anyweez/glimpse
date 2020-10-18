import { fs } from 'mz';
import { PNG } from 'pngjs';
import file_format from '../generator/file_format';
import { Cell } from '../generator/world';
import { Terrain } from '../generator/terrain';

const filename = process.argv[2];

const CELL_DIMENSION_IN_PIXELS = 4;

interface Color {
    r: number
    g: number
    b: number
    a: number
}

const color = (name: string) : Color => {
    if (name === 'SHALLOW_WATER') return { r: 112, g: 162, b: 194, a: 0 };
    if (name === 'WATER') return { r: 69, g: 123, b: 157, a: 0 };
    if (name === 'DEEP_WATER') return { r: 30, g: 79, b: 110, a: 0 };

    if (name === 'GRASS') return { r: 119, g: 207, b: 60, a: 0 };

    if (name === 'SAND') return { r: 248, g: 252, b: 111, a: 0 };

    if (name === 'ROCK') return { r: 166, g: 162, b: 162, a: 0 };

    return { r: 255, g: 0, b: 0, a: 0 }
}

const run = async () => {
    const world = await file_format.read(filename);

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

            const { terrain, elevation } = world.find(proj_x, proj_y) as Cell;

            // Determine color for each cell based on properties of the cell.
            const c = (terrain === Terrain.WATER && elevation < 5) ? color('DEEP_WATER') :
                (terrain === Terrain.WATER && elevation < 15) ? color('WATER') :
                (terrain === Terrain.WATER) ? color('SHALLOW_WATER') :
                (terrain === Terrain.GRASS) ? color('GRASS') :
                (terrain === Terrain.SAND) ? color('SAND') :
                (terrain === Terrain.ROCK) ? color('ROCK') :
                { r: 255, g: 0, b: 0, a: 0 }; // bright red, error color

            img.data[idx] = c.r;
            img.data[idx + 1] = c.g;
            img.data[idx + 2] = c.b;
            img.data[idx + 3] = 255;    
        }
    }

    img.pack().pipe(fs.createWriteStream('world.png'));
}

run();