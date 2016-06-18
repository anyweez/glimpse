function colorOf(cell) {
    // if (cell.terrain === 'grass') return 'green';
    // else if (cell.terrain === 'water') return 'blue';
    // else return 'brown';

    let r = Math.round(255 * ((100 - cell.elevation) / 100));
    let g = Math.round(255 * (cell.elevation / 100));
    let b = 0;

    return `rgb(${r},${g},${b})`;
}

module.exports = function (map, canvas) {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    let width = canvas.width / map.dim;
    let height = canvas.height / map.dim;
    let dimension = Math.min(width, height);

    let context = canvas.getContext('2d');
    
    console.log(canvas.width, canvas.height);
    map.grid.forEach(function (cell) {
        context.fillStyle = colorOf(cell);

        context.fillRect(cell.x * dimension + 1.5, cell.y * dimension + 1.5, dimension - 3, dimension - 3);
    })
};