/* These variables must be defined when linking this script */
// noinspection ES6ConvertVarToLetConst
var calendarProperties;

const calendar = new ReservationCalendar($(".reservation-calendar"), calendarProperties);


/*** Code for `reservation_actions.html` ***/

$(".dropdown.item").dropdown({
    showOnFocus: true,
});
