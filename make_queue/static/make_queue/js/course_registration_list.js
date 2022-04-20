const DISPLAY_NONE_CLASS = "display-none";
// Used to keep track of selected users
const SELECTED_ROW_CLASS = "active";

// Global state to reduce the number of DOM operations required
const state = {
    page: 0,
    elements: [],
    numPages: 0,
    elementsPerPage: 20,
    paginationElements: 2,
    sortBy: "name",
    sortOrder: true,
    searchValue: "",
    statusValue: "",
    selectedCount: 0,
    onlyShowSelectedUsers: false,
};

function updateSelectedCountText() {
    const usersSelectedText = interpolate(
        ngettext("%(num)s user selected", "%(num)s users selected", state.selectedCount),
        {num: state.selectedCount}, true,
    );
    $("#num-users-selected").text(usersSelectedText);
}

// Make each row selectable
$("tbody tr").click(function () {
    const hasClass = $(this).hasClass(SELECTED_ROW_CLASS);

    state.selectedCount += hasClass ? -1 : 1;
    $(this).toggleClass(SELECTED_ROW_CLASS, !hasClass);

    updateSelectedCountText();
    $("#selected-actions").toggleClass(DISPLAY_NONE_CLASS, state.selectedCount === 0);
    if (state.onlyShowSelectedUsers || state.selectedCount === 0) {
        state.onlyShowSelectedUsers = state.onlyShowSelectedUsers && state.selectedCount;
        filter();
    }
});

// Filters which registrations that fit the current state
function filter() {
    let numRegistrationsFiltered = 0;
    for (const element of state.elements) {
        if (state.onlyShowSelectedUsers) {
            element.display = element.$element.hasClass(SELECTED_ROW_CLASS);
        } else {
            element.display =
                (element.name.includes(state.searchValue) || element.username.includes(state.searchValue))
                && element.status.includes(state.statusValue);
        }

        numRegistrationsFiltered += element.display;
        if (!element.display)
            element.$element.toggleClass(DISPLAY_NONE_CLASS, true);
    }
    $("#num-registrations-filtered").text(numRegistrationsFiltered);
    state.numPages = Math.ceil(numRegistrationsFiltered / state.elementsPerPage);
    state.page = 0;
    sort();
}

// Sorts the elements based on the column to sort and its order
function sort() {
    state.elements.sort(function (a, b) {
        return a[state.sortBy].localeCompare(b[state.sortBy]);
    });

    if (!state.sortOrder)
        state.elements.reverse();

    updateDisplay();
}

// Status filter element
$("#status-filter").parent().dropdown({
    onChange: function (value, text, $choice) {
        state.statusValue = value;
        filter();
    },
});

// Button to toggle if only selected users should be shown
$("#show-selected-users").click(function () {
    state.onlyShowSelectedUsers = !state.onlyShowSelectedUsers;
    filter();
});

// Button to clear all selection of users
$("#clear-selected-users").click(function () {
    state.onlyShowSelectedUsers = false;
    state.selectedCount = 0;
    state.elements.forEach(function (element) {
        element.$element.toggleClass(SELECTED_ROW_CLASS, false);
    });
    $("#selected-actions").toggleClass(DISPLAY_NONE_CLASS, true);
    filter();
});

// TODO: reformat to reduce code duplication with other parts of the file
// Button to select all shown users
$("#select-shown-users").click(function () {
    const shownUnselectedUserRows = state.elements.filter((e) =>
        !e.$element.hasClass(DISPLAY_NONE_CLASS)
        && !e.$element.hasClass(SELECTED_ROW_CLASS),
    );
    if (shownUnselectedUserRows.length === 0)
        return;

    shownUnselectedUserRows.forEach(function (e) {
        e.$element.toggleClass(SELECTED_ROW_CLASS, true);
    });
    state.selectedCount += shownUnselectedUserRows.length;
    updateSelectedCountText();
    // Ensure that it's visible, even if it's already visible
    $("#selected-actions").toggleClass(DISPLAY_NONE_CLASS, false);
});

// The bulk status change dropdown
$("#status-set").parent().dropdown({
    onChange: function (value, statusText, $choice) {
        const $modal = $("#set-status-modal");

        $("#set-status-text").text(statusText);

        $("#status").val(value);
        const $form = $modal.find("form");
        // Keep the status input field and csrf token, but clear the rest (in the case that cancel has been clicked)
        $form.children().slice(2).remove();

        const selectedUsers = [];
        state.elements.forEach(function (element) {
            if (element.$element.hasClass(SELECTED_ROW_CLASS)) {
                $form.append($(`<input type="hidden" value="${element.pk}" name="users"/>`));
                selectedUsers.push(element.$element.data("name"));
            }
        });

        $("#selected-users").text(selectedUsers.join(", "));

        $modal.find(".cancel.button").click(function () {
            $("#status-set").parent().dropdown("clear");
        });
        $modal.find(".ok.button").click(function () {
            $form.submit();
        });

        $modal.modal("show");
    },
});

