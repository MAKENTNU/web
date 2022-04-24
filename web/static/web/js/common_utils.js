function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Fixes a bug (probably) in Fomantic-UI that prevents the user from making the calendar reappear after having selected a time,
 * but before changing the focus to another element on the page. This would cause nothing to happen when clicking the input field again,
 * unless the user made the input field lose focus (blur).
 * This should be called from the `onHidden()` event callback; see https://fomantic-ui.com/modules/calendar.html#/settings.
 * @param $widgetInput the `input` tag used by the widget, as a jQuery object
 */
function fixFomanticUICalendarBlurBug($widgetInput) {
    $widgetInput.blur();
}

/**
 * Fixes a bug in Fomantic-UI that doesn't update the end calendar's focused date when changing the date of the start calendar.
 * This should be called from the `onHidden()` event callback; see https://fomantic-ui.com/modules/calendar.html#/settings.
 * @param $endCalendar the Fomantic-UI end calendar, as a jQuery object
 */
function fixFomanticUIEndCalendarRefreshBug($endCalendar) {
    $endCalendar.calendar("refresh");
}
