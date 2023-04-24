/* These variables must be defined when linking this script */
// noinspection ES6ConvertVarToLetConst
var requestedUserPK;

$(".tabular.menu .item").tab();

const $userDropdown = $("#user").parent();
$userDropdown.dropdown({
    fullTextSearch: true,
    forceSelection: true,
    onChange: function (userPK, text, $choice) {
        $.ajax(`${LANG_PREFIX}/admin/reservation/quotas/users/${userPK}/`, {
            success: function (data, textStatus) {
                $("#user-quotas").html(data);
                setUpDeleteModal();
            },
        });
    },
});
if (requestedUserPK)
    $userDropdown.dropdown("set selected", requestedUserPK);
