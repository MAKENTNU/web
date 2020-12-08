const $memberInfoModal = $("#detailed-member-info");

// Global state to reduce number of jQuery calls
const state = {
    members: [],
    statusFilter: [],
    committeeFilter: [],
    searchValue: "",
    sortBy: "committees",
    sortDirection: -1,
    $sortElement: $("#member-sort-committees"),
};

String.prototype.isEmpty = function () {
    return this.length === 0;
};
Array.prototype.isEmpty = function () {
    return this.length === 0;
};

function compareElements(a, b) {
    /**
     * Compares two elements a and b either using localCompare for strings or element by element for arrays
     */
    if (typeof a === "string")
        return a.localeCompare(b);
    if (Array.isArray(a)) {
        for (let index = 0; index < Math.min(a.length, b.length); index++) {
            const elementComparision = a[index].name.localeCompare(b[index].name);
            if (elementComparision !== 0)
                return elementComparision;
        }
        return a.length - b.length;
    }
    return 0;
}

function showDetailedMemberInformation(member) {
    /**
     * Displays the selected members information in a popup modal
     */
    const textAttributeNamesToValues = {
        "name-header": member.data.name,
        name: member.data.name,
        phone: member.data.phone,
        email: member.data.email,
        cardNumber: member.data.cardNumber,
        studyProgram: member.data.studyProgram,
        dateJoined: `${member.data.termJoined} (${member.data.dateJoined})`,
        dateQuit: `${member.data.termQuit} (${member.data.dateQuit})`,
        reasonQuit: member.data.reasonQuit,
        role: member.data.role,
        guidanceExemption: member.data.guidanceExemption,
        comment: member.data.comment,
    };
    for (let textAttribute of Object.keys(textAttributeNamesToValues)) {
        $memberInfoModal.find(`#member-${textAttribute}`)
            .text(textAttributeNamesToValues[textAttribute]);
    }

    for (let urlAttribute of ["editUrl", "quitUrl", "undoQuitUrl", "retireUrl", "undoRetireUrl"]) {
        $memberInfoModal.find(`#member-${urlAttribute}`)
            .attr("href", member.data[urlAttribute])
            .toggleClass("display-none", member.data[urlAttribute].isEmpty());
    }
    $memberInfoModal.find("#member-phone").attr("href", `tel:${member.data.phone}`);
    $memberInfoModal.find("#member-email").attr("href", `mailto:${member.data.email}`);

    for (let hideableAttribute of ["dateQuit", "reasonQuit", "role", "comment"]) {
        $memberInfoModal.find(`#member-${hideableAttribute}`)
            .parent().toggleClass("display-none", member.data[hideableAttribute].isEmpty());
    }

    const $memberStatusElement = $memberInfoModal.find("#member-status, #member-status-header");
    $memberStatusElement.empty();
    $memberStatusElement.append(member.data.status.map(
        status => $(
            `<div class="ui ${status.color} label">${status.name}</div>`,
        ),
    ));

    const $memberSystemAccessesElement = $memberInfoModal.find("#member-system-accesses");
    $memberSystemAccessesElement.empty();
    $memberSystemAccessesElement.append(member.data.systemAccesses.map(access => $(`
        <tr>
            <td class="six wide column"><b>${access.name}</b></td>
            <td>
                <div class="ui ${access.value ? "green" : "red"} label">${access.displayText}</div>
                <a class="right floated orange link" href="${access.changeUrl}">
                    ${access.changeUrl.isEmpty() ? "" : gettext("Change")}
                </a>
            </td>
        </tr>
    `)));

    const $memberCommitteesElement = $memberInfoModal.find("#member-committee");
    $memberCommitteesElement.empty();
    $memberCommitteesElement.append(member.data.committees.map(
        committee => $(
            `<div class="ui ${committee.color} label">${committee.name}</div>`,
        ),
    ));

    $memberInfoModal.modal("show");
}

function filterAllows(filterValues, toMatch) {
    /**
     * Checks if at least one of the filter values matches with the given array
     */
    return filterValues.isEmpty() || filterValues.some(value => toMatch.includes(value));
}

function searchAllows(searchValue, toMatch) {
    /**
     * Checks if the search value is empty or if there is at least one match on the value
     */
    return searchValue.isEmpty() || toMatch.includes(searchValue);
}

function getFilterValues(field) {
    /**
     * Creates a list of values that the given filter field is set to
     */
    return field.val().split(",").filter(value => value !== "");
}


