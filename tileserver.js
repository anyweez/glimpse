const tilestrata = require('tilestrata');
const disk = require('tilestrata-disk');
const sharp = require('tilestrata-sharp');
const mapnik = require('tilestrata-mapnik');
const dependency = require('tilestrata-dependency');

const layers = [
    { name: 'continents', mapnik_path: './mapnik/continents.xml' },
    { name: 'cities', mapnik_path: './mapnik/cities.xml' },
    { name: 'lakes', mapnik_path: './mapnik/lakes.xml' },
    // { name: 'hillshading', mapnik_path: './mapnik/hillshading.xml' },
    { name: 'biomes', mapnik_path: './mapnik/biomes.xml' },
    { name: 'waterbodies', mapnik_path: './mapnik/waterbodies.xml' },
]

console.log('Initiatizing tileserver...')
const strata = tilestrata();

layers.forEach(layer => {
    console.log(`  Enabling layer: ${layer.name}`)
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
console.log('Enabling web endpoints...')
strata.listen(8081);