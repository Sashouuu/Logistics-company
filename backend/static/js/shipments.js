let allShipments = [];
let currentFilter = 'ALL';
let currentClientId = null;
let currentUserId = null;
let allClients = [];

async function init() {
    const token = localStorage.getItem("access_token");
    currentUserId = parseInt(localStorage.getItem("user_id"));
    const messageDiv = document.getElementById("message");

    if (!token) {
        messageDiv.innerHTML = '<p class="error">Не е намерен токен. Моля, влезте отново.</p>';
        setTimeout(() => {
            window.location.href = "/login.html";
        }, 2000);
        return;
    }

    // Зареди клиентски профил за получаване на client ID
    await loadClientProfile();
    
    // Зареди пратки
    await loadShipments();
    
    // Зареди клиентите за формата за изпращане
    await loadClientsForForm();
    
    // Attach form handler
    document.getElementById("sendShipmentForm").addEventListener("submit", handleSendShipment);
}

async function loadClientProfile() {
    const token = localStorage.getItem("access_token");
    
    try {
        const response = await fetch("/api/client/me", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error("Failed to load client profile");
        }

        const client = await response.json();
        currentClientId = client.id;
        console.log("Current client ID:", currentClientId);
    } catch (error) {
        console.error("Error loading client profile:", error);
    }
}

