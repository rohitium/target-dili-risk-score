// DILI Risk Score Checker - JavaScript

let riskData = [];
let chart = null;

// Load data when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadData();
    setupEventListeners();
});

function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');
    
    // Search on Enter key
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchTarget();
        }
    });
    
    // Autocomplete functionality
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        if (query.length >= 1) {
            showAutocomplete(query);
        } else {
            hideAutocomplete();
        }
    });
    
    // Hide autocomplete when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('#searchInput') && !e.target.closest('#autocompleteContainer')) {
            hideAutocomplete();
        }
    });
    
    // Handle keyboard navigation
    searchInput.addEventListener('keydown', function(e) {
        handleAutocompleteNavigation(e);
    });
}

async function loadData() {
    try {
        const response = await fetch('data.json');
        riskData = await response.json();
        console.log(`Loaded ${riskData.length} targets`);
    } catch (error) {
        console.error('Error loading data:', error);
        showError('Failed to load data. Please refresh the page.');
    }
}

function searchTarget() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim().toUpperCase();
    
    if (!query) {
        showError('Please enter a target symbol.');
        return;
    }
    
    // Find target in data
    const target = riskData.find(t => t.target_symbol.toUpperCase() === query);
    
    if (target) {
        displayResults(target);
    } else {
        showNotFound();
    }
}

function displayResults(target) {
    // Hide other sections
    document.getElementById('notFoundSection').style.display = 'none';
    
    // Show results section
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');
    
    // Update target info
    document.getElementById('targetSymbol').textContent = target.target_symbol;
    
    // Update risk category with appropriate styling
    const riskCategoryElement = document.getElementById('riskCategory');
    riskCategoryElement.textContent = target.risk_category;
    riskCategoryElement.className = 'badge fs-6';
    
    if (target.risk_category === 'High') {
        riskCategoryElement.classList.add('bg-danger');
    } else if (target.risk_category === 'Medium') {
        riskCategoryElement.classList.add('bg-warning');
    } else {
        riskCategoryElement.classList.add('bg-success');
    }
    
    // Update risk score
    const riskScore = (target.dili_risk_score * 100).toFixed(1);
    document.getElementById('riskScoreValue').textContent = riskScore + '%';
    
    // Update progress bar
    const progressBar = document.getElementById('riskScoreBar');
    progressBar.style.width = riskScore + '%';
    
    // Set progress bar color based on risk
    progressBar.className = 'progress-bar';
    if (target.risk_category === 'High') {
        progressBar.classList.add('bg-danger');
    } else if (target.risk_category === 'Medium') {
        progressBar.classList.add('bg-warning');
    } else {
        progressBar.classList.add('bg-success');
    }
    
    // Update detailed metrics
    document.getElementById('drugCount').textContent = target.drug_count.toLocaleString();
    document.getElementById('highRiskDrugs').textContent = target.high_risk_drug_count.toLocaleString();
    document.getElementById('diliRiskRatio').textContent = (target.dili_risk_ratio * 100).toFixed(1) + '%';
    document.getElementById('networkScore').textContent = target.network_dili_score.toFixed(2);
    
    // Create chart
    createRiskChart();
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function showNotFound() {
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('notFoundSection').style.display = 'block';
    document.getElementById('notFoundSection').classList.add('fade-in');
}

function showError(message) {
    // Create a simple alert for now
    alert(message);
}

function createRiskChart() {
    const ctx = document.getElementById('riskChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (chart) {
        chart.destroy();
    }
    
    // Calculate risk distribution
    const riskCounts = {
        'Low': riskData.filter(t => t.risk_category === 'Low').length,
        'Medium': riskData.filter(t => t.risk_category === 'Medium').length,
        'High': riskData.filter(t => t.risk_category === 'High').length
    };
    
    chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Low Risk', 'Medium Risk', 'High Risk'],
            datasets: [{
                data: [riskCounts.Low, riskCounts.Medium, riskCounts.High],
                backgroundColor: [
                    '#27ae60',  // Green for low risk
                    '#f39c12',  // Orange for medium risk
                    '#e74c3c'   // Red for high risk
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        font: {
                            size: 14
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true
            }
        }
    });
}

// Autocomplete functionality
let currentAutocompleteIndex = -1;
let filteredTargets = [];

function showAutocomplete(query) {
    const container = document.getElementById('autocompleteContainer');
    const list = document.getElementById('autocompleteList');
    
    // Filter targets based on query
    filteredTargets = riskData.filter(target => 
        target.target_symbol.toLowerCase().includes(query.toLowerCase())
    ).slice(0, 10); // Limit to 10 results
    
    if (filteredTargets.length === 0) {
        hideAutocomplete();
        return;
    }
    
    // Clear and populate list
    list.innerHTML = '';
    
    filteredTargets.forEach((target, index) => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.dataset.index = index;
        
        const riskClass = target.risk_category.toLowerCase();
        
        item.innerHTML = `
            <span class="target-symbol">${target.target_symbol}</span>
            <span class="risk-category ${riskClass}">${target.risk_category}</span>
        `;
        
        item.addEventListener('click', function() {
            selectAutocompleteItem(index);
        });
        
        list.appendChild(item);
    });
    
    container.style.display = 'block';
    currentAutocompleteIndex = -1;
}

