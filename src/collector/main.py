import json
import logging
from datetime import datetime
from server_monitor import CoupangAdServerMonitor

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def collect_data():
    """데이터 수집 함수"""
    try:
        logger.info("데이터 수집 시작")
        
        # 계정 정보 (비공개 레포지토리에서만 사용)
        username = 'alfm1991'
        password = '$als$Ehdvkf29!'
        
        # 데이터 수집
        logger.info("CoupangAdServerMonitor 초기화")
        monitor = CoupangAdServerMonitor(username, password)
        
        try:
            logger.info("웹드라이버 초기화")
            monitor.initialize_webdriver()
            
            logger.info("쿠팡 로그인 시도")
            if not monitor.login_to_coupang():
                logger.error("로그인 실패")
                return False

            logger.info("페이지당 행 수 설정")
            monitor.select_rows_per_page(20)
            
            logger.info("데이터 수집 시작")
            campaign_data = monitor.collect_data()
            
            if not campaign_data:
                logger.warning("수집된 데이터가 없습니다")
                return False

            logger.info(f"데이터 수집 완료: {len(campaign_data)} 캠페인")
            return True

        finally:
            if hasattr(monitor, 'driver'):
                logger.info("웹드라이버 종료")
                monitor.driver.quit()

    except Exception as e:
        logger.error(f"오류 발생: {str(e)}", exc_info=True)
        return False

if __name__ == '__main__':
    collect_data()
