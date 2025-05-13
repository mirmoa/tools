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
import subprocess
import sys

# 계정 정보
COUPANG_ID = "alfm1991"
COUPANG_PW = "$als$Ehdvkf29!"

# 로그 설정 - 최소화
LOG_FILE = f'log/{datetime.now().strftime("%y%m%d")}log.txt'
os.makedirs('log', exist_ok=True)

# 로깅 설정 - 간소화
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def setup_driver():
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
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        service = Service(ChromeDriverManager().install())
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
        # 기본 도메인 접속
        driver.get("https://wing.coupang.com")
        time.sleep(3)

        # 쿠키 설정
        cookies = [
            {"name": "locale", "value": "ko"},
            {"name": "wing-locale", "value": "ko"},
            {"name": "x-coupang-accept-language", "value": "ko-KR"},
            {"name": "x-coupang-target-market", "value": "KR"}
        ]

        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass

        # 로그인 페이지 접속
        driver.get("https://advertising.coupang.com/relay/wing/home?from=WING_LNB&kc_locale=ko-KR")
        time.sleep(5)

        wait = WebDriverWait(driver, 20)

        # 언어 설정 시도
        try:
            select_element = wait.until(EC.presence_of_element_located((By.ID, "changeLocale")))
            select = Select(select_element)
            select.select_by_visible_text("한국어")
            time.sleep(3)
        except Exception:
            pass

        # ID 입력
        username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        driver.execute_script("arguments[0].value = arguments[1]", username_field, username)
        time.sleep(1)

        # 비밀번호 입력
        password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
        driver.execute_script("arguments[0].value = arguments[1]", password_field, password)
        time.sleep(1)

        # 로그인 버튼 클릭
        login_button = wait.until(EC.element_to_be_clickable((By.ID, "kc-login")))
        driver.execute_script("arguments[0].click();", login_button)

        # 대시보드 페이지 로드 확인
        wait_dashboard = WebDriverWait(driver, 30)
        wait_dashboard.until(EC.url_to_be("https://advertising.coupang.com/marketing/dashboard/sales"))
        logger.info("로그인 성공")
        return True
    except Exception as e:
        logger.error(f"로그인 실패: {str(e)}")
        return False


def select_rows_per_page(driver, rows=20):
    """페이지당 표시할 행 수 선택"""
    try:
        wait = WebDriverWait(driver, 30)

        # 로딩 애니메이션이 사라질 때까지 대기
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.-loading.-active")))
        time.sleep(2)

        # select 요소 찾기 및 클릭 가능 상태 대기
        select_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "select[aria-label='rows per page']")))

        # 요소로 스크롤 (중앙에 위치하도록)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_element)
        time.sleep(1)  # 스크롤 후 짧은 대기

        # 요소가 화면에 보이는지 확인하고, 보이지 않으면 추가 스크롤
        if not select_element.is_displayed():
            logger.warning("셀렉트 박스가 화면에 보이지 않아 추가 스크롤을 시도합니다.")
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(1)

        # select 클릭
        select_element.click()

        # 옵션 선택
        option_selector = f"select[aria-label='rows per page'] option[value='{rows}']"
        option = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, option_selector)))
        option.click()

        # 변경 후 로딩 완료 대기
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

        # 테이블 로드 대기
        table = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.ReactTable.contents-body-table.dashboard-react-table-revamp")
        ))

        # 로딩 완료 대기
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.-loading.-active")))

        # 캠페인 행 찾기
        rows = table.find_elements(By.CSS_SELECTOR, ".rt-tbody .rt-tr-group")
        if not rows:
            logger.warning("캠페인 데이터가 없습니다.")
            return {}, 0

        campaigns = {}
        total_cost = 0
        campaign_column = 0  # 캠페인명 열
        cost_column = 5  # 비용 열
        current_hour = datetime.now().strftime('%H')

        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, ".rt-td")
            if not cells or len(cells) <= max(campaign_column, cost_column):
                continue

            campaign_name = cells[campaign_column].text.strip()
            cost_text = cells[cost_column].text.strip()

            if not campaign_name:
                continue

            cost = float(cost_text.replace(',', '').replace(' 원', '')) if cost_text and any(
                c.isdigit() for c in cost_text) else 0
            current_time = datetime.now().isoformat()

            campaigns[campaign_name] = {
                'total_cost': cost,
                'hourly_costs': {current_hour: cost},
                'data_points': 1,
                'last_updated': current_time
            }
            total_cost += cost

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
        return str(data_file)
    except Exception as e:
        logger.error(f"데이터 저장 실패: {str(e)}")
        return None


