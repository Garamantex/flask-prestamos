import '../scss/main.scss';
import 'bootstrap';
import $ from 'jquery';

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

        if (isNaN(plazo) || isNaN(interes) || isNaN(prestamo) || interes === 0 || plazo <= 0) {
            cuotaAproxInput.value = '';
            return;
        }

        var cuota = prestamo / plazo;
        var cuotaInteres = cuota + (cuota * interes / 100);
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
                // Mostrar un mensaje de error
                alert('El monto máximo permitido es de $' + data.maximum_sale);
                montoInput.value =  data.maximum_sale; // Establecer el valor máximo
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

obtenerValoresMaximos();

/* $(document).ready(function () {
    // Obtener el valor máximo del coordinador cuando la página se carga
    $.ajax({
        url: '/get_maximum_values_create_salesman',
        method: 'GET',
        success: function (data) {
            // Actualizar los campos de entrada correspondientes con los valores máximos
            $('#maximum_cash').val(data.maximum_cash_salesman);
            $('#maximum_sale').val(data.maximum_sale_coordinator);
            $('#maximum_expense').val(data.maximum_expense_coordinator);
            $('#maximum_installments').val(data.maximum_installments_coordinator);
            $('#minimum_interest').val(data.minimum_interest_coordinator);
        },
        error: function () {
            console.error('Error al obtener los valores máximos del coordinador');
        }
    });
}); */

function formatNumericFields() {
    const numericFields = document.querySelectorAll('.js-number');
    
    numericFields.forEach(function(field) {
        const rawValue = field.value.replace(/,/g, ''); // Eliminar comas si las hubiera
        const parsedValue = parseFloat(rawValue);
        
        if (!isNaN(parsedValue)) {
            field.value = parsedValue.toLocaleString('es-ES', { minimumFractionDigits: 2 });
        }
    });
}

formatNumericFields();

document.addEventListener('DOMContentLoaded', function() {
    // Verifica si la URL actual es la página de inicio
    if (window.location.href.endsWith('/')) {
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
    }
});
