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
from selenium.webdriver.support.ui import Select
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

def setup_driver(): # 웹드라이버 설정
    """웹드라이버 설정"""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        
        # 봇 감지 우회를 위한 추가 설정
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())  #설치 경로 C:\Users\모아유통\.wdm\drivers\chromedriver\win64
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # JavaScript 코드 실행으로 웹드라이버 감지 우회
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

def login(driver, username, password):
    """쿠팡 광고 플랫폼 로그인"""
    try:
        # 쿠키 설정을 위해 일단 도메인에 접속
        logger.info("기본 도메인 접속 시도...")
        driver.get("https://wing.coupang.com")
        time.sleep(3)  # 페이지 로드 대기
        logger.info("기본 도메인 접속 완료")
        
        # 언어 및 지역 관련 쿠키 설정
        cookies = [
            {"name": "locale", "value": "ko"},
            {"name": "wing-locale", "value": "ko"},
            {"name": "x-coupang-accept-language", "value": "ko-KR"},
            {"name": "x-coupang-target-market", "value": "KR"}
        ]
        
        logger.info("쿠키 설정 시작...")
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
                logger.info(f"쿠키 설정 성공: {cookie['name']}={cookie['value']}")
            except Exception as e:
                logger.warning(f"쿠키 설정 실패 ({cookie['name']}): {str(e)}")
        
        # 로그인 페이지 접속 - 명시적으로 한국어 설정 추가
        logger.info("로그인 페이지 접속 시도...")
        driver.get("https://advertising.coupang.com/relay/wing/home?from=WING_LNB&kc_locale=ko-KR")
        time.sleep(5)  # 페이지 로드를 위한 추가 대기
        
        # 현재 URL 로깅
        current_url = driver.current_url
        logger.info(f"현재 URL: {current_url}")
        
        # 페이지 타이틀 로깅
        page_title = driver.title
        logger.info(f"페이지 타이틀: {page_title}")
        
        # 페이지 스크린샷 저장
        timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
        screenshot_file = f'log/login_page_{timestamp}.png'
        driver.save_screenshot(screenshot_file)
        logger.info(f"로그인 페이지 스크린샷 저장: {screenshot_file}")
        
        wait = WebDriverWait(driver, 20)  # 대기 시간 증가
        
        # 언어가 한국어로 설정되어 있는지 확인
        try:
            # 언어 선택기가 로드될 때까지 대기
            logger.info("언어 선택기 찾는 중...")
            select_element = wait.until(
                EC.presence_of_element_located((By.ID, "changeLocale"))
            )
            logger.info("언어 선택기 발견")
            
            # 한국어 옵션 선택
            select = Select(select_element)
            select.select_by_visible_text("한국어")
            logger.info("언어를 한국어로 설정함")
            time.sleep(3)  # 언어 변경 적용 기다림
        except Exception as e:
            logger.warning(f"언어 설정 변경 시도 실패: {str(e)}")
        
        # ID 입력 필드가 로드될 때까지 대기
        logger.info("사용자명 입력 필드 찾는 중...")
        username_field = wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        logger.info("사용자명 입력 필드 발견")
        
        # 자바스크립트로 값 설정
        driver.execute_script("arguments[0].value = arguments[1]", username_field, username)
        logger.info("사용자명 입력 완료")
        time.sleep(1)
        
        # 비밀번호 입력
        logger.info("비밀번호 입력 필드 찾는 중...")
        password_field = wait.until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        logger.info("비밀번호 입력 필드 발견")
        
        # 자바스크립트로 값 설정
        driver.execute_script("arguments[0].value = arguments[1]", password_field, password)
        logger.info("비밀번호 입력 완료")
        time.sleep(1)
        
        # 로그인 버튼 클릭
        logger.info("로그인 버튼 찾는 중...")
        login_button = wait.until(
            EC.element_to_be_clickable((By.ID, "kc-login"))
        )
        logger.info("로그인 버튼 발견")
        
        # 자바스크립트로 클릭
        driver.execute_script("arguments[0].click();", login_button)
        logger.info("로그인 버튼 클릭 완료")
        
        # 대시보드 페이지 로드 확인
        logger.info("대시보드 페이지 로드 대기 중...")
        wait_dashboard = WebDriverWait(driver, 30)  # 대시보드 로드 대기 시간 증가
        wait_dashboard.until(
            EC.url_to_be("https://advertising.coupang.com/marketing/dashboard/sales")
        )
        logger.info("로그인 성공")
        return True
    except Exception as e:
        logger.error(f"로그인 실패: {str(e)}")
        
        # 현재 페이지 스크린샷 저장
        try:
            error_timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
            error_screenshot_file = f'log/login_error_{error_timestamp}.png'
            driver.save_screenshot(error_screenshot_file)
            logger.info(f"오류 화면 스크린샷 저장: {error_screenshot_file}")
            
            # 현재 URL 로깅
            logger.info(f"오류 발생 시 URL: {driver.current_url}")
        except:
            logger.error("오류 화면 스크린샷 저장 실패")
            
        return False

