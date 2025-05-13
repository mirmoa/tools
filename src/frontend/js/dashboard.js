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

    // 현재 시간 표시
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);

    // 데이터 로드
    loadDashboardData();
});

// 현재 시간 업데이트
function updateCurrentTime() {
    const currentTime = document.getElementById('currentTime');
    if (currentTime) {
        currentTime.textContent = new Date().toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
}

// 숫자 포맷팅
function formatNumber(num) {
    return new Intl.NumberFormat('ko-KR', {
        style: 'currency',
        currency: 'KRW'
    }).format(num);
}

// 날짜 포맷팅
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

// 캠페인별 최대 비용 계산 함수 추가
function calculateMaxCost(campaignData) {
    if (!campaignData) return {};
    
    const maxCosts = {};
    Object.entries(campaignData).forEach(([name, data]) => {
        if (data && data.hourly_costs) {
            const costs = Object.values(data.hourly_costs);
            maxCosts[name] = costs.length > 0 ? Math.max(...costs) : 0;
        } else {
            maxCosts[name] = 0;
        }
    });
    return maxCosts;
}

// 총 비용 계산 함수 추가
function calculateTotalCost(maxCosts) {
    if (!maxCosts || Object.keys(maxCosts).length === 0) return 0;
    
    return Object.values(maxCosts)
        .filter(cost => !isNaN(cost))
        .reduce((sum, cost) => sum + (cost || 0), 0);
}

// 대시보드 데이터 로드
async function loadDashboardData() {
    try {
        const today = new Date().toISOString().split('T')[0];
        const response = await fetch(`/data/daily/${today}.json`);
        
        if (!response.ok) {
            throw new Error('데이터를 불러올 수 없습니다.');
        }

        const data = await response.json();
        
        // 총 비용 계산
        const maxCosts = calculateMaxCost(data.campaign_summary);
        const totalCost = calculateTotalCost(maxCosts);

        // 쿠팡 광고 데이터 업데이트
        document.getElementById('coupangTodayCost').textContent = 
            formatNumber(totalCost);
        document.getElementById('coupangActiveCampaigns').textContent = 
            Object.keys(data.campaign_summary).length;

        // 시스템 상태 테이블 업데이트
        updateSystemStatus(data);

    } catch (error) {
        console.error('데이터 로드 중 오류:', error);
    }
}

// 시스템 상태 테이블 업데이트
function updateSystemStatus(data) {
    const tbody = document.getElementById('systemStatus');
    if (!tbody) return;

    const now = new Date();
    const nextHour = new Date(now);
    nextHour.setHours(nextHour.getHours() + 1);
    nextHour.setMinutes(0);
    nextHour.setSeconds(0);

    const services = [
        {
            name: '쿠팡 광고',
            status: data.last_updated ? '정상' : '오류',
            lastUpdate: data.last_updated || '-',
            nextRun: nextHour.toLocaleString('ko-KR', {
                hour: '2-digit',
                minute: '2-digit'
            })
        },
        {
            name: '스마트스토어',
            status: '준비중',
            lastUpdate: '-',
            nextRun: '-'
        },
        {
            name: '매출 분석',
            status: '준비중',
            lastUpdate: '-',
            nextRun: '-'
        }
    ];

    tbody.innerHTML = services.map(service => `
        <tr>
            <td>${service.name}</td>
            <td>
                <span class="badge ${service.status === '정상' ? 'bg-success' : 
                                   service.status === '오류' ? 'bg-danger' : 
                                   'bg-secondary'}">
                    ${service.status}
                </span>
            </td>
            <td>${service.lastUpdate !== '-' ? formatDate(service.lastUpdate) : '-'}</td>
            <td>${service.nextRun}</td>
        </tr>
    `).join('');
}

// 5분마다 데이터 새로고침
setInterval(loadDashboardData, 5 * 60 * 1000);