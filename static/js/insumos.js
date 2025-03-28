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
    var unidadSelect = document.getElementById("unidadMedida");

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

            // Bloquear el botón de guardar al editar
            btnGuardar.disabled = true;

            // Aplicar restricciones a la unidad de medida
            restringirUnidades(unidad);
        });
    });

    unidadSelect.addEventListener("change", function() {
        var unidadActual = document.getElementById("unidadMedida").value;
        restringirUnidades(unidadActual);
    });
});

function editarInsumo() {
    var form = document.getElementById("formInsumos");
    form.action = insumosEditarUrl;
    form.submit();
}

function restringirUnidades(unidadSeleccionada) {
    var unidadSelect = document.getElementById("unidadMedida");
    var opciones = unidadSelect.options;

    for (var i = 0; i < opciones.length; i++) {
        opciones[i].disabled = false; // Habilitar todas las opciones antes de restringir
    }

    if (["Litros", "Mililitros"].includes(unidadSeleccionada)) {
        deshabilitarOpciones(["Kilogramos", "Gramos", "Piezas"]);
    } else if (["Kilogramos", "Gramos"].includes(unidadSeleccionada)) {
        deshabilitarOpciones(["Litros", "Mililitros", "Piezas"]);
    } else if (unidadSeleccionada === "Piezas") {
        deshabilitarOpciones(["Litros", "Mililitros", "Kilogramos", "Gramos"]);
    }
}

function deshabilitarOpciones(opciones) {
    var unidadSelect = document.getElementById("unidadMedida");

    for (var i = 0; i < unidadSelect.options.length; i++) {
        if (opciones.includes(unidadSelect.options[i].value)) {
            unidadSelect.options[i].disabled = true;
        }
    }
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
