const $memberInfoModal = $("#detailed-member-info");

// Global state to reduce number of jQuery calls
const state = {
    members: [],
    statusFilter: [],
    committeeFilter: [],
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
    $memberInfoModal.find("#member-name, #member-name-header").text(member.data.name);
    $memberInfoModal.find("#member-phone").text(member.data.phone)
        .attr("href", `tel:${member.data.phone}`);
    $memberInfoModal.find("#member-email").text(member.data.email)
        .attr("href", `mailto:${member.data.email}`);
    $memberInfoModal.find("#member-cardNumber").text(member.data.cardNumber);
    $memberInfoModal.find("#member-studyProgram").text(member.data.studyProgram);

    $memberInfoModal.find("#member-dateJoined").text(`${member.data.termJoined} (${member.data.dateJoined})`);
    $memberInfoModal.find("#member-role").text(member.data.role)
        .parent().toggleClass("display-none", member.data.role.isEmpty());
    $memberInfoModal.find("#member-dateQuit").text(`${member.data.termQuit} (${member.data.dateQuit})`)
        .parent().toggleClass("display-none", member.data.dateQuit.isEmpty());
    $memberInfoModal.find("#member-reasonQuit").text(member.data.reasonQuit)
        .parent().toggleClass("display-none", member.data.reasonQuit.isEmpty());
    $memberInfoModal.find("#member-comment").text(member.data.comment)
        .parent().toggleClass("display-none", member.data.comment.isEmpty());
    $memberInfoModal.find("#member-guidanceExemption").text(member.data.guidanceExemption);

    $memberInfoModal.find("#member-editUrl").attr("href", member.data.editUrl)
        .toggleClass("display-none", member.data.editUrl.isEmpty());
    $memberInfoModal.find("#member-quitUrl").attr("href", member.data.quitUrl)
        .toggleClass("display-none", member.data.quitUrl.isEmpty());
    $memberInfoModal.find("#member-undoQuitUrl").attr("href", member.data.undoQuitUrl)
        .toggleClass("display-none", member.data.undoQuitUrl.isEmpty());
    $memberInfoModal.find("#member-retireUrl").attr("href", member.data.retireUrl)
        .toggleClass("display-none", member.data.retireUrl.isEmpty());
    $memberInfoModal.find("#member-undoRetireUrl").attr("href", member.data.undoRetireUrl)
        .toggleClass("display-none", member.data.undoRetireUrl.isEmpty());

    const $memberStatusElement = $memberInfoModal.find("#member-status, #member-status-header");
    $memberStatusElement.empty();
    $memberStatusElement.append(member.data.status.map(
        status => $(
            `<div class="ui ${status.color} label">${status.name}</div>`,
        ),
    ));

    const $memberSystemAccessesElement = $memberInfoModal.find("#member-systemAccesses");
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
    $.each(state.members, (index, member) => {
        const shouldShow = filterAllows(state.statusFilter, member.data.status.map(status => status.name))
            && filterAllows(state.committeeFilter, member.data.committees.map(committee => committee.name));
        member.$element.toggleClass("display-none", !shouldShow);
    });
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

        $row.click(() => showDetailedMemberInformation(member));
        member.$element = $row;
        state.members.push(member);
    });

    $("#member-sort-name").parent().click((e) => setSort(
        "name", $(e.target).find(".icon"),
    ));
    $("#member-sort-committees").parent().click((e) => setSort(
        "committees", $(e.target).find(".icon"),
    ));
    $("#member-sort-status").parent().click((e) => setSort(
        "status", $(e.target).find(".icon"),
    ));
    $("#member-sort-dateJoined").parent().click((e) => setSort(
        "dateJoined", $(e.target).find(".icon"),
    ));
    $("#member-sort-email").parent().click((e) => setSort(
        "email", $(e.target).find(".icon"),
    ));
    $("#member-sort-role").parent().click((e) => setSort(
        "role", $(e.target).find(".icon"),
    ));
    $("#member-sort-phone").parent().click((e) => setSort(
        "phone", $(e.target).find(".icon"),
    ));

    filter();
    sort();
}

setup();
