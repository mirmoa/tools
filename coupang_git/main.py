import os
import re
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# 계정 정보
COUPANG_ID = "alfm1991"
COUPANG_PW = "$als$Ehdvkf29!"

# 로그 디렉토리 생성
os.makedirs('log', exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'log/{datetime.now().strftime("%y%m%d")}log.txt', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def setup_driver():
    """웹드라이버 설정"""
    try:
        chrome_options = Options()
        #chrome_options.add_argument('--headless=new')  # 헤드리스 모드 추가
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        logger.info("웹드라이버 설정 완료")
        return driver
    except Exception as e:
        logger.error(f"웹드라이버 설정 실패: {str(e)}")
        raise


def login(driver):
    """쿠팡 광고센터 로그인"""
    try:
        logger.info("로그인 페이지 접속...")
        driver.get("https://advertising.coupang.com/relay/wing/home?from=WING_LNB&kc_locale=ko-KR")
        time.sleep(3)
        
        wait = WebDriverWait(driver, 20)
        
        # 아이디 입력
        username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        username_field.clear()
        username_field.send_keys(COUPANG_ID)
        logger.info("아이디 입력 완료")
        
        # 비밀번호 입력
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(COUPANG_PW)
        logger.info("비밀번호 입력 완료")
        
        # 로그인 버튼 클릭
        login_button = driver.find_element(By.ID, "kc-login")
        login_button.click()
        logger.info("로그인 버튼 클릭")
        
        # 2차 인증 대기
        logger.info("=" * 50)
        logger.info("2차 인증이 필요하면 브라우저에서 직접 완료하세요!")
        logger.info("=" * 50)
        
        # 광고관리 메뉴 나타날 때까지 대기 (최대 120초)
        wait_long = WebDriverWait(driver, 120)
        ad_menu = wait_long.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-bigfoot-component='lnb-menu-ad-management']"))
        )
        logger.info("로그인 성공!")
        
        # 광고관리 메뉴 클릭
        ad_menu.click()
        logger.info("광고관리 메뉴 클릭")
        time.sleep(3)
        
        # 테이블 로드 대기
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".rt-tbody")))
        logger.info("캠페인 테이블 로드 완료")
        return True
            
    except Exception as e:
        logger.error(f"로그인 실패: {e}")
        driver.save_screenshot(f'log/login_error_{datetime.now().strftime("%y%m%d_%H%M%S")}.png')
        return False


def select_rows_per_page(driver, rows=20):
    """페이지당 표시할 행 수 선택"""
    try:
        wait = WebDriverWait(driver, 30)
        
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.-loading.-active")))
        time.sleep(2)
        
        select_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "select[aria-label='rows per page']"))
        )
        
        driver.execute_script("arguments[0].scrollIntoView(true);", select_element)
        time.sleep(1)
        
        select_element.click()
        
        option = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"select[aria-label='rows per page'] option[value='{rows}']"))
        )
        option.click()
        
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.-loading.-active")))
        time.sleep(1)
        
        logger.info(f"{rows}개 보기 설정 완료")
        return True
    except Exception as e:
        logger.error(f"행 수 선택 실패: {str(e)}")
        return False


def collect_campaign_data(driver):
    """캠페인 데이터 수집"""
    try:
        wait = WebDriverWait(driver, 15)
        
        table = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.ReactTable.contents-body-table.dashboard-react-table-revamp")
            )
        )
        
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.-loading.-active")))
        
        rows = table.find_elements(By.CSS_SELECTOR, ".rt-tbody .rt-tr-group")
        if not rows:
            logger.warning("캠페인 데이터가 없습니다.")
            return {}, 0
            
        campaigns = {}
        total_cost = 0
        current_hour = datetime.now().strftime('%H')
        
        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, ".rt-td")
            if not cells or len(cells) <= 7:
                continue

            try:
                campaign_name = cells[0].find_element(By.CSS_SELECTOR, ".dashboard-title").text.strip()
            except:
                continue

            cost_text = cells[7].text.strip()
            
            if not campaign_name:
                continue
                
            numbers = re.findall(r'[\d,]+', cost_text)
            cost = float(numbers[-1].replace(',', '')) if numbers else 0
            
            campaigns[campaign_name] = {
                'hourly_costs': {str(h).zfill(2): 0.0 for h in range(24)},
                'last_updated': datetime.now().isoformat()
            }
            campaigns[campaign_name]['hourly_costs'][current_hour] = cost
            total_cost += cost
            
        logger.info(f"{len(campaigns)}개의 캠페인 데이터 수집 완료")
        return campaigns, total_cost
    except Exception as e:
        logger.error(f"데이터 수집 실패: {str(e)}")
        return {}, 0