// The search field for usernames
$("#search").on("input", function () {
    state.searchValue = $(this).val().toLowerCase();
    filter();
}).on("keydown", function (event) {
    // We do not want to trigger form submit on pressing the enter key. The
    // default functionality is search, and pressing the enter key should
    // emulate that.
    if (event.key === "Enter") {
        // Lose focus of the input field. This is important for mobile as
        // hitting enter is equivalent to hitting "search".
        $(this).blur();

        // Prevent form submission
        event.preventDefault();
        return false;
    }
});

// Each table header element can be clicked to change the sorting of the table
$("th").click(function () {
    const columnName = $(this).data("column-name");
    $("th i").remove();
    if (state.sortBy === columnName) {
        state.sortOrder = !state.sortOrder;
    } else {
        state.sortOrder = true;
        state.sortBy = columnName;
    }
    sort();

    const sortDirection = state.sortOrder ? "down" : "up";
    $(this).append($(`<i class="sort ${sortDirection} icon"></i>`));
});

// Calculates the range of numbers to show in the pagination bar of the table
function calculateRangePagination() {
    let start = Math.max(0, state.page - state.paginationElements);
    let end = Math.min(state.numPages - 1, state.page + state.paginationElements);

    // Special handling of edges to make sure that the correct number of elements are shown in the pagination bar
    if (start === 0)
        end = Math.min(state.numPages - 1, end + state.paginationElements - (state.page - start));

    if (end === state.numPages - 1)
        start = Math.max(0, start - state.paginationElements + (end - state.page));

    return {
        start: start,
        end: end,
    };
}

// Toggles which rows to show based on the current state
function updateDisplay() {
    const startIndex = state.page * state.elementsPerPage;
    const endIndex = (state.page + 1) * state.elementsPerPage;

    let numRegistrationsFiltered = 0;
    let displayedRegistrationsCount = 0;

    let lastInsertedElement = null;

    // Show or hide registrations based on filtering and the selected page
    for (const registration of state.elements) {
        if (!registration.display)
            continue;

        if (startIndex <= numRegistrationsFiltered && numRegistrationsFiltered < endIndex) {
            registration.$element.toggleClass(DISPLAY_NONE_CLASS, false);

            if (lastInsertedElement != null) {
                // Elements are sorted in an array, as to update the DOM only when necessary
                lastInsertedElement.after(registration.$element);
            }
            lastInsertedElement = registration.$element;

            displayedRegistrationsCount++;
        } else {
            registration.$element.toggleClass(DISPLAY_NONE_CLASS, true);
        }

        numRegistrationsFiltered++;
    }
    const registrationsDisplayedHTML = interpolate(
        ngettext("Displaying %(num)s registration", "Displaying %(num)s registrations", displayedRegistrationsCount),
        {num: `<b>${displayedRegistrationsCount}</b>`}, true,
    );
    $("#num-registrations-displayed").html(registrationsDisplayedHTML);

    // Removes old numbers in pagination bar and adds new ones
    $("#pagination-bar").children().slice(2, -2).remove();

    const pageRange = calculateRangePagination();

    $leftChangeElement.toggleClass("disabled", state.page === 0);
    $leftSkipElement.toggleClass("disabled", state.page === 0);
    $rightChangeElement.toggleClass("disabled", state.page === state.numPages - 1);
    $rightSkipElement.toggleClass("disabled", state.page === state.numPages - 1);

    for (let page = pageRange.start; page <= pageRange.end; page++) {
        const $pageElement = $(`<a class="item">${page + 1}</a>`);
        if (page === state.page)
            $pageElement.toggleClass("active", true);

        $pageElement.click(function () {
            state.page = page;
            updateDisplay();
        });
        $rightChangeElement.before($pageElement);
    }
}

const $rightSkipElement = $("#right-skip");
const $rightChangeElement = $("#right-change");
const $leftChangeElement = $("#left-change");
const $leftSkipElement = $("#left-skip");
const $downloadUsersForm = $("#download-users");

// Setup the initial state
function setupState() {
    $("tbody tr").each(function () {
            state.elements.push({
                pk: $(this).data("pk"),
                name: $(this).data("name").toLowerCase(),
                username: $(this).data("username").toLowerCase(),
                cardNumber: ("0000000000" + $(this).data("card-number").toString()).slice(-10),
                date: $(this).data("date"),
                status: $(this).data("status"),
                raise3DCourse: $(this).data("raise3d-course"),
                display: true,
                $element: $(this),
            });
        },
    );

    state.numPages = Math.ceil(state.elements.length / state.elementsPerPage);

    // Setup the action of each of the default buttons in the pagination bar
    $rightChangeElement.click(function () {
        state.page = Math.min(state.page + 1, state.numPages - 1);
        updateDisplay();
    });

    $rightSkipElement.click(function () {
        state.page = state.numPages - 1;
        updateDisplay();
    });

    $leftChangeElement.click(function () {
        state.page = Math.max(0, state.page - 1);
        updateDisplay();
    });

    $leftSkipElement.click(function () {
        state.page = 0;
        updateDisplay();
    });

    $downloadUsersForm.submit(function () {
        let selected = [];
        if (state.onlyShowSelectedUsers)
            selected = state.elements.filter((e) => e.display).map(e => e.pk);
        $downloadUsersForm.find("#selected").val(selected);
    });

    // Initial display refresh (`sort()` also calls `updateDisplay()`)
    sort();
}

setupState();
