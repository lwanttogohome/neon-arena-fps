# NEON ARENA FPS PLUS

## 포함 기능
- Three.js 기반 3D 1인칭 경기장
- WASD 이동, 점프, 마우스 시점, 발사 및 재장전
- Socket.IO 실시간 플레이어 위치/팀 동기화
- 최대 16명, 자동 팀 배정, 팀 점수
- 서버 측 이동 속도 제한, 발사 빈도 제한, 기본 조준/거리 기반 명중 판정
- 처치 시 점수 증가 및 리스폰
- Streamlit 프론트엔드와 Render 게임 서버 분리

> 학습용 프로토타입입니다. 서버 판정도 기본적인 수준이며, 상용 서비스 수준의 치트 방지·네트워크 보안·물리 충돌·매치메이킹은 아닙니다.

## 1. GitHub 업로드
1. ZIP을 PC에서 압축 해제합니다.
2. GitHub에서 `New repository`를 눌러 `neon-arena-fps` 저장소를 만듭니다.
3. 저장소 첫 화면에서 `Add file` → `Upload files`를 선택합니다.
4. 압축 해제한 폴더 안의 파일과 폴더를 저장소 최상위에 업로드합니다.
5. 최상위에 `main.py`, `game.html`, `server.py`, `requirements.txt`, `render.yaml`이 보여야 합니다.
6. `Commit changes`를 누릅니다.

## 2. Render 서버 배포
1. https://render.com 에서 GitHub로 로그인합니다.
2. `New` → `Web Service` → GitHub 저장소 `neon-arena-fps`를 연결합니다.
3. Root Directory는 비워 둡니다.
4. Runtime: Python
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `python server.py`
7. Create Web Service를 누릅니다.
8. 배포 완료 후 `https://....onrender.com` 주소를 복사합니다.
9. 그 주소를 브라우저에서 열어 `{"status":"online", ...}` 응답을 확인합니다.

## 3. Streamlit 배포
1. https://share.streamlit.io 에서 GitHub로 로그인합니다.
2. Create app을 누릅니다.
3. Repository: `neon-arena-fps`, Branch: `main`, Main file path: `main.py`
4. Deploy를 누릅니다.
5. 생성된 `....streamlit.app` 주소를 엽니다.
6. 왼쪽 사이드바의 게임 서버 주소에 Render의 `https://....onrender.com` 주소를 붙여넣습니다.
7. 닉네임을 입력하고 전투 시작을 누릅니다.
8. 다른 플레이어도 동일한 Streamlit 주소와 Render 서버 주소를 사용해야 같은 서버에서 만납니다.

## 4. 수정 후 재배포
GitHub에서 파일 클릭 → 연필(Edit) → 수정 → Commit changes. Streamlit은 변경을 감지해 재배포합니다. 서버 코드를 수정하면 Render의 Deploys/Logs도 확인하세요.

## 5. 문제 해결
- Streamlit `ModuleNotFoundError`: 루트 `requirements.txt`에 `streamlit`이 있는지 확인
- 게임 캔버스가 안 보임: 브라우저 인터넷/CDN 차단 여부 확인
- 서버 연결 실패: Render 서비스가 Live인지, 주소에 https://가 있는지 확인
- 친구가 안 보임: 두 사용자가 동일한 Render 서버 주소를 입력했는지 확인
- 마우스가 화면에 갇힘: Esc를 눌러 잠금 해제
- Render 무료 서비스는 일정 시간 미사용 후 잠들 수 있어 첫 접속이 늦을 수 있음

## 기술적 한계
현재 서버는 이동 거리 제한, 이벤트 빈도 제한, 간단한 방향/거리 기반 명중 판정을 수행합니다. 하지만 클라이언트의 카메라/조준값을 완전히 신뢰하지 않는 완전한 서버 권위형 시뮬레이션은 아닙니다. 실제 서비스 전에는 서버 틱 기반 물리, 충돌 판정, 인증, 로비/매치메이킹, 데이터 저장, 관전자·신고·차단, TLS/CORS 도메인 제한, 부하 테스트가 필요합니다.
