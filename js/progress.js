module.exports = function () {
    let states = [];
    let current = -1;

    let progress = null;
    let message = null;
    let indicator = null;

    return {
        start(st) {
            states = st;
            progress = document.getElementById('progress');
            message = progress.querySelector('h2');
            indicator = progress.querySelector('p');

            this.next();
        },

        next() {
            current++;

            return new Promise(resolve => {
                if (current > states.length - 1) this._done();
                else {
                    console.log(`${current} of ${states.length}`);
                    message.innerText = states[current];

                    this._indicator();

                    console.log(states[current]);
                }

                setTimeout(resolve, 0);
            });
        },

        _done() {
            message.innerText = 'Complete';
            this._indicator();

            // First timeout triggers fade effect. Second one actually changed the
            // display type so that the element won't capture any events, etc.
            setTimeout(() => {
                progress.classList.add('hide');

                setTimeout(() => {
                    progress.classList.add('gone');
                }, 500);
            }, 100);
        },

        _indicator() {
            let ind = [];
            for (let i = 0; i < states.length; i++) {
                if (current > i) ind.push('	&#9673;');
                else ind.push('&#9678;');
            }
            indicator.innerHTML = ind.join(' ');
        },
    };
}