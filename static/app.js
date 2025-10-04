const API_BASE = 'http://127.0.0.1:8004';

// URL Router - ДОПОЛНЕНИЕ к существующей навигации (НЕ ЗАМЕНА)
class URLRouter {
    constructor() {
        // Определяем базовый путь для GitHub Pages
        this.basePath = window.location.pathname.includes('/budget-manager-cloud/') 
            ? '/budget-manager-cloud' 
            : '';
        
        this.routes = {
            [this.basePath + '/']: 'dashboard',
            [this.basePath + '/banks']: 'banks',
            [this.basePath + '/transactions']: 'transactions',
            [this.basePath + '/advisor']: 'advisor'
        };
        
        console.log('🔧 URLRouter: basePath =', this.basePath);
        console.log('🔧 URLRouter: routes =', this.routes);
        this.init();
    }

    init() {
        // Обработка изменения URL (кнопка Назад браузера)
        window.addEventListener('popstate', (e) => {
            this.handleRoute(window.location.pathname);
        });

        // Обработка начального URL
        this.handleRoute(window.location.pathname);
    }

    handleRoute(path) {
        console.log(`🔍 handleRoute: ${path}`);
        console.log(`🔍 available routes:`, Object.keys(this.routes));
        
        // Ищем точное совпадение
        let tabName = this.routes[path];
        
        // Если точного совпадения нет, пробуем найти по частичному совпадению
        if (!tabName) {
            for (const [route, tab] of Object.entries(this.routes)) {
                if (path.startsWith(route)) {
                    tabName = tab;
                    break;
                }
            }
        }
        
        // Если ничего не найдено, используем dashboard
        if (!tabName) {
            tabName = 'dashboard';
        }
        
        console.log(`🔄 URL Router: ${path} → ${tabName}`);
        
        // Используем СУЩЕСТВУЮЩУЮ функцию showTab - НЕ МЕНЯЕМ ЕЁ
        // Задержка для гарантии, что showTab уже определена
        setTimeout(() => {
            if (typeof showTab === 'function') {
                showTab(tabName);
            }
        }, 0);
    }

    // Функция для программной навигации
    navigateToTab(tabName) {
        const routeMap = {
            'dashboard': this.basePath + '/',
            'banks': this.basePath + '/banks',
            'transactions': this.basePath + '/transactions', 
            'advisor': this.basePath + '/advisor'
        };
        
        const path = routeMap[tabName];
        if (path) {
            history.pushState({}, '', path);
            console.log(`🔄 Navigate to: ${path}`);
        }
    }
}

// Роутер будет создан в конце файла после определения всех функций

// Восстановление текущей страницы после обновления - ВЫПОЛНЯЕТСЯ ПЕРВЫМ
(function() {
    const currentPage = localStorage.getItem('currentPage');
    if (currentPage === 'plaid_management' && window.location.pathname === '/') {
        console.log('Восстанавливаем страницу Plaid после обновления');
        window.location.href = '/plaid_management.html';
        return;
    }
})();

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app...');
    
    // Initialize app
    loadDashboard();
    
    // Initialize form handlers
    initializeFormHandlers();
    
    // Set today's date for transaction form
    const transactionDate = document.getElementById('transactionDate');
    if (transactionDate) {
        transactionDate.value = new Date().toISOString().split('T')[0];
    }
});

