let memberInfoModal = $("#detailed-member-info");

// Global state to reduce number of jQuery calls
let state = {
    members: [],
    statusFilter: [],
    committeeFilter: [],
    searchValue: "",
    sortBy: "committees",
    sortDirection: -1,
    sortElement: $("#member-sort-committees"),
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
    if (typeof a === "string") return a.localeCompare(b);
    if (Array.isArray(a)) {
        for (let index = 0; index < Math.min(a.length, b.length); index++) {
            let elementComparision = a[index].name.localeCompare(b[index].name);
            if (elementComparision !== 0) return elementComparision;
        }

        return a.length - b.length;
    }
    return 0;
}


function showDetailedMemberInformation(member) {
    /**
     * Displays the selected members information in a popup modal
     */
    memberInfoModal.find("#member-name, #member-name-header").text(member.data.name);
    memberInfoModal.find("#member-phone").text(member.data.phone).attr("href", `tel:${member.data.phone}`);
    memberInfoModal.find("#member-email").text(member.data.email).attr("href", `mailto:${member.data.email}`);
    memberInfoModal.find("#member-card-number").text(member.data.cardNumber);
    memberInfoModal.find("#member-study-program").text(member.data.studyProgram);

    memberInfoModal.find("#member-joined").text(`${member.data.termJoined} (${member.data.dateJoined})`);
    memberInfoModal.find("#member-role").text(member.data.role).parent().toggleClass("make_hidden", member.data.role.isEmpty());
    memberInfoModal.find("#member-quit").text(`${member.data.termQuit} (${member.data.dateQuit})`).parent().toggleClass("make_hidden", member.data.dateQuit.isEmpty());
    memberInfoModal.find("#member-quit-reason").text(member.data.reasonQuit).parent().toggleClass("make_hidden", member.data.reasonQuit.isEmpty());
    memberInfoModal.find("#member-comment").text(member.data.comment).parent().toggleClass("make_hidden", member.data.comment.isEmpty());
    memberInfoModal.find("#member-guidance-exemption").text(member.data.guidanceExemption);

    memberInfoModal.find("#member-edit").attr("href", member.data.editUrl).toggleClass("make_hidden", member.data.editUrl.isEmpty());
    memberInfoModal.find("#member-set-quit").attr("href", member.data.quitUrl).toggleClass("make_hidden", member.data.quitUrl.isEmpty());
    memberInfoModal.find("#member-set-not-quit").attr("href", member.data.undoQuitUrl).toggleClass("make_hidden", member.data.undoQuitUrl.isEmpty());
    memberInfoModal.find("#member-set-retired").attr("href", member.data.retireUrl).toggleClass("make_hidden", member.data.retireUrl.isEmpty());
    memberInfoModal.find("#member-set-not-retired").attr("href", member.data.undoRetireUrl).toggleClass("make_hidden", member.data.undoRetireUrl.isEmpty());

    let memberStatusElement = memberInfoModal.find("#member-status, #member-status-header");
    memberStatusElement.empty();
    memberStatusElement.append(member.data.status.map(status => $(`<div class="ui ${status.color} label">${status.name}</div>`)));


    let memberSystemAccessesElement = memberInfoModal.find("#member-system-accesses");
    memberSystemAccessesElement.empty();
    memberSystemAccessesElement.append(member.data.systemAccesses.map(access => $(`
        <tr>
            <td class="six wide column"><b>${access.name}</b></td>
            <td>
                <div class="ui ${access.value ? "green" : "red"} label">${access.displayText}</div>
                <a href="${access.changeUrl}" class="right floated orange link">${access.changeUrl.isEmpty() ? "" : gettext("Change")}</a>
            </td>
        </tr>
    `)));

    let memberCommitteesElement = memberInfoModal.find("#member-committee");
    memberCommitteesElement.empty();
    memberCommitteesElement.append(member.data.committees.map(committee => $(`<div class="ui ${committee.color} label">${committee.name}</div>"`)));

    memberInfoModal.modal("show");
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
    let filters = [
        (member) => filterAllows(state.statusFilter, member.data.status.map(status => status.name)),
        (member) => filterAllows(state.committeeFilter, member.data.committees.map(committee => committee.name)),
        (member) => searchAllows(state.searchValue, member.data.name.toLowerCase()),
    ]

    $.each(state.members, (index, member) => {
        let shouldShow = filters.every(el => el(member));
        member.element.toggleClass("make_hidden", !shouldShow);
    });
}

