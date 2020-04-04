function overlap(a, b, c, d, mod) {
    /**
     * Finds the overlap of period [a, b] with period [c, d] given a modulo of the periods (e.g. wrapping week)
     */
    b = (b - a + mod) % mod;
    c = (c - a + mod) % mod;
    d = (d - a + mod) % mod;
    if (c > d) {
        return Math.min(b, d);
    } else {
        return Math.min(b, d) - Math.min(b, c);
    }
}

function inside(a, b, c, mod) {
    b = (b - a + mod) % mod;
    c = (c - a + mod) % mod;
    return c <= b;
}

function dateToWeekRep(date) {
    return (date.getDay() + 6) % 7 + date.getHours() / 24 + date.getMinutes() / (24 * 60) + date.getSeconds() / (24 * 60 * 60);
}

function hoursInsideRule(rule, startTime, endTime) {
    /**
     * Calculates how many hours the period [startTime, endTime] overlap with the given rule
     */
    // Convert date to day inside week
    startTime = dateToWeekRep(startTime);
    endTime = dateToWeekRep(endTime);
    let hours = 0;
    rule.periods.forEach(function (period) {
        hours += overlap(period[0], period[1], startTime, endTime, 7) * 24;
    });
    return hours;
}

function getPeriodIn(rules, date, direction) {
    date = (date.getDay() + 6) % 7 + date.getHours() / 24 + date.getMinutes() / (24 * 60);
    for (let ruleIndex = 0; ruleIndex < rules.length; ruleIndex++) {
        let rule = rules[ruleIndex];
        for (let periodIndex = 0; periodIndex < rule.periods.length; periodIndex++) {
            if (direction === 1 && rule.periods[periodIndex][0] === date) {
                continue;
            } else if (direction === 0 && rule.periods[periodIndex][1] === date) {
                continue;
            }
            if (inside(rule.periods[periodIndex][0], rule.periods[periodIndex][1], date, 7)) {
                return {
                    "period": rule.periods[periodIndex],
                    "max_inside": rule.max_inside,
                    "max_crossed": rule.max_crossed,
                };
            }
        }
    }
}

function getRulesCovered(rules, startTime, endTime) {
    /**
     * Returns the rules which overlap with the period [startTime, endTime]
     */
    let insideRules = [];
    rules.forEach(function (rule) {
        if (hoursInsideRule(rule, startTime, endTime)) {
            insideRules.push(rule);
        }
    });
    return insideRules;
}

function isValidForRules(rules, startTime, endTime) {
    /**
     * Checks if the period [startTime, endTime] is valid for the given set of rules
     */
    let coveredRules = getRulesCovered(rules, startTime, endTime);
    if (coveredRules.length === 1) {
        let hoursInside = hoursInsideRule(coveredRules[0], startTime, endTime);
        return coveredRules[0].max_inside >= Number(hoursInside.toFixed(2));
    }

    // If the reservation is shorter than the maximum inside for any of the rules, it should also be valid for
    // the whole duration, even though it breaks with one or more of the max_crossed rules.
    let minTime = 7 * 24;
    for (let ruleIndex = 0; ruleIndex < coveredRules.length; ruleIndex++) {
        minTime = Math.min(minTime, coveredRules[ruleIndex].max_inside);
    }

    if (minTime >= (endTime.valueOf() - startTime.valueOf()) / (60 * 60 * 1000)) {
        return true;
    }

    let maxTime = 0;
    for (let ruleIndex = 0; ruleIndex < coveredRules.length; ruleIndex++) {
        maxTime = Math.max(maxTime, coveredRules[ruleIndex].max_inside);
        let hoursInside = hoursInsideRule(coveredRules[ruleIndex], startTime, endTime);
        if (coveredRules[ruleIndex].max_crossed < Number(hoursInside.toFixed(2))) {
            return false;
        }
    }
    return (endTime.valueOf() - startTime.valueOf()) / (60 * 60 * 1000) <= maxTime;
}

