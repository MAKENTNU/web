function showSecret(id) {
    console.log(id)
    let hiddenEl = document.getElementsByClassName("hidden");
    hiddenEl[id].style.display = "block";

    let buttonEl = document.getElementsByClassName("notEnter");
    buttonEl[id].style.display = "none";

    setTimeout(hideSecret(id), 3000)
}

function hideSecret(id) {
    let hiddenEl = document.getElementsByClassName("hidden");
    hiddenEl[id].style.display = "none";

    let buttonEl = document.getElementsByClassName("notEnter");
    buttonEl[id].style.display = "block";


}