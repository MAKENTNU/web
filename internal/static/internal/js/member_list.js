/* These variables must be defined when linking this script */
// noinspection ES6ConvertVarToLetConst
var initialFilterStatuses;
// noinspection ES6ConvertVarToLetConst
var memberListURL;
// noinspection ES6ConvertVarToLetConst
var selectedMemberPK;

const SEARCH_FIELD_SEPARATOR = "∨"; // the Logical Or symbol (not a lowercase V)
const PAGE_TITLE_SEPARATOR = " | ";
const MODAL_DEFAULT_DURATION = 400; // see https://fomantic-ui.com/modules/modal.html#/settings

const $pageTitle = $("head>title");
const $memberInfoModal = $("#detailed-member-info");
const $filterStatusInput = $("input[name=filter-status]");
const $filterCommitteeInput = $("input[name=filter-committee]");
const $searchInput = $("input[name=search-text]");

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

let isChangingMemberModalStateThroughHistoryAPI = false;
const initialPageTitle = $pageTitle.text();

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

function setPageTitlePrefix(titlePrefix) {
    $pageTitle.text(titlePrefix
        ? `${titlePrefix}${PAGE_TITLE_SEPARATOR}${initialPageTitle}`
        : initialPageTitle);
}

function getMember(pk) {
    return state.allMembers.find(
        (member) => member.data.pk === pk,
    );
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
    changeHistoryAfterShowingMemberModal(member);
}

function changeHistoryAfterShowingMemberModal(member) {
    if (isChangingMemberModalStateThroughHistoryAPI) {
        isChangingMemberModalStateThroughHistoryAPI = false;
        return;
    }
    // If this is right after the page has initially loaded with a selected member (i.e. directly visiting the `member_detail` URL):
    if (!window.history.state && selectedMemberPK) {
        setPageTitlePrefix(member.data.name);
        return;
    }
    window.history.pushState({memberPK: member.data.pk}, "", member.data.detailURL);
    // Must set the title *after* calling `pushState()`
    setPageTitlePrefix(member.data.name);
}

function filterMatches(filterValues, toMatch) {
    /**
     * Matches if at least one of the filter values matches with the `toMatch` array.
     */
    return filterValues.isEmpty() || filterValues.some(value => toMatch.includes(value));
}

