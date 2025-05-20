(function () {
  const PASSWORD = "1234";

  // 이미 로그인 되어 있으면 아무것도 하지 않음
  if (sessionStorage.getItem("loggedIn") === "true") return;

  // 스타일 추가
  const style = document.createElement("style");
  style.textContent = `
    .login-overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.6);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 9999;
    }
    .login-modal {
      background: white;
      padding: 2rem;
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      max-width: 300px;
      width: 100%;
      text-align: center;
      font-family: sans-serif;
    }
    .login-modal h2 {
      margin-bottom: 1rem;
      font-size: 1.5rem;
      color: #333;
    }
    .login-modal input {
      width: 100%;
      padding: 0.5rem;
      font-size: 1rem;
      margin-bottom: 1rem;
      border: 1px solid #ccc;
      border-radius: 4px;
    }
    .login-modal button {
      width: 100%;
      padding: 0.5rem;
      font-size: 1rem;
      background-color: #007bff;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    .login-modal button:hover {
      background-color: #0056b3;
    }
    .login-error {
      color: red;
      font-size: 0.9rem;
      margin-top: 0.5rem;
    }
  `;
  document.head.appendChild(style);

  // 로그인 모달 생성
  const overlay = document.createElement("div");
  overlay.className = "login-overlay";

  const modal = document.createElement("div");
  modal.className = "login-modal";

  modal.innerHTML = `
    <h2>로그인</h2>
    <input type="password" id="login-password" placeholder="비밀번호 입력" />
    <button id="login-button">확인</button>
    <div class="login-error" id="login-error" style="display:none;">비밀번호가 틀렸습니다.</div>
  `;

  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  // 로그인 버튼 이벤트
  document.getElementById("login-button").addEventListener("click", () => {
    const input = document.getElementById("login-password").value;
    const errorMsg = document.getElementById("login-error");

    if (input === PASSWORD) {
      sessionStorage.setItem("loggedIn", "true");
      document.body.removeChild(overlay); // 모달 제거
    } else {
      errorMsg.style.display = "block";
    }
  });

  // 엔터 키도 가능하게
  document.getElementById("login-password").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      document.getElementById("login-button").click();
    }
  });
})();
