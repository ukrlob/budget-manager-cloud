const API_BASE = 'http://127.0.0.1:8004';

// Глобальные курсы валют (настраиваемые)
let customRates = {
    'USD': 1,     // USD к USD (базовая валюта)
    'CAD': 1.35,  // CAD к USD
    'EUR': 0.85,  // EUR к USD
    'UAH': 41.0,  // UAH к USD
    'RUB': 83.0   // RUB к USD
};

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Plaid page loaded, initializing...');
    
    // Initialize Plaid page
    loadPlaidUsage();
    loadExchangeRates();
    loadBanksForManagement();
});

// API call helper
async function apiCall(endpoint, options = {}) {
    console.log(`Making API call to: ${API_BASE}${endpoint}`);
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        console.log(`Response status: ${response.status}`);
        console.log(`Response headers:`, response.headers);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const contentType = response.headers.get('content-type');
        console.log(`Content-Type: ${contentType}`);
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            console.log('API response:', data);
            return data;
        } else {
            const text = await response.text();
            console.log('API response (text):', text);
            return text;
        }
    } catch (error) {
        console.error(`API call failed: ${endpoint}`, error);
        throw error;
    }
}

// Load Plaid usage counter
async function loadPlaidUsage() {
    console.log('🔄 Загружаем счетчик Plaid API...');
    
    try {
        const data = await apiCall('/api/banks/plaid/usage');
        console.log('📊 Данные счетчика Plaid из кэша:', data);
        
        // Используем данные из кэша (автоматические запросы отключены)
        console.log('✅ Используем данные из кэша (автоматические запросы отключены):', data);
        updatePlaidCounter(data);
        
    } catch (error) {
        console.error('❌ Ошибка загрузки счетчика Plaid:', error);
    }
}

// Update Plaid counter UI
function updatePlaidCounter(data) {
    const usedElement = document.getElementById('plaid-used');
    const limitElement = document.getElementById('plaid-limit');
    const counterElement = document.getElementById('plaidCounter');
    
    if (usedElement) {
        usedElement.textContent = data.used || 0;
    } else {
        console.log('❌ Элемент plaid-used не найден!');
    }
    
    if (limitElement) {
        limitElement.textContent = data.limit || 100;
    } else {
        console.log('❌ Элемент plaid-limit не найден!');
    }
    
    if (counterElement) {
        counterElement.textContent = `${data.used || 0}/${data.limit || 100}`;
    }
}

// Refresh Plaid counter
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
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Plaid API обновлен:', data);
        
        // Обновляем счетчик
        await loadPlaidUsage();
        
    } catch (error) {
        console.error('❌ Ошибка обновления Plaid API:', error);
        alert('Ошибка обновления Plaid API: ' + error.message);
    } finally {
        // Восстанавливаем кнопку
        button.textContent = 'Обновить';
        button.disabled = false;
    }
}

// Load exchange rates
async function loadExchangeRates() {
    console.log('🚀 НАЧИНАЕМ ЗАГРУЗКУ КУРСОВ ВАЛЮТ');
    
    try {
        console.log('🔄 Загружаем курсы валют с API: https://api.exchangerate-api.com/v4/latest/USD');
        
        const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📊 Курсы валют получены:', data);
        
        // Обновляем глобальные курсы
        console.log('🔍 Проверяем нужные валюты:');
        console.log('CAD:', data.rates.CAD);
        console.log('EUR:', data.rates.EUR);
        console.log('UAH:', data.rates.UAH);
        console.log('RUB:', data.rates.RUB);
        
        // Устанавливаем USD как базовую валюту
        customRates.USD = 1;
        console.log('✅ USD установлен:', customRates.USD);
        
        // Обновляем курсы
        if (data.rates.CAD) {
            customRates.CAD = data.rates.CAD;
            console.log('✅ CAD обновлен:', customRates.CAD);
        }
        if (data.rates.EUR) {
            customRates.EUR = data.rates.EUR;
            console.log('✅ EUR обновлен:', customRates.EUR);
        }
        if (data.rates.UAH) {
            customRates.UAH = data.rates.UAH;
            console.log('✅ UAH обновлен:', customRates.UAH);
        }
        if (data.rates.RUB) {
            customRates.RUB = data.rates.RUB;
            console.log('✅ RUB обновлен:', customRates.RUB);
        }
        
        console.log('✅ ВСЕ КУРСЫ ОБНОВЛЕНЫ:', customRates);
        
        // Обновляем UI
        console.log('🔄 Обновляем UI...');
        updateRatesUI();
        console.log('✅ UI обновлен');
        
    } catch (error) {
        console.error('❌ Ошибка загрузки курсов валют:', error);
    }
}

