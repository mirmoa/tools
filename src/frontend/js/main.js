// 전역 변수
let hourlyChart = null;
let dailyDetailChart = null;
let lastUpdateTime = null;  // 마지막 업데이트 시간 저장
let lastData = {  // 각 컴포넌트의 마지막 데이터 저장
    summary: null,
    hourly: null,
    campaigns: null,
    weekly: null
};
let weeklyData = [];  // 주간 데이터 저장
let currentView = 'today'; // 기본값은 오늘

// 날짜 관련 상수
const DAY_NAMES = ['일', '월', '화', '수', '목', '금', '토'];

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

// 간단한 날짜 포맷팅 함수 (YYYY-MM-DD)
function formatSimpleDate(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

// 한국식 날짜 표시 (YYYY년 MM월 DD일 (요일))
function formatKoreanDate(date) {
    return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일 (${DAY_NAMES[date.getDay()]})`;
}

// 차트 초기화 함수 수정
function initializeChart(data) {
    const ctx = document.getElementById('hourlyChart').getContext('2d');
    
    if (hourlyChart) {
        hourlyChart.destroy();
    }

    // 색상 팔레트 정의
    const colors = [
        'rgb(75, 192, 192)',
        'rgb(255, 99, 132)',
        'rgb(255, 205, 86)',
        'rgb(54, 162, 235)',
        'rgb(153, 102, 255)',
        'rgb(255, 159, 64)',
        'rgb(201, 203, 207)'
    ];

    let datasets = [];
    
    if (currentView === 'today') {
        // 오늘 데이터만 표시
        datasets = [{
            label: '오늘',
            data: Object.values(data[0]?.hourly_data || Array(24).fill(0)),
            borderColor: colors[0],
            tension: 0.1,
            fill: false
        }];
    } else {
        // 주간 데이터 표시
        datasets = (data || [])
            .sort((a, b) => new Date(b.date) - new Date(a.date))
            .map((dayData, index) => ({
                label: new Date(dayData.date).toLocaleDateString('ko-KR', {
                    month: 'short',
                    day: 'numeric',
                    weekday: 'short'
                }),
                data: Object.values(dayData.hourly_data || Array(24).fill(0)),
                borderColor: colors[index],
                tension: 0.1,
                fill: false
            }));
    }

    hourlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: 24}, (_, i) => `${String(i).padStart(2, '0')}시`),
            datasets: datasets
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
                            return `${context.dataset.label}: ${formatNumber(context.parsed.y)}`;
                        }
                    }
                },
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                }
            }
        }
    });
}

// 캠페인별 최대 비용 계산 함수
function calculateMaxCost(campaignData) {
    // 각 캠페인별 최대 비용 계산
    const maxCosts = {};
    
    Object.entries(campaignData).forEach(([name, data]) => {
        if (data.hourly_costs) {
            // 해당 캠페인의 시간별 비용 중 최대값 찾기
            const costs = Object.values(data.hourly_costs);
            maxCosts[name] = Math.max(...costs);
        } else {
            maxCosts[name] = 0;
        }
    });
    
    return maxCosts;
}

// 총 비용 계산 함수
function calculateTotalCost(maxCosts) {
    // 모든 캠페인의 최대 비용 합산
    return Object.values(maxCosts).reduce((sum, cost) => sum + cost, 0);
}

// 피크 시간대 찾기 함수
function findPeakHour(hourlyData) {
    let peakHour = '00';
    let maxCost = 0;
    
    Object.entries(hourlyData).forEach(([hour, cost]) => {
        if (cost > maxCost) {
            maxCost = cost;
            peakHour = hour;
        }
    });
    
    return `${peakHour}시`;
}

// 요약 정보 업데이트
function updateSummary(data) {
    // 각 캠페인별 최대 비용 계산
    const maxCosts = calculateMaxCost(data.campaign_summary);
    
    // 총 비용 계산 (각 캠페인의 최대 비용 합산)
    const totalCost = calculateTotalCost(maxCosts);
    
    const summaryData = {
        total_cost: totalCost,
        campaign_count: Object.keys(data.campaign_summary).length,
        last_updated: data.last_updated
    };
    
    // 변경사항이 있는 경우에만 업데이트
    if (JSON.stringify(lastData.summary) !== JSON.stringify(summaryData)) {
        document.getElementById('lastUpdated').textContent = 
            `마지막 업데이트: ${formatDate(data.last_updated)}`;
        document.getElementById('totalCost').textContent = 
            formatNumber(totalCost);
        document.getElementById('campaignCount').textContent = 
            Object.keys(data.campaign_summary).length;
            
        lastData.summary = summaryData;
    }
}

// 차트 업데이트 함수 수정
function updateHourlyChart() {
    if (!weeklyData || weeklyData.length === 0) {
        // 데이터가 없는 경우 빈 차트 표시
        initializeChart([]);
        return;
    }

    initializeChart(weeklyData);
    lastData.weekly = [...weeklyData];
}

// 캠페인 테이블 업데이트
function updateCampaignTable(campaigns) {
    const tbody = document.getElementById('campaignTable').querySelector('tbody');
    if (!tbody) return;

    tbody.innerHTML = campaigns.map(campaign => `
        <tr>
            <td>${campaign.name}</td>
            <td>${formatNumber(campaign.total_cost)}</td>
            <td>${formatDate(campaign.last_updated)}</td>
        </tr>
    `).join('');
}

// 주간 데이터 테이블 업데이트
function updateWeeklyTable() {
    const tbody = document.getElementById('weeklyTable').querySelector('tbody');
    if (!tbody) return;
    
    // 변경사항이 있는 경우에만 업데이트
    if (JSON.stringify(lastData.weekly) !== JSON.stringify(weeklyData)) {
        tbody.innerHTML = weeklyData
            .sort((a, b) => new Date(b.date) - new Date(a.date))  // 최신 날짜가 위로 오도록 정렬
            .map(dayData => {
                const date = new Date(dayData.date);
                const koreanDate = formatKoreanDate(date);
                const totalCost = dayData.total_cost;
                const campaignCount = dayData.campaign_count;
                const peakHour = findPeakHour(dayData.hourly_data);
                
                return `
                    <tr>
                        <td>${koreanDate}</td>
                        <td>${formatNumber(totalCost)}</td>
                        <td>${campaignCount}</td>
                        <td>${peakHour}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-info view-detail-btn" 
                                    data-date="${dayData.date}">
                                상세 보기
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
            
        // 상세 보기 버튼에 이벤트 리스너 추가
        document.querySelectorAll('.view-detail-btn').forEach(button => {
            button.addEventListener('click', function() {
                const date = this.getAttribute('data-date');
                showDayDetail(date);
            });
        });
        
        lastData.weekly = [...weeklyData];
    }
}

