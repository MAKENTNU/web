// Requires reservation_rule_utils.js and date_utils.js

function ReservationCalendar(element, properties) {
    /**
     * Creates a new ReservationCalendar object. The properties field is a dictionary of properties:
     *
     * machine - The pk of the machine to display for
     * selection - A boolean indicating if selection is allowed
     * canBreakRules - A boolean indicating if the user can break the reservation rules
     * date [optional] - The date to show at the start
     * onSelect [optional] - A function to handle what should be shown on selection
     * selectionPopupContent [optional] - A function to generate the content to be shown in the popup made by the
     *                                    default onSelect function. Can return jQuery elements or an HTML string.
     */
    this.date = new Date().startOfWeek();
    if (properties.date) {
        this.date = properties.date.startOfWeek();
    }

    this.informationHeaders = element.find("thead th").toArray();
    this.days = element.find("tbody .day .reservations").toArray();
    this.element = element;
    this.machine = properties.machine;
    this.selection = properties.selection;
    this.canBreakRules = properties.canBreakRules;

    if (properties.onSelect) {
        this.onSelection = properties.onSelect;
    }

    if (properties.selectionPopupContent) {
        this.selectionPopupContent = properties.selectionPopupContent;
    }

    this.init();
}

ReservationCalendar.prototype.init = function () {
    /**
     * Initialises the calendar
     */
    // Run the update function to retrieve reservations
    this.update();
    this.element.find(".next.button").click(() => {
        this.showDate(this.date.nextWeek());
    });

    this.element.find(".current.button").click(() => {
        this.showDate(new Date().startOfWeek());
    });

    this.element.find(".previous.button").click(() => {
        this.showDate(this.date.previousWeek());
    });

    // Update the red line indicating the current time every minute
    let calendar = this;
    setInterval(() => calendar.updateCurrentTimeIndication(), 60 * 1000);

    if (this.selection) {
        this.setupSelection();
    }
};

ReservationCalendar.prototype.onSelection = function () {
    /**
     * Function called after the user has selected an area in the calendar, creates a popup with content from the
     * selectionPopupContent function. Both this function and selectionPopupContent can be overridden, which is the
     * reason for their separation.
     */
    $(this.element.find(".selection.reservation").first()).popup({
        position: "right center",
        html: this.selectionPopupContent(),
        // Allows the popup to stay open when the user does not hover over the selection
        on: "onload",
    }).popup("show").popup("get popup").addClass("time-selection default popup");
};

ReservationCalendar.prototype.selectionPopupContent = function () {
    /**
     * Creates the default content for the popup after selection is finished. The content produced is a simple card with
     * information about the selection and a button to create a reservation using the selection.
     */
    let dateString;
    let startTime = this.getSelectionStartTime();
    let endTime = this.getSelectionEndTime();
    let calendar = this;

    // Use a shorthand notation if the start and end time is on the same day
    if (startTime.getDate() === endTime.getDate()) {
        dateString = `${startTime.dateString()} <br/> ${startTime.timeString()} - ${endTime.timeString()}`;
    } else {
        dateString = `${startTime.dateString()} ${startTime.timeString()} - ${endTime.dateString()} ${endTime.timeString()}`;
    }

    let popupContent = $(`
            <div class="new-reservation-popup ui card">
                <div class="ui content">
                    <div class="header">${gettext("New reservation")}</div>
                    <div class="description">
                        ${dateString}
                    </div>
                </div>
                <div class="ui bottom attached make-bg-yellow button">
                    ${gettext("Reserve")}
                </div>
            </div>
    `);

    popupContent.find(".button").on("mousedown touchstart", () => {
        // Create and submit a hidden form to create a new reservation
        let form = $(
            `<form method='POST' action='${langPrefix}/reservation/create/${calendar.machine}/'>`,
        ).appendTo(popupContent);
        $("input[name=csrfmiddlewaretoken]").clone().appendTo(form);
        // Hide the form in case something fails
        $("<input class='make_hidden' name='start_time'>").val(startTime.djangoFormat()).appendTo(form);
        $("<input class='make_hidden' name='end_time'>").val(endTime.djangoFormat()).appendTo(form);
        $("<input class='make_hidden' name='machine_name'>").val(calendar.machine).appendTo(form);
        form.submit();

        // Don't allow other events, like the deselection to be ran
        return false;
    });

    return popupContent;
};

