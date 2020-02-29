Date.prototype.startOfWeek = function () {
    /**
     * Finds the start of the current week
     */
    let dayDifference = ((this.getDay() + 6) % 7) * 24 * 60 * 60 * 1000;
    let timeDifference = this.getHours() * 60 * 60 * 1000 + this.getMinutes() * 60 * 1000 + this.getSeconds() * 1000 + this.getMilliseconds();

    return new Date(this - timeDifference - dayDifference);
};

Date.prototype.getWeekNumber = function () {
    /**
     * Finds the current week number
     */
    let date = new Date(this);
    date.setUTCDate(date.getUTCDate() + 4 - (date.getUTCDay() || 7));
    let yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
    return Math.ceil((((date - yearStart) / (24 * 60 * 60 * 1000)) + 1) / 7);
};

Date.prototype.nextDay = function () {
    /**
     * Returns the next day
     */
    let date = new Date(this);
    date.setDate(date.getDate() + 1);
    return date;
};

Date.prototype.nextWeek = function () {
    /**
     * Returns the date one week ahead in time
     */
    let date = new Date(this);
    date.setDate(date.getDate() + 7);
    return date;
};

Date.prototype.previousWeek = function () {
    /**
     * Returns the date one week behind in time
     */
    let date = new Date(this);
    date.setDate(date.getDate() - 7);
    return date;
};

function ReservationCalendar(element, properties) {
    this.date = new Date().startOfWeek();
    this.informationHeaders = element.find("thead th");
    this.element = element;
    this.init();
}

ReservationCalendar.prototype.init = function () {
    this.update();
    this.element.find(".next.button").click(() => {
        this.date = this.date.nextWeek();
        this.update();
    });

    this.element.find(".current.button").click(() => {
        this.date = new Date().startOfWeek();
        this.update();
    });

    this.element.find(".previous.button").click(() => {
        this.date = this.date.previousWeek();
        this.update();
    })
};

ReservationCalendar.prototype.update = function () {
    this.updateInformationHeaders();
};

ReservationCalendar.prototype.updateInformationHeaders = function () {
    this.informationHeaders[0].querySelector(".large.header").textContent = "";
    this.informationHeaders[0].querySelector(".medium.header").textContent = this.date.getWeekNumber();

    let date = this.date;
    for (let day = 1; day < 8; day++) {
        this.informationHeaders[day].querySelector(".medium.header").textContent = date.getDate();
        date = date.nextDay();
    }
};