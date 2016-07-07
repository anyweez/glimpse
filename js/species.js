let type = ['water', 'energy', 'plant', 'animal'];

function Population(cell, opt = {}) {
    this.id = Math.floor(Math.random() * 10000);
    this.name = opt.name || 'Example species';
    this.population = opt.population || Math.floor(Math.random() * 100);
    this.home = cell;
    // Whether this population should ever be able to decrease in population due
    // to environmental factors. Usually yes unless we're talking about water or
    // sunlight.
    this.dies = opt.dies || true;

    this.type = opt.type || 'plant';
    this.diet = {
        requires: ['energy', 'water'],
        choiceOf: [],
        quantity: 2,
    };

    this.health = 1.0;

    this.stats = {
        // Affects how much food an individual provides. More mass = more food.
        mass: Math.floor(Math.random() * 100),
        // Reproduction rate, better thought of as 'ideal reproduction rate'. The
        // actual rate will be affected by the health of the population.
        reproduction: 3, 
    };

    return this;
}

Population.prototype.step = function () {
    /**
     * How many of the different populations are we interested in eating?
     **/
    let edible = this.home.populations.filter(pop => {
        return pop.id !== this.id && this.eats(pop);
    });

    let hunger = this.population * this.diet.quantity;

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
    let consumed = (this.population * this.diet.quantity) - hunger;
    let ratio = Math.round(consumed / this.diet.quantity) / this.population;

    this.health = (this.health * 0.95) + (ratio * this.health * 0.05);

    // population modified based on health value. the higher the health value, the more
    // likely the population will increase this step. as long as its higher than 50% its
    // guaranteed not to decrease.
    let noise = (Math.random() / 5) - 0.1; // [-0.1, 0.1]
    this.population += (noise + this.health - 0.5) * this.stats.reproduction;
}

/**
 * Function to run at the end of a step.
 */
Population.prototype.end = function () {
    // If the population has reached zero, it's extinct.
    if (this.population <= 0) this.extinguish();
}

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
        let pop = Math.ceil(mass / this.stats.mass);
        // Either everyone died (the whole pop) or the requested pop
        result.population = Math.min(this.population, pop);
        result.mass = result.population * this.stats.mass;

        this.population = Math.max(0, this.population - result.population);
    } else if (population) {
        result.population = Math.min(this.population, population);
        result.mass = result.population * this.stats.mass;

        this.population = Math.max(0, this.population - result.population);
    } else {
        throw new Error('Population.die() must have either mass or population targtets specified.');
    }

    result.exterminated = this.population <= 0;
    return result;
}

Population.prototype.extinguish = function () {
    console.log('extinguishing @ population')
    // this.home.extinguish(this);
}

/**
 * Returns true if this population will eat the provided population.
 */
Population.prototype.eats = function (population) {
    return this.diet.requires.indexOf(population.type) !== -1 
        || this.diet.choiceOf.indexOf(population.type) !== -1;
}

function RenewablePopulation(cell, opt) {
    Population.call(this, cell, opt);
    console.log(this.name);
    this.stablePop = this.population;
    
    return this;
}

RenewablePopulation.prototype = new Population();

RenewablePopulation.prototype.step = function () {}

RenewablePopulation.prototype.end = function () {
    this.population = this.stablePop;
}

module.exports = {
    Population: Population,
    RenewablePopulation: RenewablePopulation,
};