function searchMatches(searchTerm, member) {
    /**
     * Matches if the search term is empty or if there is at least one match in `member.searchableDataString`.
     */
    searchTerm = searchTerm.trim().toLowerCase();
    // `searchableDataString` is already trimmed and lowercased when it's defined
    return searchTerm.isEmpty() || member.searchableDataString.includes(searchTerm);
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
        (member) => searchMatches(state.searchValue, member),
    ];

    state.displayedMembers = [];
    // On the off chance that a user searches for `SEARCH_FIELD_SEPARATOR`, don't display any search results
    // - as it shouldn't match with any fields, and could otherwise be confusing
    if (!state.searchValue.includes(SEARCH_FIELD_SEPARATOR)) {
        $.each(state.allMembers, (index, member) => {
            if (filters.every(filter => filter(member)))
                state.displayedMembers.push(member);
        });
    }
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
    $filterStatusInput.change(() => {
        state.statusFilter = getFilterValues($filterStatusInput);
        filter();
    });
    state.statusFilter = getFilterValues($filterStatusInput);

    $filterCommitteeInput.change(() => {
        state.committeeFilter = getFilterValues($filterCommitteeInput);
        filter();
    });
    state.committeeFilter = getFilterValues($filterCommitteeInput);

    $searchInput.on("input", () => {
        state.searchValue = $searchInput.val();
        filter();
    });
    state.searchValue = $searchInput.val();

    // Package member information
    $("#member-table tbody tr").each((index, row) => {
        const $row = $(row);

        const searchableData = {
            name: $row.data("name"),
            phone: $row.data("phone"),
            phoneDisplay: $row.data("phone-display"),
            phoneWithoutSpaces: $row.data("phone").replaceAll(" ", ""),
            contactEmail: $row.data("contact-email"),
            googleEmail: $row.data("google-email"),
            MAKEEmail: $row.data("make-email"),
            cardNumber: $row.data("card-number"),
            studyProgram: $row.data("study-program"),
            ntnuStartingSemester: $row.data("ntnu-starting-semester"),
            githubUsername: $row.data("github-username"),
            discordUsername: $row.data("discord-username"),
            minecraftUsername: $row.data("minecraft-username"),

            semesterJoined: $row.data("semester-joined"),
            reasonQuit: $.trim($row.data("reason-quit")),
            role: $.trim($row.data("role")),
            comment: $.trim($row.data("comment")),
        };

        const member = {
            data: {
                pk: $row.data("pk").toString(), // a PK can in principle be anything, not just an int
                detailURL: $row.data("detail-url"),
                ...searchableData,

                dateJoined: $row.data("date-joined"),
                dateJoinedSortable: $row.data("date-joined-sortable"),
                dateQuitOrRetired: $row.data("date-quit-or-retired"),
                dateQuitOrRetiredLabel: $.trim($row.data("date-quit-or-retired-label")),
                semesterQuitOrRetired: $.trim($row.data("semester-quit-or-retired")),
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
            // Searching using a precalculated string should be faster than iterating through every field of every member.
            // Also, join the fields using an uncommon character,
            // to not produce unexpected search results when e.g. a search term matches the end of one field and the beginning of the next.
            searchableDataString: Object.values(searchableData).join(SEARCH_FIELD_SEPARATOR).toLowerCase(),
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

$(".ui.dropdown").dropdown();
$filterStatusInput.parent().dropdown("set selected", initialFilterStatuses);

setup();

$memberInfoModal.modal({
    duration: MODAL_DEFAULT_DURATION,
    onHide: function ($element) {
        if (isChangingMemberModalStateThroughHistoryAPI) {
            isChangingMemberModalStateThroughHistoryAPI = false;
            return true; // let the modal hide normally
        }

        window.history.pushState({memberPK: null}, "", memberListURL);
        // Must set the title *after* calling `pushState()`
        setPageTitlePrefix("");
    },
});
if (selectedMemberPK)
    showDetailedMemberInformation(getMember(selectedMemberPK));

// When the user navigates backwards or forwards in the browser history:
window.onpopstate = function (event) {
    isChangingMemberModalStateThroughHistoryAPI = true;
    // Make the closing/opening transitions happen instantaneously (will be reset below)
    // - which also circumvents a bug that sometimes prevents the modal from opening when navigating the browser history too quickly, it seems
    $memberInfoModal.modal("setting", "duration", 0);

    let pageTitlePrefixToRestore;
    const memberPK = getCurrentPageMemberPK(event.state);
    if (memberPK) {
        const member = getMember(memberPK);
        showDetailedMemberInformation(member);
        pageTitlePrefixToRestore = member.data.name;
    } else {
        $memberInfoModal.modal("hide");
        pageTitlePrefixToRestore = "";
    }

    // Make the page title match the current URL when navigating backwards or forwards in the browser history
    // (doing this is apparently necessary in Firefox, but not in Chrome).
    // (Also, must set the title *after* running code calling `pushState()`)
    setPageTitlePrefix(pageTitlePrefixToRestore);
    // Reset the duration setting (after changing it above)
    $memberInfoModal.modal("setting", "duration", MODAL_DEFAULT_DURATION);
};

function getCurrentPageMemberPK(popEventState) {
    // `popEventState` will be `null` when the user navigates back to when the page was initially loaded,
    // or when the browser has no stored state for the page (e.g. when restoring a tab after having closed and restarted the browser)
    if (popEventState)
        return popEventState.memberPK;
    // Shouldn't use `selectedMemberPK` here, as in some browsers (like Firefox),
    // when restoring the session of a tab whose current page was the `member_detail` page,
    // and you're navigating backwards/forwards to the `member_list` page,
    // that variable will still be set - which is unexpected to this script's code.

    const pathName = window.location.pathname;
    if (pathName === memberListURL)
        return null;
    else {
        const member = state.allMembers.find(member => member.data.detailURL === pathName);
        if (member)
            return member.data.pk;
        else
            console.error(`Unable to find member with detail URL ${pathName}`);
    }
}
