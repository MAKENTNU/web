function filterUsers(searchName) {
    $(".users > .item").each(function (index, element) {
        let username = $(element).data("username");
        let fullname = $(element).data("fullname");
        $(element).toggleClass("make_hidden", !isSearchEqual(searchName, username) && !isSearchEqual(searchName, fullname));
    });
}

function isSearchEqual(search, actualValue) {
    return actualValue.toLowerCase().split(" ").join("").indexOf(search.toLowerCase().split(" ").join("")) > -1;
}

$("#user_search_field input").on('input', function (event) {
    filterUsers(event.target.value);
});