// Update rates UI
function updateRatesUI() {
    for (let i = 1; i <= 4; i++) {
        updateCurrencyPair(i);
    }
}

// Update currency pair
function updateCurrencyPair(pairNumber) {
    const fromSelect = document.getElementById(`from${pairNumber}`);
    const toSelect = document.getElementById(`to${pairNumber}`);
    const rateElement = document.getElementById(`rate${pairNumber}`);
    
    if (!fromSelect || !toSelect || !rateElement) {
        console.log(`Элементы для пары ${pairNumber} не найдены`);
        return;
    }
    
    const fromCurrency = fromSelect.value;
    const toCurrency = toSelect.value;
    
    if (customRates[fromCurrency] && customRates[toCurrency]) {
        const rate = customRates[toCurrency] / customRates[fromCurrency];
        rateElement.textContent = rate.toFixed(4);
    } else {
        rateElement.textContent = 'N/A';
    }
}

// Refresh exchange rates
function refreshExchangeRates() {
    loadExchangeRates();
}

// Load banks for management
async function loadBanksForManagement() {
    console.log('🏦 Начинаем загрузку банков для управления...');
    
    try {
        console.log('📡 Запрашиваем статус банков с http://127.0.0.1:8004/api/banks/status');
        const statusData = await apiCall('/api/banks/status');
        console.log('📡 Ответ получен:', statusData.status);
        console.log('📊 Данные статуса банков:', statusData.data);
        
        const banksGrid = document.getElementById('banksGrid');
        if (!banksGrid) {
            console.error('❌ Контейнер banksGrid не найден!');
            return;
        }
        
        if (!statusData.data || statusData.data.length === 0) {
            banksGrid.innerHTML = '<div class="no-banks">Нет подключенных банков</div>';
            return;
        }
        
        let banksHTML = '';
        
        for (const bank of statusData.data) {
            console.log(`Загружаем данные для банка: ${bank.name} (${bank.code})`);
            
            // Используем тестовые данные для демонстрации
            let accountsData = null;
            
            if (bank.code === 'RBC') {
                console.log('📊 Используем тестовые данные для Royal Bank of Canada (RBC)');
                accountsData = {
                    value: [
                        { name: 'RBC Advantage Banking', balance: 119.14, currency: 'CAD' },
                        { name: 'RBC ION Visa', balance: -58.11, currency: 'CAD' },
                        { name: 'RBC U.S. High Interest eSavings', balance: 100.82, currency: 'USD' },
                        { name: 'RBC High Interest eSavings', balance: 2000, currency: 'CAD' },
                        { name: 'RBC Advantage Banking', balance: 1403.6, currency: 'CAD' }
                    ]
                };
                console.log('✅ Тестовые данные:', accountsData.value.length, 'счетов для Royal Bank of Canada');
            } else if (bank.code === 'BMO') {
                console.log('📊 Используем тестовые данные для Bank of Montreal (BMO)');
                accountsData = {
                    value: [
                        { name: 'MasterCard', balance: 7500.02, currency: 'CAD' },
                        { name: 'Chequing', balance: 100, currency: 'CAD' }
                    ]
                };
                console.log('✅ Тестовые данные:', accountsData.value.length, 'счетов для Bank of Montreal');
            } else if (bank.code === 'WALMART') {
                console.log('📊 Используем тестовые данные для Walmart Rewards (WALMART)');
                accountsData = {
                    value: [
                        { name: 'World Mastercard', balance: 2000, currency: 'CAD' }
                    ]
                };
                console.log('✅ Тестовые данные:', accountsData.value.length, 'счетов для Walmart Rewards');
            } else {
                console.log('❌ Нет тестовых данных для', bank.name);
                accountsData = { value: [] };
            }
            
            // Подсчитываем общий баланс
            let totalBalance = 0;
            if (accountsData && accountsData.value) {
                totalBalance = accountsData.value.reduce((sum, account) => sum + (account.balance || 0), 0);
            }
            console.log('💵 Общий баланс', bank.name + ':', totalBalance);
            
            // Определяем статус банка
            const statusClass = bank.status === 'active' ? 'working' : 'error';
            const statusText = bank.status === 'active' ? 'Работает' : 'Ошибка';
            const accountCount = accountsData ? accountsData.value.length : 0;
            const lastTransaction = bank.last_transaction || 'Нет';
            
            // Генерируем HTML для счетов
            let accountsHTML = '';
            if (accountsData && accountsData.value && accountsData.value.length > 0) {
                accountsHTML = '<div class="accounts-list">';
                accountsData.value.forEach(account => {
                    accountsHTML += `
                        <div class="account-item">
                            <div class="account-name">${account.name}</div>
                            <div class="account-balance">${account.balance.toFixed(2)} ${account.currency}</div>
                        </div>
                    `;
                });
                accountsHTML += '</div>';
            }
            
            banksHTML += `
                <div class="bank-card">
                    <div class="bank-header">
                        <h3>${bank.name}</h3>
                        <div class="bank-status ${statusClass}">${statusText}</div>
                    </div>
                    <div class="bank-info">
                        <div class="bank-stats">
                            <span>Счетов: ${accountCount}</span>
                            <span>Последняя транзакция: ${lastTransaction}</span>
                        </div>
                        ${accountsHTML}
                    </div>
                    <div class="bank-actions">
                        <button class="btn btn-secondary" onclick="refreshBank('${bank.code}')">Обновить</button>
                        <button class="btn btn-secondary" onclick="viewAccounts('${bank.code}')">Счета</button>
                        <button class="btn btn-secondary" onclick="viewTransactions('${bank.code}')">Транзакции</button>
                    </div>
                </div>
            `;
        }
        
        banksGrid.innerHTML = banksHTML;
        
    } catch (error) {
        console.error('❌ Ошибка загрузки банков:', error);
        const banksGrid = document.getElementById('banksGrid');
        if (banksGrid) {
            banksGrid.innerHTML = '<div class="error">Ошибка загрузки банков</div>';
        }
    }
}

