$("#user").parent().dropdown({
    onChange: function (userPK, text, $choice) {
        $.ajax(`${LANG_PREFIX}/reservation/quota/user/${userPK}/`, {
            success: function (data, textStatus) {
                $("#user-quotas").html(data);
                setupDeleteModal();
            },
        });
    },
});
