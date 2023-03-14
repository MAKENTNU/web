/* These variables must be defined when linking this script */
// noinspection ES6ConvertVarToLetConst
var calendarProperties;

const calendar = new ReservationCalendar($(".reservation-calendar"), calendarProperties);


/*** Code for `reservation_actions.html` ***/

$(".action.list .ui.dropdown.item").dropdown({
    showOnFocus: true,
    action: function (text, value, $selectedElement) {
        // Clicking any machine in the dropdown will automatically load the linked page (since each dropdown element is an <a> tag)
        // but when using the keyboard to select a dropdown element, nothing happens.
        // This code fixes that by opening the linked page:
        const linkedPage = $selectedElement.attr("href");
        window.open(linkedPage, "_self");
    },
});
