let memberInfoModal = $("#detailed-member-info");

// Global state to reduce number of JQuery calls
let state = {
    members: [],
    stateFilter: [],
    committeeFilter: [],
};

String.prototype.isEmpty = function () {
    return this.length === 0;
};
Array.prototype.isEmpty = function () {
    return this.length === 0;
};


function showDetailedMemberInformation(member) {
    /**
     * Displays the selected members information in a popup modal
     */
    memberInfoModal.find("#member-name, #member-name-header").text(member.data.name);
    memberInfoModal.find("#member-phone").text(member.data.phone);
    memberInfoModal.find("#member-email").text(member.data.email).attr("href", "mailto:" + member.data.email);
    memberInfoModal.find("#member-card-number").text(member.data.cardNumber);
    memberInfoModal.find("#member-study-program").text(member.data.studyProgram);

    memberInfoModal.find("#member-joined").text(`${member.data.termJoined} (${member.data.dateJoined})`);
    memberInfoModal.find("#member-role").text(member.data.role).parent().toggleClass("make_hidden", member.data.role.isEmpty());
    memberInfoModal.find("#member-quit").text(`${member.data.termQuit} (${member.data.dateQuit})`).parent().toggleClass("make_hidden", member.data.dateQuit.isEmpty());
    memberInfoModal.find("#member-quit-reason").text(member.data.reasonQuit).parent().toggleClass("make_hidden", member.data.reasonQuit.isEmpty());
    memberInfoModal.find("#member-comment").text(member.data.comment).parent().toggleClass("make_hidden", member.data.comment.isEmpty());
    memberInfoModal.find("#member-guidance-exemption").text(member.data.guidanceExemption);

    let memberStateElement = memberInfoModal.find("#member-state, #member-state-header");
    memberStateElement.empty();
    memberStateElement.append(member.data.state.map(state => $(`<div class="ui ${state.color} label">${state.name}</div>`)));


    let memberSystemAccessesElement = memberInfoModal.find("#member-system-accesses");
    memberSystemAccessesElement.empty();
    memberSystemAccessesElement.append(member.data.systemAccesses.map(access => $(`<tr>
        <td class="six wide column"><b>${access.name}</b></td>
        <td><div class="ui ${access.value ? "green" : "red"} label">${access.displayText}</div></td>
    </tr>`)));

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
        let shouldShow = filterAllows(state.stateFilter, member.data.state.map(state => state.name))
            && filterAllows(state.committeeFilter, member.data.committees.map(committee => committee.name));
        member.element.toggleClass("make_hidden", !shouldShow);
    });
}

function setup() {
    /**
     * Setup of the global state and actions
     */
    let stateInput = $("input[name=filter-state]");
    stateInput.change(() => {
        state.stateFilter = getFilterValues(stateInput);
        filter();
    });
    state.stateFilter = getFilterValues(stateInput);

    let committeeInput = $("input[name=filter-committee]");
    committeeInput.change(() => {
        state.committeeFilter = getFilterValues(committeeInput);
        filter();
    });
    state.committeeFilter = getFilterValues(committeeInput);

    // Package member information
    $("#member-table tbody tr").each((index, row) => {
        row = $(row);

        let member = {
            data: {
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
                // Membership state is a list of pairs of state and color: [('Active', 'green')]. Need to parse this list.
                state: row.data("state").slice(1, -1).replace(/'/g, "").match(/[^()]+/g).filter(state => state !== ", ").map(state => state.split(", ")).map(state => ({
                    name: state[0],
                    color: state[1],
                })),
                // System accesses is a list of triples of name, value and displayText: [("Website", "True", "Yes")]. Need to parse this list
                systemAccesses: row.data("system-accesses").slice(1, -1).replace(/'/g, "").match(/[^()]+/g).filter(access => access !== ", ").map(access => access.split(", ")).map(access => ({
                    name: access[0],
                    value: access[1] === "True",
                    displayText: access[2],
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
        state.members.push(member)
    });

    filter();
}

setup();
