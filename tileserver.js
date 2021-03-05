const tilestrata = require('tilestrata');
const disk = require('tilestrata-disk');
const sharp = require('tilestrata-sharp');
const mapnik = require('tilestrata-mapnik');
const dependency = require('tilestrata-dependency');

const strata = tilestrata();

const layers = [
    { name: 'continents', mapnik_path: './mapnik/continents.xml' },
    // { name: 'cities', mapnik_path: './mapnik/cities.xml' },
    { name: 'lakes', mapnik_path: './mapnik/lakes.xml' },
    // { name: 'hillshading', mapnik_path: './mapnik/hillshading.xml' },
    // { name: 'biomes', mapnik_path: './mapnik/biomes.xml' },
]

layers.forEach(layer => {
    strata.layer(layer.name)
        .route('tile@2x.png')
            // .use(disk.cache({ dir: './mapcache' }))
            .use(mapnik({
                pathname: layer.mapnik_path,
                tileSize: 512,  // in pixels
                scale: 2,
            }))
        .route('tile.png')
            // .use(disk.cache({ dir: './mapcache' }))
            .use(dependency(layer.name, 'tile@2x.png'))
            .use(sharp(image => image.resize(256)));
});

// start accepting requests
console.log('Starting tileserver...')
strata.listen(8081);