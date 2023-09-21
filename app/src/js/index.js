import '../scss/main.scss';
import 'bootstrap';

document.addEventListener('DOMContentLoaded', function() {
    var form = document.getElementById('login-form');

    form.addEventListener('submit', function(event) {
        event.preventDefault(); // Evita el comportamiento predeterminado de envío del formulario

        var emailInput = document.getElementById('email').value;
        var passwordInput = document.getElementById('password').value;

        if (emailInput === 'admin@mail.com') {
            // Redirige al usuario admin a la página "menu-admin.html"
            window.location.href = 'menu-admin.html';
        } else if (emailInput === 'vendedor@mail.com') {
            // Redirige al usuario vendedor a la página "sale-menu.html"
            window.location.href = 'menu-sale.html';
        } else {
            // Muestra un alerta con un mensaje de error para otros usuarios
            alert('Usuario no válido');
        }
    });
});

/* calcular interes */

document.addEventListener('DOMContentLoaded', function() {
    var plazoInput = document.getElementById('dues');
    var interesInput = document.getElementById('interest');
    var cuotaAproxInput = document.getElementById('amountPerPay');

    plazoInput.addEventListener('input', function() {
        calcularCuotaAproximada();
    });

    interesInput.addEventListener('input', function() {
        calcularCuotaAproximada();
    });

    function calcularCuotaAproximada() {
        var plazo = parseInt(plazoInput.value);
        var interes = parseFloat(interesInput.value);
        var prestamo = parseFloat(document.getElementById('amount').value);

        if (isNaN(plazo) || isNaN(interes) || isNaN(prestamo) || interes === 0) {
            cuotaAproxInput.value = '';
            return;
        }

        
        var cuota = prestamo / plazo;
        console.log(cuota);
        console.log(sessionStorage)
        var cuotaInteres = cuota + (cuota * interes / 100);
        console.log(cuotaInteres);
        cuotaAproxInput.value = cuotaInteres.toFixed(2);
    }

    // Llama a la función para calcular la cuota inicialmente
    calcularCuotaAproximada();
});

async function obtenerValoresMaximos() {
    try {
        const response = await fetch("/maximum-values-loan");
        const data = await response.json();
        // Obtener elementos del formulario
        const montoInput = document.getElementById("amount");
        const cuotasSelect = document.getElementById("dues");
        const interesSelect = document.getElementById("interest");
        
        // Configurar el máximo de monto permitido
        montoInput.setAttribute("max", data.maximum_sale);

        montoInput.addEventListener("input", function() {
            const monto = parseFloat(montoInput.value);
            
            if (monto > data.maximum_sale) {
                return('El monto máximo permitido es de $' + data.maximum_sale);
            }
        });
        
        // Configurar el máximo de cuotas permitidas
        for (let i = 1; i <= data.maximum_installments; i++) {
            const option = document.createElement("option");
            option.text = i;
            cuotasSelect.add(option);
        }
        
        // Configurar el mínimo de interés permitido
        for (let i = data.minimum_interest; i <= 50; i++) {
            const option = document.createElement("option");
            option.text = i;
            interesSelect.add(option);
        }
    } catch (error) {
        console.error("Error al obtener los valores máximos del préstamo:", error);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Obtén el ID del coordinador desde algún lugar (puede ser dinámico)
    const userIdElement = document.getElementById('user-id');
    console.log(userIdElement)
    if (userIdElement) {
        const userId = userIdElement.getAttribute('data-user-id');
        // Ahora, userId contiene el ID del usuario
        console.log('ID del usuario:', userId);

        // Crea una instancia de XMLHttpRequest para realizar la solicitud AJAX
    const xhr = new XMLHttpRequest();

    // Configura la solicitud
    xhr.open('GET', `/get_maximum_values_create_salesman/${userId}`, true);

    // Configura el controlador de eventos para la carga exitosa
    xhr.onload = function() {
        if (xhr.status === 200) {
            const data = JSON.parse(xhr.responseText);

            // Establece los valores máximos en los campos de entrada correspondientes
            document.getElementById('maximum_cash').setAttribute('max', data.maximum_cash_coordinator);
            document.getElementById('maximum_sale').setAttribute('max', data.maximum_sale_coordinator);
            document.getElementById('maximum_expense').setAttribute('max', data.maximum_expense_coordinator);
            document.getElementById('maximum_installments').setAttribute('max', data.maximum_installments_coordinator);
            document.getElementById('minimum_interest').setAttribute('min', data.minimum_interest_coordinator);
            document.getElementById('fix_value').setAttribute('min', data.fix_value_coordinator);


            // Puedes agregar más campos aquí según sea necesario

            // Maneja cambios en los campos de entrada si es necesario
            document.getElementById('maximum_cash').addEventListener('input', function() {
                if (parseFloat(this.value) > parseFloat(data.maximum_cash_salesman)) {
                    alert('El monto máximo permitido es de $' + data.maximum_cash_salesman);
                    this.value = data.maximum_cash_salesman;
                }
            });

            // Puedes hacer lo mismo para otros campos si es necesario

        } else {
            console.error('Error al obtener los valores máximos del coordinador');
        }
    };

    // Maneja errores de la solicitud AJAX
    xhr.onerror = function() {
        console.error('Error de red al realizar la solicitud');
    };

    // Envía la solicitud AJAX
    xhr.send();
    }
});

// Ejecutar la función para obtener los valores máximos al cargar la página
window.addEventListener("load", obtenerValoresMaximos);
