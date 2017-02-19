

$(".table-responsive").on("click", ".btn-danger", function(){
    $('#rmpost').val(this.id);
    console.log(this.id);
});

$("#rrmove").click(function(event){
    event.preventDefault();
    $.post("/admin/remove", {id: $("#rmpost").val()}).then(function(){
        location.reload();
    });
});
