let state = {
    page: 0,
    elements: [],
    numPages: 0,
    elementPerPage: 20,
    paginationElements: 2,
    sortBy: "name",
    sortOrder: true,
    search_value: "",
    status_value: "",
    selectedCount: 0,
    onlyShowSelectedUsers: false,
};

$("tbody tr").click(function () {
    let hasClass = $(this).hasClass("active");

    state.selectedCount += Math.pow(-1, hasClass);
    $(this).toggleClass("active", !hasClass);

    $("#num-selected").text(state.selectedCount);
    $("#selected-actions").toggleClass("make_hidden", state.selectedCount === 0);
});

function filter() {
    let numberOfShown = 0;
    for (let elementIndex = 0; elementIndex < state.elements.length; elementIndex++) {
        let element = state.elements[elementIndex];

        if (state.onlyShowSelectedUsers) {
            element.display = element.element.hasClass("active");
        } else {
            element.display =
                (element.name.includes(state.search_value) || element.username.includes(state.search_value)) &&
                element.status.includes(state.status_value);
        }

        numberOfShown += element.display;
        if (!element.display) {
            element.element.toggleClass("make_hidden", true);
        }
    }
    $("#number-displayed").text(numberOfShown);
    state.numPages = Math.ceil(numberOfShown / state.elementPerPage);
    state.page = 0;
    sort();
}

function sort() {
    state.elements.sort(function (a, b) {
        return a[state.sortBy].localeCompare(b[state.sortBy])
    });

    if (!state.sortOrder) {
        state.elements.reverse();
    }

    toggle_display();
}

$("#status_filter").parent().dropdown({
    onChange: function (value) {
        state.status_value = value;
        filter();
    }
});

$("#show-selected-users").click(function () {
    state.onlyShowSelectedUsers = !state.onlyShowSelectedUsers;
    filter();
});

$("#clear-selected-users").click(function () {
    state.onlyShowSelectedUsers = false;
    state.selectedCount = 0;
    state.elements.forEach(function (element) {
        element.element.toggleClass("active", false);
    });
    $("#selected-actions").toggleClass("make_hidden", true);
    filter();
});

$("#status_set").parent().dropdown({
    onChange: function (value, statusText) {
        let modal = $("#set-status-modal");

        $("#set-status-text").text(statusText);

        $("#status").val(value);
        let form = modal.find("form");
        // Keep the status input field and csrf token, but clear the rest (in the case that cancel has been clicked)
        form.children().slice(2).remove();

        let selectedUsers = [];
        state.elements.forEach(function (element) {
            if (element.element.hasClass("active")) {
                form.append($("<input type='hidden' value='" + element.pk + "' name='users'>"));
                selectedUsers.push(element.element.data("name"));
            }
        });

        $("#selected-users").text(selectedUsers.join(", "));


        modal.find(".cancel.button").click(function() {
            $("#status_set").parent().dropdown("clear");
        });
        modal.find(".ok.button").click(function() {
            form.submit();
        });

        modal.modal("show");
    }
});

$("#search").on("input", function () {
    state.search_value = $(this).val().toLowerCase();
    filter();
});

$("th").click(function () {
    let columnName = $(this).data("column-name");
    $("th i").remove();
    if (state.sortBy === columnName) {
        state.sortOrder = !state.sortOrder;
    } else {
        state.sortOrder = true;
        state.sortBy = columnName;
    }
    sort();
    $(this).append(state.sortOrder ? $("<i class=\"ui icon sort down\"></i>") : $("<i class=\"ui icon sort up\"></i>"));
});


function calculate_range_pagination() {
    let start = Math.max(0, state.page - state.paginationElements);
    let end = Math.min(state.numPages - 1, state.page + state.paginationElements);

    if (start === 0) {
        end = Math.min(state.numPages - 1, end + state.paginationElements - (state.page - start));
    }

    if (end === state.numPages - 1) {
        start = Math.max(0, start - state.paginationElements + (end - state.page));
    }

    return {
        start: start,
        end: end,
    }
}

function toggle_display() {
    let start_index = state.page * state.elementPerPage;
    let end_index = (state.page + 1) * state.elementPerPage;

    let filteredElements = 0;

    let lastInsertedElement = null;

    for (let elementIndex = 0; elementIndex < state.elements.length; elementIndex++) {
        let element = state.elements[elementIndex];
        if (!element.display) continue;

        if (start_index <= filteredElements && filteredElements < end_index) {
            element.element.toggleClass("make_hidden", false);

            if (lastInsertedElement != null) {
                lastInsertedElement.after(element.element);
            }

            lastInsertedElement = element.element;
        } else {
            element.element.toggleClass("make_hidden", true);
        }

        filteredElements++;
    }

    let pagination_element = $("#pagination-bar");
    pagination_element.children().slice(2, -2).remove();

    let page_range = calculate_range_pagination();

    leftChangeElement.toggleClass("disabled", state.page === 0);
    leftSkipElement.toggleClass("disabled", state.page === 0);
    rightChangeElement.toggleClass("disabled", state.page === state.numPages - 1);
    rightSkipElement.toggleClass("disabled", state.page === state.numPages - 1);


    for (let page = page_range.start; page <= page_range.end; page++) {
        let page_element = $("<a class='item'>" + (page + 1) + "</a>");
        if (page === state.page) {
            page_element.toggleClass("active", true);
        }
        page_element.click(function () {
            state.page = page;
            toggle_display();
        });
        rightChangeElement.before(page_element);
    }
}

let rightSkipElement = $("#right-skip");
let rightChangeElement = $("#right-change");
let leftChangeElement = $("#left-change");
let leftSkipElement = $("#left-skip");

function setup_pagination() {

    $("tbody tr").each(function () {
            state.elements.push({
                pk: $(this).data("pk"),
                name: $(this).data("name").toLowerCase(),
                username: $(this).data("username").toLowerCase(),
                cardNumber: ("0000000000" + $(this).data("card-number").toString()).slice(-10),
                date: $(this).data("date"),
                status: $(this).data("status"),
                display: true,
                element: $(this),
            });
        }
    );

    state.numPages = Math.ceil(state.elements.length / state.elementPerPage);

    rightChangeElement.click(function () {
        state.page = Math.min(state.page + 1, state.numPages - 1);
        toggle_display();
    });

    rightSkipElement.click(function () {
        state.page = state.numPages - 1;
        toggle_display();
    });

    leftChangeElement.click(function () {
        state.page = Math.max(0, state.page - 1);
        toggle_display();
    });

    leftSkipElement.click(function () {
        state.page = 0;
        toggle_display();
    });

    toggle_display();
}

setup_pagination();