// Initialize form handlers
function initializeFormHandlers() {
    const bankForm = document.getElementById('bankForm');
    if (bankForm) {
        bankForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                name: document.getElementById('bankName').value,
                country: document.getElementById('bankCountry').value,
                currency: document.getElementById('bankCurrency').value
            };
            
            const result = await apiCall('/api/banks', 'POST', data);
            if (result.error) {
                alert(`Ошибка: ${result.error}`);
            } else {
                alert('Банк добавлен успешно!');
                document.getElementById('bankForm').reset();
                loadBanks();
                // loadDashboard(); // REMOVED - вызывается в DOMContentLoaded
            }
        });
    }
    
    const accountForm = document.getElementById('accountForm');
    if (accountForm) {
        accountForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                bank_id: document.getElementById('accountBank').value,
                account_name: document.getElementById('accountName').value,
                account_type: document.getElementById('accountType').value,
                balance: parseFloat(document.getElementById('accountBalance').value)
            };
            
            const result = await apiCall('/accounts', 'POST', data);
            if (result.error) {
                alert(`Ошибка: ${result.error}`);
            } else {
                alert('Счет добавлен успешно!');
                document.getElementById('accountForm').reset();
                loadAccounts();
                // loadDashboard(); // REMOVED - вызывается в DOMContentLoaded
            }
        });
    }
    
    const transactionForm = document.getElementById('transactionForm');
    if (transactionForm) {
        transactionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                account_id: document.getElementById('transactionAccount').value,
                amount: parseFloat(document.getElementById('transactionAmount').value),
                description: document.getElementById('transactionDescription').value,
                category: document.getElementById('transactionCategory').value,
                date: document.getElementById('transactionDate').value
            };
            
            const result = await apiCall('/transactions', 'POST', data);
            if (result.error) {
                alert(`Ошибка: ${result.error}`);
            } else {
                alert('Транзакция добавлена успешно!');
                document.getElementById('transactionForm').reset();
                loadTransactions();
                // loadDashboard(); // REMOVED - вызывается в DOMContentLoaded
            }
        });
    }
}

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
    
    // Находим кнопку с нужным ID и делаем её активной
    const activeButton = document.querySelector(`[onclick*="showTab('${tabName}')"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    // ДОБАВЛЯЕМ URL-навигацию - НЕ МЕНЯЯ существующую логику
    // НЕ обновляем URL для кнопки "Главная" - это вызывает проблемы
    if (typeof router !== 'undefined' && tabName !== 'dashboard') {
        router.navigateToTab(tabName);
    }
    
    // Load data for the tab
    if (tabName === 'dashboard') {
        // loadDashboard(); // REMOVED - вызывается в DOMContentLoaded
    } else if (tabName === 'banks') {
        setTimeout(() => loadBanksForManagement(), 100);
    } else if (tabName === 'accounts') {
        loadAccounts();
        // loadBanksForSelect('accountBank'); // Элемент не существует
    } else if (tabName === 'transactions') {
        loadTransactions();
        // loadAccountsForSelect('transactionAccount'); // Элемент не существует
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
        
        console.log(`Making API call to: ${API_BASE}${endpoint}`);
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        console.log(`Response status: ${response.status}`);
        console.log(`Response headers:`, response.headers);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        console.log(`Content-Type: ${contentType}`);
        
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Expected JSON but got:', contentType, text.substring(0, 200));
            throw new Error(`Expected JSON but got ${contentType}`);
        }
        
        const jsonData = await response.json();
        console.log(`API response:`, jsonData);
        return jsonData;
    } catch (error) {
        console.error('API Error:', error);
        return { error: error.message };
    }
}

// Load dashboard data
async function loadDashboard() {
    try {
        const [banks, accounts, transactions] = await Promise.all([
            apiCall('/api/banks'),
            apiCall('/accounts'),
            apiCall('/transactions')
        ]);

        // Check if elements exist before updating
        console.log('Loading dashboard data...');
        console.log('Banks:', banks);
        console.log('Accounts:', accounts);
        console.log('Transactions:', transactions);
        
        // These elements don't exist in HTML, so we skip them
        // const totalBanksElement = document.getElementById('totalBanks');
        // const totalAccountsElement = document.getElementById('totalAccounts');
        // const totalTransactionsElement = document.getElementById('totalTransactions');
        // const totalBalanceElement = document.getElementById('totalBalance');

        // Load additional data
        await loadPlaidUsage();
        await loadExchangeRates();
        await loadAssets(); // ВОССТАНОВЛЕНО - используем данные из вкладки "Банки"
        
    } catch (error) {
        console.error('Dashboard load error:', error);
    }
}

// Load banks
async function loadBanks() {
    console.log('Loading banks...');
    const data = await apiCall('/api/banks');
    console.log('Banks data:', data);
    
    const banksGrid = document.getElementById('banksGrid');
    
    if (!banksGrid) {
        console.log('banksGrid element not found');
        return;
    }
    
    if (data.error) {
        banksGrid.innerHTML = `<div class="error">Ошибка: ${data.error}</div>`;
        return;
    }
    
    if (data.banks && data.banks.length > 0) {
        let html = '';
        data.banks.forEach(bank => {
            html += `
            <div class="bank-card">
                <div class="bank-header">
                    <div class="bank-name">${bank.name}</div>
                    <div class="bank-balance">${bank.currency} 0.00</div>
                </div>
                <div class="accounts-list">
                    <div class="account-item">Нет счетов</div>
                </div>
            </div>`;
        });
        banksGrid.innerHTML = html;
    } else {
        banksGrid.innerHTML = '<div class="loading">Нет банков</div>';
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
    const transactionsStats = document.getElementById('transactionsStats');
    
    if (!transactionsStats) {
        console.log('transactionsStats element not found');
        return;
    }
    
    if (data.error) {
        transactionsStats.innerHTML = `<div class="error">Ошибка: ${data.error}</div>`;
        return;
    }
    
    if (data.transactions && data.transactions.length > 0) {
        let html = '<div class="transactions-summary">';
        html += `<h3>Статистика транзакций</h3>`;
        html += `<p>Всего транзакций: ${data.transactions.length}</p>`;
        html += '</div>';
        transactionsStats.innerHTML = html;
    } else {
        transactionsStats.innerHTML = '<div class="loading">Нет транзакций</div>';
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
    const data = await apiCall('/api/banks');
    const select = document.getElementById(selectId);
    
    if (!select) {
        console.log(`Select element with id '${selectId}' not found`);
        return;
    }
    
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
    
    if (!select) {
        console.log(`Element with id ${selectId} not found`);
        return;
    }
    
    if (data.accounts) {
        select.innerHTML = '<option value="">Выберите счет</option>';
        data.accounts.forEach(account => {
            select.innerHTML += `<option value="${account.id}">${account.account_name} (${account.bank_name})</option>`;
        });
    }
}

// Form handlers - MOVED TO initializeFormHandlers() function
// const bankForm = document.getElementById('bankForm');
/*
if (bankForm) {
    bankForm.addEventListener('submit', async (e) => {
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
        // loadDashboard(); // REMOVED - вызывается в DOMContentLoaded
    }
});
}
*/

/*
const accountForm = document.getElementById('accountForm');
if (accountForm) {
    accountForm.addEventListener('submit', async (e) => {
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
        // loadDashboard(); // REMOVED - вызывается в DOMContentLoaded
    }
});
}
*/

/*
const transactionForm = document.getElementById('transactionForm');
if (transactionForm) {
    transactionForm.addEventListener('submit', async (e) => {
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
        // loadDashboard(); // REMOVED - вызывается в DOMContentLoaded
    }
});
}
*/

// Set today's date for transaction form - MOVED TO initializeFormHandlers()
/*
const transactionDate = document.getElementById('transactionDate');
if (transactionDate) {
    transactionDate.value = new Date().toISOString().split('T')[0];
}
*/

// Load Plaid usage counter
async function loadPlaidUsage() {
    try {
        console.log('🔄 Загружаем счетчик Plaid API...');
        
        // Сначала пробуем получить данные из кэша
        const usageResponse = await fetch(`${API_BASE}/api/banks/plaid/usage`);
        const usageData = await usageResponse.json();
        
        console.log('📊 Данные счетчика Plaid из кэша:', usageData);
        
        if (usageData.error) {
            console.error('Plaid usage error:', usageData.error);
            return;
        }
        
        // Всегда используем данные из кэша, НЕ делаем автоматических запросов к Plaid
        console.log('✅ Используем данные из кэша (автоматические запросы отключены):', usageData);
        updatePlaidCounter(usageData.used, usageData.limit);
        
    } catch (error) {
        console.error('Error loading Plaid usage:', error);
        // Set default values on error
        updatePlaidCounter(7, 100);
    }
}

// Обновление счетчика Plaid в UI
function updatePlaidCounter(used, limit) {
        const plaidUsedElement = document.getElementById('plaid-used');
        const plaidLimitElement = document.getElementById('plaid-limit');
        
        if (plaidUsedElement) {
        plaidUsedElement.textContent = used || 0;
        console.log(`✅ Обновлен счетчик: ${used}/${limit}`);
        } else {
            console.error('❌ Элемент plaid-used не найден!');
        }
        
        if (plaidLimitElement) {
        plaidLimitElement.textContent = limit || 100;
        } else {
            console.error('❌ Элемент plaid-limit не найден!');
    }
}

// Функция для перехода на главную страницу
function goHome() {
    // Очищаем localStorage для корректного перехода
    localStorage.removeItem('currentPage');
    
    // Определяем правильный путь к главной странице
    const currentPath = window.location.pathname;
    const isOnGitHubPages = currentPath.includes('/budget-manager-cloud/');
    
    console.log('🔍 goHome() - currentPath:', currentPath);
    console.log('🔍 goHome() - isOnGitHubPages:', isOnGitHubPages);
    
    if (isOnGitHubPages) {
        // Мы на GitHub Pages - переходим на правильный базовый путь
        console.log('🏠 Переходим на главную страницу GitHub Pages');
        window.location.href = '/budget-manager-cloud/';
    } else {
        // Мы на локальном сервере - переходим на главную
        console.log('🏠 Переходим на главную страницу (локальный сервер)');
        window.location.href = '/';
    }
}

// Функция для перехода на главную страницу БЕЗ изменения URL
function goHomeNoURL() {
    console.log('🏠 Переходим на главную страницу БЕЗ изменения URL');
    // Просто переключаем на вкладку dashboard
    showTab('dashboard');
}

// Загрузка курсов валют
async function loadExchangeRates() {
    console.log('🚀 НАЧИНАЕМ ЗАГРУЗКУ КУРСОВ ВАЛЮТ');
    
    // Используем только рабочий API
    const apiUrl = 'https://api.exchangerate-api.com/v4/latest/USD';
    
    try {
        console.log(`🔄 Загружаем курсы валют с API: ${apiUrl}`);
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📊 Курсы валют получены:', data);
        
        // API возвращает курсы в формате data.rates
        const rates = data.rates;
        if (!rates) {
            throw new Error('Нет данных о курсах');
        }
        
        console.log('🔍 Проверяем нужные валюты:');
        console.log('CAD:', rates.CAD);
        console.log('EUR:', rates.EUR);
        console.log('UAH:', rates.UAH);
        console.log('RUB:', rates.RUB);
        
        // Обновляем глобальные курсы (конвертируем в формат USD -> валюта)
        // USD всегда равен 1 (базовая валюта)
        customRates.USD = 1;
        console.log('✅ USD установлен:', customRates.USD);
        
        if (rates.CAD) {
            customRates.CAD = rates.CAD;
            console.log('✅ CAD обновлен:', customRates.CAD);
        }
        if (rates.EUR) {
            customRates.EUR = rates.EUR;
            console.log('✅ EUR обновлен:', customRates.EUR);
        }
        if (rates.UAH) {
            customRates.UAH = rates.UAH;
            console.log('✅ UAH обновлен:', customRates.UAH);
        }
        if (rates.RUB) {
            customRates.RUB = rates.RUB;
            console.log('✅ RUB обновлен:', customRates.RUB);
        }
        
        console.log('✅ ВСЕ КУРСЫ ОБНОВЛЕНЫ:', customRates);
        
        // Обновляем UI
        console.log('🔄 Обновляем UI...');
        updateRatesUI();
        console.log('✅ UI обновлен');
        
    } catch (error) {
        console.error(`❌ API не работает:`, error.message);
        console.log('⚠️ Используем текущие курсы:', customRates);
        updateRatesUI();
    }
}

// Обновление UI курсов валют
function updateRatesUI() {
    // Обновляем пары валют
    for (let i = 1; i <= 4; i++) {
        updateCurrencyPair(i);
    }
}

// Обновление курсов валют
function refreshRates() {
    const button = document.querySelector('.refresh-rates');
    button.textContent = 'Обновление...';
    button.disabled = true;
    
    loadExchangeRates().finally(() => {
        button.textContent = 'Обновить';
        button.disabled = false;
    });
}

// Обновление счетчика Plaid API
async function refreshPlaidCounter() {
    const button = document.querySelector('.refresh-plaid');
    
    // Обновляем UI
    button.textContent = 'Обновление...';
    button.disabled = true;
    
    try {
        console.log('Отправляем запрос на принудительное обновление Plaid API...');
        
        // Вызываем новый endpoint для принудительного обновления
        const response = await fetch(`${API_BASE}/api/banks/plaid/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        console.log('Ответ от Plaid refresh:', data);
        
        if (data.success) {
            // Обновляем счетчик с новыми данными
            updatePlaidCounter(data.used, data.limit);
            
            console.log(`Счетчик обновлен: ${data.used}/${data.limit}`);
            
            // Показываем успешное обновление
            button.textContent = 'Обновлено!';
            
            // Через 2 секунды возвращаем обычное состояние
            setTimeout(() => {
                button.textContent = 'Обновить';
                button.disabled = false;
            }, 2000);
            
        } else {
            throw new Error(data.error || 'Ошибка обновления');
        }
        
    } catch (error) {
        console.error('Ошибка обновления Plaid API:', error);
        
        // Показываем ошибку
        button.textContent = 'Ошибка!';
        
        // Через 2 секунды возвращаем обычное состояние
        setTimeout(() => {
            button.textContent = 'Обновить';
            button.disabled = false;
        }, 2000);
    }
}

