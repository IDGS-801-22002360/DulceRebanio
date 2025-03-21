//! esta madre va a deshabilitar el input si el check esta habilitado
/*document.addEventListener("DOMContentLoaded", function () {
    const checkbox = document.getElementById("flexCheckIndeterminate");
    const input = document.getElementById("mdlCantidad");

    checkbox.addEventListener("change", function () {
        input.disabled = checkbox.checked;
    });
});
*/

/*
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
*/

//!  Funcion guardarLote
function guardarLote() {
    var sabor = $('#txtSabor').val();
    var csrfToken = $('input[name="csrf_token"]').val(); // Obtener el token CSRF del campo oculto

    if (sabor) {
        $.ajax({
            url: '/guardarLote',
            type: 'POST',
            data: { sabor: sabor, csrf_token: csrfToken }, // Incluir el token CSRF en los datos
            success: function (response) {
                if (response.success) {
                    alert(response.message);
                } else {
                    alert(response.message);
                }
            },
            error: function () {
                alert('Error al guardar el lote.');
            }
        });
    } else {
        alert('Por favor, seleccione un sabor.');
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