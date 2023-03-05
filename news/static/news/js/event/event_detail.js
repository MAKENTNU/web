// Start with the first accordion element open
$(".ui.accordion").accordion("open", 0);

/*
Fomantic-UI sticky does not adjust the height of the context element when the sticky part is taller. In the
cases where this needs to be done, we must make sure that the change is performed after Fomantic-UI has
performed their own changes. Hopefully this will be fixed at some point in Fomantic-UI, and we can remove
this stopgap solution. In most cases, the solution will not be needed, as the average number of occurrences
is low enough that the event content is taller than the sticky part.
*/
setTimeout(() => {
    const $sticky = $(".ui.sticky.rail-content");
    const $context = $("#sticky");

    function fixHeight() {
        // If the height of the sticky is greater than the context (the event content), then increase the
        // height of the event to be equal (that is, the sticky is simply a single scroll).
        if ($sticky.height() > $context.height())
            $context.height(`${$sticky.height()}px`);
    }

    // The sticky code resets the height on each resizing of the window. Thus, the change must be performed
    // each time the window is resized. To catch any other cases as well, we use the "onReposition" action.
    $sticky.sticky("setting", "onReposition", () => {
        // Use a timeout of 50 to make sure that the Fomantic-UI code is finished
        setTimeout(fixHeight, 50);
    });
    fixHeight();
}, 50); // use a timeout of 50 to make sure that the Fomantic-UI code is finished