// Защита от повторного вызова
let assetsLoading = false;

// Загрузка активов по регионам (используем данные из вкладки "Банки")
async function loadAssets() {
    if (assetsLoading) {
        console.log('⏳ Загрузка активов уже выполняется, пропускаем...');
            return;
        }
        
    assetsLoading = true;
    console.log('🚀 Начинаем загрузку активов из данных вкладки "Банки"...');
    try {
        // Используем те же данные, что и во вкладке "Банки"
        console.log(`📡 Запрашиваем статус банков с ${API_BASE}/api/banks/status`);
        const statusResponse = await fetch(`${API_BASE}/api/banks/status`);
        console.log('📡 Ответ получен:', statusResponse.status);
        
        if (!statusResponse.ok) {
            console.error('Ошибка HTTP:', statusResponse.status, statusResponse.statusText);
            return;
        }
        
        const banksData = await statusResponse.json();
        console.log('📊 Данные статуса банков:', banksData);
        
        if (!banksData || banksData.length === 0) {
            console.log('Нет банков для отображения');
            return;
        }
        
        // Группируем банки по регионам
        const regions = {
            canada: { banks: [], totalBalance: 0 },
            ukraine: { banks: [], totalBalance: 0 },
            other: { banks: [], totalBalance: 0 },
            investments: { banks: [], totalBalance: 0 }
        };
        
        // Загружаем данные для каждого банка
        for (const bank of banksData) {
            console.log(`Загружаем данные для банка: ${bank.name} (${bank.code})`);
            
            const bankInfo = {
                id: bank.code,
                name: bank.name,
                accounts: [],
                totalBalance: 0
            };
            
            // Используем ТЕСТОВЫЕ данные для демонстрации - НЕ делаем запросов к Plaid
            console.log(`📊 Используем тестовые данные для ${bank.name} (${bank.code})`);
            
            // Тестовые данные для демонстрации
            if (bank.code === 'RBC') {
                bankInfo.accounts = [
                    { id: '1', name: 'RBC Advantage Banking', balance: '119.14', currency: 'CAD' },
                    { id: '2', name: 'RBC ION Visa', balance: '60.42', currency: 'CAD' },
                    { id: '3', name: 'RBC U.S. High Interest eSavings', balance: '100.82', currency: 'USD' },
                    { id: '4', name: 'RBC High Interest eSavings', balance: '3004.68', currency: 'CAD' },
                    { id: '5', name: 'RBC Advantage Banking', balance: '1477.60', currency: 'CAD' }
                ];
                console.log(`✅ Тестовые данные: ${bankInfo.accounts.length} счетов для ${bank.name}`);
            } else if (bank.code === 'BMO') {
                bankInfo.accounts = [
                    { id: '6', name: 'MasterCard', balance: '7500.00', currency: 'CAD' },
                    { id: '7', name: 'Chequing', balance: '100.00', currency: 'CAD' }
                ];
                console.log(`✅ Тестовые данные: ${bankInfo.accounts.length} счетов для ${bank.name}`);
            } else {
                bankInfo.accounts = [];
                console.log(`❌ Нет тестовых данных для ${bank.name}`);
            }
            
            bankInfo.totalBalance = bankInfo.accounts.reduce((sum, account) => {
                const balance = parseFloat(account.balance) || 0;
                            return sum + balance;
                        }, 0);
            
                        console.log(`💵 Общий баланс ${bank.name}: ${bankInfo.totalBalance}`);
            
            // Определяем регион на основе названия банка
            if (bank.name.includes('Royal Bank of Canada') || bank.name.includes('RBC') || 
                bank.name.includes('Bank of Montreal') || bank.name.includes('BMO') || 
                bank.name.includes('Walmart Rewards') || bank.name.includes('WALMART') ||
                bank.name.includes('Canadian Imperial Bank of Commerce') || bank.name.includes('CIBC')) {
                regions.canada.banks.push(bankInfo);
                regions.canada.totalBalance += bankInfo.totalBalance;
                console.log(`Добавлен в Канаду: ${bank.name} с балансом ${bankInfo.totalBalance}`);
            } else if (bank.name.includes('PrivatBank') || bank.name.includes('Monobank') || 
                       bank.name.includes('Raiffeisen') || bank.name.includes('PUMB')) {
                regions.ukraine.banks.push(bankInfo);
                regions.ukraine.totalBalance += bankInfo.totalBalance;
                console.log(`Добавлен в Украину: ${bank.name} с балансом ${bankInfo.totalBalance}`);
            } else if (bank.name.includes('Interactive Brokers') || bank.name.includes('Investment')) {
                regions.investments.banks.push(bankInfo);
                regions.investments.totalBalance += bankInfo.totalBalance;
                console.log(`Добавлен в Инвестиции: ${bank.name} с балансом ${bankInfo.totalBalance}`);
            } else {
                regions.other.banks.push(bankInfo);
                regions.other.totalBalance += bankInfo.totalBalance;
                console.log(`Добавлен в Другие: ${bank.name} с балансом ${bankInfo.totalBalance}`);
            }
        }
        
        console.log('Финальные регионы:', regions);
        
        // Отображаем данные
        console.log('🎨 Отображаем активы по регионам...');
        displayRegionAssets('canada', regions.canada);
        displayRegionAssets('ukraine', regions.ukraine);
        displayRegionAssets('other', regions.other);
        displayRegionAssets('investments', regions.investments);
        
        // Инициализируем конвертеры валют (отключено - элементы не существуют)
        // setTimeout(() => {
        //     convertCurrency('canada', 'CAD');
        //     convertCurrency('ukraine', 'UAH');
        //     convertCurrency('other', 'USD');
        //     convertCurrency('investments', 'USD');
        // }, 1000);
        
    } catch (error) {
        console.error('Ошибка загрузки активов:', error);
    } finally {
        assetsLoading = false;
    }
}