function setSort(attributeName, element) {
    /**
     * Toggles which attribute the table will be sorted by
     */
    state.sortElement.toggleClass(state.sortDirection === 1 ? "down" : "up", false);
    if (attributeName === state.sortBy) {
        state.sortDirection *= -1;
    } else {
        state.sortBy = attributeName;
        state.sortDirection = 1;
        state.sortElement = element;
    }
    state.sortElement.toggleClass(state.sortDirection === 1 ? "down" : "up", true);
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

    $("#member-table tbody").append(state.members.map((member) => member.element));
}

function setup() {
    /**
     * Setup of the global state and actions
     */
    let statusInput = $("input[name=filter-status]");
    statusInput.change(() => {
        state.statusFilter = getFilterValues(statusInput);
        filter();
    });
    state.statusFilter = getFilterValues(statusInput);

    let committeeInput = $("input[name=filter-committee]");
    committeeInput.change(() => {
        state.committeeFilter = getFilterValues(committeeInput);
        filter();
    });
    state.committeeFilter = getFilterValues(committeeInput);

    let searchInput = $("input[name=search-text]");
    searchInput.on("input", () => {
        state.searchValue = searchInput.val().toLowerCase();
        filter();
    })
    state.searchValue = searchInput.val().toLowerCase();

    // Package member information
    $("#member-table tbody tr").each((index, row) => {
        row = $(row);

        let member = {
            data: {
                pk: row.data("pk"),
                name: row.data("name"),
                phone: row.data("phone"),
                email: row.data("email"),
                cardNumber: row.data("card-number"),
                studyProgram: row.data("study-program"),
                dateJoined: row.data("date-joined"),
                termJoined: row.data("term-joined"),
                dateQuit: row.data("date-quit"),
                termQuit: row.data("term-quit"),
                reasonQuit: row.data("reason-quit"),
                role: row.data("role"),
                comment: row.data("comment"),
                guidanceExemption: row.data("guidance-exemption"),
                editUrl: row.data("edit"),
                quitUrl: row.data("quit"),
                undoQuitUrl: row.data("undo-quit"),
                retireUrl: row.data("retire"),
                undoRetireUrl: row.data("undo-retire"),
                // Membership status is a list of pairs of status name and color: [('Active', 'green')]. Need to parse this list.
                status: row.data("status").slice(1, -1).replace(/'/g, "").match(/[^()]+/g).filter(status => status !== ", ").map(status => status.split(", ")).map(status => ({
                    name: status[0],
                    color: status[1],
                })),
                // System accesses is a list of quads of name, value, displayText and changeUrl: [("Website", "True", "Yes", "https://...")]. Need to parse this list
                systemAccesses: row.data("system-accesses").slice(1, -1).replace(/'/g, "").match(/[^()]+/g).filter(access => access !== ", ").map(access => access.split(", ")).map(access => ({
                    name: access[0],
                    value: access[1] === "True",
                    displayText: access[2],
                    changeUrl: access[3],
                })),
                // Committees is a list of pairs of name and color: [('Dev', 'green')]. Need to parse this list
                committees: row.data("committees").slice(1, -1).replace(/'/g, "").match(/[^()]*/g).filter(committee => committee !== ", " && !committee.isEmpty()).map(committee => committee.split(", ")).map(committee => ({
                    name: committee[0],
                    color: committee[1],
                })),
            },
            element: row,
        };

        row.click(() => showDetailedMemberInformation(member));
        member.element = row;
        state.members.push(member);
    });

    $("#member-sort-name").parent().click((e) => setSort("name", $(e.target).find(".icon")));
    $("#member-sort-committees").parent().click((e) => setSort("committees", $(e.target).find(".icon")));
    $("#member-sort-status").parent().click((e) => setSort("status", $(e.target).find(".icon")));
    $("#member-sort-joined").parent().click((e) => setSort("dateJoined", $(e.target).find(".icon")));
    $("#member-sort-email").parent().click((e) => setSort("email", $(e.target).find(".icon")));
    $("#member-sort-role").parent().click((e) => setSort("role", $(e.target).find(".icon")));
    $("#member-sort-phone").parent().click((e) => setSort("phone", $(e.target).find(".icon")));

    filter();
    sort();
}

setup();
