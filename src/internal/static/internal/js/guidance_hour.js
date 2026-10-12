document.addEventListener("DOMContentLoaded", function () {
    const fallbackNotesSaveErrorMessage = document
        .querySelector(".ui.container")
        ?.dataset.notesSaveErrorMessage || "Failed to save comments. Please try again.";

    function openSlotModal(slotElement) {
        const target = slotElement.dataset.slotModal;
        if (!target) {
            return;
        }

        $(target).modal({
            onHidden: function () {
                this.find(".guidance_hour_notes").each((_, el) => { el.value = el.defaultValue; });
            }
        }).modal("show");
    }

    function buildMobileDayTables() {
        const table = document.querySelector(".guidance_hour_matrix");
        const cardsContainer = document.querySelector(".guidance_hour_mobile_cards");
        if (!table || !cardsContainer) {
            return;
        }

        cardsContainer.innerHTML = "";

        const dayHeaders = Array.from(table.querySelectorAll("thead th"))
            .slice(1)
            .map((header) => header.textContent.trim());
        const rows = Array.from(table.querySelectorAll("tbody tr"));

        dayHeaders.forEach((dayLabel, dayIndex) => {
            const dayTable = document.createElement("table");
            dayTable.className = "guidance_hour_matrix guidance_hour_mobile_day_table";

            const tableHead = document.createElement("thead");
            const headerRow = document.createElement("tr");

            const timeHeader = document.createElement("th");
            timeHeader.className = "guidance_slot_time";
            timeHeader.textContent = table.querySelector("thead .guidance_slot_time")?.textContent.trim() || "Time";
            headerRow.appendChild(timeHeader);

            const dayHeader = document.createElement("th");
            dayHeader.textContent = dayLabel;
            headerRow.appendChild(dayHeader);

            tableHead.appendChild(headerRow);
            dayTable.appendChild(tableHead);

            const tableBody = document.createElement("tbody");

            rows.forEach((row) => {
                const timeLabel = row.querySelector(".guidance_slot_time")?.textContent.trim() || "";
                const slotCell = row.querySelectorAll("td")[dayIndex];
                if (!slotCell) {
                    return;
                }

                const tableRow = document.createElement("tr");
                tableRow.className = "guidance_slot_row";

                const slotTime = document.createElement("th");
                slotTime.className = "guidance_slot_time";
                slotTime.textContent = timeLabel;
                tableRow.appendChild(slotTime);

                const slotContent = slotCell.cloneNode(true);
                tableRow.appendChild(slotContent);

                tableBody.appendChild(tableRow);
            });

            dayTable.appendChild(tableBody);
            cardsContainer.appendChild(dayTable);
        });
    }

    buildMobileDayTables();

    document.addEventListener("click", function (event) {
        const slotCell = event.target.closest(".guidance_matrix_slot[data-slot-modal]");
        if (slotCell) {
            openSlotModal(slotCell);
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key !== "Enter" && event.key !== " ") {
            return;
        }

        const slotCell = event.target.closest(".guidance_matrix_slot[data-slot-modal]");
        if (!slotCell) {
            return;
        }

        event.preventDefault();
        openSlotModal(slotCell);
    });

    document.querySelectorAll(".guidance_hour_notes_save").forEach(saveButton => {
        const textarea = saveButton.closest(".content").querySelector(".guidance_hour_notes");
        const saveLabel = saveButton.dataset.saveLabel;
        const savedLabel = saveButton.dataset.savedLabel;

        saveButton.addEventListener("click", async function () {
            const notesUrl = textarea.dataset.notesUrl;
            const notes = textarea.value;

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
                    let errorMessage = fallbackNotesSaveErrorMessage;

                    try {
                        const errorData = await response.json();
                        if (typeof errorData?.message === "string" && errorData.message.length > 0) {
                            errorMessage = errorData.message;
                        }
                    } catch {
                        // Keep fallback message when response body is not JSON.
                    }

                    throw new Error(errorMessage);
                }

                await response.json();
                textarea.defaultValue = notes;

                saveButton.textContent = savedLabel;
                saveButton.classList.add("guidance_hour_notes_save_success");
                saveButton.disabled = true;
                setTimeout(() => {
                    saveButton.textContent = saveLabel;
                    saveButton.classList.remove("guidance_hour_notes_save_success");
                    saveButton.disabled = false;
                }, 1500);
            } catch (error) {
                console.error("Error saving notes:", error);
                alert(error.message || fallbackNotesSaveErrorMessage);
            }
        });
    });
});