function hideAutocomplete() {
    const container = document.getElementById('autocompleteContainer');
    container.style.display = 'none';
    currentAutocompleteIndex = -1;
}

function selectAutocompleteItem(index) {
    if (index >= 0 && index < filteredTargets.length) {
        const target = filteredTargets[index];
        document.getElementById('searchInput').value = target.target_symbol;
        hideAutocomplete();
        searchTarget();
    }
}

function handleAutocompleteNavigation(e) {
    const container = document.getElementById('autocompleteContainer');
    const items = container.querySelectorAll('.autocomplete-item');
    
    if (container.style.display === 'none') return;
    
    switch(e.key) {
        case 'ArrowDown':
            e.preventDefault();
            currentAutocompleteIndex = Math.min(currentAutocompleteIndex + 1, items.length - 1);
            updateAutocompleteSelection();
            break;
        case 'ArrowUp':
            e.preventDefault();
            currentAutocompleteIndex = Math.max(currentAutocompleteIndex - 1, -1);
            updateAutocompleteSelection();
            break;
        case 'Enter':
            if (currentAutocompleteIndex >= 0) {
                e.preventDefault();
                selectAutocompleteItem(currentAutocompleteIndex);
            }
            break;
        case 'Escape':
            hideAutocomplete();
            break;
    }
}

function updateAutocompleteSelection() {
    const items = document.querySelectorAll('.autocomplete-item');
    
    items.forEach((item, index) => {
        if (index === currentAutocompleteIndex) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });
}

// Add some sample targets for quick testing
function addSampleTargets() {
    const sampleTargets = ['CYP3A4', 'ACE', 'ACHE', 'ADORA1', 'ADRA1A'];
    const searchInput = document.getElementById('searchInput');
    
    // Add click handlers for sample targets
    const sampleContainer = document.createElement('div');
    sampleContainer.className = 'text-center mt-3';
    sampleContainer.innerHTML = '<small class="text-muted">Quick search: </small>';
    
    sampleTargets.forEach(target => {
        const link = document.createElement('a');
        link.href = '#';
        link.className = 'badge bg-light text-dark me-2';
        link.textContent = target;
        link.onclick = function(e) {
            e.preventDefault();
            searchInput.value = target;
            hideAutocomplete(); // Hide autocomplete when using quick search
            searchTarget();
        };
        sampleContainer.appendChild(link);
    });
    
    // Insert after the search input
    const searchSection = document.querySelector('.input-group');
    searchSection.parentNode.insertBefore(sampleContainer, searchSection.nextSibling);
}

// Initialize sample targets
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(addSampleTargets, 1000);
}); 