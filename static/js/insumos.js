document.addEventListener("DOMContentLoaded", function() {
    function sanitizarTexto(texto) {
        return texto.replace(/[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]/g, "").trim();
    }

    document.getElementById("materiaPrima").addEventListener("input", function() {
        this.value = sanitizarTexto(this.value);
    });
});

document.addEventListener("DOMContentLoaded", function() {
    var tableRows = document.querySelectorAll("#productosTableBody tr");
    var btnGuardar = document.querySelector("button[type='submit']");

    tableRows.forEach(function(row) {
        row.addEventListener("click", function() {
            // Recuperar el ID del insumo desde el atributo data-id
            var idMateriaPrima = row.getAttribute("data-id");
            var materia = row.getAttribute("data-materia");
            var unidad = row.getAttribute("data-unidad");
            var proveedor = row.getAttribute("data-proveedor");
            var precio = row.getAttribute("data-precio");
            
            // Asignar el valor al campo oculto
            document.getElementById("idMateriaPrima").value = idMateriaPrima;
            document.getElementById("materiaPrima").value = materia;
            document.getElementById("unidadMedida").value = unidad;
            document.getElementById("idProveedor").value = proveedor;
            document.getElementById("precioUnitario").value = precio;
            
            // Deshabilitar el botón de guardar para indicar que se va a editar
            btnGuardar.disabled = true;
        });
    });
});


function editarInsumo() {
    var form = document.getElementById("formInsumos");
    form.action = insumosEditarUrl;
    form.submit();
}

function mermarInsumo(id) {
    Swal.fire({
        title: 'Merma de Insumo',
        text: 'Ingresa la cantidad a mermar:',
        icon: 'warning',
        input: 'number',
        inputAttributes: {
            min: 0,
            step: '0.01'
        },
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Aplicar Merma',
        cancelButtonText: 'Cancelar',
        preConfirm: (value) => {
            if (!value || isNaN(value) || parseFloat(value) <= 0) {
                Swal.showValidationMessage('Ingresa una cantidad válida');
            }
            return parseFloat(value);
        }
    }).then((result) => {
        if (result.isConfirmed) {
            var cantidad = result.value;
            // Construir la URL manualmente siguiendo el patrón definido en la ruta
            var url = "/mermar_insumo/" + id + "/" + cantidad;
            window.location.href = url;
        }
    });
}