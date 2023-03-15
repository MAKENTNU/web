const $streamNameField = $("#id_stream_name").closest(".field");

// Disable the stream name field if the selected machine type does not support streams
$("select#id_machine_type").change(function () {
    const $selectedMachineType = $(this).find(":selected");
    const hasStream = $selectedMachineType.data("has-stream") !== undefined;
    $streamNameField.toggleClass("disabled", !hasStream);
});
