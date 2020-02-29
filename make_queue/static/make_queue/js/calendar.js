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

Date.prototype.djangoFormat = function () {
    let zeroPad = (value) => value < 10 ? `0${value}` : `${value}`;
    return `${this.getUTCFullYear()}-${this.getUTCMonth() + 1}-${this.getUTCDate()} ${zeroPad(this.getUTCHours())}:${zeroPad(this.getUTCMinutes())}`;
};

Date.prototype.getMonthText = function() {
    return gettext(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][this.getMonth()]);
};

function ReservationCalendar(element, properties) {
    /**
     * Creates a new ReservationCalendar object. The properties field is a dictionary of properties:
     *
     * machine - The pk of the machine to display for
     */
    this.date = new Date().startOfWeek();
    this.informationHeaders = element.find("thead th").toArray();
    this.days = element.find("tbody .day .reservations").toArray();
    this.element = element;
    this.machine = properties.machine;
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
    });
    let reservationCalendar = this;
    setInterval(() => reservationCalendar.updateCurrentTimeIndication(), 60 * 1000);
};

ReservationCalendar.prototype.update = function () {
    this.updateInformationHeaders();
    let reservationCalendar = this;

    $.get(`${window.location.origin}/reservation/calendar/${this.machine}/reservations`, {
        startDate: this.date.djangoFormat(),
        endDate: this.date.nextWeek().djangoFormat(),
    }, (data) => reservationCalendar.updateReservations.apply(reservationCalendar, [data]), "json");
};

ReservationCalendar.prototype.updateCurrentTimeIndication = function () {
    this.element.find(".current.time.indicator").remove();

    let currentTime = new Date();
    if (currentTime >= this.date && currentTime < this.date.nextWeek()) {
        let timeOfDay = (currentTime.getHours() / 24 + currentTime.getMinutes() / (60 * 24) + currentTime.getSeconds() / (60 * 24 * 60)) * 100;
        let timeIndication = $(`<div class="current time indicator" style="top: ${timeOfDay}%;">`);

        $(this.days[(currentTime.getDay() + 5) % 6]).append(timeIndication);
    }
};

ReservationCalendar.prototype.addReservation = function (reservation) {
    let startTime = Date.parse(reservation.start);
    let endTime = Date.parse(reservation.end);

    let currentDayStart = this.date;
    let currentDayEnd = this.date.nextDay();
    for (let day = 0; day < 7; day++) {
        if (startTime < currentDayEnd && endTime > currentDayStart) {
            let dayStartTime = (Math.max(startTime, currentDayStart) - currentDayStart) / (24 * 60 * 60 * 1000) * 100;
            let dayEndTime = (Math.min(endTime, currentDayEnd) - Math.max(startTime, currentDayStart)) / (24 * 60 * 60 * 1000) * 100;

            let reservationBlock = $(`<div class="${reservation.type} reservation" style="top: ${dayStartTime}%; height: ${dayEndTime}%;">`);
            $(this.days[day]).append(reservationBlock);
        }

        currentDayStart = currentDayStart.nextDay();
        currentDayEnd = currentDayEnd.nextDay();
    }
};

ReservationCalendar.prototype.updateReservations = function (data) {
    this.days.forEach(day => $(day).empty());
    this.updateCurrentTimeIndication();

    let reservationCalendar = this;
    data.reservations.forEach((reservation) => reservationCalendar.addReservation.apply(reservationCalendar, [reservation]));
};

ReservationCalendar.prototype.updateInformationHeaders = function () {
    this.informationHeaders[0].querySelector(".large.header").textContent = this.date.getMonthText();
    this.informationHeaders[0].querySelector(".medium.header").textContent = this.date.getWeekNumber();

    let date = this.date;
    for (let day = 1; day < 8; day++) {
        this.informationHeaders[day].querySelector(".medium.header").textContent = date.getDate();
        date = date.nextDay();
    }
};