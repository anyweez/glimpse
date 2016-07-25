import { Cell } from './world';
import { Terrain } from './terrain';

let type: Array<string> = ['water', 'energy', 'plant', 'animal'];

export class Population {
    id: number;
    // Whether this population should get a turn each world cycle
    active: boolean;
    name: string;
    // The count of this species in this cell.
    population: number;
    home: Cell = null;
    health: number;
    features: PopulationFeatures = {
        dies: true,
        type: 'plant',
        diet: {
            requires: ['energy'],
            choiceOf: [],
            quantity: 2,
        },
        environments: [Terrain.GRASS, Terrain.SAND],
        stats: {
            mass: Math.floor(Math.random() * 100),
            reproduction: 3,
            migratory: 0.2,
        },
    };

    constructor(home: Cell, options: any = {}) {
        this.id = Math.floor(Math.random() * 1000000);
        this.name = options.name || 'Magnus originalis';
        this.population = options.population || Math.floor(Math.random() * 100);
        this.health = 1.0;
        this.active = true;

        // Configure the population features.
        if (options.dies) this.features.dies = options.dies;
        if (options.type) this.features.type = options.type;
        if (options.environments) this.features.environments = options.environments;
        if (options.stats && options.stats.mass) this.features.stats.mass = options.stats.mass;
        if (options.stats && options.stats.reproduction) this.features.stats.reproduction = options.stats.reproduction;
        if (options.stats && options.stats.migratory) this.features.stats.migratory = options.stats.migratory;

        // Register the population automatically.
        home.spawn(this);
    }

    /**
     * Compute a single step for the population (eating, dying, potentially migrating, etc).
     */
    step() {
        // If the population is in a habitat they can't suvive in, they take a hard
        // hit to their health.
        if (this.features.environments.indexOf(this.home.terrain) === -1 &&
            this.features.environments.indexOf(Terrain.ANY) === -1) {
            this.health -= 0.25;
        }

        // How many of the different populations are we interested in eating?
        let edible = this.home.populations.filter(pop => {
            return pop.id !== this.id && this.eats(pop);
        });

        let hunger = this.population * this.features.diet.quantity;

        // While everything's not extinct and the population is still hungry, keep
        // eating.
        let i = 0;
        let c = 0;
        let exterminated: number = 0;

        while (hunger > 0 && exterminated != edible.length) {
            // Try eating 10% of the full meal required from this population.
            let result = edible[i].die({ mass: hunger / 10 });

            hunger -= result.mass;

            if (result.exterminated) exterminated++;
            i = (i + 1) % edible.length;
            c++;

            // Should not happen but has occasionally as I've added new features.
            if (c > 1000) {
                throw new Error('Likely infinite loop detected during feeding frenzy.');
            }
        }

        // The ratio of fed : total should modify the health of the population
        let consumed = (this.population * this.features.diet.quantity) - hunger;
        let ratio = Math.round(consumed / this.features.diet.quantity) / this.population;
        // let ratio = 1;

        // The species' current health is the dominant factor in their health post-step. How
        // much they've been able to eat will also play a factor.
        this.health = (this.health * 0.85) + (ratio * this.health * 0.15);

        // Population modified based on health value. the higher the health value, the more
        // likely the population will increase this step. as long as its higher than 50% its
        // guaranteed not to decrease.
        let noise = (Math.random() / 5) - 0.1; // [-0.1, 0.1]
        this.population += (noise + this.health - 0.5) * this.features.stats.reproduction;

        // Potentially migrate if the population is migratory
        if (this.features.stats.migratory > 0) this.migration();
    }

    /**
     * If the population is large enough, there's a chance they'll try to migrate to nearby cells.
     * Currently if they migrate to one, they migrate to all nearby cells.
     */
    migration() {
        let neighbors = this.home.world.neighbors(this.home);

        // Populations only migrate if they're healthy or starving. If it's a really small
        // group then they won't migrate. There's a decent change populations won't migrate
        // each step.
        //
        // TODO: make probability of migration dependent on features.stats.migratory
        if (this.population < 50 || Math.random() < 0.96) return;
        let migrants = Math.ceil(this.population * 0.02);

        neighbors.forEach(function (neighbor: Cell) {
            // Random chance to migrate in each direction.
            if (Math.random() < 0.85) return;

            // If the population already exists, combine populations.
            let existing = neighbor.populations.find(pop => pop.name === this.name);

            if (existing) existing.population += migrants;
            else {
                // Create a new population that's identical to the source population. Spawn them
                // on the neighbor.
                let pop = new Population(neighbor);
                pop.population = migrants;
                pop.health = this.health;

                // Features are shared across all populations of the same species, so no need to
                // make a copy.
                pop.features = this.features;
            }

            this.population -= migrants;
        }.bind(this));
    }

    end() {
        // If the population has reached zero, it's extinct.
        if (this.population <= 0) {
            this.extinguish();
            return;
        }

        // Bound health between [0, 1]
        this.health = Math.min(1, Math.max(0, this.health));
    }

    /**
     * Returns an object describing how much of the population was consumed, and a flag
     * indicating whether the population was exterminated.
     */
    die(target: { mass?: number; population?: number; }) {

        let result = {
            mass: 0,
            population: 0,
            exterminated: false,
        };

        if (target.mass) {
            let pop = Math.ceil(target.mass / this.features.stats.mass);
            // Either everyone died (the whole pop) or the requested pop
            result.population = Math.min(this.population, pop);
            result.mass = result.population * this.features.stats.mass;

            this.population = Math.max(0, this.population - result.population);
        } else if (target.population) {
            result.population = Math.min(this.population, target.population);
            result.mass = result.population * this.features.stats.mass;

            this.population = Math.max(0, this.population - result.population);
        } else {
            throw new Error('Population.die() must have either mass or population targtets specified.');
        }

        result.exterminated = this.population <= 0;
        return result;
    }

    extinguish() {
        this.home.extinguish(this);
    }

    /**
     * Returns true if this population will eat the provided population.
     */
    eats(population: Population): boolean {
        return this.features.diet.requires.indexOf(population.features.type) !== -1
            || this.features.diet.choiceOf.indexOf(population.features.type) !== -1;
    }
}

interface PopulationFeatures {
    dies: boolean;
    type: string;
    diet: PopulationDiet;
    environments: Array<number>;
    stats: PopulationStats;
}

interface PopulationDiet {
    requires: Array<string>;
    choiceOf: Array<string>;
    quantity: number;
}

interface PopulationStats {
    mass: number;
    reproduction: number;
    migratory: number;
}

export class RenewablePopulation extends Population {
    stablePop: number;

    constructor(cell: Cell, opt: any = {}) {
        if (opt.stats && !opt.stats.migratory) opt.stats.migratory = 0;
        if (!opt.environments) opt.environments = ['all'];

        super(cell, opt);
        this.stablePop = this.population;
        this.active = false;
    }

    // Will never get called since active = false
    step() { }
    migration() { }
    end() { }
}