// 일별 세부 정보 모달 표시
function showDayDetail(date) {
    // 날짜에 해당하는 데이터 찾기
    const dayData = weeklyData.find(data => data.date === date);
    if (!dayData) return;
    
    // 모달 제목 설정
    const modalDate = new Date(date);
    document.getElementById('dayDetailModalLabel').textContent = 
        `${formatKoreanDate(modalDate)} 상세 정보`;
    
    // 시간별 차트 초기화
    initializeDailyDetailChart(formatKoreanDate(modalDate), dayData.hourly_data);
    
    // 캠페인별 비용 테이블 업데이트
    const campaignTable = document.getElementById('dailyCampaignTable').querySelector('tbody');
    if (campaignTable) {
        // 각 캠페인별 최대 비용 계산
        const maxCosts = calculateMaxCost(dayData.campaign_summary);
        const totalCost = calculateTotalCost(maxCosts);
        
        // 비용 기준 내림차순 정렬
        const sortedCampaigns = Object.entries(maxCosts)
            .sort((a, b) => b[1] - a[1]);
        
        campaignTable.innerHTML = sortedCampaigns
            .map(([name, cost]) => {
                const percentage = totalCost > 0 ? 
                    ((cost / totalCost) * 100).toFixed(1) : 0;
                
                return `
                    <tr>
                        <td>${name}</td>
                        <td>${formatNumber(cost)}</td>
                        <td>${percentage}%</td>
                    </tr>
                `;
            }).join('');
    }
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('dayDetailModal'));
    modal.show();
}

// 주간 데이터 로드
async function loadWeeklyData() {
    try {
        // 오늘 날짜
        const today = new Date();
        
        // 최근 7일 날짜 계산
        const dates = [];
        for (let i = 6; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(today.getDate() - i);
            dates.push(formatSimpleDate(date));
        }
        
        // 각 날짜별 데이터 로드
        const dataPromises = dates.map(async (date) => {
            try {
                const response = await fetch(`/data/daily/${date}.json`);
                if (!response.ok) {
                    return null;  // 파일이 없으면 null 반환
                }
                const data = await response.json();
                
                // 각 캠페인별 최대 비용 계산
                const maxCosts = calculateMaxCost(data.campaign_summary);
                
                // 총 비용 계산 (각 캠페인의 최대 비용 합산)
                const totalCost = calculateTotalCost(maxCosts);
                
                return {
                    date: date,
                    total_cost: totalCost,
                    campaign_count: Object.keys(data.campaign_summary).length,
                    hourly_data: data.hourly_data,
                    campaign_summary: data.campaign_summary
                };
            } catch (error) {
                return null;  // 오류 발생 시 null 반환
            }
        });
        
        // 모든 데이터 가져오기
        const results = await Promise.all(dataPromises);
        
        // null이 아닌 데이터만 필터링
        weeklyData = results.filter(data => data !== null);
        
        // 주간 데이터 테이블 업데이트
        updateWeeklyTable();
        
    } catch (error) {
        console.error('주간 데이터 로드 중 오류:', error);
    }
}

// 데이터 로드 및 표시 함수 수정
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
        updateCampaignTable(data.campaign_summary);
        
        // 주간 데이터 로드
        await loadWeeklyData();
        
        // 현재 뷰에 맞는 차트 업데이트
        if (currentView === 'today') {
            // 오늘 데이터로 weeklyData 배열의 첫 번째 항목 업데이트
            if (weeklyData.length > 0) {
                weeklyData[0].hourly_data = data.hourly_data;
            }
        }
        
        // 차트 업데이트
        updateHourlyChart();

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

// 이벤트 리스너 추가
function initializeEventListeners() {
    // 차트 뷰 토글 이벤트
    document.getElementById('todayView').addEventListener('change', function() {
        if (this.checked) {
            currentView = 'today';
            updateHourlyChart();
        }
    });

    document.getElementById('weekView').addEventListener('change', function() {
        if (this.checked) {
            currentView = 'week';
            updateHourlyChart();
        }
    });
}

// 페이지 초기화
document.addEventListener('DOMContentLoaded', () => {
    setupSidebar();  // 사이드바 설정
    initializeEventListeners(); // 이벤트 리스너 초기화
    loadData();      // 초기 데이터 로드
    
    // 5분마다 새로운 데이터 확인
    setInterval(loadData, 5 * 60 * 1000);
});