ReservationCalendar.prototype.setupSelection = function () {
    /**
     * Creates all object fields required for selection and all event handlers for clicks, touches and drags.
     * The selectionStart field holds the first tap and the selectionEnd field holds the hovered value.
     */
    this.selectionStart = null;
    this.selectionEnd = null;
    this.selecting = false;

    let calendar = this;

    for (let day = 0; day < 7; day++) {
        // Start selection when the mouse is clicked
        $(this.days[day]).parent().on("mousedown touchstart", (event) => {
            calendar.selecting = true;
            calendar.selectionStart = calendar.getHoverDate(event, day);
            calendar.selectionEnd = calendar.selectionStart;
            return false;
        }).on("mousemove touchmove", (event) => {
            // Update the selection when any of the days are hovered over
            if (calendar.selecting) {
                calendar.selectionEnd = calendar.getHoverDate(event, day);
                calendar.updateSelection();
            }
        });

        // The header for the week should set the selection date to the start of the week
        $(this.informationHeaders[0]).on("mousemove touchmove", () => {
            if (calendar.selecting) {
                calendar.selectionEnd = calendar.date;
                calendar.updateSelection();
            }
        });

        // The headers above the dates should set the selection date to the start of the given day
        $(this.informationHeaders[day + 2]).on("mousemove touchmove", () => {
            if (calendar.selecting) {
                calendar.selectionEnd = calendar.date.nextDays(day);
                calendar.updateSelection();
            }
        });
    }

    // The part of the calendar that shows the timestamps should set the selection date to the start of the week
    this.element.find(".time.information").on("mousemove touchmove", () => {
        if (calendar.selecting) {
            calendar.selectionEnd = calendar.date;
            calendar.updateSelection();
        }
    });

    // Hovering over the footer will set the selection to the end of the day hovered under
    let footer = this.element.find("tfoot");
    footer.on("mousemove touchmove", (event) => {
        if (calendar.selecting) {
            // Handle both touch and mouse correctly
            let xPosition = event.touches === undefined ? event.pageX : event.touches[0].pageX;
            let hoverPosition = (xPosition - footer.offset().left) / footer.width();
            let dayHoveredUnder = Math.floor(hoverPosition * 8);
            calendar.selectionEnd = calendar.date.nextDays(dayHoveredUnder);
            calendar.updateSelection();
        }
    });

    // Stop selection whenever the mouse is released
    $(document).on("mouseup touchend", () => {
        if (calendar.selecting) {
            calendar.selecting = false;
            calendar.updateSelection();
            calendar.onSelection();
        }
    });

    // Remove the selection when the document is clicked
    $(document).on("mousedown touchstart", () => {
        if (!calendar.selecting && calendar.selectionStart != null) {
            calendar.resetSelection();
        }
    })
};

ReservationCalendar.prototype.resetSelection = function () {
    /**
     * Resets the selection if any
     */
    this.selecting = false;
    this.selectionStart = null;
    this.selectionEnd = null;
    this.element.find(".selection.reservation").remove();
};

ReservationCalendar.prototype.updateSelection = function () {
    /**
     * Updates the shown selection
     */
    let calendar = this;
    // Only draw the selection if the selection dates are set
    if (this.selectionStart != null) {
        let startTime = this.getSelectionStartTime();
        let endTime = this.getSelectionEndTime();
        this.element.find(".selection.reservation").remove();
        // A selection can be shown in the same way as the other reservations, just with other classes and callback
        this.drawReservation(startTime, endTime, "selection reservation", (element, day) => {
            // If this is the first day of the selection, add the start time indicator
            if (day <= startTime && startTime < day.nextDay()) {
                element.append($(`<div class='selection start time'>${startTime.timeString()}</div>`));

                // Add an element for expanding the selection if the selection is finished
                if (!this.selecting) {
                    let expander = $(`<div class='selection expand top'>`);
                    element.append(expander);
                    expander.on("mousedown touchstart", () => {
                        // Modification is done by simply starting the selection anew, now with the selection bound to
                        // the end time
                        calendar.selectionStart = endTime;
                        calendar.selectionEnd = startTime;
                        calendar.selecting = true;
                        calendar.updateSelection();
                        // We don't want to trigger any other events
                        return false;
                    });
                }
            }

            // If this is the last day of the selection, add the end time indicator
            if (day < endTime && endTime <= day.nextDay()) {
                element.append($(`<div class='selection end time'>${endTime.timeString()}</div>`))

                // Add an element for expanding the selection if the selection is finished
                if (!this.selecting) {
                    let expander = $(`<div class='selection expand bottom'>`);
                    element.append(expander);
                    expander.on("mousedown touchstart", () => {
                        // Modification is done by simply starting the selection anew, now with the selection bound to
                        // the start time
                        calendar.selectionStart = startTime;
                        calendar.selectionEnd = endTime;
                        calendar.selecting = true;
                        calendar.updateSelection();
                        // We don't want to trigger any other events
                        return false;
                    });
                }
            }
        });
    }
};

