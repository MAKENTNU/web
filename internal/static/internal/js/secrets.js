function showSecret(buttonId) {
    let hiddenEl = document.getElementsByClassName("hidden")
    let button = document.getElementsByTagName("button")
    for (let i =0; i<hiddenEl.length; i++) {
        if (hiddenEl[i].id == buttonId) {
            hiddenEl[i].style.display = "inline"
            button[i].style.display = "none"

            setTimeout(() => {
                hiddenEl[i].style.display = "none"
                button[i].style.display = "inline"
            }, 5000)
        }
    }
}
