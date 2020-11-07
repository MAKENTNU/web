Date.prototype.startOfWeek = function () {
    /**
     * Finds the start of the current week
     */
    const dayDifference = ((this.getDay() + 6) % 7) * 24 * 60 * 60 * 1000;
    const timeDifference = this.getHours() * 60 * 60 * 1000 + this.getMinutes() * 60 * 1000 + this.getSeconds() * 1000 + this.getMilliseconds();
    return new Date(this - timeDifference - dayDifference);
};

Date.prototype.getWeekNumber = function () {
    /**
     * Finds the current week number
     */
    const date = new Date(this);
    date.setDate(date.getDate() + 4 - (date.getDay() || 7));
    const yearStart = new Date(date.getFullYear(), 0, 1);
    return Math.ceil((((date - yearStart) / (24 * 60 * 60 * 1000)) + 1) / 7);
};

Date.prototype.nextDay = function () {
    /**
     * Returns the next day
     */
    return this.nextDays(1);
};

Date.prototype.nextDays = function (nDays) {
    /**
     * Skips n days into the future
     */
    const date = new Date(this);
    date.setDate(date.getDate() + nDays);
    return date;
};


Date.prototype.nextWeek = function () {
    /**
     * Returns the date one week ahead in time
     */
    const date = new Date(this);
    date.setDate(date.getDate() + 7);
    return date;
};

Date.prototype.previousWeek = function () {
    /**
     * Returns the date one week behind in time
     */
    const date = new Date(this);
    date.setDate(date.getDate() - 7);
    return date;
};

function zeroPad(value) {
    return value < 10 ? `0${value}` : `${value}`;
}

Date.prototype.timeString = function () {
    /**
     * Returns a string in the format HH:MM
     */
    return `${zeroPad(this.getHours())}:${zeroPad(this.getMinutes())}`;
};

Date.prototype.dateString = function () {
    /**
     * Returns a string in the format DD:MM:YYYY
     */
    return `${zeroPad(this.getDate())}.${zeroPad(this.getMonth() + 1)}.${this.getFullYear()}`;
};

Date.prototype.djangoFormat = function () {
    /**
     * Returns a string of the date in the format YYYY-mm-dd HH:MM, which is one of the formats Django accepts
     */
    return `${this.getFullYear()}-${this.getMonth() + 1}-${this.getDate()} ${zeroPad(this.getHours())}:${zeroPad(this.getMinutes())}`;
};

Date.prototype.getMonthText = function () {
    /**
     * Returns the full name of the current month translated
     */
    const MONTH_TRANSLATIONS = [
        // Have to call `gettext()` with every string to make them appear in the .po file
        gettext("January"),
        gettext("February"),
        gettext("March"),
        gettext("April"),
        gettext("May"),
        gettext("June"),
        gettext("July"),
        gettext("August"),
        gettext("September"),
        gettext("October"),
        gettext("November"),
        gettext("December"),
    ];
    return MONTH_TRANSLATIONS[this.getMonth()];
};

Date.prototype.getMonthTextShort = function () {
    /**
     * Returns the three first letters in the translated name of the current month
     */
    return this.getMonthText().slice(0, 3);
};

Date.prototype.getDayText = function () {
    /**
     * Returns the full translated name of the current day
     */
    const DAY_TRANSLATIONS = [
        // Have to call `gettext()` with every string to make them appear in the .po file
        gettext("Sunday"),
        gettext("Monday"),
        gettext("Tuesday"),
        gettext("Wednesday"),
        gettext("Thursday"),
        gettext("Friday"),
        gettext("Saturday"),
    ];
    return DAY_TRANSLATIONS[this.getDay()];
};

Date.prototype.getDayTextShort = function () {
    /**
     * Returns the three first letters in the translated name of the current day
     */
    return this.getDayText().slice(0, 3);
};
