document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".toggle_notes_button").forEach(button => {
        button.addEventListener("click", async function () {
            const targetId = this.dataset.target;
            const notesUrl = this.dataset.notesUrl;
            const row = document.getElementById(targetId);

            if (!row) return;

            const isHidden = row.classList.contains("guidance_notes_row_hidden");

            if (isHidden) {
                row.classList.remove("guidance_notes_row_hidden");

                const textarea = row.querySelector(".guidance_hours_notes");
                if (!textarea) return;

                try {
                    const response = await fetch(notesUrl, {
                        method: "GET",
                        credentials: "same-origin",
                        headers: {
                            "Accept": "application/json"
                        }
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }

                    const data = await response.json();
                    textarea.value = data.notes;
                } catch (error) {
                    console.error("Error loading notes:", error);
                    alert("Failed to load notes. Please try again.");
                }
            } else {
                row.classList.add("guidance_notes_row_hidden");
            }
        });
    });

    document.querySelectorAll(".guidance_hours_notes").forEach(textarea => {
        textarea.addEventListener("blur", async function () {
            const notesUrl = this.dataset.notesUrl;
            const notes = this.value;

            try {
                const response = await fetch(notesUrl, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "X-CSRFToken": csrfToken
                    },
                    body: new URLSearchParams({ notes })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                await response.json();
            } catch (error) {
                console.error("Error saving notes:", error);
                alert("Failed to save notes. Please try again.");
            }
        });
    });
});