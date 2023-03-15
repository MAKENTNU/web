/* These variables must be defined when linking this script */
// noinspection ES6ConvertVarToLetConst
var csrfToken;
// noinspection ES6ConvertVarToLetConst
var voteForSkillSuggestionURL;

$(".add-voter").click(function () {
    addVoterPost($(this), $(this).data("pk"), $(this).data("forced"));
});

$(".delete-suggestion").click(function () {
    deleteSuggestionPost($(this), $(this).data("delete-url"));
});

function addVoterPost($element, pk, forced) {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        },
    });
    $.ajax({
        type: "POST",
        url: voteForSkillSuggestionURL,
        data: {
            "pk": pk,
            "forced": forced,
        },
        success: function (data) {
            if (data["is_forced"]) {
                $element.closest("tr").remove();
            }
            $element.addClass("green");
            $element.addClass("disabled");
            $element.html(gettext("Voted!"));

            if (!data["user_exists"]) {
                const incrementedCount = parseInt($element.parent().siblings("#vote-count").html()) + 1;
                $element.parent().siblings("#vote-count").html(incrementedCount);
            }
            if (data["skill_passed"]) {
                $element.closest("tr").remove();
            }
        },
    });
}

function deleteSuggestionPost($element, deleteURL) {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        },
    });

    $.ajax({
        type: "DELETE",
        url: deleteURL,
        success: function (data) {
            if (data["suggestion_deleted"]) {
                $element.closest("tr").remove();
            }
        },
    });
}
