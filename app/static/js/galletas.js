document.addEventListener("DOMContentLoaded", function () {
    // Obtener los IDs de productos con bajo stock desde la variable global
    const productosBajoStock = window.productosBajoStock || [];

    // Seleccionar todas las filas de la tabla
    const filas = document.querySelectorAll("#productosTableBody tr");

    // Recorrer las filas y resaltar las que tengan bajo stock
    filas.forEach(fila => {
        const idProducto = fila.querySelector("td:first-child").textContent.trim(); // Obtener el ID del producto (primer <td>)
        
        if (productosBajoStock.includes(parseInt(idProducto))) {
            fila.classList.add("low-stock"); // Agregar la clase CSS para resaltar
        }
    });
});

//!  Funcion guardarLote
function guardarLote() {
    var sabor = $('#txtSabor').val();
    var csrfToken = $('input[name="csrf_token"]').val(); // Obtener el token CSRF del campo oculto

    if (sabor) {
        $.ajax({
            url: '/admin/produccion/guardarLote', // Ruta corregida con el prefijo correcto
            type: 'POST',
            data: { sabor: sabor, csrf_token: csrfToken },
            success: function () {
                // Redirigir a la página de galletas para que se muestren los mensajes flash
                window.location.href = '/admin/produccion/galletas'; // Ruta corregida con el prefijo correcto
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