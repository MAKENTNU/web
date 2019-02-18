$('#user').parent().dropdown({
    onChange: function (username, text) {
        $.ajax(langPrefix + "/reservation/quota/user/" + username + "/", {
            success: function (data, textStatus) {
                $("#user-quotas").html(data);
                setupDeleteModal();
            },
        });
    },
});
