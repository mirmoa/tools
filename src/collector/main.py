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
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login(driver, username, password):
    driver.get('https://ads.coupang.com')
    
    # 로그인 폼 대기
    wait = WebDriverWait(driver, 10)
    username_field = wait.until(EC.presence_of_element_located((By.NAME, 'username')))
    password_field = driver.find_element(By.NAME, 'password')
    
    # 로그인 정보 입력
    username_field.send_keys(username)
    password_field.send_keys(password)
    
    # 로그인 버튼 클릭
    login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    login_button.click()
    
    # 대시보드 로딩 대기
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'dashboard')))

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
