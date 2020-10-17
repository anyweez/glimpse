"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
function default_1() {
    var states = [];
    var current = -1;
    var tracker = {
        start: function (st) {
            states = st;
            this.next();
        },
        next: function () {
            current++;
            return new Promise(function (resolve) {
                // If all steps are complete, indicate that the entire process is done.
                if (current > states.length - 1) {
                    tracker._done();
                }
                // If more steps remain, update the user on progress and continue.
                else {
                    console.log("[" + current + " of " + states.length + "] " + states[current]);
                }
                setTimeout(resolve, 0);
            });
        },
        _done: function () {
            console.log("Done");
        },
    };
    return tracker;
}
exports.default = default_1;
;
