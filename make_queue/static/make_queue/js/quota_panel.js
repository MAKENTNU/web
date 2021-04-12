$("#user").parent().dropdown({
    onChange: function (username, text) {
        $.ajax(`${LANG_PREFIX}/reservation/quota/user/${username}/`, {
            success: function (data, textStatus) {
                $("#user-quotas").html(data);
                setupDeleteModal();
            },
        });
    },
});
