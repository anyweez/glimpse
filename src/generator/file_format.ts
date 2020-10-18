import { fs } from 'mz';
import { World, Cell } from './world';

class Worldfile {
    meta : WorldMeta
    cells : WorldfileCell[]

    constructor() {
        this.meta = new WorldMeta();
        this.cells = new Array<WorldfileCell>();
    }
}

class WorldMeta {
    width : number 
    height : number
}

class WorldfileCell {
    x : number
    y : number
    terrain : number
    elevation : number
}

const read = async (filename : string) : Promise<World> => {
    const content = await fs.readFile(filename)
        .then((res : Buffer) => JSON.parse( res.toString() ));

    const w = new World({
        dim: content.meta.width,
    });

    // Copy content from each cell into the world object.
    content.cells.forEach((cell : WorldfileCell) => {
        const wcell = w.find(cell.x, cell.y) as Cell;

        wcell.elevation = cell.elevation;
        wcell.terrain = cell.terrain;
    });

    return Promise.resolve(w);
}

/**
 * Write a worldfile to `filename` based on the specified `world`.
 * 
 * @param filename
 * @param world 
 */
const write = async (filename : string, world : World) => {
    const wf = new Worldfile();

    wf.meta.height = world.meta.dim;
    wf.meta.width = world.meta.dim;

    for (let y = 0; y < world.meta.dim; y++) {
        for (let x = 0; x < world.meta.dim; x++) {
            const wfc = new WorldfileCell();

            const cell = world.find(x, y);

            wfc.elevation = Math.round(cell.elevation * 1000) / 1000;
            wfc.x = cell.x;
            wfc.y = cell.y;
            wfc.terrain = (cell as Cell).terrain;

            wf.cells.push(wfc);
        }
    }

    const wfstr = JSON.stringify(wf);

    return await fs.writeFile(filename, wfstr);
}

export default {
    read,
    write
}