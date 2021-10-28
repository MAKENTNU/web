$("#user").parent().dropdown({
    onChange: function (userPK, text) {
        $.ajax(`${LANG_PREFIX}/reservation/quota/user/${userPK}/`, {
            success: function (data, textStatus) {
                $("#user-quotas").html(data);
                setupDeleteModal();
            },
        });
    },
});