function modifyToFirstValid(rules, startTime, endTime, modificationDirection) {
    /**
     * Modifies either startTime (modificationDirection 0) or endTime (modificationDirection 1) until the period
     * [startTime, endTime] is valid for the given set of rules.
     */
    // Check if the period is valid for the set of rules
    while (!isValidForRules(rules, startTime, endTime)) {
        // Get all rules the start/end time overlap
        let coveredRules = getRulesCovered(rules, startTime, endTime);

        // Check if the total time of the reservation is greater than what is allowed by the covered rules
        let maxTime = 0;
        let minTime = 7 * 24;
        for (let ruleIndex = 0; ruleIndex < coveredRules.length; ruleIndex++) {
            maxTime = Math.max(maxTime, coveredRules[ruleIndex].max_inside);
            minTime = Math.min(minTime, coveredRules[ruleIndex].max_inside);
        }

        // Modify the start/end time based on the maximum allowed time for the covered rules
        if (maxTime < (endTime.valueOf() - startTime.valueOf()) / (60 * 60 * 1000)) {
            if (modificationDirection) {
                endTime = new Date(startTime.valueOf() + maxTime * 60 * 60 * 1000);
            } else {
                startTime = new Date(endTime.valueOf() - maxTime * 60 * 60 * 1000);
            }
            continue;
        }

        // If the period is still not valid, this means that we have to remove the rules one by one
        let period = getPeriodIn(rules, modificationDirection ? endTime : startTime, modificationDirection);
        if (modificationDirection) {
            let currentOverlap = overlap(period.period[0], period.period[1], period.period[0], dateToWeekRep(endTime), 7) * 24;
            // Discard precision beyond seconds, as the calculation is prone to floating point accuracy errors
            currentOverlap = Number(currentOverlap.toFixed(4));
            // Shrink the overlap until
            if (currentOverlap > period.max_inside) {
                // If the overlap with the current time period is greater than the maximum allowed inside then
                // shrink till it is equal to that.
                endTime = new Date(endTime.valueOf() - (currentOverlap - period.max_inside) * 60 * 60 * 1000);
            } else if (currentOverlap > period.max_crossed) {
                // If the overlap with the current time period is greater than the maximum allowed when multiple
                // time periods are selected, then shrink till it is equal to that.
                endTime = new Date(Math.max(
                    new Date(endTime.valueOf() - (currentOverlap - period.max_crossed) * 60 * 60 * 1000),
                    new Date(startTime.valueOf() + minTime * 60 * 60 * 1000),
                ));
            } else {
                // If the overlap is smaller than both the allowed inside when single- and multi-period, shrink till
                // there is no overlap between the periods.
                endTime = new Date(endTime.valueOf() - currentOverlap * 60 * 60 * 1000);
            }
        } else {
            let currentOverlap = overlap(period.period[0], period.period[1], dateToWeekRep(startTime), period.period[1], 7) * 24;
            if (currentOverlap > period.max_inside) {
                // If the overlap with the current time period is greater than the maximum allowed inside then
                // shrink till it is equal to that.
                startTime = new Date(startTime.valueOf() + (currentOverlap - period.max_inside) * 60 * 60 * 1000);
            } else if (currentOverlap > period.max_crossed) {
                // If the overlap with the current time period is greater than the maximum allowed when multiple
                // time periods are selected, then shrink till it is equal to that.
                startTime = new Date(Math.min(
                    new Date(startTime.valueOf() + (currentOverlap - period.max_crossed) * 60 * 60 * 1000),
                    new Date(endTime.valueOf() - minTime * 60 * 60 * 1000),
                ));
            } else {
                // If the overlap is smaller than both the allowed inside when single- and multi-period, shrink till
                // there is no overlap between the periods.
                startTime = new Date(startTime.valueOf() + currentOverlap * 60 * 60 * 1000);
            }
        }
    }
    return modificationDirection ? endTime : startTime;
}