// Отображение активов региона
function displayRegionAssets(regionId, regionData) {
    console.log(`🎨 Отображаем ${regionId}:`, regionData);
    const container = document.getElementById(`${regionId}-banks`);
    
    if (!container) {
        console.error(`❌ Контейнер ${regionId}-banks не найден!`);
        return;
    }
    
    // Отображаем банки
    if (regionData.banks.length === 0) {
        container.innerHTML = `
            <div class="loading-state">
                <div>Нет подключенных банков</div>
            </div>
        `;
        return;
    }
    
    let html = '';
    for (const bank of regionData.banks) {
        const currency = regionId === 'ukraine' ? '₴' : '$';
        const currencyCode = regionId === 'ukraine' ? 'UAH' : 
                           regionId === 'canada' ? 'CAD' : 'USD';
        
        html += `
            <div class="bank-card">
                <div class="bank-header">
                    <div class="bank-name">${bank.name}</div>
                </div>
                <div class="accounts-list">
                    ${bank.accounts.length > 0 ? 
                        bank.accounts.map(account => `
                            <div class="account-item">
                                <div class="account-name">${account.name || 'Счет'}</div>
                                <div class="account-balance">${currency}${(parseFloat(account.balance) || 0).toFixed(2)} ${account.currency || currencyCode}</div>
                                <div class="account-converter">
                                    <select onchange="convertAccountCurrency('${regionId}', '${bank.id}', '${account.id || 'default'}', this.value)">
                                        <option value="">В валюте</option>
                                        ${getCurrencyOptions(account.currency || currencyCode)}
                                    </select>
                                    <div class="account-converted-balance" id="converted-${regionId}-${bank.id}-${account.id || 'default'}">${currency}${(parseFloat(account.balance) || 0).toFixed(2)}</div>
                                </div>
                            </div>
                        `).join('') :
                        '<div class="loading-state">Нет счетов</div>'
                    }
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Генерация опций валют без оригинальной валюты
function getCurrencyOptions(originalCurrency) {
    const allCurrencies = ['USD', 'EUR', 'CAD', 'UAH', 'RUB'];
    const filteredCurrencies = allCurrencies.filter(currency => currency !== originalCurrency);
    
    return filteredCurrencies.map(currency => 
        `<option value="${currency}">${currency}</option>`
    ).join('');
}

// Конвертер валют для отдельных счетов
function convertAccountCurrency(regionId, bankId, accountId, targetCurrency) {
    const convertedElement = document.getElementById(`converted-${regionId}-${bankId}-${accountId}`);
    if (!convertedElement) {
        console.log(`Элемент converted-${regionId}-${bankId}-${accountId} не найден`);
        return;
    }
    
    // Если выбрано "В валюте" - показываем оригинальный баланс
    if (!targetCurrency) {
        const accountItem = convertedElement.closest('.account-item');
        const balanceText = accountItem.querySelector('.account-balance').textContent;
        convertedElement.textContent = balanceText;
        return;
    }
    
    // Получаем оригинальный баланс из текста
    const accountItem = convertedElement.closest('.account-item');
    const balanceText = accountItem.querySelector('.account-balance').textContent;
    const balance = parseFloat(balanceText.replace(/[^\d.-]/g, ''));
    
    if (isNaN(balance)) {
        console.log(`Неверный баланс: ${balanceText}`);
        return;
    }
    
    // Получаем оригинальную валюту из текста баланса
    const originalCurrency = balanceText.match(/[A-Z]{3}/)?.[0] || 'CAD';
    
    console.log(`Конвертируем ${balance} ${originalCurrency} в ${targetCurrency}`);
    console.log('Доступные курсы:', customRates);
    
    // Проверяем наличие курсов валют
    if (!customRates[originalCurrency] || !customRates[targetCurrency]) {
        console.log(`Курсы не найдены: ${originalCurrency}=${customRates[originalCurrency]}, ${targetCurrency}=${customRates[targetCurrency]}`);
        convertedElement.textContent = 'N/A';
        return;
    }
    
    // Конвертируем: originalCurrency -> USD -> targetCurrency
    const usdAmount = balance / customRates[originalCurrency];
    const convertedAmount = usdAmount * customRates[targetCurrency];
    
    if (isNaN(convertedAmount)) {
        console.log('Ошибка конвертации');
        convertedElement.textContent = 'N/A';
        return;
    }
    
    const currencySymbol = targetCurrency === 'UAH' ? '₴' : 
                          targetCurrency === 'EUR' ? '€' : '$';
    
    convertedElement.textContent = `${currencySymbol}${convertedAmount.toFixed(2)}`;
    console.log(`✅ Конвертировано: ${convertedAmount.toFixed(2)} ${targetCurrency}`);
}

// Конвертер валют (старая функция - оставляем для совместимости)
function convertCurrency(regionId, targetCurrency) {
    const balanceElement = document.getElementById(`${regionId}-balance`);
    const convertedElement = document.getElementById(`${regionId}-converted`);
    
    if (!balanceElement || !convertedElement) {
        console.log(`Элементы для ${regionId} не найдены, пропускаем`);
        return;
    }
    
    // Получаем текущий баланс
    const balanceText = balanceElement.textContent;
    const balance = parseFloat(balanceText.replace(/[^\d.-]/g, ''));
    
    if (isNaN(balance)) {
        console.log(`Неверный баланс для ${regionId}`);
        return;
    }
    
    // Используем глобальные курсы валют
    console.log('Используем глобальные курсы:', customRates);
    
    // Определяем исходную валюту региона
    let sourceCurrency = 'USD';
    if (regionId === 'canada') sourceCurrency = 'CAD';
    else if (regionId === 'ukraine') sourceCurrency = 'UAH';
    
    // Конвертируем: sourceCurrency -> USD -> targetCurrency
    if (!customRates[sourceCurrency] || !customRates[targetCurrency]) {
        convertedElement.textContent = 'N/A';
        return;
    }
    
    const usdAmount = balance / customRates[sourceCurrency];
    const convertedAmount = usdAmount * customRates[targetCurrency];
    
    if (isNaN(convertedAmount)) {
        convertedElement.textContent = 'N/A';
        return;
    }
    
    const currencySymbol = targetCurrency === 'UAH' ? '₴' : 
                          targetCurrency === 'EUR' ? '€' : 
                          targetCurrency === 'RUB' ? '₽' : '$';
    
    convertedElement.textContent = `${currencySymbol}${convertedAmount.toFixed(2)}`;
}

// Отправка сообщения консультанту
function sendAdvisorMessage() {
    const input = document.getElementById('advisor-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    const messagesContainer = document.getElementById('advisor-messages');
    
    // Добавляем сообщение пользователя
    const userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.innerHTML = `<strong>Вы:</strong> ${message}`;
    messagesContainer.appendChild(userMessage);
    
    // Очищаем поле ввода
    input.value = '';
    
    // Прокручиваем вниз
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Имитируем ответ консультанта
    setTimeout(() => {
        const advisorMessage = document.createElement('div');
        advisorMessage.className = 'message advisor-message';
        advisorMessage.innerHTML = `<strong>Консультант:</strong> Спасибо за вопрос! Я анализирую ваши данные и скоро дам рекомендацию.`;
        messagesContainer.appendChild(advisorMessage);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 1000);
}

// Загрузка банков для вкладки "Банки"
async function loadBanksForManagement() {
    console.log('🏦 Начинаем загрузку банков для управления...');
    try {
        console.log(`📡 Запрашиваем статус банков с ${API_BASE}/api/banks/status`);
        const response = await fetch(`${API_BASE}/api/banks/status`);
        console.log('📡 Ответ получен:', response.status);
        const banksData = await response.json();
        console.log('📊 Данные статуса банков:', banksData);
        
        const banksGrid = document.getElementById('banksGrid');
        
        if (!banksGrid) {
            console.error('❌ Элемент banksGrid не найден!');
            return;
        }
        
        if (!banksData || banksData.length === 0) {
            banksGrid.innerHTML = '<div class="empty-state">Нет подключенных банков</div>';
            return;
        }
        
        let html = '';
        
        for (const bank of banksData) {
            // Загружаем счета для каждого банка
            let accounts = [];
            try {
                const accountsResponse = await fetch(`${API_BASE}/api/banks/${bank.code}/accounts`);
                const accountsData = await accountsResponse.json();
                accounts = accountsData || [];
            } catch (error) {
                console.error(`Ошибка загрузки счетов для ${bank.name}:`, error);
            }
            
            const statusClass = bank.status === 'working' ? 'working' : 'error';
            const statusText = bank.status === 'working' ? 'Работает' : 'Ошибка';
            
            html += `
                <div class="bank-card">
                    <div class="bank-header">
                        <div class="bank-name">${bank.name}</div>
                        <div class="bank-status ${statusClass}">${statusText}</div>
                    </div>
                    
                    <div class="bank-info">
                        <div class="info-item">
                            <div class="info-label">Счетов</div>
                            <div class="info-value">${bank.accounts_count}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Последняя транзакция</div>
                            <div class="info-value">${bank.last_transaction_date || 'Нет'}</div>
                        </div>
                    </div>
                    
                    ${accounts.length > 0 ? `
                        <div class="accounts-section">
                            <div class="accounts-title">Счета:</div>
                            ${accounts.map(account => `
                                <div class="account-item">
                                    <div class="account-name">${account.name}</div>
                                    <div class="account-balance">${account.balance} ${account.currency}</div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    <div class="bank-actions">
                        <button class="btn-small btn-refresh" onclick="refreshBank('${bank.code}')">Обновить</button>
                        <button class="btn-small btn-accounts" onclick="viewAccounts('${bank.code}')">Счета</button>
                        <button class="btn-small btn-transactions" onclick="viewTransactions('${bank.code}')">Транзакции</button>
                    </div>
                </div>
            `;
        }
        
        banksGrid.innerHTML = html;
        
    } catch (error) {
        console.error('Ошибка загрузки банков:', error);
        document.getElementById('banksGrid').innerHTML = '<div class="empty-state">Ошибка загрузки банков</div>';
    }
}

// Функции для кнопок банков
function refreshBank(bankCode) {
    console.log(`Обновление банка ${bankCode}`);
    // Здесь можно добавить логику обновления
}

function viewAccounts(bankCode) {
    console.log(`Просмотр счетов банка ${bankCode}`);
    // Здесь можно добавить логику просмотра счетов
}

function viewTransactions(bankCode) {
    console.log(`Просмотр транзакций банка ${bankCode}`);
    // Здесь можно добавить логику просмотра транзакций
}

// Функции переключения между методами управления банками
function showPlaidManagement() {
    console.log('Переход на страницу управления Plaid');
    window.location.href = '/budget-manager-cloud/plaid_management.html';
}

function showApiManagement() {
    console.log('Переключение на управление API');
    
    // Обновляем активную плитку
    document.querySelectorAll('.method-card').forEach(card => card.classList.remove('active'));
    document.getElementById('api-method').classList.add('active');
    
    // Показываем соответствующий контент
    document.querySelectorAll('.management-content').forEach(content => content.style.display = 'none');
    document.getElementById('api-management').style.display = 'block';
}

function showScrapingManagement() {
    console.log('Переключение на управление скраппингом');
    
    // Обновляем активную плитку
    document.querySelectorAll('.method-card').forEach(card => card.classList.remove('active'));
    document.getElementById('scraping-method').classList.add('active');
    
    // Показываем соответствующий контент
    document.querySelectorAll('.management-content').forEach(content => content.style.display = 'none');
    document.getElementById('scraping-management').style.display = 'block';
}

function showManualManagement() {
    console.log('Переключение на ручное управление');
    
    // Обновляем активную плитку
    document.querySelectorAll('.method-card').forEach(card => card.classList.remove('active'));
    document.getElementById('manual-method').classList.add('active');
    
    // Показываем соответствующий контент
    document.querySelectorAll('.management-content').forEach(content => content.style.display = 'none');
    document.getElementById('manual-management').style.display = 'block';
}

async function openPlaidLink() {
    console.log('Открытие Plaid Link...');
    
    try {
        // Получаем конфигурацию Plaid Link
        const response = await fetch(`${API_BASE}/api/plaid/link/config`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const config = await response.json();
        console.log('Plaid Link конфигурация:', config);
        
        // Здесь будет логика открытия Plaid Link
        // Пока показываем сообщение
        alert('Plaid Link будет открыт в новом окне. Функция в разработке.');
        
    } catch (error) {
        console.error('Ошибка получения конфигурации Plaid Link:', error);
        alert('Ошибка подключения к Plaid Link: ' + error.message);
    }
}

// Глобальные курсы валют (настраиваемые)
let customRates = {
    'USD': 1,     // USD к USD (базовая валюта)
    'CAD': 1.35,  // CAD к USD
    'EUR': 0.85,  // EUR к USD
    'UAH': 41.0,  // UAH к USD
    'RUB': 83.0   // RUB к USD
};

// Обновление пользовательского курса
function updateCustomRate(fromCurrency, toCurrency, value) {
    const rate = parseFloat(value);
    if (isNaN(rate)) return;
    
    if (fromCurrency === 'CAD' && toCurrency === 'USD') {
        customRates.CAD = rate;
    } else if (fromCurrency === 'USD' && toCurrency === 'EUR') {
        customRates.EUR = rate;
    } else if (fromCurrency === 'USD' && toCurrency === 'UAH') {
        customRates.UAH = rate;
    } else if (fromCurrency === 'USD' && toCurrency === 'RUB') {
        customRates.RUB = rate;
    }
    
    console.log('Обновлены курсы:', customRates);
}

// Конвертация валют в отдельном разделе
function convertCurrencyAmount() {
    const amountElement = document.getElementById('converter-amount');
    const fromCurrencyElement = document.getElementById('converter-from');
    const toCurrencyElement = document.getElementById('converter-to');
    const resultElement = document.getElementById('converter-result');
    
    if (!amountElement || !fromCurrencyElement || !toCurrencyElement || !resultElement) {
        console.error('Элементы конвертера не найдены');
        return;
    }
    
    const amount = parseFloat(amountElement.value);
    const fromCurrency = fromCurrencyElement.value;
    const toCurrency = toCurrencyElement.value;
    
    console.log(`Конвертируем: ${amount} ${fromCurrency} -> ${toCurrency}`);
    
    if (isNaN(amount) || amount <= 0) {
        resultElement.textContent = 'Введите корректную сумму';
        return;
    }
    
    if (fromCurrency === toCurrency) {
        resultElement.textContent = `${getCurrencySymbol(toCurrency)}${amount.toFixed(2)}`;
        return;
    }
    
    // Проверяем наличие курсов валют
    if (!customRates[fromCurrency] || !customRates[toCurrency]) {
        console.log(`Курсы не найдены: ${fromCurrency}=${customRates[fromCurrency]}, ${toCurrency}=${customRates[toCurrency]}`);
        resultElement.textContent = 'Курс не найден';
        return;
    }
    
    // Конвертируем: fromCurrency -> USD -> toCurrency
    const usdAmount = amount / customRates[fromCurrency];
    const convertedAmount = usdAmount * customRates[toCurrency];
    
    if (isNaN(convertedAmount)) {
        console.log('Ошибка конвертации');
        resultElement.textContent = 'Ошибка конвертации';
        return;
    }
    
    const symbol = getCurrencySymbol(toCurrency);
    resultElement.textContent = `${symbol}${convertedAmount.toFixed(2)}`;
    console.log(`✅ Результат: ${symbol}${convertedAmount.toFixed(2)}`);
}

// Получение символа валюты
function getCurrencySymbol(currency) {
    switch(currency) {
        case 'UAH': return '₴';
        case 'EUR': return '€';
        case 'USD': 
        case 'CAD': 
        case 'RUB': 
        default: return '$';
    }
}

// Обновление пары валют
function updateCurrencyPair(pairNumber) {
    const fromSelect = document.getElementById(`currency-from-${pairNumber}`);
    const toSelect = document.getElementById(`currency-to-${pairNumber}`);
    const rateElement = document.getElementById(`rate-${pairNumber}`);
    
    if (!fromSelect || !toSelect || !rateElement) {
        console.log(`Элементы для пары ${pairNumber} не найдены`);
        return;
    }
    
    const fromCurrency = fromSelect.value;
    const toCurrency = toSelect.value;
    
    console.log(`Обновляем пару ${pairNumber}: ${fromCurrency} -> ${toCurrency}`);
    
    if (fromCurrency === toCurrency) {
        rateElement.textContent = '1.0000';
        return;
    }
    
    // Проверяем наличие курсов валют
    if (!customRates[fromCurrency] || !customRates[toCurrency]) {
        console.log(`Курсы не найдены: ${fromCurrency}=${customRates[fromCurrency]}, ${toCurrency}=${customRates[toCurrency]}`);
        rateElement.textContent = 'N/A';
        return;
    }
    
    // Конвертируем: fromCurrency -> USD -> toCurrency
    const usdAmount = 1 / customRates[fromCurrency];
    const convertedAmount = usdAmount * customRates[toCurrency];
    
    if (isNaN(convertedAmount)) {
        console.log(`Ошибка конвертации для пары ${pairNumber}`);
        rateElement.textContent = 'N/A';
        return;
    }
    
    rateElement.textContent = convertedAmount.toFixed(4);
    console.log(`✅ Пара ${pairNumber}: ${convertedAmount.toFixed(4)}`);
}

// Инициализация конвертера при загрузке
document.addEventListener('DOMContentLoaded', function() {
    // Автоматически конвертируем при загрузке
    setTimeout(() => {
        console.log('🔄 Инициализируем конвертер...');
        convertCurrencyAmount();
    }, 2000);
});


// Load initial data
// loadDashboard(); // REMOVED - вызывается в DOMContentLoaded
// loadPlaidUsage(); // REMOVED - вызывается в loadDashboard()
// loadExchangeRates(); // REMOVED - вызывается в loadDashboard()
// loadAssets(); // REMOVED - вызывается в loadDashboard()
// loadBanksForManagement(); // REMOVED - вызывается в showTab('banks')

// Инициализация роутера ПОСЛЕ определения всех функций
const router = new URLRouter();