function filter() {
    /**
     * Filters the displayed rows based on the given state
     */
    const filters = [
        (member) => filterAllows(state.statusFilter, member.data.status.map(status => status.name)),
        (member) => filterAllows(state.committeeFilter, member.data.committees.map(committee => committee.name)),
        (member) => searchAllows(state.searchValue, member.data.name.toLowerCase()),
    ];

    const $table = $("#member-table-content");

    let displayedMembersCount = 0;
    $.each(state.members, (index, member) => {
        member.$element.remove();
        if (filters.every(el => el(member))) {
            $table.append(member.$element);
            member.$element.click(() => showDetailedMemberInformation(member));
            displayedMembersCount++;
        }
    });
    $("#displayed-members-count").text(displayedMembersCount);
}

function setSort(attributeName, $element) {
    /**
     * Toggles which attribute the table will be sorted by
     */
    state.$sortElement.toggleClass(state.sortDirection === 1 ? "down" : "up", false);
    if (attributeName === state.sortBy) {
        state.sortDirection *= -1;
    } else {
        state.sortBy = attributeName;
        state.sortDirection = 1;
        state.$sortElement = $element;
    }
    state.$sortElement.toggleClass(state.sortDirection === 1 ? "down" : "up", true);
    sort();
}

function sort() {
    /**
     * Sorts the table based on the current state
     */
    state.members.sort(function (a, b) {
        return compareElements(a.data[state.sortBy], b.data[state.sortBy]);
    });

    if (state.sortDirection === -1) {
        state.members.reverse();
    }

    $("#member-table tbody").append(state.members.map((member) => member.$element));
}

function setup() {
    /**
     * Setup of the global state and actions
     */
    const $statusInput = $("input[name=filter-status]");
    $statusInput.change(() => {
        state.statusFilter = getFilterValues($statusInput);
        filter();
    });
    state.statusFilter = getFilterValues($statusInput);

    const $committeeInput = $("input[name=filter-committee]");
    $committeeInput.change(() => {
        state.committeeFilter = getFilterValues($committeeInput);
        filter();
    });
    state.committeeFilter = getFilterValues($committeeInput);

    const $searchInput = $("input[name=search-text]");
    $searchInput.on("input", () => {
        state.searchValue = $searchInput.val().toLowerCase();
        filter();
    });
    state.searchValue = $searchInput.val().toLowerCase();

    // Package member information
    $("#member-table tbody tr").each((index, row) => {
        const $row = $(row);

        const member = {
            data: {
                pk: $row.data("pk"),
                name: $row.data("name"),
                phone: $row.data("phone"),
                email: $row.data("email"),
                cardNumber: $row.data("card-number"),
                studyProgram: $row.data("study-program"),
                dateJoined: $row.data("date-joined"),
                termJoined: $row.data("term-joined"),
                dateQuit: $row.data("date-quit"),
                termQuit: $.trim($row.data("term-quit")),
                reasonQuit: $.trim($row.data("reason-quit")),
                role: $.trim($row.data("role")),
                comment: $.trim($row.data("comment")),
                guidanceExemption: $.trim($row.data("guidance-exemption")),
                editUrl: $.trim($row.data("edit-url")),
                quitUrl: $.trim($row.data("quit-url")),
                undoQuitUrl: $.trim($row.data("undo-quit-url")),
                retireUrl: $.trim($row.data("retire-url")),
                undoRetireUrl: $.trim($row.data("undo-retire-url")),
                // Membership status is a list of pairs of status name and color: [('Active', 'green')]. Need to parse this list.
                status: $row.data("status").slice(1, -1).replace(/'/g, "").match(/[^()]+/g)
                    .filter(status => status !== ", ")
                    .map(status => status.split(", "))
                    .map(status => ({
                        name: status[0],
                        color: status[1],
                    })),
                // System accesses is a list of quads of name, value, displayText and changeUrl: [("Website", "True", "Yes", "https://...")]. Need to parse this list
                systemAccesses: $row.data("system-accesses").slice(1, -1).replace(/'/g, "").match(/[^()]+/g)
                    .filter(access => access !== ", ")
                    .map(access => access.split(", "))
                    .map(access => ({
                        name: access[0],
                        value: access[1] === "True",
                        displayText: access[2],
                        changeUrl: access[3],
                    })),
                // Committees is a list of pairs of name and color: [('Dev', 'green')]. Need to parse this list
                committees: $row.data("committees").slice(1, -1).replace(/'/g, "").match(/[^()]*/g)
                    .filter(committee => committee !== ", " && !committee.isEmpty())
                    .map(committee => committee.split(", "))
                    .map(committee => ({
                        name: committee[0],
                        color: committee[1],
                    })),
            },
            $element: $row,
        };

        member.$element = $row;
        state.members.push(member);
    });

    for (let sortAttribute of ["name", "committees", "status", "dateJoined", "email", "role", "phone"]) {
        $(`#member-sort-${sortAttribute}`).closest("th").click((e) => setSort(
            sortAttribute, $(e.target).find(".icon"),
        ));
    }

    filter();
    sort();
}

setup();