ReservationCalendar.prototype.getHoverDate = function (event, day) {
    /**
     * Calculate the date for the given hover event. The `day` parameter is the day of the week
     */
    let numberOfMillisecondsInDay = 24 * 60 * 60 * 1000;
    let date = this.date.nextDays(day);
    let dayElement = $(event.target).closest(".day");
    // Handle both touch and mouse
    let yPosition = event.touches === undefined ? event.pageY : event.touches[0].pageY;
    let timeOfDay = (yPosition - dayElement.offset().top) / dayElement.height();
    date = new Date(date.valueOf() + timeOfDay * numberOfMillisecondsInDay);
    return date;
};

ReservationCalendar.prototype.getSelectionStartTime = function () {
    /**
     * Simple endpoint for getting the start time of the selection without handling getSelectionTimes
     */
    return this.getSelectionTimes()[0];
};

ReservationCalendar.prototype.getSelectionEndTime = function () {
    /**
     * Simple endpoint for getting the end time of the selection without handling getSelectionTimes
     */
    return this.getSelectionTimes()[1];
};

ReservationCalendar.prototype.getSelectionTimes = function () {
    /**
     * Calculates the start and end time of the selection, so that they fit within the given rules and restrictions
     * given for reservations.
     */
    let startTime = this.roundTime(Math.max(new Date(), Math.min(this.selectionStart, this.selectionEnd)));
    let endTime = this.roundTime(Math.max(new Date(), this.selectionStart, this.selectionEnd));
    let adjusted = true;

    // Adjust the start and end times so that the selection does not overlap any reservations
    while (adjusted) {
        adjusted = false;
        this.reservations.forEach((reservation) => {
            // Change the start time if either the start time is inside the reservation or the reservation is within the
            // selection and the user clicked after the reservation in the calendar.
            if (reservation.end > startTime && (reservation.start <= startTime || (reservation.end <= endTime && this.selectionStart > reservation.start))) {
                startTime = reservation.end;
                adjusted = true;
            }

            // Change the end time if either the end time is inside the reservation or the reservation is within the
            // selection and the user clicked before the reservation in the calendar.
            if (reservation.start < endTime && (reservation.end > endTime || (reservation.start >= startTime && this.selectionStart < reservation.end))) {
                endTime = reservation.start;
                adjusted = true;
            }
        });
    }

    if (!this.canBreakRules) {
        // Decrease the end time or increase the start time based on the reservation rules. Decrease the end time if it
        // is later than where the user clicked in the calendar (rounded due to endTime being rounded), otherwise
        // increase the start time
        if (endTime > this.roundTime(this.selectionStart)) {
            endTime = modifyToFirstValid(this.reservationRules, startTime, endTime, 1);
        } else if (startTime < this.roundTime(this.selectionStart)) {
            startTime = modifyToFirstValid(this.reservationRules, startTime, endTime, 0);
        }
    }

    return [startTime, endTime];
};

ReservationCalendar.prototype.roundTime = function (time) {
    /**
     * Rounds the given date to the next 5th minute (11:00:01 -> 11:05:00)
     */
    let millisecondsIn5Minutes = 5 * 60 * 1000;
    return new Date(Math.ceil(time / millisecondsIn5Minutes) * millisecondsIn5Minutes);
};

ReservationCalendar.prototype.changeMachine = function (machine) {
    /**
     * Changes the machine used for finding reservations and updates the calendar
     */
    this.machine = machine;
    this.update();
};

ReservationCalendar.prototype.updateCanBreakRules = function (canbreakRules) {
    /**
     * Setter for the canBreakRules property
     */
    this.canBreakRules = canbreakRules;
};

ReservationCalendar.prototype.showDate = function (date) {
    /**
     * Shows the given date in the calendar
     */
    this.date = date.startOfWeek();
    this.update();
};

ReservationCalendar.prototype.update = function () {
    this.updateInformationHeaders();
    let calendar = this;

    $.get(`${window.location.origin}/reservation/calendar/${this.machine}/reservations`, {
        startDate: this.date.djangoFormat(),
        endDate: this.date.nextWeek().djangoFormat(),
    }, (data) => calendar.updateReservations.apply(calendar, [data]), "json");

    $.get(`${window.location.origin}/reservation/calendar/${this.machine}/rules`, {}, (data) => {
        calendar.reservationRules = data.rules;
    })
};

ReservationCalendar.prototype.updateCurrentTimeIndication = function () {
    /**
     * Moves the time indication line from its current position to the position of the current time
     */
    this.element.find(".current.time.indicator").remove();
    let hoursInDay = 24;
    let minutesInDay = hoursInDay * 60;
    let secondsInDay = minutesInDay * 60;

    let currentTime = new Date();
    if (currentTime >= this.date && currentTime < this.date.nextWeek()) {
        let timeOfDay = (currentTime.getHours() / hoursInDay + currentTime.getMinutes() / minutesInDay + currentTime.getSeconds() / secondsInDay) * 100;
        let timeIndication = $(`<div class="current time indicator" style="top: ${timeOfDay}%;">`);

        $(this.days[(currentTime.getDay() + 6) % 7]).append(timeIndication);
    }
};

