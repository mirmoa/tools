// 전역 변수
let hourlyChart = null;

// 사이드바 토글
document.addEventListener('DOMContentLoaded', function() {
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');

    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            mainContent.classList.toggle('active');
        });
    }

    // 데이터 로드
    loadCoupangAdsData();
});

// 숫자 포맷팅 함수
function formatNumber(num) {
    return new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: 'KRW'
    }).format(num);
}

// 날짜 포맷팅 함수
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// 차트 초기화
function initializeChart(labels, data) {
    const ctx = document.getElementById('hourlyChart').getContext('2d');
    
    if (hourlyChart) {
        hourlyChart.destroy();
    }

    hourlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '시간별 비용',
                data: data,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatNumber(context.parsed.y);
                        }
                    }
                }
            }
        }
    });
}

// 테이블 업데이트
function updateTable(campaigns) {
    const tbody = document.querySelector('#campaignTable tbody');
    tbody.innerHTML = '';

    Object.entries(campaigns).forEach(([name, data]) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${name}</td>
            <td>${formatNumber(data.total_cost)}</td>
            <td>${data.hours_collected.length}</td>
            <td>${formatDate(data.last_updated)}</td>
        `;
        tbody.appendChild(row);
    });
}

// 데이터 로드 및 표시
async function loadData() {
    try {
        // 오늘 날짜의 데이터 파일 경로
        const today = new Date().toISOString().split('T')[0];
        const response = await fetch(`/data/daily/${today}.json`);
        
        if (!response.ok) {
            throw new Error('데이터를 불러올 수 없습니다.');
        }

        const data = await response.json();

        // 마지막 업데이트 시간 표시
        document.getElementById('lastUpdated').textContent = 
            `마지막 업데이트: ${formatDate(data.last_updated)}`;

        // 총계 표시
        document.getElementById('totalCost').textContent = 
            formatNumber(data.total_cost);
        document.getElementById('campaignCount').textContent = 
            Object.keys(data.campaign_summary).length;

        // 시간별 차트 데이터 준비
        const hours = Object.keys(data.hours).sort();
        const hourlyData = hours.map(hour => data.hours[hour].total_cost);

        // 차트 업데이트
        initializeChart(hours, hourlyData);

        // 캠페인 테이블 업데이트
        updateTable(data.campaign_summary);

    } catch (error) {
        console.error('데이터 로드 중 오류:', error);
        alert('데이터를 불러오는 중 오류가 발생했습니다.');
    }
}

// 페이지 로드 시 데이터 로드
document.addEventListener('DOMContentLoaded', loadData);

// 5분마다 데이터 새로고침
setInterval(loadData, 5 * 60 * 1000);

// 쿠팡 광고 데이터 로드
async function loadCoupangAdsData() {
    try {
        // 오늘 날짜의 데이터 파일 경로
        const today = new Date().toISOString().split('T')[0];
        const response = await fetch(`/data/daily/${today}.json`);
        
        if (!response.ok) {
            throw new Error('데이터를 불러올 수 없습니다.');
        }

        const data = await response.json();

        // 마지막 업데이트 시간 표시
        document.getElementById('lastUpdated').textContent = 
            `마지막 업데이트: ${formatDate(data.last_updated)}`;

        // 요약 정보 업데이트
        document.getElementById('totalCost').textContent = 
            formatNumber(data.total_cost);
        document.getElementById('campaignCount').textContent = 
            Object.keys(data.campaign_summary).length;

        // 시간별 차트 업데이트
        updateHourlyChart(data.hourly_data);

        // 캠페인 테이블 업데이트
        updateCampaignTable(data.campaign_summary);

    } catch (error) {
        console.error('데이터 로드 중 오류:', error);
    }
}

// 시간별 차트 업데이트
function updateHourlyChart(hourlyData) {
    const ctx = document.getElementById('hourlyChart').getContext('2d');
    
    // 기존 차트가 있다면 제거
    if (window.hourlyChart) {
        window.hourlyChart.destroy();
    }

    const hours = Object.keys(hourlyData);
    const costs = Object.values(hourlyData);

    window.hourlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours,
            datasets: [{
                label: '시간별 광고 비용',
                data: costs,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    }
                }
            }
        }
    });
}

// 캠페인 테이블 업데이트
function updateCampaignTable(campaignData) {
    const tbody = document.getElementById('campaignTable').querySelector('tbody');
    if (!tbody) return;

    tbody.innerHTML = Object.entries(campaignData)
        .map(([name, data]) => `
            <tr>
                <td>${name}</td>
                <td>${formatNumber(data.total_cost)}</td>
                <td>${data.data_points}</td>
                <td>${formatDate(data.last_updated)}</td>
            </tr>
        `).join('');
}

// 5분마다 데이터 새로고침
setInterval(loadCoupangAdsData, 5 * 60 * 1000); 