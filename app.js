const API_BASE = 'https://budget-manager-cloud-527220375721.us-central1.run.app';

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
    
    // Load data for the tab
    if (tabName === 'dashboard') {
        loadDashboard();
    } else if (tabName === 'banks') {
        loadBanks();
    } else if (tabName === 'accounts') {
        loadAccounts();
        loadBanksForSelect('accountBank');
    } else if (tabName === 'transactions') {
        loadTransactions();
        loadAccountsForSelect('transactionAccount');
    } else if (tabName === 'reports') {
        loadReports();
    }
}

// API calls
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { error: error.message };
    }
}

// Load dashboard data
async function loadDashboard() {
    try {
        const [banks, accounts, transactions] = await Promise.all([
            apiCall('/banks'),
            apiCall('/accounts'),
            apiCall('/transactions')
        ]);

        document.getElementById('totalBanks').textContent = banks.banks?.length || 0;
        document.getElementById('totalAccounts').textContent = accounts.accounts?.length || 0;
        document.getElementById('totalTransactions').textContent = transactions.transactions?.length || 0;
        
        const totalBalance = accounts.accounts?.reduce((sum, acc) => sum + parseFloat(acc.balance || 0), 0) || 0;
        document.getElementById('totalBalance').textContent = totalBalance.toFixed(2);
    } catch (error) {
        console.error('Dashboard load error:', error);
    }
}

// Load banks
async function loadBanks() {
    const data = await apiCall('/banks');
    const banksList = document.getElementById('banksList');
    
    if (data.error) {
        banksList.innerHTML = `<div class="error">Ошибка: ${data.error}</div>`;
        return;
    }
    
    if (data.banks && data.banks.length > 0) {
        let html = '<table class="data-table"><tr><th>ID</th><th>Название</th><th>Страна</th><th>Валюта</th><th>Создан</th></tr>';
        data.banks.forEach(bank => {
            html += `<tr>
                <td>${bank.id}</td>
                <td>${bank.name}</td>
                <td>${bank.country}</td>
                <td>${bank.currency}</td>
                <td>${new Date(bank.created_at).toLocaleDateString()}</td>
            </tr>`;
        });
        html += '</table>';
        banksList.innerHTML = html;
    } else {
        banksList.innerHTML = '<div class="loading">Нет банков</div>';
    }
}

// Load accounts
async function loadAccounts() {
    const data = await apiCall('/accounts');
    const accountsList = document.getElementById('accountsList');
    
    if (data.error) {
        accountsList.innerHTML = `<div class="error">Ошибка: ${data.error}</div>`;
        return;
    }
    
    if (data.accounts && data.accounts.length > 0) {
        let html = '<table class="data-table"><tr><th>ID</th><th>Название</th><th>Банк</th><th>Баланс</th><th>Валюта</th></tr>';
        data.accounts.forEach(account => {
            html += `<tr>
                <td>${account.id}</td>
                <td>${account.account_name}</td>
                <td>${account.bank_name}</td>
                <td>${parseFloat(account.balance).toFixed(2)}</td>
                <td>${account.currency}</td>
            </tr>`;
        });
        html += '</table>';
        accountsList.innerHTML = html;
    } else {
        accountsList.innerHTML = '<div class="loading">Нет счетов</div>';
    }
}

// Load transactions
async function loadTransactions() {
    const data = await apiCall('/transactions');
    const transactionsList = document.getElementById('transactionsList');
    
    if (data.error) {
        transactionsList.innerHTML = `<div class="error">Ошибка: ${data.error}</div>`;
        return;
    }
    
    if (data.transactions && data.transactions.length > 0) {
        let html = '<table class="data-table"><tr><th>ID</th><th>Сумма</th><th>Описание</th><th>Категория</th><th>Счет</th><th>Дата</th></tr>';
        data.transactions.forEach(transaction => {
            html += `<tr>
                <td>${transaction.id}</td>
                <td>${parseFloat(transaction.amount).toFixed(2)}</td>
                <td>${transaction.description || '-'}</td>
                <td>${transaction.category || '-'}</td>
                <td>${transaction.account_name}</td>
                <td>${new Date(transaction.transaction_date).toLocaleDateString()}</td>
            </tr>`;
        });
        html += '</table>';
        transactionsList.innerHTML = html;
    } else {
        transactionsList.innerHTML = '<div class="loading">Нет транзакций</div>';
    }
}

