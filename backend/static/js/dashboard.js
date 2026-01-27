let allEmployeeShipments = [];
let currentEmployeeFilter = 'ALL';
let allClients = [];
let currentEmployeeId = null;

async function initDashboard() {
    const token = localStorage.getItem("access_token");
    const userRole = localStorage.getItem("role");

    if (!token || userRole !== "EMPLOYEE") {
        window.location.href = "/login.html";
        return;
    }

    // Покажи информация на потребителя
    document.getElementById("userInfo").innerHTML = `<span>👤 Служител</span>`;

    // Зареди клиентите за формата
    await loadClients();
    
    // Зареди начални данни
    await loadStats();
    await loadEmployeeShipments();

    // Attach form handler
    document.getElementById("shipmentForm").addEventListener("submit", handleShipmentSubmit);
}

async function loadClients() {
    const token = localStorage.getItem("access_token");
    
    try {
        const response = await fetch("/api/client", {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!response.ok) throw new Error("Failed to load clients");

        allClients = await response.json();
        
        // Попълни селектите
        const senderSelect = document.getElementById("sender_id");
        const receiverSelect = document.getElementById("receiver_id");
        
        senderSelect.innerHTML = '<option value="">Избери клиент (изпращач)</option>';
        receiverSelect.innerHTML = '<option value="">Избери клиент (получател)</option>';
        
        allClients.forEach(client => {
            const option = `<option value="${client.id}">${client.first_name} ${client.last_name} (${client.company_name})</option>`;
            senderSelect.innerHTML += option;
            receiverSelect.innerHTML += option;
        });
    } catch (error) {
        console.error("Error loading clients:", error);
    }
}

async function loadStats() {
    const token = localStorage.getItem("access_token");
    
    try {
        const response = await fetch("/api/shipment", {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!response.ok) throw new Error("Failed to load shipments");

        const shipments = await response.json();
        
        document.getElementById("totalShipments").innerText = shipments.length;
        document.getElementById("pendingShipments").innerText = shipments.filter(s => s.status === "PENDING").length;
        document.getElementById("transitShipments").innerText = shipments.filter(s => s.status === "IN_TRANSIT").length;
        document.getElementById("deliveredShipments").innerText = shipments.filter(s => s.status === "DELIVERED").length;
    } catch (error) {
        console.error("Error loading stats:", error);
    }
}

async function loadEmployeeShipments() {
    const token = localStorage.getItem("access_token");
    
    try {
        const response = await fetch("/api/shipment", {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!response.ok) throw new Error("Failed to load shipments");

        allEmployeeShipments = await response.json();
        displayEmployeeShipments();
    } catch (error) {
        console.error("Error loading shipments:", error);
    }
}

function displayEmployeeShipments() {
    const container = document.getElementById("employeeShipmentsContainer");
    
    let shipmentsToDisplay = allEmployeeShipments;
    if (currentEmployeeFilter !== 'ALL') {
        shipmentsToDisplay = allEmployeeShipments.filter(s => s.status === currentEmployeeFilter);
    }

    if (shipmentsToDisplay.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666;">Няма пратки</p>';
        return;
    }

    container.innerHTML = shipmentsToDisplay.map(shipment => `
        <div class="shipment-card">
            <div class="shipment-header">
                <div class="shipment-number">Пратка #${shipment.id} - ${shipment.tracking_number}</div>
                <div class="shipment-status status-${shipment.status.toLowerCase()}">${getStatusText(shipment.status)}</div>
            </div>
            <div class="shipment-details">
                <div class="detail-row">
                    <span class="detail-label">От:</span>
                    <span class="detail-value">${shipment.origin_address}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">До:</span>
                    <span class="detail-value">${shipment.destination_address}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Тегло:</span>
                    <span class="detail-value">${shipment.weight} кг</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Цена:</span>
                    <span class="detail-value">${shipment.price} BGN</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Изпратена:</span>
                    <span class="detail-value">${new Date(shipment.sent_date).toLocaleDateString('bg-BG')}</span>
                </div>
                ${shipment.received_date ? `
                <div class="detail-row">
                    <span class="detail-label">Получена:</span>
                    <span class="detail-value">${new Date(shipment.received_date).toLocaleDateString('bg-BG')}</span>
                </div>
                ` : ''}
            </div>
            <div style="margin-top: 10px;">
                ${shipment.status !== 'DELIVERED' ? `
                    <button onclick="markAsDelivered(${shipment.id})" style="padding: 5px 10px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">Отбележи като доставена</button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

async function markAsDelivered(shipmentId) {
    const token = localStorage.getItem("access_token");
    
    try {
        const response = await fetch(`/api/shipment/${shipmentId}`, {
            method: "PUT",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                status: "DELIVERED",
                received_date: new Date().toISOString()
            })
        });

        if (!response.ok) throw new Error("Failed to update shipment");

        alert("Пратката е отбелязана като доставена!");
        await loadEmployeeShipments();
        await loadStats();
    } catch (error) {
        alert("Грешка: " + error.message);
    }
}

function filterEmployeeShipments(status) {
    currentEmployeeFilter = status;
    
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`emp-filter-${status.toLowerCase()}`).classList.add('active');
    
    displayEmployeeShipments();
}

async function handleShipmentSubmit(e) {
    e.preventDefault();
    
    const token = localStorage.getItem("access_token");
    const formMessage = document.getElementById("formMessage");
    
    const trackingNumber = document.getElementById("tracking_number").value;
    
    // Проверка дали вече съществува
    const existingShipment = allEmployeeShipments.find(s => s.tracking_number === trackingNumber);
    if (existingShipment) {
        formMessage.innerHTML = '<p class="error">Пратка с този номер вече съществува!</p>';
        return;
    }

    const body = {
        sender_id: parseInt(document.getElementById("sender_id").value),
        receiver_id: parseInt(document.getElementById("receiver_id").value),
        registered_by_employee_id: currentEmployeeId || 1, // TODO: Get actual employee ID
        tracking_number: trackingNumber,
        weight: parseFloat(document.getElementById("weight").value),
        dimensions: document.getElementById("dimensions").value,
        description: document.getElementById("description").value,
        price: parseFloat(document.getElementById("price").value),
        sent_date: new Date().toISOString(),
        status: "PENDING",
        origin_address: document.getElementById("origin_address").value,
        destination_address: document.getElementById("destination_address").value
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

        formMessage.innerHTML = '<p class="success">Пратка регистрирана успешно!</p>';
        document.getElementById("shipmentForm").reset();
        
        await loadEmployeeShipments();
        await loadStats();
        
        setTimeout(() => formMessage.innerHTML = '', 3000);
    } catch (error) {
        formMessage.innerHTML = `<p class="error">Грешка: ${error.message}</p>`;
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

async function showReport(reportType) {
    const token = localStorage.getItem("access_token");
    const container = document.getElementById("reportContainer");
    
    try {
        let url = "";
        let htmlContent = "";

        switch(reportType) {
            case 'employees':
                const employeesResponse = await fetch("/api/employee", {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                const employees = await employeesResponse.json();
                htmlContent = `
                    <div class="report-container">
                        <h3>Служители в компанията</h3>
                        <table class="report-table">
                            <tr>
                                <th>ID</th>
                                <th>Име</th>
                                <th>Фамилия</th>
                                <th>Телефон</th>
                                <th>Активен</th>
                            </tr>
                            ${employees.map(e => `
                                <tr>
                                    <td>${e.id}</td>
                                    <td>${e.first_name}</td>
                                    <td>${e.last_name}</td>
                                    <td>${e.phone}</td>
                                    <td>${e.is_active ? 'Да' : 'Не'}</td>
                                </tr>
                            `).join('')}
                        </table>
                    </div>
                `;
                break;

            case 'clients':
                const clientsResponse = await fetch("/api/client", {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                const clients = await clientsResponse.json();
                htmlContent = `
                    <div class="report-container">
                        <h3>Клиенти на компанията</h3>
                        <table class="report-table">
                            <tr>
                                <th>ID</th>
                                <th>Име</th>
                                <th>Компания</th>
                                <th>Имейл</th>
                                <th>Град</th>
                            </tr>
                            ${clients.map(c => `
                                <tr>
                                    <td>${c.id}</td>
                                    <td>${c.first_name} ${c.last_name}</td>
                                    <td>${c.company_name}</td>
                                    <td>${c.email}</td>
                                    <td>${c.city}</td>
                                </tr>
                            `).join('')}
                        </table>
                    </div>
                `;
                break;

            case 'all-shipments':
                htmlContent = `
                    <div class="report-container">
                        <h3>Всички пратки (${allEmployeeShipments.length})</h3>
                        <table class="report-table">
                            <tr>
                                <th>ID</th>
                                <th>Номер</th>
                                <th>Статус</th>
                                <th>От</th>
                                <th>До</th>
                                <th>Цена</th>
                            </tr>
                            ${allEmployeeShipments.map(s => `
                                <tr>
                                    <td>${s.id}</td>
                                    <td>${s.tracking_number}</td>
                                    <td>${getStatusText(s.status)}</td>
                                    <td>${s.origin_address}</td>
                                    <td>${s.destination_address}</td>
                                    <td>${s.price} BGN</td>
                                </tr>
                            `).join('')}
                        </table>
                    </div>
                `;
                break;

            case 'undelivered':
                const undelivered = allEmployeeShipments.filter(s => s.status !== 'DELIVERED' && s.status !== 'CANCELLED');
                htmlContent = `
                    <div class="report-container">
                        <h3>Неполучени пратки (${undelivered.length})</h3>
                        <table class="report-table">
                            <tr>
                                <th>ID</th>
                                <th>Номер</th>
                                <th>Статус</th>
                                <th>От</th>
                                <th>До</th>
                            </tr>
                            ${undelivered.map(s => `
                                <tr>
                                    <td>${s.id}</td>
                                    <td>${s.tracking_number}</td>
                                    <td>${getStatusText(s.status)}</td>
                                    <td>${s.origin_address}</td>
                                    <td>${s.destination_address}</td>
                                </tr>
                            `).join('')}
                        </table>
                    </div>
                `;
                break;

            case 'revenue':
                const totalRevenue = allEmployeeShipments.reduce((sum, s) => sum + parseFloat(s.price), 0);
                htmlContent = `
                    <div class="report-container">
                        <h3>Финансов отчет</h3>
                        <div style="font-size: 24px; font-weight: bold; color: #4CAF50; margin: 20px 0;">
                            Общ приход: ${totalRevenue.toFixed(2)} BGN
                        </div>
                        <p>Брой пратки: ${allEmployeeShipments.length}</p>
                        <p>Средна цена: ${(totalRevenue / allEmployeeShipments.length).toFixed(2)} BGN</p>
                    </div>
                `;
                break;
        }

        container.innerHTML = htmlContent;
    } catch (error) {
        container.innerHTML = `<p class="error">Грешка: ${error.message}</p>`;
    }
}

function showSection(sectionId) {
    // Скрий всички секции
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });

    // Скрий всички nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });

    // Покажи избраната секция
    document.getElementById(sectionId).classList.add('active');
    document.getElementById(`nav-${sectionId}`).classList.add('active');
}

function showManagement(managementType) {
    // TODO: Implement management functions
    alert("Управление на " + managementType + " - идва скоро");
}

function loadClientInfo(type) {
    // TODO: Load client address info
}

function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("role");
    window.location.href = "/login.html";
}

// Initialize on page load
window.onload = initDashboard;
