document.addEventListener("DOMContentLoaded", function() {
    var rows = document.querySelectorAll("#proveedoresTableBody tr");
    rows.forEach(function(row) {
        row.addEventListener("click", function() {
            var id = row.getAttribute("data-id");
            var nombre = row.getAttribute("data-nombre");
            var correo = row.getAttribute("data-correo");
            var telefono = row.getAttribute("data-telefono");

            document.getElementById("idProveedor").value = id;
            document.getElementById("nombreProveedor").value = nombre;
            document.getElementById("correo").value = correo;
            document.getElementById("telefono").value = telefono;
        });
    });
});

function editarProveedor() {
    var form = document.getElementById("formProveedores");
    form.action = proveedoresEditarUrl;
    form.submit();
}

function confirmDeletion(url, itemName) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "¿Deseas eliminar " + itemName + "?",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = url;
        }
    });
}