// Load reports
async function loadReports() {
    const [balanceData, statsData] = await Promise.all([
        apiCall('/reports/balance'),
        apiCall('/stats/summary')
    ]);
    
    // Balance report
    const balanceReport = document.getElementById('balanceReport');
    if (balanceData.balance_report && balanceData.balance_report.length > 0) {
        let html = '<table class="data-table"><tr><th>Банк</th><th>Валюта</th><th>Баланс</th><th>Счетов</th></tr>';
        balanceData.balance_report.forEach(row => {
            html += `<tr>
                <td>${row.bank_name}</td>
                <td>${row.currency}</td>
                <td>${parseFloat(row.total_balance).toFixed(2)}</td>
                <td>${row.account_count}</td>
            </tr>`;
        });
        html += '</table>';
        balanceReport.innerHTML = html;
    } else {
        balanceReport.innerHTML = '<div class="loading">Нет данных</div>';
    }
    
    // Summary stats
    const summaryStats = document.getElementById('summaryStats');
    if (statsData.total_transactions !== undefined) {
        let html = '<div class="stats">';
        html += `<div class="stat-card"><div class="stat-number">${statsData.total_transactions}</div><div class="stat-label">Всего транзакций</div></div>`;
        
        if (statsData.balance_by_currency && statsData.balance_by_currency.length > 0) {
            statsData.balance_by_currency.forEach(currency => {
                html += `<div class="stat-card"><div class="stat-number">${parseFloat(currency.total_balance).toFixed(2)}</div><div class="stat-label">${currency.currency}</div></div>`;
            });
        }
        
        html += '</div>';
        summaryStats.innerHTML = html;
    } else {
        summaryStats.innerHTML = '<div class="loading">Нет данных</div>';
    }
}

// Load banks for select
async function loadBanksForSelect(selectId) {
    const data = await apiCall('/banks');
    const select = document.getElementById(selectId);
    
    if (data.banks) {
        select.innerHTML = '<option value="">Выберите банк</option>';
        data.banks.forEach(bank => {
            select.innerHTML += `<option value="${bank.id}">${bank.name} (${bank.currency})</option>`;
        });
    }
}

// Load accounts for select
async function loadAccountsForSelect(selectId) {
    const data = await apiCall('/accounts');
    const select = document.getElementById(selectId);
    
    if (data.accounts) {
        select.innerHTML = '<option value="">Выберите счет</option>';
        data.accounts.forEach(account => {
            select.innerHTML += `<option value="${account.id}">${account.account_name} (${account.bank_name})</option>`;
        });
    }
}

// Form handlers
document.getElementById('bankForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('bankName').value,
        country: document.getElementById('bankCountry').value,
        currency: document.getElementById('bankCurrency').value
    };
    
    const result = await apiCall('/banks', 'POST', data);
    
    if (result.error) {
        alert(`Ошибка: ${result.error}`);
    } else {
        alert('Банк добавлен успешно!');
        document.getElementById('bankForm').reset();
        loadBanks();
        loadDashboard();
    }
});

document.getElementById('accountForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        bank_id: parseInt(document.getElementById('accountBank').value),
        account_name: document.getElementById('accountName').value,
        account_number: document.getElementById('accountNumber').value,
        balance: parseFloat(document.getElementById('accountBalance').value),
        currency: document.getElementById('accountCurrency').value
    };
    
    const result = await apiCall('/accounts', 'POST', data);
    
    if (result.error) {
        alert(`Ошибка: ${result.error}`);
    } else {
        alert('Счет добавлен успешно!');
        document.getElementById('accountForm').reset();
        loadAccounts();
        loadDashboard();
    }
});

document.getElementById('transactionForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        account_id: parseInt(document.getElementById('transactionAccount').value),
        amount: parseFloat(document.getElementById('transactionAmount').value),
        description: document.getElementById('transactionDescription').value,
        category: document.getElementById('transactionCategory').value,
        transaction_date: document.getElementById('transactionDate').value
    };
    
    const result = await apiCall('/transactions', 'POST', data);
    
    if (result.error) {
        alert(`Ошибка: ${result.error}`);
    } else {
        alert('Транзакция добавлена успешно!');
        document.getElementById('transactionForm').reset();
        loadTransactions();
        loadDashboard();
    }
});

// Set today's date for transaction form
document.getElementById('transactionDate').value = new Date().toISOString().split('T')[0];

// Load initial data
loadDashboard();
