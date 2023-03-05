const $memberInfoModal = $("#detailed-member-info");

// Global state to reduce number of jQuery calls
const state = {
    allMembers: [],
    displayedMembers: [],
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
     * Compares `a` and `b`, either using `localCompare()` for strings, or element by element for arrays.
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
     * Displays the selected members' information in a popup modal.
     */
    const textAttributeNamesToValues = {
        "name-header": member.data.name,
        name: member.data.name,
        phone: member.data.phoneDisplay,
        contactEmail: member.data.contactEmail,
        googleEmail: member.data.googleEmail,
        MAKEEmail: member.data.MAKEEmail,
        cardNumber: member.data.cardNumber,
        studyProgram: member.data.studyProgram,
        ntnuStartingSemester: member.data.ntnuStartingSemester,
        githubUsername: member.data.githubUsername,
        discordUsername: member.data.discordUsername,
        minecraftUsername: member.data.minecraftUsername,

        dateJoined: `${member.data.semesterJoined} (${member.data.dateJoined})`,
        dateQuitOrRetired: `${member.data.semesterQuitOrRetired} (${member.data.dateQuitOrRetired})`,
        reasonQuit: member.data.reasonQuit,
        role: member.data.role,
        guidanceExemption: member.data.guidanceExemption,
        comment: member.data.comment,
    };
    for (const textAttribute of Object.keys(textAttributeNamesToValues)) {
        $memberInfoModal.find(`#member-${textAttribute}`)
            .text(textAttributeNamesToValues[textAttribute]);
    }

    for (const editAttribute of ["editURL", "setQuitURL", "canUndoQuit", "setRetiredURL", "canUndoRetired"]) {
        $memberInfoModal.find(`#member-${editAttribute}-button`)
            .toggleClass("display-none", member.data[editAttribute].isEmpty());
    }
    for (const urlAttribute of ["editURL", "setQuitURL", "setRetiredURL"]) {
        $memberInfoModal.find(`#member-${urlAttribute}-button`)
            .attr("href", member.data[urlAttribute]);
    }
    $memberInfoModal.find(`#member-dateQuitOrRetiredLabel`).text(member.data.dateQuitOrRetiredLabel);
    $memberInfoModal.find("#edit-member-status-form")
        .attr("action", member.data.editStatusURL)
        .find(".button[type=submit]")
        .click(function (event) {
            event.preventDefault(); // cancel form submission
            const $clickedButton = $(event.target);
            $memberInfoModal.find("#member-status-action").val($clickedButton.data("status-action"));
            $memberInfoModal.find("#edit-member-status-form").submit();
        });

    for (const emailAttribute of ["contactEmail", "googleEmail", "MAKEEmail"]) {
        $memberInfoModal.find(`#member-${emailAttribute}`)
            .attr("href", `mailto:${member.data[emailAttribute]}`)
            .attr("target", "_blank");
    }
    $memberInfoModal.find("#member-phone").attr("href", `tel:${member.data.phone}`);
    $memberInfoModal.find("#member-githubUsername")
        .attr("href", `https://github.com/${member.data.githubUsername}`)
        .attr("target", "_blank");

    for (const hideableAttribute of ["MAKEEmail", "dateQuitOrRetired", "reasonQuit", "role", "comment"]) {
        $memberInfoModal.find(`#member-${hideableAttribute}`)
            .closest("tr").toggleClass("display-none", member.data[hideableAttribute].isEmpty());
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
    $memberSystemAccessesElement.append(member.data.systemAccesses.map(access => {
        const toggleForm = access.changeURL.isEmpty() ? "" : `
            <div class="ui right floated toggle checkbox">
                <input type="checkbox" value="${!access.value}" ${access.value ? "checked" : ""}
                       data-change-url="${access.changeURL}"/>
                <label></label>
            </div>
        `;
        return $(`
            <tr>
                <td class="six wide column"><b>${access.name}</b></td>
                <td>
                    <div class="ui ${access.value ? "green" : "red"} label">${access.displayText}</div>
                    ${toggleForm}
                </td>
            </tr>
        `);
    }));
    $memberSystemAccessesElement.find(".toggle.checkbox input").click(function () {
        const $toggle = $(this);
        $toggle.attr("name", "value");
        $("#edit-system-access-form").attr("action", $toggle.data("change-url")).submit();
    });

    const $memberCommitteesElement = $memberInfoModal.find("#member-committee");
    $memberCommitteesElement.empty();
    $memberCommitteesElement.append(member.data.committees.map(
        committee => $(
            `<div class="ui ${committee.color} label">${committee.name}</div>`,
        ),
    ));

    $memberInfoModal.modal("show");
}

function filterMatches(filterValues, toMatch) {
    /**
     * Matches if at least one of the filter values matches with the `toMatch` array.
     */
    return filterValues.isEmpty() || filterValues.some(value => toMatch.includes(value));
}

function searchMatches(searchTerm, toMatch) {
    /**
     * Matches if the search term is empty or if there is at least one match in `toMatch`.
     */
    return searchTerm.isEmpty() || toMatch.includes(searchTerm);
}

function getFilterValues(field) {
    /**
     * Creates a list of values that the given filter field is set to.
     */
    return field.val().split(",").filter(value => value !== "");
}


function filter() {
    /**
     * Filters the displayed rows based on the given state.
     */
    const filters = [
        (member) => filterMatches(state.statusFilter, member.data.status.map(status => status.name)),
        (member) => filterMatches(state.committeeFilter, member.data.committees.map(committee => committee.name)),
        (member) => searchMatches(state.searchValue, member.data.name.toLowerCase()),
    ];

    state.displayedMembers = [];
    $.each(state.allMembers, (index, member) => {
        if (filters.every(filter => filter(member)))
            state.displayedMembers.push(member);
    });
    updateDisplayedTableRows();
    $("#displayed-members-count").text(state.displayedMembers.length);
}

function setSort(attributeName, $element) {
    /**
     * Toggles which attribute the table will be sorted by.
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
     * Sorts the table based on the current state.
     */
    state.displayedMembers.sort(function (a, b) {
        return compareElements(a.data[state.sortBy], b.data[state.sortBy]);
    });

    if (state.sortDirection === -1)
        state.displayedMembers.reverse();

    updateDisplayedTableRows(true);
}

function updateDisplayedTableRows(onlyOrderChange = false) {
    const $table = $("#member-table-content");

    function appendDisplayedMembers() {
        $table.append(state.displayedMembers.map((member) => member.$element));
    }

    if (onlyOrderChange) {
        // `append()` moves elements (instead of cloning) if they're already present in the DOM
        appendDisplayedMembers();
    } else {
        $table.empty();
        appendDisplayedMembers();
        $.each(state.displayedMembers, (index, member) => {
            member.$element.click(() => showDetailedMemberInformation(member));
        });
    }
}

function setup() {
    /**
     * Setup of the global state and actions.
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
                phoneDisplay: $row.data("phone-display"),
                contactEmail: $row.data("contact-email"),
                googleEmail: $row.data("google-email"),
                MAKEEmail: $row.data("make-email"),
                cardNumber: $row.data("card-number"),
                studyProgram: $row.data("study-program"),
                ntnuStartingSemester: $row.data("ntnu-starting-semester"),
                githubUsername: $row.data("github-username"),
                discordUsername: $row.data("discord-username"),
                minecraftUsername: $row.data("minecraft-username"),

                dateJoined: $row.data("date-joined"),
                dateJoinedSortable: $row.data("date-joined-sortable"),
                semesterJoined: $row.data("semester-joined"),
                dateQuitOrRetired: $row.data("date-quit-or-retired"),
                dateQuitOrRetiredLabel: $.trim($row.data("date-quit-or-retired-label")),
                semesterQuitOrRetired: $.trim($row.data("semester-quit-or-retired")),
                reasonQuit: $.trim($row.data("reason-quit")),
                role: $.trim($row.data("role")),
                comment: $.trim($row.data("comment")),
                guidanceExemption: $.trim($row.data("guidance-exemption")),
                editURL: $.trim($row.data("edit-url")),
                setQuitURL: $.trim($row.data("set-quit-url")),
                canUndoQuit: $.trim($row.data("can-undo-quit")),
                setRetiredURL: $.trim($row.data("set-retired-url")),
                canUndoRetired: $.trim($row.data("can-undo-retired")),
                editStatusURL: $.trim($row.data("edit-status-url")),
                // This becomes a list of objects consisting of name and color; e.g.: [('Active', 'green')]
                status: $row.data("status").slice(1, -1).replace(/'/g, "").match(/[^()]+/g)
                    .filter(status => status !== ", ")
                    .map(status => status.split(", "))
                    .map(status => ({
                        name: status[0],
                        color: status[1],
                    })),
                // This becomes a list of objects consisting of name, value, displayText and changeURL; e.g.: [("Website", "True", "Yes", "https://...")]
                systemAccesses: $row.data("system-accesses").slice(1, -1).replace(/'/g, "").match(/[^()]+/g)
                    .filter(access => access !== ", ")
                    .map(access => access.split(", "))
                    .map(access => ({
                        name: access[0],
                        value: access[1] === "True",
                        displayText: access[2],
                        changeURL: access[3],
                    })),
                // This becomes a list of objects consisting of name and color; e.g.: [('Dev', 'green')]
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
        state.allMembers.push(member);
    });

    for (const sortAttribute of ["name", "committees", "status", "dateJoinedSortable", "contactEmail", "role", "phone"]) {
        $(`#member-sort-${sortAttribute}`).closest("th").click((e) => setSort(
            sortAttribute, $(e.target).find(".icon"),
        ));
    }

    filter();
    sort();
}

setup();
