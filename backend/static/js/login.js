async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const messageDiv = document.getElementById("message");

    if (!email || !password) {
        messageDiv.innerHTML = '<p class="error">Имейл и парола са задължителни!</p>';
        return;
    }

    try {
        const response = await fetch("/api/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            messageDiv.innerHTML = `<p class="error">Грешка: ${data.error}</p>`;
            return;
        }

        // Запази токена и информацията за потребителя
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user_id", data.user_id);
        localStorage.setItem("role", data.role);

        messageDiv.innerHTML = '<p class="success">Успешно влизане! Пренасочване...</p>';
        
        // Пренасочи въз основа на роля
        setTimeout(() => {
            if (data.role === "EMPLOYEE") {
                window.location.href = "/dashboard.html";
            } else {
                window.location.href = "/shipments.html";
            }
        }, 1500);
    } catch (error) {
        messageDiv.innerHTML = `<p class="error">Грешка: ${error.message}</p>`;
    }
}

// Позволи Enter да активира влизането
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("password").addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            login();
        }
    });
});
