document.addEventListener("DOMContentLoaded", function () {
    // Obtener los IDs de productos con bajo stock desde la variable global
    const productosBajoStock = window.productosBajoStock || [];

    // Seleccionar todas las filas de la tabla
    const filas = document.querySelectorAll("#productosTableBody tr");

    // Recorrer las filas y resaltar las que tengan bajo stock
    filas.forEach(fila => {
        const idProducto = fila.getAttribute("data-id"); // Obtener el ID del producto
        
        if (productosBajoStock.includes(parseInt(idProducto))) {
            fila.classList.add("table-danger"); // Agregar la clase de Bootstrap para resaltar
        }
    });
});


document.addEventListener("DOMContentLoaded", function () {
    const idProductoInput = document.getElementById("idProducto");

    // Asignar el ID del producto seleccionado al campo oculto
    document.querySelectorAll(".btn-select").forEach(button => {
        button.addEventListener("click", function () {
            const row = this.closest("tr");
            const idProducto = row.getAttribute("data-id");
            idProductoInput.value = idProducto; // Asignar el ID al campo oculto
        });
    });

    // Validar antes de enviar el formulario
    const formMerma = document.getElementById("formMerma");
    formMerma.addEventListener("submit", function (event) {
        if (!idProductoInput.value) {
            alert("Debe seleccionar un producto antes de mermar.");
            event.preventDefault();
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const table = document.getElementById('tablaProductos');
    const txtIdGalleta = document.getElementById('txtIdGalleta');
    const txtEstatus = document.getElementById('txtEstatus');

    // Agregar evento a los botones de selección
    table.addEventListener('click', (event) => {
        const button = event.target.closest('.btn-select');
        if (button) {
            const row = button.closest('tr');
            const id = row.getAttribute('data-id');
            const estatus = row.getAttribute('data-estatus');

            // Cargar los valores en los inputs
            txtIdGalleta.value = id;
            txtEstatus.value = estatus; // Carga directamente el valor (1 o 0)
        }
    });
});

//!  Funcion guardarLote
function guardarLote() {
    var sabor = $('#txtSabor').val();
    var csrfToken = $('input[name="csrf_token"]').val(); // Obtener el token CSRF del campo oculto

    if (sabor) {
        $.ajax({
            url: '/guardarLote',
            type: 'POST',
            data: { sabor: sabor, csrf_token: csrfToken },
            success: function () {
                // Redirigir a la página de galletas para que se muestren los mensajes flash
                window.location.href = '/galletas';
            },
            error: function (xhr, status, error) {
                console.error('Error al guardar el lote:', error);
                alert('Ocurrió un error al guardar el lote. Inténtalo de nuevo.');
            }
        });
    } else {
        alert('Por favor selecciona un sabor antes de guardar.');
    }
}

//! esta funciona toma el id del producto que seleccionemos de la tabla
function selectProduct(id, estatus) {
    document.getElementById('txtIdGalleta').value = id;
    document.getElementById('txtEstatus').value = estatus;
    document.getElementById('mdlIdProducto').value = id;
}

document.getElementById('flexCheckIndeterminate').addEventListener('change', function() {
    document.getElementById('mdlCantidad').disabled = this.checked;
});

function selectProductForPaquete(idProducto) {
    document.getElementById("txtIdGalletaGranel").value = idProducto;
    console.log("Producto seleccionado para paquete: " + idProducto);
}

document.addEventListener("DOMContentLoaded", function () {
    const alerts = document.querySelectorAll("#flash-container .alert");
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove("show");
            alert.classList.add("fade");
            setTimeout(() => alert.remove(), 150); // Eliminar del DOM después de la animación
        }, 5000); // 5 segundos
    });
});