def save_data(campaigns, total_cost):
    """데이터를 JSON 파일로 저장"""
    try:
        current_time = datetime.now()
        today = current_time.strftime('%Y-%m-%d')
        current_hour = current_time.strftime('%H')
        
        # 절대경로로 저장
        data_dir = Path('C:/tools/src/frontend/public/data/daily')
        data_dir.mkdir(parents=True, exist_ok=True)
        data_file = data_dir / f'{today}.json'
        
        # 기존 데이터 로드 또는 새로 생성
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                'campaign_summary': {},
                'hourly_data': {str(h).zfill(2): 0.0 for h in range(24)},
                'last_updated': None
            }
        
        # 캠페인별 데이터 업데이트
        for campaign_name, info in campaigns.items():
            if campaign_name not in data['campaign_summary']:
                data['campaign_summary'][campaign_name] = {
                    'hourly_costs': {str(h).zfill(2): 0.0 for h in range(24)},
                    'last_updated': None
                }
            
            data['campaign_summary'][campaign_name]['hourly_costs'][current_hour] = info['hourly_costs'][current_hour]
            data['campaign_summary'][campaign_name]['last_updated'] = current_time.isoformat()
        
        data['hourly_data'][current_hour] = total_cost
        data['last_updated'] = current_time.isoformat()
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"데이터 저장 완료: {data_file}")
        logger.info(f"현재 시간({current_hour}시) 총 광고비: {total_cost:,.0f}원")
        
        return True
        
    except Exception as e:
        logger.error(f"데이터 저장 실패: {e}")
        return False


def git_push():
    """Git에 변경사항 push"""
    try:
        git_root = 'C:/tools'
        
        # git pull
        result = subprocess.run(
            ['git', 'pull', '--no-edit'],
            capture_output=True, text=True, encoding='utf-8',
            cwd=git_root
        )
        if result.returncode != 0:
            logger.warning(f"git pull 경고: {result.stderr}")
        
        # git add
        result = subprocess.run(
            ['git', 'add', 'src/frontend/public/data/daily/'],
            capture_output=True, text=True, encoding='utf-8',
            cwd=git_root
        )
        if result.returncode != 0:
            logger.error(f"git add 실패: {result.stderr}")
            return False
        
        # 변경사항 확인
        result = subprocess.run(
            ['git', 'diff', '--cached', '--quiet'],
            capture_output=True,
            cwd=git_root
        )
        if result.returncode == 0:
            logger.info("변경사항 없음 - Git push 스킵")
            return True
        
        # git commit
        today = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M')
        result = subprocess.run(
            ['git', 'commit', '-m', f'광고비 데이터 업데이트: {today} {current_time}'],
            capture_output=True, text=True, encoding='utf-8',
            cwd=git_root
        )
        if result.returncode != 0:
            logger.error(f"git commit 실패: {result.stderr}")
            return False
        
        # git push
        result = subprocess.run(
            ['git', 'push'],
            capture_output=True, text=True, encoding='utf-8',
            cwd=git_root
        )
        if result.returncode != 0:
            logger.error(f"git push 실패: {result.stderr}")
            return False
        
        logger.info("Git push 완료")
        return True
        
    except Exception as e:
        logger.error(f"Git 오류: {e}")
        return False


def main():
    """메인 실행 함수"""
    driver = None
    
    try:
        logger.info("=" * 50)
        logger.info("쿠팡 광고비 수집 시작")
        logger.info("=" * 50)
        
        driver = setup_driver()
        
        if not login(driver):
            raise Exception("로그인 실패")
        
        if not select_rows_per_page(driver):
            logger.warning("행 수 설정 실패 - 기본값으로 진행")
        
        campaigns, total_cost = collect_campaign_data(driver)
        if not campaigns:
            raise Exception("데이터 수집 실패")
        
        if not save_data(campaigns, total_cost):
            raise Exception("데이터 저장 실패")
        
        git_push()
        
        logger.info("=" * 50)
        logger.info("작업 완료!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        
    finally:
        if driver:
            driver.quit()
            logger.info("브라우저 종료")


if __name__ == "__main__":
    main()