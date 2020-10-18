import { Cell, World } from './world';

export const Terrain = {
    ANY: 1,
    WATER: 2,
    SAND: 3,
    ROCK: 4,
    GRASS: 5,
};

export const available: Array<any> = [
    {
        label: Terrain.WATER,
        func: function (cell: Cell, world: World): boolean { return cell.water; },
        color: function (cell: Cell) {
            if (cell.elevation < 5) return { r: 30, g: 79, b: 110, a: 0 };
            else if (cell.elevation < 15) return { r: 69, g: 123, b: 157, a: 0 };
            else return { r: 112, g: 162, b: 194, a: 0 };
        },
    },
    {
        label: Terrain.SAND,
        func: function (cell: Cell, world: World): boolean {
            let valid = world.neighbors(cell).filter(cell => cell.water || cell.terrain === 'sand').length > 0;
            return valid && cell.elevation - world.meta.aquiferDepth < 10;
        },
        color: function (cell: Cell) {
            return { r: 248, g: 252, b: 111, a: 0 };
        }
    },
    {
        label: Terrain.ROCK,
        func: function (cell: Cell, world: World): boolean {
            return cell.elevation > 90;
        },
        color: function (cell: Cell) {
            if (cell.elevation > 98) return { r: 232, g: 232, b: 232, a: 0 }; // snow
            else return { r: 166, g: 162, b: 162, a: 0 };
        },
    },
    {
        // grass is the default unless terrain has another label
        label: Terrain.GRASS,
        func: function (cell: Cell, world: World): boolean {
            return true;
        },
        color: function (cell: Cell) {
            if (cell.elevation < 30) return { r: 119, g: 207, b: 60, a: 0 };
            else if (cell.elevation < 70) return { r: 97, g: 179, b: 41, a: 0 };
            else return { r: 67, g: 138, b: 19, a: 0 };
        }
    }
];

interface TerrainColor {
    [key: number]: Function;
}

/**
 * Export a function that can accept a cell and return the color that the cell should
 * be rendered as based on the terrain. Does not account for populations, etc.
 */
export let colorize = function (): Function {
    let mapping: TerrainColor = {};
    available.forEach(terrain => mapping[terrain.label] = terrain.color);

    return function (cell: Cell): { r: number, g: number, b: number } {
        return mapping[cell.terrain](cell);
    };
} ();