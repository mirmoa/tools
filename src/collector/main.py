import os
import json
import logging
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# 계정 정보 (비공개 레포지토리에서만 사용)
COUPANG_ID = "alfm1991"
COUPANG_PW = "$als$Ehdvkf29!"

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # 새로운 headless 모드 사용
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')  # 창 크기 설정
    chrome_options.add_argument('--disable-gpu')  # GPU 가속 비활성화
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 자동화 감지 방지
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')  # 일반적인 user-agent 설정
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login(driver, username, password):
    try:
        driver.get("https://advertising.coupang.com/relay/wing/home?from=WING_LNB")
        logger.info("페이지 로딩 시작")
        
        # 로그인 폼이 나타날 때까지 대기 (최대 15초)
        wait = WebDriverWait(driver, 15)
        
        # ID 입력 필드 대기 및 입력
        logger.info("로그인 폼 찾는 중...")
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        password_field = driver.find_element(By.ID, "password")
        
        username_field.send_keys(username)
        logger.info("아이디 입력 완료")
        
        password_field.send_keys(password)
        logger.info("비밀번호 입력 완료")
        
        # 로그인 버튼 클릭
        login_button = driver.find_element(By.ID, "kc-login")
        login_button.click()
        logger.info("로그인 버튼 클릭")
        
        # 대시보드 로딩 대기
        wait.until(
            EC.url_to_be("https://advertising.coupang.com/marketing/dashboard/sales")
        )
        logger.info("로그인 성공 - 대시보드 로딩됨")
        
    except Exception as e:
        logger.error(f"로그인 중 오류 발생: {str(e)}")
        # 현재 페이지의 HTML을 로깅
        logger.error(f"현재 페이지 HTML: {driver.page_source}")
        raise

def collect_campaign_data(driver):
    # 캠페인 데이터 수집
    campaigns = {}
    total_cost = 0
    
    # 캠페인 목록 대기
    wait = WebDriverWait(driver, 10)
    campaign_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'campaign-item')))
    
    for campaign in campaign_elements:
        name = campaign.find_element(By.CLASS_NAME, 'campaign-name').text
        cost = float(campaign.find_element(By.CLASS_NAME, 'campaign-cost').text.replace('₩', '').replace(',', ''))
        
        campaigns[name] = {
            'total_cost': cost,
            'last_updated': datetime.now().isoformat(),
            'data_points': 1
        }
        total_cost += cost
    
    return campaigns, total_cost

def save_data(campaigns, total_cost):
    # 데이터 저장 경로 설정
    today = datetime.now().strftime('%Y-%m-%d')
    data_dir = Path('data/daily')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    data_file = data_dir / f'{today}.json'
    
    # 기존 데이터 로드 또는 새로운 데이터 생성
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 캠페인 데이터 업데이트
        for name, info in campaigns.items():
            if name in data['campaign_summary']:
                data['campaign_summary'][name]['total_cost'] += info['total_cost']
                data['campaign_summary'][name]['data_points'] += 1
                data['campaign_summary'][name]['last_updated'] = info['last_updated']
            else:
                data['campaign_summary'][name] = info
                
        # 시간별 데이터 추가
        hour = datetime.now().strftime('%H')
        data['hourly_data'][hour] = total_cost
        
    else:
        data = {
            'campaign_summary': campaigns,
            'hourly_data': {
                datetime.now().strftime('%H'): total_cost
            },
            'total_cost': total_cost,
            'last_updated': datetime.now().isoformat()
        }
    
    # 총 비용 업데이트
    data['total_cost'] = sum(campaign['total_cost'] for campaign in data['campaign_summary'].values())
    data['last_updated'] = datetime.now().isoformat()
    
    # 데이터 저장
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    driver = None
    try:
        driver = setup_driver()
        login(driver, COUPANG_ID, COUPANG_PW)
        campaigns, total_cost = collect_campaign_data(driver)
        save_data(campaigns, total_cost)
        
    except Exception as e:
        print(f'에러 발생: {str(e)}')
        raise
        
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    main()
