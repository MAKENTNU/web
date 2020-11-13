$(document).ready(function () {
    document.getElementById("id_stream_name").disabled = true;
    $("select[name=machine_type]").change(function () { 
        var input = document.getElementById("id_stream_name");
        input.disabled = this.value != 1;
    });
});