// Currency converter functions
function convertCurrencyAmount() {
    const fromCurrency = document.getElementById('fromCurrency');
    const toCurrency = document.getElementById('toCurrency');
    const amountInput = document.getElementById('amountInput');
    const resultElement = document.getElementById('converterResult');
    
    if (!fromCurrency || !toCurrency || !amountInput || !resultElement) {
        console.log('Элементы конвертера не найдены');
        return;
    }
    
    const amount = parseFloat(amountInput.value) || 0;
    const from = fromCurrency.value;
    const to = toCurrency.value;
    
    if (from === to) {
        resultElement.textContent = `$${amount.toFixed(2)}`;
        return;
    }
    
    if (customRates[from] && customRates[to]) {
        const convertedAmount = (amount * customRates[to]) / customRates[from];
        resultElement.textContent = `$${convertedAmount.toFixed(2)}`;
    } else {
        resultElement.textContent = 'Курс не найден';
    }
}

// Bank management functions
function refreshBank(bankCode) {
    console.log(`Обновление банка ${bankCode}`);
    // Здесь будет логика обновления банка
}

function viewAccounts(bankCode) {
    console.log(`Просмотр счетов банка ${bankCode}`);
    // Здесь будет логика просмотра счетов
}

function viewTransactions(bankCode) {
    console.log(`Просмотр транзакций банка ${bankCode}`);
    // Здесь будет логика просмотра транзакций
}

// Plaid Link function
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

