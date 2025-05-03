// 전역 변수
let hourlyChart = null;
let lastUpdateTime = null;  // 마지막 업데이트 시간 저장
let lastData = {  // 각 컴포넌트의 마지막 데이터 저장
    summary: null,
    hourly: null,
    campaigns: null
};

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

// 요약 정보 업데이트
function updateSummary(data) {
    const summaryData = {
        total_cost: data.total_cost,
        campaign_count: Object.keys(data.campaign_summary).length,
        last_updated: data.last_updated
    };
    
    // 변경사항이 있는 경우에만 업데이트
    if (JSON.stringify(lastData.summary) !== JSON.stringify(summaryData)) {
        document.getElementById('lastUpdated').textContent = 
            `마지막 업데이트: ${formatDate(data.last_updated)}`;
        document.getElementById('totalCost').textContent = 
            formatNumber(data.total_cost);
        document.getElementById('campaignCount').textContent = 
            Object.keys(data.campaign_summary).length;
            
        lastData.summary = summaryData;
    }
}

// 시간별 차트 업데이트
function updateHourlyChart(hourlyData) {
    // 변경사항이 있는 경우에만 업데이트
    if (JSON.stringify(lastData.hourly) !== JSON.stringify(hourlyData)) {
        const hours = Object.keys(hourlyData).sort();
        const costs = hours.map(hour => hourlyData[hour]);
        initializeChart(hours, costs);
        
        lastData.hourly = hourlyData;
    }
}

// 캠페인 테이블 업데이트
function updateCampaignTable(campaignData) {
    // 변경사항이 있는 경우에만 업데이트
    if (JSON.stringify(lastData.campaigns) !== JSON.stringify(campaignData)) {
        const tbody = document.getElementById('campaignTable').querySelector('tbody');
        if (!tbody) return;

        tbody.innerHTML = Object.entries(campaignData)
            .map(([name, data]) => {
                // 시간별 데이터가 있는 경우 해당 시간의 데이터 포인트 수를 표시
                const dataPoints = data.hourly_costs ? 
                    Object.keys(data.hourly_costs).length : 
                    1;  // 기본값
                    
                return `
                    <tr>
                        <td>${name}</td>
                        <td>${formatNumber(data.total_cost)}</td>
                        <td>${dataPoints}</td>
                        <td>${formatDate(data.last_updated)}</td>
                    </tr>
                `;
            }).join('');
            
        lastData.campaigns = campaignData;
    }
}

// 데이터 로드 및 표시
async function loadData() {
    try {
        const today = new Date().toISOString().split('T')[0];
        const response = await fetch(`/data/daily/${today}.json`);
        
        if (!response.ok) {
            throw new Error('데이터를 불러올 수 없습니다.');
        }

        const data = await response.json();
        
        // 새로운 데이터가 있는지 확인
        if (lastUpdateTime && lastUpdateTime >= new Date(data.last_updated)) {
            return; // 새로운 데이터가 없으면 업데이트하지 않음
        }
        
        // 마지막 업데이트 시간 저장
        lastUpdateTime = new Date(data.last_updated);

        // 각 컴포넌트 개별적으로 업데이트
        updateSummary(data);
        updateHourlyChart(data.hourly_data);
        updateCampaignTable(data.campaign_summary);

    } catch (error) {
        console.error('데이터 로드 중 오류:', error);
    }
}

// 사이드바 토글 설정
function setupSidebar() {
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');

    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            mainContent.classList.toggle('active');
        });
    }
}

// 페이지 초기화
document.addEventListener('DOMContentLoaded', () => {
    setupSidebar();  // 사이드바 설정
    loadData();      // 초기 데이터 로드
    
    // 5분마다 새로운 데이터 확인
    setInterval(loadData, 5 * 60 * 1000);
}); 