def git_push(file_path):
<<<<<<< HEAD
    """Git에 특정 파일 변경사항만 푸시"""
    try:
        # 현재 상태 확인 (다른 파일들의 변경 사항이 있는지)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        
        # 이전에 스테이징된 다른 파일들이 있으면 스테이징 취소
        if status:
            subprocess.run(["git", "reset"], check=True)
            logger.info("기존 스테이징된 파일 리셋")
        
        # 원격 저장소 변경사항 가져오기 (먼저 pull 수행)
        logger.info("Git pull 시도 중...")
        pull_result = subprocess.run(["git", "pull", "--rebase=false"], capture_output=True, text=True)
        if pull_result.returncode != 0:
            logger.error(f"Git pull 실패:\n{pull_result.stderr}")
            # 계속 진행 (로컬 변경사항 우선시)
        else:
            logger.info("Git pull 완료")
        
=======
    """Git에 특정 파일 변경사항 푸시"""
    try:
>>>>>>> c366146620526b19529552459d70ea2f7e88e1f4
        # 특정 파일만 추가
        subprocess.run(["git", "add", file_path], check=True)
        logger.info(f"Git에 파일 추가: {file_path}")

        # 커밋 메시지 생성
        commit_message = f"Update data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        commit_result = subprocess.run(["git", "commit", "-m", commit_message], capture_output=True, text=True)
        
        # 아무것도 커밋할 게 없는 경우 처리
        if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
            logger.info("커밋할 변경사항 없음")
            return True
            
        if commit_result.returncode != 0:
            logger.error(f"Git 커밋 실패:\n{commit_result.stderr}")
            return False
            
        logger.info(f"Git 커밋 생성: {commit_message}")

        # 원격 저장소 변경사항 가져오기 (rebase로 깔끔하게)
        # 푸시 전에 충돌을 방지하기 위해 pull --rebase를 먼저 수행
        pull_result = subprocess.run(["git", "pull", "--rebase"], capture_output=True, text=True)
        if pull_result.returncode != 0:
            logger.error(f"Git pull --rebase 실패:\n{pull_result.stderr}")
            return False
        logger.info("Git pull 완료")

        # 푸시
        push_result = subprocess.run(["git", "push"], capture_output=True, text=True)
        if push_result.returncode != 0:
            logger.error(f"Git push 실패:\n{push_result.stderr}")
<<<<<<< HEAD
            # 강제 푸시 시도
            logger.info("강제 푸시 시도...")
            force_push = subprocess.run(["git", "push", "--force"], capture_output=True, text=True)
            if force_push.returncode != 0:
                logger.error(f"강제 푸시 실패:\n{force_push.stderr}")
                return False
            logger.info("강제 푸시 완료")
            return True
=======
            return False
>>>>>>> c366146620526b19529552459d70ea2f7e88e1f4
        logger.info("Git 푸시 완료")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Git 작업 실패: {e}")
        return False
    except Exception as e:
        logger.error(f"Git 푸시 중 오류 발생: {str(e)}")
        return False

def main():
    """메인 실행 함수"""
    driver = None
    max_retries = 3
    retry_interval = 30

    for attempt in range(max_retries):
        try:
            logger.info(f"실행 시도 {attempt + 1}/{max_retries}")

            # 웹드라이버 초기화
            driver = setup_driver()

            # 로그인
            if not login(driver, COUPANG_ID, COUPANG_PW):
                raise Exception("로그인 실패")

            # 행 수 설정
            if not select_rows_per_page(driver):
                raise Exception("행 수 설정 실패")

            # 데이터 수집
            campaigns, total_cost = collect_campaign_data(driver)
            if not campaigns:
                raise Exception("데이터 수집 실패")

            # 데이터 저장
            saved_file = save_data(campaigns, total_cost)
            if not saved_file:
                raise Exception("데이터 저장 실패")

            # Git 푸시
            if git_push(saved_file):
                logger.info("데이터 수집 및 Git 푸시 완료")
            else:
                logger.error("Git 푸시 실패")

            logger.info("작업 완료")
            break

        except Exception as e:
            logger.error(f"오류 발생 (시도 {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"{retry_interval}초 후 재시도...")
                time.sleep(retry_interval)
            else:
                logger.error("최대 재시도 횟수 초과")
                sys.exit(1)

        finally:
            if driver:
                driver.quit()
                logger.info("웹드라이버 종료")


if __name__ == "__main__":
    main()