def select_rows_per_page(driver, rows=20):
    """페이지당 표시할 행 수 선택"""
    try:
        wait = WebDriverWait(driver, 30)  # 대기 시간 증가
        
        # 로딩 애니메이션이 사라질 때까지 대기
        wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.-loading.-active"))
        )
        
        # 페이지가 완전히 로드될 때까지 추가 대기
        time.sleep(2)
        
        # select 요소 찾기 및 클릭 가능 상태 대기
        select_element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "select[aria-label='rows per page']"))
        )
        
        # 요소로 스크롤
        driver.execute_script("arguments[0].scrollIntoView(true);", select_element)
        time.sleep(1)  # 스크롤 후 잠시 대기
        
        # select 클릭
        select_element.click()
        
        # 옵션 선택
        option_selector = f"select[aria-label='rows per page'] option[value='{rows}']"
        option = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, option_selector))
        )
        option.click()
        
        # 변경 후 로딩 완료 대기
        wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.-loading.-active"))
        )
        time.sleep(1)  # 추가 대기
        
        logger.info(f"{rows}개 보기 설정 완료")
        return True
    except Exception as e:
        logger.error(f"행 수 선택 실패: {str(e)}")
        return False

def collect_campaign_data(driver):
    """캠페인 데이터 수집"""
    try:
        wait = WebDriverWait(driver, 15)
        
        # 테이블 로드 대기
        table = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.ReactTable.contents-body-table.dashboard-react-table-revamp")
            )
        )
        
        # 로딩 완료 대기
        wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.-loading.-active"))
        )
        
        # 캠페인 행 찾기
        rows = table.find_elements(By.CSS_SELECTOR, ".rt-tbody .rt-tr-group")
        if not rows:
            logger.warning("캠페인 데이터가 없습니다.")
            return {}, 0
            
        campaigns = {}
        total_cost = 0
        campaign_column = 0  # 캠페인명 열
        cost_column = 5      # 비용 열
        current_hour = datetime.now().strftime('%H')
        
        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, ".rt-td")
            if not cells or len(cells) <= max(campaign_column, cost_column):
                continue
                
            campaign_name = cells[campaign_column].text.strip()
            cost_text = cells[cost_column].text.strip()
            
            if not campaign_name:
                continue
                
            cost = float(cost_text.replace(',', '').replace(' 원', '')) if cost_text and any(c.isdigit() for c in cost_text) else 0
            current_time = datetime.now().isoformat()
            
            try:
                campaigns[campaign_name] = {
                    'total_cost': cost,
                    'hourly_costs': {current_hour: cost},
                    'data_points': 1,
                    'last_updated': current_time
                }
                total_cost += cost
                logger.debug(f"캠페인 데이터 추가: {campaign_name} = {campaigns[campaign_name]}")
            except Exception as e:
                logger.error(f"캠페인 데이터 구성 실패 ({campaign_name}): {str(e)}")
                continue
            
        if not campaigns:
            logger.warning("수집된 캠페인이 없습니다.")
            return {}, 0
            
        logger.info(f"{len(campaigns)}개의 캠페인 데이터 수집 완료")
        return campaigns, total_cost
    except Exception as e:
        logger.error(f"데이터 수집 실패: {str(e)}")
        return {}, 0

