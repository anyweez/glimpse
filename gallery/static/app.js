

const app = new Vue({
    el: '#app',
    data: {
        message: 'hey',
        map_svg: null,
        map_svg_parsed: null,
        world_id: null,

        map_list: [],
        current_map_idx: null,
    },
    
    mounted() {
        window.addEventListener('keypress', ev => {
            if (ev.key === 's') {
                this.$refs.map.querySelectorAll('.city').forEach(city => {
                    city.classList.toggle('show')
                });
            }
        });

        // Get map list
        return fetch(`/maps`)
            .then(resp => resp.json())
            .then(maps => {
                this.map_list = maps;

                this.random_map_idx();
            });
    },

    methods: {
        // load the map identified by `current_map_idx`
        get_map() {
            const map_name = this.map_list[this.current_map_idx];

            return fetch(`/maps/${map_name}`)
                .then(resp => resp.text())
                .then(resp => {
                    this.world_id = map_name.split('-')[1].split('.')[0];
                    this.map_svg = resp;

                    this.map_svg_parsed = new DOMParser().parseFromString(this.map_svg, 'application/xml');
                });
        },

        // select and load a random map
        random_map_idx() {
            this.current_map_idx = Math.floor(Math.random() * this.map_list.length);

            this.get_map();
        },

        // select and load the next map in the order
        next_map_idx() {
            this.current_map_idx = (this.current_map_idx + 1) % this.map_list.length;

            this.get_map();
        },

        highlight(poi={}, type) {
            // Highlight cities
            return [...this.$refs.map.querySelectorAll(`.${type}`)].forEach(el => {
                const details = JSON.parse( el.getAttribute('details') );

                if (poi.name && (details.name === poi.name)) {
                    el.classList.add('show');
                } else {
                    el.classList.remove('show');
                }
            });
        },

        unhighlight_all() {
            document.querySelectorAll('.city').forEach(c => c.classList.remove('show'));
            document.querySelectorAll('.lake').forEach(c => c.classList.remove('show'));
            document.querySelectorAll('.mountain').forEach(c => c.classList.remove('show'));
        }
    },

    computed: {
        cities() {
            if (this.world_id === null) return [];

            return [...this.map_svg_parsed.querySelectorAll('.city')]
                .map(city => JSON.parse(city.getAttribute('details')));
        },

        lakes() {
            if (this.world_id === null) return [];

            return [...this.map_svg_parsed.querySelectorAll('.lake')]
                .map(lake => JSON.parse(lake.getAttribute('details')));
        },

        mountains() {
            if (this.world_id === null) return [];

            return [...this.map_svg_parsed.querySelectorAll('.mountain')]
                .map(lake => JSON.parse(lake.getAttribute('details')));
        },
    },
});

// const activate_map = name => {
//     return fetch(`/maps/${name}`)
//         .then(resp => resp.text())
//         .then(svg => {
//             const set_details = (html, is_subtle) => {
//                 document.querySelector('hover-details').innerHTML = html;

//                 if (is_subtle) {
//                     document.querySelector('hover-details').classList.add('subtle');
//                 } else {
//                     document.querySelector('hover-details').classList.remove('subtle');
//                 }
//             }

//             const defaultDetails = () => {
//                 const cities = document.querySelectorAll('svg .city')
//                     .map(city => `<li>${JSON.parse(city.getAttribute('details')).name}`)

//                 return `
//                     <h3>Cities</h3>
//                     <ul>${cities}</ul>
//                 `;
//             }

//             // Load SVG
//             document.querySelector('.map').innerHTML = svg;

//             const world_id = name.split('-')[1].split('.')[0];
//             document.querySelector('.details').innerHTML = `
//                 <h2>${world_id}</h2>

//                 <div class="hover-details"></div>    
//             `;

//             set_details(defaultDetails, true);

//             // Add listeners to all city markers
//             document.querySelectorAll('.map .city').forEach(city => {
//                 city.addEventListener('mouseover', () => {
//                     const details = JSON.parse( city.getAttribute('details') );
//                     console.log(`clicked on ${details.name}`)

//                     set_details(`
//                         <h3>${obj.name}</h3>
//                         <p>${obj.extra ? obj.extra : ''}</h3>
//                     `, false);
//                 });

//                 city.addEventListener('mouseout', () => {
//                     set_details(defaultDetails, true)
//                 })
//             });
//         })
// }

// const activate_details = obj => {
//     const hd = document.querySelector('.hover-details');
//     hd.classList.remove('subtle');

//     hd.innerHTML = `
//         <h3>${obj.name}</h3>
//         <p>${obj.extra ? obj.extra : ''}</h3>
//     `;
// }

// /**
//  * On window load, grab the list of all available maps. Pick a random map and display it.
//  */
// window.addEventListener('load', () => {
//     return fetch(`/maps`)
//         .then(resp => resp.json())
//         .then(map_arr => {
//             let active_idx = Math.floor( map_arr.length * Math.random() );
//             activate_map(map_arr[active_idx]);

//             // Button should take us to a new map
//             const next_btn = document.querySelector('button');
//             next_btn.addEventListener('click', () => {
//                 active_idx = (active_idx + 1) % map_arr.length; 
//                 activate_map(map_arr[active_idx]);
//             });

//             // Add SHIFT listener
//             window.addEventListener('keypress', ev => {
//                 if (ev.key === 's') {
//                     document.querySelectorAll('svg .city').forEach(city => {
//                         city.classList.toggle('show')
//                     })
//                 }
//             })
//         });
// })