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
    var plazoInput = document.getElementById('deadline');
    var interesInput = document.getElementById('interest');
    var cuotaAproxInput = document.getElementById('aprox-pay');

    plazoInput.addEventListener('input', function() {
        calcularCuotaAproximada();
    });

    interesInput.addEventListener('input', function() {
        calcularCuotaAproximada();
    });

    function calcularCuotaAproximada() {
        var plazo = parseInt(plazoInput.value);
        var interes = parseFloat(interesInput.value);
        var prestamo = parseFloat(document.getElementById('loan').value);

        if (isNaN(plazo) || isNaN(interes) || isNaN(prestamo)) {
            cuotaAproxInput.value = '';
            return;
        }

        var cuota = (prestamo * interes) / (1 - Math.pow(1 + interes, -plazo));
        cuotaAproxInput.value = cuota.toFixed(2);
    }
});