def create_daily_structure():
    """하루 데이터 구조 생성 (00-23시)"""
    hours = {str(h).zfill(2): 0 for h in range(24)}
    return {
        'campaign_summary': {},
        'hourly_data': hours.copy(),
        'last_updated': None
    }

def save_data(campaigns, total_cost):
    """데이터 저장"""
    try:
        # 현재 시간 기준으로 오늘 날짜 가져오기
        current_time = datetime.now()
        today = current_time.strftime('%Y-%m-%d')
        current_hour = current_time.strftime('%H')
        
        data_dir = Path('src/frontend/public/data/daily')
        data_dir.mkdir(parents=True, exist_ok=True)
        data_file = data_dir / f'{today}.json'
        
        # 기존 데이터 로드 또는 새로운 데이터 구조 생성
        if data_file.exists():
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # hourly_data 구조 확인 및 수정
                    if not isinstance(data.get('hourly_data'), dict):
                        data['hourly_data'] = {str(h).zfill(2): 0 for h in range(24)}
                    else:
                        # 기존 데이터 보존하면서 00-23 구조로 변환
                        current_data = data['hourly_data']
                        data['hourly_data'] = {
                            str(h).zfill(2): float(current_data.get(str(h).zfill(2), 0))
                            for h in range(24)
                        }
                        
            except json.JSONDecodeError:
                logger.warning(f"기존 파일 손상: {data_file}")
                data = create_daily_structure()
        else:
            data = create_daily_structure()
            
        # 현재 시간의 캠페인별 데이터 저장
        for campaign_name, info in campaigns.items():
            if campaign_name not in data['campaign_summary']:
                data['campaign_summary'][campaign_name] = {
                    'hourly_costs': {str(h).zfill(2): 0 for h in range(24)},
                    'last_updated': None
                }
            elif not isinstance(data['campaign_summary'][campaign_name].get('hourly_costs'), dict):
                data['campaign_summary'][campaign_name]['hourly_costs'] = {str(h).zfill(2): 0 for h in range(24)}
            else:
                # 기존 데이터 보존하면서 00-23 구조로 변환
                current_costs = data['campaign_summary'][campaign_name]['hourly_costs']
                data['campaign_summary'][campaign_name]['hourly_costs'] = {
                    str(h).zfill(2): float(current_costs.get(str(h).zfill(2), 0))
                    for h in range(24)
                }
            
            # 현재 시간의 비용 저장
            data['campaign_summary'][campaign_name]['hourly_costs'][current_hour] = info['total_cost']
            data['campaign_summary'][campaign_name]['last_updated'] = current_time.isoformat()
            
        # 현재 시간의 총 광고비 저장
        data['hourly_data'][current_hour] = total_cost
        data['last_updated'] = current_time.isoformat()
        
        # 데이터 저장
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"데이터 저장 완료: {data_file}")
        return True
    except Exception as e:
        logger.error(f"데이터 저장 실패: {str(e)}")
        return False

def main():
    """메인 실행 함수"""
    driver = None
    max_retries = 3
    retry_interval = 30
    
    for attempt in range(max_retries):
        try:
            logger.info(f"시도 {attempt + 1}/{max_retries}")
            
            # 웹드라이버 초기화
            driver = setup_driver()
            
            # 로그인 시도 (디버깅을 위해 여기서 종료됨)
            if not login(driver, COUPANG_ID, COUPANG_PW):
                raise Exception("로그인 실패")
                
            # 디버깅 중이므로 여기 이후의 코드는 실행되지 않음
            if not select_rows_per_page(driver):
                raise Exception("행 수 설정 실패")
                
            campaigns, total_cost = collect_campaign_data(driver)
            if not campaigns:
                raise Exception("데이터 수집 실패")
                
            if not save_data(campaigns, total_cost):
                raise Exception("데이터 저장 실패")
                
            logger.info("작업 완료")
            break
            
        except Exception as e:
            logger.error(f"오류 발생 (시도 {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"{retry_interval}초 후 재시도...")
                time.sleep(retry_interval)
            else:
                logger.error("최대 재시도 횟수 초과")

        finally:
            if driver:
                driver.quit()
                logger.info("웹드라이버 종료")

if __name__ == "__main__":
    main()
