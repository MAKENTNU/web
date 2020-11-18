$(document).ready(function () {
    $("select[name=machine_type]").change(function () { 
        var input = document.getElementById("id_stream_name");
        input.disabled = this.value != 1;
    });
    document.getElementById("id_stream_name").disabled = document.getElementById("id_machine_type").value != 1
});
