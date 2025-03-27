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
            btnGuardar.disabled = true;
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


document.addEventListener("DOMContentLoaded", function() {
    // Sanitizar nombre: solo permite letras, tildes, ñ y espacios
    function sanitizarNombre(texto) {
        return texto.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, "").trim();
    }

    // Sanitizar correo: permite letras, números, @, ., - y _
    function sanitizarCorreo(texto) {
        return texto.replace(/[^a-zA-Z0-9@._-]/g, "").trim();
    }

    // Sanitizar teléfono: solo permite números
    function sanitizarTelefono(texto) {
        return texto.replace(/[^0-9]/g, "").trim();
    }

    // Obtener los campos de entrada
    let nombreProveedor = document.getElementById("nombreProveedor");
    let correo = document.getElementById("correo");
    let telefono = document.getElementById("telefono");

    // Sanitizar en tiempo real cuando el usuario ingresa datos
    nombreProveedor.addEventListener("input", function() {
        this.value = sanitizarNombre(this.value);
    });

    correo.addEventListener("input", function() {
        this.value = sanitizarCorreo(this.value);
    });

    telefono.addEventListener("input", function() {
        this.value = sanitizarTelefono(this.value);
    });

});
