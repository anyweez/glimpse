export default function() {
    let states: Array<string> = [];
    let current: number = -1;

    let tracker = {
        start(st: Array<string>) {
            states = st;
            this.next();
        },

        next() {
            current++;

            return new Promise<void>(resolve => {
                // If all steps are complete, indicate that the entire process is done.
                if (current > states.length - 1) {
                    tracker._done();
                }
                // If more steps remain, update the user on progress and continue.
                else {
                    console.log(`[${current} of ${states.length}] ${states[current]}`);
                }

                setTimeout(resolve, 0);
            });
        },

        _done(): void {
            console.log(`Done`)
        },
    };

    return tracker;
};