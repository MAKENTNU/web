$(document).ready(function () {
    const has_stream_dict = JSON.parse(document.getElementById('has-stream-dict').textContent);
    $("select[name=machine_type]").change(function () { 
        var input = document.getElementById("id_stream_name");
        input.disabled = !(has_stream_dict[this.value]);
    });
    document.getElementById("id_stream_name").disabled = !(has_stream_dict[document.getElementById("id_machine_type").value])
});