async function loadShipments() {
    const token = localStorage.getItem("access_token");
    const messageDiv = document.getElementById("message");

    try {
        const response = await fetch("/api/shipment", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                messageDiv.innerHTML = '<p class="error">Сесията е изтекла. Моля, влезте отново.</p>';
                setTimeout(() => {
                    window.location.href = "/login.html";
                }, 2000);
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        allShipments = await response.json();
        displayShipments();
    } catch (error) {
        messageDiv.innerHTML = `<p class="error">Грешка при зареждане на пратки: ${error.message}</p>`;
    }
}

async function loadClientsForForm() {
    const token = localStorage.getItem("access_token");
    
    try {
        const response = await fetch("/api/client", {
            method: "GET",
            headers: { 
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        console.log("Client list response status:", response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error("Error response:", errorText);
            let errorMsg = errorText;
            try {
                const errorData = JSON.parse(errorText);
                errorMsg = errorData.error || errorData.message || errorText;
            } catch (e) {
                // Если не JSON, используем текст
            }
            throw new Error(`Failed to load clients: ${response.status} - ${errorMsg}`);
        }

        allClients = await response.json();
        console.log("Loaded clients:", allClients);
        
        // Попълни селекта за получатели
        const receiverSelect = document.getElementById("receiver_id");
        receiverSelect.innerHTML = '<option value="">Избери получател</option>';
        
        if (allClients.length === 0) {
            const option = document.createElement('option');
            option.disabled = true;
            option.textContent = 'Няма налични получатели';
            receiverSelect.appendChild(option);
            return;
        }
        
        allClients.forEach(client => {
            const option = document.createElement('option');
            option.value = client.id;
            const name = `${client.first_name || 'N/A'} ${client.last_name || 'N/A'}`;
            const company = client.company_name || 'N/A';
            option.textContent = `${name} (${company})`;
            receiverSelect.appendChild(option);
        });
    } catch (error) {
        console.error("Error loading clients:", error);
        const receiverSelect = document.getElementById("receiver_id");
        receiverSelect.innerHTML = `<option disabled>Грешка: ${error.message}</option>`;
    }
}

function displayShipments() {
    const container = document.getElementById("shipmentsContainer");
    
    let shipmentsToDisplay = allShipments;
    if (currentFilter !== 'ALL') {
        shipmentsToDisplay = allShipments.filter(s => s.status === currentFilter);
    }

    if (shipmentsToDisplay.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666;">Няма пратки за показване</p>';
        return;
    }

    container.innerHTML = shipmentsToDisplay.map(shipment => `
        <div class="shipment-card ${getCardClass(shipment.status)}">
            <div class="shipment-header">
                <div class="shipment-number">Пратка #${shipment.id}</div>
                <div class="shipment-status status-${shipment.status.toLowerCase()}">
                    ${getStatusText(shipment.status)}
                </div>
            </div>
            <div class="shipment-details">
                <div class="detail-row">
                    <span class="detail-label">Номер:</span>
                    <span class="detail-value">${shipment.tracking_number}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Тегло:</span>
                    <span class="detail-value">${shipment.weight} кг</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Размери:</span>
                    <span class="detail-value">${shipment.dimensions}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">От:</span>
                    <span class="detail-value">${shipment.origin_address}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">До:</span>
                    <span class="detail-value">${shipment.destination_address}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Дата:</span>
                    <span class="detail-value">${new Date(shipment.sent_date).toLocaleDateString('bg-BG')}</span>
                </div>
                ${shipment.received_date ? `
                <div class="detail-row">
                    <span class="detail-label">Получена:</span>
                    <span class="detail-value">${new Date(shipment.received_date).toLocaleDateString('bg-BG')}</span>
                </div>
                ` : ''}
                <div class="detail-row">
                    <span class="detail-label">Цена:</span>
                    <span class="detail-value">${shipment.price} BGN</span>
                </div>
            </div>
        </div>
    `).join('');
}

function getCardClass(status) {
    switch(status) {
        case 'PENDING': return 'pending';
        case 'IN_TRANSIT': return 'in-transit';
        case 'DELIVERED': return 'delivered';
        default: return '';
    }
}

function getStatusText(status) {
    const statusMap = {
        'PENDING': 'В очакване',
        'IN_TRANSIT': 'В пътя',
        'DELIVERED': 'Доставена',
        'CANCELLED': 'Отменена'
    };
    return statusMap[status] || status;
}

function filterShipments(status) {
    currentFilter = status;
    
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`filter-${status.toLowerCase()}`).classList.add('active');
    
    displayShipments();
}

async function handleSendShipment(e) {
    e.preventDefault();
    
    const token = localStorage.getItem("access_token");
    const formMessage = document.getElementById("sendFormMessage");
    
    // Генерирай номер за проследяване
    const trackingNumber = `CLN-${Date.now()}`;
    
    const body = {
        sender_id: currentClientId,
        receiver_id: parseInt(document.getElementById("receiver_id").value),
        registered_by_employee_id: 1, // Служител който регистрира (по подразумевание first employee)
        tracking_number: trackingNumber,
        weight: parseFloat(document.getElementById("send_weight").value),
        dimensions: document.getElementById("send_dimensions").value,
        description: document.getElementById("send_description").value,
        price: parseFloat(document.getElementById("send_price").value),
        sent_date: new Date().toISOString(),
        status: "PENDING",
        origin_address: document.getElementById("send_origin_address").value,
        destination_address: document.getElementById("send_destination_address").value
    };

    try {
        const response = await fetch("/api/shipment", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (!response.ok) {
            formMessage.innerHTML = `<p class="error">Грешка: ${data.error}</p>`;
            return;
        }

        formMessage.innerHTML = '<p class="success">Пратка регистрирана успешно! Номер: ' + trackingNumber + '</p>';
        document.getElementById("sendShipmentForm").reset();
        
        await loadShipments();
        
        setTimeout(() => {
            formMessage.innerHTML = '';
            showTab('my-shipments');
        }, 2000);
    } catch (error) {
        formMessage.innerHTML = `<p class="error">Грешка: ${error.message}</p>`;
    }
}

function showTab(tabId) {
    // Скрий всички tab-ове
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Скрий всички tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Покажи избрания tab
    document.getElementById(tabId).classList.add('active');
    event.target.classList.add('active');
}

function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("role");
    window.location.href = "/login.html";
}

// Зареди при отваряне на страницата
window.onload = function() {
    init();
};
