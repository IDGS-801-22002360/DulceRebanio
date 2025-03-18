document.addEventListener("DOMContentLoaded", function() {
    var tableRows = document.querySelectorAll("#productosTableBody tr");
    tableRows.forEach(function(row) {
        row.addEventListener("click", function() {
            var id = row.getAttribute("data-id");
            var materia = row.getAttribute("data-materia");
            var unidad = row.getAttribute("data-unidad");
            var fecha = row.getAttribute("data-fecha");
            
            document.getElementById("idMateriaPrima").value = id;
            document.getElementById("materiaPrima").value = materia;
            document.getElementById("unidadMedida").value = unidad;
            document.getElementById("fechaCaducidad").value = fecha;
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
