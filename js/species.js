let type = ['water', 'energy', 'plant', 'animal'];

function Population(cell, opt = {}) {
    this.id = Math.floor(Math.random() * 10000);
    this.name = opt.name || 'Magnus originalis';
    this.population = opt.population || Math.floor(Math.random() * 100);
    this.home = cell;
    this.health = 1.0;

    // Features are shared across all populations of this species.
    this.features = {
        // Whether this population should ever be able to decrease in population due
        // to environmental factors. Usually yes unless we're talking about water or
        // sunlight.
        dies: opt.dies || true,
        type: opt.type || 'plant',
        diet: {
            requires: ['energy', 'water'],
            choiceOf: [],
            quantity: 2,
        },
        // Match the terrain types, or 'all'
        environments: opt.environments || ['grass', 'sand'],
        stats: {
            // Affects how much food an individual provides. More mass = more food.
            mass: (opt.hasOwnProperty('stats') && opt.stats.mass) ? opt.stats.mass : Math.floor(Math.random() * 100),
            // Reproduction rate, better thought of as 'ideal reproduction rate'. The
            // actual rate will be affected by the health of the population.
            reproduction: (opt.hasOwnProperty('stats') && opt.stats.reproduction) ? opt.stats.reproduction : 3,
            // Eagerness to migrate, from [0, 1]. Currently only binary based on === 0.
            migratory: (opt.hasOwnProperty('stats') && opt.stats.migratory) ? opt.stats.migratory : 0.2,
        }
    };

    // Register the population automatically.
    if (this.home) this.home.spawn(this);

    return this;
}

Population.prototype.step = function () {
    /**
     * If the population is in a habitat they can't suvive in, they take a hard
     * hit to their health.
     */
    if (this.features.environments.indexOf(this.home.terrain) === -1 &&
        this.features.environments.indexOf('any') === -1) {
        this.health -= 0.25;
    }

    /**
     * How many of the different populations are we interested in eating?
     **/
    let edible = this.home.populations.filter(pop => {
        return pop.id !== this.id && this.eats(pop);
    });

    let hunger = this.population * this.features.diet.quantity;

    /**
     * While everything's not extinct and the population is still hungry, keep
     * eating.
     */
    let i = 0;
    let c = 0;
    let exterminated = [];

    while (hunger > 0 && exterminated.length != edible.length) {
        // Try eating 10% of the full meal required from this population.
        let result = edible[i].die({ mass: hunger / 10 });

        hunger -= result.mass;

        if (result.exterminated) exterminated.push(i);
        i = (i + 1) % edible.length;
        c++;

        // Should not happen but has occasionally as I've added new features.
        if (c > 1000) {
            throw new Error('Likely infinite loop detected during feeding frenzy.');
        }
    }

    /**
     * The ratio of fed : total should modify the health of the population
     */
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

Population.prototype.migration = function () {
    let neighbors = this.home.world.neighbors(this.home);

    // Populations only migrate if they're healthy or starving. If it's a really small
    // group then they won't migrate. There's a decent change populations won't migrate
    // each step.
    //
    // TODO: make probability of migration dependent on features.stats.migratory
    if (this.population < 50 || Math.random() < 0.96) return;
    let migrants = Math.ceil(this.population * 0.02);

    neighbors.forEach(function (neighbor) {
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
};

/**
 * Function to run at the end of a step.
 */
Population.prototype.end = function () {
    // If the population has reached zero, it's extinct.
    if (this.population <= 0) {
        this.extinguish();
        return;
    }

    // Bound health between [0, 1]
    this.health = Math.min(1, Math.max(0, this.health));
};

/**
 * Returns an object describing how much of the population was consumed, and a flag
 * indicating whether the population was exterminated.
 */
Population.prototype.die = function (target = {}) {
    let mass = target.mass || undefined;
    let population = target.population || undefined;

    let result = {
        mass: 0,
        population: 0,
        exterminated: false,
    };

    if (mass) {
        let pop = Math.ceil(mass / this.features.stats.mass);
        // Either everyone died (the whole pop) or the requested pop
        result.population = Math.min(this.population, pop);
        result.mass = result.population * this.features.stats.mass;

        this.population = Math.max(0, this.population - result.population);
    } else if (population) {
        result.population = Math.min(this.population, population);
        result.mass = result.population * this.features.stats.mass;

        this.population = Math.max(0, this.population - result.population);
    } else {
        throw new Error('Population.die() must have either mass or population targtets specified.');
    }

    result.exterminated = this.population <= 0;
    return result;
};

Population.prototype.extinguish = function () {
    console.log('extinguishing @ population')
    this.home.extinguish(this);
};

/**
 * Returns true if this population will eat the provided population.
 */
Population.prototype.eats = function (population) {
    return this.features.diet.requires.indexOf(population.features.type) !== -1
        || this.features.diet.choiceOf.indexOf(population.features.type) !== -1;
};

function RenewablePopulation(cell, opt) {
    // Set a different default for renewables (non-migratory).
    if (opt.hasOwnProperty('stats') && !opt.stats.migratory) opt.stats.migratory = 0;
    if (opt.environments) opt.environments = ['all'];

    Population.call(this, cell, opt);
    this.stablePop = this.population;

    return this;
}

RenewablePopulation.prototype = new Population();

RenewablePopulation.prototype.step = function () { };

RenewablePopulation.prototype.migration = function () { };

RenewablePopulation.prototype.end = function () {
    this.population = this.stablePop;
};

module.exports = {
    Population: Population,
    RenewablePopulation: RenewablePopulation,
};