ReservationCalendar.prototype.addReservation = function (reservation) {
    /**
     * Adds the given reservation to the calendar
     */
    reservation.start = new Date(Date.parse(reservation.start));
    reservation.end = new Date(Date.parse(reservation.end));

    this.drawReservation(reservation.start, reservation.end, `${reservation.type} reservation`, (htmlElement) => {
        // If the reservation has some text to display on hover, create a popup
        if (reservation.displayText !== undefined) {
            this.createPopup(htmlElement, reservation);
        }
    }, reservation.eventLink);
};

ReservationCalendar.prototype.drawReservation = function (startDate, endDate, classes, callback, linkToDisplay = null) {
    /**
     * Draws a reservation in the calendar. The `classes` parameter is the CSS classes given to each block displayed in
     * the calendar. The `callback` parameter is a function that is called with the given HTML element and date as
     * arguments each time this function creates a new HTML element for the reservation.
     */
    let date = this.date;
    let millisecondsInDay = 24 * 60 * 60 * 1000;
    // Iterate each day of the week since the reservation may go over several days
    for (let day = 0; day < 7; day++) {
        if (endDate > date && startDate < date.nextDay()) {
            // Find where the reservation should start and end in the given day
            let dayStartTime = (Math.max(date, startDate) - date) / millisecondsInDay * 100;
            let dayEndTime = (Math.min(date.nextDay(), endDate) - Math.max(date, startDate)) / millisecondsInDay * 100;
            const reservationHtmlTag = linkToDisplay ? `a href="${linkToDisplay}" target="_blank"` : "div";
            let reservationBlock = $(
                `<${reservationHtmlTag} class="${classes}" style="top: ${dayStartTime}%; height: ${dayEndTime}%;">`,
            );
            $(this.days[day]).append(reservationBlock);

            // Call any given callback function
            if (callback !== undefined) {
                callback(reservationBlock, date);
            }
        }
        date = date.nextDay();
    }
};

ReservationCalendar.prototype.createPopup = function (reservationElement, reservation) {
    /**
     * Creates a popup for a given reservation
     */
    let content;

    if (reservation.user !== undefined) {
        // If the backend hands us extensive data on the reservation (for admins)
        let duration = `${reservation.start.getDayTextShort()} ${reservation.start.timeString()} - ${reservation.end.getDayTextShort()} ${reservation.end.timeString()}`;

        content = `
            <div class="header">${gettext("Reservation")}</div>
            <div><b>${gettext("Name")}:</b> ${reservation.user}</div>
            <div><b>${gettext("Email")}:</b> ${reservation.email}</div>
            <div><b>${gettext("Time")}:</b> ${duration}</div>
        `;

        if (reservation.displayText !== "") {
            content += `<div><b>${gettext("Comment")}:</b></div><div>${reservation.displayText}</div>`
        }
    } else if (reservation.eventLink !== undefined) {
        // Events should show the name of the event
        content = `<div class="header">${reservation.displayText}</div>`;
    } else {
        // Otherwise just display the given text
        content = reservation.displayText;
    }

    reservationElement.popup({
        position: "top center",
        html: content,
    });
};

ReservationCalendar.prototype.updateReservations = function (data) {
    /**
     * A callback function used after performing an AJAX request to the backend for reservations. This would for example
     * be called when changing weeks.
     */

    // Reset the calendar
    this.days.forEach(day => $(day).empty());
    this.updateCurrentTimeIndication();

    // Add all new reservations
    let calendar = this;
    data.reservations.forEach((reservation) => calendar.addReservation.apply(calendar, [reservation]));

    this.reservations = data.reservations;
    this.resetSelection();
};

ReservationCalendar.prototype.updateInformationHeaders = function () {
    /**
     * Updates the information shown in the table headers to the information of the current week
     */
    this.informationHeaders[0].querySelector(".large.header").textContent = this.date.getMonthText();
    this.informationHeaders[0].querySelector(".medium.header").textContent = this.date.getWeekNumber();
    this.informationHeaders[1].querySelector(".large.header").textContent = this.date.getMonthTextShort();
    this.informationHeaders[1].querySelector(".medium.header").textContent = this.date.getWeekNumber();

    let date = this.date;
    for (let day = 2; day < 9; day++) {
        this.informationHeaders[day].querySelector(".medium.header").textContent = date.getDate();
        date = date.nextDay();
    }
};
