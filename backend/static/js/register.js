function toggleFields() {
    const role = document.getElementById("role").value;
    document.getElementById("clientFields").style.display = role === "CLIENT" ? "block" : "none";
    document.getElementById("employeeFields").style.display = role === "EMPLOYEE" ? "block" : "none";
}

async function register() {
    const role = document.getElementById("role").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const messageDiv = document.getElementById("message");

    if (!email || !password) {
        messageDiv.innerHTML = '<p class="error">Имейл и парола са задължителни!</p>';
        return;
    }

    let body = {
        email,
        password,
        role
    };

    if (role === "CLIENT") {
        body = {
            ...body,
            company_name: document.getElementById("company_name").value,
            first_name: document.getElementById("first_name").value,
            last_name: document.getElementById("last_name").value,
            phone: document.getElementById("phone").value,
            address: document.getElementById("address").value,
            city: document.getElementById("city").value,
            country: document.getElementById("country").value,
        };

        if (!body.company_name || !body.first_name || !body.last_name || !body.phone) {
            messageDiv.innerHTML = '<p class="error">Попълни всички полета!</p>';
            return;
        }
    } else if (role === "EMPLOYEE") {
        body = {
            ...body,
            company_id: parseInt(document.getElementById("company_id").value),
            office_id: parseInt(document.getElementById("office_id").value),
            first_name: document.getElementById("emp_first_name").value,
            last_name: document.getElementById("emp_last_name").value,
            phone: document.getElementById("emp_phone").value,
        };

        if (!body.company_id || !body.office_id || !body.first_name || !body.last_name || !body.phone) {
            messageDiv.innerHTML = '<p class="error">Попълни всички полета!</p>';
            return;
        }
    }

    try {
        const response = await fetch("/api/auth/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (!response.ok) {
            messageDiv.innerHTML = `<p class="error">Грешка: ${data.error}</p>`;
            return;
        }

        messageDiv.innerHTML = '<p class="success">Регистрацията е успешна! Пренасочване...</p>';
        setTimeout(() => {
            window.location.href = "/login.html";
        }, 2000);
    } catch (error) {
        messageDiv.innerHTML = `<p class="error">Грешка: ${error.message}</p>`;
    }
}

// When the page loads, set up the initial field visibility
window.onload = function() {
    toggleFields();
};
